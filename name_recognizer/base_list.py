#! /usr/bin/env python

# File:        base_list.py
# Author:      Daniel Klimaj, xklima22@stud.fit.vutbr.cz
# Description: Defines BaseList class. Parent class for custom list classes.
# Last edit:   2016-07-06

class BaseList(object):
    def __init__(self):
        self.items = []

    def size(self):
        return len(self.items)

    def empty(self):
        return True if not self.items else False

    def add(self, item):
        self.items.append(item)

    def copy(self):
        return list(self.items)

    def sort(self):
        self.items = sorted(self.items)

    def contains(self, item):
        if item in self.items:
            return True
        else:
            return False

    def __getitem__(self, index):
        return self.items[index]

    def __setitem__(self, index, item):
        self.items[index] = item

    def __iter__(self):
        for i in self.items:
            yield i

# END base_list.py
