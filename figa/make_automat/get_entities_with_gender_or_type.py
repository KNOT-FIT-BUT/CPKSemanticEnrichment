#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import os
import re
from importlib import reload
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
reload(sys)

import metrics_knowledge_base


# loading KB struct
kb_struct = metrics_knowledge_base.KnowledgeBase()

# multiple values delimiter
KB_MULTIVALUE_DELIM = metrics_knowledge_base.KB_MULTIVALUE_DELIM

name_genderflag = []


def extract_names_from_line(line):
    names = kb_struct.get_data_for(line, 'ALIASES').split(KB_MULTIVALUE_DELIM)
    names.append(kb_struct.get_data_for(line, 'NAME'))
    names = (a for a in names if a.strip() != "")

    return names


def append_names_to_list(names, gender_or_type):
    for n in names:
        n = re.sub('\s+', ' ', n).strip()
        unsuitable = ";?!()[]{}<>/~@#$%^&*_=+|\"\\"
        for x in unsuitable:
            if x in n:
                break
        else:
            name_genderflag.append(n + '\t' + gender_or_type)



def generate_name_alternatives(kb_path):
    if kb_path:
        with open(kb_path) as kb:
            for line in kb:
                if line:
                    line = line.strip('\n').split('\t')
                    ent_type = kb_struct.get_ent_type(line)
                    if ent_type in ['person', 'person:artist', 'person:fictional']:
                        names = extract_names_from_line(line)
                        gender = kb_struct.get_data_for(line, 'GENDER')

                        append_names_to_list(names, gender)
                    elif ent_type in ['country', 'country:former', 'settlement', 'wattercourse', 'waterarea', 'geo:relief', 'geo:waterfall', 'geo:island', 'geo:peninsula', 'geo:continent']:
                        names = extract_names_from_line(line)
                        append_names_to_list(names, 'L')
                    else:
                        continue;

        for n in name_genderflag:
            print(n)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--kb_path')
    args = parser.parse_args()

    generate_name_alternatives(args.kb_path)
