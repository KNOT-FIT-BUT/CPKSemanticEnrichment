#!/usr/bin/env python
# -*- coding: utf-8 -*-

# File:        process_outputs.py
# Author:      Daniel Klimaj, xklima22@stud.fit.vutbr.cz
# Description: Processes outputs of the tool "figa".
# Last edit:   2016-06-19
# Usage:       ./process_outputs.py spath dpath tpath
#              spath Path to file that has to be processed.
#              dpath Path to file in which results should be stored.
#              tpath Path to file with text.

from data_row import DataRow
from data_row_list import DataRowList
from item_list import ItemList
from text_file import TextFile

import re
import os
import sys

TOLERANCE = 15

P_BASE = os.path.dirname(os.path.abspath(__file__))
P_LIST = '/data/lists'

LIST_BLACKLIST     = '{}{}/blist_locations.txt'.format(P_BASE, P_LIST)
LIST_NOTFIRST      = '{}{}/notfirst.txt'.format(P_BASE, P_LIST)
LIST_NATIONALITIES = '{}{}/nationalities.txt'.format(P_BASE, P_LIST)
LIST_REPLACE       = '{}{}/replace.txt'.format(P_BASE, P_LIST)

LIST_NAMES         = '{}{}/names.txt'.format(P_BASE, P_LIST)
LIST_SURRNAMES     = '{}{}/surrnames.txt'.format(P_BASE, P_LIST)

OUT_FILTERED       = '{}/outputs/filtered.txt'.format(P_BASE)
OUT_LEARNED        = '{}/outputs/learned.txt'.format(P_BASE)
OUT_INITIALS       = '{}/outputs/initials.txt'.format(P_BASE)
OUT_NONINITIALS    = '{}/outputs/noninitials.txt'.format(P_BASE)

czech_letters = ['Á', 'Č', 'Ď', 'É', 'Í', 'Ľ', 'Ň', 'Ó', 'Ř', 'Š', 'Ť', 'Ú', 'Ž',]

class InputError(Exception):
    '''
    Custom Exception to handle inputs which are not defined or None.
    '''

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
         return repr('InputError: {}'.format(self.msg))

class Processor(object):

    def __init__(self, figa, text, from_file=False, ffiltered=None, \
    flearned=None, tolerance=15, sf=False):
        '''
        Constructor. Creates Processor object.
        @param figa Path to file with figa outputs or memory reference
        @param text Path to file with text or memory reference
        @param from_file Reads data from files if True, otherwise reads
            data from memory
        @param ffiltered Path to file where filtered items will be written
        @param flearned Path to file where learned items will be written
        @param tolerance Number of chars between 2 words for method
            find_adjacent_names()
        @param sf Writes filtered names in file if True
        '''

        self.from_file = from_file

        if self.from_file:
            if figa and text:
                self.figa_doc = TextFile(figa, 'r')
                self.text_doc = TextFile(text, 'r')
            else:
                raise InputError('One or more paths are missing!')
        else:
            self.figa_doc = TextFile.from_text(figa)
            self.text_doc = TextFile.from_text(text)
            self.text_doc.content = self.text_doc.content.decode('utf-8')

        if flearned != None:
            self.llearned  = TextFile(flearned, 'a')
        else:
            self.llearned = None

        # Load lists
        self.blacklist      = ItemList.from_file(LIST_BLACKLIST)
        self.notfirst       = ItemList.from_file(LIST_NOTFIRST)
        self.nationalities  = ItemList.from_file(LIST_NATIONALITIES)
        self.replacements   = ItemList.from_file(LIST_REPLACE)
        self.list_names     = ItemList.from_file(LIST_NAMES)
        self.list_surrnames = ItemList.from_file(LIST_SURRNAMES)

        self.data_rows = DataRowList()
        self.name_list = DataRowList()
        self.initials  = ItemList()

        self.tolerance     = tolerance
        self.show_filtered = sf

        if sf and ffiltered != None:
            self.lfiltered = TextFile(ffiltered, 'w')
        else:
            self.lfiltered = None

    def read_data(self):
        '''
        Reads file contents and strore them as list data_rows.
        '''

        if self.figa_doc.invalid():
            raise InputError('Figa output is either empty or missing!')

        if self.text_doc.invalid() or self.text_doc.empty():
            raise InputError('Source text is either empty or missing!')

        lines = self.figa_doc.get_lines()
        if lines == [] or lines == None:
            return
        else:
            for line in lines:
                self.data_rows.add(DataRow(line))
            self.data_rows.sort()

    def write(self, path=None):
        '''
        Writes data_rows to file specified by path and closes files.
        @param path Path to file, if path is None then rows are written to STDOUT
        '''

        if not self.name_list.empty():
            self.name_list.sort()

            if path != None:
                f = open(path, 'w')
                for d in self.name_list.items: f.write('{}\n'.format(d.__str__()))
                f.close()
            else:
                for d in self.name_list.items: print('{}'.format(d.__str__()))
        else:
            print('No data to display!')

    def get_data(self):
        '''
        Get valid data rows.
        @return List of DataRows or empty list.
        '''

        dlist = []
        self.name_list.sort()

        if not self.name_list.empty():
            for d in self.name_list.items:
                if(len(d.value.strip().split(' ')) > 1):
                    dlist.append(d)
                else:
                    if self.lfiltered != None:
                        self.lfiltered.write('0\t{}\n'.format(d.value))
            return dlist
        else:
            return []

    def close_all(self):
        '''
        Closes all files used by Processor.
        '''

        self.text_doc.close()
        self.figa_doc.close()
        self.llearned.close()
        if self.lfiltered != None: self.lfiltered.close()

    def replace_parts(self):
        '''
        Checks if string or it's part is in replace list and replaces it with
        empty string accordingly.
        '''

        for i in range(self.name_list.size()):
            for rp in self.replacements:
                if rp in self.name_list[i].value:
                    p_rp  = ItemList.get_parts(rp)
                    p_nli = self.name_list[i].parts

                    if len(p_rp) < len(p_nli):
                        is_whole = True
                        for r in p_rp:
                            for n in p_nli:
                                if r in n and not r == n:
                                    is_whole = False
                                    break

                        if is_whole:
                            self.name_list[i].set_value(\
                                self.name_list[i].value.replace(rp, '').strip())

    def mark_substrings(self):
        '''
        Removes all DataRows which values are substrings of other DataRows.
        '''

        for i in range(self.name_list.size()):
            for j in range(self.name_list.size()):
                if i != j and self.name_list[i] != None and \
                self.name_list[j] != None:
                    ilist = self.name_list[i].parts
                    jlist = self.name_list[j].parts

                    if len(ilist) > len(jlist):
                        all_in = True
                        for jp in jlist:
                            if not jp in ilist:
                                all_in = False

                        if all_in:
                            self.name_list[j].type = 8

        self.name_list.clean()

    def filter_names(self):
        '''
        Filters names from blacklist and invalid names (i.e. On June)
        '''

        names = self.name_list
        for i in range(self.name_list.size()):
            filtered = False
            name     = names[i]

            if name.value == 'Test Testingson': continue

            if self.blacklist.contains(name.value) or \
            self.replacements.contains(name.value):
                names.filter(i, 1)
                continue

            for bl in self.blacklist:
                if bl in name.value:
                    names.filter(i, 1)
                    filtered = True
                    break
            if filtered: continue

            if self.notfirst.contains(name.first()):
                names.filter(i, 2)
                continue

            if  not self.list_names.contains(name.first()) and \
            name.first() not in self.initials:
                names.filter(i, 3)
                continue

            invalid = False
            for p in name.parts:
                if self.nationalities.contains(p):
                    invalid = True
                    break
            if invalid:
                names.filter(i, 5)
                continue

            # Filter names containing only initials
            all_initials = True
            for p in name.parts:
                if len(p) == 2 and p[1] == '.':
                    pass
                else:
                    all_initials = False

            if all_initials:
                names.filter(i, 6)
                continue

            # Do not remove (type 4), just mark
            if name.last() not in self.list_surrnames:
                name.type = 7
                continue

        if self.lfiltered != None and self.show_filtered == True:
            for x in names.filtered:
                self.lfiltered.write("{}\n".format(x.strip()))

        names.clean()

    def find_full_names(self):
        sentences = self.text_doc.content.split('.')
        names = []

        possible_name = []
        current_len = 0
        index = 0
        text = self.text_doc.content.replace('\n', ' ')
        for w in text.split(' '):
            if not w:
                current_len += len(w) + 1
                continue

            if w.endswith('.') or w.endswith(','):
                czech = False
                for letter in czech_letters:
                    if w.startswith(letter):
                        czech = True
                        break
                if ( w[0].isupper() and len(w) > 1 ) or (czech and len(w) > 2):
                    possible_name.append(w[:-1])

                if possible_name and len(possible_name) > 1:
                    name = ' '.join(possible_name)
                    idr = DataRow.from_data(0, index+1 , index + len(name), name)
                    self.name_list.add(idr)
                possible_name = []
                index = 0

            else:
                czech = False

                for letter in czech_letters:
                    if w.startswith(letter):
                        czech = True
                        break

                if (w[0].isupper() and len(w) > 1) or (czech and len(w) > 2):
                    if not possible_name:
                        index = current_len

                    possible_name.append(w)

                else:
                    if len(possible_name) > 1:
                        name = ' '.join(possible_name)
                        idr = DataRow.from_data(0, index+1, index + len(name), name)
                        self.name_list.add(idr)

                    possible_name = []
                    index = 0

            current_len += len(w) + 1

        if len(possible_name) > 1:
            name = ' '.join(possible_name)
            idr = DataRow.from_data(0, index + 1, index + len(name), name)
            self.name_list.add(idr)


        '''
        for s in sentences:
            words = s.split(' ')
            possible_name = []

            for w in words:
                if not w:
                    continue

                czech = False
                for letter in czech_letters:
                    if w.startswith(letter):
                        czech = True
                        break
                if w[0].isupper() and len(w) > 1:
                    possible_name.append(w)
                elif czech and len(w) > 2:
                    possible_name.append(w)
                else:
                    if len(possible_name) >= 2:
                        names.append(' '.join(possible_name))
                    possible_name = []


            if possible_name:
                names.append(' '.join(possible_name))

        print(names)
        for n in names:
            rgx = re.compile('({})'.format(n))
            matches = re.finditer(rgx, self.text_doc.content)
            for m in matches:
                idr = DataRow.from_data(0, m.start()+1, m.end(), n)
                self.data_rows.add(idr)
                self.name_list.add(idr)

        for p in self.get_data():
            print (p)

        self.data_rows.sort()
        '''

    def find_initials(self):
        '''
        Tries to find name initials in the text (J., A., etc.)
        '''

        text_parts = self.text_doc.content.split(' ')
        for p in text_parts:

            if len(p) == 2 and p[0].isupper() and p[1] == '.':
                self.initials.add(p)
            elif p.endswith('.'):
                for letter in czech_letters:
                    if p.startswith(letter):
                        self.initials.add(p)
                        break

        self.initials = set(self.initials)

        for i in self.initials:
            rgx = re.compile('({})'.format(i.replace('.', '\.')))
            matches = re.finditer(rgx, self.text_doc.content)
            for m in matches:
                idr = DataRow.from_data(10, m.start()+1, m.end(), i)
                idr.initial = True
                self.data_rows.add(idr)

        self.data_rows.sort()

    def find_adjacent_names(self):
        '''
        Loops through data rows and attempts to find names.
        '''

        #if self.data_rows.empty():
        #    print('No data have beed read!')
        #    sys.exit(1)

        rows = self.data_rows
        for i in range(rows.size()):
            if len(rows[i].parts) != 1: continue
            if not rows[i].value[0].isupper():
                czech = False
                for letter in czech_letters:
                    if rows[i].value.startswith(letter):
                        czech = True
                        break
                if not czech:
                    continue

            parts = DataRowList.from_string(rows[i])
            if rows[i].processed:
                continue
            else:
                for j in range(i+1, rows.size()):
                    if parts[-1].end_offset == rows[j].start_offset - 2 and \
                    (not parts.contains(rows[j].value) or rows[j].initial):
                        czech = False
                        for letter in czech_letters:
                            if rows[j].value.startswith(letter):
                                czech = True
                                break
                        if rows[j].value[0].isupper() or czech:
                            parts.add(rows[j])
                            rows[j].processed = True
                    else:
                        break

                rows[i].processed = True
                soff = parts[0].start_offset
                eoff = parts[-1].end_offset
                name = ''
                for p in parts: name += p.value + ' '
                self.name_list.add(DataRow.from_data(0, soff, eoff, name.strip()))

        for i in range(self.name_list.size()):
            if len(self.name_list[i].value.split(' ')) <= 1:
                self.name_list[i] = self.name_list[i].clear()

        self.name_list.clean()
        self.data_rows.clear_processed_flag()

    def find_incomplete_names(self):
        '''
        Search for unknown words after known words.
        '''

        chars = ['\'', '.']
        isep  = ['.', ' ']  # separators of initals, e.g. "Aaaa A.A." 
        rows  = self.data_rows

        for i in range(rows.size()):
            if rows[i].processed:
                continue
            else:
                next_name = rows[i+1] if i < rows.size()-1 else None
                if not rows.has_follower(i):
                    start      = rows[i].start_offset
                    word       = rows[i].value + ' '
                    word_start = False
                    position   = rows[i].end_offset+1
                    if position >= self.text_doc.size():
                        break # Nothing else to be found
                    if not self.text_doc.content[position].isupper():
                        continue
                    else:
                        tolerance = position + self.tolerance
                        char      = self.text_doc.content[position]
                        while (char.isalpha() or char.isspace() or char in chars) and \
                        (position < tolerance or char != ' ') and (char != '\n'):
                            if word_start and not char.isupper():
                                break # Not name, end loop
                            else:
                                word_start = False
                            if char == ' ':
                                word_start = True
                            if char == '.':
                                if not ((word[-2] == ' ' or word[-2] == '.') and \
                                word[-1].isupper()):
                                    break # Not initial
                            word     += char
                            position += 1
                            char      = self.text_doc.content[position]
                        words = word.strip().split(' ')
                        words = [x for x in words if x]
                        name  = []
                        for w in words:
                            if w not in name:
                                name.append(w)
                            else:
                                break
                        name = ' '.join(name)
                        end = start + len(name) - 1
                        self.name_list.add(DataRow.from_data(1, start, \
                            end, name))

        self.name_list.sort()
        self.solve_conflicts()

    def solve_conflicts(self):
        '''
        Finds conflicting names and concatenate them into one.
        '''

        names = self.name_list
        if names.size() < 2:
            return

        for i in range(names.size()-1):
            if names[i].processed:
                continue

            if names[i].end_offset > names[i+1].start_offset:
                firts, second = None, None
                if names[i].start_offset < names[i+1].start_offset:
                    first  = names[i]
                    second = names[i+1]
                else:
                    first  = names[i+1]
                    second = names[i]

                fparts = first.parts
                sparts = second.parts
                for sp in sparts:
                    if sp not in fparts: fparts.append(sp)

                new_name              = ' '.join(fparts)
                names[i].type         = 4
                names[i].start_offset = first.start_offset
                names[i].end_offset   = first.start_offset + len(new_name) - 1
                names[i].value        = new_name
                names[i+1].processed  = True
                names[i+1].clear()

        names.clear_processed_flag()
        names.clean()

    def separate_names_with_initials(self):
        '''
        Finds names containing initals and outputs them into file.
        '''

        fi = open(OUT_INITIALS, 'w')
        fn = open(OUT_NONINITIALS, 'w')
        for n in self.name_list.items:
            ok = False
            if '.' in n.value:
                pts = n.value.split(' ')
                for p in pts:
                    if '.' in p and len(p) == 2:
                        ok = True
                        break

            if ok:
                fi.write('{}\n'.format(n.value))
            else:
                fn.write('{}\n'.format(n.value))

        fi.close()
        fn.close()

    def remove_posessions(self):
        '''
        Removes "'s" from the end of names.
        '''

        names = self.name_list
        for i in range(names.size()):
            if names[i].length() > 2:
                if names[i].value[-2:] == "'s":
                    names[i].set_value(names[i].value[:-2])

    def remove_single_names(self):
        '''
        Removes names containing only 1 word.
        '''

        for i in range(self.name_list.size()):
            if len(self.name_list[i].get_parts()) <= 1:
                if self.lfiltered != None:
                    self.lfiltered.write('0\t{}\n'.format(self.name_list[i].value))
                self.name_list.clear(i)
        self.name_list.clean()

    def try_to_learn(self):
        '''
        Learn new words.
        '''

        if self.data_rows == []:
            return

        for item in self.name_list.items:
            if item.type == 1:
                data = item.value.strip().split(' ')

                for i in range(len(data)):
                    in_names  = self.list_names.contains(data[i])
                    in_snames = self.list_surrnames.contains(data[i])
                    
                    if in_names == False and in_snames == False:
                        self.learn(data[i])

    def analyze(self):
        '''
        Preforms all Processor related actions.
        '''

        self.read_data()
        #if self.data_rows.empty():
        #    print('No data have beed read!')
        #    sys.exit(1)

        #self.find_initials()
        #self.find_adjacent_names()
        self.find_full_names()

        self.find_incomplete_names()
        self.replace_parts()

        #self.filter_names()

        # self.separate_names_with_initials()
        self.mark_substrings()
        self.remove_posessions()
        self.remove_single_names()
        self.try_to_learn()


    def learn(self, word):
        '''
        Writes newly learned word into learned.txt file.
        @param word String.
        '''

        if self.llearned != None:
            self.llearned.write('{}\n'.format(word))

if __name__ == '__main__':
    '''
    Main. Accepts 2 arguments.
    @arg spath Path to source file with data.
    @arg dpath Path to destination file, in which results are stored.
    @arg tpath Path to file with text.
    @arg show-filtered Write filtered names in file. Defaults to False.
    '''
    argc = len(sys.argv)

    if not argc in [4, 5]:
        print('USAGE: ./process_outputs spath dpath tpath [show-filtered]')
        sys.exit(1)

    spath = sys.argv[1]
    dpath = sys.argv[2]
    tpath = sys.argv[3]

    sf = False
    if argc == 5:
        if sys.argv[4] in ['--show-filtered', '-sf']:
            sf = True

    if not os.path.exists(spath):
        print('Could not locate file at {}'.format(os.path.abspath(spath)))
        sys.exit(1)

    if not os.path.exists(tpath):
        print('Could not locate file at {}'.format(os.path.abspath(tpath)))
        sys.exit(1)

    if not os.access(os.path.dirname(dpath), os.W_OK):
        print('Can not write file at {}'.format(os.path.abspath(dpath)))
        sys.exit(1)

    d = Processor(spath, tpath, True, OUT_FILTERED, OUT_LEARNED ,TOLERANCE, sf)
    d.analyze()
    d.write(dpath)
    d.close_all()

# END process_outputs.py
