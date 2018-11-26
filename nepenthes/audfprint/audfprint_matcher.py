#!/usr/bin/python
"""
audfprint.py

Implementation of acoustic-landmark-based robust fingerprinting.
Port of the Matlab implementation.

2014-05-25 Dan Ellis dpwe@ee.columbia.edu
"""
from __future__ import print_function

# For reporting progress time
import time
# For command line interface
import docopt
import os
# For __main__
import sys
# For multiprocessing options
import multiprocessing  # for new/add
import joblib           # for match

# The actual analyzer class/code
from audfprint import audfprint_analyze
# My hash_table implementation
from audfprint import hash_table
# Access to match functions, used in command line interface
from audfprint import audfprint_match

def filename_list_iterator(filelist, wavdir, wavext, listflag):
    """ Iterator to yeild all the filenames, possibly interpreting them
        as list files, prepending wavdir """
    if not listflag:
        for filename in filelist:
            yield os.path.join(wavdir, filename + wavext)
    else:
        for listfilename in filelist:
            with open(listfilename, 'r') as f:
                for filename in f:
                    yield os.path.join(wavdir, filename.rstrip('\n') + wavext)


def do_cmd(cmd, analyzer, hash_tab, filename_iter, matcher, outdir, type, report, skip_existing=False, strip_prefix=None):
    """ Breaks out the core part of running the command.
        This is just the single-core versions.
    """
    if cmd == 'match':
        # Running query, single-core mode
        for num, filename in enumerate(filename_iter):
            msgs = matcher.file_match_to_msgs(analyzer, hash_tab, filename, num)
            report(msgs)
    else:
        raise ValueError("unrecognized command: "+cmd)


def matcher_file_match_to_msgs(matcher, analyzer, hash_tab, filename):
    """Cover for matcher.file_match_to_msgs so it can be passed to joblib"""
    return matcher.file_match_to_msgs(analyzer, hash_tab, filename)


def do_cmd_multiproc(cmd, analyzer, hash_tab, filename_iter, matcher,
                     outdir, type, report, skip_existing=False,
                     strip_prefix=None, ncores=1):
    """ Run the actual command, using multiple processors """
    if cmd == 'match':
        # Running queries in parallel
        msgslist = joblib.Parallel(n_jobs=ncores)(
            # Would use matcher.file_match_to_msgs(), but you
            # can't use joblib on an instance method
            joblib.delayed(matcher_file_match_to_msgs)(matcher, analyzer,
                                                       hash_tab, filename)
            for filename in filename_iter
        )
        for msgs in msgslist:
            report(msgs)
    else:
        # This is not a multiproc command
        raise ValueError("unrecognized multiproc command: "+cmd)


# Command to separate out setting of analyzer parameters
def setup_analyzer(args):
    """Create a new analyzer object, taking values from docopts args"""
    # Create analyzer object; parameters will get set below
    analyzer = audfprint_analyze.Analyzer()
    # Read parameters from command line/docopts
    analyzer.density = float(args['--density'])
    analyzer.maxpksperframe = int(args['--pks-per-frame'])
    analyzer.maxpairsperpeak = int(args['--fanout'])
    analyzer.f_sd = float(args['--freq-sd'])
    analyzer.shifts = int(args['--shifts'])
    # fixed - 512 pt FFT with 256 pt hop at 11025 Hz
    analyzer.target_sr = int(args['--samplerate'])
    analyzer.n_fft = 512
    analyzer.n_hop = analyzer.n_fft/2
    # set default value for shifts depending on mode
    if analyzer.shifts == 0:
        # Default shift is 4 for match, otherwise 1
        analyzer.shifts = 4 if args['match'] else 1
    analyzer.fail_on_error = not args['--continue-on-error']
    return analyzer


# Command to separate out setting of matcher parameters
def setup_matcher(args):
    """Create a new matcher objects, set parameters from docopt structure"""
    matcher = audfprint_match.Matcher()
    matcher.window = int(args['--match-win'])
    matcher.threshcount = int(args['--min-count'])
    matcher.max_returns = int(args['--max-matches'])
    matcher.search_depth = int(args['--search-depth'])
    matcher.sort_by_time = args['--sortbytime']
    matcher.exact_count = args['--exact-count'] | args['--illustrate'] | args['--illustrate-hpf']
    matcher.illustrate = args['--illustrate'] | args['--illustrate-hpf']
    matcher.illustrate_hpf = args['--illustrate-hpf']
    matcher.verbose = args['--verbose']
    matcher.find_time_range = args['--find-time-range']
    matcher.time_quantile = float(args['--time-quantile'])
    return matcher


# Command to construct the reporter object
def setup_reporter(args):
    """ Creates a logging function, either to stderr or file"""
    opfile = args['--opfile']
    if opfile and len(opfile):
        f = open(opfile, "w")
        def report(msglist):
            """Log messages to a particular output file"""
            for msg in msglist:
                f.write(msg+"\n")
    else:
        def report(msglist):
            """Log messages by printing to stdout"""
            for msg in msglist:
                print(msg)
    return report

# CLI specified via usage message thanks to docopt
USAGE = """
Landmark-based audio fingerprinting.
Create a new fingerprint dbase with "new",
append new files to an existing database with "add",
or identify noisy query excerpts with "match".
"precompute" writes a *.fpt file under precompdir
with precomputed fingerprint for each input wav file.
"merge" combines previously-created databases into
an existing database; "newmerge" combines existing
databases to create a new one.

Usage: audfprint (new | add | match | precompute | merge | newmerge | list | remove) [options] [<file>]...

Options:
  -d <dbase>, --dbase <dbase>     Fingerprint database file
  -n <dens>, --density <dens>     Target hashes per second [default: 20.0]
  -h <bits>, --hashbits <bits>    How many bits in each hash [default: 20]
  -b <val>, --bucketsize <val>    Number of entries per bucket [default: 100]
  -t <val>, --maxtime <val>       Largest time value stored [default: 16384]
  -u <val>, --maxtimebits <val>   maxtime as a number of bits (16384 == 14 bits)
  -r <val>, --samplerate <val>    Resample input files to this [default: 11025]
  -p <dir>, --precompdir <dir>    Save precomputed files under this dir [default: .]
  -i <val>, --shifts <val>        Use this many subframe shifts building fp [default: 0]
  -w <val>, --match-win <val>     Maximum tolerable frame skew to count as a match [default: 2]
  -N <val>, --min-count <val>     Minimum number of matching landmarks to count as a match [default: 5]
  -x <val>, --max-matches <val>   Maximum number of matches to report for each query [default: 1]
  -X, --exact-count               Flag to use more precise (but slower) match counting
  -R, --find-time-range           Report the time support of each match
  -Q, --time-quantile <val>       Quantile at extremes of time support [default: 0.05]
  -S <val>, --freq-sd <val>       Frequency peak spreading SD in bins [default: 30.0]
  -F <val>, --fanout <val>        Max number of hash pairs per peak [default: 3]
  -P <val>, --pks-per-frame <val>  Maximum number of peaks per frame [default: 5]
  -D <val>, --search-depth <val>  How far down to search raw matching track list [default: 100]
  -H <val>, --ncores <val>        Number of processes to use [default: 1]
  -o <name>, --opfile <name>      Write output (matches) to this file, not stdout [default: ]
  -K, --precompute-peaks          Precompute just landmarks (else full hashes)
  -k, --skip-existing             On precompute, skip items if output file already exists
  -C, --continue-on-error         Keep processing despite errors reading input
  -l, --list                      Input files are lists, not audio
  -T, --sortbytime                Sort multiple hits per file by time (instead of score)
  -v <val>, --verbose <val>       Verbosity level [default: 1]
  -I, --illustrate                Make a plot showing the match
  -J, --illustrate-hpf            Plot the match, using onset enhancement
  -W <dir>, --wavdir <dir>        Find sound files under this dir [default: ]
  -V <ext>, --wavext <ext>        Extension to add to wav file names [default: ]
  --version                       Report version number
  --help                          Print this message
"""

__version__ = 20150406
config_dict = dict()
config_dict["--version"] = __version__
config_dict["--density"] = 20.0
config_dict["--hashbits"] = 20
config_dict["--bucketsize"] = 100
config_dict["--maxtime"] = 16384
config_dict["--samplerate"] = 11025
config_dict["--precompdir"] = "."
config_dict["--shifts"] = 0
config_dict["--match-win"] = 2
# config_dict["--min-count"] = 5
config_dict["--min-count"] = 2
config_dict["--max-matches"] = 1
config_dict["--time-quantile"] = 0.05
config_dict["--freq-sd"] = 30.0
config_dict["--fanout"] = 3
config_dict["--pks-per-frame"] = 5
config_dict["--search-depth"] = 100
config_dict["--ncores"] = 1
config_dict["--verbose"] = 1
config_dict["--dbase"] = "audfprint/fpdbase.pklz"
config_dict["--continue-on-error"] = True
config_dict["--sortbytime"] = None
config_dict['--exact-count'] = False
config_dict['--illustrate'] = False
config_dict['--illustrate-hpf'] = False
config_dict['--find-time-range'] = False
config_dict['--time-quantile'] = 0.02
config_dict["match"] = True


class AudioPrintMatcher(object):

    def __init__(self):
        """ Main routine for the command-line interface to audfprint """
        # Other globals set from command line
        args = config_dict
        # values = ["--dbase", "fpdbase.pklz"]
        # args = docopt.docopt(USAGE, version=__version__, argv=values)
        analyzer = setup_analyzer(args)
        precomp_type = 'hashes'

        # For everything other than precompute, we need a database name
        # Check we have one
        dbasename = args['--dbase']
        # Load existing hash table file (add, match, merge)
        hash_tab = hash_table.HashTable(dbasename)
        if analyzer and 'samplerate' in hash_tab.params \
            and hash_tab.params['samplerate'] != analyzer.target_sr:
            # analyzer.target_sr = hash_tab.params['samplerate']
            print("db samplerate overridden to ", analyzer.target_sr)

        # Create a matcher
        matcher = setup_matcher(args)

        self.args = args
        self.analyzer = analyzer
        self.matcher = matcher
        self.hash_table = hash_tab
        self.precomp_type = precomp_type

    def execute2(self, file_names: list, report):
        # python3 audfprint.py match --dbase fpdbase.pklz sound/matsumushi.mp3
        do_cmd_multiproc("match", self.analyzer, self.hash_table, file_names,
                         self.matcher, self.args['--precompdir'],
                         self.precomp_type,
                         report,
                         ncores=1)

    def execute(self, file_names: list, report):
        do_cmd("match", self.analyzer, self.hash_table, file_names,
               self.matcher, self.args['--precompdir'], self.precomp_type, report)
