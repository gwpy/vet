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

"""Command-line tool that grabs triggers and segments for hveto, UPV, and
OVL for any time period, then concatenates them into one segment file and
one trigger file. This tool then produces a DQ flag for the given type and
period, spits out a .xml file, and generates the .ini file needed to run VET.
"""

import argparse
import datetime
import glob
import os
import sys

from configparser import ConfigParser

import numpy

from gwpy.segments import DataQualityFlag
from gwpy.segments import SegmentList, Segment
from gwpy.time import (to_gps, tconvert)

from gwdetchar.cli import logger

from gwvet import __version__

__author__ = 'Erika Cowan <erika.cowan@ligo.org>'
__credits__ = 'Alex Urban <alexander.urban@ligo.org>'

PROG = ('python -m gwvet.hug' if sys.argv[0].endswith('.py')
        else os.path.basename(sys.argv[0]))
LOGGER = logger(name=PROG.split('python -m ').pop())


def grab_time_triggers(wildcard, start, end):
    """Retrieve triggers from a given GPS time range
    """
    time_segs = SegmentList([])
    start_time_utc = tconvert(start)
    for filename in glob.glob(wildcard):
        data = SegmentList.read(filename)
        LOGGER.info(' '.join(['grabbing trigger file:', filename]))
        start_end_seg = Segment(start, end)
        c = data & SegmentList([start_end_seg])
        time_segs += c
        start_time_utc += datetime.timedelta(days=1)
    return time_segs


def grab_time_segments(wildcard, start, segfile):
    """Retrieve time segments from a given start time
    """
    known_start = []
    known_end = []
    start_time_utc = tconvert(start)
    for filename in glob.glob(wildcard):
        if os.path.isfile(filename):
            segments = numpy.atleast_2d(numpy.loadtxt(filename, delimiter=','))
            known_start = [segments[i, 0] for i in range(len(segments))]
            known_end = [segments[i, 1] for i in range(len(segments))]
            start_time_utc += datetime.timedelta(days=1)
    for index in range(len(known_start)):
        segfile.write(
            str(known_start[index]) + " " + str(known_end[index]) + "\n"
        )


def write_segs(trig_seg_list, output_file):
    """Write a list of trigger segments to an output file
    """
    total_triggers = trig_seg_list.coalesce()
    total_triggers.write(output_file)


# -- parse command-line -------------------------------------------------------

def create_parser():
    """Create a command-line parser for this entry point
    """
    # initialize argument parser
    parser = argparse.ArgumentParser(
        prog=PROG,
        description=__doc__,
    )

    # positional arguments
    parser.add_argument(
        'gpsstart',
        type=to_gps,
        help='GPS start time',
    )
    parser.add_argument(
        'gpsend',
        type=to_gps,
        help='GPS end time',
    )
    parser.add_argument(
        'directory_path',
        type=str,
        help='Path to output directory for triggers and segments',
    )
    parser.add_argument(
        'dq_flag_type',
        type=str,
        help='DQ flag type, either hveto, UPVh, OVL',
    )

    # optional flags
    parser.add_argument(
        '-V',
        '--version',
        action='version',
        version=__version__,
    )
    parser.add_argument(
        '-a',
        '--hveto_analysis_seg',
        type=str,
        help='Hveto O1 offline analysis segment, one of 4,5,6,8,9',
    )
    parser.add_argument(
        '-o',
        '--online_offline',
        type=str,
        help='Selector for offline or online, needed only for hveto',
    )

    # return the argument parser
    return parser


# -- main code block ----------------------------------------------------------

def main(args=None):
    """Run the gwvet-hug CLI tool
    """
    parser = create_parser()
    args = parser.parse_args(args=args)

    # check to make sure we're within the time window of aLIGO,
    # and that end_time is after start_time
    if args.gpsstart < 971574400:  # roughly the end of S6
        parser.error("gpsstart before S6")
    if args.gpsend < args.gpsstart:
        parser.error("end_time is before gpsstart")

    # finds beginning of day for given gps time
    start_of_day = tconvert(args.gpsstart)
    start_of_day_utc = start_of_day.replace(hour=0, minute=0, second=0)
    start_of_day_gps = tconvert(start_of_day)

    # finds UTC version of start/end times
    start_time_utc = tconvert(args.gpsstart)
    end_time_utc = tconvert(args.gpsend)

    # opens files to be ready for writing
    f = open("total_" + args.dq_flag_type + "_trigs.txt", "w")  # all triggers
    g = open("total_" + args.dq_flag_type + "_segs.txt", "w")  # all segments

    # choosing to read in hveto
    if args.dq_flag_type == 'hveto':

        LOGGER.info(
            'Data Quality Flag chosen is hveto, stored in the path '
            '%s' % args.directory_path)

        # choosing the offline hveto option for O1, runs by Josh Smith
        if args.online_offline == 'offline':
            analysis_segs_45689 = ['4', '5', '6', '7', '9']
            analysis_segs_237 = ['2', '3']
            if args.hveto_analysis_seg in analysis_segs_45689:
                pattern_trigs_hveto = os.path.join(
                    args.directory_path,
                    'analysis%s' % args.hveto_analysis_seg,
                    'H1-omicron_BOTH-*-DARM',
                    '*VETO_SEGS_ROUND*.txt',
                )
                pattern_segs_hveto = os.path.join(
                    args.directory_path,
                    'analysis%s' % args.hveto_analysis_seg,
                    'H1-omicron_BOTH-*-DARM',
                    'segs.txt',
                )

            elif args.hveto_analysis_seg in analysis_segs_237:
                pattern_trigs_hveto = os.path.join(
                    args.directory_path, 'H1-omicron_BOTH-*-DARM',
                    '*VETO_SEGS_ROUND*.txt')
                pattern_segs_hveto = os.path.join(
                    args.directory_path, 'H1-omicron_BOTH-*-DARM', 'segs.txt')

            elif args.hveto_analysis_seg == '8':
                pattern_trigs_hveto = os.path.join(
                    args.directory_path, '*VETO_SEGS_ROUND*.txt')
                pattern_segs_hveto = os.path.join(
                    args.directory_path, 'segs.txt')
            else:
                raise ValueError('Must choose from O1 analysis segments '
                                 '1 through 9')
            LOGGER.info(
                'Data Quality Flag chosen is hveto, stored in the path '
                '%s' % args.directory_path)

            while start_time_utc < end_time_utc:
                day = start_time_utc.day
                month = start_time_utc.month
                year = start_time_utc.year

                triggers = grab_time_triggers(
                    pattern_trigs_hveto, args.gpsstart, args.gpsend)

                # Ideally we would be able to use the same algorithm, but
                # SegmentList.read doesn't support csv, which is the format
                # that segment files are recorded in. So, we want to
                # temporarily use another method to read in segments.
                segments = grab_time_segments(
                    pattern_segs_hveto, args.gpsstart, g)

                start_time_utc += datetime.timedelta(days=1)

            write_segs(triggers, f)

        elif args.online_offline == 'online':

            # These paths are currently hardwired for online searches.
            pattern_trigs_hveto = os.path.join(
                args.directory_path, '{}{:02}', '{}{:02}{:02}',
                '*86400-DARM', '*VETO_SEGS_ROUND*.txt')
            pattern_segs_hveto = os.path.join(
                args.directory_path, '{}{:02}', '{}{:02}{:02}',
                '*86400-DARM', 'segs.txt')

            triggers = SegmentList([])
            segments = SegmentList([])

            while start_time_utc < end_time_utc:
                day = start_time_utc.day
                month = start_time_utc.month
                year = start_time_utc.year
                wildcard_trigs_hveto = pattern_trigs_hveto.format(
                    year, month, year, month, day)
                wildcard_segs_hveto = pattern_segs_hveto.format(
                    year, month, year, month, day)
                triggers = grab_time_triggers(
                    wildcard_trigs_hveto, args.gpsstart, args.gpsend)

                # Ideally we would be able to use the same algorithm, but
                # SegmentList.read doesn't support csv, which is the format
                # segment files are recorded in. So, we want to temporarily
                # use another method to read segments in.
                segments = grab_time_segments(
                    wildcard_segs_hveto, args.gpsstart, g)

                start_time_utc += datetime.timedelta(days=1)

            write_segs(triggers, f)

            # segments.write(g)

        else:
            LOGGER.info('Did not choose online or offline. Please choose.')

    # choosing to read in UPVh!
    elif args.dq_flag_type == 'UPVh':

        LOGGER.info('Data-quality flag chosen is %s, stored in the path %s' % (
            args.dq_flag_type, args.directory_path))

        pattern_trigs_UPVh = os.path.join(
            args.directory_path, 'DARM_LOCK_{}_{}-H', 'H1:*veto.txt')
        pattern_segs_UPVh = os.path.join(
            args.directory_path, 'DARM_LOCK_{}_{}-H', 'segments.txt')
        triggers = SegmentList([])
        segments = SegmentList([])
        while start_of_day_utc < end_time_utc:
            start_of_day_gps = tconvert(start_of_day_utc)
            nextday_utc = start_of_day_utc + datetime.timedelta(days=1)
            nextday_gps = tconvert(nextday_utc)
            wildcard_UPVh_trigs = pattern_trigs_UPVh.format(
                start_of_day_gps, nextday_gps)
            wildcard_UPVh_segs = pattern_segs_UPVh.format(
                start_of_day_gps, nextday_gps)
            triggers = grab_time_triggers(
                wildcard_UPVh_trigs, args.gpsstart, args.gpsend)
            segments = grab_time_triggers(
                wildcard_UPVh_segs, args.gpsstart, args.gpsend)
            start_of_day_utc += datetime.timedelta(days=1)
            write_segs(triggers, f)
            write_segs(segments, g)

    else:  # forgot to choose UPVh or hveto
        raise ValueError(
            'Did not give a valid data-quality tool, '
            'please choose from hveto, UPVh, or OVL'
        )
    f.close()
    g.close()

    # creating DQ .xml file

    # construct flag and filename
    flag_name = 'H1:' + args.dq_flag_type + '-RND:1'
    name = 'segments_' + args.dq_flag_type + '_RND.xml'

    # reading in segment files
    try:
        knownsegments = numpy.loadtxt(
            'total_' + args.dq_flag_type + '_segs.txt')
    except OSError:
        LOGGER.info(
            "No total_{}_segs.txt file in current working directory. "
            "It should have been produced from last loop. "
            "If this file is empty, that may mean you have no active "
            "segments during this time period.".format(args.dq_flag_type))

    known_start = [knownsegments[i, 0] for i in range(len(knownsegments))]
    known_end = [knownsegments[i, 1] for i in range(len(knownsegments))]

    # reading in trigger files
    data = numpy.loadtxt('total_' + args.dq_flag_type + '_trigs.txt')

    # get an array for the start_time and end_time of each segment
    start_time = [data[i, 1] for i in range(len(data))]
    end_time = [data[i, 2] for i in range(len(data))]

    # create a data quality flag object
    flag = DataQualityFlag(
        flag_name, active=zip(start_time, end_time),
        known=zip(known_start, known_end))

    # write flag
    flag.write(name)

    LOGGER.info("Created DQ Flag: " + flag_name + " in .xml form as: " + name)

    # creating VET .ini file

    config = ConfigParser()

    config.add_section('plugins')
    config.set('plugins', 'gwvet.tabs', ' ')

    config.add_section('states')
    config.set('states', 'Science', '%(ifo)s:DMT-ANALYSIS_READY:1')

    config.add_section('segment-database')
    config.set('segment-database', 'url', 'https://segments.ligo.org')

    config.add_section('')
    config.set('', 'type', 'veto-flag')
    config.set('', 'event-channel', '%(ifo)s:GDS-CALIB_STRAIN')
    config.set('', 'event-generator', 'Omicron')
    config.set('', 'metrics',
               "'Deadtime',\n'Efficiency', \n'Efficiency/Deadtime', "
               "\n'Efficiency | SNR>=8', \n'Efficiency/Deadtime | SNR>=8', "
               "\n'Efficiency | SNR>=20', \n'Efficiency/Deadtime | SNR>=20', "
               "\n'Efficiency | SNR>=100', \n'Efficiency/Deadtime | SNR>=100',"
               " \n'Use percentage', \n'Loudest event by SNR'")

    config.add_section('tab-SNR-6')
    config.set('tab-SNR-6', 'name', 'SNR 6')
    config.set('tab-SNR-6', 'type', 'veto-flag')
    config.set('tab-SNR-6', 'shortname', 'SNR 6')
    config.set('tab-SNR-6', 'flags', flag_name)
    config.set('tab-SNR-6', 'states', "Science")
    config.set('tab-SNR-6', 'segmentfile', name)

    with open(args.dq_flag_type + '_segs.ini', 'wb') as configfile:
        config.write(configfile)

    LOGGER.info(
        '\n Created %s_segs.ini. You have everything you need to run VET now! '
        '\n' % args.dq_flag_type)
    LOGGER.info(
        'To run VET,first go into %s_segs.ini, and delete the line that only '
        'contains [], then save and exit the .ini file.\n' % args.dq_flag_type)
    LOGGER.info(
        'Finally, run the command: \n'
        '$ gw_summary gps %s %s -f /home/detchar/etc/summary/configurations/'
        'defaults.ini -f %s_segs.ini' % (
            args.gpsstart, args.gpsend, args.dq_flag_type))


# -- run from command-line ----------------------------------------------------

if __name__ == "__main__":
    main()
