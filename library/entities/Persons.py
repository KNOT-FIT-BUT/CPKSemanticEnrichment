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
	NAME_PREPOSITIONS = ["van der", "van", # Dutch / Flemish
					     "von", "zu",      # Germany
					     "de", "du",       # French
					     "da",             # Italian or Portuguese
					     "di",             # Italian or Spanish
					     "dalla", "del", "dos", "el", "la", "le", "ben", "bin", "y", # http://prirucka.ujc.cas.cz/?id=326
						]
	NAME_PREFIXES = ["d'", "o'"]             # French / Italian / Portuguese / Spanish


	@classmethod
	def get_subnames(self, whole_names, config = AutomataVariants.DEFAULT):
		'''
		From a list of whole names for a given person, it creates a set of all possible subnames.
		For example:
		   * "Václav Havel" => ["Václav", "Havel"]
		   * "Elizabeth O'Connor" => ["Elizabeth", "O'Connor", "Connor"]
		   * "Ludwig van Beethoven => ["Ludwig", "Beethoven", "van Beethoven"]
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

		regex_location_remove = regex.compile(r" ({}) .*".format("|".join(map(regex.escape, self.LOCATION_PREPOSITIONS))), flags=regex_flags)
		regex_name = regex.compile(r"^({})?\p{{Lu}}(\p{{L}}+)?(['-]\p{{Lu}}\p{{L}}+)*$".format(tmp_prefixes), flags=regex_flags) # this should match only a nice name (must support prefixes)
#		regex_name = regex.compile(r"({})?[A-Z][a-z-']+[a-zA-Z]*[a-z]+".format(tmp_prefixes)) # this should match only a nice name (must support prefixes)

		names = set()

		for whole_name in whole_names:
			# normalize whitespaces
			whole_name = regex.sub('\s+', ' ', whole_name)
			# remove a part of the name with location information (e.g. " of Polestown" from the name "Richard Butler of Polestown")
			whole_name = regex_location_remove.sub("", whole_name).title()

			# split the name only (without prepositions) to the parts
			subnames = regex_prepositions_remove.sub(" ", whole_name).split()

			for subname in subnames:
				if subname.endswith(","):
					subname = subname[:-1]

				# skip invalid / forbidden names
				if subname not in self.FORBIDDEN_NAMES:
					# normalize name to start with capital, including name with prefix (for example o'... => O'...)
					subname = subname[0].upper() + subname[1:]
#					# remove accent, because python re module doesn't support [A-Z] for Unicode
					subname_without_accent = remove_accent(subname)
#					result = regex_name.match(subname_without_accent)
					result = regex_name.match(subname)
					if result:
						match = result.group()
#						if match == subname_without_accent:

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
			preposition_name = regex_prepositions_name.search(whole_name.title())
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
