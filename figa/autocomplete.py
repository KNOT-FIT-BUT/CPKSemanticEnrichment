#!/usr/bin/env python
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

# File: autocomplete.py
# Author: Peter Hostačný, xhosta03@stud.fit.vutbr.cz


import sys
import os
import unicodedata
import sources.marker as figa
from os.path import isfile
import getopt
#from array import *

#######################################################



################## GLOBAL CONSTANTS ###################
return_all_entites = False
input_file = ""
#statistics = ""


reload(sys)
sys.setdefaultencoding("utf-8")


def to_remove_accent(input_str):
		nkfd_form = unicodedata.normalize('NFKD', unicode(input_str))
		return str("".join([c for c in nkfd_form if not unicodedata.combining(c)]))


def print_help():
	''' Print help. '''

	print'''
Name:      Autocomplete
Author:    Peter Hostacny (xhosta03@stud.fit.vutbr.cz)

Usage:   ./autocomplete.py [OPTIONS]

Options:
  -a, --return-all     -> Return all possible entities.
  -d dictionary        -> Automaton file (multiple files allowed).
  -f FILE              -> Input file.
  -h, --help           -> Show this help message and exit.
  -l, --lowercase      -> Convert input to lowercase.
  -m NUMBER            -> Define number of returned entities (default value is 5).
  -r, --remove-accent  -> Remove accent from input.
'''


		
def process_arguments(args):
	''' Parse arguments from the command line and evaluate them. '''

	dictionary_defined = False
	count = 5
	global return_all_entites
	global input_file
	#global statistics

	remove_accent = False
	lowercase = False

	try:
		opts, remaining = getopt.getopt(args[1:], "hrald:f:m:", ["help"])
	except getopt.GetoptError as err:
		print(err)
		sys.exit(1)
	if len(remaining) != 0:
		sys.stderr.write("Unrecognized option: '" + str(remaining[0]) + "'\n")
		sys.exit(1)

	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print_help()
			sys.exit(0)
		if opt in ("-d"):
			if not (isfile(arg)):
				print("File '" + arg + "' doesn't exist.")
				sys.exit(2)
			dictionary_defined = True
			dictionary = os.getcwd() + "/" + arg
		"""
		if opt in ("-s", "--sort"):
			if not (isfile(arg)):
				print("File '" + arg + "' doesn't exist.")
				sys.exit(2)
			statistics = arg
		"""
		if opt in ("-f"):
			if not (isfile(arg)):
				print("File '" + arg + "' doesn't exist.")
				sys.exit(2)
			input_file = arg
		if opt in ("-a", "--return-all"):
			return_all_entites = True
		if opt in ("-m"):
			try:
				count = int(arg)
			except ValueError:
				sys.stderr.write("'" + str(arg) + "' is not an integer.\n")
				sys.exit(3)
		if opt in ("-r", "--remove-accent"):
			remove_accent = True
		if opt in ("-l", "--lowercase"):
			lowercase = True

	if not dictionary_defined:
		sys.stderr.write("You must define a dictionary file. Try option '--help' for more information.\n")
		sys.exit(2)
#sys.stderr.write("Wrong arguments. Try option '--help' for more information.\n")
	return count, dictionary, remove_accent, lowercase



def autocomplete(dictionary, input_str, max_entity_count=5, remove_accent=False, lowercase=False, lang_file=None, return_all=False):
	''' Find entities in automata and return them as string. '''

	if max_entity_count <= 0 or max_entity_count > 300000:
		sys.stderr.write(__file__ + ": max_entity_count must be in the range 0 < x <= 300000\n")
		return

        seek_names = figa.marker(True, False, True, max_entity_count, return_all)
        seek_names.load_dict(dictionary)

	if remove_accent:
		input_str = to_remove_accent(input_str)

	if lowercase:
		input_str = input_str.lower()

	return seek_names.auto_lookup_string(input_str)


###################################################################
###################################################################
###################################################################


if __name__ == '__main__':

	dictionary = None
	count, dictionary, remove_accent, lowercase = process_arguments(sys.argv)

	#confidence = array('L', [0])

	if input_file:
		f = open(input_file, 'r')
		input_str = f.read()
	else:
		input_str = sys.stdin.read()

	#print len(input_str)

	output = autocomplete(dictionary, input_str, count, remove_accent, lowercase, None, return_all_entites)

	"""
	if statistics:
		file_stats = open(statistics, "r")
		stats = file_stats.read().splitlines()
		for line in stats:
			try:
				confidence.append(int(line)) # confidence = posledny stlpec
			except ValueError:
				# v pripade spatneho formatu confidence hodnoty v KBstatsMetrics.all
				confidence.append(0)
		file_stats.close()

		output_dict = dict()

		for line in output.splitlines():
			line_numbers = map(int, line.split("\t")[1].split(";"))
			conf_number = max([confidence[num] for num in line_numbers])
			# vytvorenie slovnika {entita : confidence}
			output_dict[line] = conf_number

		output = ""
		# zoradenie cisel v slovniku podla hodnot confidence
		for entity in sorted(output_dict, key=output_dict.get, reverse=True):
			# pridanie klucov slovnika (cisel riadkov) v poradi hodnot confidence
			output += entity + "\n"
	"""

	try:
		if (isinstance(output, basestring)):
			sys.stdout.write(output)   # vypis vysledku
			sys.stdout.flush()
	except IOError: # osetrenie kvoli padom pri presmerovani vystupu do utility head
		# stdout is closed, no point in continuing
		# Attempt to close them explicitly to prevent cleanup problems:
		try:
			sys.stdout.close()
		except IOError:
			pass
		try:
			sys.stderr.close()
		except IOError:
			pass
