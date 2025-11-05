# (C) British Crown Copyright 2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Test the afterburner.apps.model_monitor.ModelMonitor application using simple 2D
diagnostics.
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
    from afterburner.apps.model_monitor import ModelMonitor
    from afterburner.misc import stockcubes
    got_rose_config = True
except ImportError:
    got_rose_config = False


@unittest.skipUnless(got_rose_config, "rose config module not found")
class Test2dDiags(unittest.TestCase):
    """
    Test the afterburner.apps.model_monitor.ModelMonitor application using simple 2D
    diagnostics.
    """

    def setUp(self):
        self.runtime_dir = tempfile.mkdtemp()
        os.environ['RUNTIME_DIR'] = self.runtime_dir
        _fd, self.cfg_file = tempfile.mkstemp(suffix='.conf', dir=self.runtime_dir)

        # Patch the ModelMonitor._load_latest_model_data() function.
        patch = mock.patch('afterburner.apps.model_monitor.ModelMonitor._load_latest_model_data')
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

    def test_global_2d_diag(self):
        "Test the generation of a global 2D UM diagnostic."

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

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(tas_global)]
            enabled=true
            stashcode=m01s00i024
        """

        test_cube = stockcubes.geo_tyx()
        test_cube.attributes['STASH'] = STASH.from_msi('m01s00i024')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor(args)
        app.run()

        self.mock_load_model_data.assert_called_once()

        # test for existence of html output file
        html_file = os.path.join(app.html_output_dir, 'cmm.html')
        self.assertTrue(os.path.isfile(html_file))

        # test for existence of 1 netcdf file
        nc_files = os.listdir(app.nc_output_dir)
        self.assertEqual(len(nc_files), 1)

        nc_file = os.path.join(app.nc_output_dir, nc_files[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube = iris.load_cube(nc_file)
            self.assertEqual(cube.standard_name, 'air_temperature')
            self.assertEqual(cube.attributes['STASH'], 'm01s00i024')
            ntimes_in = len(test_cube.coord('time').points)
            ntimes_out = len(cube.coord('time').points)
            self.assertEqual(ntimes_in, ntimes_out)

        # test for existence of 1 image file
        img_files = os.listdir(app.img_output_dir)
        self.assertEqual(len(img_files), 1)

    def test_regional_2d_diag(self):
        "Test the generation of a regional 2D UM diagnostic."

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

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(tas_tropics)]
            enabled=true
            region_name=Tropics
            region_extent=0,-30,360,30
            stashcode=m01s00i024
        """

        test_cube = stockcubes.geo_tyx()
        test_cube.attributes['STASH'] = STASH.from_msi('m01s00i024')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor(args)
        app.run()

        self.mock_load_model_data.assert_called_once()

        # test for existence of html file
        html_file = os.path.join(app.html_output_dir, 'cmm.html')
        self.assertTrue(os.path.isfile(html_file))

        # test for existence of 1 netcdf file
        nc_files = os.listdir(app.nc_output_dir)
        self.assertEqual(len(nc_files), 1)

        nc_file = os.path.join(app.nc_output_dir, nc_files[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube = iris.load_cube(nc_file)
            self.assertEqual(cube.standard_name, 'air_temperature')
            self.assertEqual(cube.attributes['STASH'], 'm01s00i024')
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
        img_files = os.listdir(app.img_output_dir)
        self.assertEqual(len(img_files), 1)


def _create_app_config_file(config_file, config_text):
    with open(config_file, 'w') as fh:
        fh.writelines([line.strip()+'\n' for line in config_text.split('\n')])


if __name__ == '__main__':
    unittest.main()
