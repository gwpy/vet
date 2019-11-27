# coding=utf-8
# Copyright (C) Alex Urban (2019)
#
# This file is part of GWVeto.
#
# GWVeto is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GWVeto is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GWVeto.  If not, see <http://www.gnu.org/licenses/>.

"""Core utilities and classes for common VET metrics
"""

import builtins
import imp
import inspect
import re
from importlib import import_module

from astropy.units import (Quantity, Unit, dimensionless_unscaled)

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

re_quote = re.compile(r'^[\s\"\']+|[\s\"\']+$')


class Metric(object):
    """A `Metric` defines a figure of merit to assess veto performance.

    This object can be used to wrap an existing metric function into a
    standard interface for performing studies of data-quality flag
    impact.

    Parameters
    ----------
    method : `callable`
        the figure-of-merit method that should be executed
    name : `str`, optional
        the name of this `Metric`. If not given, this is taken from the
        method name
    description : `str`, optional
        the description of this `Metric`. If not given, this is taken from
        the method docstring.
    unit : `str`, `~astropy.units.core.Unit`
        the physical unit of the output of this metric function
    """
    __slots__ = ['_name', '_method', '_description', '_unit', '_triggers']

    def __init__(self, method, name=None, description=None, unit=None,
                 needs_triggers=None):
        self.method = method
        if name is None and self.method.__name__ != '<lambda>':
            name = self.method.__name__
        self.name = name
        if description is None:
            description = self.method.__doc__
        self.description = description
        self.unit = unit
        self._triggers = needs_triggers

    # -------------------------------------------
    # Metric properties

    @property
    def name(self):
        """Name of this `Metric`.

        This name should be no more than a few words long.

        :type: `str`
        """
        return self._name

    @name.setter
    def name(self, nom):
        if not isinstance(nom, str):
            raise TypeError("name attribute must be of type str")
        self._name = nom

    @property
    def method(self):
        """The callable function for this `Metric`.

        This method must accept a `SegmentList` as the first argument and
        an event `Table` as its second, although it doesn't have to actually
        use either of them. This is just for unified calling of all `Metric`
        methods.

        :type: `function`
        """
        return self._method

    @method.setter
    def method(self, func):
        if not callable(func):
            raise TypeError("method property must be a callable object, "
                            "like a function.")
        self._method = func

    @property
    def description(self):
        """Description of what this `Metric` computes.

        Ideally, this description should not describe the method called,
        and its arguments, rather just a summary of the output. See the
        builtin metrics for examples.

        This description will be printed directly to the HTML output, so
        can contain arbitrary HTML content to be printed.

        :type: `str`
        """
        return self._description

    @description.setter
    def description(self, desc):
        if not isinstance(desc, str):
            raise TypeError("description property must be of type str")
        self._description = desc.rstrip('\n ')

    @property
    def unit(self):
        """Unit of the output of this `Metric`.

        :type: :class:`~astropy.units.core.Unit`
        """
        try:
            return self._unit
        except AttributeError:
            return dimensionless_unscaled

    @unit.setter
    def unit(self, u):
        if u is None:
            try:
                del self._unit
            except AttributeError:
                pass
            return
        if not isinstance(u, Unit):
            u = Unit(u)
        self._unit = u

    @property
    def needs_triggers(self):
        """Whether this `Metric` needs a trigger table to run

        :type: `bool`
        """
        if self._triggers is not None:
            return self._triggers
        else:
            return len(inspect.getargspec(self.method).args) > 1

    # -------------------------------------------
    # Metric methods

    def __repr__(self):
        return '<{type}("{name}", "{desc}")>'.format(
            type=type(self).__name__, name=self.name,
            desc=self.description.split('\n', 1)[0])

    def __str__(self):
        return self.name

    def __call__(self, *args, **kwargs):
        """Execute the method on the aruments and return the result

        All args and kwargs are passed through to the metric method.

        Returns
        -------
        fom : :class:`~astropy.units.quantity.Quantity`
            the value of the metric for the given inputs, with a unit.
        """
        return Quantity(self.method(*args, **kwargs), unit=self.unit)

    @classmethod
    def from_ini(cls, config, section):
        """Define a new `Metric` from a `ConfigParser` section.

        Parameters
        ----------
        config : :class:`~configparser.ConfigParser`
            the configuration containing this `Metric` definiition.
        section : `str`
            the name of the section to parse.

        Returns
        -------
        metric : `Metric`
            a new metric with appropriate properties connected.

        Notes
        -----
        The following keys are recognised by this method:

        - ``'name'`` - if not given this is taken as the section name
        - ``'description'``
        - ``'unit'``
        - ``'method'`` - this should be an importable function

        Examples
        --------
        The following config fully defines a custom `Metric`

        .. code:: ini

           [volume times time]
           name = 'Volume x time'
           description = 'The relative increase in volume x time as a
                          result of applying a veto.'
           unit = '%'
           method = vtpackage.vtmodule.vtfunction
        """
        name = re_quote.sub('', config.get(section, 'name'))
        description = re_quote.sub('', config.get(section, 'description'))
        unit = re_quote.sub('', config.get(section, 'unit'))
        methodstr = config.get(section, 'method')
        try:
            modulename, methodname = methodstr.rsplit('.', 1)
        except ValueError:
            methodname = methodstr
            method = getattr(builtins, methodname)
        else:
            module = import_module(modulename)
            method = getattr(module, methodname)

        return cls(method, name=name, description=description, unit=unit)

    @classmethod
    def from_py(cls, pyfile, methodname=None, unit=None):
        """Define a new `Metric` from a Python file.

        Parameters
        ----------
        pyfile : `str`
            path to the py file containing the metric function definition;
            this should be a python file containing at least one metric
            function definition.
        methdoname : `str`
            the name of the function; if not provided, takes the name of
            the function in file or the filename, if many functions present
            in file.

        Returns
        -------
        metric : `Metric`
            a new metric with appropriate properties connected.

        Notes
        -----
        The following keys are recognised by this method:

        - ``'name'`` - methodname as defined above
        - ``'description'`` - taken from function docstring
        - ``'unit'``
        - ``'method'``

        """
        try:
            # get module name and import from 'pyfile' file
            modname = pyfile.split('/')[-1].strip('.py')
            mod = imp.load_source(modname, pyfile)
        except IOError:
            raise Exception('File %r not found.' % pyfile)

        if methodname:
            try:
                # import "methodname" method
                method = getattr(mod, methodname)
            except AttributeError:
                raise Exception('No method named %r found in file.'
                                % methodname)
        else:
            # check all methods defined in the module
            methods = list(
                filter(inspect.isfunction, list(mod.__dict__.values())))
            if len(methods) == 1:
                # import single method found
                method = methods[0]
                methodname = method.__name__

            elif modname in methods:
                # import method with same name as file
                method = getattr(mod, modname)
                methodname = modname

            else:
                raise Exception('No method named %r found in file. '
                                'Provide methodname.' % modname)

        # get description from method docstring
        description = method.__doc__ or ''

        return cls(method, name=methodname, description=description, unit=unit)


def read_all(pyfile):
    """Imports all metrics present in a given file.

    Parameters
    ----------
    pyfile : `str`
        path to the py file containing the metric function definition;
        this should be a python file containing at least one metric
        function definition.

    Returns
    -------
    metricList : `list`
        list of a new metric with appropriate properties connected.

    """
    try:
        # get module name and import from 'pyfile' file
        modname = pyfile.split('/')[-1].strip('.py')
        mod = imp.load_source(modname, pyfile)
    except IOError as e:
        raise type(e)('File %r not found.' % pyfile)
    # loop over all functions in file and add them
    metricList = []
    for method in inspect.getmembers(mod):
        if inspect.isfunction(method):
            description = method.__doc__ or ''
            metricList.append(
                Metric(method, name=method.__name__,
                       description=description))

    return metricList


def evaluate(segments, triggers, metrics):
    """Applies metrics to given segments and triggers.

    Parameters
    ----------
    segments : `~gwpy.segments.DataQualityFlag`
        segments to be analyzed.
    triggers : `~gwpy.segments.SnglInspiralTable`
        triggers to be analyzed.
    metrics : `Metric`, `list`
        metric or list of metrics with which to evaluate segments and triggers

    Returns
    -------
    results : `float`, `list`
        result(s) produced by the metric(s).

    """

    # needs type checking here

    if isinstance(metrics, Metric):
        results = metrics(segments, triggers)

    elif isinstance(metrics, list):
        results = []
        for metric in metrics:
            results.append(metric(segments, triggers))

    else:
        raise Exception('Third argument must be a metric or list of metrics.')

    return results
