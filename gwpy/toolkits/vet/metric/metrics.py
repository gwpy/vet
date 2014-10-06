# coding=utf-8
# Copyright (C) Duncan Macleod (2014)
#
# This file is part of GWVeto.
#
# GWVeto is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GWVeto is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GWVeto.  If not, see <http://www.gnu.org/licenses/>.

"""This module defines a number of standard `metrics <Metric>`.
"""

from __future__ import division
from functools import wraps

from astropy.units import Unit

from gwpy.segments import DataQualityFlag

from .. import version
from . import Metric
from .registry import register_metric

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__version__ = version.version


# -----------------------------------------------------------------------------
# Utilities

def _as_dqflag(segments):
    """Convenience method to convert segments if needed
    """
    if isinstance(segments, DataQualityFlag):
        return segments
    else:
        return DataQualityFlag(active=segments)

def _use_dqflag(f):
    """Decorator a method to convert incoming segments into `DataQualityFlag`.
    """
    @wraps(f)
    def decorated_func(segments, *args, **kwargs):
        segments = _as_dqflag(segments)
        return f(segments, *args, **kwargs)
    return decorated_func


# -----------------------------------------------------------------------------
# Standard metrics

@_use_dqflag
def deadtime(segments, *args):
    """The active duration of a given set of segments.

    Parameters
    ----------
    segments : `~gwpy.segments.DataQualityFlag`, `~glue.segments.segmentlist`
        the set of segments to test

    Returns
    -------
    %dt : `float`
        the deadtime of the given segments as a percentage
    """
    return abs(segments.active) / abs(segments.valid) * 100

register_metric(Metric(deadtime, 'Deadtime', unit=Unit('%')))


@_use_dqflag
def efficiency(segments, before, after=None):
    """The decimal fraction of events vetoed by the given segments.

    Parameters
    ----------
    segments : `~gwpy.segments.DataQualityFlag`, `~glue.segments.segmentlist`
        the set of segments to test
    before : `~glue.ligolw.table.Table`
        the event trigger table to test
    after : `~glue.ligolw.table.Table`, optional
        the remaining triggers after vetoes. This is calculated is not given

    Returns
    ------
    %eff : `float`
        the percentage of event triggers that overlap any of the veto segments
    """
    if after is None:
        after = before.veto(segments.active)
    return (len(before) - len(after)) / len(after) * 100

register_metric(Metric(efficiency, 'Efficiency', unit=Unit('%')))


@_use_dqflag
def efficiency_over_deadtime(segments, before, after=None):
    """The ratio of efficiency to deadtime.

    Parameters
    ----------
    segments : `~gwpy.segments.DataQualityFlag`, `~glue.segments.segmentlist`
        the set of segments to test
    before : `~glue.ligolw.table.Table`
        the event trigger table to test
    after : `~glue.ligolw.table.Table`, optional
        the remaining triggers after vetoes. This is calculated is not given

    Returns
    ------
    EDR : `float`
        the ratio of efficiency (%) to deadtime (%)

    Notes
    -----
    This metric function just applies the `efficiency` and `deadtime` metric
    functions and divides one by the other.
    """
    return efficiency(segments, before, after=after) / deadtime(segments)

register_metric(Metric(efficiency_over_deadtime, 'Efficiency/Deadtime',
                       unit=None))
