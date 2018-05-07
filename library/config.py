#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Tomáš Volf, ivolf[at]fit.vutbr.cz

from enum import Enum


class AutomataVariants(Enum):
	DEFAULT = 0
	LOWERCASE = 1 << 0
	NONACCENT = 1 << 1


	def __and__(self, other):
		"""Support for bitwise operations with this enum"""
		if isinstance(other, int):
			return self.value & other
		elif type(self) is type(other):
			return self.value & other.value

	def __or__(self, other):
		"""Support for bitwise operations with this enum"""
		if isinstance(other, int):
			return self.value | other
		elif type(self) is type(other):
			return self.value | other.value


	@classmethod
	def isLowercase(self, config):
		"""Helper method for bitwise operation"""
		return self.LOWERCASE & config

	@classmethod
	def isNonaccent(self, config):
		"""Helper method for bitwise operation"""
		return self.NONACCENT & config