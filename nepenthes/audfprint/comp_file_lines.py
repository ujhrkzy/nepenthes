#!/usr/bin/env python

# comp_file_lines.py
#
# Python script to count number of exact matching lines between two files, no edit distance
# 2014-09-07 Dan Ellis dpwe@ee.columbia.edu

import sys

verbose = False

onefile = False

if len(sys.argv) == 2:
    # Special case: if a single file, compare the first ws-separated field with remainder
    onefile = True
    print("onefile true")

elif len(sys.argv) < 3:
    log_format = "Usage: {}, file1.txt file2.txt [verbose]"
    print(log_format.format(sys.argv[0]))
    sys.exit(1)

file1 = sys.argv[1]
if not onefile:
    file2 = sys.argv[2]

if len(sys.argv) > 3:
    verbose = True

# Read in the files
with open(file1) as f:
    item1s = [val.rstrip("\n") for val in f]

if onefile:
    # Set item2s to everything after first block of WS in each line.
    item2s = [item.split(None, 1)[1] for item in item1s]
    # Replace items1s with everything before first WS in each line.
    item1s = [item.split(None, 1)[0] for item in item1s]
else:
    with open(file2) as f:
        item2s = [val.rstrip("\n") for val in f]

# Now, make a boolean vector of correctness
import numpy as np
correct = np.zeros(len(item1s), np.float)
for ix, items in enumerate(zip(item1s, item2s)):
    if items[0] == items[1]:
        correct[ix] = 1.0
    else:
        if verbose:
            print("{}".format(items))

print("{} correct out of {} = {}".format(int(np.sum(correct)), len(correct), 100.0*np.mean(correct)))
