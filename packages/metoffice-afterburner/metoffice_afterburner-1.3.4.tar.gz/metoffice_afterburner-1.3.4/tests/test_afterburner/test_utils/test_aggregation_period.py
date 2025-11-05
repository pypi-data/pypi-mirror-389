# (C) British Crown Copyright 2016-2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Unit tests for the afterburner.utils.cubeutils.guess_aggregation_period() function
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import cf_units
import unittest

try:
    # python3
    from unittest import mock
except ImportError:
    # python2
    import mock

import iris
import iris.coords
import iris.tests.stock
import numpy as np

from afterburner.utils.cubeutils import guess_aggregation_period

MONTH_LENGTHS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


class TestWith360DayCalendar(unittest.TestCase):
    """Tests based on a 360-day calendar. Only the most common time periods are tested."""

    def setUp(self):
        self.cube = iris.tests.stock.simple_1d()
        cm = iris.coords.CellMethod('mean', ('time',), ('1 hour',))
        self.cube.add_cell_method(cm)
        self.tunits = cf_units.Unit('hours since 1999-12-10', calendar=cf_units.CALENDAR_360_DAY)

    @mock.patch('afterburner.utils.cubeutils.iris.cube.Cube.coord')
    def test_hourly_mean(self, cube_coord):
        tpts = np.arange(5.)
        tbnds = np.array([tpts-0.5, tpts+0.5]).T
        tcoord = iris.coords.DimCoord(tpts, standard_name='time', units=self.tunits)
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1h')
        tcoord.bounds = tbnds
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1h')

    @mock.patch('afterburner.utils.cubeutils.iris.cube.Cube.coord')
    def test_6hourly_mean(self, cube_coord):
        tpts = np.arange(5.) * 6
        tbnds = np.array([tpts-3, tpts+3]).T
        tcoord = iris.coords.DimCoord(tpts, standard_name='time', units=self.tunits)
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '6h')
        tcoord.bounds = tbnds
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '6h')

    @mock.patch('afterburner.utils.cubeutils.iris.cube.Cube.coord')
    def test_daily_mean(self, cube_coord):
        tpts = np.arange(5.) * 24
        tbnds = np.array([tpts-12, tpts+12]).T
        tcoord = iris.coords.DimCoord(tpts, standard_name='time', units=self.tunits)
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1d')
        tcoord.bounds = tbnds
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1d')

    @mock.patch('afterburner.utils.cubeutils.iris.cube.Cube.coord')
    def test_monthly_mean(self, cube_coord):
        tpts = np.arange(5.) * 720
        tbnds = np.array([tpts-360, tpts+360]).T
        tcoord = iris.coords.DimCoord(tpts, standard_name='time', units=self.tunits)
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1m')
        tcoord.bounds = tbnds
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1m')

    @mock.patch('afterburner.utils.cubeutils.iris.cube.Cube.coord')
    def test_seasonal_mean(self, cube_coord):
        tpts = np.arange(5.) * 2160
        tbnds = np.array([tpts-1080, tpts+1080]).T
        tcoord = iris.coords.DimCoord(tpts, standard_name='time', units=self.tunits)
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1s')
        tcoord.bounds = tbnds
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1s')

    @mock.patch('afterburner.utils.cubeutils.iris.cube.Cube.coord')
    def test_annual_mean(self, cube_coord):
        tpts = np.arange(5.) * 8640
        tbnds = np.array([tpts-4320, tpts+4320]).T
        tcoord = iris.coords.DimCoord(tpts, standard_name='time', units=self.tunits)
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1y')
        tcoord.bounds = tbnds
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1y')
        # similar tests using 'days since...'
        tpts = np.arange(5.) * 360
        tbnds = np.array([tpts-180, tpts+180]).T
        tunits = cf_units.Unit('days since 1999-12-10', calendar=cf_units.CALENDAR_360_DAY)
        tcoord = iris.coords.DimCoord(tpts, standard_name='time', units=tunits)
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1y')
        tcoord.bounds = tbnds
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1y')

    @mock.patch('afterburner.utils.cubeutils.iris.cube.Cube.coord')
    def test_decadal_mean(self, cube_coord):
        tpts = np.arange(5.) * 3600
        tbnds = np.array([tpts-1800, tpts+1800]).T
        tunits = cf_units.Unit('days since 1999-12-10', calendar=cf_units.CALENDAR_360_DAY)
        tcoord = iris.coords.DimCoord(tpts, standard_name='time', units=tunits)
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '10y')
        tcoord.bounds = tbnds
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '10y')

    @mock.patch('afterburner.utils.cubeutils.iris.cube.Cube.coord')
    def test_centennial_mean(self, cube_coord):
        tpts = np.arange(5.) * 36000
        tbnds = np.array([tpts-18000, tpts+18000]).T
        tunits = cf_units.Unit('days since 1999-12-10', calendar=cf_units.CALENDAR_360_DAY)
        tcoord = iris.coords.DimCoord(tpts, standard_name='time', units=tunits)
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '100y')
        tcoord.bounds = tbnds
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '100y')

    @mock.patch('afterburner.utils.cubeutils.iris.cube.Cube.coord')
    def test_no_mean(self, cube_coord):
        self.cube.cell_methods = None
        tpts = np.arange(5.)
        tcoord = iris.coords.DimCoord(tpts, standard_name='time', units=self.tunits)
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), None)

    @mock.patch('afterburner.utils.cubeutils.iris.cube.Cube.coord')
    def test_scalar_coord(self, cube_coord):
        tpts = np.array([12])
        tbnds = np.array([[0,24]])
        tcoord = iris.coords.DimCoord(tpts, standard_name='time', units=self.tunits)
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), None)
        tcoord.bounds = tbnds
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1d')


class TestWith365DayCalendar(unittest.TestCase):
    """Tests based on a 365-day calendar. Only the most common time periods are tested."""

    def setUp(self):
        self.cube = iris.tests.stock.simple_1d()
        cm = iris.coords.CellMethod('mean', ('time',), ('1 hour',))
        self.cube.add_cell_method(cm)
        self.tunits = cf_units.Unit('hours since 1999-12-10', calendar=cf_units.CALENDAR_365_DAY)

    @mock.patch('afterburner.utils.cubeutils.iris.cube.Cube.coord')
    def test_monthly_mean(self, cube_coord):
        monlens = np.roll(np.array(MONTH_LENGTHS), 1)  # month lengths from Dec-Nov.
        tbnds = np.zeros([12,2])
        tbnds[:,1] = np.cumsum(monlens * 24)
        tbnds[1:12,0] = tbnds[0:11,1]
        tpts = tbnds[:,0] + (monlens * 12)
        tcoord = iris.coords.DimCoord(tpts, standard_name='time', units=self.tunits)
        tcoord.bounds = tbnds
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1m')

    @mock.patch('afterburner.utils.cubeutils.iris.cube.Cube.coord')
    def test_seasonal_mean(self, cube_coord):
        monlens = np.roll(np.array(MONTH_LENGTHS), 1)  # month lengths from Dec-Nov.
        sealens = monlens.reshape(4,3).sum(axis=1)     # climate season lengths
        tbnds = np.zeros([4,2])
        tbnds[:,1] = np.cumsum(sealens * 24)
        tbnds[1:4,0] = tbnds[0:3,1]
        tpts = (tbnds[:,0] + tbnds[:,1]) * 0.5
        tcoord = iris.coords.DimCoord(tpts, standard_name='time', units=self.tunits)
        tcoord.bounds = tbnds
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1s')

    @mock.patch('afterburner.utils.cubeutils.iris.cube.Cube.coord')
    def test_annual_mean(self, cube_coord):
        tpts = np.arange(5.) * 365
        tbnds = np.array([tpts-182, tpts+183]).T
        tunits = cf_units.Unit('days since 1999-12-10', calendar=cf_units.CALENDAR_365_DAY)
        tcoord = iris.coords.DimCoord(tpts, standard_name='time', units=tunits)
        tcoord.bounds = tbnds
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '1y')

    @mock.patch('afterburner.utils.cubeutils.iris.cube.Cube.coord')
    def test_decadal_mean(self, cube_coord):
        tpts = np.arange(5.) * 3650
        tbnds = np.array([tpts-1825, tpts+1825]).T
        tunits = cf_units.Unit('days since 1999-12-10', calendar=cf_units.CALENDAR_365_DAY)
        tcoord = iris.coords.DimCoord(tpts, standard_name='time', units=tunits)
        tcoord.bounds = tbnds
        cube_coord.return_value = tcoord
        self.assertEqual(guess_aggregation_period(self.cube), '10y')


if __name__ == '__main__':
    unittest.main()
