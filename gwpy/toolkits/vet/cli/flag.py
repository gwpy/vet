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

from gwpy.utils import gprint
from gwpy.segments import (Segment, SegmentList, DataQualityFlag)

from .. import version
from ..segments import get_segments
from ..triggers import get_triggers

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__version__ = version.version


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


def run(args):
    """Execute the flag study
    """
    # get analysis segments
    span = SegmentList([Segment(float(args.gps_start_time),
                                float(args.gps_end_time))])
    if args.verbose:
        gprint("Getting analysis segments...", end=' ')
    if args.analysis_flag or args.analysis_segments:
        analysis = get_segments(args.analysis_flag, span,
                                cache=args.analysis_segments,
                                url=args.segment_url)
    else:
        analysis = DataQualityFlag(active=span, valid=span)
    if args.verbose:
        gprint("Done, %.2f%% livetime."
               % (abs(analysis.active) / abs(span) * 100))

    # get flag segments
    if args.verbose:
        gprint("Getting veto segments...", end=' ')
    if args.flag and os.path.isfile(args.flag[0]):
        segs = get_segments(None, analysis, url=args.segment_url,
                            cache=args.flag)
    else:
        segs = get_segments(args.flag, analysis, url=args.segment_url)
    if args.intersection:
        allsegs = segs.intersection()
    else:
        allsegs = segs.union()
    if args.verbose:
        gprint("Done.")

    # get triggers
    if args.trigger_file or args.auto_locate_triggers:
        if args.verbose:
            gprint("Getting triggers...", end=' ')
        triggers = get_triggers(args.channel, args.trigger_format, analysis,
                                cache=args.trigger_file)
        if args.verbose:
            gprint("Done, %d triggers found." % len(triggers))
    else:
        triggers = None

    # apply vetoes
    if any([m.needs_triggers for m in args.metrics]):
        if args.verbose:
            gprint("Applying vetoes...", end=' ')
        after = triggers.veto(allsegs.active)
        if args.verbose:
            gprint("Done, %d triggers remaining." % len(after))

    # apply metrics
    if args.verbose:
        gprint("\nMetric results\n--------------")

    for metric in args.metrics:
        if metric.needs_triggers:
            result = metric(allsegs, triggers, after=after)
        else:
            result = metric(allsegs)
        print('%s: %s' % (str(metric), result))
