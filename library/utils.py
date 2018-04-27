#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Tomáš Volf, ivolf[at]fit.vutbr.cz

import unicodedata


def remove_accent(_string):
    """Removes accents from a string. For example, Eduard Ovčáček -> Eduard Ovcacek."""
    nkfd_form = unicodedata.normalize('NFKD', _string)
    return str("".join([c for c in nkfd_form if not unicodedata.combining(c)]))