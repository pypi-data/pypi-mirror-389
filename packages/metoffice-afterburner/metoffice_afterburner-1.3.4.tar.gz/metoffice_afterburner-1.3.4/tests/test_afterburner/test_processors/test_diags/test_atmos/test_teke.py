# (C) British Crown Copyright 2016, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.processors.diags.atmos.teke module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import unittest
import iris
from iris.fileformats.pp import STASH
from iris.tests.stock import lat_lon_cube
from afterburner.processors.diags import TransientEddyKineticEnergy
import numpy.testing as npt


class TestTekeProcessor(unittest.TestCase):
    """Test the TransientEddyKineticEnergy diagnostic processor class."""

    def setUp(self):
        self.cubelist = self._create_windspeed_cubes()

    def test_init(self):
        proc = TransientEddyKineticEnergy()
        self.assertEqual(proc.uwind_stashcode, 'm01s30i201')
        self.assertEqual(proc.vwind_stashcode, 'm01s30i202')
        self.assertEqual(proc.result_metadata['var_name'], 'teke')
        self.assertEqual(proc.result_metadata['units'], 'm2 s-2')

    def test_run(self):
        proc = TransientEddyKineticEnergy()
        cubes = proc.run(self.cubelist)
        self.assertEqual(len(cubes), 1)
        teke = cubes[0]
        self.assertEqual(teke.long_name, proc.result_metadata['long_name'])
        self.assertEqual(teke.var_name, proc.result_metadata['var_name'])
        self.assertEqual(teke.units, proc.result_metadata['units'])
        self.assertEqual(teke.shape, self.cubelist[0].shape)
        self.assertTrue(teke.attributes.get('history') is not None)
        self.assertTrue(teke.attributes.get('STASH') is None)
        testdata = teke.data.copy()
        testdata[:] = 2.0   # result of (3 + 3 - 1**2 - 1**2) * 0.5
        npt.assert_allclose(teke.data, testdata)

    def _create_windspeed_cubes(self):
        uwind = lat_lon_cube()
        uwind.attributes['STASH'] = STASH.from_msi('m01s30i201')
        uwind.data[:] = 1

        vwind = lat_lon_cube()
        vwind.attributes['STASH'] = STASH.from_msi('m01s30i202')
        vwind.data[:] = 1

        u2wind = lat_lon_cube()
        u2wind.attributes['STASH'] = STASH.from_msi('m01s30i211')
        u2wind.data[:] = 3

        v2wind = lat_lon_cube()
        v2wind.attributes['STASH'] = STASH.from_msi('m01s30i222')
        v2wind.data[:] = 3

        return iris.cube.CubeList([uwind, vwind, u2wind, v2wind])


if __name__ == '__main__':
    unittest.main()
