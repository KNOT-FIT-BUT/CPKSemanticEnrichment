#!/usr/bin/env python
# -*- coding: utf-8 -*-

class NatToKB():

    def __init__(self):

        with open('narodnosti.txt') as f:
            self.nationalities = f.read().splitlines()

    def get_nationalities(self):

        nationalities = []

        for nat in self.nationalities:
            nat2 = nat[:-2] + 'ý'
            nationalities.append(nat)
            nationalities.append(nat2)

            if nat.startswith('Č'):
                nat = 'č' + nat[2:]
                nat2 = 'č' + nat2[2:]
            elif nat.startswith('Á'):
                nat = 'á' + nat[2:]
                nat2= 'á' + nat2[2:]
            elif nat.startswith('Ř'):
                nat = 'ř' + nat[2:]
                nat2 = 'ř' + nat2[2:]
            elif nat.startswith('Š'):
                nat = 'š' + nat[2:]
                nat2 = 'š' + nat2[2:]
            elif nat.startswith('Ž'):
                nat = 'ž' + nat[2:]
                nat2 = 'ž' + nat2[2:]
            else:
                nat = nat.lower()
                nat2 = nat2.lower()

            nationalities.append(nat)
            nationalities.append(nat2)

        return nationalities