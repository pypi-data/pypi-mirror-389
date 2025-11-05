# (C) British Crown Copyright 2017, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Unit tests for the afterburner.misc.stockcubes module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import unittest
import cf_units
import numpy as np
import numpy.testing as npt

from afterburner.misc import stockcubes

CAL_360 = cf_units.CALENDAR_360_DAY
CAL_365 = cf_units.CALENDAR_365_DAY


class TestGeoYX(unittest.TestCase):

    def test_defaults(self):
        cube = stockcubes.geo_yx()
        self.assertEqual(cube.ndim, 2)
        self.assertEqual(cube.shape, (7, 6))
        self.assertEqual(cube.dtype, np.float32)
        self.assertEqual(cube.data[0,0], 0)

    def test_custom_data(self):
        cube = stockcubes.geo_yx(data=1.0)
        self.assertEqual(cube.data[0,0], 1.0)
        cube = stockcubes.geo_yx(data=np.ones(shape=[19, 18]))
        self.assertEqual(cube.shape, (19, 18))

    def test_custom_shape(self):
        cube = stockcubes.geo_yx(shape=(19, 18))
        self.assertEqual(cube.shape, (19, 18))

    def test_custom_dtypes(self):
        cube = stockcubes.geo_yx(dtype='f8')
        self.assertEqual(cube.dtype, np.float64)
        cube = stockcubes.geo_yx(dtype='i4')
        self.assertEqual(cube.dtype, np.int32)

    def test_custom_metadata(self):
        cube = stockcubes.geo_yx(standard_name='surface_temperature',
            var_name='tas', units='K')
        self.assertEqual(cube.standard_name, 'surface_temperature')
        self.assertEqual(cube.var_name, 'tas')
        self.assertEqual(cube.units, 'K')

    def test_circular_longitude(self):
        cube = stockcubes.geo_yx()
        self.assertTrue(cube.coord('longitude').circular)

    def test_offset_longitudes(self):
        cube = stockcubes.geo_yx(start_lon=-180.0, end_lon=180.0)
        loncrd = cube.coord('longitude')
        self.assertEqual(loncrd.points[0], -180.0)
        self.assertEqual(loncrd.points[-1], 120.0)
        self.assertEqual(loncrd.bounds[0,0], -210.0)
        self.assertEqual(loncrd.bounds[-1,1], 150.0)

    def test_clipped_latitudes(self):
        cube = stockcubes.geo_yx()
        latcrd = cube.coord('latitude')
        self.assertLessEqual(latcrd.bounds.max(), 90.0)
        self.assertGreaterEqual(latcrd.bounds.min(), -90.0)

    def test_custom_latitudes(self):
        cube = stockcubes.geo_yx(start_lat=0, end_lat=60, npoints=7)
        latcrd = cube.coord('latitude')
        self.assertEqual(latcrd.points[0], 0.0)
        self.assertEqual(latcrd.points[-1], 60.0)


class TestGeoZYX(unittest.TestCase):

    def test_defaults(self):
        cube = stockcubes.geo_zyx()
        self.assertEqual(cube.ndim, 3)
        self.assertEqual(cube.shape, (5, 7, 6))
        self.assertEqual(cube.dtype, np.float32)
        self.assertEqual(cube.data[0,0,0], 0)
        self.assertEqual(cube.coords()[0].name(), 'pressure')

    def test_custom_data(self):
        cube = stockcubes.geo_zyx(data=1.0)
        self.assertEqual(cube.data[0,0,0], 1.0)
        data = np.arange(0., 50., 10)
        cube = stockcubes.geo_zyx(data=data)
        npt.assert_array_equal(cube.data[:,0,0], data)
        cube = stockcubes.geo_zyx(data=np.ones(shape=[5, 19, 18]))
        self.assertEqual(cube.shape, (5, 19, 18))

    def test_custom_shape(self):
        cube = stockcubes.geo_zyx(shape=(10, 19, 18))
        self.assertEqual(cube.shape, (10, 19, 18))

    def test_custom_zaxis(self):
        cube = stockcubes.geo_zyx(zaxis_type='height')
        self.assertEqual(cube.coords()[0].name(), 'height')
        cube = stockcubes.geo_zyx(zaxis_type='level')
        self.assertEqual(cube.coords()[0].name(), 'model_level_number')

    def test_circular_longitude(self):
        cube = stockcubes.geo_zyx()
        self.assertTrue(cube.coord('longitude').circular)


class TestGeoTYX(unittest.TestCase):

    def test_defaults(self):
        cube = stockcubes.geo_tyx()
        self.assertEqual(cube.ndim, 3)
        self.assertEqual(cube.shape, (12, 7, 6))
        self.assertEqual(cube.dtype, np.float32)
        self.assertEqual(cube.data[0,0,0], 0)
        tcoord = cube.coord('time')
        self.assertEqual(tcoord.name(), 'time')
        self.assertEqual(tcoord.units.calendar, CAL_360)

    def test_custom_data(self):
        cube = stockcubes.geo_tyx(data=1.0)
        self.assertEqual(cube.data[0,0,0], 1.0)
        cube = stockcubes.geo_tyx(data=np.ones(shape=[6, 19, 18]))
        self.assertEqual(cube.shape, (6, 19, 18))

    def test_custom_shape(self):
        cube = stockcubes.geo_tyx(shape=(6, 19, 18))
        self.assertEqual(cube.shape, (6, 19, 18))

    def test_custom_time_units(self):
        tunits = cf_units.Unit('days since 1850-01-01', calendar=CAL_365)
        cube = stockcubes.geo_tyx(tunits=tunits)
        tcoord = cube.coord('time')
        self.assertEqual(tcoord.units.origin, 'days since 1850-01-01')
        self.assertEqual(tcoord.units.calendar, CAL_365)

    def test_circular_longitude(self):
        cube = stockcubes.geo_tyx()
        self.assertTrue(cube.coord('longitude').circular)


class TestGeoTZYX(unittest.TestCase):

    def test_defaults(self):
        cube = stockcubes.geo_tzyx()
        self.assertEqual(cube.ndim, 4)
        self.assertEqual(cube.shape, (12, 5, 7, 6))
        self.assertEqual(cube.dtype, np.float32)
        self.assertEqual(cube.data[0,0,0,0], 0)

    def test_custom_data(self):
        cube = stockcubes.geo_tzyx(data=1.0)
        self.assertEqual(cube.data[0,0,0,0], 1.0)
        cube = stockcubes.geo_tzyx(data=np.ones(shape=[6, 5, 19, 18]))
        self.assertEqual(cube.shape, (6, 5, 19, 18))

    def test_custom_shape(self):
        cube = stockcubes.geo_tzyx(shape=(6, 3, 19, 18))
        self.assertEqual(cube.shape, (6, 3, 19, 18))

    def test_circular_longitude(self):
        cube = stockcubes.geo_tzyx()
        self.assertTrue(cube.coord('longitude').circular)


class TestRotYX(unittest.TestCase):

    def test_defaults(self):
        cube = stockcubes.rot_yx()
        self.assertEqual(cube.ndim, 2)
        self.assertEqual(cube.shape, (7, 6))
        self.assertEqual(cube.dtype, np.float32)
        self.assertEqual(cube.data[0,0], 0)

    def test_coords(self):
        cube = stockcubes.rot_yx()
        dim_coords = cube.coords(dim_coords=True)
        self.assertEqual(dim_coords[0].name(), 'grid_latitude')
        self.assertEqual(dim_coords[1].name(), 'grid_longitude')
        aux_coords = cube.coords(dim_coords=False)
        self.assertEqual(aux_coords[0].name(), 'latitude')
        self.assertEqual(aux_coords[1].name(), 'longitude')

    def test_custom_data(self):
        cube = stockcubes.rot_yx(data=1.0)
        self.assertEqual(cube.data[0,0], 1.0)
        cube = stockcubes.rot_yx(data=np.ones(shape=[19, 18]))
        self.assertEqual(cube.shape, (19, 18))

    def test_custom_shape(self):
        cube = stockcubes.rot_yx(shape=(19, 18))
        self.assertEqual(cube.shape, (19, 18))

    def test_custom_dtypes(self):
        cube = stockcubes.rot_yx(dtype='f8')
        self.assertEqual(cube.dtype, np.float64)
        cube = stockcubes.rot_yx(dtype='i4')
        self.assertEqual(cube.dtype, np.int32)

    def test_custom_domain(self):
        cube = stockcubes.rot_yx(shape=(19, 18), start_lat=-90, end_lat=90,
            start_lon=0, end_lon=180)
        latcrd = cube.coord('grid_latitude')
        loncrd = cube.coord('grid_longitude')
        self.assertEqual(latcrd.points[0], -90.0)
        self.assertEqual(latcrd.points[-1], 90.0)
        self.assertEqual(loncrd.points[0], 0.0)
        self.assertEqual(loncrd.points[-1], 170.0)

    def test_clipped_latitudes(self):
        cube = stockcubes.rot_yx(shape=(19, 18), start_lat=-90, end_lat=90,
            start_lon=0, end_lon=360)
        latcrd = cube.coord('grid_latitude')
        self.assertLessEqual(latcrd.bounds.max(), 90.0)
        self.assertGreaterEqual(latcrd.bounds.min(), -90.0)


class TestRotZYX(unittest.TestCase):

    def test_defaults(self):
        cube = stockcubes.rot_zyx()
        self.assertEqual(cube.ndim, 3)
        self.assertEqual(cube.shape, (5, 7, 6))
        self.assertEqual(cube.dtype, np.float32)
        self.assertEqual(cube.data[0,0,0], 0)
        self.assertEqual(cube.coords()[0].name(), 'pressure')

    def test_custom_data(self):
        cube = stockcubes.rot_zyx(data=1.0)
        self.assertEqual(cube.data[0,0,0], 1.0)
        data = np.arange(0., 50., 10)
        cube = stockcubes.rot_zyx(data=data)
        npt.assert_array_equal(cube.data[:,0,0], data)
        cube = stockcubes.rot_zyx(data=np.ones(shape=[5, 19, 18]))
        self.assertEqual(cube.shape, (5, 19, 18))

    def test_custom_shape(self):
        cube = stockcubes.rot_zyx(shape=(10, 19, 18))
        self.assertEqual(cube.shape, (10, 19, 18))

    def test_custom_dtypes(self):
        cube = stockcubes.rot_zyx(dtype='f8')
        self.assertEqual(cube.dtype, np.float64)
        cube = stockcubes.rot_zyx(dtype='i4')
        self.assertEqual(cube.dtype, np.int32)

    def test_custom_zaxis(self):
        cube = stockcubes.rot_zyx(zaxis_type='height')
        self.assertEqual(cube.coords()[0].name(), 'height')
        cube = stockcubes.rot_zyx(zaxis_type='level')
        self.assertEqual(cube.coords()[0].name(), 'model_level_number')


class TestRotTYX(unittest.TestCase):

    def test_defaults(self):
        cube = stockcubes.rot_tyx()
        self.assertEqual(cube.ndim, 3)
        self.assertEqual(cube.shape, (12, 7, 6))
        self.assertEqual(cube.dtype, np.float32)
        self.assertEqual(cube.data[0,0,0], 0)
        tcoord = cube.coord('time')
        self.assertEqual(tcoord.name(), 'time')
        self.assertEqual(tcoord.units.calendar, CAL_360)

    def test_coords(self):
        cube = stockcubes.rot_tyx()
        dim_coords = cube.coords(dim_coords=True)
        self.assertEqual(dim_coords[1].name(), 'grid_latitude')
        self.assertEqual(dim_coords[2].name(), 'grid_longitude')
        aux_coords = cube.coords(dim_coords=False)
        self.assertEqual(aux_coords[0].name(), 'latitude')
        self.assertEqual(aux_coords[1].name(), 'longitude')

    def test_custom_data(self):
        cube = stockcubes.rot_tyx(data=1.0)
        self.assertEqual(cube.data[0,0,0], 1.0)
        cube = stockcubes.rot_tyx(data=np.ones(shape=[6, 19, 18]))
        self.assertEqual(cube.shape, (6, 19, 18))

    def test_custom_shape(self):
        cube = stockcubes.rot_tyx(shape=(6, 19, 18))
        self.assertEqual(cube.shape, (6, 19, 18))

    def test_custom_time_units(self):
        tunits = cf_units.Unit('days since 1850-01-01', calendar=CAL_365)
        cube = stockcubes.rot_tyx(tunits=tunits)
        tcoord = cube.coord('time')
        self.assertEqual(tcoord.units.origin, 'days since 1850-01-01')
        self.assertEqual(tcoord.units.calendar, CAL_365)


class TestBngYX(unittest.TestCase):

    def test_defaults(self):
        cube = stockcubes.bng_yx()
        self.assertEqual(cube.ndim, 2)
        self.assertEqual(cube.shape, (7, 6))
        self.assertEqual(cube.dtype, np.float32)
        self.assertEqual(cube.data[0,0], 0)

    def test_coords(self):
        cube = stockcubes.bng_yx()
        dim_coords = cube.coords(dim_coords=True)
        self.assertEqual(dim_coords[0].name(), 'projection_y_coordinate')
        self.assertEqual(dim_coords[1].name(), 'projection_x_coordinate')
        aux_coords = cube.coords(dim_coords=False)
        self.assertEqual(len(aux_coords), 0)
        cube = stockcubes.bng_yx(aux_lat_lon=True)
        aux_coords = cube.coords(dim_coords=False)
        self.assertEqual(aux_coords[0].name(), 'latitude')
        self.assertEqual(aux_coords[1].name(), 'longitude')

    def test_custom_data(self):
        cube = stockcubes.bng_yx(data=1.0)
        self.assertEqual(cube.data[0,0], 1.0)
        cube = stockcubes.bng_yx(data=np.ones(shape=[19, 18]))
        self.assertEqual(cube.shape, (19, 18))

    def test_custom_shape(self):
        cube = stockcubes.bng_yx(shape=(19, 18))
        self.assertEqual(cube.shape, (19, 18))

    def test_custom_dtypes(self):
        cube = stockcubes.bng_yx(dtype='f8')
        self.assertEqual(cube.dtype, np.float64)
        cube = stockcubes.bng_yx(dtype='i4')
        self.assertEqual(cube.dtype, np.int32)


class TestBngZYX(unittest.TestCase):

    def test_defaults(self):
        cube = stockcubes.bng_zyx()
        self.assertEqual(cube.ndim, 3)
        self.assertEqual(cube.shape, (5, 7, 6))
        self.assertEqual(cube.dtype, np.float32)
        self.assertEqual(cube.data[0,0,0], 0)

    def test_coords(self):
        cube = stockcubes.bng_zyx()
        dim_coords = cube.coords(dim_coords=True)
        self.assertEqual(dim_coords[0].name(), 'height')
        self.assertEqual(dim_coords[1].name(), 'projection_y_coordinate')
        self.assertEqual(dim_coords[2].name(), 'projection_x_coordinate')
        aux_coords = cube.coords(dim_coords=False)
        self.assertEqual(len(aux_coords), 0)
        cube = stockcubes.bng_zyx(aux_lat_lon=True)
        aux_coords = cube.coords(dim_coords=False)
        self.assertEqual(aux_coords[0].name(), 'latitude')
        self.assertEqual(aux_coords[1].name(), 'longitude')

    def test_custom_data(self):
        cube = stockcubes.bng_zyx(data=1.0)
        self.assertEqual(cube.data[0,0,0], 1.0)
        cube = stockcubes.bng_zyx(data=np.ones(shape=[5, 19, 18]))
        self.assertEqual(cube.shape, (5, 19, 18))

    def test_custom_shape(self):
        cube = stockcubes.bng_zyx(shape=(10, 19, 18))
        self.assertEqual(cube.shape, (10, 19, 18))

    def test_custom_dtypes(self):
        cube = stockcubes.bng_zyx(dtype='f8')
        self.assertEqual(cube.dtype, np.float64)
        cube = stockcubes.bng_yx(dtype='i4')
        self.assertEqual(cube.dtype, np.int32)


class TestBngTYX(unittest.TestCase):

    def test_defaults(self):
        cube = stockcubes.bng_tyx()
        self.assertEqual(cube.ndim, 3)
        self.assertEqual(cube.shape, (12, 7, 6))
        self.assertEqual(cube.dtype, np.float32)
        self.assertEqual(cube.data[0,0,0], 0)
        tcoord = cube.coord('time')
        self.assertEqual(tcoord.name(), 'time')
        self.assertEqual(tcoord.units.calendar, CAL_360)

    def test_coords(self):
        cube = stockcubes.bng_tyx()
        dim_coords = cube.coords(dim_coords=True)
        self.assertEqual(dim_coords[0].name(), 'time')
        self.assertEqual(dim_coords[1].name(), 'projection_y_coordinate')
        self.assertEqual(dim_coords[2].name(), 'projection_x_coordinate')
        cube = stockcubes.bng_tyx(aux_lat_lon=True)
        aux_coords = cube.coords(dim_coords=False)
        self.assertEqual(aux_coords[0].name(), 'latitude')
        self.assertEqual(aux_coords[1].name(), 'longitude')

    def test_custom_data(self):
        cube = stockcubes.bng_tyx(data=1.0)
        self.assertEqual(cube.data[0,0,0], 1.0)
        cube = stockcubes.bng_tyx(data=np.ones(shape=[6, 19, 18]))
        self.assertEqual(cube.shape, (6, 19, 18))

    def test_custom_shape(self):
        cube = stockcubes.bng_tyx(shape=(6, 19, 18))
        self.assertEqual(cube.shape, (6, 19, 18))

    def test_custom_time_units(self):
        tunits = cf_units.Unit('days since 1850-01-01', calendar=CAL_365)
        cube = stockcubes.bng_tyx(tunits=tunits)
        tcoord = cube.coord('time')
        self.assertEqual(tcoord.units.origin, 'days since 1850-01-01')
        self.assertEqual(tcoord.units.calendar, CAL_365)
