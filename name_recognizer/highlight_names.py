#! /usr/bin/env python

# File:        highlight_names.py
# Author:      Daniel Klimaj, xklima22@stud.fit.vutbr.cz
# Description: Markups names in text found by figa.
# Last edit:   2015-05-28
# Usage:       ./highlight_names.py < text > html

from data_row import DataRow

import sys
import os
import re

SPAN0_OPEN = '<span style="color: green;" >'
SPAN1_OPEN = '<span style="color: red;" >'
SPAN2_OPEN = '<span style="color: purple" >'
SPAN8_OPEN = '<span style="color: olive" >'
SPAN7_OPEN = '<span style="color: lime" >'
SPANX_OPEN = '<span style="color: blue;" >'
SPAN_CLOSE = '</span>'
HTML_OPEN  = '<html>\n<body>'
HTML_CLOSE = '</body>\n</html>'

class Name(object):
    def __init__(self, name, soffset, eoffset, dtype):
        '''
        Constructor.
        @param name String.
        @param soffset Starting offset of name.
        @param eoffset Ending offset of name.
        @param dtype Type of name.
        '''

        self.name  = name
        self.count = 1
        self.offsets = [[soffset, eoffset]]
        self.type = dtype
        self.match_starts = []
        self.match_ends = []

    def add_offset(self, soffset, eoffset):
        '''
        Adds offsets to offset list of name.
        @param soffset Start offset.
        @param eoffset End offset.
        '''

        self.offsets.append([soffset, eoffset])
        self.count += 1

    def add_match(self, start, end):
        '''
        Adds match start and end index of the name in the text.
        @param start Start index of match.
        @param end End index of match.
        '''

        self.match_starts.append(start)
        self.match_ends.append(end)

    def __str__(self):
        '''
        To string.
        '''

        return '{}\t{}\t{}\t{}\t{}\t{}'.format(self.name, self.type, \
        self.offsets, self.match_starts, self.match_ends, self.count)

class Partial(object):
    # Handle partial matches

    def __init__(self, name):
        '''
        Constructor.
        @param name String.
        '''

        self.name = name
        self.match_starts = []
        self.match_ends = []

    def add_partial_match(self, start, end):
        '''
        Adds partial match's start and end index in the text.
        @param start Start index of partial match.
        @param end End index of partial match.
        '''

        self.match_starts.append(start)
        self.match_ends.append(end)

def exists(name, name_list):
    '''
    Checks if name exists in name_list.
    @param name String.
    @param name_list List of Name objects.
    @return True if name is in name_list.
    '''

    for n in name_list:
        if name == n.name:
            return True

    return False

def index(name, name_list):
    '''
    Finds name's index.
    @param name String.
    @param name_list List of Name objects.
    @return Name's index or None.
    '''

    for i in range(len(name_list)):
        if name == name_list[i].name:
            return i

    return None

def check_index(i, name_list):
    '''
    Gets information about index by checking name_list. Information is in a
    form of integer pair - first number indicates whether index is start or
    end index of some name, second number stands for name type. Pair [0,0]
    indicates, that index is not start nor end of any name.
    @param i Index.
    @param name_list List of Name objects.
    @return Pair of integers as list.
    '''

    for n in name_list:
        for x in n.match_starts:
            if i == x:
                return [1, n.type]

        for x in n.match_ends:
            if i == x:
                return [-1, n.type]

    return [0, 0]

def check_partial(i, partial_list):
    '''
    Checks whether index is start or end index of partial match. Method shouldn't
    precede check_index method. Method works similary to check_index.
    '''

    for p in partial_list:
        for x in p.match_starts:
            if i == x:
                return [2, 0]

        for x in p.match_ends:
            if i == x:
                return [-2, 0]

    return[0, 0]

def highlight_names(text, datarows):
    '''
    Highlight names.
    @param text Text.
    @param datarows List of DataRow objects.
    '''

    namelist     = []
    partials     = []
    raw_partials = []

    for dr in datarows:
        if not exists(dr.value, namelist):
            namelist.append(Name(dr.value, dr.start_offset, dr.end_offset, \
            dr.type))
        else:
            i = index(dr.value, namelist)
            if i != None:
                namelist[i].add_offset(dr.start_offset, dr.end_offset)

    for i in range(len(namelist)):
        rgx = re.compile('({})'.format(namelist[i].name.strip()), re.M)
        matches = re.finditer(rgx, text)
        matches = list(matches)
        l = len(matches)

        if False: #l < namelist[i].count:
            print('{}, {}'.format(l, namelist[i].count))
            print('Text does not match figa outputs!')
            sys.exit(1)
        else:
            if l > namelist[i].count:
                namelist[i].type = -1

            for m in matches:
                namelist[i].add_match(m.start(), m.end())

        name_parts = namelist[i].name.split(' ')
        for part in name_parts:
            raw_partials.append(part)

    raw_partials = [x for x in raw_partials if x]
    raw_partials = set(raw_partials)
    for rp in raw_partials:
        partials.append(Partial(rp))

    for i in range(len(partials)):
        rgx = re.compile('({})'.format(partials[i].name))
        matches = re.finditer(rgx, text)

        for m in matches:
            partials[i].add_partial_match(m.start(), m.end())

    output = ''
    output += HTML_OPEN

    can_write_partial = True
    in_partial = False
    for i in range(len(text)):
        status = check_index(i, namelist)
        if status == [0, 0] and (can_write_partial or in_partial):
            status = check_partial(i, partials)

        if status[0] == 1:
            if status[1] == -1:
                output += '{}{}'.format(SPANX_OPEN, text[i])
                can_write_partial = False
            elif status[1] == 0:
                output += '{}{}'.format(SPAN0_OPEN, text[i])
                can_write_partial = False
            elif status[1] == 1:
                output += '{}{}'.format(SPAN1_OPEN, text[i])
                can_write_partial = False
            elif status[1] == 7:
                output += '{}{}'.format(SPAN7_OPEN, text[i])
                can_write_partial = False
            elif status[1] == 8:
                output += '{}{}'.format(SPAN8_OPEN, text[i])
                can_write_partial = False
        elif status[0] == -1:
            if status[1] in [-1, 0, 1, 7, 8]:
                output += '{}{}'.format(SPAN_CLOSE, text[i])
                can_write_partial = True
        elif status[0] == 2:
            output += '{}{}'.format(SPAN2_OPEN, text[i])
        elif status[0] == -2:
            output += '{}{}'.format(SPAN_CLOSE, text[i])
        else:
            output += text[i]

    output += HTML_CLOSE
    
    # replace all new line characters to preserve text structure in html
    output = output.replace('\n', '<br />')

    return output

if __name__ == '__main__':
    '''
    Main. No arguments, use stdin and stdout. Expects existence of figa.out file.
    '''

    fr = os.path.abspath('./figa.out')
    if not os.path.exists(fr):
        print('Could not find file "{}"!'.format(fr))
        sys.exit(1)

    f = open(fr)

    datarows = []
    for line in f.readlines():
        datarows.append(DataRow(line.strip()))

    text = sys.stdin.read()
    f.close()

    output = highlight_names(text, datarows)

    print(output)

# END highlight_names.py
