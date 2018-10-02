#!/usr/bin/env python3
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

# Author: Lubomir Otrusina, iotrusina@fit.vutbr.cz
#
# Description: Creates namelist from KB.

import itertools
import argparse
import os
import regex
import sys
from library.config import AutomataVariants
from library.utils import remove_accent
from library.entities.Persons import Persons
from importlib import reload
from natToKB import NatToKB
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import metrics_knowledge_base

reload(sys)

# defining commandline arguments
parser = argparse.ArgumentParser()
parser.add_argument("-l", "--lowercase", action="store_true", help="creates a lowercase list")
parser.add_argument("-a", "--autocomplete", action="store_true", help="creates a list for autocomplete")
parser.add_argument("-u", "--uri", action="store_true", help="creates an uri list")
args = parser.parse_args()

# a dictionary for storing results
dictionary = {}

# automata variants config
atm_config = AutomataVariants.DEFAULT
if args.lowercase:
	atm_config |= AutomataVariants.LOWERCASE
if args.autocomplete:
	atm_config |= AutomataVariants.NONACCENT

# loading KB struct
kb_struct = metrics_knowledge_base.KnowledgeBase()

# multiple values delimiter
KB_MULTIVALUE_DELIM = metrics_knowledge_base.KB_MULTIVALUE_DELIM

def load_name_inflections(cznames_file):
	result = {}

	with open(cznames_file) as f:
		for line in f:
			if line:
				line = line.strip('\n').split('\t')
				name = line[0]
				aliases = line[2].split('|') if line[2] != '' else []
				aliases = [a.split('#')[0] for a in aliases]

				if name not in result:
					result[name] = set()

				for a in aliases:
					result[name].add(a)
	return result

def add_to_dictionary(_key, _value, _type, _fields, alt_names):
	"""
	 Adds the name into the dictionary. For each name it adds also an alternative without accent.

	 _key : the name of a given entity
	 _value : the line number (from the KB) corresponding to a given entity
	 _type : the type of a given entity
	"""

	# removing white spaces
	_key = regex.sub('\s+', ' ', _key).strip()

	# there are no changes for the name from the allow list
	if _key not in allow_list:

		# we don't want names with any of these characters
		unsuitable = ";?!()[]{}<>/~@#$%^&*_=+|\"\\"
		_key = _key.strip()
		for x in unsuitable:
			if x in _key:
				return

		# inspecting names with numbers
		if len(regex.findall(r"[0-9]+", _key)) != 0:
			# we don't want entities containing only numbers
			if len(regex.findall(r"^[0-9 ]+$", _key)) != 0:
				return
			# exception for people or artist name (e.g. John Spencer, 1st Earl Spencer)
			if _type in ["person", "person:artist", "person:fictional"]:
				if len(regex.findall(r"[0-9]+(st|nd|rd|th)", _key)) == 0:
					return
			# we don't want locations with numbers at all
			if _type.startswith("geoplace:"):
				return

		# special filtering for people and artists
		if _type in ["person", "person:artist", "person:fictional"]:
			# we don't want names starting with "List of"
			if _key.startswith("Seznam "):
				return

		# generally, we don't want names starting with low characters
		if _type in ["person", "person:artist", "person:fictional", "event", "organisation"] or _type.startswith('geo'):
			if len(regex.findall(r"^\p{Ll}+", _key)) != 0:
				return

		# filtering out all names with length smaller than 2 and greater than 80 characters
		if len(_key) < 2 or len(_key) > 80:
			return

		# filtering out names ending by ., characters
		if _type not in ["person", "person:artist", "person:fictional"]:
			if len(regex.findall(r"[.,]$", _key)) != 0:
				return

	# adding name into the dictionary
	add(_key, _value, _type)

	# generating permutations for person and artist names
	if _type in ["person", "person:artist", "person:fictional"]:
		length = _key.count(" ") + 1
		if length <= 4 and length > 1:
			parts = _key.split(" ")
			# if a name contains any of these words, we will not create permutations
			if not (set(parts) & set(["van", "von"])):
				names = list(itertools.permutations(parts))
				for x in names:
					r = " ".join(x)
					add(_key, _value, _type)

		alternatives = None
		if _key in alt_names:
			alternatives = alt_names[_key]

		if alternatives:
			for a in alternatives:
				add(a, _value, _type)

	# adding various alternatives for given types
	if _type in ["person", "person:artist", "person:fictional", 'organisation'] or _type.startswith('geo'):
		if "Svatý " in _key:
			add(regex.sub(r"Svatý ", "Sv. ", _key), _value, _type) # Saint John -> Sv. John
			add(regex.sub(r"Svatý ", "Sv.", _key), _value, _type) # Saint John -> Sv.John
			add(regex.sub(r"Svatý ", "Sv ", _key), _value, _type) # Saint John -> Sv John
		if "Sv " in _key:
			add(regex.sub(r"Sv ", "Sv. ", _key), _value, _type) # St John -> St. John
			add(regex.sub(r"Sv ", "Sv.", _key), _value, _type) # St John -> St.John
			add(regex.sub(r"Sv ", "Svatý ", _key), _value, _type) # St John -> Saint John
		if "Sv." in _key:
			if "Sv. " in _key:
				add(regex.sub(r"Sv\. ", "Sv ", _key), _value, _type) # St. John -> St John
				add(regex.sub(r"Sv\. ", "Sv.", _key), _value, _type) # St. John -> St.John
				add(regex.sub(r"Sv\. ", "Svatý ", _key), _value, _type) # St. John -> Saint John
			else:
				add(regex.sub(r"Sv\.", "Sv ", _key), _value, _type) # St.John -> St John
				add(regex.sub(r"Sv\.", "Sv. ", _key), _value, _type) # St.John -> St. John
				add(regex.sub(r"Sv\.", "Svatý ", _key), _value, _type) # St.John -> Saint John

	if _type in ["person", "person:artist", "person:fictional"]:
		add(regex.sub(r"(\p{Lu})\p{Ll}* (\p{Lu}\p{Ll}*)", "\g<1>. \g<2>", _key), _value, _type) # Adolf Born -> A. Born
		add(regex.sub(r"(\p{Lu})\p{Ll}* (\p{Lu})\p{Ll}* (\p{Lu}\p{Ll}*)", "\g<1>. \g<2>. \g<3>", _key), _value, _type) # Peter Paul Rubens -> P. P. Rubens
		add(regex.sub(r"(\p{Lu}\p{Ll}*) (\p{Lu})\p{Ll}* (\p{Lu}\p{Ll}*)", "\g<1> \g<2>. \g<3>", _key), _value, _type) # Peter Paul Rubens -> Peter P. Rubens
		if "Mc" in _key:
			add(regex.sub(r"Mc(\p{Lu})", "Mc \g<1>", _key), _value, _type) # McCollum -> Mc Collum
			add(regex.sub(r"Mc (\p{Lu})", "Mc\g<1>", _key), _value, _type) # Mc Collum -> McCollum
		if "." in _key:
			new_key = regex.sub(r"(\p{Lu})\. (?=\p{Lu})", "\g<1>.", _key) # J. M. W. Turner -> J.M.W.Turner
			add(new_key, _value, _type)
			new_key = regex.sub(r"(\p{Lu})\.(?=\p{Lu}\p{Ll}+)", "\g<1>. ", new_key) # J.M.W.Turner -> J.M.W. Turner
			add(new_key, _value, _type)
			add(regex.sub(r"\.", "", new_key), _value, _type) # J.M.W. Turner -> JMW Turner
		if "-" in _key:
			add(regex.sub(r"\-", " ", _key), _value, _type) # Payne-John Christo -> Payne John Christo
		if "ì" in _key:
			add(regex.sub("ì", "í", _key), _value, _type) # Melozzo da Forlì -> Melozzo da Forlí

		parts = _key.split(" ")
		# if a name contains any of these words, we will not create permutations
		if not (set(parts) & set(["von", "van"])):
			for x in f_name:
				if x in _key:
					new_key = regex.sub(' ?,? ' + x + '$', '', _key) # John Brown, Jr. -> John Brown
					new_key = regex.sub('^' + x + ' ', '', new_key) # Sir Patrick Stewart -> Patrick Stewart
					if new_key.count(' ') >= 1:
						add(new_key, _value, _type)

	if _type in ["settlement", "watercourse"]:
		description = kb_struct.get_data_for(_fields, 'DESCRIPTION')
		if _key in description:
			if _type == 'settlement':
				country = kb_struct.get_data_for(_fields, 'COUNTRY')
			elif _type == 'watercourse':
				country = kb_struct.get_data_for(_fields, 'SOURCE_LOC')
			if country and country not in _key:
				add(_key + ", " + country, _value, _type) # Peking -> Peking, China
				add(regex.sub("United States", "US", _key + ", " + country), _value, _type)

	#if _type in ["event"]:
	#	if len(regex.findall(r"^[0-9]{4} (Summer|Winter) Olympics$", _key)) != 0:
	#		location = kb_struct.get_data_for(_fields, 'LOCATION')
	#		year = kb_struct.get_data_for(_fields, 'START DATE')[:4]
	#		if year and location and "|" not in location:
	#			add("Olympics in " + location + " in " + year, _value, _type) # 1928 Summer Olympics -> Olympics in Amsterdam in 1928
	#			add("Olympics in " + year + " in " + location, _value, _type) # 1928 Summer Olympics -> Olympics in 1928 in Amsterdam
	#			add("Olympic Games in " + location + " in " + year, _value, _type) # 1928 Summer Olympics -> Olympic Games in Amsterdam in 1928
	#			add("Olympic Games in " + year + " in " + location, _value, _type) # 1928 Summer Olympics -> Olympic Games in 1928 in Amsterdam

	#if _type in ["geoplace:populatedPlace", 'geoplace:mountain', 'geoplace:castle', 'geoplace:lake', 'geo:mountainRange', 'geoplace:observationTower', 'geoplace:waterfall']:
	#	description = kb_struct.get_data_for(_fields, 'DESCRIPTION')
	#	if _key in description:
	#		if _type == 'geoplace:populatedPlace':
	#			country = kb_struct.get_data_for(_fields, 'LOCATION')
	#		else:
	#			country = kb_struct.get_data_for(_fields, 'COUNTRY')
	#		if country not in _key:
	#			add(_key + ", " + country, _value, _type) # Peking -> Peking, China
	#			add(regex.sub("United States", "US", _key + ", " + country), _value, _type)

def add(_key, _value, _type):
	"""
	 Adds the name into the dictionary. For each name it adds also an alternative without accent.

	 _key : the name
	 _value : the line number (from the KB) corresponding to a given entity
	 _type : the type prefix for a given entity
	"""

	# disabling of some types (because the size of automaton exceeds 256MB and automaton is unstable)
#	if _type in ["mythology", "family", "group", "event", "museum"] and not args.autocomplete:
	if _type in ["mythology", "family", "group", "museum"] and not args.autocomplete:
		return

	_key = _key.strip()

	if args.autocomplete:
		_key = remove_accent(_key.lower())

	if args.lowercase:
		_key = _key.lower()

	# removing entities that begin with '-. or space
	if len(regex.findall(r"^[ '-\.]", _key)) != 0:
		return

	# adding the type-specific prefix to begining of the name
	if args.autocomplete:
		_key = _type+":\t"+_key

	# adding the name into the dictionary
	if _key not in dictionary:
		dictionary[_key] = set()
	dictionary[_key].add(_value)

	# removing accent
#	_accent = remove_accent(_key)

	# adding the name without accent into the dictionary
#	if _accent not in dictionary:
#		dictionary[_accent] = set()
#	dictionary[_accent].add(_value)

SURNAME_MATCH = regex.compile(r"(((?<=^)|(?<=[ ]))(da |von )?((\p{Lu}\p{Ll}*-)?(\p{Lu}\p{Ll}+))$)")
UNWANTED_MATCH = regex.compile(r"(Princ|Svatý|,|z|[0-9])")

def process_person(_fields, _line_num, alt_names):
	""" Processes a line with entity of person type. """

	aliases = kb_struct.get_data_for(_fields, 'ALIASES').split(KB_MULTIVALUE_DELIM)
	aliases.append(kb_struct.get_data_for(_fields, 'NAME'))
	aliases = (a for a in aliases if a.strip() != "")

	name = kb_struct.get_data_for(_fields, 'NAME')
	confidence = float(kb_struct.get_data_for(_fields, 'CONFIDENCE'))

	CONFIDENCE_THRESHOLD = 20

	for t in aliases:
		length = t.count(" ") + 1
		if length >= 2 or confidence >= CONFIDENCE_THRESHOLD:
			add_to_dictionary(t, _line_num, "person", _fields, alt_names)

#	if confidence >= CONFIDENCE_THRESHOLD:
#		surname_match = SURNAME_MATCH.search(name)
#		unwanted_match = UNWANTED_MATCH.search(name)
#		if surname_match and not unwanted_match:
#			surname = surname_match.group(0)
#			add_to_dictionary(surname, _line_num, "person", _fields, alt_names)

def process_artist(_fields, _line_num, alt_names):
	""" Processes a line with entity of artist type. """

	aliases = kb_struct.get_data_for(_fields, 'ALIASES').split(KB_MULTIVALUE_DELIM)
	aliases.append(kb_struct.get_data_for(_fields, 'NAME'))
	aliases = (a for a in aliases if a.strip() != "")

	name = kb_struct.get_data_for(_fields, 'NAME')
	confidence = float(kb_struct.get_data_for(_fields, 'CONFIDENCE'))
	surname = ""

	CONFIDENCE_THRESHOLD = 15

	for t in aliases:
		length = t.count(" ") + 1
		if length >= 2 or confidence >= CONFIDENCE_THRESHOLD:
			add_to_dictionary(t, _line_num, "person:artist", _fields, alt_names)

def process_fictional(_fields, _line_num, alt_names):
	""" Processes a line with entity of person:fictional type. """

	aliases = kb_struct.get_data_for(_fields, 'ALIASES').split(KB_MULTIVALUE_DELIM)
	aliases.append(kb_struct.get_data_for(_fields, 'NAME'))
	aliases = (a for a in aliases if a.strip() != "")

	name = kb_struct.get_data_for(_fields, 'NAME')
	confidence = float(kb_struct.get_data_for(_fields, 'CONFIDENCE'))
	surname = ""

	CONFIDENCE_THRESHOLD = 15

	for t in aliases:
		length = t.count(" ") + 1
		if length >= 2 or confidence >= CONFIDENCE_THRESHOLD:
			add_to_dictionary(t, _line_num, "person:fictional", _fields, alt_names)

#	if confidence >= CONFIDENCE_THRESHOLD:
#		surname_match = SURNAME_MATCH.search(name)
#		unwanted_match = UNWANTED_MATCH.search(name)
#		if surname_match and not unwanted_match:
#			surname = surname_match.group(0)
#			add_to_dictionary(surname, _line_num, "person:artist", _fields, alt_names)

def process_other(_fields, _line_num, alt_names):
	""" Processes a line with entity of location type. """

	aliases = kb_struct.get_data_for(_fields, 'ALIASES').split(KB_MULTIVALUE_DELIM)
	aliases.append(kb_struct.get_data_for(_fields, 'NAME'))
	for t in aliases:
		add_to_dictionary(t, _line_num, _fields[1], _fields, alt_names)

def process_location(_fields, _line_num):
	""" Processes a line with entity of location type. """

	aliases = kb_struct.get_data_for(_fields, 'ALIASES').split(KB_MULTIVALUE_DELIM)
	aliases.append(kb_struct.get_data_for(_fields, 'NAME'))
	for t in aliases:
		add_to_dictionary(t, _line_num, "location", _fields)

def process_artwork(_fields, _line_num):
	""" Processes a line with entity of artwork type. """

	aliases = kb_struct.get_data_for(_fields, 'ALIASES').split(KB_MULTIVALUE_DELIM)
	aliases.append(kb_struct.get_data_for(_fields, 'NAME'))
	for t in aliases:
		add_to_dictionary(t, _line_num, "artwork", _fields)

def process_museum(_fields, _line_num):
	""" Processes a line with entity of museum type. """

	aliases = kb_struct.get_data_for(_fields, 'ALIASES').split(KB_MULTIVALUE_DELIM)
	aliases.append(kb_struct.get_data_for(_fields, 'NAME'))
	for t in aliases:
		add_to_dictionary(t, _line_num, "museum", _fields)

def process_fieldsvent(_fields, _line_num):
	""" Processes a line with entity of event type. """

	aliases = kb_struct.get_data_for(_fields, 'ALIASES').split(KB_MULTIVALUE_DELIM)
	aliases.append(kb_struct.get_data_for(_fields, 'NAME'))
	for t in aliases:
		add_to_dictionary(t, _line_num, "event", _fields)

def process_visual_art_form(_fields, _line_num):
	""" Processes a line with entity of visual_art_form type. """

	aliases = kb_struct.get_data_for(_fields, 'ALIASES').split(KB_MULTIVALUE_DELIM)
	aliases.append(kb_struct.get_data_for(_fields, 'NAME'))
	for t in aliases:
		add_to_dictionary(t, _line_num, "visual_art_form", _fields)

def process_visual_art_medium(_fields, _line_num):
	""" Processes a line with entity of visual_art_medium type. """

	aliases = kb_struct.get_data_for(_fields, 'ALIASES').split(KB_MULTIVALUE_DELIM)
	aliases.append(kb_struct.get_data_for(_fields, 'NAME'))
	for t in aliases:
		add_to_dictionary(t, _line_num, "visual_art_medium", _fields)

def process_visual_art_genre(_fields, _line_num):
	""" Processes a line with entity of visual_art_genre type. """

	aliases = kb_struct.get_data_for(_fields, 'ALIASES').split(KB_MULTIVALUE_DELIM)
	aliases.append(kb_struct.get_data_for(_fields, 'NAME'))
	for t in aliases:
		add_to_dictionary(t, _line_num, "visual_art_genre", _fields)

def process_art_period_movement(_fields, _line_num):
	""" Processes a line with entity of art_period_movement type. """

	aliases = kb_struct.get_data_for(_fields, 'ALIASES').split(KB_MULTIVALUE_DELIM)
	aliases.append(kb_struct.get_data_for(_fields, 'NAME'))
	for t in aliases:
		add_to_dictionary(t, _line_num, "art_period_movement", _fields)

def process_nationality(_fields, _line_num):
	""" Processes a line with entity of nationalities type. """

	aliases = kb_struct.get_data_for(_fields, 'ADJECTIVAL FORM').split(KB_MULTIVALUE_DELIM)
	for t in aliases:
		add_to_dictionary(t, _line_num, "nationality", _fields)

def process_mythology(_fields, _line_num):
	""" Processes a line with entity of mythology type. """

	aliases = kb_struct.get_data_for(_fields, 'ALIASES').split(KB_MULTIVALUE_DELIM)
	aliases.append(kb_struct.get_data_for(_fields, 'NAME'))
	for t in aliases:
		length = t.count(" ") + 1
		if length >= 2 or t == kb_struct.get_data_for(_fields, 'NAME'):
			add_to_dictionary(t, _line_num, "mythology", _fields)

def process_family(_fields, _line_num):
	""" Processes a line with entity of family type. """

	aliases = kb_struct.get_data_for(_fields, 'ALIASES').split(KB_MULTIVALUE_DELIM)
	aliases.append(kb_struct.get_data_for(_fields, 'NAME'))
	for t in aliases:
		add_to_dictionary(t, _line_num, "family", _fields)

def process_group(_fields, _line_num):
	""" Processes a line with entity of group type. """

	aliases = kb_struct.get_data_for(_fields, 'ALIASES').split(KB_MULTIVALUE_DELIM)
	aliases.append(kb_struct.get_data_for(_fields, 'NAME'))
	for t in aliases:
		add_to_dictionary(t, _line_num, "group", _fields)

def process_uri(_fields, _line_num):
	""" Processes all URIs for a given entry. """

	entity_head = kb_struct.get_ent_head(_fields)

	uris = []
	if 'WIKIPEDIA URL' in entity_head:
		uris.append(kb_struct.get_data_for(_fields, 'WIKIPEDIA URL'))
	if 'DBPEDIA URL' in entity_head:
		uris.append(kb_struct.get_data_for(_fields, 'DBPEDIA URL'))
	if 'FREEBASE URL' in entity_head:
		uris.append(kb_struct.get_data_for(_fields, 'FREEBASE URL'))
	if 'OTHER URL' in entity_head:
		uris.extend(kb_struct.get_data_for(_fields, 'OTHER URL').split(KB_MULTIVALUE_DELIM))
	uris = [u for u in uris if u.strip() != ""]

	for u in uris:
		if u not in dictionary:
			dictionary[u] = set()
		dictionary[u].add(_line_num)

if __name__ == "__main__":

	if args.uri:
		# processing the KB
		line_num = 1
		for l in sys.stdin:
			fields = l[:-1].split("\t")
			process_uri(fields, str(line_num))
			line_num += 1

	else:
		# loading the list of titles, degrees etc. (earl, sir, king, baron, ...)
		with open("freq_terms_filtred.all") as f_file:
			f_name = f_file.read().splitlines()

		# loading the allow list (these names will be definitely in the namelist)
		with open("allow_list") as allow_file:
			allow_list = allow_file.read().splitlines()

		# loading the list of first names
		with open("yob2012.txt") as firstname_file:
			firstname_list = firstname_file.read().splitlines()

		# loading the list of all nationalities
		with open("nationalities.txt") as nationality_file:
			nationality_list = nationality_file.read().splitlines()

		# load version number (string) of KB
		with open("../../VERSION") as kb_version_file:
			kb_version = kb_version_file.read().strip()

		alternatives = load_name_inflections('czechnames_' + kb_version + '.out')

		# processing the KB
		line_num = 1
		for l in sys.stdin:
			fields = l[:-1].split("\t")
			ent_type = kb_struct.get_ent_type(fields)

			if ent_type == "person:fictional":
				process_fictional(fields, str(line_num), alternatives)
			elif ent_type == "person:artist":
				process_artist(fields, str(line_num), alternatives)
			elif ent_type == "person":
				process_person(fields, str(line_num), alternatives)
			else:
				process_other(fields, str(line_num), alternatives)
			'''
			elif ent_type == "location":
				process_location(fields, str(line_num))
			elif ent_type == "artwork":
				process_artwork(fields, str(line_num))
			elif ent_type == "event":
				process_fieldsvent(fields, str(line_num))
			elif ent_type == "visual_art_form":
				process_visual_art_form(fields, str(line_num))
			elif ent_type == "visual_art_genre":
				process_visual_art_genre(fields, str(line_num))
			elif ent_type == "art_period_movement":
				process_art_period_movement(fields, str(line_num))
			elif ent_type == "visual_art_medium":
				process_visual_art_medium(fields, str(line_num))
			elif ent_type == "nationality":
				process_nationality(fields, str(line_num))
			elif ent_type == "museum":
				process_museum(fields, str(line_num))
			elif ent_type == "mythology":
				process_mythology(fields, str(line_num))
			elif ent_type == "family":
				process_family(fields, str(line_num))
			elif ent_type == "group":
				process_group(fields, str(line_num))
			'''
			line_num += 1

		# Subnames in all inflections with 'N'
		subnames = set()
		for base, inflections in alternatives.items():
			inflections.add(base)
			for subname in Persons.get_subnames(inflections, atm_config):
				if subname not in dictionary:
					dictionary[subname] = set()
					dictionary[subname].add('N')

		# Pronouns with first lower and first upper with 'N'
		pronouns = ["on", "ho", "mu", "něm", "jím", "ona", "jí", "ní"]
		if (not args.lowercase):
			pronouns += [pronoun.capitalize() for pronoun in pronouns]
		if (args.autocomplete):
			pronouns += [remove_accent(pronoun) for pronoun in pronouns]
		dictionary.update(dict.fromkeys(pronouns, 'N'))

	# geting nationalities
	ntokb = NatToKB()
	nationalities = ntokb.get_nationalities()
	for nat in nationalities:
		if nat not in dictionary:
			dictionary[nat] = set()
		dictionary[nat].add('N')

	# printing the output
	for item in dictionary.items():
		print(item[0] + "\t" + ";".join(item[1]))
