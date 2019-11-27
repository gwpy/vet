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

import decorator
import operator

import numpy
from scipy.stats import poisson

from astropy.units import Unit

from gwpy.segments import DataQualityFlag

from gwsumm.triggers import get_times

from .core import Metric
from .registry import (get_metric, register_metric)

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

SAFETY_THRESHOLD = 5e-3


# -----------------------------------------------------------------------------
# Utilities

@decorator.decorator
def _use_dqflag(f, segments, *args, **kwargs):
    """Decorator a method to convert incoming segments into `DataQualityFlag`
    """
    if not isinstance(segments, DataQualityFlag):
        segments = DataQualityFlag(active=segments)
    return f(segments, *args, **kwargs)


# -----------------------------------------------------------------------------
# Standard metrics

@_use_dqflag
def deadtime(segments):
    """The active duration of a given set of segments

    Parameters
    ----------
    segments : `~gwpy.segments.DataQualityFlag`, `~glue.segments.segmentlist`
        the set of segments to test

    Returns
    -------
    %dt : `float`
        the deadtime of the given segments as a percentage
    """
    segments = segments.copy().coalesce()
    if abs(segments.known) == 0:
        return 0
    return float(abs(segments.active)) / float(abs(segments.known)) * 100


register_metric(Metric(deadtime, 'Deadtime', unit=Unit('%')))


@_use_dqflag
def efficiency(segments, before, after=None):
    """The decimal fraction of events vetoed by the given segments

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
    try:
        return (len(before) - len(after)) / len(before) * 100
    except ZeroDivisionError:
        return 0.


register_metric(Metric(efficiency, 'Efficiency', unit=Unit('%')))


@_use_dqflag
def efficiency_over_deadtime(segments, before, after=None):
    """The ratio of efficiency to deadtime

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
    try:
        return efficiency(segments, before, after=after) / deadtime(segments)
    except ZeroDivisionError:
        return 0.


register_metric(Metric(efficiency_over_deadtime, 'Efficiency/Deadtime',
                       unit=None))


@_use_dqflag
def use_percentage(segments, before, after=None):
    """The decimal fraction of segments that are used to veto triggers
    """
    try:
        etg = before.etg
    except AttributeError:
        etg = None
    times = get_times(before, etg)
    used = 0
    for seg in segments.active:
        if numpy.logical_and(times >= float(seg[0]),
                             times < float(seg[1])).any():
            used += 1
    try:
        return used / len(segments.active) * 100
    except ZeroDivisionError:
        return 0.


register_metric(Metric(
    use_percentage, 'Use percentage', unit=Unit('%')))


@_use_dqflag
def safety(segments, injections, threshold=SAFETY_THRESHOLD):
    """The safety of these segments with respect to vetoing GW signals

    The 'safety' of a given segment list is determined by comparing the
    number of coincidences between the veto segments and injection segments
    to random chance.

    A segment list is returned as safe (`True`) if the Poisson significance
    of the number of injection coincidences exceeds the threshold (default
    5e-3).

    Parameters
    ----------
    segments : `~gwpy.segments.DataQualityFlag`, `~glue.segments.segmentlist`
        the set of segments to test
    injections : `~glue.segments.segmentlist`
        the set of injections against which to compare
    threshold : `float`, optional, default: 5e-3
        the Poission significance value above which a set of segments is
        declared unsafe

    Returns
    -------
    safe : `bool`
        the boolean statement of whether this segment list is safe (`True`)
        or not (`False`)
    """
    if not isinstance(injections, DataQualityFlag):
        injections = DataQualityFlag(active=injections)
    # segment info
    deadtime = float(abs(segments.active))
    livetime = float(abs(segments.known))
    # injection coincidence
    numveto = len([inj for inj in injections.active if
                   inj.intersects(segments)])
    numexp = len(injections) * deadtime / livetime
    # statistical significance
    prob = 1 - poisson.cdf(numveto - 1, numexp)
    return prob < threshold


register_metric(Metric(safety, 'Safety', unit=None))


def loudest_event_metric_factory(column):
    column = column.lower()
    @_use_dqflag
    def loudest_event(segments, before, after=None):
        """Percentage reduction in the amplitude of the loudest event by %s

        Parameters
        ----------
        segments : `DataQualityFlag`, `~glue.segments.segmentlist`
            the set of segments to test
        before : `~glue.ligolw.table.Table`
            the event trigger table to test
        after : `~glue.ligolw.table.Table`, optional
            the remaining triggers after vetoes.
            This is calculated is not given

        Returns
        ------
        reduction : `float`
            the percentage reduction in the amplitude of the loudest event
        """
        if after is None:
            after = before.veto(segments.active)
        try:
            brank = before[column].max()
        except ValueError:  # no triggers to start with
            return 0
        try:
            arank = after[column].max()
        except ValueError:  # no triggers after veto
            return 100
        return (brank - arank) / brank * 100
    loudest_event.__doc__ %= column
    return register_metric(Metric(
        loudest_event, 'Loudest event by %s' % column, unit=Unit('%')))


# -- generic factory method ---------------------

OPERATORS = {
    '<': operator.lt,
    '<=': operator.le,
    '=': operator.eq,
    '>=': operator.ge,
    '>': operator.gt,
    '==': operator.is_,
    '!=': operator.is_not,
}


def metric_by_column_value_factory(metric, column, threshold, operator='>=',
                                   name=None):
    metric = get_metric(metric)
    try:
        op = OPERATORS[operator]
    except KeyError as e:
        e.args = ("Cannot parse operator %r, choose one of : %s"
                  % (operator, ', '.join(list(OPERATORS.keys()))))

    @_use_dqflag
    def metric_by_column_value(segments, before, after=None):
        b = before.filter((column.lower(), op, threshold))
        if after is None:
            a = None
        else:
            a = after.filter((column.lower(), op, threshold))
        return metric(segments, b, after=a)

    tag = ' (%s %s %s)' % (column, operator, threshold)
    metric_by_column_value.__doc__ = metric.description.splitlines()[0] + tag
    if name is None:
        name = metric.name + tag
    return register_metric(Metric(metric_by_column_value, name,
                                  unit=metric.unit))
