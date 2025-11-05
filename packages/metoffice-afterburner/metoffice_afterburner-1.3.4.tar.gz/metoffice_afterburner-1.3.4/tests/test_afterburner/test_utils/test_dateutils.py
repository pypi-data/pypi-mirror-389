# (C) British Crown Copyright 2016-2022, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.utils.dateutils module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import unittest
import operator
import cf_units
import numpy as np
from datetime import datetime
from packaging import version

try:
    import cftime as nct
except ImportError:
    import netcdftime as nct

from iris.time import PartialDateTime as PDT

import afterburner.utils.dateutils as dateutils
from afterburner.utils.dateutils import MAX_YEAR_VALUE
from afterburner.misc.stockcubes import geo_tyx
from afterburner.exceptions import CoordinateError


def _get_cftime_date_padding_char():
    """
    Return the character used to pad dates with years < 1000. Prior to v1.3 of
    the cftime package this was the space character. From v1.3 it changed to the
    '0' character.
    """
    dts = nct.datetime(1, 1, 1).strftime('%Y-%m-%d')
    return dts[0]


class TestDateTimeRange(unittest.TestCase):
    """Test the dateutils.DateTimeRange class."""

    def setUp(self):
        self.pdt_att_names = ['year', 'month', 'day', 'hour', 'minute', 'second']
        self.dtr = dateutils.DateTimeRange('1970-01-01T06:30:00', '1970-04-01T18:30:00')

    def test_bad_init_args(self):
        with self.assertRaises(ValueError):
            dateutils.DateTimeRange(None, None)
            dateutils.DateTimeRange('', '')

    def test_iso_construction(self):
        values = [getattr(self.dtr.start_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 1, 6, 30, 0])
        values = [getattr(self.dtr.end_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 4, 1, 18, 30, 0])

        dtr = dateutils.DateTimeRange('1970-01-01T06:30', '1970-04-01T18:30')
        values = [getattr(dtr.start_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 1, 6, 30, 0])
        values = [getattr(dtr.end_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 4, 1, 18, 30, 0])

        dtr = dateutils.DateTimeRange('1970-01-01T06', '1970-04-01T18')
        values = [getattr(dtr.start_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 1, 6, 0, 0])
        values = [getattr(dtr.end_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 4, 1, 18, 0, 0])

        dtr = dateutils.DateTimeRange('1970-01-01', '1970-04-01')
        values = [getattr(dtr.start_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 1, 0, 0, 0])
        values = [getattr(dtr.end_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 4, 1, 0, 0, 0])

    def test_cf_construction(self):
        # CF uses space character separator rather than T character.
        dtr = dateutils.DateTimeRange('1970-01-01 06:30:00', '1970-04-01 18:30:00')
        values = [getattr(dtr.start_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 1, 6, 30, 0])
        values = [getattr(dtr.end_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 4, 1, 18, 30, 0])

        dtr = dateutils.DateTimeRange('1970-01-01 06:30', '1970-04-01 18:30')
        values = [getattr(dtr.start_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 1, 6, 30, 0])
        values = [getattr(dtr.end_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 4, 1, 18, 30, 0])

        dtr = dateutils.DateTimeRange('1970-01-01 06', '1970-04-01 18')
        values = [getattr(dtr.start_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 1, 6, 0, 0])
        values = [getattr(dtr.end_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 4, 1, 18, 0, 0])

    def test_half_open_time_range(self):
        dtr = dateutils.DateTimeRange(None, '1970-04-01')
        self.assertEqual(dtr.start, dateutils.DATETIME_NEG_INF.isoformat())
        self.assertEqual(dtr.start_pdt, dateutils.DATETIME_NEG_INF)
        self.assertTrue(dtr.contains('1970-01-01'))
        self.assertFalse(dtr.contains('1970-04-01'))
        self.assertFalse(dtr.contains('1970-06-01'))

        dtr = dateutils.DateTimeRange('1970-04-01', None)
        self.assertEqual(dtr.end, dateutils.DATETIME_POS_INF.isoformat())
        self.assertEqual(dtr.end_pdt, dateutils.DATETIME_POS_INF)
        self.assertFalse(dtr.contains('1970-01-01'))
        self.assertTrue(dtr.contains('1970-04-01'))
        self.assertTrue(dtr.contains('1970-06-01'))

    def test_from_datetime_method(self):
        # Test using Iris PDT objects.
        start_pdt = PDT(year=1970, month=1, day=1, hour=6, minute=30)
        end_pdt = PDT(year=1970, month=4, day=1, hour=18, minute=30)
        dtr = dateutils.DateTimeRange.from_datetime(start_pdt, end_pdt)
        values = [getattr(dtr.start_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 1, 6, 30, 0])
        values = [getattr(dtr.end_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 4, 1, 18, 30, 0])
        self.assertEqual(dtr.interval_type, 'leftclosed')

        start_pdt = PDT(year=1970, month=1, day=1)
        end_pdt = PDT(year=1970, month=4, day=1)
        dtr = dateutils.DateTimeRange.from_datetime(start_pdt, end_pdt,
            interval_type='closed')
        values = [getattr(dtr.start_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 1, 0, 0, 0])
        values = [getattr(dtr.end_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 4, 1, 0, 0, 0])
        self.assertEqual(dtr.interval_type, 'closed')

        # Test using datetime.datetime objects.
        start_dt = datetime.utcnow().replace(microsecond=0)
        end_dt = start_dt.replace(year=start_dt.year+1)
        dtr = dateutils.DateTimeRange.from_datetime(start_dt, end_dt)
        self.assertEqual(dtr.start_pdt, start_dt)
        self.assertEqual(dtr.end_pdt, end_dt)

        # Test using incomplete dates.
        with self.assertRaises(ValueError):
            dateutils.DateTimeRange.from_datetime(PDT(year=1970, month=1), PDT(year=1970, month=4))
            dateutils.DateTimeRange.from_datetime(PDT(month=1, day=1), PDT(month=4, day=30))

    @unittest.skipUnless(nct.__name__ == 'cftime', "cftime package not present")
    def test_from_datetime_with_cftime(self):
        start_dt = nct.datetime(year=1970, month=1, day=1)
        end_dt = nct.datetime(year=1970, month=4, day=1)
        dtr = dateutils.DateTimeRange.from_datetime(start_dt, end_dt)
        default_cal = getattr(start_dt, 'calendar') or 'gregorian'
        self.assertEqual(dtr.calendar, default_cal)

        start_dt = nct.Datetime360Day(year=1970, month=1, day=1)
        end_dt = nct.Datetime360Day(year=1970, month=4, day=1)
        dtr = dateutils.DateTimeRange.from_datetime(start_dt, end_dt)
        self.assertEqual(dtr.calendar, '360_day')

        start_dt = nct.DatetimeNoLeap(year=1970, month=1, day=1)
        end_dt = nct.DatetimeNoLeap(year=1970, month=4, day=1)
        dtr = dateutils.DateTimeRange.from_datetime(start_dt, end_dt)
        self.assertEqual(dtr.calendar, 'noleap')

        # override calendar attribute associated with datetime objects
        dtr = dateutils.DateTimeRange.from_datetime(start_dt, end_dt,
            calendar='365_day')
        self.assertEqual(dtr.calendar, '365_day')

    def test_from_cube_method(self):
        # The geo_tyx() function returns a cube with 12 month's worth of data.
        cube = geo_tyx()
        dtr = dateutils.DateTimeRange.from_cube(cube)
        values = [getattr(dtr.start_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 16, 0, 0, 0])
        values = [getattr(dtr.end_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 12, 16, 0, 0, 0])

        dtr = dateutils.DateTimeRange.from_cube(cube, use_bounds=True)
        values = [getattr(dtr.start_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 1, 0, 0, 0])
        values = [getattr(dtr.end_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1971, 1, 1, 0, 0, 0])
        self.assertEqual(dtr.interval_type, 'leftclosed')

        # Test using specific interval type.
        cube = geo_tyx()
        dtr = dateutils.DateTimeRange.from_cube(cube, interval_type='closed')
        self.assertEqual(dtr.interval_type, 'closed')

        # Test using a single time coordinate, w/ cell bounds.
        tmp_cube = cube[0,:,:]
        dtr = dateutils.DateTimeRange.from_cube(tmp_cube)
        values = [getattr(dtr.start_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 16, 0, 0, 0])
        values = [getattr(dtr.end_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 16, 0, 0, 0])

        dtr = dateutils.DateTimeRange.from_cube(tmp_cube, use_bounds=True)
        values = [getattr(dtr.start_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 1, 0, 0, 0])
        values = [getattr(dtr.end_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 2, 1, 0, 0, 0])

        # Test using a single time coordinate, w/o cell bounds.
        tmp_cube.coord('time').bounds = None
        dtr = dateutils.DateTimeRange.from_cube(tmp_cube, use_bounds=True)
        values = [getattr(dtr.start_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 16, 0, 0, 0])
        values = [getattr(dtr.end_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 16, 0, 0, 0])

        # Test with invalid time units.
        tmp_cube = cube.copy()
        tmp_cube.coord('time').units = 'days'
        self.assertRaises(CoordinateError, dateutils.DateTimeRange.from_cube, tmp_cube)

        # Test with alternative coordinate name.
        tmp_cube = cube.copy()
        tmp_cube.coord('time').standard_name = 'forecast_reference_time'
        dtr = dateutils.DateTimeRange.from_cube(tmp_cube, time_coord_name='forecast_reference_time')
        self.assertEqual(dtr.start_pdt.year, 1970)

    def test_setter_methods(self):
        self.dtr.start = '1970-01-30T12:00:00'
        values = [getattr(self.dtr.start_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 30, 12, 0, 0])

        self.dtr.end = '1970-04-30T12:00:00'
        values = [getattr(self.dtr.end_pdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 4, 30, 12, 0, 0])

    def test_getitem_method(self):
        self.assertEqual(self.dtr[0], '1970-01-01T06:30:00')
        self.assertEqual(self.dtr[1], '1970-04-01T18:30:00')
        self.assertEqual(self.dtr[:], ['1970-01-01T06:30:00', '1970-04-01T18:30:00'])
        with self.assertRaises(IndexError):
            _dummy = self.dtr[2]
            _dummy = self.dtr[1:3]
        with self.assertRaises(TypeError):
            _dummy = self.dtr['x']

    def test_str_method(self):
        self.assertEqual(str(self.dtr), '1970-01-01T06:30:00 1970-04-01T18:30:00')

    def test_repr_method(self):
        self.assertEqual(repr(self.dtr),
            "DateTimeRange('1970-01-01T06:30:00', '1970-04-01T18:30:00')")

        dtr = dateutils.DateTimeRange('1970-01-01', '1970-04-01', calendar=
            cf_units.CALENDAR_360_DAY)
        self.assertEqual(repr(dtr),
            "DateTimeRange('1970-01-01', '1970-04-01', calendar='360_day')")

    def test_as_name_token(self):
        self.assertEqual(self.dtr.as_name_token(),
            '1970-01-01T06:30:00_1970-04-01T18:30:00')
        self.assertEqual(self.dtr.as_name_token(compact=True),
            '19700101T063000_19700401T183000')
        self.assertEqual(self.dtr.as_name_token(dates_only=True),
            '1970-01-01_1970-04-01')
        self.assertEqual(self.dtr.as_name_token(dates_only=True, compact=True),
            '19700101_19700401')

    def test_invalid_calendar(self):
        with self.assertRaises(ValueError):
            dateutils.DateTimeRange('1970-01-01', '1970-04-01', calendar='360Day')

    def test_invalid_date_order(self):
        with self.assertRaises(ValueError):
            dateutils.DateTimeRange('1971-01-01', '1970-04-01')
            self.dtr.start = '1970-04-01T18:30:01'  # 1 second after end
            self.dtr.start = '1970-05-01'           # 1 month after end
            self.dtr.start = '1971-04-01'           # 1 year after end
            self.dtr.end = '1970-01-01T05:30:00'    # 1 hour before start
            self.dtr.end = '1969-12-30'             # 1 day before start
            self.dtr.end = '1969-01-01'             # 1 year before start

    @unittest.skipUnless(nct.__name__ == 'netcdftime', "netcdftime package not present")
    def test_nc_datetime_props(self):
        dtr = dateutils.DateTimeRange('1970-01-01T06:30:00', '1970-04-01T18:30:00',
            calendar=cf_units.CALENDAR_PROLEPTIC_GREGORIAN)
        self.assertEqual(dtr.start_ncdt, nct.datetime(1970, 1, 1, 6, 30))
        self.assertEqual(dtr.end_ncdt, nct.datetime(1970, 4, 1, 18, 30))

        dtr = dateutils.DateTimeRange('1970-01-01', '1970-04-01',
            calendar=cf_units.CALENDAR_PROLEPTIC_GREGORIAN)
        self.assertEqual(dtr.start_ncdt, nct.datetime(1970, 1, 1))
        self.assertEqual(dtr.end_ncdt, nct.datetime(1970, 4, 1))

        # Depending on the version of the netcdftime package, we won't know what
        # type of object it will pass back when a non-gregorian calendar is used
        # (and no base class that we can check for either!).
        # So just test individual instance attributes.
        dtr = dateutils.DateTimeRange('1970-01-01', '1970-02-30', calendar=
            cf_units.CALENDAR_360_DAY)
        values = [getattr(dtr.end_ncdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 2, 30, 0, 0, 0])

    @unittest.skipUnless(nct.__name__ == 'cftime', "cftime package not present")
    def test_cf_datetime_props(self):
        dtr = dateutils.DateTimeRange('1970-01-01T06:30:00', '1970-04-01T18:30:00')
        self.assertEqual(dtr.start_ncdt, nct.DatetimeGregorian(1970, 1, 1, 6, 30))
        self.assertEqual(dtr.end_ncdt, nct.DatetimeGregorian(1970, 4, 1, 18, 30))

        dtr = dateutils.DateTimeRange('1970-01-01', '1970-04-01',
            calendar=cf_units.CALENDAR_PROLEPTIC_GREGORIAN)
        if version.parse(nct.__version__) >= version.parse("1.5.0"):
            # Comparison of 'cftime.datetime' instances with different
            # 'real-world' calendars was enabled.
            self.assertEqual(dtr.start_ncdt, nct.datetime(1970, 1, 1))
            self.assertEqual(dtr.end_ncdt, nct.datetime(1970, 4, 1))
        else:
            with self.assertRaises(TypeError):        
                self.assertEqual(dtr.start_ncdt, nct.datetime(1970, 1, 1))
            with self.assertRaises(TypeError):        
               self.assertEqual(dtr.end_ncdt, nct.datetime(1970, 4, 1))
        
    def test_datetime_props(self):
        dtr = dateutils.DateTimeRange('1970-01-01', '1970-04-01',
            calendar=cf_units.CALENDAR_PROLEPTIC_GREGORIAN)

        # Confirm that start_ncdt & end_ncdt properties are read-only.
        with self.assertRaises(AttributeError):
            dtr.start_ncdt = nct.datetime(1970, 1, 1)
            dtr.end_ncdt = nct.datetime(1970, 4, 1)

    def test_contains_leftclosed(self):
        dtr = dateutils.DateTimeRange('1970-01-01T06:30:00', '1970-04-01T18:30:00')
        self.assertFalse(dtr.contains('1970-01-01'))
        self.assertFalse(dtr.contains('1970-01-01T06:30:00', interval_type='leftopen'))
        self.assertTrue(dtr.contains('1970-01-01T06:30:00'))
        self.assertTrue(dtr.contains('1970-01-16'))
        self.assertTrue(dtr.contains(PDT(1970, 4, 1)))
        self.assertFalse(dtr.contains('1970-04-01T18:30:00'))
        self.assertFalse(dtr.contains('1970-04-02'))

    def test_contains_leftopen(self):
        dtr = dateutils.DateTimeRange('1970-01-01T06:30:00', '1970-04-01T18:30:00',
            interval_type='leftopen')
        self.assertFalse(dtr.contains('1970-01-01'))
        self.assertFalse(dtr.contains('1970-01-01T06:30:00'))
        self.assertTrue(dtr.contains('1970-01-01T06:30:00', interval_type='leftclosed'))
        self.assertTrue(dtr.contains('1970-01-16'))
        self.assertTrue(dtr.contains(datetime(1970, 4, 1)))
        self.assertTrue(dtr.contains('1970-04-01T18:30:00'))
        self.assertFalse(dtr.contains('1970-04-02'))

    def test_contains_open(self):
        dtr = dateutils.DateTimeRange('1970-01-01T06:30:00', '1970-04-01T18:30:00',
            interval_type='open')
        self.assertFalse(dtr.contains('1970-01-01'))
        self.assertFalse(dtr.contains('1970-01-01T06:30:00'))
        self.assertTrue(dtr.contains('1970-01-01T06:30:00', interval_type='leftclosed'))
        self.assertTrue(dtr.contains('1970-01-16'))
        self.assertTrue(dtr.contains(nct.datetime(1970, 4, 1)))
        self.assertFalse(dtr.contains('1970-04-01T18:30:00'))
        self.assertFalse(dtr.contains('1970-04-02'))

    def test_contains_closed(self):
        dtr = dateutils.DateTimeRange('1970-01-01T06:30:00', '1970-04-01T18:30:00',
            interval_type='closed')
        self.assertFalse(dtr.contains('1970-01-01'))
        self.assertFalse(dtr.contains('1970-01-01T06:30:00', interval_type='leftopen'))
        self.assertTrue(dtr.contains('1970-01-01T06:30:00'))
        self.assertTrue(dtr.contains('1970-01-16'))
        self.assertTrue(dtr.contains(PDT(1970, 2, 30)))
        self.assertTrue(dtr.contains('1970-04-01T18:30:00'))
        self.assertFalse(dtr.contains('1970-04-02'))

    def test_contains_with_cal_check(self):
        dtr = dateutils.DateTimeRange('1970-01-01T06:30:00', '1970-04-01T18:30:00')
        self.assertEqual(dtr.calendar, cf_units.CALENDAR_GREGORIAN)
        self.assertTrue(dtr.contains('1970-01-16', check_calendar=True))
        self.assertTrue(dtr.contains(PDT(1970, 1, 16), check_calendar=True))
        ndt = nct.datetime(1970, 1, 16)
        self.assertTrue(dtr.contains(ndt))
        if getattr(ndt, 'calendar', None):
            # Check for the calendar attribute on netcdftime objects.
            # If present then run some additional calendar tests.
            if dtr.calendar == ndt.calendar:
                self.assertTrue(dtr.contains(ndt, check_calendar=True))
            else:
                self.assertFalse(dtr.contains(ndt, check_calendar=True))

    def test_contains_bad_input(self):
        dtr = dateutils.DateTimeRange('1970-01-01T06:30:00', '1970-04-01T18:30:00')
        self.assertRaises(ValueError, dtr.contains, '1970-1-1')   # invalid date syntax
        self.assertRaises(ValueError, dtr.contains, [1970,1,1])   # invalid argument

    def test_time_updates(self):
        dtr = dateutils.DateTimeRange('1970-01-01T06:30:00', '1970-04-01T18:30:00')

        self.assertEqual(dtr.start_pdt, PDT(1970, 1, 1, 6, 30, 0))
        self.assertEqual(dtr.end_pdt, PDT(1970, 4, 1, 18, 30, 0))
        values = [getattr(dtr.start_ncdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 1, 1, 6, 30, 0])
        values = [getattr(dtr.end_ncdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 4, 1, 18, 30, 0])

        # update the start and end times
        dtr.start = '1970-02-01T00:00:00'
        dtr.end = '1970-05-01T12:00:00'

        self.assertEqual(dtr.start_pdt, PDT(1970, 2, 1, 0, 0, 0))
        self.assertEqual(dtr.end_pdt, PDT(1970, 5, 1, 12, 0, 0))
        values = [getattr(dtr.start_ncdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 2, 1, 0, 0, 0])
        values = [getattr(dtr.end_ncdt, att) for att in self.pdt_att_names]
        self.assertEqual(values, [1970, 5, 1, 12, 0, 0])


class TestPdtFromDateString(unittest.TestCase):
    """Test dateutils.pdt_from_date_string()"""

    def test_ymdhms(self):
        pdt = dateutils.pdt_from_date_string('2000-01-01T06:15:30')
        self.assertListEqual([2000, 1, 1, 6, 15, 30],
            [pdt.year, pdt.month, pdt.day, pdt.hour, pdt.minute, pdt.second])
        pdt = dateutils.pdt_from_date_string('2000-01-01 06:15:30')
        self.assertListEqual([2000, 1, 1, 6, 15, 30],
            [pdt.year, pdt.month, pdt.day, pdt.hour, pdt.minute, pdt.second])

    def test_ymdhm(self):
        pdt = dateutils.pdt_from_date_string('2000-01-01T06:15')
        self.assertListEqual([2000, 1, 1, 6, 15, 0],
            [pdt.year, pdt.month, pdt.day, pdt.hour, pdt.minute, pdt.second])
        pdt = dateutils.pdt_from_date_string('2000-01-01 06:15')
        self.assertListEqual([2000, 1, 1, 6, 15, 0],
            [pdt.year, pdt.month, pdt.day, pdt.hour, pdt.minute, pdt.second])

    def test_ymdh(self):
        pdt = dateutils.pdt_from_date_string('2000-01-01T06')
        self.assertListEqual([2000, 1, 1, 6, 0, 0],
            [pdt.year, pdt.month, pdt.day, pdt.hour, pdt.minute, pdt.second])
        pdt = dateutils.pdt_from_date_string('2000-01-01 06')
        self.assertListEqual([2000, 1, 1, 6, 0, 0],
            [pdt.year, pdt.month, pdt.day, pdt.hour, pdt.minute, pdt.second])

    def test_ymd(self):
        pdt = dateutils.pdt_from_date_string('2000-01-01')
        self.assertListEqual([2000, 1, 1, None, None, None],
            [pdt.year, pdt.month, pdt.day, pdt.hour, pdt.minute, pdt.second])
        pdt = dateutils.pdt_from_date_string('2000-01-01', default=0)
        self.assertListEqual([2000, 1, 1, 0, 0, 0],
            [pdt.year, pdt.month, pdt.day, pdt.hour, pdt.minute, pdt.second])

    def test_hms(self):
        pdt = dateutils.pdt_from_date_string('06:15:30')
        self.assertListEqual([None, None, None, 6, 15, 30],
            [pdt.year, pdt.month, pdt.day, pdt.hour, pdt.minute, pdt.second])
        pdt = dateutils.pdt_from_date_string('06:15:30', default=1)
        self.assertListEqual([1, 1, 1, 6, 15, 30],
            [pdt.year, pdt.month, pdt.day, pdt.hour, pdt.minute, pdt.second])

    def test_hm(self):
        pdt = dateutils.pdt_from_date_string('06:15')
        self.assertListEqual([None, None, None, 6, 15, 0],
            [pdt.year, pdt.month, pdt.day, pdt.hour, pdt.minute, pdt.second])
        pdt = dateutils.pdt_from_date_string('06:15', default=1)
        self.assertListEqual([1, 1, 1, 6, 15, 0],
            [pdt.year, pdt.month, pdt.day, pdt.hour, pdt.minute, pdt.second])

    def test_invalid_dates(self):
        self.assertRaises(ValueError, dateutils.pdt_from_date_string, '2000-01-01T')
        self.assertRaises(ValueError, dateutils.pdt_from_date_string, '2000-01')
        self.assertRaises(ValueError, dateutils.pdt_from_date_string, 'T06:15:30')
        self.assertRaises(ValueError, dateutils.pdt_from_date_string, '06:')
        self.assertRaises(ValueError, dateutils.pdt_from_date_string, '6')


class TestPdtToNcDatetime(unittest.TestCase):
    """Test dateutils.pdt_to_nc_datetime()"""

    def test_no_calendar(self):
        pdt = PDT(year=1970, month=1, day=1)
        ndt = dateutils.pdt_to_nc_datetime(pdt)
        self.assertListEqual([1970, 1, 1, 0, 0, 0],
            [ndt.year, ndt.month, ndt.day, ndt.hour, ndt.minute, ndt.second])

        pdt = PDT(year=1970, month=1, day=1, hour=6, minute=15, second=30)
        ndt = dateutils.pdt_to_nc_datetime(pdt)
        self.assertListEqual([1970, 1, 1, 6, 15, 30],
            [ndt.year, ndt.month, ndt.day, ndt.hour, ndt.minute, ndt.second])

    def test_gregorian_calendar_with_date(self):
        pdt = PDT(year=1970, month=1, day=1)
        ndt = dateutils.pdt_to_nc_datetime(pdt, calendar=cf_units.CALENDAR_GREGORIAN)
        self.assertListEqual([1970, 1, 1, 0, 0, 0],
            [ndt.year, ndt.month, ndt.day, ndt.hour, ndt.minute, ndt.second])
        cal = getattr(ndt, 'calendar', '')
        if cal:
            if version.parse(nct.__version__) >= version.parse("1.5.2"):
                # The 'gregorian' calendar was silently changed to 'standard'
                # internally, since 'gregorian' deprecated in CF v1.9.
                self.assertEqual(cal, cf_units.CALENDAR_STANDARD)
            else:
                self.assertEqual(cal, cf_units.CALENDAR_GREGORIAN)

    def test_gregorian_calendar_with_date_time(self):
        pdt = PDT(year=1970, month=1, day=1, hour=6, minute=15, second=30)
        ndt = dateutils.pdt_to_nc_datetime(pdt, calendar=cf_units.CALENDAR_GREGORIAN)
        self.assertListEqual([1970, 1, 1, 6, 15, 30],
            [ndt.year, ndt.month, ndt.day, ndt.hour, ndt.minute, ndt.second])
        cal = getattr(ndt, 'calendar', '')
        if cal:
            if version.parse(nct.__version__) >= version.parse("1.5.2"):
                # The 'gregorian' calendar was silently changed to 'standard'
                # internally, since 'gregorian' deprecated in CF v1.9.
                self.assertEqual(cal, cf_units.CALENDAR_STANDARD)
            else:
                self.assertEqual(cal, cf_units.CALENDAR_GREGORIAN)

    def test_360_day_calendar(self):
        pdt = PDT(year=1970, month=1, day=1)
        ndt = dateutils.pdt_to_nc_datetime(pdt, calendar=cf_units.CALENDAR_360_DAY)
        self.assertListEqual([1970, 1, 1, 0, 0, 0],
            [ndt.year, ndt.month, ndt.day, ndt.hour, ndt.minute, ndt.second])
        cal = getattr(ndt, 'calendar', '')
        if cal: self.assertEqual(cal, cf_units.CALENDAR_360_DAY)

        pdt = PDT(year=1970, month=1, day=1, hour=6, minute=15, second=30)
        ndt = dateutils.pdt_to_nc_datetime(pdt, calendar=cf_units.CALENDAR_360_DAY)
        self.assertListEqual([1970, 1, 1, 6, 15, 30],
            [ndt.year, ndt.month, ndt.day, ndt.hour, ndt.minute, ndt.second])
        if cal: self.assertEqual(cal, cf_units.CALENDAR_360_DAY)

    def test_invalid_calendar(self):
        with self.assertRaises(ValueError):
            dateutils.pdt_to_nc_datetime(PDT(year=1970, month=1, day=1), calendar='360Day')

    def test_invalid_dates(self):
        with self.assertRaises(ValueError):
            dateutils.pdt_to_nc_datetime(PDT(year=1970))
            dateutils.pdt_to_nc_datetime(PDT(year=1970, month=1))


class TestPdtCompare(unittest.TestCase):
    """Test dateutils.pdt_compare()"""

    def test_with_fully_defined_pdts(self):
        pdt1 = PDT(1970, 1, 1, 6, 15, 30)
        pdt2 = PDT(1970, 2, 1, 12, 15, 30)
        self.assertTrue(dateutils.pdt_compare(pdt1, operator.lt, pdt2))
        self.assertFalse(dateutils.pdt_compare(pdt1, operator.eq, pdt2))
        self.assertFalse(dateutils.pdt_compare(pdt1, operator.gt, pdt2))

    def test_with_partially_defined_pdts(self):
        pdt1 = PDT(1970, 1, 1, 0, 0, 0)
        pdt2 = PDT(1970, 1, 1)
        self.assertTrue(dateutils.pdt_compare(pdt1, operator.le, pdt2))
        self.assertTrue(dateutils.pdt_compare(pdt1, operator.eq, pdt2))
        self.assertFalse(dateutils.pdt_compare(pdt1, operator.gt, pdt2))
        pdt2 = PDT(1970, 2, 1)
        self.assertTrue(dateutils.pdt_compare(pdt1, operator.le, pdt2))
        self.assertFalse(dateutils.pdt_compare(pdt1, operator.eq, pdt2))
        self.assertFalse(dateutils.pdt_compare(pdt1, operator.gt, pdt2))

    def test_with_string_operator_names(self):
        pdt1 = PDT(1970, 1, 1, 6, 15, 30)
        pdt2 = PDT(1970, 2, 1, 12, 15, 30)
        self.assertTrue(dateutils.pdt_compare(pdt1, 'lt', pdt2))
        self.assertTrue(dateutils.pdt_compare(pdt1, 'le', pdt2))
        self.assertFalse(dateutils.pdt_compare(pdt1, 'eq', pdt2))
        self.assertTrue(dateutils.pdt_compare(pdt1, 'ne', pdt2))
        self.assertFalse(dateutils.pdt_compare(pdt1, 'ge', pdt2))
        self.assertFalse(dateutils.pdt_compare(pdt1, 'gt', pdt2))

    def test_without_ymd(self):
        pdt1 = PDT(hour=6, minute=30, second=0)
        pdt2 = PDT(hour=6, minute=30)
        self.assertFalse(dateutils.pdt_compare(pdt1, 'lt', pdt2))
        self.assertTrue(dateutils.pdt_compare(pdt1, 'eq', pdt2))
        self.assertFalse(dateutils.pdt_compare(pdt1, 'gt', pdt2))
        pdt1 = PDT(hour=6, minute=30, second=0)
        pdt2 = PDT(hour=9, minute=30)
        self.assertTrue(dateutils.pdt_compare(pdt1, 'lt', pdt2))
        self.assertFalse(dateutils.pdt_compare(pdt1, 'eq', pdt2))
        self.assertFalse(dateutils.pdt_compare(pdt1, 'gt', pdt2))

    def test_invalid_operator(self):
        pdt1 = PDT(1970, 1, 1, 0, 0, 0)
        pdt2 = PDT(1970, 1, 1)
        self.assertRaises(AttributeError, dateutils.pdt_compare, pdt1, 'EQ', pdt2)
        self.assertRaises(AttributeError, dateutils.pdt_compare, pdt1, 'xx', pdt2)


class TestParseYmdString(unittest.TestCase):
    """Test dateutils.parse_ymd_string()"""

    def test_valid_dates(self):
        self.assertListEqual(dateutils.parse_ymd_string('1970-01-01'), [1970, 1, 1])
        self.assertListEqual(dateutils.parse_ymd_string('1970-02-30'), [1970, 2, 30])
        self.assertListEqual(dateutils.parse_ymd_string('+1970-01-01'), [1970, 1, 1])
        self.assertListEqual(dateutils.parse_ymd_string('-1970-01-01'), [-1970, 1, 1])
        self.assertListEqual(dateutils.parse_ymd_string('10000-01-01'), [10000, 1, 1])
        self.assertListEqual(dateutils.parse_ymd_string('-10000-01-01'), [-10000, 1, 1])
        self.assertListEqual(dateutils.parse_ymd_string('0500-01-01'), [500, 1, 1])
        self.assertListEqual(dateutils.parse_ymd_string('-0500-01-01'), [-500, 1, 1])
        self.assertListEqual(dateutils.parse_ymd_string('0000-01-01'), [0, 1, 1])
        self.assertListEqual(dateutils.parse_ymd_string('+0000-01-01'), [0, 1, 1])

    def test_invalid_dates(self):
        self.assertRaises(ValueError, dateutils.parse_ymd_string, '1970/01/01')
        self.assertRaises(ValueError, dateutils.parse_ymd_string, '1970-1-1')
        self.assertRaises(ValueError, dateutils.parse_ymd_string, '1970-01')
        self.assertRaises(ValueError, dateutils.parse_ymd_string, '1970')
        self.assertRaises(ValueError, dateutils.parse_ymd_string, '500-01-01')


class TestParseHmsString(unittest.TestCase):
    """Test dateutils.parse_hms_string()"""

    def test_valid_times(self):
        self.assertListEqual(dateutils.parse_hms_string('00:15:30'), [0, 15, 30])
        self.assertListEqual(dateutils.parse_hms_string('0:15'), [0, 15, 0])
        self.assertListEqual(dateutils.parse_hms_string('06:15:30'), [6, 15, 30])
        self.assertListEqual(dateutils.parse_hms_string('06:15'), [6, 15, 0])
        self.assertListEqual(dateutils.parse_hms_string('06'), [6, 0, 0])
        self.assertListEqual(dateutils.parse_hms_string('6:5:9'), [6, 5, 9])
        self.assertListEqual(dateutils.parse_hms_string('6:5'), [6, 5, 0])
        self.assertListEqual(dateutils.parse_hms_string('6'), [6, 0, 0])

    def test_invalid_times(self):
        self.assertRaises(ValueError, dateutils.parse_hms_string, 'T06:15:30')
        self.assertRaises(ValueError, dateutils.parse_hms_string, '06:15:')
        self.assertRaises(ValueError, dateutils.parse_hms_string, '06:')
        self.assertRaises(ValueError, dateutils.parse_hms_string, '')


class TestValidDatetimeFormat(unittest.TestCase):
    """Test dateutils.is_valid_datetime_format()"""

    def test_valid_datetimes(self):
        self.assertTrue(dateutils.is_valid_datetime_format('1970-01-01T09:15:30'))
        self.assertTrue(dateutils.is_valid_datetime_format('1970-01-01 09:15:30'))
        self.assertTrue(dateutils.is_valid_datetime_format(u'1970-01-01T09:15:30'))
        self.assertTrue(dateutils.is_valid_datetime_format('1970-01-01T09:15'))
        self.assertTrue(dateutils.is_valid_datetime_format('1970-01-01T09'))
        self.assertTrue(dateutils.is_valid_datetime_format('1970-01-01 09:15'))
        self.assertTrue(dateutils.is_valid_datetime_format('1970-01-01 09'))
        self.assertTrue(dateutils.is_valid_datetime_format('1970-02-30'))
        self.assertTrue(dateutils.is_valid_datetime_format('10000-01-01'))
        self.assertTrue(dateutils.is_valid_datetime_format('-9999-01-01'))
        self.assertTrue(dateutils.is_valid_datetime_format('0500-01-01'))
        self.assertTrue(dateutils.is_valid_datetime_format('09:15:30'))
        self.assertTrue(dateutils.is_valid_datetime_format('09:15'))

    def test_invalid_datetimes(self):
        self.assertFalse(dateutils.is_valid_datetime_format('1970-01-01t09:15:30'))    # lower case 't'
        self.assertFalse(dateutils.is_valid_datetime_format(' 1970-01-01T09:15:30 '))  # extraneous spaces
        self.assertFalse(dateutils.is_valid_datetime_format('1970-01-01 09:15:30.5'))  # extraneous digits
        self.assertFalse(dateutils.is_valid_datetime_format('1970-1-1 9:15:30'))       # insufficient digits
        self.assertFalse(dateutils.is_valid_datetime_format('1970/01/01 09:15:30'))    # incorrect date separator
        self.assertFalse(dateutils.is_valid_datetime_format('1970-01-01 09.15.30'))    # incorrect time separator
        self.assertFalse(dateutils.is_valid_datetime_format('500-01-01'))              # leading zero missing
        self.assertFalse(dateutils.is_valid_datetime_format('1970-01'))                # incomplete date
        self.assertFalse(dateutils.is_valid_datetime_format('09'))                     # ambiguous value


class TestDateRounding(unittest.TestCase):
    """Test the date rounding functions."""

    def test_decadal_rounding(self):
        """Test decadal date rounding."""
        pdt = PDT(year=1969, month=11, day=1)
        pdt = dateutils.round_date_down(pdt, '10y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1959, 12, 1])

        pdt = PDT(year=1969, month=12, day=1)
        pdt = dateutils.round_date_down(pdt, '10y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 12, 1])

        pdt = PDT(year=1970, month=1, day=1)
        pdt = dateutils.round_date_down(pdt, '10y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 12, 1])

        pdt = PDT(year=1974, month=12, day=1)
        pdt = dateutils.round_date_down(pdt, '10y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 12, 1])

        pdt = PDT(year=1979, month=1, day=1)
        pdt = dateutils.round_date_down(pdt, '10y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 12, 1])

        pdt = PDT(year=1969, month=11, day=1)
        pdt = dateutils.round_date_up(pdt, '10y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 12, 1])
 
        pdt = PDT(year=1969, month=12, day=1)
        pdt = dateutils.round_date_up(pdt, '10y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1979, 12, 1])
 
        pdt = PDT(year=1970, month=1, day=1)
        pdt = dateutils.round_date_up(pdt, '10y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1979, 12, 1])
 
        pdt = PDT(year=1974, month=12, day=1)
        pdt = dateutils.round_date_up(pdt, '10y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1979, 12, 1])
 
        pdt = PDT(year=1979, month=1, day=1)
        pdt = dateutils.round_date_up(pdt, '10y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1979, 12, 1])

    def test_5year_rounding(self):
        """Test 5-year date rounding."""
        pdt = PDT(year=1969, month=11, day=1)
        pdt = dateutils.round_date_down(pdt, '5y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1964, 12, 1])

        pdt = PDT(year=1969, month=12, day=1)
        pdt = dateutils.round_date_down(pdt, '5y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 12, 1])

        pdt = PDT(year=1970, month=1, day=1)
        pdt = dateutils.round_date_down(pdt, '5y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 12, 1])

        pdt = PDT(year=1970, month=12, day=1)
        pdt = dateutils.round_date_down(pdt, '5y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 12, 1])

        pdt = PDT(year=1974, month=1, day=1)
        pdt = dateutils.round_date_down(pdt, '5y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 12, 1])

        pdt = PDT(year=1969, month=11, day=1)
        pdt = dateutils.round_date_up(pdt, '5y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 12, 1])
 
        pdt = PDT(year=1969, month=12, day=1)
        pdt = dateutils.round_date_up(pdt, '5y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1974, 12, 1])
 
        pdt = PDT(year=1970, month=1, day=1)
        pdt = dateutils.round_date_up(pdt, '5y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1974, 12, 1])
 
        pdt = PDT(year=1970, month=12, day=1)
        pdt = dateutils.round_date_up(pdt, '5y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1974, 12, 1])
 
        pdt = PDT(year=1974, month=1, day=1)
        pdt = dateutils.round_date_up(pdt, '5y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1974, 12, 1])

    def test_annual_rounding(self):
        """Test annual date rounding."""
        pdt = PDT(year=1970, month=1, day=1)
        pdt = dateutils.round_date_down(pdt, 'y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 12, 1])

        pdt = PDT(year=1970, month=1, day=16)
        pdt = dateutils.round_date_down(pdt, 'y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 12, 1])

        pdt = PDT(year=1970, month=12, day=1)
        pdt = dateutils.round_date_down(pdt, 'y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 12, 1])

        pdt = PDT(year=1970, month=12, day=16)
        pdt = dateutils.round_date_down(pdt, 'y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 12, 1])

        pdt = PDT(year=1970, month=1, day=1)
        pdt = dateutils.round_date_up(pdt, 'y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 12, 1])

        pdt = PDT(year=1970, month=1, day=16)
        pdt = dateutils.round_date_up(pdt, 'y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 12, 1])

        pdt = PDT(year=1970, month=12, day=1)
        pdt = dateutils.round_date_up(pdt, 'y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1971, 12, 1])

        pdt = PDT(year=1970, month=12, day=16)
        pdt = dateutils.round_date_up(pdt, 'y')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1971, 12, 1])

    def test_annual_rounding_custom_ref_date(self):
        """Test annual date rounding with custom reference date."""
        # Define Jan 1st as standard year boundary.
        ref_pdt = PDT(year=1800, month=1, day=1)

        pdt = PDT(year=1970, month=1, day=1)
        pdt = dateutils.round_date_down(pdt, 'y', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 1, 1])

        pdt = PDT(year=1970, month=12, day=16)
        pdt = dateutils.round_date_down(pdt, 'y', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 1, 1])

        pdt = PDT(year=1970, month=1, day=1)
        pdt = dateutils.round_date_up(pdt, 'y', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1971, 1, 1])

        pdt = PDT(year=1970, month=12, day=16)
        pdt = dateutils.round_date_up(pdt, 'y', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1971, 1, 1])

    def test_seasonal_rounding_down(self):
        """Test seasonal date rounding down."""
        # start of DJF season
        pdt = PDT(year=1969, month=12, day=1)
        pdt = dateutils.round_date_down(pdt, 's')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 12, 1])

        # middle of DJF season
        pdt = PDT(year=1970, month=1, day=16)
        pdt = dateutils.round_date_down(pdt, 's')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 12, 1])

        # start of MAM season
        pdt = PDT(year=1970, month=3, day=1)
        pdt = dateutils.round_date_down(pdt, 's')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 3, 1])

        # middle of MAM season
        pdt = PDT(year=1970, month=4, day=16)
        pdt = dateutils.round_date_down(pdt, 's')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 3, 1])

    def test_seasonal_rounding_up(self):
        """Test seasonal date rounding up."""
        # start of DJF season
        pdt = PDT(year=1969, month=12, day=1)
        pdt = dateutils.round_date_up(pdt, 's')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 3, 1])

        # middle of DJF season
        pdt = PDT(year=1969, month=12, day=16)
        pdt = dateutils.round_date_up(pdt, 's')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 3, 1])

        # start of JJA season
        pdt = PDT(year=1970, month=6, day=1)
        pdt = dateutils.round_date_up(pdt, 's')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 9, 1])

        # middle of JJA season
        pdt = PDT(year=1970, month=7, day=16)
        pdt = dateutils.round_date_up(pdt, 's')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 9, 1])

        # start of SON season
        pdt = PDT(year=1970, month=9, day=1)
        pdt = dateutils.round_date_up(pdt, 's')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 12, 1])

        # middle of SON season
        pdt = PDT(year=1970, month=10, day=16)
        pdt = dateutils.round_date_up(pdt, 's')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 12, 1])

    def test_seasonal_rounding_custom_ref_date(self):
        """Test seasonal date rounding with custom reference date."""
        # Standard climatological seasons always use day=1, so these tests are
        # mainly for the sake of completeness, or nearly so.
        ref_pdt = PDT(year=1800, month=1, day=16)

        pdt = PDT(year=1970, month=1, day=1)
        pdt = dateutils.round_date_down(pdt, 's', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 10, 16])

        pdt = PDT(year=1970, month=1, day=30)
        pdt = dateutils.round_date_down(pdt, 's', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 1, 16])

        pdt = PDT(year=1970, month=12, day=1)
        pdt = dateutils.round_date_down(pdt, 's', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 10, 16])

        pdt = PDT(year=1970, month=12, day=30)
        pdt = dateutils.round_date_down(pdt, 's', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 10, 16])

        pdt = PDT(year=1970, month=1, day=30)
        pdt = dateutils.round_date_up(pdt, 's', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 4, 16])

        pdt = PDT(year=1970, month=12, day=1)
        pdt = dateutils.round_date_up(pdt, 's', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1971, 1, 16])

    def test_monthly_rounding(self):
        """Test monthly date rounding."""
        pdt = PDT(year=1970, month=1, day=1)
        pdt = dateutils.round_date_down(pdt, 'm')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 1, 1])

        pdt = PDT(year=1970, month=2, day=30)
        pdt = dateutils.round_date_down(pdt, 'm')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 2, 1])

        pdt = PDT(year=1970, month=12, day=16)
        pdt = dateutils.round_date_down(pdt, 'm')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 12, 1])

        pdt = PDT(year=1970, month=1, day=1)
        pdt = dateutils.round_date_up(pdt, 'm')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 2, 1])

        pdt = PDT(year=1970, month=2, day=30)
        pdt = dateutils.round_date_up(pdt, 'm')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 3, 1])

        pdt = PDT(year=1970, month=12, day=16)
        pdt = dateutils.round_date_up(pdt, 'm')
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1971, 1, 1])

    def test_monthly_rounding_custom_ref_date(self):
        """Test monthly date rounding with custom reference date."""
        ref_pdt = PDT(year=1800, month=1, day=16)

        pdt = PDT(year=1970, month=1, day=1)
        pdt = dateutils.round_date_down(pdt, 'm', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1969, 12, 16])

        pdt = PDT(year=1970, month=1, day=16)
        pdt = dateutils.round_date_down(pdt, 'm', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 1, 16])

        pdt = PDT(year=1970, month=1, day=30)
        pdt = dateutils.round_date_down(pdt, 'm', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 1, 16])

        pdt = PDT(year=1970, month=1, day=1)
        pdt = dateutils.round_date_up(pdt, 'm', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 1, 16])

        pdt = PDT(year=1970, month=1, day=16)
        pdt = dateutils.round_date_up(pdt, 'm', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 2, 16])

        pdt = PDT(year=1970, month=1, day=30)
        pdt = dateutils.round_date_up(pdt, 'm', ref_date=ref_pdt)
        self.assertEqual([pdt.year, pdt.month, pdt.day], [1970, 2, 16])


class TestMooseToIsoDate(unittest.TestCase):
    """Test the moose_date_to_iso_date function."""

    def test_good_date(self):
        iso_date = dateutils.moose_date_to_iso_date('1970/01/01')
        self.assertEqual(iso_date, '1970-01-01')

    def test_good_date_hhmm(self):
        iso_date = dateutils.moose_date_to_iso_date('1970/01/01 12:30')
        self.assertEqual(iso_date, '1970-01-01T12:30:00')

    def test_good_date_hhmmss(self):
        iso_date = dateutils.moose_date_to_iso_date('1970/01/01 12:30:00')
        self.assertEqual(iso_date, '1970-01-01T12:30:00')

    def test_big_year(self):
        iso_date = dateutils.moose_date_to_iso_date('10000/01/01')
        self.assertEqual(iso_date, '10000-01-01')

    def test_big_year_hhmm(self):
        iso_date = dateutils.moose_date_to_iso_date('10000/01/01 12:30')
        self.assertEqual(iso_date, '10000-01-01T12:30:00')

    def test_big_year_hhmmss(self):
        iso_date = dateutils.moose_date_to_iso_date('10000/01/01 12:30:00')
        self.assertEqual(iso_date, '10000-01-01T12:30:00')

    def test_small_year(self):
        iso_date = dateutils.moose_date_to_iso_date('500/01/01')
        self.assertEqual(iso_date, '0500-01-01')
        iso_date = dateutils.moose_date_to_iso_date('50/01/01')
        self.assertEqual(iso_date, '0050-01-01')

    def test_negative_year(self):
        self.assertRaises(ValueError, dateutils.moose_date_to_iso_date, '-1970/1/1')

    def test_bad_date(self):
        self.assertRaises(ValueError, dateutils.moose_date_to_iso_date, '1970/1/1')

    def test_bad_hhmm(self):
        self.assertRaises(ValueError, dateutils.moose_date_to_iso_date, '1970/01/01 9:30')

    def test_no_date(self):
        self.assertRaises(ValueError, dateutils.moose_date_to_iso_date, '12:30:00')


class TestIsoToMooseDate(unittest.TestCase):
    """Test the iso_date_to_moose_date function."""

    def test_good_date(self):
        moose_date = dateutils.iso_date_to_moose_date('1970-01-01')
        self.assertEqual(moose_date, '1970/01/01')

    def test_good_date_hhmmss(self):
        moose_date = dateutils.iso_date_to_moose_date('1970-01-01T12:30:00')
        self.assertEqual(moose_date, '1970/01/01 12:30')

    def test_good_date_hhmmss_inc_secs(self):
        moose_date = dateutils.iso_date_to_moose_date('1970-01-01T12:30:15',
            include_secs=True)
        self.assertEqual(moose_date, '1970/01/01 12:30:15')

    def test_big_year(self):
        moose_date = dateutils.iso_date_to_moose_date('10000-01-01')
        self.assertEqual(moose_date, '10000/01/01')

    def test_big_year_hhmmss(self):
        moose_date = dateutils.iso_date_to_moose_date('1970-01-01T12:30:00')
        self.assertEqual(moose_date, '1970/01/01 12:30')

    def test_small_year(self):
        moose_date = dateutils.iso_date_to_moose_date('0500-01-01')
        self.assertEqual(moose_date, '0500/01/01')
        self.assertRaises(ValueError, dateutils.iso_date_to_moose_date, '500-01-01')

    def test_negative_year(self):
        self.assertRaises(ValueError, dateutils.iso_date_to_moose_date, '-1970-01-01')

    def test_bad_date(self):
        self.assertRaises(ValueError, dateutils.iso_date_to_moose_date, '1970-1-1')

    def test_bad_hhmmss(self):
        self.assertRaises(ValueError, dateutils.iso_date_to_moose_date, '1970-01-01T09.30.00')

    def test_no_date(self):
        self.assertRaises(ValueError, dateutils.iso_date_to_moose_date, '12:30:00')


class TestImmutableDateTime(unittest.TestCase):
    """Test the ImmutableDateTime class."""

    def test_immutability(self):
        dt = dateutils.ImmutableDateTime(1970,1,1)
        with self.assertRaises(AttributeError):
            dt.year = 1971
            dt.newatt = 'foo'
            del dt.microsecond

    def test_infinity_constants(self):
        self.assertNotEqual(dateutils.DATETIME_POS_INF, dateutils.DATETIME_NEG_INF)
        self.assertTrue(dateutils.DATETIME_POS_INF > dateutils.DATETIME_NEG_INF)
        self.assertTrue(dateutils.DATETIME_NEG_INF < dateutils.DATETIME_POS_INF)
        pos_inf_as_str = '{}-09-09 09:09:09'.format(MAX_YEAR_VALUE)
        pos_inf_as_iso_str = '{}-09-09T09:09:09'.format(MAX_YEAR_VALUE)
        self.assertEqual(str(dateutils.DATETIME_POS_INF), pos_inf_as_str)
        self.assertEqual(dateutils.DATETIME_POS_INF.strftime(), pos_inf_as_str)
        self.assertEqual(dateutils.DATETIME_POS_INF.isoformat(), pos_inf_as_iso_str)

    def test_string_formatting(self):
        dt = dateutils.ImmutableDateTime(1970,1,1)
        self.assertEqual(str(dt), '1970-01-01 00:00:00')
        self.assertEqual(dt.strftime(), '1970-01-01 00:00:00')
        self.assertEqual(dt.isoformat(), '1970-01-01T00:00:00')
        self.assertEqual('{:%Y/%m/%d}'.format(dt), '1970/01/01')

        dt = dateutils.ImmutableDateTime(-1970,1,1)
        self.assertEqual(str(dt), '-1970-01-01 00:00:00')
        self.assertEqual(dt.strftime(), '-1970-01-01 00:00:00')
        self.assertEqual(dt.isoformat(), '-1970-01-01T00:00:00')
        self.assertEqual('{:%Y/%m/%d}'.format(dt), '-1970/01/01')

        dt = dateutils.ImmutableDateTime(1,1,1)
        year = '{0}{0}{0}1'.format(_get_cftime_date_padding_char())
        self.assertEqual(str(dt), '0001-01-01 00:00:00')
        self.assertEqual(dt.strftime(), '{}-01-01 00:00:00'.format(year))
        self.assertEqual(dt.isoformat(), '0001-01-01T00:00:00')
        self.assertEqual('{:%Y/%m/%d}'.format(dt), '{}/01/01'.format(year))

    def test_with_partialdatetimes(self):
        test_val_set = [
            [PDT(1970,1,1), False, True, True, False],
            [PDT(-1970,1,1), False, True, True, False],
            [PDT(-MAX_YEAR_VALUE,9,9,9,9,9), True, False, True, False],
            [PDT(MAX_YEAR_VALUE,9,9,9,9,9), False, True, False, True],
        ]

        for test_vals in test_val_set:
            self.assertEqual(dateutils.DATETIME_NEG_INF == test_vals[0], test_vals[1])
            self.assertEqual(dateutils.DATETIME_NEG_INF < test_vals[0], test_vals[2])
            self.assertEqual(dateutils.DATETIME_POS_INF > test_vals[0], test_vals[3])
            self.assertEqual(dateutils.DATETIME_POS_INF == test_vals[0], test_vals[4])

    def test_with_ncdatetimes(self):
        test_val_set = [
            [nct.datetime(1970,1,1), False, True, True, False],
            [nct.datetime(-1970,1,1), False, True, True, False],
            [nct.datetime(-MAX_YEAR_VALUE,9,9,9,9,9), True, False, True, False],
            [nct.datetime(MAX_YEAR_VALUE,9,9,9,9,9), False, True, False, True],
        ]

        for test_vals in test_val_set:
            self.assertEqual(dateutils.DATETIME_NEG_INF == test_vals[0], test_vals[1])
            self.assertEqual(dateutils.DATETIME_NEG_INF < test_vals[0], test_vals[2])
            self.assertEqual(dateutils.DATETIME_POS_INF > test_vals[0], test_vals[3])
            self.assertEqual(dateutils.DATETIME_POS_INF == test_vals[0], test_vals[4])

        self.assertTrue(dateutils.DATETIME_NEG_INF < nct.datetime(1970,1,1))
        self.assertTrue(dateutils.DATETIME_POS_INF > nct.datetime(1970,1,1))
        self.assertEqual(dateutils.DATETIME_NEG_INF, nct.datetime(-MAX_YEAR_VALUE,9,9,9,9,9))
        self.assertEqual(dateutils.DATETIME_POS_INF, nct.datetime(MAX_YEAR_VALUE,9,9,9,9,9))

    def test_with_valid_pydatetimes(self):
        test_val_set = [
            [datetime(1,1,1), False, True, True, False],
            [datetime(1970,1,1), False, True, True, False],
            [datetime(9999,9,9), False, True, True, False],
        ]

        for test_vals in test_val_set:
            self.assertEqual(dateutils.DATETIME_NEG_INF == test_vals[0], test_vals[1])
            self.assertEqual(dateutils.DATETIME_NEG_INF < test_vals[0], test_vals[2])
            self.assertEqual(dateutils.DATETIME_POS_INF > test_vals[0], test_vals[3])
            self.assertEqual(dateutils.DATETIME_POS_INF == test_vals[0], test_vals[4])

        # Comparisons involving Python datetimes on the left-hand side do not work.
        #self.assertTrue(datetime(1970,1,1) > dateutils.DATETIME_NEG_INF)
        #self.assertTrue(datetime(1970,1,1) < dateutils.DATETIME_POS_INF)

    def test_with_invalid_pydatetimes(self):
        # Python datetimes outside the range 1..9999 raise a ValueError
        with self.assertRaises(ValueError):
            self.assertTrue(dateutils.DATETIME_NEG_INF == datetime(-MAX_YEAR_VALUE,9,9,9,9,9))
            self.assertTrue(dateutils.DATETIME_POS_INF == datetime(MAX_YEAR_VALUE,9,9,9,9,9))
            self.assertTrue(dateutils.DATETIME_POS_INF > datetime(0,1,1))

    def test_with_invalid_datetime_parts(self):
        with self.assertRaises(AssertionError):
            dt = dateutils.ImmutableDateTime(1970, 0, 1)
            dt = dateutils.ImmutableDateTime(1970, 13, 1)
            dt = dateutils.ImmutableDateTime(1970, 1, 0)
            dt = dateutils.ImmutableDateTime(1970, 1, 32)
            dt = dateutils.ImmutableDateTime(1970, 1, 1, 24)
            dt = dateutils.ImmutableDateTime(1970, 1, 1, 12, 60)
            dt = dateutils.ImmutableDateTime(1970, 1, 1, 12, 30, 60)


class TestIterDates(unittest.TestCase):
    """Test the dateutils.iter_dates iterator yielding datetime objects."""

    def test_with_defaults(self):
        it = dateutils.iter_dates('1970-04-01', '1970-05-01', step=5)
        dates = [x for x in it]
        self.assertEqual(str(dates[0]), '1970-04-01 00:00:00')
        self.assertEqual(str(dates[1]), '1970-04-06 00:00:00')
        self.assertEqual(str(dates[-1]), '1970-04-26 00:00:00')

    def test_with_extra_minute(self):
        it = dateutils.iter_dates('1970-04-01', '1970-05-01T00:01', step=5)
        dates = [x for x in it]
        self.assertEqual(str(dates[0]), '1970-04-01 00:00:00')
        self.assertEqual(str(dates[-1]), '1970-05-01 00:00:00')

    def test_with_neg_step(self):
        it = dateutils.iter_dates('1970-05-01', '1970-04-01', step=-5)
        dates = [x for x in it]
        self.assertEqual(str(dates[0]), '1970-05-01 00:00:00')
        self.assertEqual(str(dates[1]), '1970-04-26 00:00:00')
        self.assertEqual(str(dates[-1]), '1970-04-06 00:00:00')

    def test_with_endpoint(self):
        it = dateutils.iter_dates('1970-04-01', '1970-05-01', step=5,
            endpoint=True)
        dates = [x for x in it]
        self.assertEqual(str(dates[0]), '1970-04-01 00:00:00')
        self.assertEqual(str(dates[-1]), '1970-05-01 00:00:00')

    def test_with_endpoint_and_neg_step(self):
        it = dateutils.iter_dates('1970-05-01', '1970-04-01', step=-5,
            endpoint=True)
        dates = [x for x in it]
        self.assertEqual(str(dates[0]), '1970-05-01 00:00:00')
        self.assertEqual(str(dates[1]), '1970-04-26 00:00:00')
        self.assertEqual(str(dates[-1]), '1970-04-01 00:00:00')

    def test_with_cal360(self):
        tu = cf_units.Unit('days since 1950-01-01', calendar='360_day')
        it = dateutils.iter_dates('1970-01-01', '1970-02-01', step=5, time_units=tu)
        dates = [x for x in it]
        self.assertEqual(str(dates[0]), '1970-01-01 00:00:00')
        self.assertEqual(str(dates[1]), '1970-01-06 00:00:00')
        self.assertEqual(str(dates[-1]), '1970-01-26 00:00:00')

        tu = cf_units.Unit('hours since 1950-01-01', calendar='360_day')
        it = dateutils.iter_dates('1970-01-01T12', '1970-02-01T12', step=5,
            time_units=tu)
        dates = [x for x in it]
        self.assertEqual(str(dates[0]), '1970-01-01 12:00:00')
        self.assertEqual(str(dates[1]), '1970-01-06 12:00:00')
        self.assertEqual(str(dates[-1]), '1970-01-26 12:00:00')

    def test_with_cal360_and_endpoint(self):
        tu = cf_units.Unit('days since 1950-01-01', calendar='360_day')
        it = dateutils.iter_dates('1970-01-01', '1970-02-01', step=5, time_units=tu,
            endpoint=True)
        dates = [x for x in it]
        self.assertEqual(str(dates[0]), '1970-01-01 00:00:00')
        self.assertEqual(str(dates[-1]), '1970-02-01 00:00:00')

        tu = cf_units.Unit('hours since 1950-01-01', calendar='360_day')
        it = dateutils.iter_dates('1970-01-01T12', '1970-02-01T12', step=5,
            time_units=tu, endpoint=True)
        dates = [x for x in it]
        self.assertEqual(str(dates[0]), '1970-01-01 12:00:00')
        self.assertEqual(str(dates[-1]), '1970-02-01 12:00:00')

    def test_with_hourly_step(self):
        it = dateutils.iter_dates('1970-04-01', '1970-04-02', step=3600/86400.)
        dates = [x for x in it]
        self.assertEqual(str(dates[0]), '1970-04-01 00:00:00')
        self.assertEqual(str(dates[1]), '1970-04-01 01:00:00')
        self.assertEqual(str(dates[-1]), '1970-04-01 23:00:00')

        it = dateutils.iter_dates('1970-04-01', '1970-04-02', step=3600/86400.,
            endpoint=True)
        dates = [x for x in it]
        self.assertEqual(str(dates[0]), '1970-04-01 00:00:00')
        self.assertEqual(str(dates[-2]), '1970-04-01 23:00:00')
        self.assertEqual(str(dates[-1]), '1970-04-02 00:00:00')


class TestIterDatesForNumVals(unittest.TestCase):
    """Test the dateutils.iter_dates iterator yielding numeric time values."""

    def test_with_default_cal(self):
        it = dateutils.iter_dates('1970-01-01', '1970-02-01', return_nums=True)
        secs = [x for x in it]
        start = 5364662400
        self.assertAlmostEqual(secs[0], start)
        self.assertAlmostEqual(secs[1], start + 86400)
        self.assertAlmostEqual(secs[-1], start + 86400*30)

        it = dateutils.iter_dates('1970-01-01', '1970-02-01', return_nums=True,
            endpoint=True)
        secs = [x for x in it]
        self.assertAlmostEqual(secs[0], start)
        self.assertAlmostEqual(secs[-1], start + 86400*31)

    def test_with_cal_360(self):
        tu = cf_units.Unit('seconds since 1800-01-01', calendar='360_day')
        it = dateutils.iter_dates('1970-01-01', '1970-02-01', return_nums=True,
            time_units=tu)
        secs = [x for x in it]
        start = 5287680000
        self.assertAlmostEqual(secs[0], start)
        self.assertAlmostEqual(secs[1], start + 86400)
        self.assertAlmostEqual(secs[-1], start + 86400*29)

        it = dateutils.iter_dates('1970-01-01', '1970-02-01', return_nums=True,
            time_units=tu, endpoint=True)
        secs = [x for x in it]
        self.assertAlmostEqual(secs[0], start)
        self.assertAlmostEqual(secs[-1], start + 86400*30)

    def test_with_5day_step(self):
        it = dateutils.iter_dates('1970-02-01', '1970-03-01', step=5,
            return_nums=True, time_units='days since 1970-01-01')
        days = [x for x in it]
        self.assertAlmostEqual(days[0], 31.0)
        self.assertAlmostEqual(days[1], 36.0)
        self.assertAlmostEqual(days[-1], 56.0)

        it = dateutils.iter_dates('1970-02-01', '1970-03-01', step=5,
            return_nums=True, time_units='days since 1970-01-01', num_dtype=np.int32)
        days = [x for x in it]
        self.assertEqual(days[0], 31)
        self.assertEqual(days[1], 36)
        self.assertEqual(days[-1], 56)

    def test_with_5day_step_and_cal360(self):
        tu = cf_units.Unit('days since 1970-01-01', calendar='360_day')
        it = dateutils.iter_dates('1970-02-01', '1970-03-01', step=5,
            return_nums=True, time_units=tu)
        days = [x for x in it]
        self.assertAlmostEqual(days[0], 30.0)
        self.assertAlmostEqual(days[1], 35.0)
        self.assertAlmostEqual(days[-1], 55.0)

        it = dateutils.iter_dates('1970-02-01', '1970-03-01', step=5,
            return_nums=True, time_units=tu, endpoint=True)
        days = [x for x in it]
        self.assertAlmostEqual(days[0], 30.0)
        self.assertAlmostEqual(days[1], 35.0)
        self.assertAlmostEqual(days[-1], 60.0)

    def test_with_hourly_step(self):
        it = dateutils.iter_dates('1970-02-01', '1970-03-01', step=3600/86400.,
            return_nums=True, time_units='hours since 1970-01-01')
        hours = [x for x in it]
        self.assertAlmostEqual(hours[0], 744.0)
        self.assertAlmostEqual(hours[1], 745.0)
        self.assertAlmostEqual(hours[-1], 1415.0)

        it = dateutils.iter_dates('1970-02-01', '1970-03-01', step=3600/86400.,
            return_nums=True, time_units='hours since 1970-01-01', num_dtype=np.int32)
        hours = [x for x in it]
        self.assertEqual(hours[0], 744)
        self.assertEqual(hours[1], 745)
        self.assertEqual(hours[-1], 1415)

    def test_with_hourly_step_and_cal360(self):
        tu = cf_units.Unit('hours since 1970-01-01', calendar='360_day')
        it = dateutils.iter_dates('1970-02-01', '1970-03-01', step=3600/86400.,
            return_nums=True, time_units=tu)
        hours = [x for x in it]
        self.assertAlmostEqual(hours[0], 720.0)
        self.assertAlmostEqual(hours[1], 721.0)
        self.assertAlmostEqual(hours[-1], 1439.0)


class TestIterDateChunks(unittest.TestCase):
    """Test the dateutils.iter_date_chunks iterator."""

    def test_apm_stream(self):
        it = dateutils.iter_date_chunks('1970-01-01', '1971-01-01', 'apm',
            calendar='360_day')
        dtr = next(it)
        self.assertEqual(dtr.start, '1970-01-01T00:00:00')
        self.assertEqual(dtr.end, '1970-02-01T00:00:00')

    def test_aps_stream(self):
        it = dateutils.iter_date_chunks('1970-01-01', '1971-01-01', 'aps',
            calendar='360_day')
        dtr = next(it)
        self.assertEqual(dtr.start, '1969-12-01T00:00:00')
        self.assertEqual(dtr.end, '1970-03-01T00:00:00')

    def test_apy_stream(self):
        it = dateutils.iter_date_chunks('1970-01-01', '1975-01-01', 'apy',
            calendar='360_day')
        dtr = next(it)
        self.assertEqual(dtr.start, '1969-12-01T00:00:00')
        self.assertEqual(dtr.end, '1970-12-01T00:00:00')

    def test_invalid_calendar(self):
        it = dateutils.iter_date_chunks('1970-01-01', '1971-01-01', 'apm',
            calendar='360Day')
        # note that an exception isn't raised until the iterator is accessed
        self.assertRaises(ValueError, next, it)


if __name__ == '__main__':
    unittest.main()
