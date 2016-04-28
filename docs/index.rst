##################################################################
GWpy VET: the Gravitational-Wave Veto Evaluation and Testing suite
##################################################################

VET is a `GWpy <https://gwpy.github.io/>`_ toolbox for evaluating the performance of Data Quality (DQ) vetoes.

VET extends the functionality of `GWSumm <https://github.com/gwpy/gwsumm>`_ to provide HTML summaries of a number of key metrics useful in determining the effectualness of DQ products.

**Introduction:**

.. toctree::
   :maxdepth: 1

   vetoes
   install

**Command-line interface**

VET is primarily accessed as a plugin on top of the ``gw_summary`` executable, requiring an INI-format configuration file. See these pages for more details:

.. toctree::
   :maxdepth: 2

   configuration
   run

**Developer API**

.. toctree::
   :maxdepth: 2

   metrics
