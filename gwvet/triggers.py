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

import re

from gwpy.table.filters import in_segmentlist
from gwpy.segments import DataQualityFlag

from gwsumm import globalv
from gwsumm.triggers import (get_triggers, get_times)

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

re_meta = re.compile(r'(\||:|\&)')


def veto(table, flag, tag='', channel='unknown-channel', etg='unknown-etg'):
    """Apply a veto to a set of event table and return survivors
    """
    alabel = veto_tag(channel, flag, tag)
    vlabel = veto_tag(channel, flag, tag, mode='#')
    akey = '%s,%s' % (alabel, etg.lower())
    vkey = '%s,%s' % (vlabel, etg.lower())
    if alabel in globalv.TRIGGERS:
        return get_triggers(alabel, etg, flag.known, query=False)
    else:
        times = get_times(table, etg=etg)
        in_segs = in_segmentlist(times, flag.active)
        vetoed = table[in_segs]
        vetoed.segments = flag.active
        after = table[~in_segs]
        after.segments = flag.known - flag.active
        for t, key in zip([after, vetoed], [akey, vkey]):
            globalv.TRIGGERS[key] = t
        return after


def vetoed(table, flag):
    """Apply a veto to a set of event table and return vetoed events
    """
    if isinstance(flag, DataQualityFlag):
        flag = flag.active
    times = get_times(table, table.meta.get('etg', None))
    vetoed = in_segmentlist(times, flag)
    return table[vetoed]


def veto_tag(channel, flag, tag=None, mode='after'):
    """Create a channel name tag for this veto

    The output is a `str` with the following format:

    <channel name><mode><flag name>,<tag>

    where the 'mode' is one of

    - '#': channel after excluding segments
    - '@': channel after including segments

    Parameters
    ----------
    channel : `str`
        name of channel being vetoed
    flag : `str`
        name of flag doing the vetoing
    tag : `str`
        arbitrary tag for this veto operation, normally the name of the
        enclosing IFO state
    mode : `str`
        one of 'after' or 'vetoed' defining which operation was performed

        - 'after': require events outside flag segments
        - 'vetoed': require events inside flag segments

    Returns
    -------
    tag : `str`
        tag string as described above
    """
    if mode == 'after':
        op = '#'
    else:
        op = '@'
    if isinstance(flag, DataQualityFlag):
        flag = flag.name
    fname = re_meta.sub('-', str(flag))
    if tag is None:
        return '%s%s%s' % (channel, op, fname)
    else:
        return '%s%s%s,%s' % (channel, op, fname, tag)
