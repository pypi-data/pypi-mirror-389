# (C) British Crown Copyright 2018-2023, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Unit tests for the afterburner.stats.spatial module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import logging
import unittest
import warnings
import numpy as np
import numpy.ma as ma
import numpy.testing as npt

import iris
import iris.analysis
import iris.coords

from afterburner import compare_iris_version
from afterburner.stats import spatial
from afterburner.utils import cubeutils
from afterburner.misc import stockcubes

_logger = logging.getLogger('afterburner')
_log_level = _logger.level


def setUpModule(self):
    # disable logging
    _logger.level = 100
    
    # disable Iris warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='iris.*')


def tearDownModule(self):
    # enable logging
    _logger.level = _log_level

    # reset warnings
    warnings.resetwarnings()


class TestLatLonDomain(unittest.TestCase):
    """Test the generation of statistics over a global lat-long domain."""

    def setUp(self):
        col = np.array([0,2,4,6,8,10], dtype='f').reshape(6, 1)
        data = np.repeat(col, 6, axis=1)
        cube = stockcubes.geo_yx(data)
        self.cube = cube
        self.data_mean = np.average(data)
        self.data_sum = np.sum(data)
        self.data_std = np.std(data, ddof=1)   # set ddof to match Iris usage

    def test_mean(self):
        aggregator = iris.analysis.MEAN
        result = spatial.calc_spatial_stat(self.cube, aggregator)
        self.assertEqual(result.ndim, 0)
        self.assertAlmostEqual(result.data, self.data_mean)
        self.assertTrue(result.cell_methods[0].method == 'mean')
        self.assertTrue(cubeutils.is_scalar_coord(result, 'latitude'))
        self.assertTrue(cubeutils.is_scalar_coord(result, 'longitude'))
        lon_coord = result.coord('longitude')
        self.assertTrue(cubeutils.is_circular(lon_coord.points, 360, bounds=lon_coord.bounds))

    def test_zonal_mean(self):
        aggregator = iris.analysis.MEAN
        result = spatial.calc_spatial_stat(self.cube, aggregator, coords='longitude')
        self.assertEqual(result.ndim, 1)
        self.assertTrue(result.cell_methods[0].method == 'mean')
        self.assertFalse(cubeutils.is_scalar_coord(result, 'latitude'))
        self.assertTrue(cubeutils.is_scalar_coord(result, 'longitude'))
        lon_coord = result.coord('longitude')
        self.assertTrue(cubeutils.is_circular(lon_coord.points, 360, bounds=lon_coord.bounds))

    def test_area_weighted_mean(self):
        aggregator = iris.analysis.MEAN
        result = spatial.calc_spatial_stat(self.cube, aggregator, area_weighted=True)
        self.assertEqual(result.ndim, 0)
        self.assertAlmostEqual(result.data, self.data_mean)
        self.assertTrue(result.cell_methods[0].method == 'mean')
        self.assertTrue(cubeutils.is_scalar_coord(result, 'latitude'))
        self.assertTrue(cubeutils.is_scalar_coord(result, 'longitude'))
        lon_coord = result.coord('longitude')
        self.assertTrue(cubeutils.is_circular(lon_coord.points, 360, bounds=lon_coord.bounds))

    def test_mean_w_user_weights(self):
        aggregator = iris.analysis.MEAN
        wts = np.ones(self.cube.shape)
        wts[-1] = 0.1
        result = spatial.calc_spatial_stat(self.cube, aggregator, agg_opts={'weights': wts})
        self.assertEqual(result.ndim, 0)
        self.assertLess(result.data, self.data_mean)

    @unittest.skipUnless(hasattr(iris.coords, 'CellMeasure'), "iris.coords.CellMeasure class not present")
    def test_mean_w_area_cell_measure(self):
        cube = stockcubes.geo_tzyx(10.0)
        wts = np.ones(cube.shape[-2:])
        cell_area = iris.coords.CellMeasure(wts, standard_name='cell_area',
            measure='area', units='m2')
        cube.add_cell_measure(cell_area, [2, 3])
        aggregator = iris.analysis.MEAN
        result = spatial.calc_spatial_stat(cube, aggregator, area_weighted=True)
        self.assertEqual(result.ndim, 2)

    def test_mean_w_bool_mask(self):
        aggregator = iris.analysis.MEAN
        mask = ma.ones(self.cube.shape)
        mask = ma.masked_where(self.cube.data > 8, mask)
        result = spatial.calc_spatial_stat(self.cube, aggregator, mask=mask)
        self.assertEqual(result.ndim, 0)
        self.assertLess(result.data, self.data_mean)

        mask = np.ones(self.cube.shape)
        with self.assertRaises(ValueError):
            spatial.calc_spatial_stat(self.cube, aggregator, mask=mask)

    def test_sum(self):
        aggregator = iris.analysis.SUM
        result = spatial.calc_spatial_stat(self.cube, aggregator)
        self.assertEqual(result.ndim, 0)
        self.assertAlmostEqual(result.data, self.data_sum)
        self.assertTrue(result.cell_methods[0].method == 'sum')
        self.assertTrue(cubeutils.is_scalar_coord(result, 'latitude'))
        self.assertTrue(cubeutils.is_scalar_coord(result, 'longitude'))
        lon_coord = result.coord('longitude')
        self.assertTrue(cubeutils.is_circular(lon_coord.points, 360, bounds=lon_coord.bounds))

    def test_sum_w_frac_mask(self):
        aggregator = iris.analysis.SUM
        mask = ma.masked_equal(self.cube.data, 0)
        mask[~mask.mask] = 0.5
        result = spatial.calc_spatial_stat(self.cube, aggregator, mask=mask,
            mask_is_area_frac=True)
        self.assertEqual(result.ndim, 0)
        self.assertAlmostEqual(result.data, self.data_sum*0.5)

    def test_std_dev(self):
        aggregator = iris.analysis.STD_DEV
        result = spatial.calc_spatial_stat(self.cube, aggregator)
        self.assertEqual(result.ndim, 0)
        self.assertAlmostEqual(result.data, self.data_std)
        self.assertTrue(result.cell_methods[0].method == 'standard_deviation')
        self.assertTrue(cubeutils.is_scalar_coord(result, 'latitude'))
        self.assertTrue(cubeutils.is_scalar_coord(result, 'longitude'))

    def test_std_dev_w_ddof_arg(self):
        aggregator = iris.analysis.STD_DEV
        # set ddof argument to the default value used by the numpy.std() function
        result = spatial.calc_spatial_stat(self.cube, aggregator, agg_opts={'ddof': 0})
        self.assertEqual(result.ndim, 0)
        self.assertAlmostEqual(result.data, np.std(self.cube.data))

    def test_unexpected_aggregator_options(self):
        wts = np.ones(self.cube.shape)
        wts[-1] = 0.1
        with self.assertRaises(TypeError):
            spatial.calc_spatial_stat(self.cube, iris.analysis.STD_DEV, area_weighted=True)
            spatial.calc_spatial_stat(self.cube, iris.analysis.STD_DEV, agg_opts={'weights': wts})


class TestHeightLatLonDomain(unittest.TestCase):
    """Test the generation of statistics over a global height-lat-long domain."""

    def setUp(self):
        col = np.array([0,2,4,6,8,10], dtype='f').reshape(6, 1)
        data = np.tile(col, [3,1,6])
        cube = stockcubes.geo_zyx(data)
        self.cube = cube
        self.data_mean = np.average(data[0])
        self.data_sum = np.sum(data[0])

    def test_mean(self):
        aggregator = iris.analysis.MEAN
        result = spatial.calc_spatial_stat(self.cube, aggregator)
        self.assertEqual(result.ndim, 1)
        self.assertAlmostEqual(result.data[0], self.data_mean)
        self.assertTrue(result.cell_methods[0].method == 'mean')
        self.assertTrue(cubeutils.is_scalar_coord(result, 'latitude'))
        self.assertTrue(cubeutils.is_scalar_coord(result, 'longitude'))
        lon_coord = result.coord('longitude')
        self.assertTrue(cubeutils.is_circular(lon_coord.points, 360, bounds=lon_coord.bounds))

    def test_zonal_mean(self):
        aggregator = iris.analysis.MEAN
        result = spatial.calc_spatial_stat(self.cube, aggregator, coords='longitude')
        self.assertEqual(result.ndim, 2)
        self.assertTrue(result.cell_methods[0].method == 'mean')
        self.assertFalse(cubeutils.is_scalar_coord(result, 'latitude'))
        self.assertTrue(cubeutils.is_scalar_coord(result, 'longitude'))
        lon_coord = result.coord('longitude')
        self.assertTrue(cubeutils.is_circular(lon_coord.points, 360, bounds=lon_coord.bounds))

    def test_mean_w_bool_mask(self):
        aggregator = iris.analysis.MEAN
        mask = ma.ones(self.cube.shape[-2:])
        mask = ma.masked_where(self.cube.data[0] > 8, mask)
        result = spatial.calc_spatial_stat(self.cube, aggregator, mask=mask)
        self.assertEqual(result.ndim, 1)
        self.assertLess(result.data[0], self.data_mean)

        mask = np.ones(self.cube.shape[-2:])
        with self.assertRaises(ValueError):
            spatial.calc_spatial_stat(self.cube, aggregator, mask=mask)

    def test_sum(self):
        aggregator = iris.analysis.SUM
        result = spatial.calc_spatial_stat(self.cube, aggregator)
        self.assertEqual(result.ndim, 1)
        self.assertAlmostEqual(result.data[0], self.data_sum)
        self.assertTrue(result.cell_methods[0].method == 'sum')
        self.assertTrue(cubeutils.is_scalar_coord(result, 'latitude'))
        self.assertTrue(cubeutils.is_scalar_coord(result, 'longitude'))
        lon_coord = result.coord('longitude')
        self.assertTrue(cubeutils.is_circular(lon_coord.points, 360, bounds=lon_coord.bounds))

    def test_sum_w_frac_mask(self):
        aggregator = iris.analysis.SUM
        mask = ma.masked_equal(self.cube.data[0], 0)
        mask[~mask.mask] = 0.5
        result = spatial.calc_spatial_stat(self.cube, aggregator, mask=mask,
            mask_is_area_frac=True)
        self.assertEqual(result.ndim, 1)
        self.assertAlmostEqual(result.data[0], self.data_sum*0.5)


class TestRotatedLatLonDomain(unittest.TestCase):
    """Test the generation of statistics over a rotated lat-long domain."""

    def setUp(self):
        col = np.array([0,2,4,6,8,10], dtype='f').reshape(6, 1)
        data = np.repeat(col, 6, axis=1)
        cube = stockcubes.rot_yx(data)
        self.cube = cube
        self.data_mean = np.average(data)
        self.data_sum = np.sum(data)

    def test_mean(self):
        aggregator = iris.analysis.MEAN
        result = spatial.calc_spatial_stat(self.cube, aggregator,
            coords=['grid_latitude', 'grid_longitude'])
        self.assertEqual(result.ndim, 0)
        self.assertAlmostEqual(result.data, self.data_mean)
        self.assertTrue(result.cell_methods[0].method == 'mean')
        self.assertTrue(cubeutils.is_scalar_coord(result, 'grid_latitude'))
        self.assertTrue(cubeutils.is_scalar_coord(result, 'grid_longitude'))

    @unittest.skipIf(compare_iris_version('2.1', 'ge'), "Iris version >= 2.1")
    def test_zonal_mean(self):
        aggregator = iris.analysis.MEAN
        # Iris versions prior to 2.1 raise an error if one tries to partially
        # collapse a multi-dimensional coordinate (latitude, in this case).
        with self.assertRaises(ValueError):
            spatial.calc_spatial_stat(self.cube, aggregator, coords='grid_longitude')

    @unittest.skipIf(compare_iris_version('3.4', 'ge'), "Iris version >= 3.4")
    def test_area_weighted_mean(self):
        aggregator = iris.analysis.MEAN
        # Iris < 3.4 raises an error if it's asked to calculate area weights.
        with self.assertRaises(ValueError):
            spatial.calc_spatial_stat(self.cube, aggregator, area_weighted=True,
                coords=['grid_latitude', 'grid_longitude'])

    def test_mean_w_user_weights(self):
        aggregator = iris.analysis.MEAN
        wts = np.ones(self.cube.shape)
        wts[-1] = 0.1
        result = spatial.calc_spatial_stat(self.cube, aggregator, agg_opts={'weights': wts},
            coords=['grid_latitude', 'grid_longitude'])
        self.assertEqual(result.ndim, 0)
        self.assertLess(result.data, self.data_mean)

    @unittest.skipUnless(hasattr(iris.coords, 'CellMeasure'), "iris.coords.CellMeasure class not present")
    def test_mean_w_area_cell_measure(self):
        cube = stockcubes.rot_zyx(10.0)
        wts = np.ones(cube.shape[-2:])
        cell_area = iris.coords.CellMeasure(wts, standard_name='cell_area',
            measure='area', units='m2')
        cube.add_cell_measure(cell_area, [1, 2])
        aggregator = iris.analysis.MEAN
        result = spatial.calc_spatial_stat(cube, aggregator, area_weighted=True,
            coords=['grid_latitude', 'grid_longitude'])
        self.assertEqual(result.ndim, 1)
        self.assertTrue(cubeutils.is_scalar_coord(result, 'grid_latitude'))
        self.assertTrue(cubeutils.is_scalar_coord(result, 'grid_longitude'))

    def test_sum(self):
        aggregator = iris.analysis.SUM
        result = spatial.calc_spatial_stat(self.cube, aggregator,
            coords=['grid_latitude', 'grid_longitude'])
        self.assertEqual(result.ndim, 0)
        self.assertAlmostEqual(result.data, self.data_sum)
        self.assertTrue(result.cell_methods[0].method == 'sum')
        self.assertTrue(cubeutils.is_scalar_coord(result, 'grid_latitude'))
        self.assertTrue(cubeutils.is_scalar_coord(result, 'grid_longitude'))

    def test_sum_w_frac_mask(self):
        aggregator = iris.analysis.SUM
        mask = ma.masked_equal(self.cube.data, 0)
        mask[~mask.mask] = 0.5
        result = spatial.calc_spatial_stat(self.cube, aggregator, mask=mask,
            mask_is_area_frac=True)
        self.assertEqual(result.ndim, 0)
        self.assertAlmostEqual(result.data, self.data_sum*0.5)


if __name__ == '__main__':
    unittest.main()
