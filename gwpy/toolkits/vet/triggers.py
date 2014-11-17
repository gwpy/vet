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

from . import version

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__version__ = version.version

from glue.lal import Cache

from gwpy.table import lsctables
from gwpy.table.io import trigfind
from gwpy.table.utils import get_row_value
from gwpy.time import to_gps
from gwpy.segments import (Segment, SegmentList, DataQualityFlag)

ETG_TABLE = {
    # single-IFO burst
    'omicron': lsctables.SnglBurstTable,
    'omega': lsctables.SnglBurstTable,
    'omegadq': lsctables.SnglBurstTable,
    'kleinewelle': lsctables.SnglBurstTable,
    'kw': lsctables.SnglBurstTable,
    'dmtomega': lsctables.SnglBurstTable,
    'dmt_wsearch': lsctables.SnglBurstTable,
    # multi-IFO burst
    'cwb': lsctables.MultiBurstTable,
    # single-IFO inspiral
    'daily_ihope': lsctables.SnglInspiralTable,
    'daily_ahope': lsctables.SnglInspiralTable,
}


def get_etg_table(etg):
    """Find which table should be used for the given etg

    Parameters
    ----------
    etg : `str`
        name of Event Trigger Generator for which to query

    Returns
    -------
    table : `~gwpy.table.Table`
        LIGO_LW table registered to the given ETG

    Raises
    ------
    KeyError
        if the ETG is not registered
    """
    try:
        return ETG_TABLE[etg.lower()]
    except KeyError as e:
        e.args = ('No LIGO_LW table registered to etg %r' % etg,)
        raise


def register_etg_table(etg, table, force=False):
    """Register a specific LIGO_LW table to an ETG

    Parameters
    ----------
    etg : `str`
        name of Event Trigger Generator to register
    table : `~gwpy.table.Table`, `str`
        `Table` class to register, or the ``tableName`` of the relevant class
    force : `bool`, optional, default: `False`
        overwrite an existing registration for the given ETG

    Raises
    ------
    KeyError
        if a `str` table cannot be resolved to a specific class
    """
    if isinstance(table, str):
        try:
            table = lsctables.TableByName[etg]
        except KeyError as e:
            e.args = ('Cannot parse table name %r' % table,)
    if etg.lower() in ETG_TABLE and not force:
        raise KeyError('LIGO_LW table already registered to etg %r' % etg,)
    ETG_TABLE[etg.lower()] = table
    return table


def get_triggers(channel, etg, segments, table=None, columns=None, cache=None):
    """Fetch a set of event triggers for the given channel

    Parameters
    ----------
    channel : `str`, `~gwpy.detector.Channel`
        name of channel for which to search
    etg : `str`
        name of Event Trigger Generator for which to search
    segments : `~gwpy.segments.DataQualityFlag`, `~gwpy.segments.SegmentList`
        span over which to read triggers
    table : `type`, optional
        table class to read into, e.g. `~gwpy.table.lsctables.SnglBurstTable`
    columns : `list` of `str`, optional
        `list` of column names to read, defaults to all valid columns
    cache : `~glue.lal.Cache`, optional
        cache of files to use as data source. If not given, the :meth:`fetch`
        method of the relevant table class will be used to find and read the
        triggers

    Returns
    -------
    table : `~gwpy.table.Table`
        a LIGO_LW `Table` object, filled with rows
    """
    # format segments
    if isinstance(segments, DataQualityFlag):
        segments = segments.active
    elif isinstance(segments, tuple):
        segments = [Segment(to_gps(segments[0]), to_gps(segments[1]))]
    segments = SegmentList(segments)
    # get table class
    if table is None:
        table = get_etg_table(etg)
    elif isinstance(table, str):
        table = TableByName[table]
    form = etg
    # make new table instance
    new = lsctables.New(table, columns=columns)
    new.segments = type(segments)()
    # read new triggers
    for segment in segments:
        segment = type(segment)(map(float, segment))
        filter_ = lambda t: float(get_row_value(t, 'time')) in segment
        if cache is None:
            c2 = trigfind.find_trigger_urls(str(channel), etg, segment[0],
                                            segment[1])
            form = 'ligolw'
        else:
            if isinstance(cache, Cache):
                c2 = cache.sieve(segment=segment)
            else:
                c2 = cache
            form = etg
        new.extend(table.read(c2, columns=columns, filt=filter_, format=form))
        new.segments.append(segment)

    return new


