#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright 2014 Brno University of Technology

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
import re

filename = "HEAD-KB"

'''
VISUAL ARTIST (prefix: p)
==========================================
ID
TYPE
blah blah (MULTIPLE VALUES)
'''

def generate(text):
	result = []
	type_and_prefix = re.compile("^\s*(\w(?:\w|\s)*\w) \(\s*prefix:\s*(\w)\s*\)\s*$")
	attributes = re.compile("^\s*(\w(?:\w|\s)*\w)(?: \(\s*(?:(MULTIPLE\s*VALUES)|(?:NULLABLE))\s*\))?\s*$")
	url = re.compile('(?:^|\s)URL(?:$|\s)')
	date = re.compile('(?:^|\s)DATE(?:$|\s)')
	
	text_split = text.split("\n")
	find = type_and_prefix.search( text_split.pop(0) )
	text_split.pop(0)
	
	result += [find.group(2) +":"+ find.group(1) +":"+ attributes.search( text_split.pop(0) ).group(1)]
	
	for line in text_split:
		if line != "":
			found = attributes.search( line )
			if found and found.group(1):
				typified = ""
				address_prefix = ""
				delimiter = ""
				if found.group(1) == "IMAGE":
					typified += "g"
					address_prefix = "[http://athena3.fit.vutbr.cz/kb/images/freebase/]"
				elif date.search( found.group(1) ):
					typified += "e"
				elif url.search( found.group(1) ):
					typified += "ui"
				
				if found.group(2):
					typified += "m"
				
				if (typified) or (address_prefix):
					delimiter = ":"
				
				result += [ typified + address_prefix + delimiter + found.group(1) ]
	
	return result
#

if __name__ == "__main__":
	result = []
	text = ""
	line = sys.stdin.readline()
	
	while line != "":
		while line != "\n":
			text += line
			line = sys.stdin.readline()
		if text == "":
			line = sys.stdin.readline()
			continue
		result += [generate(text)]
		text = ""
		line = sys.stdin.readline()
	
	output = open(filename, 'w')
	for header in result:
		output.write( header.pop(0) )
		for item in header:
			output.write("\t")
			output.write(item)
		output.write("\n")
	output.write("\n")
	output.close()
	
	sys.exit(0)
#

# konec souboru generator.py
