.. _configuration:

###########################
Configuration files for VET
###########################

Processing data with VET on the command line will require a custom INI-format configuration file for your analysis.

====================
Declaring the plugin
====================

.. note:: All VET configuration files must declare that it needs the ``gwsumm.tabs`` plugin to operate:

.. code-block:: ini

   [plugins]
   gwvet.tabs =

This just tells the ``gw_summary`` executable to import the `gwvet.tabs` module, which registers the VET functionality.

==================
Defining a 'state'
==================

By default all analysis are done over the full GPS `[start, end)` segment. For long periods, however, you might want to run over a selection of times within that period based on the state of the interferometer, or some other criteria.

You can define a new state by using the ``[states]`` section

.. code-block:: ini

   [states]
   Observing = H1:DMT-ANALYSIS_READY:1

This defines the 'Observing' state by referencing the ``H1:DMT-ANALYSIS_READY:1`` data-quality flag.
In this way you can run your analysis using only times when that flag was active by referring to this state in your tab configuration.

================
Defining a 'tab'
================

Each analysis is declared using a section name of the form ``[tab-<name>]``, where ``<name>`` can be anything you like as long as it is unique. Each ``[tab]`` will correspond to a single HTML page in the output.

-------------------
Basic configuration
-------------------

The required parameters are

=========  =======================================================
``type``   the type of tab this is, always use ``veto-flag``
``name``   the display/link name of this tab
``flags``  a comma-separated list of data-quality flags to analyse
=========  =======================================================

e.g.

.. code-block:: ini

   [tab-veto]
   name = My veto
   type = veto-flag
   flags = X1:VET-TEST_FLAG:1

-----------------------
Specifying the segments
-----------------------

By default the ``flags`` given will be search for in the segment database (`https://segments.ligo.org <https://github.com/ligovirgo/dqsegdb>`_), but you can manually specify a ``segmentfile`` to test custom segments:

.. code-block:: ini

   segmentfile = mysegments.xml

.. note::

   You can use a simply ASCII ``txt`` file for your segments, but for best
   results you should use a `LIGO_LW`-formatted XML file with the full
   ``segment``, ``segment_summary``, and ``segment_definer`` table set.

As noted above, you can choose to run the analysis only when a given state is active, by using the ``state`` parameter

.. code-block:: ini

   state = Observing

----------------
Metric selection
----------------

By default the only metric tested is `~gwsumm.metric.metrics.deadtime`, but you can give a comma-separated list of names for new metrics, e.g.

.. code-block:: ini

   metrics = deadtime, efficiency, efficiency/deadtime

------------------------------------------
Testing performance against event triggers
------------------------------------------

While the `~gwsumm.metric.metrics.deadtime` metric simply requires the veto segments themselves to run, more involved metrics (e.g. `~gwsumm.metric.metrics.efficiency` require a set of event triggers to fold into the performance calculation.

You can specify a set of event triggers to use by giving the following options:

===================  =========================================================
``event-channel``    the name of the data channel used to produce these events
``event-generator``  the name of the algorithm used to produce these events
``event-table``      the :mod:`LIGO_LW <glue.ligolw>` table that can be used to
                     store these events in memory
===================  =========================================================

e.g.

.. code-block:: ini

   event-channel = H1:GDS-CALIB_STRAIN
   event-generator = pycbc
   event-table = sngl_inspiral

--------
Example
--------

The following configuration file can be used to test the ``H1:DMT-ETMY_ESD_DAC_OVERFLOW`` flag against Omicron triggers:

.. code-block:: ini

   [tab-etmy-esd]
   name = ETMY ESD
   type = veto-flag
   flags = H1:DMT-ETMY_ESD_DAC_OVERFLOW:1
   state = Observing
   event-channel = H1:GDS-CALIB_STRAIN
   event-generator = Omicron

===============================
Using the ``[DEFAULT]`` section
===============================

The INI file parser in python allows for the use of a special section called ``[DEFAULT]`` to define parameters that should get copied to all other sections in the file. VET leverages this to allow you to define common ``[tab]`` options in that section.

So, if you want to test a number of different flags, you can put all of the common options in the ``[DEFAULT]`` section, and keep the individual tab sections nice and simple, e.g.

.. code-block:: ini

   [DEFAULT]
   metrics = deadtime, efficiency, efficiency/deadtime
   state = Observing
   event-channel = H1:GDS-CALIB_STRAIN
   event-generator = Omicron

   [tab-ETMY-ESD]
   name = ETMY ESD
   flags = H1:DMT-ETMY_ESD_DAC_OVERFLOW:1

   [tab-OMC-DCPD]
   name = OMC DCPD
   flags = H1:DMT-OMC_DCPD_ADC_OVERFLOW:1


======================
Using ``defaults.ini``
======================

The configuration file options for the full ``gw_summary`` executable are too numerous to itemise here, you should see the `GWSumm configuration docs <https://ldas-jobs.ligo.caltech.edu/~duncan.macleod/gwsumm/latest/configuration/>`_ for that. But, it is useful to note that if you are running on the LDAS system provided by the LIGO Data Grid, you can pick the ``defaults.ini`` file used by the LIGO Summary Pages to simplify getting the 'standard' full configuration. You can pass this path to ``gw_summary`` using the ``-f/--config-file`` option::

    /home/detchar/etc/summary/configuration/defaults.ini
