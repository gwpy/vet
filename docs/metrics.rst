.. currentmodule:: gwvet

.. _metrics:

#######
Metrics
#######

Veto performance is evaluated by designing metric functions that test the impact of a veto on a set of data.

The simplest veto metric is the *deadtime*, the fractional amount of analysis time that is removed by applying a veto. High deadtime is normally a bad thing, as it reduces the amount of time remaining in which results can be found, but can be a good thing if the flag is also has high *efficiency*, meaning it removes a high fraction of background noise events.

With GWpy VET, users can take their simple functional methods and convert them into :class:`~gwvet.Metric` objects, allowing easy evaluation of multiple metrics.

To that end, GWpy VET supplies a number of standard metrics:

.. autosummary::

   ~gwvet.metric.metrics.deadtime
   ~gwvet.metric.metrics.efficiency
   ~gwvet.metric.metrics.efficiency_over_deadtime

These metrics can all be accessed via the registry.

------------
The registry
------------

To make life a little easier when working with both built-in and custom metrics, GWpy VET uses a registry to map the human-readable names to their `Metric` objects:

.. autosummary::

   get_metric
   get_all_metrics
   register_metric

For example,

   >>> from gwvet import get_metric
   >>> dt = get_metric('deadtime')
   >>> dt(mysegments)

Any user can define and register their own metrics from any function::

   >>> def my_metric(segments):
           return abs(segments)**2
   >>> register_metric(my_metric, 'squared deadtime')

-----------------
Available metrics
-----------------

.. automodule:: gwvet.metric.metrics

-------------
Reference/API
-------------

.. autoclass:: Metric

