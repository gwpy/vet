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

"""Registry for GWpy VET metics

All metric types should be registered for easy identification from the
configuration INI files
"""

import re

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

_METRICS = {}

REGEX_METRIC_FACTORY = re.compile(
    r'(?P<metric>(.*))\|(\s+)?'  # match metric name,
    r'(?P<column>[\w\s]+)(\s+)?'  # match column name
    r'(?P<operator>[<>=!]+)(\s+)?'  # match operator
    r'(?P<value>(.*))\Z'  # match value (arbitrary text)
)
REGEX_LOUDEST_EVENT_FACTORY = re.compile(
    r'loudest event by (?P<column>[\w\s]+)', re.I)


def register_metric(metric, name=None, force=False):
    """Register a new `Metric` to the given ``name``

    Parameters
    ----------
    metric : `type`
        `Metric` `class` to be registered
    name : `str`, optional
        name against which the metric should be registered.
        If not given the metric.name attribute will be accessed.
    force : `bool`, default: `False`
        overwrite existing registration for this type.

    Returns
    -------
    metric : `Metric`
        the input metric as given (for ease of function chaining)

    Raises
    ------
    ValueError
        if name is already registered and ``force`` not given as `True`
    """
    if name is None:
        name = metric.name
    if force or name.lower() not in _METRICS:
        _METRICS[name.lower()] = metric
    else:
        raise ValueError("A metric has already been registered as %r" % name)
    return metric


def get_metric(name):
    """Query the registry for the metric class registered to the given
    name

    Parameters
    ----------
    name : `str`
        key of metric to be accessed.
    """
    name = re.sub('[\'\"]', '', name)
    try:
        return _METRICS[name.lower()]
    except KeyError:
        # match metric with column restrictions
        try:
            match = REGEX_METRIC_FACTORY.match(name).groupdict()
        except AttributeError:
            pass
        else:
            from .metrics import metric_by_column_value_factory
            return metric_by_column_value_factory(
                match['metric'].rstrip(), match['column'],
                float(match['value']), match['operator'], name=name)
        # match loudest event metric
        try:
            match = REGEX_LOUDEST_EVENT_FACTORY.match(name).groupdict()
        except AttributeError:
            pass
        else:
            from .metrics import loudest_event_metric_factory
            return loudest_event_metric_factory(match['column'])
        raise ValueError("No Metric registered with name %r" % name)


def get_all_metrics():
    """Find all registered metrics.

    Returns
    -------
    metricdict : `dict`
        the (unordered) `dict` of all registered metrics.
    """
    return list(_METRICS.values())
