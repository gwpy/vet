# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2014-2015)
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

"""ETG configurations
"""

from gwsumm.plot import get_column_label
from gwsumm.utils import re_cchar

from . import version

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__version__ = version.version


_DEFAULTS = {
    'frequency': 'peak_frequency',
    'snr': 'snr',
    'det': 'snr',
    'det-limits': [3, 100],
    'det-log': True,
}

ETG_PARAMETERS = {}


def register_etg_parameters(name, force=False, **parameters):
    """Store parameters for a new ETG, or override an existing set
    """
    global ETG_PARAMETERS
    if name.lower() in ETG_PARAMETERS and not force:
        raise RuntimeError("ETG parameters already registerd for name %r"
                           % name)
    name = name.lower()
    ETG_PARAMETERS[name] = _DEFAULTS.copy()
    ETG_PARAMETERS[name].update(parameters)
    return ETG_PARAMETERS[name]


def get_etg_parameters(name):
    canon = get_canonical_etg_name(name)
    try:
        return ETG_PARAMETERS[canon]
    except KeyError as e:
        return register_etg_parameters(canon)


# map of equivalent ETG names
ETG_EQUIVALENTS = [
    ['cwb', 'coherent_waveburst', 'waveburst'],
    ['excesspower', 'gstlal_excesspower', 'ep'],
    ['ahope', 'daily_ahope', 'daily cbc', 'inspiral', 'gstlal_inspiral',
     'daily_ahope_bns', 'daily_ahope_nsbh', 'daily_ahope_bbh'],
    ['kleinewelle', 'kw'],
    ['dmtomega', 'dmt_omega'],
]


def get_canonical_etg_name(name):
    name = re_cchar.sub('_', name.lower())
    for group in ETG_EQUIVALENTS:
        if name in group:
            return group[0]
    ETG_EQUIVALENTS.append([name])
    return name


# -----------------------------------------------------------------------------
# register well known ETGs

register_etg_parameters('omicron')
register_etg_parameters('kleinewelle', frequency='central_freq')
register_etg_parameters('excesspower', frequency='central_freq')
register_etg_parameters('cwb', **{
    'frequency': 'central_freq',
    'det': 'amplitude',
    'det-label': get_column_label('rho'),
    'det-limits': [3, 50],
})
register_etg_parameters('ahope', **{
    'frequency': 'template_duration',
    'det': 'new_snr',
    'det-limits': [6, 10],
    'det-log': False,
})
