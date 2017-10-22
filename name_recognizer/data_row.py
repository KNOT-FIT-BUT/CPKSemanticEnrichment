#! /usr/bin/env python

# File:        data_row.py
# Author:      Daniel Klimaj, xklima22@stud.fit.vutbr.cz
# Description: Defines DataRow class.
# Last edit:   2015-05-28

import re

class DataRow(object):

    def __init__(self, data):
        '''
        Constructor. Creates DataRow object from data.
        @param data String with data. Data must be separated with tabs.
        '''

        self.type         = -1
        self.start_offset = None
        self.end_offset   = None
        self.value        = ''
        self.empty        = True
        self.processed    = False
        self.initial      = False
        self.parts        = []
        self.extra_info   = ''

        data = data.strip()

        fragments = data.split("\t")
        if len(fragments) in [4,5]:
            # Skip lines with missing offsets
            if fragments[1] == '' or fragments[2] == '':
                print('Invalid offset(s) in: {}'.format(data))
                return

            # Store values and split into arrays
            frgs = fragments[0].strip().split(';')
            if len(frgs) < 1:
                fragments[0] = "0"
            else:
                fragments[0] = frgs[0]

            self.type         = int(fragments[0].strip())
            self.start_offset = int(fragments[1].strip())
            self.end_offset   = int(fragments[2].strip())
            self.value        = self.decode(fragments[3].strip())
            self.empty        = False
            self.parts        = self.get_parts()
        else:
            print('Invalid data format: {}'.format(data))

    def __lt__(self, other):
        '''
        Comparing.
        '''

        return self.start_offset < other.end_offset

    def __repr__(self):
        '''
        Object representation.
        '''

        return '{}: {}'.format(self.__class__.__name__, self.value)

    def __str__(self):
        '''
        String representation of DataRow.
        '''

        if self.empty: return

        dr_type = self.type
        soffset = str(self.start_offset)
        eoffset = str(self.end_offset)

        return '{}\t{}\t{}\t{}'.format(dr_type, soffset, eoffset, self.value)

    @classmethod
    def from_data(klass, dtype, soffset, eoffset, value):
        return klass('{}\t{}\t{}\t{}'.format(dtype, soffset, eoffset, value))

    def clear(self):
        '''
        Set all fields to empty string thus removing data. Alters caller object.
        '''

        self.type         = -1
        self.start_offset = ''
        self.end_offset   = ''
        self.value        = ''
        self.empty        = True
        self.extra_info   = ''

    def decode(self, string):
        '''
        Converts ASCII characters in string to Unicode.
        @param string String to decode
        @returns Decoded string
        '''

        rgxstr = r'&#x.*?;'
        rgx = re.compile(rgxstr)
        m = rgx.search(string)

        if m == None:
            return string
        else:
            matches = re.findall(rgxstr, string)
            matches = sorted(set(matches))

            for match in matches:
                r = re.compile(r'&#x(.*?);')
                m = r.search(match).group(1)
                #s = bytes.fromhex(m).decode('utf-8') python3 only
                s = str(bytearray.fromhex(m)) # 2/3 compatible
                string = string.replace(match, s)

            return string

    def get_values(self):
        '''
        DataRow to list.
        '''

        return [self.type, self.start_offset, self.end_offset, self.value]

    def get_parts(self):
        p = self.value.split(' ')
        return [x for x in p if x]

    def set_value(self, new):
        new_p = new.strip().split(' ')
        idx   = 0
        if len(new_p) > 0:
            try:
                idx = self.value.index(new_p[0])
            except ValueError:
                print("Error: '{}'' does not contain '{}'".format(self.value, new))
                return

        self.value        = new
        self.start_offset = self.start_offset + idx
        self.end_offset   = self.start_offset + len(self.value) - 1
        self.parts        = self.get_parts()

    def first(self):
        if len(self.parts) > 0:
            return self.parts[0]
        else:
            return None

    def last(self):
        if len(self.parts) > 0:
            return self.parts[-1]
        else:
            return None

    def length(self):
        return len(self.value)

# END data_row.py
