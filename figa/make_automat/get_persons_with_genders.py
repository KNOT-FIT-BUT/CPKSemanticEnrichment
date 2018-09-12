import argparse
import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import metrics_knowledge_base
reload(sys)
sys.setdefaultencoding("utf-8")

# loading HEAD-KB file
headKB, ent_type_cols = metrics_knowledge_base.getDictHeadKB()

# multiple values delimiter
KB_MULTIVALUE_DELIM = metrics_knowledge_base.KB_MULTIVALUE_DELIM

def generate_name_alternatives(kb_path):
    if kb_path:
        name_lines = []
        with open(kb_path) as kb:
            for line in kb:
                if line:
                    line = line.strip('\n').split('\t')
                    if not line[0] in ['person', 'person:artist']:
                        continue
                    else:
                        for subtype in headKB['person']:
                            aliases = line[headKB['person'][subtype]['ALIAS']].split(KB_MULTIVALUE_DELIM)
                            aliases.append(line[headKB['person'][subtype]['JMENO']])
                            aliases = (a for a in aliases if a.strip() != "")

                            gender = line[7]

                            for t in aliases:
                                t = re.sub('\s+', ' ', t).strip()
                                unsuitable = ";?!()[]{}<>/~@#$%^&*_=+|\"\\"
                                t = t.strip()
                                for x in unsuitable:
                                    if x in t:
                                        break
                                else:
                                    name_lines.append(t + '\t' + gender)

        for n in name_lines:
            print(n)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--kb_path')
    args = parser.parse_args()

    generate_name_alternatives(args.kb_path)
