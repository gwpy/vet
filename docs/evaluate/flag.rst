#####################################
Evaluating a single data-quality flag
#####################################

Interactive
===========

The simplest form of VET is for a single data-quality flag or segmentlist.

The first thing we need to do is load some science segments to define the bounds of the study::

    >>> from gwpy.toolkits.vet import get_segments
    >>> s6segdb = 'https://segdb.ligo.caltech.edu'
    >>> analysis = get_segments('H1:DMT-SCIENCE:1', ('Aug 19 2010', 'Aug 20 2010'), url=s6segdb)

Next we can fetch the segments for the `H1:DCH-SEISVETO_CBC:2` flag - capturing times of transient seismic noise on the LHO instrumental floor::

    >>> vetoes = get_segments('H1:DCH-SEISVETO_CBC:2', analysis, url=s6segdb)

Already we can evaluate the `deadtime` of these segments::

    >>> from gwpy.toolkits.vet import get_metric
    >>> dt = get_metric('deadtime')
    >>> dt(vetoes)
    <Quantity 7.8425628803110392 %>

For a more interesting test, we can load some triggers::

    >>> from gwpy.toolkits.vet import get_triggers
    >>> trigs = get_triggers('H1:LSC-DARM_ERR', 'omegadq', analysis, cache=['/home/detchar/public_html/S6/glitch/Wdata/966211215_966297615/clusters.txt'])

and can evaluate some more metrics::

    >>> get_metric('efficiency')(vetoes, trigs)
    <Quantity 18.234556287237378 %>
    >>> get_metric('efficiency/deadtime')(vetoes, trigs)
    <Quantity 2.3250761983707791>

.. note::

   While segment database queries can be performed from any machine, the trigger file referenced under ``'/home/detchar/...'`` is only available on the LHO LDAS computing system.

   In general this will be true for event trigger files for each of the H1 and L1 instruments.

Command-line
============

The same analysis can be performed from the command-line using the `gwvet` executable provided by GWpy VET in `flag` mode:

.. code-block:: bash

   $ gwvet flag H1:DCH-SEISVETO_CBC:2 --gps-start-time 'Aug 19 2010' --gps-end-time 'Aug 20 2010' --segment-url https://segdb.ligo.caltech.edu --analysis-flag H1:DMT-SCIENCE:1 --trigger-file /home/detchar/public_html/S6/glitch/Wdata/966211215_966297615/clusters.txt --trigger-format omegadq --metric deadtime --metric efficiency --metric efficiency/deadtime
   Deadtime: 7.84256288031 %
   Efficiency: 18.2345562872 %
   Efficiency/Deadtime: 2.32507619837

For full documentation on all command-line options, you can run:

.. command-output:: gwvet flag --help
