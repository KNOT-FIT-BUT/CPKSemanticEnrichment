#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from KB_shm import *

# # TESTOVACÍ KONSTANTY # #
SLOUPEC = 8
# # # # # # # # # # # # # #

KB_shm_p = c_void_p(0)
KB_shm_fd = c_int(-1)
status = c_int(0)

# Připojení KB
KB_shm_fd = c_int( connectKB_shm("SharedKB-speedtest") )
if KB_shm_fd.value < 0:
	sys.stderr.write("ERROR: connectKB_shm()")
	exit(1)

KB_shm_p = c_void_p( mmapKB_shm(KB_shm_fd) )
if KB_shm_p.value == None:
	sys.stderr.write("ERROR: mmapKB_shm()")
	disconnectKB_shm(KB_shm_p, KB_shm_fd)
	exit(1)

#. . .#

i = 1
string = c_char_p( KBSharedMemDataAt( KB_shm_p, i, SLOUPEC ) ).value
if string == None and c_char_p( KBSharedMemDataAt( KB_shm_p, i, 1 ) ).value != None:
	string = ""
while string != None:
	print(string)
	i += 1
	string = c_char_p( KBSharedMemDataAt( KB_shm_p, i, SLOUPEC ) ).value
	if string == None and c_char_p( KBSharedMemDataAt( KB_shm_p, i, 1 ) ).value != None:
		string = ""

#. . .#

status = c_int( disconnectKB_shm(KB_shm_p, KB_shm_fd) )
if status.value != 0:
	sys.stderr.write("ERROR: disconnectKB_shm()")
	exit(1)

KB_shm_p = c_void_p(0)
KB_shm_fd = c_int(-1)
print("lines:", i)
exit(0)

# konec souboru benchmark.py
