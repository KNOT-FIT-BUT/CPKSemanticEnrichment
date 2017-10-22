#! /usr/bin/env python

# File:        data_row_list.py
# Author:      Daniel Klimaj, xklima22@stud.fit.vutbr.cz
# Description: Defines DataRowList class.
# Last edit:   2016-07-06

from base_list import BaseList
from data_row import DataRow

class DataRowList(BaseList):
    def __init__(self):
        BaseList.__init__(self)
        self.filtered = []

    @classmethod
    def from_string(klass, s):
        drl = klass()
        drl.add(s)
        return drl

    def sort(self):
        self.clean()
        self.items = sorted(self.items)

    def clean(self):
        self.items = [x for x in self.items if x and not x.empty]

    def contains(self, value):
        for item in self.items:
            if value == item.value:
                return True
        return False

    def clear_processed_flag(self):
        for i in range(self.size()):
            self.items[i].processed = False

    def has_follower(self, index):
        self.sort()
        if(index >= self.size()-1 or index < 0):
            return False
        elif(self.items[index+1].start_offset - self.items[index].end_offset != 2):
            return False
        else:
            return True

    def clear(self, idx):
        self.items[idx].clear()

    def filter(self, idx, reason, clean = False):
        if idx < self.size():
            self.filtered.append("{}\t{}".format(reason, self.items[idx].value))
            self.clear(idx)
            if clean:
                self.clean()

# END data_row_list.py
