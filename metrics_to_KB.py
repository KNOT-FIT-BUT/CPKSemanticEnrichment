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

import metrics_knowledge_base
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
	'-H', '--head-kb',
	help='Header for the knowledge base, which specify its types and their atributes (default: %(default)s).',
	default=metrics_knowledge_base.PATH_HEAD_KB
)
parser.add_argument(
	'-k', '--knowledge-base',
	help='File containing the knowledge base',
	required=True
)

arguments = parser.parse_args()

kb = metrics_knowledge_base.KnowledgeBase(path_to_headkb=arguments.head_kb, path_to_kb=arguments.knowledge_base)
kb.insert_metrics()
print kb
