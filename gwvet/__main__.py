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

"""Study the performance of one or more data-quality flags.

This utility evalutes the performance of a given flag, or set of flags,
based on a number of pre-defined metrics.

All of the command-line options can be given through the configuration files
with the named sections (given in the section headings in --help), while any
arguments given explicitly on the command-line take precedence.
"""

import argparse
import os.path
import sys

from gwpy.time import to_gps

from gwdetchar.cli import logger

from gwsumm import globalv
from gwsumm.config import GWSummConfigParser

from gwvet import __version__
from gwvet.metric import get_metric
from gwvet.cli import ACTIONS

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Alex Urban <alexander.urban@ligo.org>'

PROG = ('python -m gwvet' if sys.argv[0].endswith('.py')
        else os.path.basename(sys.argv[0]))
LOGGER = logger(name=PROG.split('python -m ').pop())


# -- utilities ----------------------------------------------------------------

class ParseGPS(argparse.Action):
    """Parse arbitrary input into GPS format from command-line
    """
    def __call__(self, parser, namespace, values, option_string=None):
        values = float(values)
        setattr(namespace, self.dest, to_gps(values))


# -- parse command-line -------------------------------------------------------

def create_parser():
    """Create a command-line parser for this entry point
    """
    # initialize the argument parser
    parser = argparse.ArgumentParser(
        prog=PROG,
        description=__doc__,
        epilog="All questions and comments should be "
               "addressed to detchar@ligo.org.",
    )

    # optional arguments
    parser._optionals.title = 'Optional arguments'
    parser.add_argument(
        '-V',
        '--version',
        action='version',
        version=__version__,
    )
    sharedopts = argparse.ArgumentParser(add_help=False)
    sharedopts.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        default=False,
        help="print verbose progress to stdout, default: %(default)s",
    )

    # general arguments
    genopts = sharedopts.add_argument_group(
        'General options',
        'Standard parameters that define the scope of this study',
    )
    genopts.add_argument(
        '-s',
        '--gps-start-time',
        action=ParseGPS,
        help='GPS start time for study',
        required=True,
    )
    genopts.add_argument(
        '-e',
        '--gps-end-time',
        action=ParseGPS,
        help='GPS end time for study',
        required=True,
    )
    genopts.add_argument(
        '-m',
        '--metric',
        action='append',
        dest='metrics',
        metavar='METRIC',
        help='metric to use in study, can be given multiple times',
    )

    # trigger arguments
    trigopts = sharedopts.add_argument_group(
        "Event trigger options",
        "Configure analysis triggers used to evaluate performance "
        "of data-quality flags on a search-specific basis",
    )
    trigopts.add_argument(
        '-c',
        '--channel',
        action='store',
        type=str,
        help="name of primary event trigger channel",
    )
    trigopts.add_argument(
        '-f',
        '--trigger-format',
        help='format of trigger files, if given',
    )
    trigsource = trigopts.add_mutually_exclusive_group(required=False)
    trigsource.add_argument(
        '-t',
        '--auto-locate-triggers',
        action='store_true',
        default=False,
        help="use trigfind to auto-locate trigger files, default: %(default)s",
    )
    trigsource.add_argument(
        '-T',
        '--trigger-file',
        action='append',
        type=str,
        help="path to trigger file, can be given multiple times",
    )

    # segdb options
    segopts = sharedopts.add_argument_group(
        "Segment database options",
    )
    segopts.add_argument(
        '-u',
        '--segment-url',
        default='https://segdb.ligo.caltech.edu',
        help='URL of segment database, default: %(default)s',
    )

    # output options
    outopts = sharedopts.add_argument_group(
        'Output options',
        'Configure HTML and figure output',
    )
    outopts.add_argument(
        '-o',
        '--html-dir',
        default=None,
        help='target directory for output HTML, default: %(default)s',
    )
    outopts.add_argument(
        '-l',
        '--label',
        default='Vetoes',
        help='text label for plots and HTML, default: %(default)s',
    )

    # toggle single-flag analysis mode
    subparser = {}
    subparsers = parser.add_subparsers(
        dest='mode',
        title='Select one of the following study modes',
        description='[run {} <mode> --help for detailed help]'.format(PROG),
    )
    for (action, mod) in ACTIONS.items():
        subparser[action] = mod.add_command_line_arguments(
            subparsers, [sharedopts])

    # return the argument parser
    return parser


# -- main code block ----------------------------------------------------------

def main(args=None):
    """Run the VET command-line interface
    """
    parser = create_parser()
    args = parser.parse_args(args=args)

    # -- setup --------------------------------------

    LOGGER.info(" -- GW Veto Evaluation and Testing system -- ")

    # set default metrics
    if (
        not args.metrics
        and (args.auto_locate_triggers or args.trigger_file)
    ):
        args.metrics = ['deadtime', 'efficiency']
    elif not args.metrics:
        args.metrics = ['deadtime']
    args.metrics = map(get_metric, args.metrics)

    # set verbosity level
    globalv.VERBOSE = args.verbose

    # construct config
    LOGGER.info("Loading configuration")
    config = GWSummConfigParser()
    config.add_section('general')
    config.set('general', 'gps-start-time', str(int(args.gps_start_time)))
    config.set('general', 'gps-end-time', str(int(args.gps_end_time)))
    config.add_section('segment-database')
    config.set('segment-database', 'url', args.segment_url)

    # set output directory
    if args.html_dir:
        if not os.path.isdir(args.html_dir):
            os.makedirs(args.html_dir)
        os.chdir(args.html_dir)

    # -- execute mode action ------------------------

    action = args.mode
    ACTIONS[action].run(args, config)

    LOGGER.info(" -- Data products written, all done -- ")


# -- run from command-line ----------------------------------------------------

if __name__ == "__main__":
    main()
