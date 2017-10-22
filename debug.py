#!/usr/bin/env python
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

# ****************************************************
# * Soubor:  debug.py                                *
# * Datum:   2015/02/18                              *
# * Autor:   Jan Doležal, xdolez52@stud.fit.vutbr.cz *
# * Projekt: Decipher - SEC API Extensions           *
# ****************************************************

import sys

# Pro debugování:
import inspect
import traceback
import time
DEBUG_EN = True
#

# FUNKCE A TŘÍDY:

def print_dbg_en(*args, **kwargs):
	delim = kwargs.get("delim", " ")
	stack_num = kwargs.get("stack_num", 1)
	
	callerframerecord = inspect.stack()[stack_num]
	frame = callerframerecord[0]
	info = inspect.getframeinfo(frame)
	
	head = "(%s, %s, %s, time=%r, cpuTime=%r)" % (info.filename, info.function, info.lineno, time.time(), time.clock())
	
	try:
		dbg_msg = map(unicode, args)
	except UnicodeDecodeError:
		dbg_msg = []
		for arg in args:
			if isinstance(arg, unicode):
				dbg_msg.append(arg)
			else:
				dbg_msg.append(unicode(arg, "utf-8"))
	
	dbg_msg = [s.encode("utf-8") for s in dbg_msg]
	dbg_msg = delim.join(dbg_msg)
	
	sys.stderr.write("%s:\n'''\n%s\n'''\n" % (head, dbg_msg))
	sys.stderr.flush()
#

def print_dbg(*args, **kwargs):
	if not DEBUG_EN:
		return
	if "stack_num" not in kwargs:
		kwargs["stack_num"] = 2
	print_dbg_en(*args, **kwargs)
#

def cur_inspect():
	callerframerecord = inspect.stack()[1]
	frame = callerframerecord[0]
	info = inspect.getframeinfo(frame)
	
	head = "(%s, %s, %s, time=%r, cpuTime=%r)" % (info.filename, info.function, info.lineno, time.time(), time.clock())
	
	return head
#

def caller_inspect():
	callerframerecord = inspect.stack()[2]
	frame = callerframerecord[0]
	info = inspect.getframeinfo(frame)
	
	head = "(%s, %s, %s, time=%r, cpuTime=%r)" % (info.filename, info.function, info.lineno, time.time(), time.clock())
	
	return head
#

def cur_traceback():
	formated_traceback = traceback.format_stack()[:-1]
	return "".join(formated_traceback)
#

# konec souboru debug.py
