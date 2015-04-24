# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2014)
#
# This file is part of GWpy VET.
#
# GWpy VET is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GWpy VET is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GWpy VET.  If not, see <http://www.gnu.org/licenses/>.

"""Utilities for trigger reading
"""

from __future__ import print_function
import re

from . import version

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__version__ = version.version

from gwpy.table.utils import get_row_value
from gwpy.segments import DataQualityFlag

from gwsumm import globalv
from gwsumm.triggers import get_triggers

re_meta = re.compile('(\||:|\&)')


def veto(table, flag, tag=''):
    """Apply a veto to a set of event table and return survivors
    """
    fname = re_meta.sub('-', flag.name)
    alabel = '%s-%s%s' % (table.channel, fname, tag)
    vlabel = '%s@%s%s' % (table.channel, fname, tag)
    akey = '%s,%s' % (alabel, table.etg.lower())
    vkey = '%s,%s' % (vlabel, table.etg.lower())
    if alabel in globalv.TRIGGERS:
        return get_triggers(alabel, table.etg, flag.known, query=False)
    else:
        after = table.copy()
        vetoed = table.copy()
        segs = flag.active
        get = get_row_value
        for row in table:
            if float(get(row, 'time')) in segs:
                vetoed.append(row)
            else:
                after.append(row)
        for t, key in zip([after, vetoed], [akey, vkey]):
            t.segments = flag.known
            t.channel = table.channel
            t.etg = table.etg
            globalv.TRIGGERS[key] = t
        return after


def vetoed(table, flag):
    """Apply a veto to a set of event table and return vetoed events
    """
    if isinstance(flag, DataQualityFlag):
        flag = flag.active
    after = table.copy()
    for row in table:
        if float(get_row_value(row, 'time')) in flag:
            after.append(row)
    return after
