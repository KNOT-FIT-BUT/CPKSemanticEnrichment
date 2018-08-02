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

# Author: Matej Magdolen, xmagdo00@stud.fit.vutbr.cz
# Author: Jan Doležal, xdolez52@stud.fit.vutbr.cz
# Author: Lubomír Otrusina, iotrusina@fit.vutbr.cz
#
# Description: Loads a knowledge base and computes metrics and scores for static disambiguation.

import os
import re
import sys
import numpy

# for debugging purposes only
import debug
debug.DEBUG_EN = False
from debug import print_dbg

# CONSTANTS

# getting the absolute path to the directory with this script
script_dir = os.path.dirname(os.path.abspath(__file__))
PATH_HEAD_KB = os.path.abspath(os.path.join(script_dir, "HEAD-KB"))
KB_MULTIVALUE_DELIM = "|"

# FUNCTIONS AND CLASSES

def getDictHeadKB(path_to_headkb=PATH_HEAD_KB):
	"""
	Returns a dictionary with the structure of KB from HEAD-KB and number of column with attribute TYPE.
	"""
	
	PARSER_FIRST = re.compile(r"""(?ux)
		^
		<(?P<TYPE>[^>]+)> # NOTE: Potlačení podtypů
		(?:\{(?P<FLAGS>(?:\w|[ ])*)(?:\[(?P<PREFIX_OF_VALUE>[^\]]+)\])?\})?
		(?P<NAME>(?:\w|[ ])+)
		$
	""")
	PARSER_OTHER = re.compile(r"""(?ux)
		^
		(?:\{(?P<FLAGS>(?:\w|[ ])*)(?:\[(?P<PREFIX_OF_VALUE>[^\]]+)\])?\})?
		(?P<NAME>(?:\w|[ ])+)
		$
	""")
	
	lines = []
	with open(path_to_headkb) as head_kb_file:
		for line in head_kb_file:
			if line[:-1] != "":
				lines.append(line[:-1].split("\t"))
	
	headKB = {} # Slovník TYPE:{SUBTYPE:{COLUMN_NAME:COLUMN}}
	ent_type_col = None # Sloupec ve kterém je definován typ entity
	for line_num in range(len(lines)):
		plain_column = ""
		head_type = ""
		for col_num in range(len(lines[line_num])):
			plain_column = lines[line_num][col_num]
			if col_num == 0:
				splitted = PARSER_FIRST.search(plain_column)
				head_type = splitted.group("TYPE")
				head_subtype = None # NOTE: Potlačení podtypů
				if not headKB.has_key(head_type):
					headKB[head_type] = {}
				
				print_dbg(head_type, "/", head_subtype, ": ", line_num, delim="")
				
				if not head_subtype:
					head_subtype = ""
				headKB[head_type][head_subtype] = {}
			else:
				splitted = PARSER_OTHER.search(plain_column)
			col_name = splitted.group("NAME")
			headKB[head_type][head_subtype][col_name] = col_num
			print_dbg(head_type, "/", head_subtype, " -> ", col_name, ": ", col_num, delim="")
			
			if col_name == "TYPE":
				if ent_type_col is None:
					ent_type_col = col_num
				elif ent_type_col != col_num:
					raise RuntimeError("getDictHeadKB: TYPE column must be at same column for each type of entity in HEAD-KB!")
	return headKB, ent_type_col

class KnowledgeBase:
	"""
	* Pracuje s daty (sloupci) obsaženými na řádku v KB nebo v daném seznamu.
	* Sloupce jsou adresovány dle jejich názvů v HEAD_KB.
	* Tato třída je určena především pro přidání metrik do KB (metrics_to_KB.py), ale je používána pro svou jednoduchost i v dalších skriptech (kb_filter.py, prepare_kb_to_stats_and_metrics.py, wiki_stats_to_KB.py, KB2namelist.py).
	* Načítá KB až je to vyžadováno (lazy přístup). Je tedy možné načíst pouze zajímavé řádky z KB, převést je na seznamy a ty předávat místo čísel řádků metodám instance této třídy, není-li nutno držet v paměti celou KB.
	* Tisk instance této třídy vytiskne celou KB, byla-li načtena, jinak vytiskne pouze prázdný řetězec.
	* Instance je reprezentována řetězcem obsahujícím cestu k HEAD-KB, KB a dále informaci zda-li je KB načtena do paměti.
	"""
	
	def __init__(self, path_to_headkb=PATH_HEAD_KB, path_to_kb=None):
		self.path_to_headkb = path_to_headkb
		self.headKB, self.ent_type_col = getDictHeadKB(self.path_to_headkb)
		
		self._kb_loaded = False
		self.lines = []
		
		# lists of metrics values in kb for computing percentiles
		self.metrics = {'person':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'organisation':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'geo':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'geo:geoplace':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'geoplace:populatedPlace':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'event':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'person:artist':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'geoplace:protectedArea':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'geoplace:conservationArea':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'geoplace:mountain':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'geoplace:castle':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'geoplace:lake':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'geoplace:forest':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'geoplace:mountainPass':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'geo:mountainRange':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'geo:river':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'geoplace:observationTower':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]},
				'geo:waterfall':{'description_length':[], 'columns_number':[], 'wiki_backlinks':[], 'wiki_hits':[], 'wiki_ps':[]}}

		# data structure for indexing percentile scores
		self.metric_index = {'person':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'organisation':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'geo':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'geo:geoplace':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'geoplace:populatedPlace':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'event':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'person:artist':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'geoplace:protectedArea':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'geoplace:conservationArea':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'geoplace:mountain':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'geoplace:castle':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'geoplace:lake':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'geoplace:forest':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'geoplace:mountainPass':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'geo:mountainRange':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'geo:river':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'geoplace:observationTower':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}},
					'geo:waterfall':{'description_length':{}, 'columns_number':{}, 'wiki_backlinks':{}, 'wiki_hits':{}, 'wiki_ps':{}}
					}
		
		self.path_to_kb = path_to_kb
	
	def __repr__(self):
		return "KnowledgeBase(path_to_headkb=%r, path_to_kb=%r, kb_is_loaded=%r)" % (self.path_to_headkb, self.path_to_kb, self._kb_loaded)
	
	def check_or_load_kb(self):
		if not self._kb_loaded:
			self.load_kb()
	
	def load_kb(self):
		# loading knowledge base
		self.lines = []
		with open(self.path_to_kb) as kb_file:
			for line in kb_file:
				self.lines.append(line[:-1].split("\t"))
		self._kb_loaded = True
	
	def get_ent_head(self, line):
		ent_type = self.get_ent_type(line)
		ent_subtype = self.get_ent_subtype(line)
		
		if ent_subtype:
			ent_subtypes = [""] + ent_subtype.split(KB_MULTIVALUE_DELIM)
		else:
			ent_subtypes = [""]
		
		head = []
		for subtype in ent_subtypes:
			head.extend([item[0] for item in sorted(self.headKB[ent_type][subtype].items(), key=lambda i: i[-1])])
		
		return head
	
	def get_ent_type(self, line):
		""" Returns a type of an entity at the line of the knowledge base. """
		
		ent_type = self.get_field(line, self.ent_type_col)
		return ent_type
	
	def get_ent_subtype(self, line):
		""" Returns a subtype of an entity at the line of the knowledge base. """
		
		ent_type = self.get_ent_type(line)
		if self.headKB[ent_type][""].has_key("SUBTYPE"):
			ent_subtype = self.get_field(line, self.headKB[ent_type][""]["SUBTYPE"])
		else:
			ent_subtype = ""
		return ent_subtype
	
	def get_location_code(self, line):
		return self.get_data_for(line, "FEATURE CODE")[0:3]

	def get_field(self, line, column):
		""" Returns a column of a line in the knowledge base. """
		
		if isinstance(line, list): # line jako sloupce dané entity
			return line[column]
		else: # line jako číslo řádku na kterém je daná entita
			self.check_or_load_kb()
			
			# KB lines are indexed from one
			try:
				return self.lines[int(line) - 1][column]
			except:
				sys.stderr.write("line " + str(line) + " column " + str(column) + "\n")
				raise
	
	def get_col_for(self, line, col_name):
		""" Line numbering from one. """

		# getting the entity type
		ent_type = self.get_ent_type(line)
		ent_subtype = self.get_ent_subtype(line)
		
		if ent_subtype:
			ent_subtypes = [""] + ent_subtype.split(KB_MULTIVALUE_DELIM)
		else:
			ent_subtypes = [""]
		
		col = 0
		colCnt = 0
		for subtype in ent_subtypes:
			if self.headKB[ent_type][subtype].has_key(col_name):
				col = self.headKB[ent_type][subtype][col_name]
				col += colCnt
				break
			else:
				colCnt += len(self.headKB[ent_type][subtype])
		else:
			raise RuntimeError("Bad column name '%s' for line '%s'." % (col_name, line))
		
		return col
	
	def get_data_for(self, line, col_name):
		""" Line numbering from one. """
		
		return self.get_field(line, self.get_col_for(line, col_name))
	
	def nonempty_columns(self, line):
		""" Returns a number of columns at the specified line of the knowledge base which have a non-empty value. """
		
		if isinstance(line, list): # line jako sloupce dané entity
			columns = line
		else: # line jako číslo řádku na kterém je daná entita
			self.check_or_load_kb()
			columns = self.lines[line - 1]
		
		metrics_cols = [self.get_col_for(columns, colname) for colname in ('WIKI BACKLINKS', 'WIKI HITS', 'WIKI PRIMARY SENSE', 'SCORE WIKI', 'SCORE METRICS', 'CONFIDENCE')]
		
		result = 0
		# KB lines are indexed from one
		for col in range(len(columns)):
			if col not in metrics_cols and columns[col]:
				result += 1
		
		return result
	
	def description_length(self, line):
		""" Returns a length of a description of a specified line. """
		
		# getting the entity type
		ent_type = self.get_ent_type(line)
		if ent_type in ["person:artist", "person", "event"]:
			field = "ODSTAVEC"
		elif ent_type == "organisation":
			field = "POPIS"
		else:
			field = "INFO"
		
		description = self.get_data_for(line, field)
		if description is None:
			return 0 # Pokud entita nemá popis mezi atributy, tak je délka popisu nulová.
		else:
			return len(description)
	
	def metric_percentile(self, line, metric):
		""" Computing a percentile score for a given metric and entity. """

		# getting the entity type
		ent_type = self.get_ent_type(line)

		value = 0
		if metric == 'description_length':
			value = self.description_length(line)
		elif metric == 'columns_number':
			value = self.nonempty_columns(line)
		elif metric[0:4] == 'wiki':
			value_str = self.get_wiki_value(line, metric[5:])
			if value_str:
				value = int(value_str)
		return self.metric_index[ent_type][metric][value]
	
	def get_wiki_value(self, line, column_name):
		"""
		Return a link to Wikipedia or a statistc value identified
		by column_name from knowledge base line.
		"""

		column_rename = {'backlinks' : "WIKI BACKLINKS", 'hits' : "WIKI HITS", 'ps' : "WIKI PRIMARY SENSE"}
		if column_name == 'link':
			return self.get_data_for(line, "WIKI_URL")
		else:
			return self.get_data_for(line, column_rename[column_name])
	
	def insert_metrics(self):
		""" Computing SCORE WIKI, SCORE METRICS and CONFIDENCE and adding them to the KB. """
		
		self.check_or_load_kb()
		
		# computing statistics
		for line_num in range(1, len(self.lines) + 1):
			ent_type = self.get_ent_type(line_num)
			if ent_type == "nationality": # FIXME: Z čeho se má pak počítat CONFIDENCE, co?
				continue

			self.metrics[ent_type]['columns_number'].append(self.nonempty_columns(line_num))
			self.metrics[ent_type]['description_length'].append(self.description_length(line_num))
			if self.get_wiki_value(line_num, 'backlinks'):
				self.metrics[ent_type]['wiki_backlinks'].append(int(self.get_wiki_value(line_num, 'backlinks')))
				self.metrics[ent_type]['wiki_hits'].append(int(self.get_wiki_value(line_num, 'hits')))
				self.metrics[ent_type]['wiki_ps'].append(int(self.get_wiki_value(line_num, 'ps')))
		
		# sorting statistics
		for i in self.metrics:
			for j in self.metrics[i]:
				self.metrics[i][j].sort()
		
		# indexing statistics
		for i in self.metrics:
			for j in self.metrics[i]:
				for k in range(0, len(self.metrics[i][j])):
					if self.metrics[i][j][k] not in self.metric_index[i][j]:
						max_value = float(self.metrics[i][j][-1])
						if j in ['wiki_backlinks', 'wiki_hits']:
							max_value = 0.25 * max_value
						if max_value:
							normalized_value = float(self.metrics[i][j][k]) / max_value
							self.metric_index[i][j][self.metrics[i][j][k]] = min(normalized_value, 1.0)
						else:
							self.metric_index[i][j][self.metrics[i][j][k]] = 1.0
		
		# computing SCORE WIKI, SCORE METRICS and CONFIDENCE
		for line_num in range(1, len(self.lines) + 1):
			
			columns = self.lines[line_num - 1]
			
			# getting the entity type
			ent_type = self.get_ent_type(columns)
			if ent_type == "nationality": # FIXME: Opravdu chceme, aby typ "nationality" byl bez merik a CONFIDENCE? Pokud ano, je třeba to nějak zohlednit v NERu a SECu.
				continue
			# computing SCORE WIKI
			score_wiki = 0
			if self.get_wiki_value(columns, 'backlinks'):
				wiki_backlinks = self.metric_percentile(columns, 'wiki_backlinks')
				wiki_hits = self.metric_percentile(columns, 'wiki_hits')
				wiki_ps = self.metric_percentile(columns, 'wiki_ps')
				score_wiki = 100 * numpy.average([wiki_backlinks, wiki_hits, wiki_ps], weights=[5, 5, 1])
			columns[self.get_col_for(columns, "SCORE WIKI")] = "%.2f" % score_wiki
			
			# computing SCORE METRICS
			description_length = self.metric_percentile(columns, 'description_length')
			columns_number = self.metric_percentile(columns, 'columns_number')
			score_metrics = 100 * numpy.average([description_length, columns_number])
			columns[self.get_col_for(columns, "SCORE METRICS")] = "%.2f" % score_metrics
			
			# computing CONFIDENCE
			columns[self.get_col_for(columns, "CONFIDENCE")] = "%.2f" % numpy.average([score_wiki, score_metrics], weights=[5, 1])
	
	def _str1(self):
		return '\n'.join(['\t'.join(line) for line in self.lines+[""]])
	
	def _str2(self):
		result = ""
		for line in self.lines:
			result += '\t'.join(line) + '\n'
		return result
	
	def __str__(self):
		return self._str1()

