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
# Příklad načtení:
'''
from KB_shm import *
'''

import os
import re
from ctypes import CDLL, c_char, c_char_p, c_int, c_uint, c_void_p, POINTER
#from ctypes import byref

# Pro debugování:
import inspect
DEBUG_EN = True
DEBUG_EN = False
#

def print_dbg(text=""):
	if not DEBUG_EN:
		return
	callerframerecord = inspect.stack()[1]
	frame = callerframerecord[0]
	info = inspect.getframeinfo(frame)
	
	head = "("+ info.filename +", "+ info.function +", "+ str(info.lineno) +")"
	
	print( head +":\n'''\n"+ text +"\n'''" )
#

# Získání absolutní cesty k adresáři ve kterém je tento soubor.
script_dir = os.path.dirname(os.path.abspath(__file__))
# Načtení dynamické knihovny "libKB_shm.so"
libKB_shm = CDLL( os.path.join(script_dir, "libKB_shm.so") )

# Pro jazyky C/C++
'''
KB_shm_p = c_void_p(0)
KB_shm_fd = c_int(-1)
status = c_int(0)

status = c_int( connectKBSharedMem( byref(KB_shm_p), byref(KB_shm_fd) ) )
if status.value != 0:
	print("ERROR")
	exit(1)

. . .

status = c_int( disconnectKBSharedMem( byref(KB_shm_p), byref(KB_shm_fd) ) )
if status.value != 0:
	print("ERROR")
	exit(1)

exit(0)
'''
connectKBSharedMem = libKB_shm.connectKBSharedMem
connectKBSharedMem.argtypes = [POINTER(c_void_p), POINTER(c_int)]
connectKBSharedMem.restype = c_int

disconnectKBSharedMem = libKB_shm.disconnectKBSharedMem
disconnectKBSharedMem.argtypes = [POINTER(c_void_p), POINTER(c_int)]
disconnectKBSharedMem.restype = c_int

# Pro jazyky Java, Python, ...
'''
KB_shm_p = c_void_p(0)
KB_shm_fd = c_int(-1)
status = c_int(0)

KB_shm_fd = c_int( connectKB_shm() )
if KB_shm_fd.value < 0:
	print("ERROR")
	exit(1)

KB_shm_p = c_void_p( mmapKB_shm(KB_shm_fd) )
if KB_shm_p.value == None:
	print("ERROR")
	disconnectKB_shm(KB_shm_p, KB_shm_fd)
	exit(1)

. . .

status = c_int( disconnectKB_shm(KB_shm_p, KB_shm_fd) )
if status.value != 0:
	print("ERROR")
	exit(1)

KB_shm_p = c_void_p(0)
KB_shm_fd = c_int(-1)
exit(0)
'''
checkKB_shm = libKB_shm.checkKB_shm
checkKB_shm.argtypes = [c_char_p]
checkKB_shm.restype = c_int

connectKB_shm = libKB_shm.connectKB_shm
connectKB_shm.argtypes = [c_char_p]
connectKB_shm.restype = c_int

mmapKB_shm = libKB_shm.mmapKB_shm
mmapKB_shm.argtypes = [c_int]
mmapKB_shm.restype = c_void_p

disconnectKB_shm = libKB_shm.disconnectKB_shm
disconnectKB_shm.argtypes = [c_void_p, c_int]
disconnectKB_shm.restype = c_int

# Funkce pro získání řetězců
'''
KBSharedMemDataAt( KB_shm_p, 1, 1 )
c_char_p( KBSharedMemDataAt( KB_shm_p, 1, 1 ) )
print( c_char_p( KBSharedMemDataAt( KB_shm_p, 1, 1 ) ).value )

print( c_char_p( KBSharedMemHeadFor( KB_shm_p, 'p', 1 ) ).value )
print( c_char_p( KBSharedMemHeadFor_Boost( KB_shm_p, 'p', 1, byref(line) ) ).value )
'''
KBSharedMemHeadAt = libKB_shm.KBSharedMemHeadAt
KBSharedMemHeadAt.argtypes = [c_void_p, c_uint, c_uint]
KBSharedMemHeadAt.restype = c_void_p

KBSharedMemHeadFor = libKB_shm.KBSharedMemHeadFor
KBSharedMemHeadFor.argtypes = [c_void_p, c_char, c_uint]
KBSharedMemHeadFor.restype = c_void_p

KBSharedMemHeadFor_Boost = libKB_shm.KBSharedMemHeadFor_Boost
KBSharedMemHeadFor_Boost.argtypes = [c_void_p, c_char, c_uint, POINTER(c_uint)]
KBSharedMemHeadFor_Boost.restype = c_void_p

KBSharedMemDataAt = libKB_shm.KBSharedMemDataAt
KBSharedMemDataAt.argtypes = [c_void_p, c_uint, c_uint]
KBSharedMemDataAt.restype = c_void_p

# Funkce pro získání verze

KBSharedMemVersion = libKB_shm.KBSharedMemVersion
KBSharedMemVersion.argtypes = [c_void_p]
KBSharedMemVersion.restype = c_uint

getVersionFromSrc = libKB_shm.getVersionFromSrc
getVersionFromSrc.argtypes = [c_char_p]
getVersionFromSrc.restype = c_int

getVersionFromBin = libKB_shm.getVersionFromBin
getVersionFromBin.argtypes = [c_char_p]
getVersionFromBin.restype = c_int

# Příklad použití:
'''
KB_shm_p = c_void_p(0)
KB_shm_fd = c_int(-1)
status = c_int(0)

KB_shm_fd = c_int( connectKB_shm() )
if KB_shm_fd.value < 0:
	print("ERROR")
	exit(1)

KB_shm_p = c_void_p( mmapKB_shm(KB_shm_fd) )
if KB_shm_p.value == None:
	print("ERROR")
	disconnectKB_shm(KB_shm_p, KB_shm_fd)
	exit(1)

#. . .#

raw_input("hit enter...")

str = c_char_p( KBSharedMemHeadAt( KB_shm_p, 1, 1 ) ).value
i = 1
while str != None:
	j = 1
	while str != None:
		print(str)
		j += 1
		str = c_char_p( KBSharedMemHeadAt( KB_shm_p, i, j ) ).value
	i += 1
	str = c_char_p( KBSharedMemHeadAt( KB_shm_p, i, 1 ) ).value

raw_input("hit enter...")

j = 1
str = c_char_p( KBSharedMemHeadFor( KB_shm_p, 'p', j ) ).value
while str != None:
	print(str)
	j += 1
	str = c_char_p( KBSharedMemHeadFor( KB_shm_p, 'p', j ) ).value

raw_input("hit enter...")

str = c_char_p( KBSharedMemDataAt( KB_shm_p, 1, 1 ) ).value
i = 1
while str != None:
	j = 1
	while str != None:
		print(str)
		j += 1
		str = c_char_p( KBSharedMemDataAt( KB_shm_p, i, j ) ).value
	i += 1
	str = c_char_p( KBSharedMemDataAt( KB_shm_p, i, 1 ) ).value

raw_input("hit enter...")

#. . .#

status = c_int( disconnectKB_shm(KB_shm_p, KB_shm_fd) )
if status.value != 0:
	print("ERROR")
	exit(1)

KB_shm_p = c_void_p(0)
KB_shm_fd = c_int(-1)
exit(0)
'''

class KbShmException(Exception):
	pass
#

class KB_shm(object):
	'''
	Třída zastřešující KB_shm.
	'''
	def __init__(self, kb_shm_name=None, multivalue_delim="|"):
		'''
		Inicializace.
		'''
		self.KB_shm_p = c_void_p(0)
		self.KB_shm_fd = c_int(-1)
		self.KB_shm_name = c_char_p(kb_shm_name)
		self.headLine_Boost = {} # Slovník TYPE:{SUBTYPE:LINE(Řádek na kterým je daný typ/podtyp definován)}
		self.headCol_Boost = {} # Slovník LINE:{COLUMN_NAME:COLUMN}
		self.headColCnt_Boost = {} # Slovník LINE:COLUMN_COUNT(Počet sloupců na daném řádku)
		self.headType_Boost = {} # Slovník LINE:(TYPE,SUBTYPE)
		self.multivalue_delim = multivalue_delim
		
		self.data_type_col = None # Sloupec ve kterém je definován typ entity
		
		self._alive = False
		self._prepared = False
	
	def start(self, kb_shm_name=None):
		'''
		Připojí sdílenou paměť.
		'''
		assert not self._alive
		
		if kb_shm_name == None:
			kb_shm_name = self.KB_shm_name
		else:
			kb_shm_name = c_char_p(kb_shm_name)
		
		self.KB_shm_fd = c_int( connectKB_shm(kb_shm_name) )
		if self.KB_shm_fd.value < 0:
			raise KbShmException("connectKB_shm")
		
		self.KB_shm_p = c_void_p( mmapKB_shm(self.KB_shm_fd) )
		if self.KB_shm_p.value == None:
			disconnectKB_shm(self.KB_shm_p, self.KB_shm_fd)
			raise KbShmException("mmapKB_shm")
		
		self._alive = True
		
		self.prepareBoosts()
	
	def end(self):
		'''
		Odpojí sdílenou paměť.
		'''
		if self.KB_shm_fd.value != -1:
			status = c_int(0)
			status = c_int( disconnectKB_shm(self.KB_shm_p, self.KB_shm_fd) )
			if status.value != 0:
				raise KbShmException("disconnectKB_shm")
		
		self.__init__(self.KB_shm_name.value, self.multivalue_delim)
	
	def check(self, kb_shm_name=None):
		'''
		Zkontroluje zda je sdílená paměť k dispozici.
		'''
		if kb_shm_name == None:
			kb_shm_name = self.KB_shm_name
		else:
			kb_shm_name = c_char_p(kb_shm_name)
		
		status = c_int(0)
		status = c_int( checkKB_shm(kb_shm_name) )
		if status.value != 0:
			return False
		else:
			return True
	
	def prepareBoosts(self):
		assert self._alive
		
		self.headLine_Boost = {}
		self.headCol_Boost = {}
		
		# viz https://knot.fit.vutbr.cz/wiki/index.php/Decipher_ner#Sloupce_v_HEAD-KB
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
		
		text = self.headAt(1, 1)
		line = 1
		while text != None:
			splitted = PARSER_FIRST.search(text)
			head_type = splitted.group("TYPE")
			head_subtype = None # NOTE: Potlačení podtypů
			if not self.headLine_Boost.has_key(head_type):
				self.headLine_Boost[head_type] = {}
			
			if head_subtype:
				self.headLine_Boost[head_type][head_subtype] = line
				self.headType_Boost[line] = (head_type, head_subtype)
			else:
				self.headLine_Boost[head_type][""] = line
				self.headType_Boost[line] = (head_type, "")
			print_dbg(str(head_type)+"/"+str(head_subtype)+": "+str(line))
			
			col = 1
			col_name = splitted.group("NAME")
			self.headCol_Boost[line] = {}
			
			while text != None:
				if col > 1:
					splitted = PARSER_OTHER.search(text)
					col_name = splitted.group("NAME")
				
				self.headCol_Boost[line][col_name] = col
				print_dbg(str(line)+", "+str(col_name)+": "+str(col))
				
				if col_name == "TYPE":
					if self.data_type_col is None:
						self.data_type_col = col
					elif self.data_type_col != col:
						raise KbShmException("prepareBoosts: TYPE column must be at same column for each type of entity in HEAD-KB!")
				
				col += 1
				text = self.headAt(line, col)
			
			self.headColCnt_Boost[line] = col - 1
			line += 1
			text = self.headAt(line, 1)
		
		self._prepared = True
	
	def version(self):
		assert self._alive
		return c_uint( KBSharedMemVersion( self.KB_shm_p ) ).value
	
	def headAt(self, line, col):
		assert self._alive
		return c_char_p( KBSharedMemHeadAt( self.KB_shm_p, line, col ) ).value
	
	def headExist(self, ent_type, ent_subtype):
		'''
		headExist("person", "")
		
		@param ent_type
			Název typu entity.
		@param ent_subtype
			Název podtypu entity. Může obsahovat i více podtypů oddělených self.multivalue_delim.
		@return
			Pokud je definován typ \a ent_type a všechny jeho podtypy \a ent_subtype, pak vrátí True, jinak False.
		'''
		assert self._alive
		
		if ent_subtype:
			ent_subtype = [""] + ent_subtype.split(self.multivalue_delim)
		else:
			ent_subtype = [""]
		
		if all(self.headLine(ent_type, st) != None for st in ent_subtype):
			result = True
		else:
			result = False
		return result
	
	def headLine(self, ent_type, ent_subtype):
		'''
		headLine("person", "")
		
		@param ent_type
			Název typu entity.
		@param ent_subtype
			Název podtypu entity. (HEAD-KB obsahuje na jednom řádku jeden podtyp, proto nelze zde zadat více podtypů.)
		@return
			Vrátí číslo řádku na kterém je definován typ \a ent_type a podtyp \a ent_subtype. Dojde-li k chybě, vrátí None.
		'''
		assert self._alive and self._prepared
		
		if self.headLine_Boost.has_key(ent_type) and self.headLine_Boost[ent_type].has_key(ent_subtype):
			result = self.headLine_Boost[ent_type][ent_subtype]
		else:
			result = None
		return result
	
	def headFor(self, ent_type, ent_subtype, col):
		'''
		headFor("person", "", 9)
		
		Pro typ \a ent_type a podtyp \a ent_subtype vrátí název \a col-tého sloupce.
		
		@param ent_type
			Název typu entity.
		@param ent_subtype
			Název podtypu entity. Může obsahovat i více podtypů oddělených self.multivalue_delim.
		@param col
			Sloupec, jehož název chceme zjistit.
		@return
			Vrátí název \a col-tého sloupce. Dojde-li k chybě, vrátí None.
		'''
		assert self._alive and self._prepared
		
		if ent_subtype:
			ent_subtype = [""] + ent_subtype.split(self.multivalue_delim)
		else:
			ent_subtype = [""]
		
		colCnt = 0
		resultCol = None
		line = None
		for st in ent_subtype:
			line = self.headLine(ent_type, st)
			if line == None:
				return None
			
			if col <= (colCnt + self.headColCnt_Boost[line]):
				resultCol = col - colCnt
				break
			else:
				colCnt += self.headColCnt_Boost[line]
		
		if line and resultCol:
			result = self.headAt(line, resultCol)
		else:
			result = None
		return result
	
	def headCol(self, ent_type, ent_subtype, col_name):
		'''
		headCol("person", "", "DATE OF BIRTH")
		
		Pro typ \a ent_type a podtyp \a ent_subtype vrátí číslo sloupce \a col_name.
		
		@param ent_type
			Název typu entity.
		@param ent_subtype
			Název podtypu entity. Může obsahovat i více podtypů oddělených self.multivalue_delim.
		@param col_name
			Název sloupce, jehož číslo chceme zjistit.
		@return
			Vrátí číslo sloupce \a col_name. Dojde-li k chybě, vrátí None.
		'''
		assert self._alive and self._prepared
		
		def headCol_(self, ent_type, ent_subtype, col_name):
			line = self.headLine(ent_type, ent_subtype)
			if line:
				if self.headCol_Boost[line].has_key(col_name):
					result = self.headCol_Boost[line][col_name]
				else:
					return None
			else:
				result = None
			return result
		#
		
		# Jako první se bude sloupec hledat v daném typu a až poté v podtypu (nebo podtypech až to bude aktuální)
		if ent_subtype:
			ent_subtype = [""] + ent_subtype.split(self.multivalue_delim)
		else:
			ent_subtype = [""]
		
		col = 0
		colCnt = 0
		line = None
		for st in ent_subtype:
			col = headCol_(self, ent_type, st, col_name)
			if col:
				col += colCnt
				break
			else:
				line = self.headLine(ent_type, st)
				if line == None:
					return None # NOTE: Vyhodit chybovou hlášku? "None" znamená chybu, jinak OK.
				colCnt += self.headColCnt_Boost[line]
		
		return col
	
	def headType(self, line):
		assert self._alive and self._prepared
		
		if self.headType_Boost.has_key(line):
			return self.headType_Boost[line][0]
		else:
			return None
	
	def headSubtype(self, line):
		assert self._alive and self._prepared
		
		if self.headType_Boost.has_key(line):
			return self.headType_Boost[line][1]
		else:
			return None
	
	def dataAt(self, line, col):
		assert self._alive
		return c_char_p( KBSharedMemDataAt( self.KB_shm_p, line, col ) ).value
	
	def dataFor(self, line, col_name):
		'''
		dataFor(10000, "DATE OF BIRTH")
		'''
		assert self._alive
		
		ent_type = self.dataType(line)
		if ent_type == None:
			return None
		
		ent_subtype = self.dataSubtype(line)
		if ent_subtype == None:
			return None
		
		col = self.headCol(ent_type, ent_subtype, col_name)
		if col == None:
			return None
		
		return self.dataAt(line, col)
	
	def dataType(self, line):
		assert self._alive and self._prepared
		return self.dataAt(line, self.data_type_col)
	
	def dataSubtype(self, line):
		assert self._alive and self._prepared
		col = self.headCol(self.dataType(line), "", "SUBTYPE")
		if isinstance(col, int):
			return self.dataAt(line, col)
		else:
			return ""
	
	@staticmethod
	def getVersionFromSrc(kb_path):
		assert isinstance(kb_path, str)
		
		kb_path = c_char_p(kb_path)
		
		status = c_int(0)
		status = c_int( getVersionFromSrc(kb_path) )
		if status.value < 0:
			raise KbShmException("getVersionFromSrc: %s" % status.value)
		else:
			return status.value
	
	@staticmethod
	def getVersionFromBin(kb_bin_path):
		assert isinstance(kb_bin_path, str)
		
		kb_bin_path = c_char_p(kb_bin_path)
		
		status = c_int(0)
		status = c_int( getVersionFromBin(kb_bin_path) )
		if status.value < 0:
			raise KbShmException("getVersionFromBin: %s" % status.value)
		else:
			return status.value
#

# konec souboru KB_shm.py
