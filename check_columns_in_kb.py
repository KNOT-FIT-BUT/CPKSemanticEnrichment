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
import argparse

parser = argparse.ArgumentParser(
	description = "Check number of columns in the knowledge base reading from standard input against HEAD-KB. Mismatch print to standard error output. Exit 1 when find one or more mismatch."
)
parser.add_argument(
	'-H', '--head-kb',
	help='Header for the knowledge base, which specify its types and their atributes (default: %(default)s).',
	default=metrics_knowledge_base.PATH_HEAD_KB
)
parser.add_argument(
	'--cat',
	action="store_true",
	help='Print standard input to standard output.'
)

arguments = parser.parse_args()

kb_struct = metrics_knowledge_base.KnowledgeBase(path_to_headkb=arguments.head_kb)

kb_is_ok = True
line_num = 0
for line in sys.stdin:
	line_num += 1
	columns = line.rstrip("\n").split("\t")
	ent_head = kb_struct.get_ent_head(columns)
	if len(columns) != len(ent_head):
		sys.stderr.write('Bad line %s in KB: has %s columns, but its entity in HEAD-KB has %s columns.\n' % (line_num, len(columns), len(ent_head)))
		kb_is_ok = False
	if arguments.cat:
		sys.stdout.write(line)

if not kb_is_ok:
	sys.exit(1)

# EOF
