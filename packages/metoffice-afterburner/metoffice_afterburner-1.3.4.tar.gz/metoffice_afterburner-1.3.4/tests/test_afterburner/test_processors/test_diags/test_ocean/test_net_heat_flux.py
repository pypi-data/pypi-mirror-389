#  (C) British Crown Copyright 2016-2020, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.processors.diags.ocean.net_heat_flux module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import unittest
import numpy as np
import numpy.ma as ma
import numpy.testing as npt

try:
    # python3
    from unittest import mock
except ImportError:
    # python2
    import mock

import iris
from iris.fileformats.pp import STASH

from afterburner.processors.diags.ocean.net_heat_flux import NetHeatFluxIntoOcean
from afterburner.processors.diags.ocean.net_heat_flux import LATENT_HEAT_OF_VAPORIZATION as LHV
from afterburner.exceptions import DataProcessingError
from afterburner.misc import stockcubes

from scipy.constants import Stefan_Boltzmann as SBC


class TestNetHeatFluxIntoOceanProcessor(unittest.TestCase):
    """Test the NetHeatFluxIntoOcean diagnostic processor class."""

    def setUp(self):
        self.cubelist = _create_input_cubes()
        # increase log level to prevent log messages appearing in test output
        _proc = NetHeatFluxIntoOcean(log_level='critical')

    def test_init(self):
        proc = NetHeatFluxIntoOcean(result_metadata={'var_name': 'net_heat_flux',
            'standard_name': 'surface_downward_heat_flux_in_sea_water'})
        self.assertEqual(proc.result_metadata['var_name'], 'net_heat_flux')
        self.assertEqual(proc.result_metadata['standard_name'],
            'surface_downward_heat_flux_in_sea_water')
        self.assertEqual(proc.result_metadata['units'], 'W m-2')

    def test_with_good_fields(self):
        proc = NetHeatFluxIntoOcean(result_metadata={'units': 'W ft-2'})
        cubes = proc.run(self.cubelist)
        self.assertEqual(len(cubes), 1)
        nhflux = cubes[0]
        self.assertEqual(nhflux.long_name, proc.result_metadata['long_name'])
        self.assertEqual(nhflux.var_name, proc.result_metadata['var_name'])
        self.assertEqual(nhflux.units, 'W ft-2')
        self.assertEqual(nhflux.shape, self.cubelist[0].shape)
        self.assertTrue(nhflux.attributes.get('history') is not None)
        self.assertTrue(nhflux.attributes.get('STASH') is None)
        testdata = nhflux.data.copy()
        testdata[:] = 10.0 + 2.5 - 5.0 - SBC - LHV
        npt.assert_allclose(nhflux.data, testdata)

    def test_with_unequal_shapes(self):
        # reduce time dimension of sea temp cube by 1
        seatem = self.cubelist[-1][0:-1]
        tmp_cubes = self.cubelist[0:-1]
        tmp_cubes.append(seatem)
        proc = NetHeatFluxIntoOcean()
        self.assertRaises(DataProcessingError, proc.run, tmp_cubes)

    def test_with_missing_field(self):
        tmp_cubes = _create_input_cubes(include_laf=False)
        proc = NetHeatFluxIntoOcean()
        self.assertRaises(DataProcessingError, proc.run, tmp_cubes[0:-1])

    def test_with_missing_values(self):
        tmp_cubes = _create_input_cubes()

        # mask out one column of data in the sensible heat flux cube
        shflux = tmp_cubes[2]
        data = ma.masked_array(shflux.data, fill_value=1e20)
        data[0,0,:] = ma.masked
        shflux.data = data

        proc = NetHeatFluxIntoOcean()
        cubes = proc.run(tmp_cubes)
        self.assertEqual(len(cubes), 1)
        nhflux = cubes[0]
        self.assertTrue(ma.all(nhflux.data.mask[0,0,:]))

    def test_with_missing_laf_data(self):
        tmp_cubes = _create_input_cubes(include_laf=False)
        proc = NetHeatFluxIntoOcean()
        cubes = proc.run(tmp_cubes)
        self.assertEqual(len(cubes), 1)
        nhflux = cubes[0]
        nmasked = ma.count_masked(nhflux.data[0])   # in 1st time slice
        self.assertEqual(nmasked, 0)

    def test_with_laf_cube(self):
        in_cubes = _create_input_cubes()
        laf_cube, = in_cubes.extract('land_area_fraction')
        self.assertEqual(laf_cube.ndim, 2)
        land_pts = np.where(laf_cube.data > 0)
        nland = len(land_pts[0])
        in_cubes.append(laf_cube)
        proc = NetHeatFluxIntoOcean()
        cubes = proc.run(in_cubes)
        self.assertEqual(len(cubes), 1)
        nhflux = cubes[0]
        nmasked = ma.count_masked(nhflux.data[0])   # in 1st time slice
        self.assertEqual(nmasked, nland)

    @mock.patch('afterburner.processors.diags.ocean.net_heat_flux._read_laf_file')
    def test_with_laf_file(self, mock_load_laf):
        in_cubes = _create_input_cubes()
        laf_cube, = in_cubes.extract('land_area_fraction')
        mock_load_laf.return_value = laf_cube
        self.assertEqual(laf_cube.ndim, 2)
        land_pts = np.where(laf_cube.data > 0)
        nland = len(land_pts[0])
        proc = NetHeatFluxIntoOcean(laf_file='dummy_file')
        cubes = proc.run(in_cubes)
        self.assertEqual(len(cubes), 1)
        nhflux = cubes[0]
        nmasked = ma.count_masked(nhflux.data[0])   # in 1st time slice
        self.assertEqual(nmasked, nland)

    def test_with_custom_laf_threshold(self):
        in_cubes = _create_input_cubes()
        laf_cube, = in_cubes.extract('land_area_fraction')
        self.assertEqual(laf_cube.ndim, 2)
        land_pts = np.where(laf_cube.data >= 0.25)
        nland = len(land_pts[0])
        in_cubes.append(laf_cube)
        proc = NetHeatFluxIntoOcean(laf_threshold=0.25)
        cubes = proc.run(in_cubes)
        self.assertEqual(len(cubes), 1)
        nhflux = cubes[0]
        nmasked = ma.count_masked(nhflux.data[0])   # in 1st time slice
        self.assertEqual(nmasked, nland)

    def test_aw_mean(self):
        proc = NetHeatFluxIntoOcean()
        cubes = proc.run(self.cubelist, calc_aw_mean=True)
        self.assertEqual(len(cubes), 2)
        nhflux, awmean = cubes
        coords = awmean.coords(dim_coords=True)
        self.assertEqual(awmean.ndim, 1)
        self.assertEqual(awmean.shape[0], nhflux.shape[0])
        self.assertEqual(awmean.var_name, 'aw_mean_of_net_heat_flux_into_ocean')
        self.assertEqual(coords[0].name(), 'time')
        self.assertTrue(len(awmean.cell_methods) > 0)
        areacm = awmean.cell_methods[-1]
        self.assertEqual(areacm.coord_names, ('area',))
        self.assertEqual(areacm.method, 'mean where sea')
        testdata = ma.zeros(awmean.shape, dtype=awmean.data.dtype)
        testdata[:] = 10.0 + 2.5 - 5.0 - SBC - LHV
        npt.assert_allclose(awmean.data, testdata)


class TestNetHeatFluxProcessor(unittest.TestCase):
    """Test the short form of the NetHeatFluxIntoOcean diagnostic processor class."""

    def setUp(self):
        self.cubelist = _create_input_cubes(short_form=True)
        # increase log level to prevent log messages appearing in test output
        _proc = NetHeatFluxIntoOcean(log_level='critical')

    def test_with_standard_fields(self):
        proc = NetHeatFluxIntoOcean()
        cubes = proc.run(self.cubelist)
        self.assertEqual(len(cubes), 1)
        nhflux = cubes[0]
        self.assertEqual(nhflux.long_name, proc.result_metadata['long_name'])
        self.assertEqual(nhflux.var_name, proc.result_metadata['var_name'])
        self.assertEqual(nhflux.shape, self.cubelist[0].shape)
        self.assertTrue(nhflux.attributes.get('history') is not None)
        self.assertTrue(nhflux.attributes.get('STASH') is None)
        testdata = nhflux.data.copy()
        testdata[:] = 6.5   # 10.0 + 2.5 - 5.0 - 1.0
        npt.assert_allclose(nhflux.data, testdata)

    def test_with_dw_lw_flux(self):
        proc = NetHeatFluxIntoOcean()
        std_cubes = _create_input_cubes(short_form=True)
        tmp_cubes = _create_input_cubes(include_laf=False, short_form=False)
        std_cubes[2] = tmp_cubes[2]    # replace net_dn_lw with dw_lw flux
        std_cubes.append(tmp_cubes[3]) # append surface temp
        self.assertEqual(std_cubes[2].name(), 'surface_downwelling_longwave_flux')
        self.assertEqual(std_cubes[-1].name(), 'surface_temperature')
        cubes = proc.run(std_cubes)
        self.assertEqual(len(cubes), 1)
        nhflux = cubes[0]
        self.assertEqual(nhflux.long_name, proc.result_metadata['long_name'])
        self.assertEqual(nhflux.var_name, proc.result_metadata['var_name'])
        self.assertEqual(nhflux.shape, self.cubelist[0].shape)
        testdata = nhflux.data.copy()
        testdata[:] = 10.0 + (2.5-SBC) - 5.0 - 1
        npt.assert_allclose(nhflux.data, testdata)

    def test_with_evap_flux(self):
        proc = NetHeatFluxIntoOcean()
        std_cubes = _create_input_cubes(short_form=True)
        tmp_cubes = _create_input_cubes(include_laf=False, short_form=False)
        std_cubes[3] = tmp_cubes[4]    # replace lh flux with evap flux
        self.assertEqual(std_cubes[3].name(), 'water_evaporation_flux')
        cubes = proc.run(std_cubes)
        self.assertEqual(len(cubes), 1)
        nhflux = cubes[0]
        self.assertEqual(nhflux.long_name, proc.result_metadata['long_name'])
        self.assertEqual(nhflux.var_name, proc.result_metadata['var_name'])
        self.assertEqual(nhflux.shape, self.cubelist[0].shape)
        testdata = nhflux.data.copy()
        testdata[:] = 10.0 + 2.5 - 5.0 - LHV
        npt.assert_allclose(nhflux.data, testdata)

    def test_with_missing_field(self):
        tmp_cubes = _create_input_cubes(include_laf=False, short_form=True)
        proc = NetHeatFluxIntoOcean()
        self.assertRaises(DataProcessingError, proc.run, tmp_cubes[0:-1])

    def test_aw_mean(self):
        proc = NetHeatFluxIntoOcean()
        cubes = proc.run(self.cubelist, calc_aw_mean=True)
        self.assertEqual(len(cubes), 2)
        nhflux, awmean = cubes
        coords = awmean.coords(dim_coords=True)
        self.assertEqual(awmean.ndim, 1)
        self.assertEqual(awmean.shape[0], nhflux.shape[0])
        self.assertEqual(awmean.var_name, 'aw_mean_of_net_heat_flux_into_ocean')
        self.assertEqual(coords[0].name(), 'time')


def _create_input_cubes(include_laf=True, short_form=False):

    cubes = iris.cube.CubeList()

    swflux = stockcubes.geo_tyx(standard_name='surface_net_downward_shortwave_flux',
        units='W m-2')
    swflux.attributes['STASH'] = STASH.from_msi('m01s01i203')
    swflux.data = swflux.data.astype('float32')
    swflux.data[:] = 10.0
    cubes.append(swflux)

    shflux = stockcubes.geo_tyx(standard_name='surface_upward_sensible_heat_flux',
        units='W m-2')
    shflux.attributes['STASH'] = STASH.from_msi('m01s03i228')
    shflux.data = shflux.data.astype('float32')
    shflux.data[:] = 5.0
    cubes.append(shflux)

    if short_form:
        lwflux = stockcubes.geo_tyx(standard_name='surface_net_downward_longwave_flux',
            units='W m-2')
        lwflux.attributes['STASH'] = STASH.from_msi('m01s02i201')
        lwflux.data = lwflux.data.astype('float32')
        lwflux.data[:] = 2.5
        cubes.append(lwflux)

        lhflux = stockcubes.geo_tyx(standard_name='surface_upward_latent_heat_flux',
            units='W m-2')
        lhflux.attributes['STASH'] = STASH.from_msi('m01s03i234')
        lhflux.data = lhflux.data.astype('float32')
        lhflux.data[:] = 1.0
        cubes.append(lhflux)

    else:
        lwflux = stockcubes.geo_tyx(standard_name='surface_downwelling_longwave_flux',
            units='W m-2')
        lwflux.attributes['STASH'] = STASH.from_msi('m01s02i207')
        lwflux.data = lwflux.data.astype('float32')
        lwflux.data[:] = 2.5
        cubes.append(lwflux)

        seatem = stockcubes.geo_tyx(standard_name='surface_temperature', units='K')
        seatem.attributes['STASH'] = STASH.from_msi('m01s00i507')
        seatem.data = seatem.data.astype('float32')
        seatem.data[:] = 1.0
        cubes.append(seatem)

        evflux = stockcubes.geo_tyx(standard_name='water_evaporation_flux',
            units='kg m-2 s-1')
        evflux.attributes['STASH'] = STASH.from_msi('m01s03i232')
        evflux.data = evflux.data.astype('float32')
        evflux.data[:] = 1.0
        cubes.append(evflux)

    if include_laf:
        cubes.append(_create_laf_cube(swflux.shape[1:]))

    return cubes


def _create_laf_cube(shape):
    data = np.random.uniform(0.0, 1.0, shape).astype(np.float32)
    data = np.where(data < 0.25, 0, data)   # set at least some all-sea points
    laf_cube = iris.cube.Cube(data, standard_name='land_area_fraction', units='1')
    return laf_cube


if __name__ == '__main__':
    unittest.main()
