# -*- coding: utf-8 -*-

from audfprint.audfprint_matcher import AudioPrintMatcher
from itertools import chain

__author__ = "ujihirokazuya"
__date__ = "2017/12/02"

matcher = AudioPrintMatcher()


def _exec():
    file_names = ["/Users/ujihirokazuya/unirobot/music/nepenthes-master/nepenthes_root/nepenthes/madara-suzu.mp3"]
    messages = list()

    def _report(message):
        messages.append(message)

    matcher.execute(file_names, _report)
    # flatten
    messages = list(chain.from_iterable(messages))
    values = ",".join(messages)
    print(values)


if __name__ == '__main__':
    _exec()
