# (C) British Crown Copyright 2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Unit tests for the afterburner.stats.temporal module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import logging
import unittest
import numpy as np
import numpy.testing as npt
import cf_units as cfu
try:
    import cftime as cft
except ImportError:
    import netcdftime as cft

import iris
import iris.coords
import iris.coord_categorisation as coord_cat

from afterburner.stats import temporal
from afterburner.utils import cubeutils

_logger = logging.getLogger('afterburner')
_log_level = _logger.level


def setUpModule(self):
    # disable logging
    _logger.level = 100


def tearDownModule(self):
    # enable logging
    _logger.level = _log_level


class TestMonthlyStats(unittest.TestCase):
    """Test the monthly statistic generation functions."""

    def setUp(self):
        ntimes = 90
        data = np.random.uniform(low=0.0, high=50.0, size=ntimes)
        time = _create_apa_time_coord(npoints=ntimes)
        cube = iris.cube.Cube(data, standard_name='air_temperature', units='degc')
        cube.add_dim_coord(time, 0)
        self.cube = cube

    def test_monthly_mean(self):
        aggregator = iris.analysis.MEAN
        result = temporal.calc_time_stat(self.cube, aggregator, temporal.TP_MONTH)
        self.assertTrue(result.cell_methods[0].method == 'mean')
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('month_number' in coord_names)
        self.assertTrue('year' in coord_names)
        npt.assert_array_equal(result.coord('month_number').points, [12, 1, 2])

        result = temporal.calc_monthly_stat(self.cube, aggregator)
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('month_number' in coord_names)
        self.assertTrue('year' in coord_names)
        npt.assert_array_equal(result.coord('month_number').points, [12, 1, 2])

    def test_monthly_std(self):
        aggregator = iris.analysis.STD_DEV
        result = temporal.calc_time_stat(self.cube, aggregator, temporal.TP_MONTH)
        self.assertTrue(result.cell_methods[0].method == 'standard_deviation')
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('month_number' in coord_names)
        self.assertTrue('year' in coord_names)
        npt.assert_array_equal(result.coord('month_number').points, [12, 1, 2])

        result = temporal.calc_monthly_stat(self.cube, aggregator, agg_opts={'ddof': 0})
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('month_number' in coord_names)
        self.assertTrue('year' in coord_names)
        npt.assert_array_equal(result.coord('month_number').points, [12, 1, 2])


class TestSeasonalStats(unittest.TestCase):
    """Test the seasonal statistic generation functions."""

    def setUp(self):
        ntimes = 24
        data = np.random.uniform(low=0.0, high=50.0, size=ntimes)
        time = _create_apm_time_coord(npoints=ntimes)
        cube = iris.cube.Cube(data, standard_name='air_temperature', units='degc')
        cube.add_dim_coord(time, 0)
        self.cube = cube

    def test_custom_seasonal_mean(self):
        aggregator = iris.analysis.MEAN
        result = temporal.calc_time_stat(self.cube, aggregator, temporal.TP_SEASON,
            seasons=('jfm', 'amj', 'jas', 'ond'))
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('season' in coord_names)
        self.assertTrue('season_year' in coord_names)
        self.assertEqual(len(result.coord('time').points), 9)

        result = temporal.calc_seasonal_stat(self.cube, aggregator,
            seasons=('jfm', 'amj', 'jas', 'ond'))
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('season' in coord_names)
        self.assertTrue('season_year' in coord_names)
        self.assertEqual(len(result.coord('time').points), 9)

    def test_model_seasonal_mean(self):
        aggregator = iris.analysis.MEAN
        result = temporal.calc_time_stat(self.cube, aggregator, temporal.TP_MODEL_SEASON)
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('season' in coord_names)
        self.assertTrue('season_year' in coord_names)
        self.assertEqual(len(result.coord('time').points), 8)

        result = temporal.calc_seasonal_stat(self.cube, aggregator)
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('season' in coord_names)
        self.assertTrue('season_year' in coord_names)
        self.assertEqual(len(result.coord('time').points), 8)


class TestAnnualStats(unittest.TestCase):
    """Test the annual statistic generation functions."""

    def setUp(self):
        ntimes = 24
        data = np.random.uniform(low=0.0, high=50.0, size=ntimes)
        time = _create_apm_time_coord(npoints=ntimes)
        cube = iris.cube.Cube(data, standard_name='air_temperature', units='degc')
        cube.add_dim_coord(time, 0)
        self.cube = cube

    def test_annual_mean(self):
        aggregator = iris.analysis.MEAN
        result = temporal.calc_time_stat(self.cube, aggregator, temporal.TP_YEAR)
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('year' in coord_names)
        npt.assert_array_equal(result.coord('year').points, [1999, 2000, 2001])

        result = temporal.calc_annual_stat(self.cube, aggregator)
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('year' in coord_names)
        npt.assert_array_equal(result.coord('year').points, [1999, 2000, 2001])

    def test_model_annual_mean(self):
        aggregator = iris.analysis.MEAN
        result = temporal.calc_time_stat(self.cube, aggregator, temporal.TP_MODEL_YEAR)
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('model_year' in coord_names)
        npt.assert_array_equal(result.coord('model_year').points, [2000, 2001])

        result = temporal.calc_model_annual_stat(self.cube, aggregator)
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('model_year' in coord_names)
        npt.assert_array_equal(result.coord('model_year').points, [2000, 2001])


class TestDecadalStats(unittest.TestCase):
    """Test the decadal statistic generation functions."""

    def setUp(self):
        ntimes = 20
        data = np.random.uniform(low=0.0, high=50.0, size=ntimes)
        time = _create_apy_time_coord(npoints=ntimes)
        cube = iris.cube.Cube(data, standard_name='air_temperature', units='degc')
        cube.add_dim_coord(time, 0)
        self.cube = cube

    def test_decadal_mean(self):
        aggregator = iris.analysis.MEAN
        result = temporal.calc_time_stat(self.cube, aggregator, temporal.TP_DECADE)
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('decade' in coord_names)
        npt.assert_array_equal(result.coord('decade').points, [2005, 2015])

        result = temporal.calc_decadal_stat(self.cube, aggregator)
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('decade' in coord_names)
        npt.assert_array_equal(result.coord('decade').points, [2005, 2015])

    def test_model_decadal_mean(self):
        aggregator = iris.analysis.MEAN
        result = temporal.calc_time_stat(self.cube, aggregator, temporal.TP_MODEL_DECADE)
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('model_decade' in coord_names)
        npt.assert_array_equal(result.coord('model_decade').points, [20041201, 20141201])

        result = temporal.calc_model_decadal_stat(self.cube, aggregator)
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('model_decade' in coord_names)
        npt.assert_array_equal(result.coord('model_decade').points, [20041201, 20141201])

    def test_multi_year_decadal_mean(self):
        aggregator = iris.analysis.MEAN
        result = temporal.calc_model_decadal_stat(self.cube, aggregator)
        coord1 = self.cube.coord('model_decade')

        cubeutils.add_multi_year_aux_coord(self.cube, 'time', 10, name='ten_years')
        coord_names = [c.name() for c in self.cube.coords()]
        self.assertTrue('ten_years' in coord_names)
        coord2 = self.cube.coord('ten_years')
        
        npt.assert_array_equal(coord1.points, coord2.points)


class TestMonthlyClim(unittest.TestCase):
    """Test the monthly climatology generation functions."""

    def setUp(self):
        ntimes = 36
        data = np.random.uniform(low=0.0, high=50.0, size=ntimes)
        time = _create_apm_time_coord(npoints=ntimes)
        cube = iris.cube.Cube(data, standard_name='air_temperature', units='degc')
        cube.add_dim_coord(time, 0)
        self.cube = cube

    def test_monthly_lta(self):
        aggregator = iris.analysis.MEAN
        result = temporal.calc_monthly_clim(self.cube, aggregator)
        self.assertTrue(result.cell_methods[0].method == 'mean')
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('month_number' in coord_names)
        self.assertEqual(len(result.coord('time').points), 12)
        npt.assert_array_equal(result.coord('month_number').points,
            np.roll(np.arange(1, 13), 1))

    def test_monthly_std(self):
        aggregator = iris.analysis.STD_DEV
        result = temporal.calc_monthly_clim(self.cube, aggregator)
        self.assertTrue(result.cell_methods[0].method == 'standard_deviation')
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('month_number' in coord_names)
        self.assertEqual(len(result.coord('time').points), 12)
        npt.assert_array_equal(result.coord('month_number').points,
            np.roll(np.arange(1, 13), 1))


class TestSeasonalClim(unittest.TestCase):
    """Test the seasonal climatology generation functions."""

    def setUp(self):
        ntimes = 36
        data = np.random.uniform(low=0.0, high=50.0, size=ntimes)
        time = _create_apm_time_coord(npoints=ntimes)
        cube = iris.cube.Cube(data, standard_name='air_temperature', units='degc')
        cube.add_dim_coord(time, 0)
        self.cube = cube

    def test_seasonal_lta(self):
        aggregator = iris.analysis.MEAN
        result = temporal.calc_seasonal_clim(self.cube, aggregator)
        self.assertTrue(result.cell_methods[0].method == 'mean')
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('season' in coord_names)
        self.assertEqual(len(result.coord('time').points), 4)
        self.assertEqual(result.coord('season').points[0], 'djf')

    def test_seasonal_var(self):
        aggregator = iris.analysis.VARIANCE
        seasons = ('jfm', 'amj', 'jas', 'ond')   # use custom seasons
        result = temporal.calc_seasonal_clim(self.cube, aggregator, seasons=seasons)
        self.assertTrue(result.cell_methods[0].method == 'variance')
        coord_names = [c.name() for c in result.coords()]
        self.assertTrue('season' in coord_names)
        self.assertEqual(len(result.coord('time').points), 4)
        self.assertEqual(result.coord('season').points[0], 'ond')


class TestCalcTimeStatFunction(unittest.TestCase):
    """Test the calc_time_stat() utility function."""

    def setUp(self):
        ntimes = 24
        data = np.random.uniform(low=0.0, high=50.0, size=ntimes)
        time = _create_apm_time_coord(npoints=ntimes)
        cube = iris.cube.Cube(data, standard_name='air_temperature', units='degc')
        cube.add_dim_coord(time, 0)
        self.cube = cube

    def test_call_with_cube(self):
        aggregator = iris.analysis.MEAN
        result = temporal.calc_time_stat(self.cube, aggregator, temporal.TP_YEAR)
        self.assertTrue(result, isinstance(result, iris.cube.Cube))
        self.assertTrue('year' in [c.name() for c in result.coords(dim_coords=False)])

    def test_call_with_cubelist(self):
        aggregator = iris.analysis.MEAN
        cubelist = iris.cube.CubeList([self.cube])
        result = temporal.calc_time_stat(cubelist, aggregator, temporal.TP_YEAR)
        self.assertTrue(result, isinstance(result, iris.cube.CubeList))
        self.assertEqual(len(result), 1)

    def test_append_to_cubelist_keyword(self):
        aggregator = iris.analysis.MEAN
        cubelist = iris.cube.CubeList([self.cube])
        result = temporal.calc_time_stat(cubelist, aggregator, temporal.TP_YEAR,
            append_to_cubelist=True)
        self.assertTrue(result, isinstance(result, iris.cube.CubeList))
        self.assertEqual(len(result), 2)

    def test_stop_on_error_keyword(self):
        aggregator = iris.analysis.MEAN
        self.cube.remove_coord('time')
        cubelist = iris.cube.CubeList([self.cube])
        self.assertRaises(Exception, temporal.calc_time_stat, cubelist, aggregator,
            temporal.TP_YEAR, stop_on_error=True)

    def test_drop_new_coords_keyword(self):
        aggregator = iris.analysis.MEAN
        result = temporal.calc_time_stat(self.cube, aggregator, temporal.TP_YEAR,
            drop_new_coords=True)
        self.assertTrue(result, isinstance(result, iris.cube.Cube))
        self.assertFalse('year' in [c.name() for c in self.cube.coords()])


class TestMultiYearAuxCoord(unittest.TestCase):
    """Test the cubeutils.add_multi_year_aux_coord() utility function."""

    # In theory this class ought to be in the test_cubeutils module. It was
    # created here owing to conceptual overlap with the test classes above
    # which make use of various auxiliary coordinates.

    def setUp(self):
        # create time coordinate spanning 60 years, one point per year
        ntimes = 60
        data = np.random.uniform(low=0.0, high=50.0, size=ntimes)
        time = _create_apy_time_coord(npoints=ntimes)
        cube = iris.cube.Cube(data, standard_name='air_temperature', units='degc')
        cube.add_dim_coord(time, 0)
        self.cube = cube

    def test_20_year_period(self):
        cubeutils.add_multi_year_aux_coord(self.cube, 'time', 20, name='twenty_years')
        coord_names = [c.name() for c in self.cube.coords()]
        self.assertTrue('twenty_years' in coord_names)
        coord = self.cube.coord('twenty_years')
        npt.assert_array_equal(coord.points[ 0:20], [20091201]*20)
        npt.assert_array_equal(coord.points[20:40], [20291201]*20)
        npt.assert_array_equal(coord.points[40:60], [20491201]*20)

    def test_20_year_period_w_bounds(self):
        cubeutils.add_multi_year_aux_coord(self.cube, 'time', 20, name='twenty_years',
            add_bounds=True)
        coord_names = [c.name() for c in self.cube.coords()]
        self.assertTrue('twenty_years' in coord_names)
        coord = self.cube.coord('twenty_years')
        self.assertEqual(coord.bounds.shape, (60,2))
        self.assertEqual(coord.bounds[0,0], 19991201)
        self.assertEqual(coord.bounds[0,-1], 20191201)

    def test_20_year_period_w_ref_date(self):
        cubeutils.add_multi_year_aux_coord(self.cube, 'time', 20, name='twenty_years',
            ref_date=cft.datetime(1900, 1, 1))
        coord_names = [c.name() for c in self.cube.coords()]
        self.assertTrue('twenty_years' in coord_names)
        coord = self.cube.coord('twenty_years')
        npt.assert_array_equal(coord.points[ 0:20], [20100101]*20)
        npt.assert_array_equal(coord.points[20:40], [20300101]*20)
        npt.assert_array_equal(coord.points[40:60], [20500101]*20)

    def test_25_year_period(self):
        cubeutils.add_multi_year_aux_coord(self.cube, 'time', 25, name='25_years')
        coord_names = [c.name() for c in self.cube.coords()]
        self.assertTrue('25_years' in coord_names)
        coord = self.cube.coord('25_years')
        npt.assert_array_equal(coord.points[ 0:10], [19961201]*10)
        npt.assert_array_equal(coord.points[10:35], [20211201]*25)
        npt.assert_array_equal(coord.points[35:60], [20461201]*25)

    def test_25_year_period_w_ref_date(self):
        cubeutils.add_multi_year_aux_coord(self.cube, 'time', 25, name='25_years',
            ref_date=cft.datetime(1900, 1, 1))
        coord_names = [c.name() for c in self.cube.coords()]
        self.assertTrue('25_years' in coord_names)
        coord = self.cube.coord('25_years')
        npt.assert_array_equal(coord.points[ 0:25], [20120101]*25)
        npt.assert_array_equal(coord.points[25:50], [20370101]*25)
        npt.assert_array_equal(coord.points[50:60], [20620101]*10)


def _create_apa_time_coord(npoints=90, units=None, calendar='360_day'):
    """Create a daily-mean time coordinate object."""
    times = np.arange(npoints)
    if not units:
        units = cfu.Unit('days since 1999-12-01', calendar=calendar)
    tcoord = iris.coords.DimCoord(times, standard_name='time', units=units)
    if npoints > 1: tcoord.guess_bounds()
    return tcoord


def _create_apm_time_coord(npoints=12, units=None, calendar='360_day'):
    """Create a monthly-mean time coordinate object."""
    times = np.arange(15, npoints*30+15, 30)
    if not units:
        units = cfu.Unit('days since 1999-12-01', calendar=calendar)
    tcoord = iris.coords.DimCoord(times, standard_name='time', units=units)
    if npoints > 1: tcoord.guess_bounds()
    return tcoord


def _create_apy_time_coord(npoints=10, units=None, calendar='360_day'):
    """Create an annual-mean time coordinate object."""
    times = np.arange(180, npoints*360+180, 360)
    if not units:
        units = cfu.Unit('days since 1999-12-01', calendar=calendar)
    tcoord = iris.coords.DimCoord(times, standard_name='time', units=units)
    if npoints > 1: tcoord.guess_bounds()
    return tcoord


if __name__ == '__main__':
    unittest.main()
