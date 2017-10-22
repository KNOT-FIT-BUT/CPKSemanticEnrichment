#!/usr/bin/env python
# -*- coding: utf-8 -*-

import name_recognizer
import sys
import os
sys.path.append('/mnt/minerva1/nlp/projects/naki_cpk/xprext00/cz_ner/figa')
import sources.marker as figa

nr = name_recognizer.NameRecognizer()

seek_names = None
output = None

def get_ent_from_figa(input_string):
    global seek_names

    if not seek_names:
        seek_names = figa.marker()
        #print(input_string)
        seek_names.load_dict("/mnt/minerva1/nlp/projects/naki_cpk/xprext00/cz_ner/figa/automata.ct")
        out = seek_names.lookup_string(input_string)
        return out

input_string = open('/mnt/minerva1/nlp/projects/naki_cpk/xprext00/cz_ner/inputfile').read()
input_string = "Autosalon je veřejná přehlídka současných automobilových modelů, novinek nebo konceptů .\
    \
    Jsou nezbytné pro automobilové výrobce a lokální dealery z důvodů styku s veřejností, reklamy a zvýšení publicity.\
    \
    Internationale Automobilausstellung , Frankfurt nad Mohanem .\
    \
    Mondial de l'Automobile , Paříž .\
    \
    Tokyo Motor Show, Tokio .\
    \
    Auto China, Peking .\
    \
    Auto Expo, Nové Dillí .\
    \
    Auto Mobil International, Lipsko .\
    \
    Auto Shanghai, Šanghaj .\
    \
    British Motor Show, Londýn .\
    \
    Essen Motor Show, Essen .\
    \
    LA Auto Show, Los Angeles .\
    \
    MIMS, Moskva .\
    \
    New York International Auto Show, New York .\
    \
    Reisen &amp; Caravan, Erfurt .\
    \
    Retro Classics, Stuttgart .\
    \
    Techno-Classica, Essen .\
    \
    Tuning World Bodensee, Friedrichshafen .\
    \
    Salone dell'automobile di Torino , Turín .\
    \
    Veterama, Mannheim .\
    \
    Vienna Autoshow, Vídeň .\
    \
    Automobilový sport .\
    \
    V tomto článku byl použit překlad textu z článku Auto show na anglické Wikipedii. "

input_string_in_unicode = input_string.decode("utf8", "replace")

output = get_ent_from_figa(input_string)
print(output)

data_rows = nr.recognize_names(input_string, figa_out=output)
print(data_rows)