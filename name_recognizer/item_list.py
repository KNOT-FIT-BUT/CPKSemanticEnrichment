#! /usr/bin/env python

# File:        doc_list.py
# Author:      Daniel Klimaj, xklima22@stud.fit.vutbr.cz
# Description: Defines DocList class.
# Last edit:   2016-07-06

from base_list import BaseList
import os

class ItemList(BaseList):
    '''
    Class to handle lists stored in documents.
    '''

    def __init__(self):
        BaseList.__init__(self)
        self.path = None

    @classmethod
    def from_file(klass, path):
        il = klass()
        il.path = os.path.abspath(path)
        il.reload()
        return il

    def _get_list(self):
        '''
        Get contents of file at path and return list.
        @param path Path to file.
        '''

        tlist = []
        try:
            f = open(self.path)
            for line in f.readlines():
                tlist.append(line.strip())
        except IOError:
            print('File {} not found!'.format(self.path))
            return []
        else:
            f.close()
            return tlist

    def reload(self):
        self.items = self._get_list()

    @staticmethod
    def get_parts(item):
        p = item.split(' ')
        return [x for x in p if x]

# END doc_list.py
