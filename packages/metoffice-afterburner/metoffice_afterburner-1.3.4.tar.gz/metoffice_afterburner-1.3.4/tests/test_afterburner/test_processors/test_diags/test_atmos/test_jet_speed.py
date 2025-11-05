# (C) British Crown Copyright 2016-2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.processors.diags.atmos.jet_speed module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import unittest
import numpy as np

import iris
from iris.fileformats.pp import STASH

from afterburner.misc import stockcubes
from afterburner.processors.diags import JetSpeed


class TestJetSpeedProcessor(unittest.TestCase):
    """Test the JetSpeed diagnostic processor class."""

    def setUp(self):
        self.cubelist = self._create_input_cubes()

    def test_init(self):
        proc = JetSpeed()
        self.assertEqual(proc.lp_cutoff, 0.1)
        self.assertEqual(proc.lp_window, 61)
        self.assertEqual(proc.result_metadata['long_name'], 'Jet Strength')
        self.assertEqual(proc.result_metadata['var_name'], 'jet_strength')

    def test_with_defaults(self):
        proc = JetSpeed()
        uwind_cube = self.cubelist[0]
        self.assertEqual(uwind_cube.shape, (120, 19, 36))
        cubes = proc.run(uwind_cube)
        self.assertEqual(len(cubes), 1)
        jspeed = cubes[0]
        self.assertEqual(jspeed.long_name, proc.result_metadata['long_name'])
        self.assertEqual(jspeed.var_name, proc.result_metadata['var_name'])
        self.assertEqual(jspeed.units, uwind_cube.units)
        self.assertEqual(jspeed.shape, (uwind_cube.shape[0] - proc.lp_window + 1,))
        self.assertTrue(jspeed.attributes.get('history') is not None)
        aux_coords = [c.name() for c in jspeed.coords(dim_coords=False)]
        self.assertTrue('latitude' in aux_coords)

    def test_with_custom_metadata(self):
        metadata = {'long_name': 'Jet Speed', 'var_name': 'jet_speed'}
        proc = JetSpeed(result_metadata=metadata)
        cubes = proc.run(self.cubelist)
        self.assertEqual(len(cubes), 1)
        jspeed = cubes[0]
        self.assertEqual(jspeed.long_name, 'Jet Speed')
        self.assertEqual(jspeed.var_name, 'jet_speed')

    def test_with_twocubes_on(self):
        proc = JetSpeed(twocubes=True)
        cubes = proc.run(self.cubelist)
        self.assertEqual(len(cubes), 2)
        jspeed, jlat = cubes
        self.assertEqual(np.rint(jspeed.data[0]), 60.0)
        self.assertEqual(jlat.long_name, 'Jet Latitude')
        self.assertEqual(jlat.var_name, 'jet_latitude')
        self.assertEqual(jlat.ndim, 1)
        self.assertEqual(jlat.data[0], 50.0)

    def test_with_custom_sector(self):
        proc = JetSpeed(sector=[-30, 30, -80, -10])
        self.assertEqual(proc.sector, [-30, 30, -80, -10])
        cubes = proc.run(self.cubelist)
        self.assertEqual(len(cubes), 1)
        jspeed = cubes[0]
        self.assertEqual(np.rint(jspeed.data[0]), 60.0)
        jlat = jspeed.coord('latitude')
        self.assertEqual(jlat.points[0], -50.0)

    def test_with_custom_window(self):
        proc = JetSpeed(lp_window=41)
        self.assertEqual(proc.lp_window, 41)
        uwind_cube = self.cubelist[0]
        cubes = proc.run(uwind_cube)
        self.assertEqual(len(cubes), 1)
        jspeed = cubes[0]
        self.assertEqual(jspeed.shape, (uwind_cube.shape[0] - proc.lp_window + 1,))
        self.assertEqual(np.rint(jspeed.data[0]), 60.0)

    def test_with_invalid_filter_window(self):
        proc = JetSpeed(lp_window=121)
        assert proc.lp_window == 121
        with self.assertRaises(ValueError):
            proc.run(self.cubelist)

    def _create_input_cubes(self):
        # create a cube of eastward windspeed with maximum values at latitude
        # 50N and 50N for each time step.
        halfcol = np.array([0, 15, 30, 45, 60, 45, 30, 15, 5], dtype='f')
        col = np.concatenate([halfcol, [0], halfcol[::-1]]).reshape(19, 1)
        data = np.tile(col, [120, 1, 36])
        uwind = stockcubes.geo_tyx(data=data, standard_name='eastward_wind',
            long_name='Eastward Windspeed', var_name='uwind', units='m s-1')
        uwind.attributes['STASH'] = STASH.from_msi('m01s30i201')

        return iris.cube.CubeList([uwind])


if __name__ == '__main__':
    unittest.main()
