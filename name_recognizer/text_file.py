#! /usr/bin/env python

# File:        text_file.py
# Author:      Daniel Klimaj, xklima22@stud.fit.vutbr.cz
# Description: Defines TextFile class.
# Last edit:   2016-07-06

import os
import re

class TextFile(object):
    def __init__(self, path, mode):
        self.content = ""
        self.path    = None
        self.mode    = mode
        self.file    = None

        if path != None:
            self.path = os.path.abspath(path)
            if mode != None:
                self.open()
            else:
                print('Missing file mode for file {}'.format(self.path))

    @classmethod
    def from_text(klass, text, clean_whitespace=False):
        doc = klass(None, None)
        doc.content = text.strip()
        if clean_whitespace:
            rgx = re.compile(r'[^\S\n]')
            doc.content = rgx.sub(' ', doc.content)
            rgx = re.compile(r'\n+')
            doc.content = rgx.sub('\n', doc.content)
        return doc

    def open(self):
        if self.path != None and self.mode != None:
            try:
                self.file = open(self.path, self.mode)
            except IOError:
                print('Could not open file \'{}\''.format(self.path))
                self.file  = None

            if self.file != None and self.mode == 'r':
                self.content = self.file.read()

    def empty(self):
        return True if self.content == "" else False

    def invalid(self):
        return True if self.content == None else False

    def size(self):
        return len(self.content)

    def get_lines(self):
        lines = self.content.split('\n')
        return [x for x in lines if x]

    def close(self):
        if self.file != None:
            self.file.close()
            self.file = None

    def write(self, data):
        if self.file != None:
            self.file.write(data)

# END text_file.py
