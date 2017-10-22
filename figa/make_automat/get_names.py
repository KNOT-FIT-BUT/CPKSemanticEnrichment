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

# Author: Lubomír Otrusina, iotrusina@fit.vutbr.cz
# Modify by: Jan Doležal, xdolez52@stud.fit.vutbr.cz
#
# Description: Creates names file with partial person names.

import sys, os
import uuid
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import ner_knowledge_base

# loading knowledge base
kb_daemon_run = True
while kb_daemon_run:
    kb_shm_name = "/decipherKB-daemon_shm-%s" % uuid.uuid4()
    kb = ner_knowledge_base.KnowledgeBaseCZ(kb_shm_name=kb_shm_name)
    kb_daemon_run = kb.check()

try:
    kb.start()
    kb.initName_dict()
    kb.print_subnames()

    PRONOUNS = ["on", "ho", "mu", "o něm", "jím", "ona", "jí", "o ní"]

    for p in PRONOUNS:
        print p
        print p.capitalize()
    
finally:
    kb.end()

# konec souboru get_names.py
