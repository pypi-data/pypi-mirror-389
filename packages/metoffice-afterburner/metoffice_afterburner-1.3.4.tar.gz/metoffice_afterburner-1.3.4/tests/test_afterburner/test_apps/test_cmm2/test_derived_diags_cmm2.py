# (C) British Crown Copyright 2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Test the afterburner.apps.model_monitor2.ModelMonitor2 application using derived
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

import numpy.testing as npt

import iris
import iris.coords
from iris.fileformats.pp import STASH

try:
    from afterburner.apps.model_monitor2 import ModelMonitor2
    from afterburner.misc import stockcubes
    got_rose_config = True
except ImportError:
    got_rose_config = False


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestDerivedDiags(unittest.TestCase):
    """
    Test the afterburner.apps.model_monitor2.ModelMonitor2 application using derived
    diagnostics.
    """

    def setUp(self):
        self.runtime_dir = tempfile.mkdtemp()
        os.environ['RUNTIME_DIR'] = self.runtime_dir
        _fd, self.cfg_file = tempfile.mkstemp(suffix='.conf', dir=self.runtime_dir)

        # Patch the ModelMonitor2._load_latest_model_data() function.
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

    def test_trivial_formula(self):
        "Test the generation of a derived diagnostic based on a trivial formula."

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

            [namelist:diags(tas_celsius)]
            enabled=true
            formula=m01s00i024-273
            var_name=tas_celsius
            long_name=Surface Air Temperature
            standard_name=air_temperature
            units=degC
        """

        test_cube = stockcubes.geo_tyx()
        test_cube.attributes['STASH'] = STASH.from_msi('m01s00i024')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.mock_load_model_data.assert_called_once()

        # test for existence of 1 netcdf file
        nc_dir = os.path.join(app.nc_output_dir, 'awmean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 1)

        nc_file = os.path.join(nc_dir, nc_files[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube = iris.load_cube(nc_file)
            self.assertEqual(cube.var_name, 'tas_celsius')
            self.assertEqual(cube.standard_name, 'air_temperature')
            self.assertEqual(cube.units.origin, 'degC')
            ntimes_in = len(test_cube.coord('time').points)
            ntimes_out = len(cube.coord('time').points)
            self.assertEqual(ntimes_in, ntimes_out)
            drvd_cube = test_cube - 273
            weights = iris.analysis.cartography.area_weights(drvd_cube)
            drvd_cube = drvd_cube.collapsed(['latitude', 'longitude'],
                iris.analysis.MEAN, weights=weights)
            npt.assert_allclose(cube.data, drvd_cube.data)

    def test_nontrivial_formula(self):
        "Test the generation of a derived diagnostic based on a non-trivial formula."

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

            [namelist:diags(tas_fahrenheit)]
            enabled=true
            formula=(m01s00i024-273) * 1.8 + 32
            var_name=tas_fahrenheit
            long_name=Surface Air Temperature
            standard_name=air_temperature
            units=degF
        """

        test_cube = stockcubes.geo_tyx()
        test_cube.attributes['STASH'] = STASH.from_msi('m01s00i024')
        self.mock_load_model_data.return_value = iris.cube.CubeList([test_cube])

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.mock_load_model_data.assert_called_once()

        # test for existence of 1 netcdf file
        nc_dir = os.path.join(app.nc_output_dir, 'awmean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 1)

        nc_file = os.path.join(nc_dir, nc_files[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube = iris.load_cube(nc_file)
            self.assertEqual(cube.var_name, 'tas_fahrenheit')
            self.assertEqual(cube.standard_name, 'air_temperature')
            self.assertEqual(cube.units.origin, 'degF')
            ntimes_in = len(test_cube.coord('time').points)
            ntimes_out = len(cube.coord('time').points)
            self.assertEqual(ntimes_in, ntimes_out)
            drvd_cube = (test_cube - 273) * 1.8 + 32
            weights = iris.analysis.cartography.area_weights(drvd_cube)
            drvd_cube = drvd_cube.collapsed(['latitude', 'longitude'],
                iris.analysis.MEAN, weights=weights)
            npt.assert_allclose(cube.data, drvd_cube.data)


    def test_toa_radiation_balance(self):
        "Test the generation of the built-in TOA radiation balance diagnostic."

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

            [namelist:diags(toa_radiation_balance)]
            enabled=true
            var_name=toa_radiation_balance
            long_name=TOA Radiation Balance
            standard_name=toa_net_downward_radiative_flux
        """

        sw_in = stockcubes.geo_tyx(data=10.0, var_name='sw_in', units='W m-2')
        sw_in.attributes['STASH'] = STASH.from_msi('m01s01i207')
        sw_out = stockcubes.geo_tyx(data=5.0, var_name='sw_out', units='W m-2')
        sw_out.attributes['STASH'] = STASH.from_msi('m01s01i208')
        lw_out = stockcubes.geo_tyx(data=2.0, var_name='lw_out', units='W m-2')
        lw_out.attributes['STASH'] = STASH.from_msi('m01s03i332')

        self.mock_load_model_data.side_effect = [iris.cube.CubeList([x]) for x in
            [sw_in, sw_out, lw_out]]

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.assertEqual(self.mock_load_model_data.call_count, 3)

        # test for existence of 1 netcdf file
        nc_dir = os.path.join(app.nc_output_dir, 'awmean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 1)

        nc_file = os.path.join(nc_dir, nc_files[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube = iris.load_cube(nc_file)
            self.assertEqual(cube.var_name, 'toa_radiation_balance')
            self.assertEqual(cube.standard_name, 'toa_net_downward_radiative_flux')
            self.assertEqual(cube.units.origin, 'W m-2')
            ntimes_in = len(sw_in.coord('time').points)
            ntimes_out = len(cube.coord('time').points)
            self.assertEqual(ntimes_in, ntimes_out)
            drvd_cube = sw_in - sw_out - lw_out
            weights = iris.analysis.cartography.area_weights(drvd_cube)
            drvd_cube = drvd_cube.collapsed(['latitude', 'longitude'],
                iris.analysis.MEAN, weights=weights)
            npt.assert_allclose(cube.data, drvd_cube.data)

    def test_custom_diag_with_stash_codes(self):
        "Test the generation of a custom diagnostic based on STASH codes."

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

            [namelist:diags(surface_albedo)]
            enabled=true
            formula=m01s01i211 / m01s01i210
            var_name=surface_albedo
            long_name=Surface Albedo
            standard_name=surface_albedo
        """

        sw_in = stockcubes.geo_tyx(data=10.0, var_name='sw_in', units='W m-2')
        sw_in.attributes['STASH'] = STASH.from_msi('m01s01i210')
        sw_out = stockcubes.geo_tyx(data=5.0, var_name='sw_out', units='W m-2')
        sw_out.attributes['STASH'] = STASH.from_msi('m01s01i211')

        self.mock_load_model_data.side_effect = [iris.cube.CubeList([x]) for x in
            [sw_in, sw_out]]

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.assertEqual(self.mock_load_model_data.call_count, 2)

        # test for existence of 1 netcdf file
        nc_dir = os.path.join(app.nc_output_dir, 'awmean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 1)

        nc_file = os.path.join(nc_dir, nc_files[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube = iris.load_cube(nc_file)
            self.assertEqual(cube.var_name, 'surface_albedo')
            self.assertEqual(cube.standard_name, 'surface_albedo')
            self.assertEqual(cube.units.origin, '1')
            ntimes_in = len(sw_in.coord('time').points)
            ntimes_out = len(cube.coord('time').points)
            self.assertEqual(ntimes_in, ntimes_out)
            drvd_cube = sw_out / sw_in
            weights = iris.analysis.cartography.area_weights(drvd_cube)
            drvd_cube = drvd_cube.collapsed(['latitude', 'longitude'],
                iris.analysis.MEAN, weights=weights)
            npt.assert_allclose(cube.data, drvd_cube.data)

    def test_mip_diag_with_cdds_constant(self):
        "Test the generation of a custom diagnostic with a named CDDS constant."

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

            [namelist:diags(fake_ice)]
            enabled=true
            class_path=afterburner.processors.diags.derived.MipDerivedDiagnostic
            formula=m01s05i216 * ICE_DENSITY
            var_name=fake_ice
            long_name=Fake Ice
            units=kg m-2 s-1
        """

        precip = stockcubes.geo_tyx(data=1.0, standard_name=None, long_name=None,
            var_name='precip', units='kg m-2 s-1')
        precip.attributes['STASH'] = STASH.from_msi('m01s05i216')

        self.mock_load_model_data.return_value = iris.cube.CubeList([precip])

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.mock_load_model_data.assert_called_once()

        # test for existence of 1 netcdf file
        nc_dir = os.path.join(app.nc_output_dir, 'awmean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 1)

        nc_file = os.path.join(nc_dir, nc_files[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube = iris.load_cube(nc_file)
            self.assertEqual(cube.var_name, 'fake_ice')
            self.assertEqual(cube.units.origin, 'kg m-2 s-1')
            ntimes_in = len(precip.coord('time').points)
            ntimes_out = len(cube.coord('time').points)
            self.assertEqual(ntimes_in, ntimes_out)

    def test_mip_diag_with_pp_constraint(self):
        "Test the generation of a custom diagnostic with a PP constraint."

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

            [namelist:diags(fake_ice)]
            enabled=true
            class_path=afterburner.processors.diags.derived.MipDerivedDiagnostic
            formula=m01s05i216 * ICE_DENSITY
            lbproc=128
            var_name=fake_ice
            long_name=Fake Ice
            units=kg m-2 s-1
        """

        precip = stockcubes.geo_tyx(data=1.0, standard_name=None, long_name=None,
            var_name='precip', units='kg m-2 s-1')
        precip.attributes['STASH'] = STASH.from_msi('m01s05i216')

        precip2 = stockcubes.geo_tyx(data=1.0, standard_name=None, long_name=None,
            var_name='precip', units='kg m-2 s-1')
        precip2.attributes['STASH'] = STASH.from_msi('m01s05i216')
        precip2.cell_methods = (iris.coords.CellMethod('maximum', coords=['time']),)

        self.mock_load_model_data.side_effect = [iris.cube.CubeList([x]) for x in
            [precip, precip2]]

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.mock_load_model_data.assert_called_once()

        # test for existence of 1 netcdf file
        nc_dir = os.path.join(app.nc_output_dir, 'awmean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 1)

        nc_file = os.path.join(nc_dir, nc_files[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cube = iris.load_cube(nc_file)
            self.assertEqual(cube.var_name, 'fake_ice')
            self.assertEqual(cube.units.origin, 'kg m-2 s-1')
            ntimes_in = len(precip.coord('time').points)
            ntimes_out = len(cube.coord('time').points)
            self.assertEqual(ntimes_in, ntimes_out)


def _create_app_config_file(config_file, config_text):
    with open(config_file, 'w') as fh:
        fh.writelines([line.strip()+'\n' for line in config_text.split('\n')])


if __name__ == '__main__':
    unittest.main()
