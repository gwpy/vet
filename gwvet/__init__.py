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

"""Gravitational-Wave Veto Evaluation and Testing suite
"""

from ._version import get_versions

__version__ = get_versions()['version']
__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

from gwsumm.segments import get_segments  # noqa: F401
from gwsumm.triggers import get_triggers  # noqa: F401

from .metric import (  # noqa: F401
    _use_dqflag,
    deadtime,
    efficiency,
    efficiency_over_deadtime,
    use_percentage,
    safety,
    loudest_event_metric_factory,
    metric_by_column_value_factory,
)

del get_versions
