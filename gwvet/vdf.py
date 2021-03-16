# coding=utf-8
# Copyright (C) Duncan Macleod (2013)
#
# This file is part of GWpy VET.
#
# GWpy VET is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GWSumm is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GWpy VET.  If not, see <http://www.gnu.org/licenses/>.

"""Analyse a veto definer file in full using the GWpy VET package
"""

import argparse
import os
import re
import sys

from configparser import NoSectionError
from getpass import getuser
from math import (ceil, floor)
from urllib.parse import urlparse
from urllib.request import urlopen

from gwpy.segments import (
    DataQualityFlag,
    DataQualityDict,
)
from gwpy.time import to_gps

from gwdetchar.cli import logger

from gwsumm import batch
from gwsumm.config import GWSummConfigParser as ConfigParser
from gwsumm.state import SummaryState
from gwsumm.utils import (
    get_default_ifo,
    re_cchar,
    mkdir,
)

from gwvet import __version__

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Alex Urban <alexander.urban@ligo.org>'

try:
    IFO = get_default_ifo()
except ValueError:
    IFO = None

DEFAULT_METRICS = [
    'Deadtime',
    'Efficiency',
    'Efficiency/Deadtime',
    'Use percentage',
    'Loudest event by SNR',
]

PROG = ('python -m gwvet.vdf' if sys.argv[0].endswith('.py')
        else os.path.basename(sys.argv[0]))
LOGGER = logger(name=PROG.split('python -m ').pop())


# -- utilities ----------------------------------------------------------------

def add_config_section(config, section, **params):
    """Add a section to the global configuration
    """
    config.add_section(section)
    for key, val in params.items():
        config.set(section, key, val)


def configure_veto_tab(config, section, parent, state, flags,
                       segmentfile, metrics, **params):
    """Configure the tab corresponding to a given veto
    """
    tab = 'tab-%s' % section
    config.add_section(tab)
    params.setdefault('type', 'veto-flag')
    params.setdefault('name', section)
    if parent is not None:
        params.setdefault('parent', parent)
    params.setdefault('flags', ','.join(flags))
    params.setdefault('union', '|'.join(flags))
    params.setdefault('intersection', '&'.join(flags))
    params.setdefault('states', state.key)
    params.setdefault('veto-name', params['name'])
    params.setdefault('metrics', ','.join(metrics))
    # set others
    if 'event-channel' in params:
        params.setdefault('before', '%(event-channel)s')
        params.setdefault('after', '%(event-channel)s#%(union)s')
        params.setdefault('vetoed', '%(event-channel)s@%(union)s')
    for key, val in params.items():
        config.set(tab, key, val)
    return tab


# -- parse command-line -------------------------------------------------------

def create_parser():
    """Create a command-line parser for this entry point
    """
    # initialize argument parser
    parser = argparse.ArgumentParser(
        prog=PROG,
        description=__doc__,
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='print verbose output',
    )
    parser.add_argument(
        '-V',
        '--version',
        action='version',
        version=__version__,
    )
    parser._positionals.title = 'Positional arguments'
    parser._optionals.title = 'Optional arguments'

    # required arguments
    parser.add_argument(
        'veto-definer-file',
        help='path to veto definer file',
    )
    parser.add_argument(
        'gpsstart',
        type=to_gps,
        help='GPS start time/date of analysis',
    )
    parser.add_argument(
        'gpsend',
        type=to_gps,
        help='GPS end time/date of analysis',
    )

    # analysis options
    analargs = parser.add_argument_group('Analysis options')
    analargs.add_argument(
        '-f',
        '--config-file',
        type=os.path.abspath,
        default=[],
        action='append',
        help='path to INI file defining this analysis',
    )
    analargs.add_argument(
        '-i',
        '--ifo',
        default=IFO,
        help='prefix of IFO to study, default: %(default)s',
    )
    analargs.add_argument(
        '-o',
        '--output-directory',
        default=os.curdir,
        type=os.path.abspath,
        help='output directory path, default: %(default)s, '
             'this path should be web-viewable',
    )
    analargs.add_argument(
        '-c',
        '--categories',
        default='1,2,3,4',
        help='list of categories to analyse, default: %(default)s',
    )
    analargs.add_argument(
        '-m',
        '--metric',
        action='append',
        help='name of metric to use in analysis, can be given '
             'multiple times, default: %s' % DEFAULT_METRICS,
    )
    analargs.add_argument(
        '-I',
        '--independent',
        action='store_true',
        help='analyse categories independently, rather than '
             'hierarchichally, default: hierarchichally',
    )
    analargs.add_argument(
        '-g',
        '--global-config',
        action='append',
        default=[],
        help='path to gwsumm configuration file passed to all gw_summary jobs',
    )

    # trigger options
    trigargs = parser.add_argument_group('Trigger options')
    trigargs.add_argument(
        '-x',
        '--event-channel',
        default=IFO and '%s:GDS-CALIB_STRAIN' % IFO or None,
        help='name of event trigger channel, default: %(default)s',
    )
    trigargs.add_argument(
        '-G',
        '--event-generator',
        default='Omicron',
        help='name of event trigger generator, default: %(default)s',
    )
    trigargs.add_argument(
        '-X',
        '--event-file',
        help='path to event cache file',
    )

    # segment options
    segargs = parser.add_argument_group('Segment options')
    segargs.add_argument(
        '-a',
        '--analysis-segments',
        action='append',
        default=IFO and ['%s:DMT-ANALYSIS_READY:1' % IFO] or None,
        help='flag indicating analysis time, or path of segment file '
             'containing segments for a single flag, default: %(default)s, '
             'can be given multiple times to use the intersection of many '
             'flags, or the union of many files',
    )
    segargs.add_argument(
        '-n',
        '--analysis-name',
        default='Analysis',
        help='Human-readable name for summary state, '
             'e.g. \'Science\', default: %(default)s',
    )
    segargs.add_argument(
        '-t',
        '--segment-url',
        dest='segdb',
        default='https://segments.ligo.org',
        help='url of segment database, default: %(default)s',
    )
    segargs.add_argument(
        '-S',
        '--on-segdb-error',
        default='raise',
        choices=['raise', 'ignore', 'warn'],
        help='how to handle (dq)segdb errors, default: %(default)s',
    )

    # return the argument parser
    return parser


# -- main code block ----------------------------------------------------------

def main(args=None):
    """Run the online Guardian node visualization tool
    """
    parser = create_parser()
    args = parser.parse_args(args=args)

    # parse command line options
    ifo = args.ifo
    if not args.ifo:
        parser.error('--ifo must be given if not obvious from the host')
    start = getattr(args, 'gpsstart')
    end = getattr(args, 'gpsend')
    duration = int(ceil(end) - floor(start))
    categories = args.categories.split(',')
    for i, c in enumerate(categories):
        try:
            categories[i] = int(c)
        except (TypeError, ValueError):
            pass
    vetofile = getattr(args, 'veto-definer-file')
    vetofile = (urlparse(vetofile).netloc
                or os.path.abspath(vetofile))
    args.metric = args.metric or DEFAULT_METRICS

    # -- setup --------------------------------------

    tag = '%d-%d' % (start.seconds, end.seconds)
    outdir = os.path.abspath(os.path.join(args.output_directory, tag))
    mkdir(outdir)
    os.chdir(outdir)
    mkdir('etc', 'segments', 'condor')

    # -- segment handling ---------------------------

    os.chdir('segments')
    ALLSEGMENTS = DataQualityDict()

    # -- get analysis segments ----------------------

    aflags = args.analysis_segments
    asegments = DataQualityFlag('%s:VET-ANALYSIS_SEGMENTS:0' % ifo)
    for i, flag in enumerate(aflags):
        # use union of segments from a file
        if os.path.isfile(flag):
            asegments += DataQualityFlag.read(flag)
        # or intersection of segments from multiple flags
        else:
            new = DataQualityFlag.query(flag, start, end, url=args.segdb)
            if i:
                asegments.known &= new.known
                asegments.active &= new.active
            else:
                asegments.known = new.known
                asegments.active = new.active
    ALLSEGMENTS[asegments.name] = asegments

    if os.path.isfile(aflags[0]):
        asegments.filename = aflags

    # -- read veto definer and process --------------

    if urlparse(vetofile).netloc:
        tmp = urlopen(vetofile)
        vetofile = os.path.abspath(os.path.basename(vetofile))
        with open(vetofile, 'w') as f:
            f.write(tmp.read())
        LOGGER.info('Downloaded veto definer file')
    vdf = DataQualityDict.from_veto_definer_file(
        vetofile, format='ligolw', start=start, end=end, ifo=ifo)
    LOGGER.info('Read %d flags from veto definer' % len(vdf.keys()))

    # populate veto definer file from database
    vdf.populate(source=args.segdb, on_error=args.on_segdb_error)
    ALLSEGMENTS += vdf

    # organise flags into categories
    flags = dict((c, DataQualityDict()) for c in categories)
    for name, flag in vdf.items():
        try:
            flags[flag.category][name] = flag
        except KeyError:
            pass

    # find the states and segments for each category
    states, after, oldtitle = (dict(), None, '')
    for i, category in enumerate(categories):
        title = isinstance(category, int) and 'Cat %d' % category or category
        tag = re_cchar.sub('_', str(title).upper())
        states[category] = SummaryState(
            'After %s' % oldtitle,
            key=tag,
            known=after.known,
            active=after.active,
            definition=after.name,
        ) if i else SummaryState(
                args.analysis_name,
                key=args.analysis_name,
                definition=asegments.name,
        )
        try:
            segs = flags[category].union()
        except TypeError:  # no flags
            segs = DataQualityFlag()
        segs.name = '%s:VET-ANALYSIS_%s:0' % (ifo, tag)
        ALLSEGMENTS[segs.name] = segs
        after = (after - segs) if i else (asegments - segs)
        after.name = '%s:VET-ANALYSIS_AFTER_%s:0' % (ifo, tag)
        ALLSEGMENTS[after.name] = after
        oldtitle = title

    # write all segments to disk
    segfile = os.path.abspath('%s-VET_SEGMENTS-%d-%d.xml.gz'
                              % (ifo, start.seconds, duration))
    ALLSEGMENTS.write(segfile)

    os.chdir(os.pardir)

    if args.verbose:
        LOGGER.debug("All segments accessed and written to\n%s" % segfile)

    # -- job preparation ----------------------------

    os.chdir('etc')

    configs = []
    for category in categories:
        title = (isinstance(category, int)
                 and 'Category %d' % category or category)
        tab = 'tab-%s' % title
        config = ConfigParser()

        # add segment-database configuration
        add_config_section(config, 'segment-database', url=args.segdb)

        # add plot configurations
        pconfig = ConfigParser()
        pconfig.read(args.config_file)
        for section in pconfig.sections():
            if section.startswith('plot-'):
                config._sections[section] = pconfig._sections[section].copy()

        try:
            plots = pconfig.items('plots-%s' % category, raw=True)
        except NoSectionError:
            try:
                plots = pconfig.items('plots', raw=True)
            except NoSectionError:
                plots = []

        # add state
        if args.independent:
            state = states[categories[0]]
        else:
            state = states[category]
        sname = 'state-%s' % state.key
        add_config_section(config, sname, key=state.key, name=state.name,
                           definition=state.definition, filename=segfile)

        # add plugin
        add_config_section(config, 'plugins', **{'gwvet.tabs': ''})

        # define metrics
        if category == 1:
            metrics = ['Deadtime']
        else:
            metrics = args.metric

        # define summary tab
        if category == 1:
            tab = configure_veto_tab(
                config, title, title, state, flags[category].keys(), segfile,
                metrics, name='Summary', **{'veto-name': title})
        else:
            tab = configure_veto_tab(
                config, title, title, state, flags[category].keys(), segfile,
                metrics, name='Summary', **{
                    'veto-name': title,
                    'event-channel':  args.event_channel,
                    'event-generator': args.event_generator,
                })
        if len(categories) == 1:
            config.set(tab, 'index',
                       '%(gps-start-time)s-%(gps-end-time)s/index.html')
        for key, value in plots:
            if re.match('%\(flags\)s (?:plot-)?segments', value):  # noqa: W605
                config.set(tab, key, '%%(union)s,%s' % value)
                if '%s-labels' % key not in plots:
                    config.set(tab, '%s-labels' % key, 'Union,%(flags)s')
            else:
                config.set(tab, key, value)

        # now a tab for each flag
        for flag in flags[category]:
            if category == 1:
                tab = configure_veto_tab(
                    config, flag, title, state, [flag], segfile, metrics)
            else:
                tab = configure_veto_tab(
                    config, flag, title, state, [flag], segfile, metrics, **{
                        'event-channel': args.event_channel,
                        'event-generator': args.event_generator})
                if args.event_file:
                    config.set(tab, 'event-file', args.event_file)
            for key, value in plots:
                config.set(tab, key, value)

        if len(categories) > 1 and category != categories[-1]:
            with open('%s.ini' % re_cchar.sub('-', title.lower()), 'w') as f:
                config.write(f)
                configs.append(os.path.abspath(f.name))

    # configure summary job
    if len(categories) > 1:
        state = states[categories[0]]
        add_config_section(config, 'state-%s' % state.key, key=state.key,
                           name=state.name, definition=state.definition,
                           filename=segfile)
        try:
            plots = pconfig.items('plots', raw=True)
        except NoSectionError:
            plots = []
        flags = [f for c in categories for f in flags[c].keys()]
        tab = configure_veto_tab(
            config, 'Impact of full veto definer file', None, state, flags,
            segfile, args.metric, shortname='Summary',
            index='%(gps-start-time)s-%(gps-end-time)s/index.html',
            **{'event-channel': args.event_channel,
               'event-generator': args.event_generator,
               'veto-name': 'All vetoes'})
        if args.event_file:
            config.set(tab, 'event-file', args.event_file)
        for key, value in plots:
            config.set(tab, key, value)
        with open('%s.ini' % re_cchar.sub('-', title.lower()), 'w') as f:
            config.write(f)
            configs.append(os.path.abspath(f.name))

    os.chdir(os.pardir)

    if args.verbose:
        LOGGER.debug("Generated configuration files for each category")

    # -- condor preparation -------------------------

    os.chdir(os.pardir)

    # get condor variables
    if getuser() == 'detchar':
        accgroup = 'ligo.prod.o1.detchar.dqproduct.gwpy'
    else:
        accgroup = 'ligo.dev.o1.detchar.dqproduct.gwpy'

    gwsumm_args = [
        '--gps-start-time', str(start.seconds),
        '--gps-end-time', str(end.seconds),
        '--ifo', ifo,
        '--file-tag', 'gwpy-vet',
        '--condor-command', 'accounting_group=%s' % accgroup,
        '--condor-command', 'accounting_group_user=%s' % getuser(),
        '--on-segdb-error', args.on_segdb_error,
        '--output-dir', args.output_directory,
    ]
    for cf in args.global_config:
        gwsumm_args.extend(('--global-config', cf))
    for cf in configs:
        gwsumm_args.extend(('--config-file', cf))
    if args.verbose:
        gwsumm_args.append('--verbose')

    if args.verbose:
        LOGGER.debug('Generating summary DAG via:\n')
        LOGGER.debug(' '.join([batch.PROG] + gwsumm_args))

    # execute gwsumm in batch mode
    batch.main(args=gwsumm_args)


# -- run from command-line ----------------------------------------------------

if __name__ == "__main__":
    main()
