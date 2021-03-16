# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2013)
#
# This file is part of the GWpy VET python package.
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

"""Setup the GW Veto Evaluation and Testing (`gwvet`) package
"""

import versioneer

from setuptools import setup

version = versioneer.get_version()
cmdclass = versioneer.get_cmdclass()

try:
    from sphinx.setup_command import BuildDoc
except ImportError:
    pass
else:
    cmdclass['build_sphinx'] = BuildDoc

# run setup
# NOTE: all other metadata and options come from setup.cfg
setup(
    version=version,
    project_urls={
        "Bug Tracker": "https://github.com/gwpy/vet/issues",
        "Discussion Forum": "https://gwdetchar.slack.com",
        "Source Code": "https://github.com/gwpy/vet",
    },
    cmdclass=cmdclass,
)
