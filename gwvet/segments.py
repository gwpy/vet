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

"""Utilities for segment access
"""

from json import loads as decode_json

from astropy.io.registry import _get_valid_format

from glue.lal import Cache

from dqsegdb import urifunctions

from gwpy.time import to_gps
from gwpy.segments import (Segment, SegmentList,
                           DataQualityFlag, DataQualityDict)

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


def get_segments(flags, segments, cache=None,
                 url='https://segdb-er.ligo.caltech.edu', **kwargs):
    """Fetch some segments from the segment database

    Parameters
    ----------
    flags : `str`, `list`
        one of more flags for which to query
    segments : `~gwpy.segments.DataQualityFlag`, `~gwpy.segments.SegmentList`
        span over which to query for flag segments
    cache : `~glue.lal.Cache`, optional
        cache of files to use as data source
    url : `str`
        URL of segment database, if ``cache`` is not given
    **kwargs
        other keyword arguments to pass to either
        `~gwpy.segments.DataQualityFlag.read` (if ``cache`` is given) or
        `~gwpy.segments.DataQualityFlag.query` (otherwise)

    Returns
    -------
    segments : `~gwpy.segments.DataQualityFlag`,
               `~gwpy.segments.DataQualityDict`
        a single `~gwpy.segments.DataQualityFlag` (if ``flags`` is given
        as a `str`), or a `~gwpy.segments.DataQualityDict` (if ``flags``
        is given as a `list`)
    """
    # format segments
    if isinstance(segments, DataQualityFlag):
        segments = segments.active
    elif isinstance(segments, tuple):
        segments = [Segment(to_gps(segments[0]), to_gps(segments[1]))]
    segments = SegmentList(segments)

    # get format for files
    if cache is not None and not isinstance(cache, Cache):
        kwargs.setdefault(
            'format', _get_valid_format('read', DataQualityFlag, None,
                                        None, (cache[0],), {}))

    # populate an existing set of flags
    if isinstance(flags, (DataQualityFlag, DataQualityDict)):
        return flags.populate(source=cache or url, segments=segments,
                              **kwargs)
    # query one flag
    elif cache is None and isinstance(flags, str):
        return DataQualityFlag.query(flags, segments, url=url, **kwargs)
    # query lots of flags
    elif cache is None:
        return DataQualityDict.query(flags, segments, url=url, **kwargs)
    # read one flag
    elif flags is None or isinstance(flags, str):
        segs = DataQualityFlag.read(cache, flags, coalesce=False, **kwargs)
        if segs.known:
            segs.known &= segments
        else:
            segs.known = segments
        segs.active &= segments
        return segs
    # read lots of flags
    else:
        segs = DataQualityDict.read(cache, flags, coalesce=True, **kwargs)
        for name, flag in segs.items():
            flag.known &= segments
            flag.active &= segments
        return segs


def get_known_flags(start, end, url='https://segments.ligo.org', ifo=None,
                    badonly=None):
    """Return the list of all flags with known segments

    Parameters
    ----------
    start : `int`
        the GPS start time of the query
    end : `int`
        the GPS end time of the query
    url : `str`, optional
        the FQDN of the target segment database
    ifo : `str`, optional
        the prefix for the IFO, if `None` all flags are returned

    Returns
    -------
    flags : `list` of `str`
        a list of flag names (<ifo>:<name>:<version>) that are known by
        the database in the given [start, end) interval
    """
    start = int(to_gps(start))
    end = int(to_gps(end))
    uri = '%s/report/known?s=%d&e=%d' % (url, start, end)
    out = decode_json(urifunctions.getDataUrllib2(uri))

    def select_flag(f):
        if ifo is not None and f['ifo'] != ifo:
            return False
        if (badonly is not None and
                f['metadata']['active_indicates_ifo_badness'] != badonly):
            return False
        return True

    return sorted(['%s:%s:%d' % (f['ifo'], f['name'], f['version'])
                   for f in out['results'] if select_flag(f)])
