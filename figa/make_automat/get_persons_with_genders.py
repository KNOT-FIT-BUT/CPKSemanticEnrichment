import argparse
import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import metrics_knowledge_base
reload(sys)
sys.setdefaultencoding("utf-8")

# loading KB struct
kb_struct = metrics_knowledge_base.KnowledgeBase()

# multiple values delimiter
KB_MULTIVALUE_DELIM = metrics_knowledge_base.KB_MULTIVALUE_DELIM

def generate_name_alternatives(kb_path):
    if kb_path:
        name_lines = []
        with open(kb_path) as kb:
            for line in kb:
                if line:
                    line = line.strip('\n').split('\t')
                    if kb_struct.get_ent_type(line) not in ['person', 'person:artist', 'person:fictional']:
                        continue
                    else:
                        aliases = kb_struct.get_data_for(line, 'ALIASES').split(KB_MULTIVALUE_DELIM)
                        aliases.append(kb_struct.get_data_for(line, 'NAME'))
                        aliases = (a for a in aliases if a.strip() != "")

                        gender = kb_struct.get_data_for(line, 'GENDER')

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
