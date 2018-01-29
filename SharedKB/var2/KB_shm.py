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
import sys
import re
from ctypes import CDLL, c_char, c_char_p, c_int, c_uint, c_void_p, POINTER, byref

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
libKB_shm_path = os.path.join(script_dir, "libKB_shm.so")
if not os.path.isfile(libKB_shm_path):
	sys.exit("Could not found " + libKB_shm_path)
libKB_shm = CDLL( libKB_shm_path )

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
	def __init__(self, kb_shm_name=None):
		'''
		Inicializace.
		'''
		self.KB_shm_p = c_void_p(0)
		self.KB_shm_fd = c_int(-1)
		self.KB_shm_name = c_char_p(kb_shm_name)
		self.headFor_Boost = {} # Slovník TYPE:LINE_OF_TYPE(Řádek na kterým je daný typ definován)
		self.headCol_Boost = {} # Slovník LINE_OF_TYPE:{COLUMN_NAME:COLUMN}
		self.headFor_Boost_reverse = {} # Slovník LINE_OF_TYPE:TYPE
		
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
		
		self.__init__(self.KB_shm_name.value)
	
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
		
		self.headFor_Boost = {}
		self.headCol_Boost = {}
		
		text = self.headAt(1, 1)
		line = 1
		while text != None:
			#text = "<person>ID"
			#splitted = re.search('^<([^>]+)>(?:\{((?:\w|[ ])*)(?:\[([^\]]+)\])?\})?((?:\w|[ ])+)$', text)
			#print(splitted.group(4))
			text = text[1:-1]
			self.headFor_Boost[text] = line
			self.headCol_Boost[line] = {}
			#print_dbg(str(text)+": "+str(line))
			col = 1
			self.headCol_Boost[line]["TYPE"] = col
			#print_dbg(str(line)+", "+str("TYPE")+": "+str(col))
			while text != None:
				if col > 1:
					
					splitted = re.search('^(?:\{((?:\w|[ ])*)(?:\[([^\]]+)\])?\})?((?:\w|[ ])+)$', text)
					self.headCol_Boost[line][splitted.group(3)] = col
					print_dbg(str(line)+", "+str(splitted.group(3))+": "+str(col))
				col += 1
				text = self.headAt(line, col)
			line += 1
			text = self.headAt(line, 1)
		self.headFor_Boost_reverse = dict(zip(self.headFor_Boost.values(), self.headFor_Boost.keys()))
		
		self._prepared = True
	
	def version(self):
		assert self._alive
		return c_uint( KBSharedMemVersion( self.KB_shm_p ) ).value
	
	def headAt(self, line, col):
		assert self._alive
		return c_char_p( KBSharedMemHeadAt( self.KB_shm_p, line, col ) ).value
	
	def headFor(self, ent_type, col):
		'''
		headFor("person", 9)
		'''
		assert self._alive
		
		if self.headFor_Boost.has_key(ent_type):
			line = self.headFor_Boost[ent_type]
			result = self.headAt(line, col)
		else:
			result = None
		return result
	
	def headCol(self, ent_type, col_name):
		'''
		headCol("person", "DATE OF BIRTH")
		'''
		assert self._alive
		
		if self.headFor_Boost.has_key(ent_type):
			line = self.headFor_Boost[ent_type]
			
			if self.headCol_Boost[line].has_key(col_name):
				result = self.headCol_Boost[line][col_name]
			else:
				return None
		else:
			result = None
		return result
	
	def headType(self, line):
		assert self._alive
		
		if self.headFor_Boost_reverse.has_key(line):
			return self.headFor_Boost_reverse[line]
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
		
		col = self.headCol(ent_type, col_name)
		if col == None:
			return None
		
		return self.dataAt(line, col)
	
	def dataType(self, line):
		assert self._alive
		return self.dataAt(line, 1)
	
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
