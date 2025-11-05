# (C) British Crown Copyright 2016, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.processors.diags.atmos.toa_radiation_balance module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import unittest
import iris
from iris.fileformats.pp import STASH
from iris.tests.stock import lat_lon_cube
from afterburner.processors.diags import ToaRadiationBalance
import numpy.testing as npt


class TestToaRadiationBalanceProcessor(unittest.TestCase):
    """Test the ToaRadiationBalance diagnostic processor class."""

    def setUp(self):
        self.cubelist = self._create_radiation_cubes()

    def test_init(self):
        proc = ToaRadiationBalance(result_metadata={'var_name': 'toa_rad_bal'})
        self.assertEqual(proc.result_metadata['standard_name'], 'toa_net_downward_radiative_flux')
        self.assertEqual(proc.result_metadata['var_name'], 'toa_rad_bal')

    def test_run(self):
        proc = ToaRadiationBalance(result_metadata={'units': 'W ft-2'})
        cubes = proc.run(self.cubelist)
        self.assertEqual(len(cubes), 1)
        radbal = cubes[0]
        self.assertEqual(radbal.long_name, proc.result_metadata['long_name'])
        self.assertEqual(radbal.var_name, proc.result_metadata['var_name'])
        self.assertEqual(radbal.units, 'W ft-2')
        self.assertEqual(radbal.shape, self.cubelist[0].shape)
        self.assertTrue(radbal.attributes.get('history') is not None)
        self.assertTrue(radbal.attributes.get('STASH') is None)
        testdata = radbal.data.copy()
        testdata[:] = 2.5   # result of (10 - 5 - 2.5) 
        npt.assert_allclose(radbal.data, testdata)

    def _create_radiation_cubes(self):
        sw_in = lat_lon_cube()
        sw_in.standard_name = 'toa_incoming_shortwave_flux'
        sw_in.attributes['STASH'] = STASH.from_msi('m01s01i207')
        sw_in.data = sw_in.data.astype('float32')
        sw_in.data[:] = 10.0

        sw_out = lat_lon_cube()
        sw_out.standard_name = 'toa_outgoing_shortwave_flux'
        sw_out.attributes['STASH'] = STASH.from_msi('m01s01i208')
        sw_out.data = sw_out.data.astype('float32')
        sw_out.data[:] = 5.0

        lw_out = lat_lon_cube()
        lw_out.standard_name = 'toa_outgoing_longwave_flux'
        lw_out.attributes['STASH'] = STASH.from_msi('m01s03i332')
        lw_out.data = lw_out.data.astype('float32')
        lw_out.data[:] = 2.5

        return iris.cube.CubeList([sw_in, sw_out, lw_out])


if __name__ == '__main__':
    unittest.main()
