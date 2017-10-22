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

# Author: Peter Hostačný, xhosta03@stud.fit.vutbr.cz
# Author: Lubomir Otrusina, iotrusina@fit.vutbr.cz
#
# Description: Sorts and uniques namelist from KB.

import argparse
import sys
from array import *

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--statistics", help="sorting line numbers by confidence score")
args = parser.parse_args()

STOP_LIST = set()

try:
	with open("stop_list.all.sorted") as stop_list:
		STOP_LIST = stop_list.read().splitlines()
except IOError:
	pass

if __name__ == "__main__":
	dictionary = {}

	for line in sys.stdin:
		split_line = line[:-1].split("\t")
		if split_line[0] not in dictionary:
			dictionary[split_line[0]] = set()
		dictionary[split_line[0]] |= set(split_line[1].split(";"))

	confidence = array('L', [0])

	if args.statistics:
		with open(args.statistics) as file_stats:
			stats = file_stats.read().splitlines()
		for line in stats:
			try:
				# the confidence score is in a last column
				confidence.append(int(line))
			except ValueError:
				# the confidence score has a wrong format
				confidence.append(0)

		for k in sorted(dictionary.keys()):
			N_removed = False;
			sorted_ids = []

			try:
				# converts string to integer
				ids = map(int, dictionary[k])
			except ValueError:
				# there is a fragment (value "N")
				ids = list(dictionary[k])
				# there are also other values except value "N"
				if len(ids) > 1:
					if "N" in ids:
						ids.remove("N")
						# value "N" was in the list
						N_removed = True
					# converts string to integer
					ids = map(int, ids)
				else:
					print k+ "\t" + "N"
					continue

			# creates a dictionary {line_number : confidence_score}
			ids = dict([(line, conf) for line in ids for conf in [confidence[line]]])

			# sorts dictionary according the confidence score
			for line_number in sorted(ids, key=ids.get, reverse=True):
				# filling the dictionary
				sorted_ids.append(line_number)

			# converts id to string
			sorted_ids = map(str, sorted_ids)

			if N_removed:
				# adding deleted value "N"
				sorted_ids.append("N")

			# output format "Entity[\t]12345;12346;N"
			if k not in STOP_LIST:
				print k + "\t" + ";".join(sorted_ids)
			elif "N" in sorted_ids:
				print k + "\t" + "N"
	else:
		for k in sorted(dictionary.keys()):
			ids = sorted(dictionary[k])
			if k not in STOP_LIST:
				print k + "\t" + ";".join(ids)
			elif "N" in ids:
				print k + "\t" + "N"

