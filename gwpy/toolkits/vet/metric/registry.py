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

from .. import version
__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__version__ = version.version

_METRICS = {}


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
        raise ValueError("Plot %r has already been registered to the %s "
                         "class" % (name, metric.__name__))


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
        raise ValueError("No Metric registered with name %r" % name)


def get_all_metrics():
    """Find all registered metrics.

    Returns
    -------
    metricdict : `dict`
        the (unordered) `dict` of all registered metrics.
    """
    return _METRICS.values()
