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

""".. currentmodule:: gwvet
#######
Metrics
#######

GWpy VET defines a custom `Metric` object, designed to wrap existing
figure-of-merit functions into a standard format such that they can be
applied conveniently to a set of segments and event triggers.
"""

from .core import (  # noqa: F401
    Metric,
    read_all,
    evaluate,
)
from .registry import (  # noqa: F401
    register_metric,
    get_all_metrics,
    get_metric,
)
from .metrics import (  # noqa: F401
    _use_dqflag,
    deadtime,
    efficiency,
    efficiency_over_deadtime,
    use_percentage,
    safety,
    loudest_event_metric_factory,
    metric_by_column_value_factory,
)

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__all__ = ['Metric', 'register_metric', 'get_metric', 'get_all_metrics',
           'read_all', 'evaluate', 'deadtime', 'efficiency', 'safety',
           'efficiency_over_deadtime', 'use_percentage',
           'loudest_by_column_value_factory', 'loudest_event_metric_factory']
