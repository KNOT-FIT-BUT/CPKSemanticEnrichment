#!/usr/bin/env python3

import sys
import argparse
import re
from collections import defaultdict

MORPHDIR='/mnt/minerva1/nlp/projects/ma/data/morph/'
SPECIAL_PREFIXES = ['nejne','nej','ne']

def parse_args():
    """ Parse program arguments """

    parser = argparse.ArgumentParser(
            description='generated wordform for a given lemma and tag filter')
    parser.add_argument('lemma')
    parser.add_argument('tag_filter')
    parser.add_argument('-p', '--parafile', help='paradigms file',
            default=MORPHDIR+'czech.paradigms')
    parser.add_argument('-l', '--lpnfile', help='lpn file',
            default=MORPHDIR+'czech.lpn')

    return parser.parse_args()


def wordform_from_lemma_and_rule(lemma, remove, prefix_suffix):
    """ Get wordform from lemma and rule """

    if lemma.endswith(remove):
        beginning = lemma[:len(lemma)-len(remove)] 
    else:
        print('ERROR: lemma' + lemma + 'does not end' + remove, file = sys.stderr)
        sys.exit()

    prefix = ''
    suffix = prefix_suffix
    for testprefix in SPECIAL_PREFIXES:
        if prefix_suffix.startswith(testprefix+'-'):
            prefix = testprefix
            suffix = prefix_suffix[len(testprefix)+1:]
            break

    return prefix + beginning + suffix


def gen_wordform(lemma, tag_filter, pns4l, trs4p):
    """ Generate a wordform corresponding to the given lemma and tag filter"""

    for (paradigm,note) in pns4l[lemma]:
        for tag_and_rule in trs4p[paradigm].split(' '):
            tag, remove, prefix_suffix = tag_and_rule.split(':')
            if re.search(tag_filter,tag): 
                yield wordform_from_lemma_and_rule(lemma, remove, prefix_suffix)

def load_trs4p_pns4l (para_filename, lpn_filename):
    """ Load the .paradigms and the .lpn files and initialize structures """

    # tag-rules for a given paradigm
    trs4p={}
    with open(para_filename) as parafile:
        for line in parafile:
            line = line.rstrip()
            paradigm, tag_of_lemma, longest_remove, tags_and_rules, *_ = line.split('\t')
            # exclude paradigms for surnames
            if not ('_nM' in paradigm or '_nF' in paradigm or 'gR' in paradigm):
                trs4p[paradigm] = tags_and_rules

    # known paradigms (and notes) corresponding to a given lemma
    pns4l = defaultdict(set)
    with open(lpn_filename) as lpnfile:
        for line in lpnfile:
            line = line.rstrip()
            lemma, paradigm, note = line.split('#')
            if paradigm in trs4p:
                pns4l[lemma].add((paradigm,note))
            #else:
            #    print('ERROR: paradigm' + paradigm + 'used for lemma', lemma, 'not found', file=sys.stderr)

    return trs4p, pns4l


def main(argv):
    """ initialize structures and print the generated wordform """

    # parse program arguments
    args = parse_args()

    # load data structures
    trs4p, pns4l = load_trs4p_pns4l (args.parafile, args.lpnfile)

    print(', '.join(list(set(gen_wordform(lemma = args.lemma, tag_filter = args.tag_filter, trs4p = trs4p, pns4l = pns4l)))))


if __name__ == "__main__":
    sys.exit(main(sys.argv))

