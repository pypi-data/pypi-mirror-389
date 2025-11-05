# (C) British Crown Copyright 2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Test the afterburner.apps.model_monitor2.ModelMonitor2 application using
diagnostics on rotated grids.
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
from contextlib import contextmanager

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
    got_rose_config = True
except ImportError:
    got_rose_config = False


@contextmanager
def latlon_coords_renamed(cube):
    """
    Defines a context manager that temporarily renames the latitude & longitude
    coordinates associated with a cube in order to avoid an exception being
    thrown when an attempt is made to compute area weights from the cube. This
    mechanism is *only* intended to be used with cubes that feature dimension
    coords based upon rotated lat/long coordinates, and auxiliary coords based
    upon regular lat/long coordinates.
    """
    # __enter__ code
    try:
        lat = cube.coord('latitude', dim_coords=False)
        lat.standard_name = None
        lat_orig_long_name = lat.long_name
        lat.long_name = 'renamed_lat'
    except iris.exceptions.CoordinateNotFoundError:
        lat = None
    try:
        lon = cube.coord('longitude', dim_coords=False)
        lon.standard_name = None
        lon_orig_long_name = lon.long_name
        lon.long_name = 'renamed_lon'
    except iris.exceptions.CoordinateNotFoundError:
        lon = None

    yield cube

    # __exit__ code
    try:
        lat = cube.coord('renamed_lat', dim_coords=False)
        lat.standard_name = 'latitude'
        lat.long_name = lat_orig_long_name
    except iris.exceptions.CoordinateNotFoundError:
        pass
    try:
        lon = cube.coord('renamed_lon', dim_coords=False)
        lon.standard_name = 'longitude'
        lon.long_name = lon_orig_long_name
    except iris.exceptions.CoordinateNotFoundError:
        pass


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestRotatedGrids(unittest.TestCase):
    """
    Test the afterburner.apps.model_monitor2.ModelMonitor2 application using
    diagnostics on rotated grids.
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

    def test_awmean_ukv_diag(self):
        "Test the generation of the a-w mean of a diagnostic on the UKV domain."

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
            statistic=awmean
            stashcode=m01s00i024
        """
        _create_app_config_file(self.cfg_file, app_config)

        test_cube = stockcubes.rot_tyx()
        test_cube.attributes['STASH'] = STASH.from_msi('m01s00i024')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        args = ['-c', self.cfg_file, '-q']
        with latlon_coords_renamed(test_cube):
            app = ModelMonitor2(args)
            app.run()

        self.mock_load_model_data.assert_called_once()

        # test for existence of html output file
        html_file = os.path.join(app.html_output_dir, 'cmm.html')
        self.assertTrue(os.path.isfile(html_file))

        # test for existence of 1 image file
        img_dir = os.path.join(app.img_output_dir, 'awmean')
        img_files = os.listdir(img_dir)
        self.assertEqual(len(img_files), 1)

        # test for existence of 1 netcdf file
        nc_dir = os.path.join(app.nc_output_dir, 'awmean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 1)

        nc_file = os.path.join(nc_dir, nc_files[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube = iris.load_cube(nc_file)
            self.assertEqual(cube.standard_name, 'air_temperature')
            self.assertEqual(cube.attributes['STASH'], 'm01s00i024')
            ntimes_in = len(test_cube.coord('time').points)
            ntimes_out = len(cube.coord('time').points)
            self.assertEqual(ntimes_in, ntimes_out)

    def test_mean_ukv_subset_diag(self):
        "Test the generation of the mean of a diagnostic on a subset of the UKV domain."

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

            [namelist:diags(tas_subset)]
            enabled=true
            region_name=UKV subset
            region_extent=355,-5,365,5
            statistic=mean
            stashcode=m01s00i024
        """
        _create_app_config_file(self.cfg_file, app_config)

        test_cube = stockcubes.rot_tyx()
        test_cube.attributes['STASH'] = STASH.from_msi('m01s00i024')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        args = ['-c', self.cfg_file, '-q']
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            app = ModelMonitor2(args)
            app.run()

        self.mock_load_model_data.assert_called_once()

        # test for existence of html output file
        html_file = os.path.join(app.html_output_dir, 'cmm.html')
        self.assertTrue(os.path.isfile(html_file))

        # test for existence of 1 image file
        img_dir = os.path.join(app.img_output_dir, 'mean')
        img_files = os.listdir(img_dir)
        self.assertEqual(len(img_files), 1)

        # test for existence of 1 netcdf file
        nc_dir = os.path.join(app.nc_output_dir, 'mean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 1)

        nc_file = os.path.join(nc_dir, nc_files[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube = iris.load_cube(nc_file)
            self.assertEqual(cube.standard_name, 'air_temperature')
            self.assertEqual(cube.attributes['STASH'], 'm01s00i024')
            ntimes_in = len(test_cube.coord('time').points)
            ntimes_out = len(cube.coord('time').points)
            self.assertEqual(ntimes_in, ntimes_out)

    def test_awsum_ukv_diag(self):
        "Test the generation of the a-w sum of a diagnostic on the UKV domain."

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
            statistic=awsum
            stashcode=m01s00i024
        """
        _create_app_config_file(self.cfg_file, app_config)

        test_cube = stockcubes.rot_tyx()
        test_cube.attributes['STASH'] = STASH.from_msi('m01s00i024')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        args = ['-c', self.cfg_file, '-q']
        with latlon_coords_renamed(test_cube):
            app = ModelMonitor2(args)
            app.run()

        self.mock_load_model_data.assert_called_once()

        # test for existence of html output file
        html_file = os.path.join(app.html_output_dir, 'cmm.html')
        self.assertTrue(os.path.isfile(html_file))

        # test for existence of 1 image file
        img_dir = os.path.join(app.img_output_dir, 'awsum')
        img_files = os.listdir(img_dir)
        self.assertEqual(len(img_files), 1)

        # test for existence of 1 netcdf file
        nc_dir = os.path.join(app.nc_output_dir, 'awsum')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 1)

        nc_file = os.path.join(nc_dir, nc_files[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube = iris.load_cube(nc_file)
            self.assertEqual(cube.standard_name, 'air_temperature')
            self.assertEqual(cube.attributes['STASH'], 'm01s00i024')
            ntimes_in = len(test_cube.coord('time').points)
            ntimes_out = len(cube.coord('time').points)
            self.assertEqual(ntimes_in, ntimes_out)

    def test_sum_ukv_subset_diag(self):
        "Test the generation of the sum of a diagnostic on a subset of the UKV domain."

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
            statistic=sum
            stashcode=m01s00i024
        """
        _create_app_config_file(self.cfg_file, app_config)

        test_cube = stockcubes.rot_tyx()
        test_cube.attributes['STASH'] = STASH.from_msi('m01s00i024')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        args = ['-c', self.cfg_file, '-q']
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            app = ModelMonitor2(args)
            app.run()

        self.mock_load_model_data.assert_called_once()

        # test for existence of html output file
        html_file = os.path.join(app.html_output_dir, 'cmm.html')
        self.assertTrue(os.path.isfile(html_file))

        # test for existence of 1 image file
        img_dir = os.path.join(app.img_output_dir, 'sum')
        img_files = os.listdir(img_dir)
        self.assertEqual(len(img_files), 1)

        # test for existence of 1 netcdf file
        nc_dir = os.path.join(app.nc_output_dir, 'sum')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 1)

        nc_file = os.path.join(nc_dir, nc_files[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube = iris.load_cube(nc_file)
            self.assertEqual(cube.standard_name, 'air_temperature')
            self.assertEqual(cube.attributes['STASH'], 'm01s00i024')
            ntimes_in = len(test_cube.coord('time').points)
            ntimes_out = len(cube.coord('time').points)
            self.assertEqual(ntimes_in, ntimes_out)


def _create_app_config_file(config_file, config_text):
    with open(config_file, 'w') as fh:
        fh.writelines([line.strip()+'\n' for line in config_text.split('\n')])


if __name__ == '__main__':
    unittest.main()
