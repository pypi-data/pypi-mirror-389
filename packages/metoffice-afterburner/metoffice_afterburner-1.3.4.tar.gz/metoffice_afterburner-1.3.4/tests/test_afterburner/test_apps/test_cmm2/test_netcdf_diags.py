# (C) British Crown Copyright 2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Test the afterburner.apps.model_monitor2.ModelMonitor2 application using simple
netCDF-based diagnostics.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import os
import sys
import shutil
import tempfile
import unittest
import warnings
import logging

try:
    # python3
    from unittest import mock
except ImportError:
    # python2
    import mock

import iris
from iris.fileformats.pp import STASH

try:
    from afterburner.apps.model_monitor2 import ModelMonitor2
    from afterburner.misc import stockcubes
    from afterburner.exceptions import AppConfigError
    got_rose_config = True
except ImportError:
    got_rose_config = False


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestNetcdfDiags(unittest.TestCase):
    """
    Test the afterburner.apps.model_monitor2.ModelMonitor2 application using simple
    netCDF-based diagnostics.
    """

    def setUp(self):
        self.runtime_dir = tempfile.mkdtemp()
        os.environ['RUNTIME_DIR'] = self.runtime_dir
        _fd, self.cfg_file = tempfile.mkstemp(suffix='.conf', dir=self.runtime_dir)

        # Patch the ModelMonitor._load_latest_model_data() function.
        patch = mock.patch('afterburner.apps.model_monitor2.ModelMonitor2._load_latest_model_data')
        self.mock_load_model_data = patch.start()
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

    def test_global_ony_diag(self):
        """
        Test the generation of a global area-weighted mean from a NEMO ony stream
        diagnostic.
        """

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=VarSplit
            cache_dir=$RUNTIME_DIR/varsplit
            output_dir=$RUNTIME_DIR/output
            stream=ony

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(sst_global)]
            enabled=true
            var_name=sst
        """

        test_cube = stockcubes.geo_tyx(standard_name='sea_surface_temperature',
            long_name='Sea Surface Temperature', var_name='sst')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.mock_load_model_data.assert_called_once()

        # test for existence of html output file
        html_file = os.path.join(app.html_output_dir, 'cmm.html')
        self.assertTrue(os.path.isfile(html_file))

        # test for existence of 1 netcdf file
        nc_dir = os.path.join(app.nc_output_dir, 'awmean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 1)

        nc_file = os.path.join(nc_dir, nc_files[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube = iris.load_cube(nc_file)
            self.assertEqual(cube.standard_name, 'sea_surface_temperature')
            ntimes_in = len(test_cube.coord('time').points)
            ntimes_out = len(cube.coord('time').points)
            self.assertEqual(ntimes_in, ntimes_out)

        # test for existence of 1 image file
        img_dir = os.path.join(app.img_output_dir, 'awmean')
        img_files = os.listdir(img_dir)
        self.assertEqual(len(img_files), 1)

    def test_regional_ony_diag(self):
        """
        Test the generation of a regional area-weighted mean from a NEMO ony
        diagnostic.
        """

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=VarSplit
            cache_dir=$RUNTIME_DIR/varsplit
            output_dir=$RUNTIME_DIR/output
            stream=ony

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(sst_tropics)]
            enabled=true
            region_name=Tropics
            region_extent=0,-30,360,30
            var_name=sst
        """

        test_cube = stockcubes.geo_tyx(standard_name='sea_surface_temperature',
            long_name='Sea Surface Temperature', var_name='sst')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.mock_load_model_data.assert_called_once()

        # test for existence of html file
        html_file = os.path.join(app.html_output_dir, 'cmm.html')
        self.assertTrue(os.path.isfile(html_file))

        # test for existence of 1 netcdf file
        nc_dir = os.path.join(app.nc_output_dir, 'awmean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 1)

        nc_file = os.path.join(nc_dir, nc_files[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube = iris.load_cube(nc_file)
            self.assertEqual(cube.standard_name, 'sea_surface_temperature')
            ntimes_in = len(test_cube.coord('time').points)
            ntimes_out = len(cube.coord('time').points)
            self.assertEqual(ntimes_in, ntimes_out)
            lats = cube.coord('latitude').points
            self.assertGreaterEqual(lats[0], -30)
            self.assertLess(lats[-1], 30)
            lons = cube.coord('longitude').points
            self.assertGreaterEqual(lons[0], 0)
            self.assertLess(lons[-1], 360)

        # test for existence of 1 image file
        img_dir = os.path.join(app.img_output_dir, 'awmean')
        img_files = os.listdir(img_dir)
        self.assertEqual(len(img_files), 1)

    def test_onm_diag(self):
        """
        Test the generation of a global area-weighted mean from a NEMO onm stream
        diagnostic.
        """

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=VarSplit
            cache_dir=$RUNTIME_DIR/varsplit
            output_dir=$RUNTIME_DIR/output
            stream=onm

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(sst_global)]
            enabled=true
            var_name=sst
        """

        test_cube = stockcubes.geo_tyx(standard_name='sea_surface_temperature',
            long_name='Sea Surface Temperature', var_name='sst')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.mock_load_model_data.assert_called_once()

        # test for existence of html output file
        html_file = os.path.join(app.html_output_dir, 'cmm.html')
        self.assertTrue(os.path.isfile(html_file))

        # test for existence of 1 netcdf file
        nc_dir = os.path.join(app.nc_output_dir, 'awmean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 1)

        # test for existence of 1 image file
        img_dir = os.path.join(app.img_output_dir, 'awmean')
        img_files = os.listdir(img_dir)
        self.assertEqual(len(img_files), 1)

    def test_inm_diag(self):
        """
        Test the generation of a global area-weighted mean from a CICE inm stream
        diagnostic.
        """

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=VarSplit
            cache_dir=$RUNTIME_DIR/varsplit
            output_dir=$RUNTIME_DIR/output
            stream=inm

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(icet)]
            enabled=true
            var_name=icet
        """

        test_cube = stockcubes.geo_tyx(standard_name=None,
            long_name='Sea Ice Temperature', var_name='icet')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.mock_load_model_data.assert_called_once()

        # test for existence of html output file
        html_file = os.path.join(app.html_output_dir, 'cmm.html')
        self.assertTrue(os.path.isfile(html_file))

        # test for existence of 1 netcdf file
        nc_dir = os.path.join(app.nc_output_dir, 'awmean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 1)

        # test for existence of 1 image file
        img_dir = os.path.join(app.img_output_dir, 'awmean')
        img_files = os.listdir(img_dir)
        self.assertEqual(len(img_files), 1)

    def test_with_aux_time_coord(self):
        """
        Test the handling of a NEMO-like diagnostic which uses a simple time
        counter as the initial dimensional time coordinate, and 'real' time as
        an auxiliary coordinate. The CMM2 app should detect this and swap the
        coords around.
        """

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=VarSplit
            cache_dir=$RUNTIME_DIR/varsplit
            output_dir=$RUNTIME_DIR/output
            stream=ony

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(sst_tropics)]
            enabled=true
            region_name=Tropics
            region_extent=0,-30,360,30
            var_name=sst
        """

        test_cube = stockcubes.geo_tyx(standard_name='sea_surface_temperature',
            long_name='Sea Surface Temperature', var_name='sst')

        # Add time_counter as an aux coord and immediately promote it to a
        # dim coord, thus demoting the real time coord to be an aux coord.
        ntimes = test_cube.shape[0]
        time_cntr = iris.coords.DimCoord(range(ntimes), units='1',
            long_name='time_counter', var_name='time_counter')
        test_cube.add_aux_coord(time_cntr, 0)
        iris.util.promote_aux_coord_to_dim_coord(test_cube, 'time_counter')

        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.mock_load_model_data.assert_called_once()

        # test for existence of html file
        html_file = os.path.join(app.html_output_dir, 'cmm.html')
        self.assertTrue(os.path.isfile(html_file))

        # test for existence of 1 netcdf file
        nc_dir = os.path.join(app.nc_output_dir, 'awmean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 1)

        # test for existence of 1 image file
        img_dir = os.path.join(app.img_output_dir, 'awmean')
        img_files = os.listdir(img_dir)
        self.assertEqual(len(img_files), 1)


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestInvalidNetcdfStreams(unittest.TestCase):
    """
    Test the handling of invalid netCDF-style data streams.
    """

    def setUp(self):
        self.runtime_dir = tempfile.mkdtemp()
        os.environ['RUNTIME_DIR'] = self.runtime_dir
        _fd, self.cfg_file = tempfile.mkstemp(suffix='.conf', dir=self.runtime_dir)

        # Patch the _get_cached_data_extent() function.
        patch = mock.patch('afterburner.apps.model_monitor2._get_cached_data_extent')
        self.mock_get_cached_data_extent = patch.start()
        self.addCleanup(patch.stop)

        # Disable logging.
        lgr = logging.getLogger('afterburner.apps')
        self.log_level = lgr.level
        lgr.level = 100

        # Define the text for building an app config file. The stream property
        # gets updated by each test method below.
        self.app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=VarSplit
            cache_dir=$RUNTIME_DIR/varsplit
            output_dir=$RUNTIME_DIR/output
            stream=???

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(sst)]
            enabled=true
            var_name=sst
        """

    def tearDown(self):
        if os.path.isdir(self.runtime_dir):
            shutil.rmtree(self.runtime_dir, ignore_errors=True)

        # Re-enable logging
        lgr = logging.getLogger('afterburner.apps')
        lgr.level = self.log_level

    def test_with_invalid_stream(self):

        test_cube = stockcubes.geo_tyx(standard_name='sea_surface_temperature',
            long_name='Sea Surface Temperature', var_name='sst')
        self.mock_get_cached_data_extent.return_value = None

        app_config = self.app_config.replace("???", 'xxx', 1)
        _create_app_config_file(self.cfg_file, app_config)

        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        self.assertRaises(AppConfigError, app.run)

    def test_with_invalid_nemo_stream(self):

        test_cube = stockcubes.geo_tyx(standard_name='sea_surface_temperature',
            long_name='Sea Surface Temperature', var_name='sst')
        self.mock_get_cached_data_extent.return_value = None

        os.makedirs(os.path.join(self.runtime_dir, 'varsplit', 'anqjm', 'oxx', 'sst'))
        os.makedirs(os.path.join(self.runtime_dir, 'output', 'nc', 'awmean'))

        app_config = self.app_config.replace("???", 'oxx', 1)
        _create_app_config_file(self.cfg_file, app_config)

        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        self.assertRaises(ValueError, app.run)

        self.mock_get_cached_data_extent.assert_called_once()

    def test_with_invalid_cice_stream(self):

        test_cube = stockcubes.geo_tyx(standard_name=None,
            long_name='Sea Ice Temperature', var_name='sst')
        self.mock_get_cached_data_extent.return_value = None

        os.makedirs(os.path.join(self.runtime_dir, 'varsplit', 'anqjm', 'ixx', 'sst'))
        os.makedirs(os.path.join(self.runtime_dir, 'output', 'nc', 'awmean'))

        app_config = self.app_config.replace("???", 'ixx', 1)
        _create_app_config_file(self.cfg_file, app_config)

        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        self.assertRaises(ValueError, app.run)

        self.mock_get_cached_data_extent.assert_called_once()


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestVerticalLevels(unittest.TestCase):
    """Test correct handling of vertical levels/depths."""

    def setUp(self):
        self.runtime_dir = tempfile.mkdtemp()
        os.environ['RUNTIME_DIR'] = self.runtime_dir
        _fd, self.cfg_file = tempfile.mkstemp(suffix='.conf', dir=self.runtime_dir)

        # Patch the ModelMonitor._load_latest_model_data() function.
        patch = mock.patch('afterburner.apps.model_monitor2.ModelMonitor2._load_latest_model_data')
        self.mock_load_model_data = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.apps.ModelMonitor2._update_diag_data_cache')
        self.mock_update_cache = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.apps.ModelMonitor2._generate_plot_images')
        self.mock_gen_images = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.apps.ModelMonitor2._generate_html_page')
        self.mock_gen_html = patch.start()
        self.addCleanup(patch.stop)

        # Disable logging.
        lgr = logging.getLogger('afterburner.apps')
        self.log_level = lgr.level
        lgr.level = 100

        # Define the text for building an app config file. The level property
        # gets updated by each test method below.
        self.app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=VarSplit
            cache_dir=$RUNTIME_DIR/varsplit
            output_dir=$RUNTIME_DIR/output
            stream=onm

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(seatemp)]
            enabled=true
            var_name=seatemp
            level=?
        """

    def tearDown(self):
        if os.path.isdir(self.runtime_dir):
            shutil.rmtree(self.runtime_dir, ignore_errors=True)

        # Re-enable logging
        lgr = logging.getLogger('afterburner.apps')
        lgr.level = self.log_level

    def test_with_single_model_level(self):
        """Test correct handling of a single model level."""

        test_cube = stockcubes.geo_tzyx(standard_name='sea_water_temperature',
            long_name='Sea Temperature', var_name='seatemp', zaxis_type='level')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])
        zcoord = test_cube.coord('model_level_number')

        zlevel = "level={0}".format(zcoord.points[0])
        app_config = self.app_config.replace("level=?", zlevel, 1)
        _create_app_config_file(self.cfg_file, app_config)

        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.mock_load_model_data.assert_called_once()
        cube = self.mock_update_cache.call_args[0][0]
        self.assertTrue(cube is not None)
        self.assertEqual(cube.ndim, 1)
        self.assertEqual(cube.var_name, 'seatemp')

    def test_with_single_depth_level(self):
        """Test correct handling of a single depth level."""

        test_cube = stockcubes.geo_tzyx(standard_name='sea_water_temperature',
            long_name='Sea Temperature', var_name='seatemp', zaxis_type='height')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])
        zcoord = test_cube.coord('height')
        zcoord.standard_name = 'depth'

        zdepth = "level={0}".format(zcoord.points[0])
        app_config = self.app_config.replace("level=?", zdepth, 1)
        _create_app_config_file(self.cfg_file, app_config)

        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.mock_load_model_data.assert_called_once()
        cube = self.mock_update_cache.call_args[0][0]
        self.assertTrue(cube is not None)
        self.assertEqual(cube.ndim, 1)
        self.assertEqual(cube.var_name, 'seatemp')


def _create_app_config_file(config_file, config_text):
    with open(config_file, 'w') as fh:
        fh.writelines([line.strip()+'\n' for line in config_text.split('\n')])


if __name__ == '__main__':
    unittest.main()
