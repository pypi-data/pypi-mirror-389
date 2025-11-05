# (C) British Crown Copyright 2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.processors.diags.atmos.poleward_heat_transport
module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import logging
import unittest
import numpy as np
import numpy.testing as npt
import scipy.constants

import iris
from iris.coords import DimCoord
from iris.fileformats.pp import STASH

from afterburner.misc import stockcubes
from afterburner.processors.diags.atmos.poleward_heat_transport import (P0,
    CVD, GRAV, LHC, PolewardHeatTransport)
from afterburner.exceptions import DataProcessingError

_logger = logging.getLogger('afterburner')
_log_level = _logger.level


def setUpModule(self):
    # disable logging
    _logger.level = 100


def tearDownModule(self):
    # enable logging
    _logger.level = _log_level


class TestPhtProcessor(unittest.TestCase):
    """Test the PolewardHeatTransport diagnostic processor class."""

    def test_init_mse(self):
        proc = PolewardHeatTransport()
        self.assertEqual(proc.result_metadata['standard_name'],
            'northward_atmosphere_heat_transport')
        self.assertEqual(proc.result_metadata['var_name'],
            'moist_static_energy')
        self.assertEqual(proc.result_metadata['units'], 'PW')
        self.assertEqual(proc.earth_radius, 0)
        self.assertEqual(proc.surface_pressure, 1013.25)
        self.assertEqual(proc.input_diagnostic_ids['sensible_heat_transport'],
            'm01s30i224')

    def test_init_dse(self):
        proc = PolewardHeatTransport(calc_dse=True, earth_radius=6371999,
            surface_pressure=1013.99, sensible_heat_transport='some_std_name')
        self.assertEqual(proc.result_metadata['standard_name'],
            'northward_atmosphere_heat_transport')
        self.assertEqual(proc.result_metadata['var_name'],
            'dry_static_energy')
        self.assertEqual(proc.result_metadata['units'], 'PW')
        self.assertEqual(proc.earth_radius, 6371999)
        self.assertEqual(proc.surface_pressure, 1013.99)
        self.assertEqual(proc.input_diagnostic_ids['sensible_heat_transport'],
            'some_std_name')

    def test_mse_metadata(self):
        cubes = _create_test_cubes()
        proc = PolewardHeatTransport(result_metadata={'long_name': 'Moist Static Energy'})
        result = proc.run(cubes)
        self.assertEqual(len(result), 1)
        pht_cube = result[0]
        self.assertEqual(pht_cube.ndim, 2)
        self.assertEqual([c.name() for c in pht_cube.coords()], ['time', 'latitude'])
        self.assertEqual(pht_cube.standard_name, 'northward_atmosphere_heat_transport')
        self.assertEqual(pht_cube.long_name, 'Moist Static Energy')
        self.assertEqual(pht_cube.attributes['surface_pressure'], P0)

    def test_dse_metadata(self):
        cubes = _create_test_cubes()
        proc = PolewardHeatTransport(calc_dse=True, result_metadata={
            'long_name': 'Dry Static Energy'})
        result = proc.run(cubes)
        self.assertEqual(len(result), 1)
        pht_cube = result[0]
        self.assertEqual(pht_cube.ndim, 2)
        self.assertEqual([c.name() for c in pht_cube.coords()], ['time', 'latitude'])
        self.assertEqual(pht_cube.standard_name, 'northward_atmosphere_heat_transport')
        self.assertEqual(pht_cube.long_name, 'Dry Static Energy')
        self.assertEqual(pht_cube.attributes['surface_pressure'], P0)

    def test_mse_result(self):
        cubes = _create_test_cubes()
        proc = PolewardHeatTransport(surface_pressure=1100)
        result = proc.run(cubes)
        self.assertEqual(len(result), 1)
        pht_cube = result[0]
        self.assertEqual(pht_cube.ndim, 2)
        self.assertFalse('earth_radius' in pht_cube.attributes)
        self.assertEqual(pht_cube.attributes['surface_pressure'], 1100)
        pht_data = _calc_expected_pht_values(cubes)
        expected = pht_data[0]
        actual = pht_cube.data[0]
        npt.assert_allclose(expected, actual)

    def test_mse_result_with_decr_plevels(self):
        cubes = _create_test_cubes(plevel_dirn='decreasing')
        proc = PolewardHeatTransport(surface_pressure=1100)
        result = proc.run(cubes)
        self.assertEqual(len(result), 1)
        pht_cube = result[0]
        self.assertEqual(pht_cube.ndim, 2)
        pht_data = _calc_expected_pht_values(cubes)
        expected = pht_data[0]
        actual = pht_cube.data[0]
        npt.assert_allclose(expected, actual)

    def test_mse_result_with_named_inputs(self):
        cubes = _create_test_cubes()
        proc = PolewardHeatTransport(surface_pressure=1100,
            sensible_heat_transport='product_of_northward_wind_and_air_temperature',
            latent_heat_transport='product_of_northward_wind_and_specific_humidity',
            potential_energy_transport='product_of_northward_wind_and_geopotential_height')
        result = proc.run(cubes)
        self.assertEqual(len(result), 1)
        pht_cube = result[0]
        self.assertEqual(pht_cube.ndim, 2)
        pht_data = _calc_expected_pht_values(cubes)
        expected = pht_data[0]
        actual = pht_cube.data[0]
        npt.assert_allclose(expected, actual)

    def test_dse_result(self):
        cubes = _create_test_cubes()
        proc = PolewardHeatTransport(calc_dse=True, surface_pressure=1100)
        result = proc.run(cubes)
        self.assertEqual(len(result), 1)
        pht_cube = result[0]
        self.assertEqual(pht_cube.ndim, 2)
        self.assertFalse('earth_radius' in pht_cube.attributes)
        self.assertEqual(pht_cube.attributes['surface_pressure'], 1100)
        pht_data = _calc_expected_pht_values(cubes, calc_dse=True)
        expected = pht_data[0]
        actual = pht_cube.data[0]
        npt.assert_allclose(expected, actual)

    def test_dse_result_with_radius(self):
        cubes = _create_test_cubes()
        proc = PolewardHeatTransport(calc_dse=True, earth_radius=6371999)
        result = proc.run(cubes)
        self.assertEqual(len(result), 1)
        pht_cube = result[0]
        self.assertTrue('earth_radius' in pht_cube.attributes)
        self.assertEqual(pht_cube.attributes['earth_radius'], 6371999.0)

    def test_incongruent_cubes(self):
        "Test using input cubes with unequal shape/dimensions."
        cubes = _create_test_cubes()
        pet = cubes[2][:-1]   # delete last time from PET cube
        proc = PolewardHeatTransport()
        self.assertRaises(DataProcessingError, proc.run, cubes[:-1] + [pet])

    def test_with_invalid_stash_code(self):
        "Test using an input cube with an incorrect STASH code."
        cubes = _create_test_cubes()
        pet = cubes[2]
        # Assign invalid STASH code to the PET cube
        pet.attributes['STASH'] = STASH.from_msi('m01s99i999')
        proc = PolewardHeatTransport()
        self.assertRaises(DataProcessingError, proc.run, cubes)

    def test_with_return_components(self):
        cubes = _create_test_cubes()
        proc = PolewardHeatTransport()
        result = proc.run(cubes, return_components=True)
        self.assertEqual(len(result), 4)
        for x in result:
            self.assertTrue(isinstance(x, iris.cube.Cube))


def _create_test_cubes(plevel_dirn='increasing'):
    """Create 4D test cubes of SHT, LHT and PET."""

    levels = np.linspace(100.0, 1000.0, 10, dtype=np.float32)
    if plevel_dirn == 'decreasing': levels = levels[::-1]
    zcoord = DimCoord(levels, long_name='pressure', var_name='pressure', units='hPa')

    # Create a cube of sensible heat transport.
    data = np.ones([2, 10, 7, 6], dtype=np.float32)
    sht = stockcubes.geo_tzyx(data=data, var_name='sht', long_name=None,
        standard_name='product_of_northward_wind_and_air_temperature',
        units='K m s-1')
    sht.attributes['STASH'] = STASH.from_msi('m01s30i224')
    sht.remove_coord('pressure')
    sht.add_dim_coord(zcoord, 1)

    # Create a cube of latent heat transport.
    data = np.ones([2, 10, 7, 6], dtype=np.float32) * 2
    lht = stockcubes.geo_tzyx(data=data, var_name='lht', long_name=None,
        standard_name='product_of_northward_wind_and_specific_humidity',
        units='m s-1')
    lht.attributes['STASH'] = STASH.from_msi('m01s30i225')
    lht.remove_coord('pressure')
    lht.add_dim_coord(zcoord, 1)

    # Create a cube of potential energy transport.
    data = np.ones([2, 10, 7, 6], dtype=np.float32) * 3
    pet = stockcubes.geo_tzyx(data=data, var_name='pet', long_name=None,
        standard_name='product_of_northward_wind_and_geopotential_height',
        units='m2 s-1')
    pet.attributes['STASH'] = STASH.from_msi('m01s30i227')
    pet.remove_coord('pressure')
    pet.add_dim_coord(zcoord, 1)

    cubes = iris.cube.CubeList([sht, lht, pet])

    return cubes


def _calc_expected_pht_values(cubes, calc_dse=False):
    """Calculate an array of expected MSE or DSE values from the passed in cubes."""

    sht, lht, pet = cubes

    sht.data = np.ma.masked_equal(sht.data, 0)
    lht.data = np.ma.masked_equal(lht.data, 0)
    pet.data = np.ma.masked_equal(pet.data, 0)

    deltap = np.ones(10, dtype=np.float32) * 100
    deltap[-1] = 150.0
    deltap[0] = 50.0
    #zcoord = sht.coord('pressure')
    #deltap = _calc_pressure_level_thickness(zcoord.points, 1100.0)

    lat_weights = iris.analysis.cartography.cosine_latitude_weights(sht[0,0,:,:])
    lat_lengths = lat_weights[:,0] * 2 * scipy.constants.pi * 6371229

    zi = np.mean(sht.data, axis=3) * lat_lengths
    vizi = np.ma.sum(zi*deltap[:,None], axis=1) * 100.0 / GRAV
    sht_data = vizi * CVD

    zi = np.mean(lht.data, axis=3) * lat_lengths
    vizi = np.ma.sum(zi*deltap[:,None], axis=1) * 100.0 / GRAV
    lht_data = vizi * LHC

    zi = np.mean(pet.data, axis=3) * lat_lengths
    pet_data = np.ma.sum(zi*deltap[:,None], axis=1) * 100.0

    if calc_dse:
        pht_data = sht_data + pet_data
    else:
        pht_data = sht_data + lht_data + pet_data

    return pht_data * 1e-15


if __name__ == '__main__':
    unittest.main()
