# (C) British Crown Copyright 2016-2017, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Unit test for afterburner.utils.cubeutils
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import unittest
import warnings
import cf_units as cfu
import numpy as np
import numpy.testing as npt

import iris
import iris.exceptions
import iris.util
import iris.coords
import iris.tests.stock

from afterburner.utils import cubeutils
from afterburner.utils import dateutils
from afterburner.misc import stockcubes


class TestMakeDimCoordFromAuxCoord(unittest.TestCase):
    """ test make_dim_coord_from_aux_coord() """
    # to create a coordinate it has to have an approved standard_name, hence
    # using forecast_period rather than something more abstract
    def setUp(self):
        self.cube = iris.tests.stock.simple_3d()

    def test_missing_coordinate_raises_exception(self):
        self.assertRaises(iris.exceptions.CoordinateNotFoundError,
            cubeutils.convert_aux_coord_to_dim_coord,
            self.cube, 'forecast_period')

    def test_ignores_existing_dim_coord(self):
        fp_coord = iris.coords.AuxCoord([1, 2], standard_name='forecast_period')
        fp_dim_coord = iris.coords.DimCoord.from_coord(fp_coord)
        self.cube.add_aux_coord(fp_dim_coord, 0)

        cubeutils.convert_aux_coord_to_dim_coord(self.cube, 'forecast_period')
        self.assertIsInstance(self.cube.coord('forecast_period'),
            iris.coords.DimCoord)

    def test_fixes_aux_coord(self):
        fp_coord = iris.coords.AuxCoord([1, 2], standard_name='forecast_period')
        self.cube.add_aux_coord(fp_coord, 0)
        self.assertIsInstance(self.cube.coord('forecast_period'),
            iris.coords.AuxCoord)

        cubeutils.convert_aux_coord_to_dim_coord(self.cube, 'forecast_period')
        self.assertIsInstance(self.cube.coord('forecast_period'),
            iris.coords.DimCoord)


class TestExtractTimeSlice(unittest.TestCase):
    """Tests the cubeutils.extract_time_slice() function."""

    def setUp(self):
        # Obtain a stock test cube. This cube has seven 6-hourly time coords
        # between 2014-12-21 00:00:00 and 2014-12-22 12:00:00. We'll use these
        # for now, although if the stock cube changes in future then we might
        # want to reassign the time coords in this setup method.
        self.cube = iris.tests.stock.realistic_3d()

    def test_contained_time_range(self):
        dt_range = ('2014-12-21T06:00:00', '2014-12-22T06:00:00')
        subcube = cubeutils.extract_time_slice(self.cube, dt_range)
        time = subcube.coord('time')
        self.assertEqual(len(time.points), 4)

        dt_range = ('2014-12-21T06:00', '2014-12-22T09:00')
        subcube = cubeutils.extract_time_slice(self.cube, dt_range)
        time = subcube.coord('time')
        self.assertEqual(len(time.points), 5)

        # Check that DateTimeRange objects work too.
        dt_range = dateutils.DateTimeRange('2014-12-21', '2014-12-22')
        subcube = cubeutils.extract_time_slice(self.cube, dt_range)
        time = subcube.coord('time')
        self.assertEqual(len(time.points), 4)

    def test_overlapping_time_range(self):
        dt_range = ('2014-12-20T12:00:00', '2014-12-21T12:00:00')
        subcube = cubeutils.extract_time_slice(self.cube, dt_range)
        time = subcube.coord('time')
        self.assertEqual(len(time.points), 2)

        # Check that CF-style date-time strings work too.
        dt_range = ('2014-12-21 12:00:00', '2014-12-23 12:00:00')
        subcube = cubeutils.extract_time_slice(self.cube, dt_range)
        time = subcube.coord('time')
        self.assertEqual(len(time.points), 5)

    def test_disjoint_time_range(self):
        dt_range = ('2014-12-10T12:00:00', '2014-12-20T12:00:00')
        subcube = cubeutils.extract_time_slice(self.cube, dt_range)
        self.assertEqual(subcube, None)

        dt_range = dateutils.DateTimeRange('2015-12-21', '2015-12-22')
        subcube = cubeutils.extract_time_slice(self.cube, dt_range)
        self.assertEqual(subcube, None)

    def test_invalid_coord_name(self):
        dt_range = dateutils.DateTimeRange('2014-12-21', '2014-12-22')
        self.assertRaises(iris.exceptions.CoordinateNotFoundError,
            cubeutils.extract_time_slice, self.cube, dt_range, coord_name='tim')

    def test_invalid_time_range_argument(self):
        dt_range = '2014-12-21, 2014-12-22'
        self.assertRaises(ValueError, cubeutils.extract_time_slice, self.cube, dt_range)


class TestIsScalarCoord(unittest.TestCase):
    """Tests the cubeutils.is_scalar_coord() function."""

    def test_with_missing_coord(self):
        cube = stockcubes.geo_tyx()
        self.assertIsNone(cubeutils.is_scalar_coord(cube, 'absent'))

    def test_with_dim_coord(self):
        cube = stockcubes.geo_tyx()
        self.assertFalse(cubeutils.is_scalar_coord(cube, 'time'))

    def test_with_aux_coord(self):
        cube = stockcubes.geo_tyx()
        iris.util.demote_dim_coord_to_aux_coord(cube, 'time')
        self.assertFalse(cubeutils.is_scalar_coord(cube, 'time'))

    def test_with_scalar_coord(self):
        cube = stockcubes.geo_tyx()[0]   # obtain first time slice
        self.assertTrue(cubeutils.is_scalar_coord(cube, 'time'))


class TestIsCircular(unittest.TestCase):
    """Tests the cubeutils.is_circular() function."""

    def test_standard_longitudes(self):
        pts_list = [
            np.arange(0, 360.0, 5.0),
            np.arange(0, 360.0, 10.0),
            np.arange(0, 360.0, 30.0)
        ]
        for pts in pts_list:
            self.assertTrue(cubeutils.is_circular(pts, 360))
            crd = iris.coords.DimCoord(pts, standard_name='longitude', units='degrees_east')
            crd.guess_bounds()
            self.assertTrue(cubeutils.is_circular(pts, 360, bounds=crd.bounds))

    def test_shifted_longitudes(self):
        pts_list = [
            np.arange(-90, 270.0, 5.0),
            np.arange(-180, 180.0, 10.0),
            np.arange(90, 450.0, 30.0)
        ]
        for pts in pts_list:
            self.assertTrue(cubeutils.is_circular(pts, 360))
            crd = iris.coords.DimCoord(pts, standard_name='longitude', units='degrees_east')
            crd.guess_bounds()
            self.assertTrue(cubeutils.is_circular(pts, 360, bounds=crd.bounds))

    def test_non_circular_longitudes(self):
        pts_list = [
            np.arange(90, 270.0, 5.0),
            np.arange(-90, 90.0, 10.0),
            np.arange(-180, 0.0, 30.0)
        ]
        for pts in pts_list:
            self.assertFalse(cubeutils.is_circular(pts, 360))
            crd = iris.coords.DimCoord(pts, standard_name='longitude', units='degrees_east')
            crd.guess_bounds()
            self.assertFalse(cubeutils.is_circular(pts, 360, bounds=crd.bounds))

    def test_irregular_longitudes(self):
        pts = np.array([0.0, 90.00001, 179.99999, 270.00001, 359.99999])
        self.assertTrue(cubeutils.is_circular(pts[:-1], 360))
        self.assertTrue(cubeutils.is_circular(None, 360, bounds=pts[[0,-1]]))

        pts = np.array([0.0, 90.001, 179.999, 270.001, 359.999])
        self.assertTrue(cubeutils.is_circular(pts[:-1], 360))
        self.assertTrue(cubeutils.is_circular(None, 360, bounds=pts[[0,-1]]))
        self.assertFalse(cubeutils.is_circular(None, 360, bounds=pts[[0,-1]], rtol=1e-6))

        pts = np.array([-180.00001, -90.00001, 0.0, 89.99999, 179.99999])
        self.assertTrue(cubeutils.is_circular(pts[:-1], 360))
        self.assertTrue(cubeutils.is_circular(None, 360, bounds=pts[[0,-1]]))


class TestHasGlobalDomain(unittest.TestCase):
    """Tests the cubeutils.has_global_domain() function."""

    def test_standard_global_domain(self):
        cube = stockcubes.geo_yx()
        self.assertTrue(cubeutils.has_global_domain(cube))

    def test_global_domain_with_lon_shifts(self):
        cube = stockcubes.geo_yx()
        loncrd0 = cube.coord('longitude')

        # adjust longitudes to range [-90, 270)
        loncrd1 = loncrd0.copy(points=loncrd0.points-90, bounds=None)
        cube1 = cube.copy()
        cube1.remove_coord('longitude')
        cube1.add_dim_coord(loncrd1, 1)
        # test without bounds
        self.assertTrue(cubeutils.has_global_domain(cube1))
        # test with bounds
        loncrd1.guess_bounds()
        self.assertTrue(cubeutils.has_global_domain(cube1))

        # adjust longitudes to range [-180, 180)
        loncrd1 = loncrd0.copy(points=loncrd0.points-180, bounds=None)
        cube1 = cube.copy()
        cube1.remove_coord('longitude')
        cube1.add_dim_coord(loncrd1, 1)
        # test without bounds
        self.assertTrue(cubeutils.has_global_domain(cube1))
        # test with bounds
        loncrd1.guess_bounds()
        self.assertTrue(cubeutils.has_global_domain(cube1))

    def test_limited_latitude_domain(self):
        cube = stockcubes.geo_yx()
        cube1 = cube.intersection(latitude=[-60, 60])
        self.assertFalse(cubeutils.has_global_domain(cube1))
        cube1.coord('latitude').bounds = None
        self.assertFalse(cubeutils.has_global_domain(cube1))

    def test_limited_longitude_domain(self):
        cube = stockcubes.geo_yx()
        cube1 = cube.intersection(longitude=[90, 270])
        self.assertFalse(cubeutils.has_global_domain(cube1))
        cube1.coord('longitude').bounds = None
        self.assertFalse(cubeutils.has_global_domain(cube1))

    def test_limited_lat_lon_domain(self):
        cube = stockcubes.geo_yx()
        cube1 = cube.intersection(latitude=[-60, 60], longitude=[90, 270])
        self.assertFalse(cubeutils.has_global_domain(cube1))
        cube1.coord('latitude').bounds = None
        cube1.coord('longitude').bounds = None
        self.assertFalse(cubeutils.has_global_domain(cube1))

    def test_rotated_pole_domain(self):
        cube = stockcubes.rot_yx()
        self.assertFalse(cubeutils.has_global_domain(cube))

    def test_global_scalar_coords(self):
        cube = stockcubes.geo_yx()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube1 = cube.collapsed(['latitude', 'longitude'], iris.analysis.MEAN)
        self.assertTrue(cubeutils.has_global_domain(cube1))
        cube1.coord('latitude').bounds = None
        cube1.coord('longitude').bounds = None
        self.assertEqual(cubeutils.has_global_domain(cube1), None)

    def test_nonglobal_scalar_coords(self):
        cube = stockcubes.geo_yx()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube1 = cube.collapsed(['latitude', 'longitude'], iris.analysis.MEAN)
        latcrd = cube1.coord('latitude')
        loncrd = cube1.coord('longitude')
        self.assertEqual(len(latcrd.points), 1)
        self.assertEqual(len(loncrd.points), 1)
        # set non-global latitudes
        latbnds = np.array([[-80.,80.]])
        cube1.remove_coord('latitude')
        cube1.add_aux_coord(latcrd.copy(points=latcrd.points, bounds=latbnds))
        self.assertFalse(cubeutils.has_global_domain(cube1))
        # set non-global longitudes
        lonbnds = np.array([[30.,330.]])
        cube1.remove_coord('latitude')
        cube1.add_aux_coord(latcrd)
        cube1.remove_coord('longitude')
        cube1.add_aux_coord(loncrd.copy(points=loncrd.points, bounds=lonbnds))
        self.assertFalse(cubeutils.has_global_domain(cube1))


class TestIsMeanOfAllTimeSteps(unittest.TestCase):
    """ test is_mean_of_all_time_steps() """
    def setUp(self):
        self.cube = iris.tests.stock.simple_1d()

    def test_mean(self):
        new_cm = iris.coords.CellMethod('mean', ('time',), ('1 hour',))
        self.cube.cell_methods = (new_cm,)
        ret_val = cubeutils.is_mean_of_all_time_steps(self.cube)
        self.assertTrue(ret_val)

    def test_diurnal_cycle_diagnostic(self):
        new_cm = iris.coords.CellMethod('mean', ('time',), ('24 hour',))
        self.cube.cell_methods = (new_cm,)
        ret_val = cubeutils.is_mean_of_all_time_steps(self.cube)
        self.assertFalse(ret_val)

    def test_not_mean(self):
        new_cm = iris.coords.CellMethod('maximum', ('time',), ('1 hour',))
        self.cube.cell_methods = (new_cm,)
        ret_val = cubeutils.is_mean_of_all_time_steps(self.cube)
        self.assertFalse(ret_val)

    def test_not_time_mean(self):
        new_cm = iris.coords.CellMethod('mean', ('level',))
        self.cube.cell_methods = (new_cm,)
        ret_val = cubeutils.is_mean_of_all_time_steps(self.cube)
        self.assertFalse(ret_val)

    def test_no_cell_methods(self):
        self.cube.cell_methods = tuple()
        ret_val = cubeutils.is_mean_of_all_time_steps(self.cube)
        self.assertFalse(ret_val)


class TestIsTimeMean(unittest.TestCase):
    """ test is_time_mean() """
    def setUp(self):
        self.cube = iris.tests.stock.simple_1d()

    def test_mean(self):
        new_cm = iris.coords.CellMethod('mean', ('time',))
        self.cube.cell_methods = (new_cm,)
        ret_val = cubeutils.is_time_mean(self.cube)
        self.assertTrue(ret_val)

    def test_not_mean(self):
        new_cm = iris.coords.CellMethod('maximum', ('time',))
        self.cube.cell_methods = (new_cm,)
        ret_val = cubeutils.is_time_mean(self.cube)
        self.assertFalse(ret_val)

    def test_no_cell_methods(self):
        self.cube.cell_methods = tuple()
        ret_val = cubeutils.is_time_mean(self.cube)
        self.assertFalse(ret_val)


class TestIsTimeMaximum(unittest.TestCase):
    """ test is_time_maximum() """
    def setUp(self):
        self.cube = iris.tests.stock.simple_1d()

    def test_maximum(self):
        new_cm = iris.coords.CellMethod('maximum', ('time',), ('1 hour',))
        self.cube.cell_methods = (new_cm,)
        ret_val = cubeutils.is_time_maximum(self.cube)
        self.assertTrue(ret_val)

    def test_not_maximum(self):
        new_cm = iris.coords.CellMethod('mean', ('time',), ('1 hour',))
        self.cube.cell_methods = (new_cm,)
        ret_val = cubeutils.is_time_maximum(self.cube)
        self.assertFalse(ret_val)

    def test_no_cell_methods(self):
        self.cube.cell_methods = tuple()
        ret_val = cubeutils.is_time_maximum(self.cube)
        self.assertFalse(ret_val)


class TestIsTimeMinimum(unittest.TestCase):
    """ test is_time_minimum() """
    def setUp(self):
        self.cube = iris.tests.stock.simple_1d()

    def test_minimum(self):
        new_cm = iris.coords.CellMethod('minimum', ('time',), ('1 hour',))
        self.cube.cell_methods = (new_cm,)
        ret_val = cubeutils.is_time_minimum(self.cube)
        self.assertTrue(ret_val)

    def test_not_minimum(self):
        new_cm = iris.coords.CellMethod('maximum', ('time',), ('1 hour',))
        self.cube.cell_methods = (new_cm,)
        ret_val = cubeutils.is_time_minimum(self.cube)
        self.assertFalse(ret_val)

    def test_no_cell_methods(self):
        self.cube.cell_methods = tuple()
        ret_val = cubeutils.is_time_minimum(self.cube)
        self.assertFalse(ret_val)


class TestCheckCellMethod(unittest.TestCase):
    """ test _check_cell_method() """
    def setUp(self):
        self.cube = iris.tests.stock.simple_1d()

    def test_true(self):
        new_cm = iris.coords.CellMethod('mean', ('time',), ('1 hour',))
        self.cube.cell_methods = (new_cm,)
        ret_val = cubeutils._check_cell_method(self.cube, 'mean')
        self.assertTrue(ret_val)

    def test_false(self):
        new_cm = iris.coords.CellMethod('mean', ('time',), ('1 hour',))
        self.cube.cell_methods = (new_cm,)
        ret_val = cubeutils._check_cell_method(self.cube, 'maximum')
        self.assertFalse(ret_val)

    def test_no_cell_method(self):
        self.cube.cell_methods = tuple()
        ret_val = cubeutils._check_cell_method(self.cube, 'maximum')
        self.assertFalse(ret_val)


class TestCellMethodCubeFunc(unittest.TestCase):
    """Tests the make_cell_method_cube_func() function."""

    def test_time_mean(self):
        cube1 = stockcubes.geo_yx()
        cube2 = stockcubes.geo_tyx()
        cube3 = stockcubes.geo_tzyx()
        cubelist = iris.cube.CubeList([cube1, cube2, cube3])

        callback = cubeutils.make_cell_method_cube_func('mean', 'time')
        constraint = iris.Constraint(cube_func=callback)
        cubes = cubelist.extract(constraint)
        self.assertEqual(len(cubes), 2)

        callback = cubeutils.make_cell_method_cube_func('mean', 'height')
        constraint = iris.Constraint(cube_func=callback)
        cubes = cubelist.extract(constraint)
        self.assertEqual(len(cubes), 0)

    def test_time_min(self):
        cube1 = stockcubes.geo_tyx()
        cube2 = stockcubes.geo_tzyx()
        cubelist = iris.cube.CubeList([cube1, cube2])

        callback = cubeutils.make_cell_method_cube_func('minimum', 'time')
        constraint = iris.Constraint(cube_func=callback)
        cubes = cubelist.extract(constraint)
        self.assertEqual(len(cubes), 0)

        cm2 = iris.coords.CellMethod('minimum', ('time',))
        cube2.cell_methods = (cm2,)
        cubes = cubelist.extract(constraint)
        self.assertEqual(len(cubes), 1)

    def test_time_max(self):
        cube1 = stockcubes.geo_tyx()
        cube2 = stockcubes.geo_tzyx()
        cubelist = iris.cube.CubeList([cube1, cube2])

        callback = cubeutils.make_cell_method_cube_func('maximum', 'time')
        constraint = iris.Constraint(cube_func=callback)
        cubes = cubelist.extract(constraint)
        self.assertEqual(len(cubes), 0)

        cm2 = iris.coords.CellMethod('maximum', ('time',))
        cube2.cell_methods = (cm2,)
        cubes = cubelist.extract(constraint)
        self.assertEqual(len(cubes), 1)

    def test_time_intervals(self):
        cube1 = stockcubes.geo_tyx()
        cm1 = iris.coords.CellMethod('mean', ('time',), ('1 hour',))
        cube1.cell_methods = (cm1,)

        cube2 = stockcubes.geo_tzyx()
        cm2 = iris.coords.CellMethod('mean', ('time',), ('24 hour',))
        cube2.cell_methods = (cm2,)
        cubelist = iris.cube.CubeList([cube1, cube2])

        callback = cubeutils.make_cell_method_cube_func('mean', 'time')
        constraint = iris.Constraint(cube_func=callback)
        cubes = cubelist.extract(constraint)
        self.assertEqual(len(cubes), 2)

        callback = cubeutils.make_cell_method_cube_func('mean', 'time', interval='1 hour')
        constraint = iris.Constraint(cube_func=callback)
        cubes = cubelist.extract(constraint)
        self.assertEqual(len(cubes), 1)

        callback = cubeutils.make_cell_method_cube_func('mean', 'time', interval='24 hour')
        constraint = iris.Constraint(cube_func=callback)
        cubes = cubelist.extract(constraint)
        self.assertEqual(len(cubes), 1)

        callback = cubeutils.make_cell_method_cube_func('mean', 'time', interval='6 hour')
        constraint = iris.Constraint(cube_func=callback)
        cubes = cubelist.extract(constraint)
        self.assertEqual(len(cubes), 0)

class TestDataShapesEqual(unittest.TestCase):
    """Tests the cubeutils.data_shapes_equal() function."""

    def setUp(self):
        self.cube1 = iris.tests.stock.simple_1d()
        self.cube2 = iris.tests.stock.simple_3d()
        self.cube3 = iris.tests.stock.realistic_3d()

    def test_equal(self):
        cubes = iris.cube.CubeList([self.cube1])
        self.assertTrue(cubeutils.data_shapes_equal(cubes))
        cubes.append(self.cube1)
        self.assertTrue(cubeutils.data_shapes_equal(cubes))

    def test_unequal(self):
        cubes = iris.cube.CubeList([self.cube1, self.cube2])
        self.assertFalse(cubeutils.data_shapes_equal(cubes))
        cubes = iris.cube.CubeList([self.cube2, self.cube3])
        self.assertFalse(cubeutils.data_shapes_equal(cubes))

    def test_bad_input(self):
        cubes = iris.cube.CubeList()
        self.assertRaises(ValueError, cubeutils.data_shapes_equal, cubes)
        self.assertRaises(TypeError, cubeutils.data_shapes_equal, self.cube1)


class TestTimeAxesEqual(unittest.TestCase):
    """Tests the cubeutils.are_time_axes_equal() function."""

    def test_equal(self):
        cube1 = stockcubes.geo_tyx()
        cube2 = stockcubes.geo_tyx()
        cubelist = iris.cube.CubeList([cube1, cube2])
        self.assertTrue(cubeutils.are_time_axes_equal(cubelist))

    def test_equal_dates_different_time_coords(self):
        cube1 = stockcubes.geo_tyx()
        cube2 = stockcubes.geo_tyx()
        tcoord1 = cube1.coord('time')
        tpts = tcoord1.points + 360
        tunits = cfu.Unit('days since 1969-01-01', calendar='360_day')
        tcoord2 = iris.coords.DimCoord(tpts, standard_name='time', units=tunits)
        tcoord2.guess_bounds()
        cube2.remove_coord('time')
        cube2.add_dim_coord(tcoord2, 0)
        cubelist = iris.cube.CubeList([cube1, cube2])
        self.assertTrue(cubeutils.are_time_axes_equal(cubelist))

    def test_unequal_time_units(self):
        cube1 = stockcubes.geo_tyx()
        tunits = cfu.Unit('days since 1971-01-01', calendar='360_day')
        cube2 = stockcubes.geo_tyx(tunits=tunits)
        cubelist = iris.cube.CubeList([cube1, cube2])
        self.assertFalse(cubeutils.are_time_axes_equal(cubelist))

    def test_unequal_calendar(self):
        cube1 = stockcubes.geo_tyx()
        tunits = cfu.Unit('days since 1970-01-01', calendar='standard')
        cube2 = stockcubes.geo_tyx(tunits=tunits)
        cubelist = iris.cube.CubeList([cube1, cube2])
        self.assertFalse(cubeutils.are_time_axes_equal(cubelist))

    def test_scalar_coord(self):
        cube1 = stockcubes.geo_tyx()
        cube2 = stockcubes.geo_yx()
        tunits = cfu.Unit('days since 1970-01-01', calendar='standard')
        tcoord2 = iris.coords.DimCoord(0, standard_name='time', units=tunits)
        cube2.add_aux_coord(tcoord2)
        cubelist = iris.cube.CubeList([cube1, cube2])
        self.assertFalse(cubeutils.are_time_axes_equal(cubelist))

    def test_no_time_axis(self):
        cube1 = stockcubes.geo_tyx()
        cube2 = stockcubes.geo_yx()
        cubelist = iris.cube.CubeList([cube1, cube2])
        self.assertRaises(iris.exceptions.CoordinateNotFoundError,
            cubeutils.are_time_axes_equal, cubelist)


class TestAugmentCube(unittest.TestCase):
    """Tests the cubeutils.augment_cube_class() function using cube objects."""

    def test_stash_code_property(self):
        cube3d = iris.tests.stock.realistic_3d()
        self.assertRaises(AttributeError, getattr, cube3d, 'stash_code')
        cubeutils.augment_cube_class(cube3d)
        self.assertEqual(cube3d.stash_code(), None)
        cube3d.attributes['STASH'] = 'm01s02i345'
        self.assertEqual(cube3d.stash_code(), 'm01s02i345')
        # verify that other cubes have not been augmented
        cube1d = iris.tests.stock.simple_1d()
        self.assertRaises(AttributeError, getattr, cube1d, 'stash_code')

    def test_meaning_period_property(self):
        cube3d = iris.tests.stock.realistic_3d()
        self.assertRaises(AttributeError, getattr, cube3d, 'meaning_period')
        cubeutils.augment_cube_class(cube3d)
        self.assertEqual(cube3d.meaning_period(), None)
        cm = iris.coords.CellMethod(method='mean', coords=('time',))
        cube3d.add_cell_method(cm)
        self.assertEqual(cube3d.meaning_period(), '6h')
        # verify that other cubes have not been augmented
        cube1d = iris.tests.stock.simple_1d()
        self.assertRaises(AttributeError, getattr, cube1d, 'meaning_period')


class TestAugmentCubeClass(unittest.TestCase):
    """Tests the cubeutils.augment_cube_class() function."""

    def test_stash_code_property(self):
        cube3d = iris.tests.stock.realistic_3d()
        cubeutils.augment_cube_class()
        self.assertEqual(cube3d.stash_code(), None)
        cube3d.attributes['STASH'] = 'm01s02i345'
        self.assertEqual(cube3d.stash_code(), 'm01s02i345')
        cube1d = iris.tests.stock.simple_1d()
        self.assertEqual(cube1d.stash_code(), None)

    def test_meaning_period_property(self):
        cube3d = iris.tests.stock.realistic_3d()
        cubeutils.augment_cube_class()
        self.assertEqual(cube3d.meaning_period(), None)
        cm = iris.coords.CellMethod(method='mean', coords=('time',))
        cube3d.add_cell_method(cm)
        self.assertEqual(cube3d.meaning_period(), '6h')


class TestRebaseTimeCoords(unittest.TestCase):

    def test_gregorian(self):
        c1u = cfu.Unit("days since 2001-01-01 0:0:0")
        c1 = iris.coords.DimCoord(0.0, standard_name="time", units=c1u)
        c2u = cfu.Unit("days since 2002-01-01 0:0:0")
        c2 = iris.coords.DimCoord(0.0, standard_name="time", units=c2u)
        c3u = cfu.Unit("days since 2003-01-01 0:0:0")
        c3 = iris.coords.DimCoord(0.0, standard_name="time", units=c3u)
        clist = [c3,c1,c2]   # intentionally in non-chronological order

        cubeutils.rebase_time_coords(clist)
        self.assertEqual(c2.units.origin, c1u.origin)
        self.assertEqual(c2.points[0], 365)
        self.assertEqual(c3.units.origin, c1u.origin)
        self.assertEqual(c3.points[0], 730)

    def test_cal360(self):
        c1u = cfu.Unit("days since 2001-01-01 0:0:0", calendar="360_day")
        c1 = iris.coords.DimCoord(0.0, standard_name="time", units=c1u)
        c2u = cfu.Unit("days since 2002-01-01 0:0:0", calendar="360_day")
        c2 = iris.coords.DimCoord(0.0, standard_name="time", units=c2u)
        c3u = cfu.Unit("days since 2003-01-01 0:0:0", calendar="360_day")
        c3 = iris.coords.DimCoord(0.0, standard_name="time", units=c3u)
        clist = [c3,c1,c2]   # intentionally in non-chronological order

        cubeutils.rebase_time_coords(clist)
        self.assertEqual(c2.units.origin, c1u.origin)
        self.assertEqual(c2.points[0], 360)
        self.assertEqual(c3.units.origin, c1u.origin)
        self.assertEqual(c3.points[0], 720)

    def test_with_mixed_base_units(self):
        c1u = cfu.Unit("days since 2001-01-01 0:0:0")
        c1 = iris.coords.DimCoord(0.0, standard_name="time", units=c1u)
        c2u = cfu.Unit("hours since 2002-01-01 0:0:0")
        c2 = iris.coords.DimCoord(0.0, standard_name="time", units=c2u)
        c3u = cfu.Unit("seconds since 2003-01-01 0:0:0")
        c3 = iris.coords.DimCoord(0.0, standard_name="time", units=c3u)
        clist = [c3,c1,c2]   # intentionally in non-chronological order

        cubeutils.rebase_time_coords(clist)
        #self.assertEqual(c2.units.origin, c1u.origin)
        self.assertEqual(c2.points[0], 365 * 24)         # hours since 2001-1-1
        #self.assertEqual(c3.units.origin, c1u.origin)
        self.assertEqual(c3.points[0], 730 * 24 * 3600)  # secs since 2001-1-1

    def test_with_target_units(self):
        c1u = cfu.Unit("days since 2001-01-01 0:0:0")
        c1 = iris.coords.DimCoord(0.0, standard_name="time", units=c1u)
        c2u = cfu.Unit("days since 2002-01-01 0:0:0")
        c2 = iris.coords.DimCoord(0.0, standard_name="time", units=c2u)
        c3u = cfu.Unit("days since 2003-01-01 0:0:0")
        c3 = iris.coords.DimCoord(0.0, standard_name="time", units=c3u)
        clist = [c3,c1,c2]   # intentionally in non-chronological order

        tu = "days since 1990-01-01 0:0:0"
        cubeutils.rebase_time_coords(clist, target_unit=tu)
        self.assertEqual(c1.units.origin, tu)
        self.assertEqual(c1.points[0], 4018)
        self.assertEqual(c2.units.origin, tu)
        self.assertEqual(c2.points[0], 4383)
        self.assertEqual(c3.units.origin, tu)
        self.assertEqual(c3.points[0], 4748)

        tu = cfu.Unit("days since 1990-01-01 0:0:0", calendar="gregorian")
        cubeutils.rebase_time_coords(clist, target_unit=tu)
        self.assertEqual(c1.units.origin, tu.origin)
        self.assertEqual(c2.units.origin, tu.origin)
        self.assertEqual(c3.units.origin, tu.origin)


    def test_bounds(self):
        values = [0.0, 1.0, 2.0]
        c1u = cfu.Unit("days since 2001-01-01 0:0:0", calendar="360_day")
        c1 = iris.coords.DimCoord(values, standard_name="time", units=c1u)
        c1.guess_bounds()
        c2u = cfu.Unit("days since 2002-01-01 0:0:0", calendar="360_day")
        c2 = iris.coords.DimCoord(values, standard_name="time", units=c2u)
        c2.guess_bounds()
        c3u = cfu.Unit("days since 2003-01-01 0:0:0", calendar="360_day")
        c3 = iris.coords.DimCoord(values, standard_name="time", units=c3u)
        c3.guess_bounds()
        clist = [c3,c1,c2]   # intentionally in non-chronological order

        cubeutils.rebase_time_coords(clist)
        npt.assert_array_equal(c1.bounds[0], np.array([-0.5, 0.5]))
        self.assertEqual(c2.units.origin, c1u.origin)
        npt.assert_array_equal(c2.bounds[0], np.array([359.5, 360.5]))
        self.assertEqual(c3.units.origin, c1u.origin)
        npt.assert_array_equal(c3.bounds[0], np.array([719.5, 720.5]))

    def test_with_incompatible_units(self):
        c1u = cfu.Unit("days since 2001-01-01 0:0:0", calendar="gregorian")
        c1 = iris.coords.DimCoord(0.0, standard_name="time", units=c1u)
        c2u = cfu.Unit("days since 2002-01-01 0:0:0", calendar="360_day")
        c2 = iris.coords.DimCoord(0.0, standard_name="time", units=c2u)
        c3 = iris.coords.DimCoord(0.0, standard_name="time", units='days')

        with self.assertRaises(ValueError):
            cubeutils.rebase_time_coords([c1, c2])
            cubeutils.rebase_time_coords([c1, c3])

    def test_with_invalid_target_units(self):
        c1u = cfu.Unit("days since 2001-01-01 0:0:0")
        c1 = iris.coords.DimCoord(0.0, standard_name="time", units=c1u)
        c2u = cfu.Unit("days since 2002-01-01 0:0:0")
        c2 = iris.coords.DimCoord(0.0, standard_name="time", units=c2u)

        with self.assertRaises(ValueError):
            cubeutils.rebase_time_coords([c1, c2], target_unit='days')
            tu = cfu.Unit("days since 1990-01-01 0:0:0", calendar="365_day")
            cubeutils.rebase_time_coords([c1, c2], target_unit=tu)


if __name__ == '__main__':
    unittest.main()
