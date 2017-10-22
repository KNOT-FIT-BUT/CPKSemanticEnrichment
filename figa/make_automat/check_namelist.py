#!/usr/bin/env python3
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

# File:   check_namelist.py
# Author: Peter Hostačný, xhosta03@stud.fit.vutbr.cz
# Date:   25.2.2015

import re
import sys
import codecs
from os.path import isfile
import getopt


################## GLOBAL CONSTANTS ###################
bin_numbers = False
MAX_ERRORS = 10


def print_help():
	''' Print help. '''

	print('''
Author:        Peter Hostacny (xhosta03@stud.fit.vutbr.cz)
Description:   Script controls validity of namelists for fsa_build. There is no guaranty of complete validity, but it can find a lot of bugs. Namelist should be in ASCII format with normal/binary numbers (argument -b for binary numbers).

REQUIRE: Python 3

Examples of correct line:
Entity in namelist|15455;18752
Alle Menschen Br&#xC3BC;der|2067522
Entity|N
Entity2|1578;N
Some entity   |4583

Examples of incorrect line:
Entity on line with missing pipe 2547
Missing number after semicolon|1542;
|1545
Missing number|
N is not at the end|N;5500
utf_char-šč|55554

Usage:   ./check_namelist.py [OPTIONS] [FILES]

Options:
  -h, --help       -> Show this help message and exit.
  -b               -> Namelist with binary numbers.
  -n               -> Maximum number of errors per namelist. [DEFAULT 10]
''')

def process_arguments(args):
	''' Parse arguments from the command line and evaluate them. '''

	global bin_numbers, MAX_ERRORS

	try:
		opts, remaining = getopt.getopt(args[1:], "hbn:", ["help"])
	except getopt.GetoptError as err:
		print(err)
		sys.exit(1)

	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print_help()
			sys.exit(0)
		elif opt in ("-b"): # numbers are in binary form
			bin_numbers = True
		elif opt in ("-n"): # numbers are in binary form
			MAX_ERRORS = int(arg)

	# checking if all entered files exist
	for namelist in remaining:
		if not (isfile(namelist)):
			print("File '" + namelist + "' doesn't exist.")
			sys.exit(2)

	return remaining


def check_it(lines):
	''' argument: list of lines  '''
	result = ""
	error_counter = 0
	counter = 0
	max_chars = 0 # max. length of line in the namelist

	# if there is 'N', it must be at the end of line
	line_pattern = re.compile("^(?P<entity>[^|]+)\|(?P<numbers>[0-9]+(?:;[0-9]+)*(?:;N)?|N)$")
	bin_line_pattern = re.compile(b"^(?P<entity>[^|]+)\|(?P<numbers>.*)$")

	for line in lines:
		if len(line) > max_chars:
			max_chars = len(line)

	for line in lines:
		if error_counter >= MAX_ERRORS:
			result += "### Too many wrong lines. ###\n"
			break

		counter += 1 # counting lines

		if len(line) == 0:
			if counter == len(lines): # if there is empty line at the end of file
				break; # empty line is normal because of splitting byte object creates it
			result += str(counter) + ": " + str(line) + "    # Empty line.\n"
			error_counter += 1
			continue

		# trying to match line with pattern
		if not bin_numbers:	# namelist with numbers in ascii
			match = line_pattern.match(line)
			if not match:
				result += str(counter) + ": " + line + "    # Bad format.\n"
				error_counter += 1
				continue
		else: # numbers are in binary form
			match = bin_line_pattern.match(line)
			if not match:
				result += str(counter) + ": " + str(line) + "    # Bad format.\n"
				error_counter += 1
				continue

		# checking presence of unicode characters (namelist should be coded as ascii)
		try:
			if bin_numbers:
				match.group('entity').decode().encode("ascii")
			else:
				line.encode("ascii")
		except UnicodeEncodeError:
			error_counter += 1
			result += str(counter) + ": " + line +  "    # There is an unicode character in the namelist.\n"

		# binary number is 4 bytes long and there can be byte 'N' at the end of line
		if bin_numbers:
			num_section_length = len(match.group('numbers'))
			if match.group('numbers').endswith(b'N') and num_section_length%4 != 1:
				error_counter += 1
				result += str(counter) + ": " + str(line) +  "    # Error in coding of numbers section\n"
			if not match.group('numbers').endswith(b'N') and num_section_length%4 != 0:
				error_counter += 1
				result += str(counter) + ": " + str(line) +  "    # Error in coding of numbers section\n"

	print("max. lenght of line: " + str(max_chars))
	print("    number of lines: " + str(len(lines)))

	return result



if __name__ == '__main__':

	result = ""
	print()

	namelists = process_arguments(sys.argv)
	if len(namelists) != 0:
		for namelist in namelists: # for every namelist passed through arguments
			print("=====  " + namelist + "  =====")
			if bin_numbers:
				with open(namelist, 'rb') as input_file:
					result = check_it(input_file.read().split(b'\n'))
			else:
				with codecs.open(namelist, 'r', encoding='utf-8') as input_file:
					result = check_it(input_file.read().splitlines())
			print("-----------------------------------")
			if len(result) == 0:
				print("O.K.")
			else:
				sys.stdout.buffer.write(result.encode('utf-8'))
			print()

