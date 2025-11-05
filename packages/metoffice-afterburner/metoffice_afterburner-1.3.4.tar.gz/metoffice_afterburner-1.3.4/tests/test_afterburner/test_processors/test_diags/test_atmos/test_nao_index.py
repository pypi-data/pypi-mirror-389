# (C) British Crown Copyright 2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.processors.diags.atmos.nao_index module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import assertCountEqual

import unittest
import numpy as np
import numpy.testing as npt

import iris
import iris.util
from iris.fileformats.pp import STASH

from afterburner.misc import stockcubes
from afterburner.processors.diags import NaoIndex
from afterburner.exceptions import DataProcessingError


class TestNaoIndexProcessor(unittest.TestCase):
    """Test the NaoIndex diagnostic processor class."""

    def test_initialization(self):
        "Test for correct initialization of the processor object."
        proc = NaoIndex()
        self.assertEqual(proc.mslp_stashcode, 'm01s16i222')
        self.assertEqual(proc.result_metadata['var_name'], 'nao_index')
        self.assertEqual(proc.interp_method, 'nearest')

        proc = NaoIndex(mslp_stashcode='m01s23i456', interp_method='linear')
        self.assertEqual(proc.mslp_stashcode, 'm01s23i456')
        self.assertEqual(proc.interp_method, 'linear')

    def test_yx_cube_no_time_coord(self):
        "Test using a simple lat-long cube with no time coordinate."
        mslp_cube = _create_2d_mslp_cube()
        mslp_cube.remove_coord('time')
        cubes = iris.cube.CubeList([mslp_cube])
        proc = NaoIndex()
        result = proc.run(cubes)
        self.assertEqual(len(result), 1)
        nao_cube = result[0]
        self.assertEqual(nao_cube.var_name, 'nao_index')
        self.assertEqual(nao_cube.units, 'hPa')
        self.assertEqual(nao_cube.shape, (1,))
        self.assertEqual(nao_cube.data[0], -30.0)

    def test_yx_cube_scalar_time_coord(self):
        "Test using a simple lat-long cube with a scalar time coordinate."
        mslp_cube = _create_2d_mslp_cube()
        aux_coords = [c.name() for c in mslp_cube.coords(dim_coords=False)]
        self.assertTrue('time' in aux_coords)
        cubes = iris.cube.CubeList([mslp_cube])
        proc = NaoIndex(result_metadata={'units': 'mbar'})
        result = proc.run(cubes)
        self.assertEqual(len(result), 1)
        nao_cube = result[0]
        self.assertEqual(nao_cube.units, 'mbar')
        self.assertEqual(nao_cube.shape, (1,))
        self.assertEqual(nao_cube.data[0], -30.0)
        aux_coords = [c.name() for c in nao_cube.coords(dim_coords=False)]
        self.assertTrue('time' in aux_coords)

    def test_tyx_cube(self):
        "Test using a time-lat-long cube."
        mslp_cube = _create_3d_mslp_cube()
        cubes = iris.cube.CubeList([mslp_cube])
        proc = NaoIndex()
        result = proc.run(cubes)
        self.assertEqual(len(result), 1)
        nao_cube = result[0]
        self.assertEqual(nao_cube.var_name, 'nao_index')
        self.assertEqual(nao_cube.units, 'hPa')
        self.assertEqual(nao_cube.ndim, 1)
        self.assertEqual(nao_cube.shape[0], mslp_cube.shape[0])
        coord_names = [c.name() for c in nao_cube.coords(dim_coords=True)]
        assertCountEqual(self, coord_names, ['time'])
        self.assertEqual(len(nao_cube.coords('latitude')), 1)
        self.assertEqual(len(nao_cube.coords('longitude')), 1)
        npt.assert_allclose(nao_cube.data, np.repeat(-30, nao_cube.shape))

    def test_etyx_cube(self):
        "Test using a realization-time-lat-long cube."
        mslp_cube = _create_4d_mslp_cube()
        cubes = iris.cube.CubeList([mslp_cube])
        proc = NaoIndex(result_metadata={'units': 'mbar'})
        result = proc.run(cubes)
        self.assertEqual(len(result), 1)
        nao_cube = result[0]
        self.assertEqual(nao_cube.var_name, 'nao_index')
        self.assertEqual(nao_cube.units, 'mbar')
        self.assertEqual(nao_cube.ndim, 2)
        self.assertEqual(nao_cube.shape, mslp_cube.shape[:-2])
        coord_names = [c.name() for c in nao_cube.coords(dim_coords=True)]
        assertCountEqual(self, coord_names, ['realization', 'time'])
        self.assertEqual(len(nao_cube.coords('latitude')), 1)
        self.assertEqual(len(nao_cube.coords('longitude')), 1)
        npt.assert_allclose(np.ravel(nao_cube.data),
            np.repeat(-30, np.prod(nao_cube.shape)))

    def test_with_custom_station_coords(self):
        "Test using a time-lat-long cube with custom station coordinates."
        mslp_cube = _create_3d_mslp_cube()
        cubes = iris.cube.CubeList([mslp_cube])
        azores_station = (32.5, 334.3)
        iceland_station = (67.8, 337.2)
        proc = NaoIndex(azores_station=azores_station, iceland_station=iceland_station)
        result = proc.run(cubes)
        self.assertEqual(len(result), 1)
        nao_cube = result[0]
        npt.assert_allclose(nao_cube.data, np.repeat(-40, nao_cube.shape))
        loncrd = nao_cube.coord('longitude')
        npt.assert_allclose(loncrd.bounds, np.array([[0.0, 360.0]]))

    def test_with_invalid_stash_code(self):
        "Test using an input cube with an incorrect STASH code."
        mslp_cube = _create_2d_mslp_cube()
        mslp_cube.attributes['STASH'] = STASH.from_msi('m01s23i456')
        mslp_cube.standard_name = None
        cubes = iris.cube.CubeList([mslp_cube])
        proc = NaoIndex()
        self.assertRaises(DataProcessingError, proc.run, cubes)

    def test_with_invalid_coords(self):
        "Test using an input cube with invalid coordinates."
        proc = NaoIndex()
        mslp_cube = _create_2d_mslp_cube()
        bad_cube = mslp_cube.copy()
        bad_cube.remove_coord('latitude')
        cubes = iris.cube.CubeList([bad_cube])
        self.assertRaises(DataProcessingError, proc.run, cubes)

        bad_cube = mslp_cube.copy()
        bad_cube.coord('latitude').rename('grid_latitude')
        bad_cube.coord('longitude').rename('grid_longitude')
        cubes = iris.cube.CubeList([bad_cube])
        self.assertRaises(DataProcessingError, proc.run, cubes)


def _create_2d_mslp_cube():
    """Build and return a 2D cube of MSLP with an NAO index value of -30."""
    mslp = _create_3d_mslp_cube()
    # return first time slice of 3d cube
    return mslp[0]


def _create_3d_mslp_cube():
    """
    Build and return a 3D cube of MSLP with an NAO index value of -30 for each
    time slice.
    """
    mslp = _create_4d_mslp_cube()
    # return first realization-time slice of 4d cube
    return mslp[0]


def _create_4d_mslp_cube():
    """
    Build and return a 4D cube of MSLP with an NAO index value of -30 for each
    (realization, time) slice.
    """
    data = np.zeros([2,2,9,9], dtype=np.float32)
    for i in range(9):
        data[:,:,i,:] = i * 10   # set row values equal to row latitude!

    mslp = stockcubes.geo_etyx(data=data, start_lat=0, end_lat=80,
        start_lon=-90, end_lon=0, long_name='MSLP', var_name='mslp',
        standard_name='air_pressure_at_sea_level', units='hPa')

    return mslp


if __name__ == '__main__':
    unittest.main()
