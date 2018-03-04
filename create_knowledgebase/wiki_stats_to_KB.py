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

with open("./data/in/wiki_stats_cs.tsv") as wiki_stats:
    stats = dict()
    for line in wiki_stats:
        items = line[:-1].split("\t")
        url = "http://cs.wikipedia.org/wiki/" + items[0]
        stats[url] = items[1:]

found = 0
not_found = 0

with open("./data/in/KBbasic_cs.tsv") as kb:
    for line in kb:
        split_line = line[:-1].split("\t")
        ent_type = split_line[0]
        
        if ent_type in metrics_knowledge_base.KnowledgeBase.wiki_link_column:
            index = metrics_knowledge_base.KnowledgeBase.wiki_link_column[ent_type]
        else:
            sys.stdout.write(line.strip('\n') + "\t\t\t\n")
            continue

        if index >= len(split_line):
            sys.stderr.write("ERROR: There is no column " + str(index + 1) + " in row " + line + ".\n")
            exit(99)

        link = split_line[index]
        
        if link in stats:
            sys.stdout.write(line.strip('\n') + '\t' + stats[link][0] + '\t' + stats[link][1] + '\t' + stats[link][2] + '\n')
            found += 1
        else:
            sys.stdout.write(line.strip('\n') + "\t\t\t\n")
            if link:
                not_found += 1
