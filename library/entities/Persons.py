#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Tomáš Volf, ivolf[at]fit.vutbr.cz

import regex
import library.reUtils as reUtils
from library.config import AutomataVariants
from library.utils import remove_accent


class Persons():
	FORBIDDEN_NAMES = ["Pán", "Paní", "Svatý", "Svatá"]
	LOCATION_PREPOSITIONS = ["z", "ze", "of"]
	LOCATION_PREPOSITIONS_CONJUNCITIONS = ["a", "and"]
	NAME_PREPOSITIONS = ["van der", "van", # Dutch / Flemish
					     "von", "zu",      # Germany
					     "de", "du",       # French
					     "da",             # Italian or Portuguese
					     "di",             # Italian or Spanish
					     "dalla", "del", "dos", "el", "la", "le", "ben", "bin", "y", # http://prirucka.ujc.cas.cz/?id=326
						]
	NAME_PREFIXES = ["d'", "o'"]             # French / Italian / Portuguese / Spanish


	@classmethod
	def get_normalized_subnames(self, src_names, separate_to_names = False, config = AutomataVariants.DEFAULT):
		'''
		From a list of surnames for a given person, it creates a set of all possible surnames variants respecting settings of lowercase / non-accent / ..
		For example:
		   * ["Havel"] => ["Havel"]
		   * ["O'Connor"] => ["O'Connor", "Connor"]
		   * ["van Beethoven"] => ["Ludwig", "Beethoven", "van Beethoven"]
		'''

		if AutomataVariants.isLowercase(config):
			regex_flags = regex.IGNORECASE
		else:
			regex_flags = 0

		# tmp_preposition in the form of "([Vv]an|[Zz]u|..)"
		tmp_prepositions = reUtils.list2FirstIncaseAlternation(self.NAME_PREPOSITIONS)
		regex_prepositions_remove = regex.compile(r" {} ".format(tmp_prepositions))
		regex_prepositions_name = regex.compile(r" {} \p{{Lu}}\p{{L}}+".format(tmp_prepositions), flags=regex_flags)

		# tmp_prefixes in the form og "([Dd]\\'|[Oo]\\'|..)"
		tmp_prefixes = reUtils.list2FirstIncaseAlternation(self.NAME_PREFIXES)
		regex_prefixes_only_check = regex.compile(r"^{}\p{{Lu}}".format(tmp_prefixes), flags=regex_flags)
		regex_prefixes_only = regex.compile(r"^{}".format(tmp_prefixes))

		str_regex_location_remove = r" (?:{}) .*".format("|".join(map(regex.escape, self.LOCATION_PREPOSITIONS)))
		regex_location_remove = regex.compile(str_regex_location_remove, flags=regex_flags)
		regex_name = regex.compile(r"^(?:{})?\p{{Lu}}(\p{{L}}+)?(['-]\p{{Lu}}\p{{L}}+)*(?:{})?$".format(tmp_prefixes, str_regex_location_remove), flags=regex_flags) # this should match only a nice name (must support prefixes)
#		regex_name = regex.compile(r"({})?[A-Z][a-z-']+[a-zA-Z]*[a-z]+".format(tmp_prefixes)) # this should match only a nice name (must support prefixes)

		names = set()

		for name in src_names:
			# normalize whitespaces
			name = regex.sub('\s+', ' ', name)
			subname_location = regex.search(r"([^ ]+" + str_regex_location_remove + r")", name)
			if subname_location:
				subname_location = subname_location.group()
			# remove a part of the name with location information (e.g. " of Polestown" from the name "Richard Butler of Polestown")
			name = regex_location_remove.sub("", name).title()

			if separate_to_names:
				# split the name only (without prepositions) to the parts
				subnames = regex_prepositions_remove.sub(" ", name).split()
			else:
				subnames = [name]

			if subname_location:
				subnames.append(subname_location)

			for subname in subnames:
				if subname[-1] == ",":
					subname = subname[:-1]

				# skip invalid / forbidden names
				if subname not in self.FORBIDDEN_NAMES:
					# normalize name to start with capital, including name with prefix (for example o'... => O'...)
					subname = subname[0].upper() + subname[1:]
					# remove accent, because python re module doesn't support [A-Z] for Unicode
					subname_without_accent = remove_accent(subname)
					result = regex_name.match(subname)
					if result:
						# add non-accent variant (if required) to processing (only if not same as base name)
						for subname in [subname, subname_without_accent] if (AutomataVariants.isNonaccent(config) and subname != subname_without_accent) else [subname]:
							if (AutomataVariants.isLowercase(config)):
								subname = subname.lower()
							names.add(subname)
							if regex.match(regex_prefixes_only_check, subname):
								# add also a variant with small letter starting prefix => "o'Conor"
								if (not subname[0].islower()):
									names.add(subname[0].lower() + subname[1:])

								# from "O'Connor" add also surname only without prefix => "Connor"
								nonprefix = regex_prefixes_only.sub('', subname)
								names.add(nonprefix.lower() if AutomataVariants.isLowercase(config) else nonprefix.capitalize())

			# search for names with preposition, i.e. "van Eyck"
			preposition_name = regex_prepositions_name.search(name.title())
			if preposition_name:
				match = preposition_name.group()

				# normalize name to start with capital, including name with preposition (for example "van Eyck" => "Van Eyck")
				# Warning: contain space on the beginning to avoid match "Ivan Novák" as "van Novák" => it is needed to get substring from second char
				subname = match[1:].title()
				subname_without_accent = remove_accent(subname)

				# add non-accent variant (if required) to processing (only if not same as base name)
				for subname in [subname, subname_without_accent] if (AutomataVariants.isNonaccent(config) and subname != subname_without_accent) else [subname]:
					if (AutomataVariants.isLowercase(config)):
						subname = subname.lower()
					names.add(subname)

					# add also a variant with small letter starting preposition => "van Eyck"
					if (not subname[0].islower()):
						names.add(subname[0].lower() + subname[1:])
		return names

	@classmethod
	def add_to_dictionary_by_config(self, subname, dictionary, config = AutomataVariants.DEFAULT):
		dictionary.add(subname.lower() if AutomataVariants.isLowercase(config) else subname)
