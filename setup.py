#!/usr/bin/env python
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

"""Setup the GWpy VET (`gwvet`) package
"""

import glob
import os.path

from setuptools import (setup, find_packages)

# set basic metadata
PACKAGENAME = 'gwvet'
DISTNAME = 'gwvet'
AUTHOR = 'Duncan Macleod, Alex Urban'
AUTHOR_EMAIL = 'alexander.urban@ligo.org'
LICENSE = 'GPL-3.0-or-later'

cmdclass = {}

# -- versioning ---------------------------------------------------------------

import versioneer
__version__ = versioneer.get_version()
cmdclass.update(versioneer.get_cmdclass())

# -- documentation ------------------------------------------------------------

# import sphinx commands
try:
    from sphinx.setup_command import BuildDoc
except ImportError:
    pass
else:
    cmdclass['build_sphinx'] = BuildDoc

# -- dependencies -------------------------------------------------------------

setup_requires = [
    'setuptools',
    'pytest-runner',
]
install_requires = [
    'astropy>=1.0',
    'decorator',
    'dqsegdb',
    'gwdetchar>=1.0.0',
    'gwpy>=1.0.0',
    'gwsumm>=1.0.1',
    'gwtrigfind',
    'lscsoft-glue>=1.60.0',
    'MarkupPy',
    'matplotlib>=1.5',
    'numpy>=1.7',
    'scipy',
]
tests_require = [
    'pytest>=2.8,<3.7',
    'pytest-cov',
    'flake8',
]
extras_require = {
    'doc': ['sphinx', 'numpydoc', 'sphinx_rtd_theme', 'sphinxcontrib-epydoc'],
}

# -- run setup ----------------------------------------------------------------

packagenames = find_packages()
scripts = glob.glob(os.path.join('bin', '*'))

# read description
with open('README.rst', 'rb') as f:
    longdesc = f.read().decode().strip()

setup(name=DISTNAME,
      provides=[PACKAGENAME],
      version=__version__,
      description=None,
      long_description=longdesc,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      license=LICENSE,
      url='https://github.com/gwpy/vet',
      project_urls={
          "Bug Tracker": "https://github.com/gwpy/vet/issues",
          "Discussion Forum": "https://gwdetchar.slack.com",
          "Source Code": "https://github.com/gwpy/vet",
      },
      packages=packagenames,
      include_package_data=True,
      cmdclass=cmdclass,
      scripts=scripts,
      setup_requires=setup_requires,
      install_requires=install_requires,
      extras_require=extras_require,
      use_2to3=False,
      classifiers=[
          'Programming Language :: Python',
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Science/Research',
          ('License :: OSI Approved :: '
           'GNU General Public License v3 or later (GPLv3+)'),
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Topic :: Scientific/Engineering :: Astronomy',
          'Topic :: Scientific/Engineering :: Physics',
      ],
      )
