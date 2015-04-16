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

import decorator

import numpy

from astropy.units import Unit

from gwpy.segments import DataQualityFlag
from gwpy.table.utils import get_table_column

from .. import version
from . import Metric
from .registry import register_metric

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__version__ = version.version


# -----------------------------------------------------------------------------
# Utilities

@decorator.decorator
def _use_dqflag(f, segments, *args, **kwargs):
    """Decorator a method to convert incoming segments into `DataQualityFlag`.
    """
    if not isinstance(segments, DataQualityFlag):
        segments = DataQualityFlag(active=segments)
    return f(segments, *args, **kwargs)


# -----------------------------------------------------------------------------
# Standard metrics

@_use_dqflag
def deadtime(segments):
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
    if abs(segments.known) == 0:
        return 0
    return float(abs(segments.active)) / float(abs(segments.known)) * 100

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


@_use_dqflag
def use_percentage(segments, before, after=None):
    """The decimal fraction of segments that are used to veto triggers
    """
    times = get_table_column(before, 'time').astype(float)
    used = 0
    for seg in segments.active:
        if numpy.logical_and(times >= float(seg[0]),
                             times < float(seg[1])).any():
            used += 1
    return used / len(segments.active) * 100

register_metric(Metric(
    use_percentage, 'Use percentage', unit=Unit('%')))
