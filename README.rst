=====
GWVET
=====

The Gravitational-wave Veto Evaluation and Testing suite (`python:gwvet`) is
a plugin for `GWSumm`_ designed to enable and assist with review of
data-quality veto products.

|PyPI version| |Conda version|

|License| |Supported Python versions|

|Build Status| |Coverage Status|

Installation
------------

GWVET is best installed with `conda`_:

.. code:: bash

   conda install -c conda-forge gwvet

but can also be installed with `pip`_:

.. code:: bash

   python -m pip install gwvet

------------
Contributing
------------

All code should follow the Python Style Guide outlined in `PEP 0008`_;
users can use the `flake8`_ package to check their code for style issues
before submitting.

See `the contributions guide`_ for the recommended procedure for
proposing additions/changes.

.. _GWSumm: https://github.com/gwpy/gwsumm
.. _conda: https://conda.io
.. _pip: https://pip.pypa.io/en/stable/
.. _PEP 0008: https://www.python.org/dev/peps/pep-0008/
.. _flake8: http://flake8.pycqa.org
.. _the contributions guide: https://github.com/gwpy/vet/blob/master/CONTRIBUTING.md

.. |PyPI version| image:: https://badge.fury.io/py/gwvet.svg
   :target: http://badge.fury.io/py/gwvet
.. |Conda version| image:: https://img.shields.io/conda/vn/conda-forge/gwvet.svg
   :target: https://anaconda.org/conda-forge/gwvet/
.. |License| image:: https://img.shields.io/pypi/l/gwvet.svg
   :target: https://choosealicense.com/licenses/gpl-3.0/
.. |Supported Python versions| image:: https://img.shields.io/pypi/pyversions/gwvet.svg
   :target: https://pypi.org/project/gwvet/
.. |Build Status| image:: https://travis-ci.org/gwpy/gwvet.svg?branch=master
   :target: https://travis-ci.org/gwpy/gwvet
.. |Coverage Status| image:: https://codecov.io/gh/gwpy/gwvet/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/gwpy/gwvet
