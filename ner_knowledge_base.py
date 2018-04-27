#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import re
import imp
import cPickle as pickle
import threading
import subprocess
import unicodedata
import tempfile
import time

# Pro debugování:
from debug import print_dbg, print_dbg_en, cur_inspect

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIRPATH_KB_DAEMON = os.path.abspath(os.path.join(SCRIPT_DIR, "SharedKB/var2"))
PATH_KB_DAEMON = os.path.abspath(os.path.join(DIRPATH_KB_DAEMON, "decipherKB-daemon"))
PATH_KB = os.path.abspath(os.path.join(SCRIPT_DIR, "KB-HEAD.all"))
#PATH_KB = "KB-HEAD.all"

KB_MULTIVALUE_DELIM = "|"

# # Timeouty v sekundách:
Timeout_SharedKB_start = 300
Timeout_process_exists = 10

reload(sys)
sys.setdefaultencoding("utf-8")

def remove_accent(_string):
    """Removes accents from a string. For example, Eduard Ovčáček -> Eduard Ovcacek."""
    nkfd_form = unicodedata.normalize('NFKD', unicode(_string))
    return str("".join([c for c in nkfd_form if not unicodedata.combining(c)]))

class KnowledgeBaseCZ(object):


	def __init__(self, kb_shm_name=None):

		KB_shm = imp.load_source('KB_shm', os.path.join(DIRPATH_KB_DAEMON,"KB_shm.py"))
		self.kb_shm_name = kb_shm_name
		self.kb_shm = KB_shm.KB_shm(self.kb_shm_name)
		self.kb_daemon = None

	def start(self):
		kb_daemon_run = self.check()

		try:
			if(self.kb_shm_name == None):
				if(kb_daemon_run):
					self.kb_shm.start()
					if(not self.checkVersion()):
						self.end()
						self.__init__("/decipherKB-CZ-daemon_shm-%s" % self.kb_shm.getVersionFromSrc(PATH_KB))
						return self.start()
				else:
					self.__init__("/decipherKB-CZ-daemon_shm-%s" % self.kb_shm.getVersionFromSrc(PATH_KB))
					return self.start()
			else:

				if(kb_daemon_run):
					self.kb_shm.start()
					if( not self.checkVersion()):
						raise RuntimeError("\"%s\" has different version compared to \"%s\"." % (self.kb_shm_name, PATH_KB))
				else:
					self.kb_daemon = KbDaemon(self.kb_shm_name)
					self.kb_daemon.start()
					self.kb_shm.start()

		except:
			self.end()
			raise

	def check(self):
		return self.kb_shm.check()

	def checkVersion(self):

		return self.version() == self.kb_shm.getVersionFromSrc(PATH_KB)

	def version(self):

		return self.kb_shm.version()

	def end(self):

		if self.kb_daemon:
			self.kb_daemon.stop()
		self.kb_shm.end()
		self.kb_daemon = None

	def initName_dict(self):
		'''
		Dictionary asociates parts of person names with corresponding items of knowledge base.
		'''
		PATH_NAMEDICT = os.path.join(SCRIPT_DIR, "ner_namedict.pkl")
		PATH_FRAGMENTS = os.path.join(SCRIPT_DIR, "ner_fragments.pkl")

		#person_alias = self.get_head_col("person", "ALIAS")
		person_name = self.get_head_col("person", "JMENO")
		#artist_other = self.get_head_col("artist", "OTHER TERM")
		#artist_preferred = self.get_head_col("artist", "PREFERRED TERM")
		#artist_display = self.get_head_col("artist", "DISPLAY TERM")

		self.name_dict = {}
		self.fragments = set()

		# Proto aby se nemusela znova procházet KB, vytvoří se soubor PATH_NAMEDICT.
		# Namedict se bude načítat z něj pokud PATH_KB bude starší než PATH_NAMEDICT - tím dojde k urychlení.
		if (os.access(PATH_NAMEDICT, os.F_OK)) and (os.stat(PATH_KB).st_mtime < os.stat(PATH_NAMEDICT).st_mtime) and (os.access(PATH_FRAGMENTS, os.F_OK)) and (os.stat(PATH_NAMEDICT).st_mtime <= os.stat(PATH_FRAGMENTS).st_mtime):
			file_namedict = open(PATH_NAMEDICT, 'rb')
			file_fragments = open(PATH_FRAGMENTS, 'rb')

			self.name_dict = pickle.load(file_namedict)
			self.fragments = pickle.load(file_fragments)

			file_namedict.close()
			file_fragments.close()
		else:
			file_namedict = open(PATH_NAMEDICT, 'wb')
			file_fragments = open(PATH_FRAGMENTS, 'wb')

			line = 1
			text = self.get_data_at(line, 1)

			while text != None:
				ent_type = self.get_ent_type(line)

				if ent_type in ["person", "preson:artist"]:
					if ent_type == "person":
						#whole_names = self.get_data_at(line, person_alias).split(KB_MULTIVALUE_DELIM)
						whole_names = [self.get_data_at(line, person_name)]

					#elif ent_type == "artist":
					#	whole_names = self.get_data_at(line, artist_other).split(KB_MULTIVALUE_DELIM)
					#	whole_names.append(self.get_data_at(line, artist_preferred))
					#	whole_names.append(self.get_data_at(line, artist_display))

					# creates subnames
					names = self.get_subnames(whole_names, ent_type, line)

					for name in names:
						name = remove_accent(name).lower()
						if name not in self.name_dict:
							self.name_dict[name] = set([line])
						else:
							self.name_dict[name].add(line)
				line += 1
				text = self.get_data_at(line, 1)
			pickle.dump(self.name_dict, file_namedict, pickle.HIGHEST_PROTOCOL)
			pickle.dump(self.fragments, file_fragments, pickle.HIGHEST_PROTOCOL)

			file_namedict.close()
			file_fragments.close()


	def get_subnames(self, whole_names, ent_type, line):
		'''
		From a list of whole names for a given person, it creates a set of all possible subnames.
		For example, for the name name "George Washington", it creates a set containing two subnames - "George" and "Washington".
		'''

		forbidden = ["Pán", "Pani", "Svatý"]
		#roles = ["Baron", "Prince", "Duke", "Earl", "King", "Pope", "Queen", "Artist", "Painter"]
		regex_place = re.compile(r" (z|ze) .*")
		regex_role = re.compile(r"[Tt]he [a-zA-Z]+")
		regex_van = re.compile(r"[Vv]an [a-zA-Z]+")
		regex_name = re.compile(r"[A-Z][a-z-']+[a-zA-Z]*[a-z]+") # this should match only a nice name
		names = set()
		roles = set()

		# getting roles for artists and persons
		#if ent_type == "artist":
		#	roles.add("artist")
		#	preferred_role = self.get_data_for(line, "PREFERRED ROLE")
		#	if preferred_role and " " not in preferred_role:
		#		roles.add(preferred_role)
		#	other_roles = self.get_data_for(line, "OTHER ROLE").split("|")
		#	for other_role in other_roles:
		#		if other_role and " " not in other_role:
		#			roles.add(other_role)
#		if ent_type == "person":
#			professions = self.get_data_for(line, "POVOLANI").split("|")
#			for profession in professions:
#				if profession:
#					roles.add(profession)
#
#		for role in roles:
#			role = role.lower()
#			names.add(role)
#			self.fragments.add(role)
#			self.fragments.add(role.decode('utf8').title())

		for whole_name in whole_names:

			# removing a part of the name with location information (e.g. " of Polestown" from the name "Richard Butler of Polestown")
			whole_name = regex_place.sub("", whole_name)

			# searching for a role
			#role = regex_role.match(whole_name)
			#if role:
			#	match = role.group()
			#	if match.split(" ")[1] in roles:
			#		names.add(match)
			#		match = match.lower()
			#		self.fragments.add(match)
			#		self.fragments.add(match.title())
			#		self.fragments.add(match.replace("the", "The"))

			# splitting the name to the parts
			subnames = whole_name.split(' ')
			#print(whole_name)
			for subname in subnames:
				if subname.endswith(","):
					subname = subname[:-1]
				# removing accent, because python re module doesn't support [A-Z] for Unicode
				subname_without_accent = remove_accent(subname)
				result = regex_name.match(subname_without_accent)
				if result:
					match = result.group()
					if match == subname_without_accent and subname not in forbidden and match not in roles:
						names.add(subname)
						self.fragments.add(subname)
						self.fragments.add(subname_without_accent)

			# searching for "van Eyck"
			vanName = regex_van.search(whole_name)
			if vanName:
				match = vanName.group()
				names.add(match)
				match = "v" + match[1:]
				self.fragments.add(match)
				self.fragments.add(match.replace("van", "Van"))
				self.fragments.add(remove_accent(match))
				self.fragments.add(remove_accent(match.replace("van", "Van")))

		return names

	def print_subnames(self):
		'''
		Print all partial name variants from self.name_dict.
		'''
		for fragment in self.fragments:
			print fragment

	def get_field(self, line, column):
		'''
		Zavrhovaná metoda!
		Číslování řádků od 1 a sloupců od 0, podle "ner.py".
		Ovšem SharedKB čísluje řádky i sloupce od 1.
		'''

		return self.kb_shm.dataAt(line, column + 1)

	def get_data_at(self, line, col):
		'''
		Číslování řádků i sloupců od 1.
		'''

		return self.kb_shm.dataAt(line, col)

	def get_data_for(self, line, col_name):
		'''
		Číslování řádků od 1.
		'''

		return self.kb_shm.dataFor(line, col_name)

	def get_head_at(self, line, col):
		'''
		Číslování řádků i sloupců od 1.
		'''

		return self.kb_shm.headAt(line, col)

	def get_head_for(self, ent_type, col):
		'''
		Číslování sloupců od 1.
		'''

		return self.kb_shm.headFor(ent_type, col)

	def get_head_col(self, ent_type, col_name):
		'''
		Vrátí číslo sloupce pro požadovaný ent_type a jméno sloupce.
		'''

		return self.kb_shm.headCol(ent_type, col_name)

	def get_complete_data(self, line, delim='\t'):
		'''
		Vrátí tuple (počet sloupců, celý řádek), kde v jednom řetězci je celý řádek pro požadovaný line, tak jak je v KB.
		Parametr delim umožňuje změnit oddělovač sloupců.
		'''

		text_line = ""
		col = 1
		text = self.get_data_at(line, col)

		if text != None:
			text_line += text
			col += 1
			text = self.get_data_at(line, col)

		while text != None:
			text_line += delim
			text_line += text
			col += 1
			text = self.get_data_at(line, col)

		return (col-1, text_line)

	def get_complete_head(self, ent_type, delim='\t'):
		'''
		Vrátí tuple (počet sloupců, celý řádek), kde v jednom řetězci je celý řádek pro požadovaný line, tak jak je v KB.
		Parametr delim umožňuje změnit oddělovač sloupců.
		'''

		text_line = ""
		col = 1
		text = self.get_head_for(ent_type, col)

		if text != None:
			text_line += text
			col += 1
			text = self.get_head_for(ent_type, col)

		while text != None:
			text_line += delim
			text_line += text
			col += 1
			text = self.get_head_for(ent_type, col)

		return (col-1, text_line)

	def get_complete_ent_pretty(self, line):
		'''
		Vrátí tuple (počet sloupců, celý řádek), kde v jednom řetězci je celý řádek pro požadovaný line, tak jak je v KB.
		Parametr delim umožňuje změnit oddělovač sloupců.
		'''

		text_line = ""
		col = 1
		ent_type = self.get_ent_type(line)
		text_head = self.get_head_for(ent_type, col)
		text_data = self.get_data_at(line, col)

		if (text_head != None) and (text_data != None):
			text_line += text_head + ": " + text_data
			col += 1
			text_head = self.get_head_for(ent_type, col)
			text_data = self.get_data_at(line, col)

		while (text_head != None) and (text_data != None):
			text_line += "\n"
			text_line += text_head + ": " + text_data
			col += 1
			text_head = self.get_head_for(ent_type, col)
			text_data = self.get_data_at(line, col)

		return (col - 1, text_line)

	def get_ent_type(self, line):
		"""Returns a type of an entity at the line of the knowledge base"""

		return self.kb_shm.dataType(line)

	def people_named(self, subname):
		"""
		Returns all names (KB ids) containing a given subname.
		"""

		return self.name_dict.get(subname, set())

	def get_score(self, line):
		"""
		Returns disambiguation score based on Wikipedia statistics and score based on other metrics.
		"""

		result = self.get_data_for(line, "CONFIDENCE")

		try:
			if not result:
				return 0
			else:
				return float(result)
		except:
			err_type = self.get_ent_type(line)
			if err_type == None:
				err_head = (None, None)
				err_data = (None, None)
			else:
				err_head = self.get_complete_head(err_type)
				err_data = self.get_complete_data(line)
			print_dbg_en("Line \"", line, "\" have non-integer type \"", type(result), "\" with content \"", result, "\"", delim="")
			print_dbg_en("Dump head for type \"", err_type, "\" (cols=", err_head[0], "):\n\"\"\"\n", err_head[1], "\n\"\"\"", delim="")
			print_dbg_en("Dump line \"", line, "\" (cols=", err_data[0], "):\n\"\"\"\n", err_data[1], "\n\"\"\"", delim="")
			print_dbg_en("Version of connected KB (at \"", self.kb_shm_name, "\") is \"", self.version(), "\".", delim="")
			raise

	def get_dates(self, line):
		ent_type = self.get_ent_type(line)
		if ent_type in ["person", "artist"]:
			dates = set([self.get_data_for(line, "DATUM_NAROZENI"), self.get_data_for(line, "DATUM_UMRTI")])
			dates.discard("")
			return dates
		return set()

	def get_nationalities(self, line):

		return self.get_data_for(line, "NARODNOST").split(KB_MULTIVALUE_DELIM)


class KbDaemon(object):
	def __init__(self, kb_shm_name=None):
		self.ps = None
		self.stdout = tempfile.TemporaryFile()
		self.stderr = tempfile.TemporaryFile()
		self.exitcode = None
		self.kb_shm_name = kb_shm_name

	def start(self):
		if self.kb_shm_name:
			self.ps = subprocess.Popen([PATH_KB_DAEMON, "-s", self.kb_shm_name, PATH_KB], stdout=self.stdout, stderr=self.stderr)
		else:
			self.ps = subprocess.Popen([PATH_KB_DAEMON, PATH_KB], stdout=self.stdout, stderr=self.stderr)

		output = ""
		try:
			i = 0

			output = self.stdout.readline()

			while (output == "" or output[-1] != "\n") and self.ps.poll() == None:
				if i >= Timeout_SharedKB_start:
					raise RuntimeError("Timeout of subprocess \"%s\"." % (PATH_KB_DAEMON))
				time.sleep(1)
				self.stdout.seek(0)
				output = self.stdout.readline()
		except:
			self.ps.terminate()
			self.ps.wait()
			raise

		print_dbg(output)

		if (self.ps.poll() != None):
			ps_exitcode = self.ps.wait()

			self.stdout.seek(0)
			self.stderr.seek(0)
			ps_stdout = self.stdout.read()
			ps_stderr = self.stderr.read()

			sys.stderr.write("%s [EXITCODE]:\n%s\n" % (PATH_KB_DAEMON, ps_exitcode))
			if (ps_stdout):
				sys.stderr.write("%s [STDOUT]:\n%s\n" % (PATH_KB_DAEMON, ps_stdout))
			if (ps_stderr):
				sys.stderr.write("%s [STDERR]:\n%s\n" % (PATH_KB_DAEMON, ps_stderr))

			self.stdout.close()
			self.stderr.close()
			self.ps = None
			raise RuntimeError("\"%s\" has failed to start." % (PATH_KB_DAEMON))

	def stop(self):
		if not self.ps:
			return

		self.ps.terminate()
		ps_exitcode = self.ps.wait()

		self.stdout.seek(0)
		self.stdout.readline()
		self.stderr.seek(0)
		ps_stdout = self.stdout.read()
		ps_stderr = self.stderr.read()

		if (ps_exitcode != 0):
			sys.stderr.write("%s [EXITCODE]:\n%s\n" % (PATH_KB_DAEMON, ps_exitcode))
		if (ps_stdout):
			sys.stderr.write("%s [STDOUT]:\n%s\n" % (PATH_KB_DAEMON, ps_stdout))
		if (ps_stderr):
			sys.stderr.write("%s [STDERR]:\n%s\n" % (PATH_KB_DAEMON, ps_stderr))

		self.stdout.close()
		self.stderr.close()
		self.ps = None
		self.exitcode = ps_exitcode