# (C) British Crown Copyright 2016, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Unit tests for the afterburner.coords module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import unittest
import numpy as np
import numpy.testing as npt
from iris.coords import CoordExtent

from afterburner.coords import *
from afterburner.utils import (OpenInterval, LeftOpenInterval,
    LeftClosedInterval, ClosedInterval)
from afterburner.misc import stockcubes

# Define +ve and -ve infinity.
POSINF = float('inf')
NEGINF = float('-inf')


class _TestPoint(object):
    """Simple class for representing a coordinate location on the globe."""

    def __init__(self, lat, lon, x, y):
        self.lat = lat
        self.lon = lon
        self.x = x
        self.y = y

    @property
    def latlon(self):
        return self.lat, self.lon

    @property
    def lonlat(self):
        return self.lon, self.lat

    @property
    def xy(self):
        return self.x, self.y


# Coordinates of Met Office HQ in various coordinate systems.
hq_osgb36 = _TestPoint(50.726728, -3.473658, 296000.0, 93000.0)
hq_wgs84 = _TestPoint(50.727281, -3.474856, 0, 0)


class TestCoordRange(unittest.TestCase):
    """Unit tests for the CoordRange class."""

    def test_scalar_values(self):
        cr = CoordRange(1)
        self.assertTrue(cr.contains(1))
        self.assertFalse(cr.contains(0))
        self.assertTrue(isinstance(cr.values, np.ndarray))

        cr = CoordRange(-273.0)
        self.assertTrue(cr.contains(-273))
        self.assertFalse(cr.contains(0))
        self.assertTrue(isinstance(cr.values, np.ndarray))

    def test_list_of_ints(self):
        cr = CoordRange(range(1, 10))
        self.assertFalse(cr.contains(0))
        self.assertTrue(cr.contains(1))
        self.assertTrue(cr.contains(9))
        self.assertFalse(cr.contains(10))
        self.assertTrue(isinstance(cr.values, np.ndarray))

        cr = CoordRange(range(1, 10), dtype='int32')
        self.assertEqual(cr.values.dtype.itemsize, 4)
        self.assertFalse(cr.contains(0))
        self.assertTrue(cr.contains(1))
        self.assertTrue(cr.contains(9))
        self.assertFalse(cr.contains(10))

        cr = CoordRange(range(9, 0, -1))
        self.assertFalse(cr.contains(0))
        self.assertTrue(cr.contains(1))
        self.assertTrue(cr.contains(9))
        self.assertFalse(cr.contains(10))
        self.assertTrue(isinstance(cr.values, np.ndarray))

    def test_list_of_floats(self):
        # test 32-bit floats
        cr = CoordRange(range(1, 10), dtype='f4')
        self.assertEqual(cr.values.dtype.kind, 'f')
        self.assertEqual(cr.values.dtype.itemsize, 4)
        self.assertFalse(cr.contains(np.float32(0.9999), rtol=0, atol=1e-5))
        self.assertTrue(cr.contains(np.float32(0.999999), rtol=0, atol=1e-5))
        self.assertTrue(cr.contains(1.0))
        self.assertFalse(cr.contains(np.float32(1.0001), rtol=0, atol=1e-5))
        self.assertTrue(cr.contains(np.float32(1.000001), rtol=0, atol=1e-5))
        self.assertFalse(cr.contains(1.5))
        self.assertTrue(cr.contains(9.0))
        self.assertFalse(cr.contains(10.0))

        # test 64-bit floats
        cr = CoordRange(np.arange(1., 10.), dtype='f8')
        self.assertEqual(cr.values.dtype.kind, 'f')
        self.assertEqual(cr.values.dtype.itemsize, 8)
        self.assertFalse(cr.contains(0.99999, rtol=0, atol=1e-7))
        self.assertTrue(cr.contains(0.9999999, rtol=0, atol=1e-7))
        self.assertTrue(cr.contains(1.0))
        self.assertFalse(cr.contains(1.00001, rtol=0, atol=1e-7))
        self.assertTrue(cr.contains(1.00000001, rtol=0, atol=1e-7))
        self.assertFalse(cr.contains(1.5))
        self.assertTrue(cr.contains(9.0))
        self.assertFalse(cr.contains(10.0))

    def test_open_interval(self):
        cr = CoordRange([1, 10], open=True)
        self.assertTrue(cr.is_interval())
        self.assertTrue(isinstance(cr.interval, OpenInterval))
        self.assertFalse(cr.contains(0))
        self.assertFalse(cr.contains(1))
        self.assertTrue(cr.contains(5))
        self.assertFalse(cr.contains(10))

        cr = CoordRange([10, 1], open=True)
        self.assertFalse(cr.contains(0))
        self.assertFalse(cr.contains(1))
        self.assertTrue(cr.contains(5))
        self.assertFalse(cr.contains(10))

        cr = CoordRange([1, POSINF], open=True)
        self.assertFalse(cr.contains(0))
        self.assertFalse(cr.contains(1))
        self.assertTrue(cr.contains(10000))
        self.assertTrue(cr.contains(1e20))
        self.assertFalse(cr.contains(POSINF))

        self.assertRaises(ValueError, CoordRange, [1,5,10], open=True)

    def test_leftopen_interval(self):
        cr = CoordRange([1, 10], leftopen=True)
        self.assertTrue(cr.is_interval())
        self.assertTrue(isinstance(cr.interval, LeftOpenInterval))
        self.assertFalse(cr.contains(0))
        self.assertFalse(cr.contains(1))
        self.assertTrue(cr.contains(5))
        self.assertTrue(cr.contains(10))
        self.assertFalse(cr.contains(11))

        cr = CoordRange([10, 1], leftopen=True)
        self.assertFalse(cr.contains(0))
        self.assertTrue(cr.contains(1))
        self.assertTrue(cr.contains(5))
        self.assertFalse(cr.contains(10))
        self.assertFalse(cr.contains(11))

        cr = CoordRange([NEGINF, -1], leftopen=True)
        self.assertFalse(cr.contains(0))
        self.assertTrue(cr.contains(-1))
        self.assertTrue(cr.contains(-10000))
        self.assertTrue(cr.contains(-1e20))
        self.assertFalse(cr.contains(NEGINF))

    def test_leftclosed_interval(self):
        cr = CoordRange([1, 10], leftclosed=True)
        self.assertTrue(cr.is_interval())
        self.assertTrue(isinstance(cr.interval, LeftClosedInterval))
        self.assertFalse(cr.contains(0))
        self.assertTrue(cr.contains(1))
        self.assertTrue(cr.contains(5))
        self.assertFalse(cr.contains(10))
        self.assertFalse(cr.contains(11))

        cr = CoordRange([10, 1], leftclosed=True)
        self.assertFalse(cr.contains(0))
        self.assertFalse(cr.contains(1))
        self.assertTrue(cr.contains(5))
        self.assertTrue(cr.contains(10))
        self.assertFalse(cr.contains(11))

        cr = CoordRange([1, POSINF], leftclosed=True)
        self.assertFalse(cr.contains(0))
        self.assertTrue(cr.contains(1))
        self.assertTrue(cr.contains(10000))
        self.assertTrue(cr.contains(1e20))
        self.assertFalse(cr.contains(POSINF))

    def test_closed_interval(self):
        cr = CoordRange([1, 10], closed=True)
        self.assertTrue(cr.is_interval())
        self.assertTrue(isinstance(cr.interval, ClosedInterval))
        self.assertFalse(cr.contains(0))
        self.assertTrue(cr.contains(1))
        self.assertTrue(cr.contains(5))
        self.assertTrue(cr.contains(10))
        self.assertFalse(cr.contains(11))

        cr = CoordRange([10, 1], closed=True)
        self.assertFalse(cr.contains(0))
        self.assertTrue(cr.contains(1))
        self.assertTrue(cr.contains(5))
        self.assertTrue(cr.contains(10))
        self.assertFalse(cr.contains(11))

        cr = CoordRange([1, POSINF], closed=True)
        self.assertFalse(cr.contains(0))
        self.assertTrue(cr.contains(1))
        self.assertTrue(cr.contains(10000))
        self.assertTrue(cr.contains(1e20))
        self.assertTrue(cr.contains(POSINF))

    def test_data_types(self):
        cr = CoordRange([1, 10], open=True)
        self.assertEqual(cr.values.dtype.kind, 'i')
        self.assertEqual(cr.values.dtype.itemsize, 8)

        cr = CoordRange([1, 10], open=True, dtype='i4')
        self.assertEqual(cr.values.dtype.kind, 'i')
        self.assertEqual(cr.values.dtype.itemsize, 4)

        cr = CoordRange([1., 10.], open=True)
        self.assertEqual(cr.values.dtype.kind, 'f')
        self.assertEqual(cr.values.dtype.itemsize, 8)

        cr = CoordRange([1, 10], open=True, dtype='f4')
        self.assertEqual(cr.values.dtype.kind, 'f')
        self.assertEqual(cr.values.dtype.itemsize, 4)

        cr = CoordRange([1, 10], open=True, dtype='f8')
        self.assertEqual(cr.values.dtype.kind, 'f')
        self.assertEqual(cr.values.dtype.itemsize, 8)

    def test_from_str(self):
        cr = CoordRange.from_string('42')
        self.assertEqual(cr.values.dtype.kind, 'i')
        self.assertTrue(np.array_equal(cr.values, [42]))

        cr = CoordRange.from_string('3.14')
        self.assertEqual(cr.values.dtype.kind, 'f')
        self.assertTrue(np.allclose(cr.values, [3.14]))

        cr = CoordRange.from_string('0,1,3,5,7')
        self.assertEqual(cr.values.dtype.kind, 'i')
        self.assertTrue(np.array_equal(cr.values, [0, 1, 3, 5, 7]))

        cr = CoordRange.from_string('0,1,3.0,5,7')
        self.assertEqual(cr.values.dtype.kind, 'f')
        self.assertTrue(np.array_equal(cr.values, [0, 1., 3., 5., 7.]))

        cr = CoordRange.from_string('(1,10)')
        self.assertEqual(cr.values.dtype.kind, 'i')
        self.assertTrue(np.array_equal(cr.values, [1, 10]))
        self.assertTrue(isinstance(cr.interval, OpenInterval))

        cr = CoordRange.from_string('(1.0,10.0]')
        self.assertEqual(cr.values.dtype.kind, 'f')
        self.assertTrue(np.array_equal(cr.values, [1., 10.]))
        self.assertTrue(isinstance(cr.interval, LeftOpenInterval))

        cr = CoordRange.from_string('[1,10)', dtype='int32')
        self.assertEqual(cr.values.dtype.itemsize, 4)
        self.assertTrue(np.array_equal(cr.values, [1, 10]))
        self.assertTrue(isinstance(cr.interval, LeftClosedInterval))

        cr = CoordRange.from_string('[1,10]', dtype='float32')
        self.assertEqual(cr.values.dtype.itemsize, 4)
        self.assertTrue(np.array_equal(cr.values, [1., 10.]))
        self.assertTrue(isinstance(cr.interval, ClosedInterval))

        cr = CoordRange.from_string('[1,inf)')
        self.assertTrue(np.array_equal(cr.values, [1., float('inf')]))
        self.assertTrue(isinstance(cr.interval, LeftClosedInterval))

        cr = CoordRange.from_string('(0,+inf)')
        self.assertTrue(np.array_equal(cr.values, [0, float('inf')]))
        self.assertTrue(isinstance(cr.interval, OpenInterval))

        cr = CoordRange.from_string('(-inf,-273]')
        self.assertTrue(np.array_equal(cr.values, [float('-inf'), -273.]))
        self.assertTrue(isinstance(cr.interval, LeftOpenInterval))

        self.assertRaises(ValueError, CoordRange.from_string, '41 42 43')
        self.assertRaises(ValueError, CoordRange.from_string, '[41, 42, 43]')

    def test_as_coord_extent(self):
        cr = CoordRange([1, 10], open=True)
        ce = cr.as_coord_extent('latitude')
        self.assertEqual(ce.minimum, 1)
        self.assertEqual(ce.maximum, 10)
        self.assertEqual(ce.min_inclusive, False)
        self.assertEqual(ce.max_inclusive, False)

        cr = CoordRange([-10, 10], leftopen=True)
        ce = cr.as_coord_extent('latitude')
        self.assertEqual(ce.minimum, -10)
        self.assertEqual(ce.maximum, 10)
        self.assertEqual(ce.min_inclusive, False)
        self.assertEqual(ce.max_inclusive, True)

        cr = CoordRange([10, 1], leftclosed=True)
        ce = cr.as_coord_extent('latitude')
        self.assertEqual(ce.minimum, 1)
        self.assertEqual(ce.maximum, 10)
        self.assertEqual(ce.min_inclusive, False)
        self.assertEqual(ce.max_inclusive, True)

        cr = CoordRange([1, 10], closed=True)
        ce = cr.as_coord_extent('latitude')
        self.assertEqual(ce.minimum, 1)
        self.assertEqual(ce.maximum, 10)
        self.assertEqual(ce.min_inclusive, True)
        self.assertEqual(ce.max_inclusive, True)

        cr = CoordRange([1, 10])
        self.assertRaises(TypeError, cr.as_coord_extent, 'latitude')

    def test_eq_method_w_arrays(self):
        cr = CoordRange(range(1, 10))
        self.assertEqual(cr, CoordRange(range(1, 10)))
        self.assertNotEqual(cr, CoordRange(range(0, 10)))
        self.assertNotEqual(cr, CoordRange(range(1, 10), dtype='f4'))

        cr = CoordRange(range(1, 10), dtype='f4')
        self.assertEqual(cr, CoordRange(np.arange(1, 10), dtype='f4'))
        self.assertNotEqual(cr, CoordRange(range(0, 10), dtype='f4'))
        self.assertNotEqual(cr, CoordRange(np.arange(1, 10), dtype='f8'))
        self.assertNotEqual(cr, CoordRange(range(1, 10)))

        cr = CoordRange(range(1, 10), dtype='f8')
        self.assertEqual(cr, CoordRange(np.arange(1, 10), dtype=np.float64))
        self.assertNotEqual(cr, CoordRange(range(0, 10), dtype=np.float64))
        self.assertNotEqual(cr, CoordRange(np.arange(1, 10), dtype=np.float32))
        self.assertNotEqual(cr, CoordRange(range(1, 10)))

    def test_eq_method_w_intervals(self):
        cr = CoordRange([0, 10], leftclosed=True)
        self.assertEqual(cr, CoordRange([0, 10], leftclosed=True))
        self.assertNotEqual(cr, CoordRange([0, 10], leftclosed=True, dtype='f4'))
        self.assertNotEqual(cr, CoordRange([1, 10], leftclosed=True))
        self.assertNotEqual(cr, CoordRange([0, 10], leftopen=True))

        cr = CoordRange([0, float('inf')], leftclosed=True)
        self.assertEqual(cr, CoordRange([0, float('inf')], leftclosed=True))
        self.assertNotEqual(cr, CoordRange([0, float('inf')], leftopen=True))

        cr = CoordRange([1, 10], leftclosed=True)
        self.assertNotEqual(cr, CoordRange([1, 10]))
        self.assertNotEqual(cr, CoordRange(range(1, 10)))

    def test_hash_method(self):
        cr1 = CoordRange(range(1, 10))
        cr2 = CoordRange(range(1, 10))
        cr3 = CoordRange(range(0, 10))
        self.assertEqual(hash(cr1), hash(cr2))
        self.assertEqual(len(set([cr1, cr2, cr3])), 2)
        self.assertNotEqual(hash(cr1), hash(cr3))
        self.assertNotEqual(id(cr1), id(cr2))

        cr1 = CoordRange([0, 10], leftclosed=True)
        cr2 = CoordRange([0, 10], leftclosed=True)
        cr3 = CoordRange([0, 10], leftopen=True)
        self.assertEqual(hash(cr1), hash(cr2))
        self.assertEqual(len(set([cr1, cr2, cr3])), 2)
        self.assertNotEqual(hash(cr1), hash(cr3))
        self.assertNotEqual(id(cr1), id(cr2))

    def test_immutability(self):
        cr = CoordRange(range(1, 10))
        with self.assertRaises(AttributeError):
            cr.values = range(0, 9)
            cr.values[0] = -999
            cr._values[0] = -999


class TestRectRegionAs2dMask(unittest.TestCase):
    """Unit tests for the rectangular_region_as_2d_mask() function."""

    def test_using_named_coords(self):
        cube = stockcubes.geo_yx(shape=(19,36))
        lat_extent = CoordExtent('latitude', -45, 45)
        lon_extent = CoordExtent('longitude', 45, 135)

        marr = rectangular_region_as_2d_mask([lat_extent, lon_extent], cube=cube)
        self.assertEqual(marr.shape, cube.shape)
        self.assertEqual(marr.count(), 11*11)   # 11 lats x 11 lons

        marr = rectangular_region_as_2d_mask([lat_extent, lon_extent], cube=cube,
            ignore_bounds=True)
        self.assertEqual(marr.shape, cube.shape)
        self.assertEqual(marr.count(), 9*9)   # 9 lats x 9 lons

        with self.assertRaises(ValueError):
            rectangular_region_as_2d_mask([lat_extent])
            rectangular_region_as_2d_mask([lat_extent, lon_extent], cube=None)
            rectangular_region_as_2d_mask([lat_extent, lon_extent, lat_extent])

    def test_using_coord_objects(self):
        cube = stockcubes.geo_yx(shape=(19,36))
        lat_extent = CoordExtent(cube.coord('latitude'), -45, 45)
        lon_extent = CoordExtent(cube.coord('longitude'), 45, 135)

        marr = rectangular_region_as_2d_mask([lat_extent, lon_extent])
        self.assertEqual(marr.shape, cube.shape)
        self.assertEqual(marr.count(), 11*11)   # 11 lats x 11 lons

        marr = rectangular_region_as_2d_mask([lat_extent, lon_extent],
            ignore_bounds=True)
        self.assertEqual(marr.shape, cube.shape)
        self.assertEqual(marr.count(), 9*9)   # 9 lats x 9 lons

        with self.assertRaises(ValueError):
            rectangular_region_as_2d_mask([lat_extent])
            rectangular_region_as_2d_mask([lat_extent, lon_extent, lat_extent])

    def test_using_rot_pole_coords(self):
        cube = stockcubes.rot_yx(shape=(21,20), start_lat=-10, end_lat=30,
            start_lon=340, end_lon=380)
        lat_extent = CoordExtent('grid_latitude', -5, 10)
        lon_extent = CoordExtent('grid_longitude', 350, 365)

        marr = rectangular_region_as_2d_mask([lat_extent, lon_extent], cube=cube)
        self.assertEqual(marr.shape, cube.shape)
        self.assertEqual(marr.count(), 9*9)   # 9 lats x 9 lons

        marr = rectangular_region_as_2d_mask([lat_extent, lon_extent], cube=cube,
            ignore_bounds=True)
        self.assertEqual(marr.shape, cube.shape)
        self.assertEqual(marr.count(), 8*8)   # 8 lats x 8 lons

    # shifted longitudes not currently working
    def test_using_shifted_longitudes(self):
        cube = stockcubes.geo_yx(shape=(19,36))
        lat_extent = CoordExtent('latitude', -45, 45)
        lon_extent = CoordExtent('longitude', -25, 25)

        marr = rectangular_region_as_2d_mask([lat_extent, lon_extent], cube=cube)
        self.assertEqual(marr.shape, cube.shape)
        self.assertEqual(marr.count(), 11*7)   # 11 lats x 7 lons

        marr = rectangular_region_as_2d_mask([lat_extent, lon_extent], cube=cube,
            ignore_bounds=True)
        self.assertEqual(marr.shape, cube.shape)
        self.assertEqual(marr.count(), 9*5)   # 9 lats x 5 lons

        cube = stockcubes.geo_yx(shape=(19,36), start_lon=-180, end_lon=180)
        lat_extent = CoordExtent('latitude', -45, 45)
        lon_extent = CoordExtent('longitude', 335, 385)

        marr = rectangular_region_as_2d_mask([lat_extent, lon_extent], cube=cube)
        self.assertEqual(marr.shape, cube.shape)
        self.assertEqual(marr.count(), 11*7)   # 11 lats x 7 lons

        marr = rectangular_region_as_2d_mask([lat_extent, lon_extent], cube=cube,
            ignore_bounds=True)
        self.assertEqual(marr.shape, cube.shape)
        self.assertEqual(marr.count(), 9*5)   # 9 lats x 5 lons


class TestOsgbGeodeticToWgs84Geodetic(unittest.TestCase):
    """Unit tests for the OSGB36_GCRS_TO_WGS84_GCRS CoordTransformer object."""

    def test_using_lat_lon_tuple(self):
        lon, lat = OSGB36_GCRS_TO_WGS84_GCRS.transform(*hq_osgb36.lonlat)
        npt.assert_allclose([lon, lat], hq_wgs84.lonlat)

    def test_using_lat_lon_arrays(self):
        lons = np.array([hq_osgb36.lon, hq_osgb36.lon+1])
        lats = np.array([hq_osgb36.lat, hq_osgb36.lat+1])
        result = OSGB36_GCRS_TO_WGS84_GCRS.transform(lons, lats)
        lon, lat = result[0][0:2]
        npt.assert_array_equal(result.shape, (2,3))
        npt.assert_allclose([lon, lat], hq_wgs84.lonlat)


class TestOsgbProjectedToWgs84Geodetic(unittest.TestCase):
    """Unit tests for the OSGB36_PCRS_TO_WGS84_GCRS CoordTransformer object."""

    def test_using_x_y_tuple(self):
        lon, lat = OSGB36_PCRS_TO_WGS84_GCRS.transform(*hq_osgb36.xy)
        npt.assert_allclose([lon, lat], hq_wgs84.lonlat)

    def test_using_x_y_arrays(self):
        xx = np.array([hq_osgb36.x, hq_osgb36.x+100])
        yy = np.array([hq_osgb36.y, hq_osgb36.y+100])
        result = OSGB36_PCRS_TO_WGS84_GCRS.transform(xx, yy)
        x, y = result[0][0:2]
        npt.assert_array_equal(result.shape, (2,3))
        npt.assert_allclose([x, y], hq_wgs84.lonlat)


class TestWgs84GeodeticToOsgbGeodetic(unittest.TestCase):
    """Unit tests for the WGS84_GCRS_TO_OSGB36_GCRS CoordTransformer object."""

    def test_using_lat_lon_tuple(self):
        lon, lat = WGS84_GCRS_TO_OSGB36_GCRS.transform(*hq_wgs84.lonlat)
        npt.assert_allclose([lon, lat], hq_osgb36.lonlat)

    def test_using_lat_lon_arrays(self):
        lons = np.array([hq_wgs84.lon, hq_wgs84.lon+1])
        lats = np.array([hq_wgs84.lat, hq_wgs84.lat+1])
        result = WGS84_GCRS_TO_OSGB36_GCRS.transform(lons, lats)
        lon, lat = result[0][0:2]
        npt.assert_array_equal(result.shape, (2,3))
        npt.assert_allclose([lon, lat], hq_osgb36.lonlat)


class TestWgs84GeodeticToOsgbProjected(unittest.TestCase):
    """Unit tests for the WGS84_GCRS_TO_OSGB36_PCRS CoordTransformer object."""

    def test_using_lat_lon_tuple(self):
        x, y = WGS84_GCRS_TO_OSGB36_PCRS.transform(*hq_wgs84.lonlat)
        npt.assert_allclose([x, y], hq_osgb36.xy, atol=0.5)

    def test_using_lat_lon_arrays(self):
        lons = np.array([hq_wgs84.lon, hq_wgs84.lon+1])
        lats = np.array([hq_wgs84.lat, hq_wgs84.lat+1])
        result = WGS84_GCRS_TO_OSGB36_PCRS.transform(lons, lats)
        x, y = result[0][0:2]
        npt.assert_array_equal(result.shape, (2,3))
        npt.assert_allclose([x, y], hq_osgb36.xy, atol=0.5)


if __name__ == '__main__':
    unittest.main()
