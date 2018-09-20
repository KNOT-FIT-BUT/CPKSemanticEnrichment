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
        items = line.rstrip("\n").split("\t")
        url = "https://cs.wikipedia.org/wiki/" + items[0]
        stats[url] = items[1:]

found = 0
not_found = 0

kb_struct = metrics_knowledge_base.KnowledgeBase()

for line in sys.stdin:
    columns = line.rstrip("\n").split("\t")
    
    link = kb_struct.get_data_for(columns, "WIKIPEDIA LINK")
    if link and link in stats:
        columns[kb_struct.get_col_for(columns, "WIKI BACKLINKS")] = stats[link][0]
        columns[kb_struct.get_col_for(columns, "WIKI HITS")] = stats[link][1]
        columns[kb_struct.get_col_for(columns, "WIKI PRIMARY SENSE")] = stats[link][2]
        sys.stdout.write("\t".join(columns) + "\n")
        found += 1
    else:
        sys.stdout.write(line)
        if link:
            not_found += 1
