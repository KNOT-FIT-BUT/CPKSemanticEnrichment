#! /usr/bin/env python

# File:        process_outputs.py
# Author:      Daniel Klimaj, xklima22@stud.fit.vutbr.cz
# Description: Interface for process_outputs and highlight_names
# Last edit:   2015-07-27
# Usage:       ./name_recognizer.py

import os
import subprocess as sp

import process_outputs as po
import highlight_names as hn

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

class NameRecognizer(object):

    def __init__(self, figa_path=None, fsa_path=None, show_filtered=False):
        '''
        Constructor.
        @param figa_path Path to figa binary.
        @param fsa_path Path to .fsa file.
        @param show_filtered Writes filtered names into file if set to True.
            Defaults to False.
        '''

        self.set_figa_path(figa_path)
        self.set_automata_path(fsa_path)
        self.show_filtered = show_filtered

    def _prepare_lists(self):
        '''
        Checks existency of mandatory files and folders and
        creates them if needed.
        '''

        data_dir  = "{}/data".format(SCRIPT_PATH)
        list_dir  = "{}/data/lists".format(SCRIPT_PATH)
        out_dir   = "{}/outputs".format(SCRIPT_PATH)

        blist     = "{}/data/lists/blist_locations.txt".format(SCRIPT_PATH)
        notfirst  = "{}/data/lists/notfirst.txt".format(SCRIPT_PATH)
        onlyfirst = "{}/data/lists/onlyfirst.txt".format(SCRIPT_PATH)

        learned   = "{}/outputs/learned.txt".format(SCRIPT_PATH)
        filtered  = "{}/outputs/filtered.txt".format(SCRIPT_PATH)

        try:
            if not os.path.exists(data_dir):
                os.mkdir(data_dir)

            if not os.path.exists(list_dir):
                os.mkdir(list_dir)

            if not os.path.exists(out_dir):
                os.mkdir(out_dir)

            if not os.path.exists(blist):
                open(blist, 'w').close()

            if not os.path.exists(notfirst):
                open(notfirst, 'w').close()

            if not os.path.exists(onlyfirst):
                open(onlyfirst, 'w').close()

            if not os.path.exists(learned):
                open(learned, 'w').close()

            if not os.path.exists(filtered):
                open(filtered, 'w').close()
        except:
            print("An error occured while creating necessary files and directories!")
            return False

        return True

    def _process(self, text):
        '''
        Uses figa tool and automata to gain disambiguated entities of text which
        are then processed to contain only name entities.
        @param text String.
        @return Name entities or None on error.
        '''

        result = None
        err    = None

        if self.figa_path == None or self.fsa_path == None:
            return None

        try:
            process = [self.figa_path, "-d", self.fsa_path, "-p"]
            p = sp.Popen(process, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
            result, err = p.communicate(text)
        except Exception as e:
            print("An error occured while processing data with figa:\n{}".format(e))
            return None

        if err != None and err != "":
            print(err)
            return None

        return result

    def set_figa_path(self, path):
        '''
        Sets path to figa tool if path exists.
        @param path Path to figa.
        '''

        if path == None:
            self.figa_path = None
        else:
            if os.path.exists(path):
                self.figa_path = path
            else:
                print('NameRecognizer Error: Invalid path {}'.format(path))

    def set_automata_path(self, path):
        '''
        Sets path to automata if path exists.
        @param path Path to automata.
        '''

        if path == None:
            self.fsa_path = None
        else:
            if os.path.exists(path):
                self.fsa_path = path
            else:
                print('NameRecognizer Error: Invalid path {}'.format(path))

    def recognize_names(self, data, figa_out=None, print_result=False):
        '''
        Process data.
        @param data Text.
        @param figa_out Directly pass figa outputs.
        @param print_result Prints result if True.
        @return Recognized names
        '''

        status = self._prepare_lists()
        if not status:
            return None

        fo = figa_out
        if figa_out == None:
            fo = self._process(data)

        p = po.Processor(fo, data, False, po.OUT_FILTERED, po.OUT_LEARNED, \
            po.TOLERANCE, self.show_filtered)
        p.analyze()
        rslt = p.get_data()
        p.close_all()

        if print_result:
            for r in rslt:
                print(r)

        return rslt

    def highlight(self, text, figa_outs):
        '''
        Highlight names in text according to outputs in figa_outs.
        @param text Text.
        @param figa_outs Processed and sorted outputs produced by Figa tool.
            Use process method first.
        @return Highlighted text in HTML format.
        '''

        return hn.highlight_names(text, figa_outs)

if __name__ == "__main__":
    '''
    For testing purpose. No arguments required.
    '''

    data = open("{}/../data/input/example_input2".format(SCRIPT_PATH)).read()
    figa = os.path.abspath("{}/../figa/figav08".format(SCRIPT_PATH))
    fsa  = os.path.abspath("{}/../figa/automata.fsa".format(SCRIPT_PATH))

    nr = NameRecognizer(figa, fsa)
    rows = nr.recognize_names(data)

    print("Test recognize_names method:")
    if rows != []:
        for r in rows:
            print(r)

    #print("\nTest highlight method:")
    #print(nr.highlight(data, rows))

# END name_recognizer.py
