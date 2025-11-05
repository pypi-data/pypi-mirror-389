# (C) British Crown Copyright 2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Test the afterburner.apps.model_monitor.ModelMonitor application using simple 3D
diagnostics.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import os
import sys
import shutil
import tempfile
import unittest
import logging

try:
    # python3
    from unittest import mock
except ImportError:
    # python2
    import mock

import numpy as np
import cf_units
import iris
from iris.fileformats.pp import STASH

try:
    from afterburner.apps.model_monitor import ModelMonitor
    got_rose_config = True
except ImportError:
    got_rose_config = False


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestVerticalLevels(unittest.TestCase):
    """Test correct handling of vertical levels and pseudo-levels."""

    def setUp(self):

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_dir=$RUNTIME_DIR/caches/varsplit
            output_dir=$RUNTIME_DIR/cmm

            [namelist:models(anqjm)]
            enable=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(soilmoist)]
            enable=true
            level=2
            stashcode=m01s08i223
        """
        self.runtime_dir = tempfile.mkdtemp()
        os.environ['RUNTIME_DIR'] = self.runtime_dir

        fh, self.cfg_file = tempfile.mkstemp(suffix='.conf', dir=self.runtime_dir)
        with open(self.cfg_file, 'w') as fh:
            fh.writelines([line.strip()+'\n' for line in app_config.split('\n')])

        patch = mock.patch('afterburner.apps.model_monitor.ModelMonitor._load_latest_model_data')
        self.mock_load_model_data = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.apps.model_monitor.ModelMonitor._update_diag_data_cache')
        self.mock_update_cache = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.apps.model_monitor.ModelMonitor._generate_plot_images')
        self.mock_gen_images = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.apps.model_monitor.ModelMonitor._generate_html_page')
        self.mock_gen_html = patch.start()
        self.addCleanup(patch.stop)

        # Disable logging.
        lgr = logging.getLogger('afterburner.apps')
        self.log_level = lgr.level
        lgr.level = 100

    def tearDown(self):
        if os.path.isdir(self.runtime_dir):
            shutil.rmtree(self.runtime_dir, ignore_errors=True)

        # Re-enable logging
        lgr = logging.getLogger('afterburner.apps')
        lgr.level = self.log_level

    def test_diag_with_levels(self):
        test_cube = _create_4d_cube_with_named_zaxis(zaxis_name='level')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor(args)
        app.run()

        self.mock_update_cache.assert_called_once()
        cube = self.mock_update_cache.call_args[0][0]
        self.assertTrue(cube is not None)
        self.assertEqual(cube.ndim, 1)
        self.assertEqual(cube.var_name, test_cube.var_name)

    def test_diag_with_model_levels(self):
        test_cube = _create_4d_cube_with_named_zaxis(zaxis_name='model_level')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor(args)
        app.run()

        self.mock_update_cache.assert_called_once()
        cube = self.mock_update_cache.call_args[0][0]
        self.assertTrue(cube is not None)
        self.assertEqual(cube.ndim, 1)
        self.assertEqual(cube.var_name, test_cube.var_name)

    def test_diag_with_model_level_numbers(self):
        test_cube = _create_4d_cube_with_named_zaxis(zaxis_name='model_level_number')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor(args)
        app.run()

        self.mock_update_cache.assert_called_once()
        cube = self.mock_update_cache.call_args[0][0]
        self.assertTrue(cube is not None)
        self.assertEqual(cube.ndim, 1)
        self.assertEqual(cube.var_name, test_cube.var_name)

    def test_diag_with_pseudo_levels(self):
        test_cube = _create_4d_cube_with_named_zaxis(zaxis_name='pseudo_level')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor(args)
        app.run()

        self.mock_update_cache.assert_called_once()
        cube = self.mock_update_cache.call_args[0][0]
        self.assertTrue(cube is not None)
        self.assertEqual(cube.ndim, 1)
        self.assertEqual(cube.var_name, test_cube.var_name)


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestPressureLevels(unittest.TestCase):
    """Test correct handling of pressure levels."""

    def setUp(self):

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_dir=$RUNTIME_DIR/caches/varsplit
            output_dir=$RUNTIME_DIR/cmm

            [namelist:models(anqjm)]
            enable=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(uwind)]
            enable=true
            level=250
            stashcode=m01s30i201
        """
        self.runtime_dir = tempfile.mkdtemp()
        os.environ['RUNTIME_DIR'] = self.runtime_dir

        fh, self.cfg_file = tempfile.mkstemp(suffix='.conf', dir=self.runtime_dir)
        with open(self.cfg_file, 'w') as fh:
            fh.writelines([line.strip()+'\n' for line in app_config.split('\n')])

        patch = mock.patch('afterburner.apps.ModelMonitor._load_latest_model_data')
        self.mock_load_model_data = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.apps.ModelMonitor._update_diag_data_cache')
        self.mock_update_cache = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.apps.ModelMonitor._generate_plot_images')
        self.mock_gen_images = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.apps.ModelMonitor._generate_html_page')
        self.mock_gen_html = patch.start()
        self.addCleanup(patch.stop)

        # Disable logging.
        lgr = logging.getLogger('afterburner.apps')
        self.log_level = lgr.level
        lgr.level = 100

    def tearDown(self):
        if os.path.isdir(self.runtime_dir):
            shutil.rmtree(self.runtime_dir, ignore_errors=True)

        # Re-enable logging
        lgr = logging.getLogger('afterburner.apps')
        lgr.level = self.log_level

    def test_diag_with_levels(self):
        test_cube = _create_4d_cube_with_pressure_axis()
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor(args)
        app.run()

        self.mock_update_cache.assert_called_once()
        cube = self.mock_update_cache.call_args[0][0]
        self.assertTrue(cube is not None)
        self.assertEqual(cube.ndim, 1)
        self.assertEqual(cube.var_name, test_cube.var_name)


def _create_4d_cube_with_named_zaxis(zaxis_name='level', stash_code='m01s08i223'):

    times = np.arange(0., 360., 30.)
    tunits = cf_units.Unit('days since 1970-01-01', calendar='360_day')
    tcoord = iris.coords.DimCoord(times, standard_name='time', units=tunits)

    levels = np.arange(1, 5)
    zcoord = iris.coords.DimCoord(levels, long_name=zaxis_name, units='1')
    try:
        zcoord.standard_name = zaxis_name
    except:
        pass

    lats = np.arange(-90., 91., 30.)
    ycoord = iris.coords.DimCoord(lats, standard_name='latitude', units='degrees_north')
    ycoord.guess_bounds()
    ycoord.coord_system = iris.coord_systems.GeogCS(6371229)

    lons = np.arange(0., 360., 60.)
    xcoord = iris.coords.DimCoord(lons, standard_name='longitude', units='degrees_east')
    xcoord.guess_bounds()
    xcoord.coord_system = iris.coord_systems.GeogCS(6371229)

    data = np.ones([len(times), len(levels), len(lats), len(lons)])
    cube = iris.cube.Cube(data, units='1', long_name='soil moisture', var_name='soil_moisture')
    cube.add_dim_coord(tcoord, 0)
    cube.add_dim_coord(zcoord, 1)
    cube.add_dim_coord(ycoord, 2)
    cube.add_dim_coord(xcoord, 3)

    if stash_code:
        cube.attributes['STASH'] = STASH.from_msi(stash_code)

    return cube


def _create_4d_cube_with_pressure_axis(zaxis_name='pressure', stash_code='m01s30i201'):

    times = np.arange(0., 360., 30.)
    tunits = cf_units.Unit('days since 1970-01-01', calendar='360_day')
    tcoord = iris.coords.DimCoord(times, standard_name='time', units=tunits)

    levels = [1000., 800., 500., 250.]
    zcoord = iris.coords.DimCoord(levels, long_name=zaxis_name, units='hPa')
    try:
        zcoord.standard_name = zaxis_name
    except:
        pass

    lats = np.arange(-90., 91., 30.)
    ycoord = iris.coords.DimCoord(lats, standard_name='latitude', units='degrees_north')
    ycoord.guess_bounds()
    ycoord.coord_system = iris.coord_systems.GeogCS(6371229)

    lons = np.arange(0., 360., 60.)
    xcoord = iris.coords.DimCoord(lons, standard_name='longitude', units='degrees_east')
    xcoord.guess_bounds()
    xcoord.coord_system = iris.coord_systems.GeogCS(6371229)

    data = np.ones([len(times), len(levels), len(lats), len(lons)])
    cube = iris.cube.Cube(data, units='m s-1', long_name='eastward windspeed',
        var_name='uwind')
    cube.add_dim_coord(tcoord, 0)
    cube.add_dim_coord(zcoord, 1)
    cube.add_dim_coord(ycoord, 2)
    cube.add_dim_coord(xcoord, 3)

    if stash_code:
        cube.attributes['STASH'] = STASH.from_msi(stash_code)

    return cube


if __name__ == '__main__':
    unittest.main()
