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

from astropy.units import Unit

from gwpy.segments import DataQualityFlag

from .. import version
from . import Metric
from .registry import register_metric

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__version__ = version.version


def deadtime(self, segments):
    """The active duration of a given set of segments.
    """
    return abs(segments.active) / abs(segments.valid) * 100

register_metric(Metric(deadtime, 'Deadtime', unit=Unit('%')))


def efficiency(self, segments, events):
    """The decimal fraction of events vetoed by the given segments.
    """
    if isinstance(segments, DataQualityFlag):
        segments = segments.active
    if hasattr(events, 'vetoed'):
        vetoed = events.vetoed(segments)
    else:
        raise NotImplementedError("Custom efficiency calculations haven't "
                                    "been implemented yet.")
    return len(vetoed) / len(events)

register_metric(Metric(efficiency, 'Efficiency', unit=Unit('%')))


def efficiency_over_deadtime(self, segments, events):
    """The ratio of efficiency to deadtime.
    """
    return efficiency(segments, events) / deadtime(segments)

register_metric(Metric(efficiency_over_deadtime, 'Efficiency/Deadtime',
                       unit=None))
