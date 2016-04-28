.. _command-line:

##############
How to run VET
##############

A VET analysis can be executed from the command-line using the ``gw_summary`` executable:

.. code-block:: bash

   $ gw_summary gps <start> <end> -f config.ini

where ``<start>`` and ``<end>`` are the GPS start and end times of your analysis period and ``config.ini`` is your :ref:`configuration file <configuration>`.

For full help, use the ``--help`` option on the command line

.. command-output:: gw_summary --help
