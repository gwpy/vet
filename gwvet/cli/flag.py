# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2014)
#
# This file is part of GWpy VET.
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

"""Study a single data-quality flag
"""

import os.path

from gwpy.segments import Segment

from gwsumm.state import (generate_all_state, SummaryState)
from gwsumm.utils import vprint

from ..tabs import FlagTab

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


def add_command_line_arguments(topparser, parents=[]):
    """Add the command-line arguments for this action
    """
    help, desc = __doc__.split('\n', 1)
    parser = topparser.add_parser('flag', parents=parents,
                                  help=help, description=desc)
    parser._optionals.title = 'Optional arguments'
    arggroup = parser.add_argument_group('Flag options')
    arggroup.add_argument('flag', help='name of flag(s) to study', nargs='+')
    arggroup.add_argument('--intersection', action='store_true', default=False,
                          help='use intersection of all flags, default: union')
    # add analysis segment options
    arggroup.add_argument(
        '-a', '--analysis-flag', metavar='FLAG',
        help='flag to use for analysis segments (e.g. science mode)')
    arggroup.add_argument(
        '-A', '--analysis-segments', action='append', metavar='FILE',
        help='file from which to read analysis segments - .txt, .xml(.gz) or '
             '.lcf files (LAL cache) are accepted, can be given multiple '
             'times.')
    return parser


def run(args, config):
    """Execute the flag study
    """
    if (args.label == 'Vetoes' and len(args.flag) == 1 and
            not os.path.isfile(args.flag[0])):
        args.label = args.flag[0]

    vprint("\n-------------------------------------------------\n")
    vprint("Processing %s\n" % args.label)

    span = Segment(args.gps_start_time, args.gps_end_time)

    # format analysis state
    if args.analysis_flag:
        state = SummaryState(args.analysis_flag, definition=args.analysis_flag,
                             known=[span])
        state.fetch(config=config)
    else:
        state = generate_all_state(*span)

    tab = FlagTab(args.label, args.gps_start_time, args.gps_end_time,
                  args.flag, states=[state], metrics=args.metrics,
                  channel=args.channel, etg=args.trigger_format,
                  intersection=args.intersection)
    tab.index = 'index.html'
    tab.process(config=config)
    tab.write_html(ifo='VET')
