# (C) British Crown Copyright 2016-2025, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.metavar module.
"""
from __future__ import absolute_import, division, print_function

import unittest

import cf_units
import iris
import iris.cube
import numpy as np
import pytest
from afterburner.coords import CoordRange
from afterburner.exceptions import UnknownModelNameError
from afterburner.metavar import (CiceMetaVariable, MetaVariable,
                                 NemoMetaVariable, UmMetaVariable,
                                 _normalize_version_string)
from afterburner.utils.dateutils import DateTimeRange
from packaging.version import Version
from six.moves import filter, input, map, range, zip


class TestFactoryMethod(unittest.TestCase):
    """Test the MetaVariable.create_variable method."""

    def test_create_um_var(self):
        var = MetaVariable.create_variable('UM', '10', 'mi-abcde', stream_id='apy',
            stash_code='m01s00i024')
        self.assertEqual(var.model_name, 'UM')
        self.assertEqual(var.model_vn, '10.0.0')

    def test_create_nemo_var(self):
        var = MetaVariable.create_variable('NEMO', '10.1', 'mi-abcde', stream_id='ony',
            var_name='votemper')
        self.assertEqual(var.model_name, 'NEMO')
        self.assertEqual(var.model_vn, '10.1.0')

    def test_create_unknown_model(self):
        self.assertRaises(UnknownModelNameError, MetaVariable.create_variable,
            'MU', '0', 'mi-abcde')


class TestUmMetaVariable(unittest.TestCase):
    """Test the UmMetaVariable class."""

    def test_minimal_var_def(self):
        var = UmMetaVariable('10', 'mi-abcde', stream_id='apy', stash_code='m01s00i024')
        self.assertEqual(var.model_name, 'UM')
        self.assertEqual(var.model_vn, '10.0.0')
        var = UmMetaVariable('10.1', 'mi-abcde', stream_id='apy', stash_code='m01s00i024')
        self.assertEqual(var.model_vn, '10.1.0')

    def test_maximal_var_def(self):
        var = UmMetaVariable('10', 'mi-abcde', stream_id='apy', stash_code='m01s00i024',
            lbproc=128, lbtim=122, time_range=('1970-01-01T09:00:00', '1971-01-01T09:00:00'),
            calendar='360_day', newmode=True)
        self.assertEqual(var.start_time.year, 1970)
        self.assertEqual(var.end_time.year, 1971)
        self.assertEqual(var.calendar, cf_units.CALENDAR_360_DAY)

    def test_no_stash_code(self):
        self.assertRaises(ValueError, UmMetaVariable, '10', 'mi-abcde', stream_id='apy')

    def test_bad_stash_code(self):
        self.assertRaises(ValueError, UmMetaVariable, '10', 'mi-abcde', stream_id='apy',
            stash_code='x01y00z024')

    def test_stash_code_from_var_name(self):
        var = UmMetaVariable('10', 'mi-abcde', stream_id='apy', var_name='m01s00i024')
        self.assertEqual(var.stash_code, 'm01s00i024')
        self.assertEqual(var.var_name, 'm01s00i024')
        # and now using an invalid stash code
        self.assertRaises(ValueError, UmMetaVariable, '10', 'mi-abcde', stream_id='apy',
            var_name='x01y00z024')

    def test_name_property(self):
        var = UmMetaVariable('10', 'mi-abcde', stream_id='apy', stash_code='m01s00i024')
        self.assertEqual(var.name, 'm01s00i024')

    def test_slug_property(self):
        var = UmMetaVariable('10', 'mi-abcde', stream_id='apy', stash_code='m01s00i024')
        self.assertEqual(var.slug, 'm01s00i024')

    def test_calendar_from_lbtim(self):
        var = UmMetaVariable('10', 'mi-abcde', stream_id='apy', stash_code='m01s00i024',
            lbtim=121)
        self.assertEqual(var.calendar, cf_units.CALENDAR_GREGORIAN)
        var = UmMetaVariable('10', 'mi-abcde', stream_id='apy', stash_code='m01s00i024',
            lbtim=122)
        self.assertEqual(var.calendar, cf_units.CALENDAR_360_DAY)
        var = UmMetaVariable('10', 'mi-abcde', stream_id='apy', stash_code='m01s00i024',
            lbtim=123)
        self.assertEqual(var.calendar, None)
        var = UmMetaVariable('10', 'mi-abcde', stream_id='apy', stash_code='m01s00i024',
            lbtim=124)
        self.assertEqual(var.calendar, cf_units.CALENDAR_365_DAY)

    def test_bad_calendar(self):
        self.assertRaises(ValueError, UmMetaVariable, '10', 'mi-abcde', stream_id='apy',
            stash_code='m01s00i024', calendar='400_day')

    def test_inconsistent_calendars(self):
        self.assertRaises(ValueError, UmMetaVariable, '10', 'mi-abcde', stream_id='apy',
            stash_code='m01s00i024', lbtim=121, calendar='360_day')
        self.assertRaises(ValueError, UmMetaVariable, '10', 'mi-abcde', stream_id='apy',
            stash_code='m01s00i024', lbtim=122, calendar='gregorian')
        self.assertRaises(ValueError, UmMetaVariable, '10', 'mi-abcde', stream_id='apy',
            stash_code='m01s00i024', lbtim=124, calendar='360_day')

    def test_gregorian_calendar_fix(self):
        """Tests that the warning will be produced if the calendars are gregorian and
        standard."""
        if Version(iris.__version__) < Version("3.3"):
            pytest.skip("Workaround unneeded for this version of iris.")
        UM_model_test = UmMetaVariable('10', 'mi-abcde', stream_id='apy',
            stash_code='m01s00i024', calendar='gregorian')
        # Create iris cube with standard calendar
        gregorian_cube = iris.cube.Cube(np.zeros((2,2)))
        gregorian_cube.add_dim_coord(iris.coords.DimCoord(np.arange(2), "time",
                                                          units="hours since epoch"),0)
        calendar = gregorian_cube.coord('time').units.calendar
        warning_message = "Calendars gregorian and standard assumed to be the same."
        with self.assertWarnsRegex(UserWarning, warning_message):
            UM_model_test._iris_calendar_compatibility_check(calendar)

    def test_date_time_range(self):
        dtr = DateTimeRange('1970-01-01T06', '1971-06-01T18')
        var = UmMetaVariable('10', 'mi-abcde', stream_id='apy', stash_code='m01s00i024',
            time_range=dtr, calendar='360_day')
        self.assertEqual(var.start_time.year, 1970)
        self.assertEqual(var.start_time.month, 1)
        self.assertEqual(var.start_time.day, 1)
        self.assertEqual(var.start_time.hour, 6)
        self.assertEqual(var.end_time.year, 1971)
        self.assertEqual(var.end_time.month, 6)
        self.assertEqual(var.end_time.day, 1)
        self.assertEqual(var.end_time.hour, 18)

    def test_str_method(self):
        var = UmMetaVariable('10', 'mi-abcde', stream_id='apy', stash_code='m01s00i024')
        self.assertEqual(str(var), 'UM v10.0.0, mi-abcde/apy, m01s00i024:lbproc=None:lbtim=None')

        var.realization_id = 'r1i2p3'
        var.lbproc = 128
        var.lbtim = 122
        self.assertEqual(str(var), 'UM v10.0.0, mi-abcde/r1i2p3/apy, m01s00i024:lbproc=128:lbtim=122')

        var.time_range = ('1970-01-01T09:00:00', '1971-01-01T09:00:00')
        self.assertEqual(str(var), 'UM v10.0.0, mi-abcde/r1i2p3/apy, m01s00i024:lbproc=128:lbtim=122,'
            ' from 1970-01-01T09:00:00 to 1971-01-01T09:00:00')


class TestNemoMetaVariable(unittest.TestCase):
    """Test the NemoMetaVariable class."""

    def test_minimal_var_def(self):
        var = NemoMetaVariable('10', 'mi-abcde', stream_id='ony', var_name='votemper')
        self.assertEqual(var.model_name, 'NEMO')
        self.assertEqual(var.model_vn, '10.0.0')
        var = NemoMetaVariable('10.1', 'mi-abcde', stream_id='ony', var_name='votemper')
        self.assertEqual(var.model_vn, '10.1.0')

    def test_maximal_var_def(self):
        var = NemoMetaVariable('10', 'mi-abcde', stream_id='ony', var_name='votemper',
            long_name='Sea Water Temperature', standard_name='sea_water_temperature',
            time_range=('1970-01-01T09:00:00', '1971-01-01T09:00:00'), calendar='360_day',
            grid_type='W', aux_var_profile='default')
        self.assertEqual(var.start_time.year, 1970)
        self.assertEqual(var.end_time.year, 1971)
        self.assertEqual(var.calendar, cf_units.CALENDAR_360_DAY)
        self.assertEqual(var.aux_var_names, NemoMetaVariable.AUX_VAR_PROFILES['default'])

    def test_no_var_names(self):
        self.assertRaises(ValueError, NemoMetaVariable, '10', 'mi-abcde', stream_id='ony')

    def test_name_property(self):
        var = NemoMetaVariable('10', 'mi-abcde', stream_id='ony', var_name='votemper',
            long_name='Sea Temperature', standard_name='sea_temperature')
        self.assertEqual(var.name, 'sea_temperature')
        var = NemoMetaVariable('10', 'mi-abcde', stream_id='ony', var_name='votemper',
            long_name='Sea Temperature')
        self.assertEqual(var.name, 'Sea Temperature')
        var = NemoMetaVariable('10', 'mi-abcde', stream_id='ony', var_name='votemper')
        self.assertEqual(var.name, 'votemper')

    def test_slug_property(self):
        var = NemoMetaVariable('10', 'mi-abcde', stream_id='ony', var_name='votemper',
            long_name='Sea Temperature', standard_name='sea_temperature')
        self.assertEqual(var.slug, 'votemper')
        var = NemoMetaVariable('10', 'mi-abcde', stream_id='ony', var_name='votemper',
            long_name='Sea Temperature')
        self.assertEqual(var.slug, 'votemper')
        var = NemoMetaVariable('10', 'mi-abcde', stream_id='ony', var_name='votemper')
        self.assertEqual(var.slug, 'votemper')

    def test_bad_calendar(self):
        self.assertRaises(ValueError, NemoMetaVariable, '10', 'mi-abcde', stream_id='ony',
            var_name='votemper', calendar='400_day')

    def test_gregorian_calendar_fix(self):
        """Tests that the warning will be produced if the calendars are gregorian and
        standard."""
        if Version(iris.__version__) < Version("3.3"):
            pytest.skip("Workaround unneeded for this version of iris.")
        Nemo_model_test = NemoMetaVariable('10', 'mi-abcde', stream_id='ony', var_name='votemper',
                                          calendar='gregorian')
        # Create iris cube with standard calendar
        gregorian_cube = iris.cube.Cube(np.zeros((2,2)))
        gregorian_cube.add_dim_coord(iris.coords.DimCoord(np.arange(2), "time", units="hours since epoch"),0)
        calendar = gregorian_cube.coord('time').units.calendar
        warning_message = "Calendars gregorian and standard assumed to be the same."
        with self.assertWarnsRegex(UserWarning, warning_message):
            Nemo_model_test._iris_calendar_compatibility_check(calendar)

    def test_bad_grid_type(self):
        self.assertRaises(ValueError, NemoMetaVariable, '10', 'mi-abcde', stream_id='ony',
            var_name='votemper', grid_type='Q')

    def test_aux_var_precedence(self):
        var = NemoMetaVariable('10', 'mi-abcde', stream_id='ony', var_name='votemper',
            aux_var_names=['nav_lon', 'nav_lat'], aux_var_profile='default')
        self.assertEqual(var.aux_var_names, ['nav_lon', 'nav_lat'])

    def test_date_time_range(self):
        dtr = DateTimeRange('1970-01-01T06', '1971-06-01T18')
        var = NemoMetaVariable('10', 'mi-abcde', stream_id='ony', var_name='votemper',
            time_range=dtr, calendar='360_day')
        self.assertEqual(var.start_time.year, 1970)
        self.assertEqual(var.start_time.month, 1)
        self.assertEqual(var.start_time.day, 1)
        self.assertEqual(var.start_time.hour, 6)
        self.assertEqual(var.end_time.year, 1971)
        self.assertEqual(var.end_time.month, 6)
        self.assertEqual(var.end_time.day, 1)
        self.assertEqual(var.end_time.hour, 18)

    def test_str_method(self):
        var = NemoMetaVariable('10', 'mi-abcde', stream_id='ony', var_name='votemper')
        self.assertEqual(str(var), 'NEMO v10.0.0, mi-abcde/ony, votemper on T-grid')

        var.realization_id = 'r1i2p3'
        var.grid_type = 'W'
        self.assertEqual(str(var), 'NEMO v10.0.0, mi-abcde/r1i2p3/ony, votemper on W-grid')

        var.time_range = ('1970-01-01T09:00:00', '1971-01-01T09:00:00')
        self.assertEqual(str(var), 'NEMO v10.0.0, mi-abcde/r1i2p3/ony, votemper on W-grid,'
            ' from 1970-01-01T09:00:00 to 1971-01-01T09:00:00')


class TestCiceMetaVariable(unittest.TestCase):
    """Test the CiceMetaVariable class."""

    def test_minimal_var_def(self):
        var = CiceMetaVariable('10', 'mi-abcde', stream_id='iny', var_name='snoice')
        self.assertEqual(var.model_name, 'CICE')
        self.assertEqual(var.model_vn, '10.0.0')
        var = CiceMetaVariable('10.1', 'mi-abcde', stream_id='iny', var_name='snoice')
        self.assertEqual(var.model_vn, '10.1.0')

    def test_maximal_var_def(self):
        var = CiceMetaVariable('10', 'mi-abcde', stream_id='iny', var_name='sst',
            long_name='Sea Surface Temperature', standard_name='sea_surface_temperature',
            time_range=('1970-01-01T09:00:00', '1971-01-01T09:00:00'), calendar='360_day',
            grid_type='T', aux_var_profile='default')
        self.assertEqual(var.start_time.year, 1970)
        self.assertEqual(var.end_time.year, 1971)
        self.assertEqual(var.calendar, cf_units.CALENDAR_360_DAY)
        self.assertEqual(var.aux_var_names, CiceMetaVariable.AUX_VAR_PROFILES['default'])

    def test_no_var_names(self):
        self.assertRaises(ValueError, CiceMetaVariable, '10', 'mi-abcde', stream_id='iny')

    def test_name_property(self):
        var = CiceMetaVariable('10', 'mi-abcde', stream_id='iny', var_name='sst',
            long_name='Sea Surface Temperature', standard_name='sea_surface_temperature')
        self.assertEqual(var.name, 'sea_surface_temperature')
        var = CiceMetaVariable('10', 'mi-abcde', stream_id='iny', var_name='sst',
            long_name='Sea Surface Temperature')
        self.assertEqual(var.name, 'Sea Surface Temperature')
        var = CiceMetaVariable('10', 'mi-abcde', stream_id='iny', var_name='sst')
        self.assertEqual(var.name, 'sst')

    def test_slug_property(self):
        var = CiceMetaVariable('10', 'mi-abcde', stream_id='iny', var_name='sst',
            long_name='Sea Surface Temperature', standard_name='sea_surface_temperature')
        self.assertEqual(var.slug, 'sst')
        var = CiceMetaVariable('10', 'mi-abcde', stream_id='iny', var_name='sst',
            long_name='Sea Surface Temperature')
        self.assertEqual(var.slug, 'sst')
        var = CiceMetaVariable('10', 'mi-abcde', stream_id='iny', var_name='sst')
        self.assertEqual(var.slug, 'sst')

    def test_bad_calendar(self):
        self.assertRaises(ValueError, CiceMetaVariable, '10', 'mi-abcde', stream_id='iny',
            var_name='snoice', calendar='400_day')

    def test_gregorian_calendar_fix(self):
        """Tests that the warning will be produced if the calendars are gregorian and
        standard."""
        if Version(iris.__version__) < Version("3.3"):
            pytest.skip("Workaround unneeded for this version of iris.")
        Cice_model_test = CiceMetaVariable('10', 'mi-abcde', stream_id='iny',
            var_name='sst', long_name='Sea Surface Temperature',
            standard_name='sea_surface_temperature', calendar='gregorian')
        # Create iris cube with standard calendar
        gregorian_cube = iris.cube.Cube(np.zeros((2,2)))
        gregorian_cube.add_dim_coord(iris.coords.DimCoord(np.arange(2), "time", units="hours since epoch"),0)
        calendar = gregorian_cube.coord('time').units.calendar
        warning_message = "Calendars gregorian and standard assumed to be the same."
        with self.assertWarnsRegex(UserWarning, warning_message):
            Cice_model_test._iris_calendar_compatibility_check(calendar)

    def test_bad_grid_type(self):
        self.assertRaises(ValueError, CiceMetaVariable, '10', 'mi-abcde', stream_id='iny',
            var_name='snoice', grid_type='Q')

    def test_aux_var_precedence(self):
        var = CiceMetaVariable('10', 'mi-abcde', stream_id='iny', var_name='snoice',
            aux_var_names=['TLAT', 'TLON'], aux_var_profile='default')
        self.assertEqual(var.aux_var_names, ['TLAT', 'TLON'])

    def test_date_time_range(self):
        dtr = DateTimeRange('1970-01-01T06', '1971-06-01T18')
        var = CiceMetaVariable('10', 'mi-abcde', stream_id='iny', var_name='snoice',
            time_range=dtr, calendar='360_day')
        self.assertEqual(var.start_time.year, 1970)
        self.assertEqual(var.start_time.month, 1)
        self.assertEqual(var.start_time.day, 1)
        self.assertEqual(var.start_time.hour, 6)
        self.assertEqual(var.end_time.year, 1971)
        self.assertEqual(var.end_time.month, 6)
        self.assertEqual(var.end_time.day, 1)
        self.assertEqual(var.end_time.hour, 18)

    def test_str_method(self):
        var = CiceMetaVariable('10', 'mi-abcde', stream_id='iny', var_name='snoice')
        self.assertEqual(str(var), 'CICE v10.0.0, mi-abcde/iny, snoice on T-grid')

        var.realization_id = 'r1i2p3'
        var.grid_type = 'U'
        self.assertEqual(str(var), 'CICE v10.0.0, mi-abcde/r1i2p3/iny, snoice on U-grid')

        var.time_range = ('1970-01-01T09:00:00', '1971-01-01T09:00:00')
        self.assertEqual(str(var), 'CICE v10.0.0, mi-abcde/r1i2p3/iny, snoice on U-grid,'
            ' from 1970-01-01T09:00:00 to 1971-01-01T09:00:00')


class TestDecodeTimeRange(unittest.TestCase):
    """Test the MetaVariable.decode_time_range method."""

    def test_valid_dates(self):
        var = UmMetaVariable('10', 'mi-abcde', stash_code='m01s00i024',
            time_range=('1970-01-01T09:00:00', '1971-01-01T09:00:00'),
            calendar='360_day')
        var.decode_time_range()

        test_atts = ['year', 'month', 'day', 'hour', 'minute', 'second']
        actual = [getattr(var.start_time, att) for att in test_atts]
        expect = [1970, 1, 1, 9, 0, 0]
        self.assertEqual(actual, expect)

        actual = [getattr(var.end_time, att) for att in test_atts]
        expect = [1971, 1, 1, 9, 0, 0]
        self.assertEqual(actual, expect)

        var.time_range = ('1970-01-01', '1971-01-01')
        var.decode_time_range()
        actual = [getattr(var.start_time, att) for att in test_atts]
        expect = [1970, 1, 1, 0, 0, 0]
        self.assertEqual(actual, expect)

        actual = [getattr(var.end_time, att) for att in test_atts]
        expect = [1971, 1, 1, 0, 0, 0]
        self.assertEqual(actual, expect)

        var.time_range = ('0:30:0', '23:30:00')
        var.decode_time_range()
        actual = [getattr(var.start_time, att) for att in test_atts]
        expect = [0, 0, 0, 0, 30, 0]
        self.assertEqual(actual, expect)

        actual = [getattr(var.end_time, att) for att in test_atts]
        expect = [0, 0, 0, 23, 30, 0]
        self.assertEqual(actual, expect)

    def test_invalid_dates(self):
        self.assertRaises(ValueError, UmMetaVariable, '10', 'mi-abcde',
            stash_code='m01s00i024',
            time_range=('19700101090000', '19710101090000'))
        self.assertRaises(ValueError, UmMetaVariable, '10', 'mi-abcde',
            stash_code='m01s00i024',
            time_range=('19700101', '19710101'))


class TestAxisRangeAttributes(unittest.TestCase):
    """Test the axis range attributes: xaxis_range, yaxis_range, zaxis_range."""

    def test_default_values(self):
        var1 = UmMetaVariable('10', 'mi-abcde', stash_code='m01s00i024')
        var2 = NemoMetaVariable('10', 'mi-abcde', var_name='votemper')
        for var in [var1, var2]:
            self.assertEqual(var.xaxis_range, None)
            self.assertEqual(var.yaxis_range, None)
            self.assertEqual(var.zaxis_range, None)

    def test_init_values(self):
        var = UmMetaVariable('10', 'mi-abcde', stash_code='m01s00i024',
            xaxis_range=CoordRange(60.0),
            yaxis_range=CoordRange([-45.0, 45.0], closed=True),
            zaxis_range=CoordRange([1, 2, 3], dtype='f4'))

        self.assertTrue(var.xaxis_range.contains(60))
        self.assertTrue(var.yaxis_range.is_interval())
        self.assertTrue(var.zaxis_range.contains(1))
        self.assertFalse(var.zaxis_range.contains(2.5))

    def test_post_init(self):
        var = NemoMetaVariable('10', 'mi-abcde', var_name='votemper')
        self.assertRaises(ValueError, setattr, var, 'zaxis_range', [1, 2, 3])
        var.zaxis_range = CoordRange((1, 3, 5, 7, 9))
        self.assertFalse(var.zaxis_range.is_interval())
        self.assertTrue(var.zaxis_range.contains(5))
        self.assertFalse(var.zaxis_range.contains(8))
        var.zaxis_range = None
        self.assertEqual(var.zaxis_range, None)


class TestNormalizeVnString(unittest.TestCase):
    """Test the _normalize_version_string function."""

    def test_normalize_vn_string(self):
        self.assertEqual(_normalize_version_string('0'), '0.0.0')
        self.assertEqual(_normalize_version_string('1'), '1.0.0')
        self.assertEqual(_normalize_version_string('1.2'), '1.2.0')
        self.assertEqual(_normalize_version_string('1.2.3'), '1.2.3')
        self.assertEqual(_normalize_version_string('1.2.3.4'), '1.2.3')


if __name__ == '__main__':
    unittest.main()
