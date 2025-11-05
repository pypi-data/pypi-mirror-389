#!/usr/bin/env python
# (C) British Crown Copyright 2016-2020, Met Office.
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
umfilelist - script for generating UM file names
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

original_doc="""
Script Name: umfilelist.py
============

Creation Date: 2008-03-17
==============

Creator: Paul Whitfield
========

Synopsis:
=========
umfilelist.py
    --stream=<stream_id>
        2- or 3-char stream identifier
    [--stream_out=<output_stream_id>]
        Alternative stream identifier to use in returned filenames. Defaults to
        the value set by the --stream option. This option may be useful when, for
        example, instantaneous/daily data (e.g. apa) has been output to a stream
        directory normally reserved for climate mean data (e.g. apl).
    --startdate=<start_date>
        YYYYMMDD[hhmm]
    --enddate=<end_date>
        YYYYMMDD[hhmm]
    [--cmrdate=<ref_date>]
        YYYYMMDD[hhmm] [185912010000]
    [--calendar=<calendar>]
        Calendar ['standard', 'gregorian', 'proleptic_gregorian'
            'noleap', '365_day', '360_day', 'julian', 'all_leap',
            '366_day']
    [--reinit=<reinit_interval>]
        Reinitialisation interval in days for daily/instantaneous data streams.
        Ordinarily this option is ignored in the case of climate mean streams.
        However, the reinitialisation interval can be force-overridden by
        prefixing the value with a minus sign, e.g. -90 for seasonal-mean data.
    [--standard_absolute_time |
     --long_absolute_time |
     --short_absolute_time]
        Use standard, long, or short absolute time format in filenames.
        The default is standard_absolute_time format.
    [--newmode]
        Use new filenaming convention
    [--prefix]
        Prefix for filenames
    [--suffix]
        Suffix for filenames
    [--notrail]
        Ignore trailing daily files, i.e. those with dates greater than
            the last reinitialisation interval.
    [--valid_dates]
        Return a list of (filename, validstart, validend) tuples.
    [--zeropad_dates | --no_zeropad_dates]
        Enable (the default) or disable 0-padding of year values in date strings.
    [--compare=<inventory>]
        Compare the generated list of filenames against filenames in
            the specified inventory. <inventory> can be a dictionary,
            or a filepath to a python shelve containing a dictionary,
            keyed on filename. If set to 'MASS' or 'MASS-R', then
            compare against the runid/stream filename listing in
            MASS-R.
    [--stdout]
        Write output to standard out instead of returning a list.

Purpose:
========
The script generates a list of expected filenames for a Unified Model
(UM) stream and for a specified date range.

If option --valid_dates is specified, then a list of (filename,
validstart, validend) tuples is returned. Where 'validstart' and
'validend' are the valid start and end dates associated with the
filename.

If option --compare=<inventory> is specified, then a list of
differences between the generated list and <inventory> is returned
instead. If inventory is set to 'MASS' or 'MASS-R', then the generated
list is compared against the associated runid/stream listing in MASS-R.
Otherwise, <inventory> is expected to be a DDS inventory, either as a
dictionary keyed on inventory filenames or as a pathname of a Python
shelve containing a dictionary keyed on inventory filenames.

NOTE: --valid_dates works for listing mode only; it does not work with
      compare mode (option --compare). If both --compare and
      --valid_dates are specified, then --valid_dates is ignored.

If option --stdout is specified, then the listings are written to
standard out rather than returned in a Python list.

The stream can be specified as either the 2- or 3-chararcter id, e.g.
'apm' or 'pm'. If the 3-charcater version is supplied, then the leading
character is stripped off and added to the filename prefix. The stream
identifier must be supplied (option --stream).

A list of file names is genertated for a range of dates specifed by a
start date and an end date. The start and end dates are supplied by via
options --startdate and --enddate; typically, the 'earliest' and
'latest' dates can be determined by running the 'moo mdls' command. The
start date and end date must be supplied.

The climate meaning reference date can be specifed via option
--cmrdate. If not supplied, then the default climate meaning reference
date '185912010000' is used.

All dates must be specified using the format YYYMMDDhhmm. If 'hhmm' is
anything other than '0000', then a WARNING is issued and 'hhmm' is set
to '0000'.

Option --newmode uses the new file naming convention. For the old file
naming convention, dates used in the name of an output file represent
the date at the end of an interval. Since date formats are forced to
have a time of '0000', a daily date used in the file name, e.g., c10
(00Z 1st December), means that the file may contain data up to 00Z for
that date, i.e. the file will include data for 30th November but not
for the 1st December.

The time format used in the file names can be in one of several
formats. The valid formats are:

   standard absolute time  (option --standard_absolute_time)
   long absolute time      (option --long_absolute_time)
   short absolute time     (option --short_absolute_time)

If not specified then the standard_absolute_time format is used by default.

For daily streams (e.g. 'apa'), and also ap[1-4] streams, the reinitialisation
interval, in days, can be specified using option --reinit.

If not supplied, then the reinitialisation period defaults to a value
of '0'.

By default, for daily streams, if there are trailing dates, i.e. dates
that lie between the last full reinitialistion interval and the end
date, then an extra file name is generated to include any trailing
dates. Trailing dates can be ignored by specifying option --notrail,
i.e., the extra file name is not generated.

A prefix to be added to the generated file names may be specified via
option --prefix. Typically, this would be the experiment runid.

A suffix to be added to the generated file names may be specified via
option --suffix, example '.pp'.

File names are generated with the following format:

  3-character stream identifier

    <prefix><char><separator><stream><timestamp><suffix>

    <prefix>     - as supplied by the user
    <separator>  - determined from the time format [ '.' or '@' or '-' ]
    <char>       - the first character of the stream identifier
    <stream>     - the last two characters of the stream identifier
    <timestamp>  - date/time with format determined by the time format
    <suffix>     - as supplied by the user


  2-character stream identifier

    <prefix><separator><stream><timestamp><suffix>

    <prefix> - as supplied by the user
    <separator>  - determined from the time format [ '.' or '@' or '-' ]
    <stream>     - the 2-character stream identifier
    <timestamp>  - date/time with format determined by the time format
    <suffix>     - as supplied by the user


Example:
========
Generate a list of file names for runid/stream abcde/apy for the date
range 1st December 1979 to 1st December 2009 using the standard
absolute time format and write to standard out.

  umfilelist.py --prefix=abcde --stream=apy --startdate=197912010000 \
      --enddate=200912010000 --standard_absolute_time --stdout

    abcdea.pyi0c10
    abcdea.pyi1c10
    abcdea.pyi2c10
    abcdea.pyi3c10
    abcdea.pyi4c10
    abcdea.pyi5c10
    abcdea.pyi6c10
    abcdea.pyi7c10
    abcdea.pyi8c10
    abcdea.pyi9c10
    abcdea.pyj0c10
    abcdea.pyj1c10
    abcdea.pyj2c10
    abcdea.pyj3c10
    abcdea.pyj4c10
    abcdea.pyj5c10
    abcdea.pyj6c10
    abcdea.pyj7c10
    abcdea.pyj8c10
    abcdea.pyj9c10
    abcdea.pyk0c10
    abcdea.pyk1c10
    abcdea.pyk2c10
    abcdea.pyk3c10
    abcdea.pyk4c10
    abcdea.pyk5c10
    abcdea.pyk6c10
    abcdea.pyk7c10
    abcdea.pyk8c10
    abcdea.pyk9c10
"""
import logging
import sys
import os
import subprocess
import getopt
import re
import shelve

try:
    from cftime import datetime, date2num, num2date
except ImportError:
    from netcdftime import datetime
    from cf_units import date2num, num2date

global hour_codes
global day_codes
global month_codes
global month_2char_codes
global month_3char_codes
global season_2char_codes
global season_3char_codes
global year_codes
global stream_reinitialisation
global is_daily
global strftime_format

__all__ = ['main', 'main_as_iterator']

logger = logging.getLogger(__name__)
interactive = False

try:
    moo = subprocess.check_output(['which', 'moo'])
    moo = moo.decode('utf8').strip()   # for Python 3 compatibility
except subprocess.CalledProcessError:
    logger.error("Unable to find 'moo' command in runtime environment.")
    moo = 'moo'
mools = '%s ls' % moo
massrhlq = 'moose:/crum'

hour_codes = {
    0: '0', 1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8',
    9: '9', 10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f', 16: 'g',
    17: 'h', 18: 'i', 19: 'j', 20: 'k', 21: 'l', 22: 'm', 23: 'n'}

day_codes = {
    1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
    10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f', 16: 'g', 17: 'h',
    18: 'i', 19: 'j', 20: 'k', 21: 'l', 22: 'm', 23: 'n', 24: 'o', 25: 'p',
    26: 'q', 27: 'r', 28: 's', 29: 't', 30: 'u', 31: 'v'}

month_codes = {
    1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
    10: 'a', 11: 'b', 12: 'c'}

month_2char_codes = {
    2: 'ja', 3: 'fb', 4: 'mr', 5: 'ar', 6: 'my', 7: 'jn', 8: 'jl', 9: 'ag',
    10: 'sp', 11: 'ot', 12: 'nv', 1: 'dc'}

month_3char_codes = {
    2: 'jan', 3: 'feb', 4: 'mar', 5: 'apr', 6: 'may', 7: 'jun', 8: 'jul',
    9: 'aug', 10: 'sep', 11: 'oct', 12: 'nov', 1: 'dec'}

season_2char_codes = {
    4: 'jm', 5: 'fa', 6: 'mm', 7: 'aj', 8: 'mj', 9: 'ja', 10: 'js', 11: 'ao',
    12: 'sn', 1: 'od', 2: 'nj', 3: 'df'}

season_3char_codes = {
    4: 'jfm', 5: 'fma', 6: 'mam', 7: 'amj', 8: 'mjj', 9: 'jja', 10: 'jas',
    11: 'aso', 12: 'son', 1: 'ond', 2: 'ndj', 3: 'djf'}

year_codes = {
    0: '0', 1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8',
    9: '9', 10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f', 16: 'g',
    17: 'h', 18: 'i', 19: 'j', 20: 'k', 21: 'l', 22: 'm', 23: 'n', 24: 'o',
    25: 'p', 26: 'q', 27: 'r', 28: 's', 29: 't', 30: 'u', 31: 'v', 32: 'w',
    33: 'x', 34: 'y', 35: 'z'}

stream_interval = {
    # 2013-06-05 added apk - MDE
    'pa': 1, 'pb': 1, 'pc': 1, 'pd': 1, 'pe': 1, 'pf': 1, 'pg': 1, 'ph': 1,
    'pi': 1, 'pj': 1, 'pk': 1, 'pp': 5, 'pw': 7, 'pt': 10, 'pr': 14, 'pm': 30,
    'ps': 90, 'py': 360, 'pv': 1800, 'px': 3600, 'pl': 18000, 'pu': 36000,
    'pz': 360000, 'p1': 1, 'p2': 1, 'p3': 1, 'p4': 1}

# Daily/instantaneous streams are:
#
#    pa, pb, pc, pd, pe, pf, pg, ph, pi, pj
#
is_daily = re.compile(r'^p[a-k]$')  # 2013-06-05 added apk - MDE
#    ca, da, dz,
#    ma, mb, mc, md, me, mf, mg, mh, mi, mj,
#
# is_daily = re.compile("""^ca$|^d[a|z]$|^[m|p][a-j]$""")

# Regex for identifying period-N mean streams, e.g. ap1 to ap4. This would normally
# be implemented as a function but is done this way for consistency with is_daily.
is_periodn = re.compile(r'^p[1-9]$')

strftime_format = "%Y%m%d%H%M"


def exit_nicely(msg=''):
    """
    Takes an error message as argument.

    Prints the error message and prints the help message then performs
    a system exit from Python.

    :param msg: the error message to print out
    :type msg: string
    """
    sys.stderr.write(str(__doc__) + '\n')
    sys.stderr.write(str(msg) + '\n')
    sys.exit()


def check_date(date_time, calendar):
    """
    Checks if 'date_time' is in the expected format: YYYYMMDDhhmm.

    :param date_time: the date/time string to validate
    :type date_time: string
    :param calendar: the calendar type
    :type calendar: string
    :return: the validated date/time
    :rtype: netcdftime.datetime
    """
    date_regex = re.compile(r'^(\d{8}|\d{12})$')
    status = date_regex.match(date_time)
    if not status:
        exit_nicely('ERROR: Invalid date (expected format: YYYYMMDD[hhmm]): "%s"'
                    % date_time)

    year = int(date_time[0:4])
    month = int(date_time[4:6])
    day = int(date_time[6:8])
    if len(date_time) == 12:
        hour = int(date_time[8:10])
        minute = int(date_time[10:12])
    else:
        hour = minute = 0

    if month not in range(1, 13):
        exit_nicely('ERROR: Invalid month: "%s"' % month)
    if day not in range(1, 32):  # modified for gregorian calendar MDE
        exit_nicely('ERROR: Invalid day: "%s"' % day)
    if hour != 0 or minute != 0:
        msg = 'Setting hour and minutes for date "%s" to 0' % date_time
        warning_message(msg)
        hour = minute = 0

    return create_datetime(year, month, day, hour, minute, calendar=calendar)


def create_datetime(year, month, day, hour=0, minute=0, second=0, calendar=None):
    """
    Create a datetime object taking into account the calendar type, if defined.
    This is necessary because the cftime.datetime constructor has version-specific
    behaviour which can result in exceptions being raised by, for example, the
    strftime() method attached to the returned object.
    """

    dt = None

    # If a calendar has been specified then include it in the constructor call.
    if calendar:
        try:
            dt = datetime(year, month, day, hour, minute, second, calendar=calendar)
        except TypeError:
            pass   # drop through to following code block

    # Otherwise it is assumed that the calendar argument is not supported.
    if dt is None:
        dt = datetime(year, month, day, hour, minute, second)

    return dt


def parse_args(args):
    """
    Parse the supplied arguments and perform some basic checks.

    Parses the options and arguments passed to the umfilelist script
    and returns the parsed parameters:

    fileprefix [string]: prefix for filenames
    stream [string]: the stream
    stream_out [string]: the stream name to use in generated filenames
    filenamemode [string]: file naming convention: new or old
    timestamp_id [string]: the time format to use in filename
                           generation
    startdate [netcdftime.datetime]: start date for filename generation
    enddate [netcdftime.datetime]: end date for filename generation
    cmrdate [netcdftime.datetime]: climate meaning reference date
    calendar [string]: calendar for filename generation
    reinitialisation [integer]: reinitialisation period for daily files
    trailing_file [bool]: include trailing daily files
    filesuffix [string]: suffix for filenames
    valid_dates [bool]: include in the output the valid start date and
                        valid end date for each filename generated in
                        the output
    zeropad_dates [bool]: enables zero-padding of years in date strings
    no_zeropad_dates [bool]: disables zero-padding of years in date strings
    inventory [string]: inventory path if comparing the generated
                        filenames
    stdout [bool]: write output to standard out

    :param args: the options and arguments to be parsed
    :type args: list
    :return: the parsed parameters
    """
    short_opts = ''
    long_opts = []
    long_opts.append('prefix=')
    long_opts.append('stream=')
    long_opts.append('stream_out=')
    long_opts.append('newmode')
    long_opts.append('long_absolute_time')
    # long_opts.append('relative_time_hours')
    # long_opts.append('relative_time_timesteps=')
    long_opts.append('short_absolute_time')
    long_opts.append('standard_absolute_time')
    # long_opts.append('sub_hourly')
    long_opts.append('startdate=')
    long_opts.append('enddate=')
    long_opts.append('calendar=')
    long_opts.append('cmrdate=')
    long_opts.append('reinit=')
    long_opts.append('notrail')
    long_opts.append('suffix=')
    long_opts.append('valid_dates')
    long_opts.append('zeropad_dates')
    long_opts.append('no_zeropad_dates')
    long_opts.append('compare=')
    long_opts.append('stdout')

    timestamp_models = (' --short_absolute_time\n --standard_absolute_time\n'
                        ' --long_absolute_time\n')
    # timestamp_models += (' --relative_time_hours\n '
    #                      ' --relative_time_timesteps\n --sub_hourly\n')

    fileprefix = ''
    stream = None
    stream_out = None
    filenamemode = 'old'
    timestamp_id = None
    # timestepInterval = 0
    startdate = 'None'
    enddate = 'None'
    calendar = '360_day'
    cmrdate = '185912010000'
    reinitialisation = '0'
    trailing_file = True
    filesuffix = ''
    valid_dates = False
    zeropad_dates = True
    inventory = ''
    stdout = False

    try:
        (opts, dummy) = getopt.getopt(args, short_opts, long_opts)
    except getopt.GetoptError:
        exit_nicely('ERROR: Invalid argument list: "%s"' % args)

    for opt, arg in opts:
        if opt == '--prefix':
            fileprefix = arg
        elif opt == '--stream':
            stream = arg
        elif opt == '--stream_out':
            stream_out = arg
        elif opt == '--newmode':
            filenamemode = 'new'
        elif opt == '--long_absolute_time':
            timestamp_id = 'long_absolute_time'
        # elif opt == '--relative_time_hours':
        #     timestamp_id = 'relative_time_hours'
        # elif opt == '--relative_time_timesteps':
        #     timestamp_id = 'relative_time_timesteps'
        #     timestepInterval = arg
        elif opt == '--short_absolute_time':
            timestamp_id = 'short_absolute_time'
        elif opt == '--standard_absolute_time':
            timestamp_id = 'standard_absolute_time'
        # elif opt == '--sub_hourly':
        #     timestamp_id = 'sub_hourly'
        elif opt == '--startdate':
            startdate = arg
        elif opt == '--enddate':
            enddate = arg
        elif opt == '--calendar':
            calendar = arg
        elif opt == '--cmrdate':
            cmrdate = arg
        elif opt == '--reinit':
            reinitialisation = arg
        elif opt == '--notrail':
            trailing_file = False
        elif opt == '--suffix':
            filesuffix = arg
        elif opt == '--compare':
            inventory = arg
        elif opt == '--valid_dates':
            valid_dates = True
        elif opt == '--stdout':
            stdout = True
        elif opt == '--zeropad_dates':
            zeropad_dates = True
        elif opt == '--no_zeropad_dates':
            zeropad_dates = False

    # Do some basic checks
    if not stream:
        exit_nicely('ERROR: Provide stream identifier (option --stream=)')
    if not stream_out:
        stream_out = stream

    streams = sorted(stream_interval)
    if stream[-2:] not in streams:
        msg = ('ERROR: Invalid stream identifier: "%s"\n Valid streams are:'
               '\n  [a|o] + %s')
        exit_nicely(msg % (stream, streams))

    if not timestamp_id:
        timestamp_id = 'standard_absolute_time'

    startdate = check_date(startdate, calendar)
    enddate = check_date(enddate, calendar)
    cmrdate = check_date(cmrdate, calendar)

    try:
        reinitialisation = int(reinitialisation)
    except:
        exit_nicely('ERROR: Invalid reinit: "%s"' % reinitialisation)

    return (fileprefix, stream, stream_out, filenamemode, timestamp_id, startdate, enddate,
            cmrdate, calendar, reinitialisation, trailing_file, filesuffix,
            valid_dates, zeropad_dates, inventory, stdout)


def year_date_1(year, month, day, hour, calendar):
    """
    Generate the yeardate code <year_base_10><dayofyear><hour_code>
    from the supplied parameters.

    :param year: the year [YYYY]
    :type year: integer
    :param month: the month [MM]
    :type month: integer
    :param day: the day [DD]
    :type day: integer
    :param hour: the hour [hh]
    :type hour: integer
    :return: the yeardate code
    :rtype: string
    """
    year_code = yearcode_base_10(year)
    date_code = '%03d%s' % (day_of_year(year, month, day, calendar),
                            hour_codes[hour])
    return '%s%s' % (year_code, date_code)


def year_date_2(year, month, day, interval, aligned, daily):
    """
    Generate a yeardate code as one of:

        <year_base_3600><month2_code>             (monthly)
        <year_base_3600><season2_code>            (seasonal)
        <year_base_3600><month_code><day_code>    (other)

    from the supplied parameters.

    :param year: the year [YYYY]
    :type year: integer
    :param month: the month [MM]
    :type month: integer
    :param day: the day [DD]
    :type day: integer
    :param interval: the meaning interval in days
    :type interval: integer
    :param aligned: the climate meaning reference date is the 1st of
                    the month
    :type aligned: boolean
    :param daily: the stream is a daily stream
    :type daily: boolean
    :return: the yeardate code
    :rtype: string
    """
    if interval == 30 and aligned:
        datecode = month_2char_codes[month]
        if month == 1 and day == 1:
            year = year - 1
    elif interval == 90 and aligned and not daily:
        datecode = season_2char_codes[month]
        if month == 1 and day == 1:
            year = year - 1
    else:
        datecode = '%s%s' % (month_codes[month], day_codes[day])

    yearcode = yearcode_base_3600(year)
    return '%s%s' % (yearcode, datecode)


def year_date_3(year, month, day, hour, interval, aligned, daily):
    """
    Generate a yeardate code as one of:

        <year_base_360><month3_code>                        (monthly)
        <year_base_360><season3_code>                       (seasonal)
        <year_base_360><month_code><day_code><hour_code>    (other)

    from the supplied parameters.

    :param year: the year [YYYY]
    :type year: integer
    :param month: the month [MM]
    :type month: integer
    :param day: the day [DD]
    :type day: integer
    :param hour: the hour [hh]
    :type hour: integer
    :param interval: the meaning interval in days
    :type interval: integer
    :param aligned: the climate meaning reference date is the 1st of
                    the month
    :type aligned: boolean
    :param daily: the stream is a daily stream
    :type daily: boolean
    :return: the yeardate code
    :rtype: string
    """
    if interval == 30 and aligned:
        datecode = month_3char_codes[month]
        if month == 1 and day == 1:
            year = year - 1
    elif interval == 90 and aligned and not daily:
        datecode = season_3char_codes[month]
        if month == 1 and day == 1:
            year = year - 1
    else:
        datecode = '%s%s%s' % (month_codes[month], day_codes[day],
                               hour_codes[hour])

    yearcode = yearcode_base_360(year)
    return '%s%s' % (yearcode, datecode)


def yearcode_base_10(year):
    """
    For the given year, return the base 10 year.

    :param year: the year [YYYY]
    :type year: integer
    :return: the base 10 year
    :rtype: integer
    """
    return year % 10


def yearcode_base_360(year):
    """
    For the given year, return the base 360 year.

    :param year: the year [YYYY]
    :type year: integer
    :return: the base 360 year
    :rtype: integer
    """
    year_360 = year % 360
    decade = year_360 // 10
    year_in_decade = year_360 % 10

    return '%s%s' % (year_codes[decade], year_in_decade)


def yearcode_base_3600(year):
    """
    For the given year, return the base 3600 year.

    :param year: the year [YYYY]
    :type year: integer
    :return: the base 3600 year
    :rtype: integer
    """
    year_3600 = year % 3600
    century = year_3600 // 100
    year_in_century = year_3600 % 100

    return '%s%02d' % (year_codes[century], year_in_century)


def day_of_year(year, month, day, calendar):
    """
    For the given year/month/day, return the day of the year in the
    calendar.

    :param year: the year [YYYY]
    :type year: integer
    :param month: the month [MM]
    :type month: integer
    :param day: the day [DD]
    :type day: integer
    :param calendar: the calendar
    :type calendar: string
    :return: the day of the year
    :rtype: integer
    """
    date = create_datetime(year, month, day, calendar=calendar)
    units = 'days since %s-01-01 00:00:00' % year
    numeric_date = date2num(date, units, calendar)
    # Note that:
    #    units = 'days since 1990-01-01 00:00:00'
    #    date = datetime(1990, 01, 01)
    #    date2num(date, units, 'standard') = 0
    return int(numeric_date + 1)


def days_in_year(year, calendar):
    """
    For the given year, return the number of days in the calendar.

    :param year: the year [YYYY]
    :type year: integer
    :param calendar: the calendar
    :type calendar: string
    :return: the number of days in the year
    :rtype: integer
    """
    return days_in_range(year, 1, 1, year + 1, 1, 1, calendar)


def days_in_range(start_year, start_month, start_day, end_year, end_month,
                  end_day, calendar):
    """
    For two given calendar dates, return the number of days between the
    start date and the end date.

    :param start_year: the start year [YYYY]
    :type start_year: integer
    :param start_month: the start month [MM]
    :type start_month: integer
    :param start_day: the start day [DD]
    :type start_day: integer
    :param end_year: the end year [YYYY]
    :type end_year: integer
    :param end_month: the end month [MM]
    :type end_month: integer
    :param end_day: the end day [DD]
    :type end_day: integer
    :param calendar: the calendar
    :type calendar: string
    :return: the number of days between the start date and the end date
    :rtype: integer
    """
    start_date = create_datetime(start_year, start_month, start_day, calendar=calendar)
    end_date = create_datetime(end_year, end_month, end_day, calendar=calendar)
    units = 'days since 1800-01-01 00:00:00'
    numeric_start_date = date2num(start_date, units, calendar)
    numeric_end_date = date2num(end_date, units, calendar)
    return int(numeric_end_date - numeric_start_date)


def date_add_days(year, month, day, days_to_add, calendar):
    """
    For the given calendar date, add the specifed number of days, and
    return the new calendar date.

    :param year: the year [YYYY]
    :type year: integer
    :param month: the month [MM]
    :type month: integer
    :param day: the day [DD]
    :type day: integer
    :param days_to_add: days to add
    :type days_to_add: integer
    :param calendar: the calendar
    :type calendar: string
    :return: the new calendar date in the form (year, month, day)
    :rtype: tuple
    """
    date = create_datetime(year, month, day, calendar=calendar)
    # Units must be 'days', since the next step is to add the days
    # specified by the 'days_to_add' parameter (it doesn't matter what
    # the reference time is, so long as it doesn't change between
    # calling date2num and num2date).
    units = 'days since 1800-01-01 00:00:00'
    numeric_date = date2num(date, units, calendar)
    new_date = num2date(numeric_date + days_to_add, units, calendar)
    return new_date.year, new_date.month, new_date.day


def determine_range(startdate, enddate, cmrdate, calendar, interval, daily,
                    trailing_file):
    """
    For the given calendar information for a stream, return:

      a. the year, month and day corresponding to the start of the
         first meaning / reinitialisation interval, which is the date
         that is both closest to the start date (startdate) but falls
         within the range defined by the start date and the end date
         (enddate) after applying an integer number of intervals
         (interval) to the climate meaning reference date (cmrdate).
      b. the number of days in the range, which is the number of days
         between the start of the first meaning / reinitialisation
         interval (a.) and the date corresponding to the end of the
         last meaning / reinitialisation interval, where the latter is
         the date that is both closest to the end date but falls within
         the range defined by start date and end date after applying an
         integer number of intervals to the start of the first meaning
         / reinitialisation interval.
      c. whether the climate meaning reference date is aligned on the
         start of the month

    in the form (year, month, day, range, aligned), where year, month,
    day and range are integers and aligned is a boolean.

    If the stream is a daily stream and 'trailing_file' is set True,
    then the range is extended to include trailing dates, i.e. dates
    that lie between the last full meaning/reinitialistion interval and
    the end date.

    :param startdate: the start date of the range
    :type startdate: netcdftime.datetime
    :param enddate: the end date of the range
    :type enddate: netcdftime.datetime
    :param cmrdate: the climate meaning reference date
    :type cmrdate: netcdftime.datetime
    :param calendar: the calendar
    :type calendar: string
    :param interval: the meaning interval in days
    :type interval: integer
    :param daily: the stream is a daily stream
    :type daily: boolean
    :param trailing_file: for daily streams, extend the range to
                                  include trailing dates
    :type trailing_file: boolean
    """
    start_year = startdate.year
    start_month = startdate.month
    start_day = startdate.day

    end_year = enddate.year
    end_month = enddate.month
    end_day = enddate.day

    cmr_year = cmrdate.year
    cmr_month = cmrdate.month
    cmr_day = cmrdate.day

    aligned = cmr_day == 1

    days0 = days_in_range(cmr_year, cmr_month, cmr_day, start_year,
                          start_month, start_day, calendar)
    if not daily:
        if days0 % interval:
            days = days_in_year(cmr_year, calendar)
            annual = interval // days
            units = 'days'
            if annual:
                units = 'years'
                if annual == 1:
                    units = 'year'
            msg = ('Climate meaning reference date "%s" not aligned '
                   'with start date "%s" for a meaning period of "%s" %s.\n' %
                   (cmrdate.strftime(strftime_format),
                    startdate.strftime(strftime_format), interval, units))
            warning_message(msg)

    # t0_delta: Number of days from start date
    # to the start of the first full climate meaning interval
    # or reinitialisation interval (daily stream).
    t0_delta = (interval - (days0 % interval)) % interval

    # Start date of the first full interval.
    (isy, ism, isdt) = date_add_days(start_year, start_month, start_day,
                                     t0_delta, calendar)

    # Days between start of first full interval and end date.
    days1 = days_in_range(isy, ism, isdt, end_year, end_month, end_day,
                          calendar)

    # t1_delta: Number of days from the end date to
    # the end date of the last full interval.
    t1_delta = -(days1 % interval)

    # If trailing dates are required for daily data and the
    # end date doesn't fall on a reinitialisation date
    # boundary (t1_delta is non-zero) and the reinitilisation
    # period is greater than 1, then increment t1_delta by
    # interval. This results in an additional filename being
    # generated, i.e. an extra file that would hold data for
    # trailing dates.
    if daily and trailing_file and t1_delta != 0 and interval > 1:
        t1_delta = t1_delta + interval

    # End date of the last full interval.
    (iey, iem, iedt) = date_add_days(end_year, end_month, end_day, t1_delta,
                                     calendar)

    # irange: Number of days between the start of the
    # first interval and the end of the last interval.
    irange = days_in_range(isy, ism, isdt, iey, iem, iedt, calendar)

    return isy, ism, isdt, irange, aligned


def new_file_naming(year, month, day, stream, startdate, enddate, interval,
                    daily, zeropad_dates=True):
    """
    Generate the date format for the new file naming convention.

    :param year: the year [YYYY]
    :type year: integer
    :param month: the month [MM]
    :type month: integer
    :param day: the day [DD]
    :type day: integer
    :param stream: the stream type, e.g., 'pa', 'pm', 'ps'
    :type stream: string
    :param startdate: the start date of the range
    :type startdate: netcdftime.datetime
    :param enddate: the end date of the range
    :type enddate: netcdftime.datetime
    :param interval: the meaning interval in days
    :type interval: integer
    :param daily: the stream is a daily stream
    :type daily: boolean
    :param zeropad_dates: set to True to zero-pad year values in date strings
    :type zeropad_dates: boolean
    :return: the date format for the new file naming convention
    :rtype: string
    """
    january = 1
    thefirst = 1
    monthly_interval = 30
    monthly = 'pm'
    seasonal = 'ps'
    if daily:
        if zeropad_dates:
            filename_start = startdate.strftime('%Y')
        else:
            filename_start = str(startdate.year)
        if interval == monthly_interval:
            filename_end = month_3char_codes[month]
        else:
            filename_end = startdate.strftime('%m%d')
    else:
        if zeropad_dates:
            filename_start = '%04d' % year
        else:
            filename_start = str(year)
        if month == january and day == thefirst:
            filename_start = year - 1
        if stream == monthly or (is_periodn.match(stream) and interval == 30):
            filename_end = month_3char_codes[month]
        elif stream == seasonal or (is_periodn.match(stream) and interval == 90):
            filename_end = season_3char_codes[month]
        else:
            filename_end = enddate.strftime('%m%d')
    return '%s%s' % (filename_start, filename_end)


def warning_message(msg):
    """
    Write a warning message.

    The destination depends on the context. If the module constant
    interactive is set True then output goes to stderr, otherwise the
    output goes to a logger.

    :param msg: message to print
    :type msg: string
    """
    if interactive:
        msg = 'WARNING: %s\n' % msg
        sys.stderr.write(msg)
    else:
        logger.warning(msg)


def absolute_time_filenames(timestamp_id, prefix, mode, stream, stream_out,
        startdate, enddate, cmrdate, calendar, reinitialisation, trailing_file,
        suffix='', zeropad_dates=True):
    """
    For the given stream and calendar dates: start date, end date,
    climate meaning reference date, generate a list of Unified Model
    file names.

    The format of the generated file names is determined by the prefix,
    the mode (old or new file naming convention), the stream, the time
    format (timestamp_id), the reinitialisation interval (for daily
    files), and the daily naming mode. If 'trailing_file' is True, and
    the stream is a daily stream, then an additional file name is
    generated if there are trailing dates, i.e. dates that lie between
    the last full reinitialistion interval and the end date. Suffix is
    added to the end of each filename, e.g. '.pp'.

    :param timestamp_id: the time format
    :type timestamp_id: string
    :param prefix: prefix for filenames
    :type prefix: string
    :param mode: file naming convention: new or old
    :type mode: string
    :param stream: the stream
    :type stream: string
    :param stream_out: alternative stream identifier to use in returned filenames
    :type stream_out: string
    :param startdate: the start date
    :type startdate: netcdftime.datetime
    :param enddate: the end date
    :type enddate: netcdftime.datetime
    :param cmrdate: the climate meaning reference date
    :type cmrdate: netcdftime.datetime
    :param calendar: the calendar
    :type calendar: string
    :param reinitialisation: reinitialisation period for daily files
    :type reinitialisation: integer
    :param trailing_file: for daily streams, extend the range to
                          include trailing dates
    :type trailing_file: boolean
    :param suffix: suffix for filenames
    :type suffix: string
    :param zeropad_dates: set to True to zero-pad year values in date strings
    :type zeropad_dates: boolean
    :return: the generated file names
    :rtype: list
    """
    filesinfo = list(get_fileinfo(timestamp_id, prefix, mode, stream, stream_out,
                    startdate, enddate, cmrdate, calendar, reinitialisation,
                    trailing_file, suffix=suffix, zeropad_dates=zeropad_dates))
    return filesinfo


def get_fileinfo(timestamp_id, prefix, mode, stream, stream_out, startdate,
        enddate, cmrdate, calendar, reinitialisation, trailing_file, suffix='',
        zeropad_dates=True):
    """
    Generator function that returns information (filename, start_date, end_date)
    for each UM file matching the constraints defined by the function arguments.
    """
    filenameprefix = prefix
    if len(stream) == 3:
        filenameprefix = filenameprefix + stream_out[0]
    if mode == 'new':
        separatorid = '.'
    else:
        timestampiddict = {}
        timestampiddict['standard_absolute_time'] = ['.', 360]
        timestampiddict['long_absolute_time'] = ['@', 3600]
        timestampiddict['short_absolute_time'] = ['-', 10]
        separatorid = timestampiddict[timestamp_id][0]
    file_type = stream[-2:]
    filenameprefix = '%s%s%s' % (filenameprefix, separatorid, stream_out[-2:])

    hour = startdate.hour
    minute = startdate.minute

    daily = bool(is_daily.match(file_type))
    periodn = bool(is_periodn.match(file_type))

    if reinitialisation > 0:
        if not (daily or periodn):
            msg = ('Ignoring user-defined reinitialisation period ({0} days).\n'
                'Stream "{1}" is not daily/instantaneous/periodN.'.format(
                reinitialisation, stream))
            warning_message(msg)
            interval = stream_interval[file_type]
        else:
            # Daily or periodN stream
            interval = reinitialisation
    elif reinitialisation < 0:
        # A -ve reinit period can now be used to force-override the period for
        # the case where a non-climate-mean stream (e.g. ap[a-k] or ap[1-4]) has
        # been configured to hold climate mean output.
        interval = abs(reinitialisation)
    else:
        # Climate meaning stream
        interval = stream_interval[file_type]

    if mode == 'old':
        yearcycle = timestampiddict[timestamp_id][1]
        yearrange = enddate.year - startdate.year
        if yearrange > yearcycle:
            msg = ('Duplicate file names probable. Year range > Year cycle: '
                   '"%s" > "%s"' % (yearrange, yearcycle))
            warning_message(msg)

    # The value of irange (used in the loop below) is the number of
    # days in the interval, but for monthly, seasonal, yearly,
    # etc., data with dates from the e.g., proleptic_gregorian
    # calendar, the number of days in a month / season / year will
    # change. However, since the aim is to loop over whole months /
    # seasons / years (regardless of how many days are contained
    # within that month / season / year), by setting the calendar
    # to 360_day and using the corresponding interval (e.g., 30,
    # 90, 360) provides a "quick and dirty" way of performing the
    # required calculation. Note that the code will fail if the
    # startdate / climate meaning reference date falls outside the
    # 360_day calendar.
    if interval >= 30:
        calendar = '360_day'

    # For daily streams, the climate meaning reference date (CMRD) is
    # not relevant and iyear = start_year, imonth = start_month, iday =
    # start_day and irange = (enddate - startdate) (since aligned is
    # based on the CMRD, it is not relevant for daily streams).
    # Therefore, this code should be refactored such that the daily
    # stream calculations do not rely on the CMRD.
    (iyear, imonth, iday, irange, aligned) = determine_range(
        startdate, enddate, cmrdate, calendar, interval, daily, trailing_file)
    daycount = interval
    filestartdate = create_datetime(iyear, imonth, iday, hour, minute, calendar=calendar)

    try:
        while daycount <= irange:

            year_date_code = None
            (year, month, day) = date_add_days(
                iyear, imonth, iday, daycount, calendar)
            fileenddate = create_datetime(year, month, day, hour, minute, calendar=calendar)

            if mode == 'new':
                filenamedate = new_file_naming(
                    year, month, day, file_type, filestartdate, fileenddate,
                    interval, daily, zeropad_dates=zeropad_dates)
                filename = '%s%s%s' % (filenameprefix, filenamedate, suffix)
            else:
                if timestamp_id == 'standard_absolute_time':
                    year_date_code = year_date_3(year, month, day, hour, interval,
                                                 aligned, daily)
                elif timestamp_id == 'long_absolute_time':
                    year_date_code = year_date_2(year, month, day, interval,
                                                 aligned, daily)
                elif timestamp_id == 'short_absolute_time':
                    year_date_code = year_date_1(year, month, day, hour, calendar)

                if year_date_code:
                    filename = '%s%s%s' % (filenameprefix, year_date_code, suffix)

            fileinfo = (filename, filestartdate.strftime(strftime_format),
                        fileenddate.strftime(strftime_format))

            daycount = daycount + interval
            filestartdate = fileenddate

            yield fileinfo

    except GeneratorExit:
        logger.debug('Caught GeneratorExit exception.')
        return


def massnot(inventory, expected):
    """
    Compare a list of expected filenames for a Unified Model
    runid/stream against filenames found in the specified inventory.

    'inventory' is the one of:

      Dictionary containing a LINK inventory.

      Filepath of python shelve containing a LINK dictionary.

      MASS or MASS-R -- get filenames for stream from MASS-R.

    The required runid/stream is taken from the filenames in the
    'expected' list.

    The function returns a list of expected files not found in the
    inventory and a list of inventory files not found in the expected
    list.

    If the inventory argument is 'MASS' or 'MASS-R', then a call is
    made to the shell to run 'moo ls' to list the filenames in MASS-R
    for the stream.

    :param inventory: source of filename inventory
    :type inventory: dictionary or string
    :param expected: the expected filenames for comparing with the
                     inventory
    :type expected: list
    :return: the expected files not found in the inventory and the
             inventory files not found in the list of expected files
    :rtype: tuple containing two lists
    """
    exp_diff = []
    inv_diff = []
    if not expected:
        exit_nicely('ERROR: Input list "expected" contains no file names.')
    temp1 = expected[0].split('/')[-1]
    # FIXME: suspect that the '\' char in the next line should be a '/' char?
    rsid = re.compile('%s\%s' % (temp1[0:6], temp1[6:9]))
    runid = temp1[0:5]
    stream = temp1[5] + temp1[7:9]
    temp2 = [x.split('/')[-1] for x in expected if rsid.search(x)]
    lentemp2 = len(temp2)
    lenexpected = len(expected)
    if lenexpected == lentemp2:
        expected = temp2[:]
    else:
        exit_nicely('ERROR: Input list "expected" contains filenames for more '
                    'than one runid/stream.')

    if inventory == 'MASS-R' or inventory == 'MASS':
        print('%s %s/%s/%s.pp' % (mools, massrhlq, runid, stream))
        try:
            mlsout = subprocess.check_output([mools, "{0}/{1}/{2}.pp".format(
                massrhlq, runid, stream)])
            mlsout = mlsout.decode('utf8').strip().split('\n')
        except subprocess.CalledProcessError as exc:
            exit_nicely("ERROR returned from '{0}' is '{1}'. Error code '{2}'".format(
                    mools, exc.output, exc.returncode))
        found = [f.split('/')[-1] for f in mlsout]

    elif isinstance(inventory, dict):
        found = [f.split('/')[-1] for f in inventory.keys() if rsid.search(f)]

    elif os.path.exists(inventory):
        inv_open = shelve.open(inventory)
        found = [f.split('/')[-1] for f in inv_open.keys() if rsid.search(f)]
        inv_open.close()

    else:
        exit_nicely('ERROR: Cannot determine inventory format.')

    setexpected = set(expected)
    setfound = set(found)

    # expected but not found
    exp_diff = list(setexpected.difference(setfound))
    exp_diff.sort()

    # found but not expected
    inv_diff = list(setfound.difference(setexpected))
    inv_diff.sort()

    return exp_diff, inv_diff


def main(args):
    """
    The controlling function for the script (but see the :func:`main_as_iterator`
    function for an alternative entry point for use by client code).

    Calls parse_args to parse the options/arguments passed to the
    script. Calls absolute_time_filenames which returns a list of
    information for expected files.

    If an inventory is specified (compare mode), then the list of
    expected files is compared with filenames in the inventory and two
    difference lists are generated.

    If an inventory is not specified (normal mode), then a list of
    expected filenames is generated.

    Output is either returned in a list or printed to standard out.

    In normal mode, filenames only are printed by default, but if
    option --valid_dates is specified, then the start and end dates
    valid for a file are listed along with the filename.

    :return: A list of UM filenames matching the constraints imposed by the input
        arguments (refer to the parse_args function for a description of these).
    """
    (fileprefix, stream, stream_out, filenamemode, timestamp_id, startdate, enddate,
     cmrdate, calendar, reinitialisation, trailing_file, filesuffix,
     valid_dates, zeropad_dates, inventory, stdout) = parse_args(args)

    filesinfo = absolute_time_filenames(timestamp_id, fileprefix, filenamemode,
        stream, stream_out, startdate, enddate, cmrdate, calendar, reinitialisation,
        trailing_file, suffix=filesuffix, zeropad_dates=zeropad_dates)
    filenames = [x[0] for x in filesinfo]

    if inventory:
        filelist = [[], []]
        (exp_diff, inv_diff) = massnot(inventory, filenames)
        if exp_diff is not None:
            if not len(exp_diff) and not len(inv_diff):
                if stdout:
                    sys.stdout.write('No differences found.\n')
            else:
                if stdout:
                    if len(exp_diff):
                        sys.stdout.write('\n%s files expected but not found '
                                         'in %s:\n' % (len(exp_diff),
                                                       inventory))
                        for filename in exp_diff:
                            sys.stdout.write('%s\n' % filename)

                    if len(inv_diff):
                        sys.stdout.write('\n%s files found in %s but not '
                                         'expected:\n' % (len(inv_diff),
                                                          inventory))
                        for filename in inv_diff:
                            sys.stdout.write('%s\n' % filename)
                else:
                    for filename in exp_diff:
                        filelist[0].append(filename)

                    for filename in inv_diff:
                        filelist[1].append(filename)
    else:
        filelist = []
        if valid_dates:
            for fileinfo in filesinfo:
                if stdout:
                    sys.stdout.write('%s %s %s\n' % fileinfo)
                else:
                    filelist.append(fileinfo)
        else:
            for filename in filenames:
                if stdout:
                    sys.stdout.write('%s\n' % filename)
                else:
                    filelist.append(filename)

    return filelist


def main_as_iterator(args):
    """
    An alternative to the :func:`main` function. As the name suggests, the
    current function acts as an iterator over the sequence of UM filenames that
    meet the criteria defined by the input arguments. Unlike the main function,
    however, this function does not support the inventory comparison operation
    (since that operation requires the full list of filenames to work).

    :return: A sequence of UM filenames matching the constraints imposed by the
        input arguments (refer to the parse_args function for a description of
        these).
    """
    (fileprefix, stream, stream_out, filenamemode, timestamp_id, startdate, enddate,
     cmrdate, calendar, reinitialisation, trailing_file, filesuffix,
     valid_dates, zeropad_dates, inventory, stdout) = parse_args(args)

    it = get_fileinfo(timestamp_id, fileprefix, filenamemode, stream, stream_out,
        startdate, enddate, cmrdate, calendar, reinitialisation, trailing_file,
        suffix=filesuffix, zeropad_dates=zeropad_dates)

    if valid_dates:
        for fileinfo in it:
            yield fileinfo
    else:
        for fileinfo in it:
            yield fileinfo[0]


if __name__ == '__main__':
    interactive = True
    main(sys.argv[1:])
