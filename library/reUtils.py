#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Tomáš Volf, ivolf[at]fit.vutbr.cz

import re


def list2FirstIncaseAlternation(data):
	# ["foo", "bar"] => "([Ff]oo|[Bb]ar)"
	return r"({})".format("|".join(
			map(
				lambda x: (
					"[" + str.upper(x[0]) + str.lower(x[0]) + "]" if x[0].isalpha()
					else x[0]
				) + x[1:],
				map(re.escape, data)
			)
		))