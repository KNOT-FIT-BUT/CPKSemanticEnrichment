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
from ctypes import CDLL, c_char, c_char_p, c_int, c_uint, c_void_p, POINTER, byref

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
connectKB_shm = libKB_shm.connectKB_shm
connectKB_shm.argtypes = []
connectKB_shm.restype = c_int

mmapKB_shm = libKB_shm.mmapKB_shm
mmapKB_shm.argtypes = [c_int]
mmapKB_shm.restype = c_void_p

disconnectKB_shm = libKB_shm.disconnectKB_shm
disconnectKB_shm.argtypes = [c_void_p, c_int]
disconnectKB_shm.restype = c_int

# Funkce pro získání řetězců
'''
KBSharedMemDataAt( KB_shm_p, 1 )
c_char_p( KBSharedMemDataAt( KB_shm_p, 1 ) )
print( c_char_p( KBSharedMemDataAt( KB_shm_p, 1 ) ).value )

print( c_char_p( KBSharedMemHeadFor( KB_shm_p, 'p' ) ).value )
'''
KBSharedMemHeadAt = libKB_shm.KBSharedMemHeadAt
KBSharedMemHeadAt.argtypes = [c_void_p, c_uint]
KBSharedMemHeadAt.restype = c_void_p

KBSharedMemHeadFor = libKB_shm.KBSharedMemHeadFor
KBSharedMemHeadFor.argtypes = [c_void_p, c_char]
KBSharedMemHeadFor.restype = c_void_p

KBSharedMemHeadFor_Boost = libKB_shm.KBSharedMemHeadFor_Boost
KBSharedMemHeadFor_Boost.argtypes = [c_void_p, c_char, POINTER(c_uint)]
KBSharedMemHeadFor_Boost.restype = c_void_p

KBSharedMemDataAt = libKB_shm.KBSharedMemDataAt
KBSharedMemDataAt.argtypes = [c_void_p, c_uint]
KBSharedMemDataAt.restype = c_void_p

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

i = 1
str = c_char_p( KBSharedMemHeadAt( KB_shm_p, i ) ).value
while str != None:
	print(str)
	i += 1
	str = c_char_p( KBSharedMemHeadAt( KB_shm_p, i ) ).value

raw_input("hit enter...")

str = c_char_p( KBSharedMemHeadFor( KB_shm_p, 'p' ) ).value
print(str)

raw_input("hit enter...")

i = 1
str = c_char_p( KBSharedMemDataAt( KB_shm_p, i ) ).value
while str != None:
	print(str)
	i += 1
	str = c_char_p( KBSharedMemDataAt( KB_shm_p, i ) ).value

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

class KB_shm:
	'''
	Třída zastřešující KB_shm.
	'''
	def __init__(self):
		'''
		Inicializace.
		'''
		self.KB_shm_p = c_void_p(0)
		self.KB_shm_fd = c_int(-1)
		self.headFor_Boost = {}

	def start(self):
		'''
		Připojí sdílenou paměť.
		'''
		self.KB_shm_fd = c_int( connectKB_shm() )
		if self.KB_shm_fd.value < 0:
			RuntimeError("connectKB_shm")

		self.KB_shm_p = c_void_p( mmapKB_shm(self.KB_shm_fd) )
		if self.KB_shm_p.value == None:
			disconnectKB_shm(self.KB_shm_p, self.KB_shm_fd)
			RuntimeError("mmapKB_shm")

	def end(self):
		'''
		Odpojí sdílenou paměť.
		'''
		status = c_int(0)
		status = c_int( disconnectKB_shm(self.KB_shm_p, self.KB_shm_fd) )
		if status.value != 0:
			RuntimeError("disconnectKB_shm")

		self.__init__()

	def headAt(self, line):
		return c_char_p( KBSharedMemHeadAt( self.KB_shm_p, line ) ).value

	def headFor(self, prefix):
		if self.headFor_Boost.has_key(prefix):
			result = c_char_p( KBSharedMemHeadAt( self.KB_shm_p, self.headFor_Boost[prefix] ) ).value
		else:
			line = c_uint(0)
			result = c_char_p( KBSharedMemHeadFor_Boost( self.KB_shm_p, prefix, byref(line) ) ).value
			self.headFor_Boost[prefix] = line
		return result

	def dataAt(self, line):
		return c_char_p( KBSharedMemDataAt( self.KB_shm_p, line ) ).value
#

# konec souboru KB_shm.py
