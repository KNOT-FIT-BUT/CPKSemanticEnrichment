#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

class NatToKB():

	def __init__(self):
		with open(os.path.dirname(__file__) + '/narodnosti.txt') as f:
			self.nationalities = f.read().splitlines()

	def get_nationalities(self):

		nationalities = []

		for nat in self.nationalities:
			nat2 = nat[:-1] + 'ý'
			nationalities.append(nat)
			nationalities.append(nat2)

			if nat[0] in ['Á', 'Č', 'Í', 'Ř', 'Š', 'Ž']:
				nat = nat[0].lower() + nat[1:]
				nat2 = nat2[0].lower() + nat2[1:]
			else:
				nat = nat.lower()
				nat2 = nat2.lower()

			nationalities.append(nat)
			nationalities.append(nat2)

		return nationalities