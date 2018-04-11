#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2015 Brno University of Technology

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import sys
import metrics_knowledge_base


with open("wiki_stats") as wiki_stats:
    stats = dict()
    for line in wiki_stats:
        items = line[:-1].split("\t")
        name = items[0]
        stats[name] = items[1:]

found = 0
not_found = 0



with open("kb_cs") as kb:
    for line in kb:
        split_line = line.split("\t")

        ent_type = split_line[1]

        if ent_type in metrics_knowledge_base.KnowledgeBase.wiki_link_column:
            index = metrics_knowledge_base.KnowledgeBase.wiki_link_column[ent_type]
        else:
            sys.stdout.write(line.strip('\n') + "\t\t\t\n")
            continue

        if index > len(split_line):
            sys.stderr.write("ERROR: There is no column " + str(index + 1) + " in row " + line + ".\n")
            continue
            exit(99)

        name = split_line[index-1].replace(" ", "_")

        if name in stats:
            sys.stdout.write(line.strip('\n') + '\t' + stats[name][0] + '\t' + stats[name][1] + '\t' + stats[name][2] + '\n')
            found += 1
        else:
            sys.stdout.write(line.strip('\n') + "\t\t\t\n")
            if name:
                not_found += 1
