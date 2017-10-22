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

# Author: Lubomír Otrusina, iotrusina@fit.vutbr.cz
#
# Description: Generates various morphological forms of a given word.

import sys, os
from pattern.en import pluralize, singularize
from pattern.en import conjugate, lemma, lexeme

for line in sys.stdin:
	word = line.strip()
	print word
	#print pluralize(word)
	#print singularize(word)
	#print conjugate(word, 'inf')
	#print conjugate(word, '1sg')
	#print conjugate(word, '2sg')
	#print conjugate(word, '3sg')
	#print conjugate(word, 'pl')
	#print conjugate(word, 'part')
	#print conjugate(word, 'p')
	#print conjugate(word, '1sgp')
	#print conjugate(word, '2sgp')
	#print conjugate(word, '3gp')
	#print conjugate(word, 'ppl')
	#print conjugate(word, 'ppart')
