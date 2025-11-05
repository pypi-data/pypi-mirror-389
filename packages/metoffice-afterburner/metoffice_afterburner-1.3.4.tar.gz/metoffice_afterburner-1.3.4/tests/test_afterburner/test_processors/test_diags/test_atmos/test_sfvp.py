# (C) British Crown Copyright 2016, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.processors.diags.atmos.streamfunc_velpot module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import sys
import unittest
import numpy as np
import numpy.testing as npt
import iris
from iris.fileformats.pp import STASH


@unittest.skipUnless('windspharm' in sys.modules, "windspharm module not found")
class TestStreamFuncVelPotProcessor(unittest.TestCase):
    """Test the StreamFuncVelPot diagnostic processor class."""

    def setUp(self):
        self.cubelist = _create_windspeed_cubes()

    def test_run(self):
        from afterburner.processors.diags.atmos.streamfunc_velpot import StreamFuncVelPot
        proc = StreamFuncVelPot()
        self.assertEqual(proc.uwind_stashcode, 'm01s30i201')
        self.assertEqual(proc.vwind_stashcode, 'm01s30i202')

        cubes = proc.run(self.cubelist)
        self.assertEqual(len(cubes), 2)
        strmfn, velpot = cubes

        self.assertEqual(strmfn.standard_name, 'atmosphere_horizontal_streamfunction')
        self.assertEqual(strmfn.var_name, 'streamfunction')
        self.assertEqual(strmfn.units, 'm2 s-1')
        self.assertEqual(strmfn.shape, self.cubelist[0].shape)
        self.assertTrue(strmfn.attributes.get('history') is not None)
        self.assertTrue(strmfn.attributes.get('STASH') is None)

        self.assertEqual(velpot.standard_name, 'atmosphere_horizontal_velocity_potential')
        self.assertEqual(velpot.var_name, 'velocity_potential')
        self.assertEqual(velpot.units, 'm2 s-1')
        self.assertEqual(velpot.shape, self.cubelist[0].shape)
        self.assertTrue(velpot.attributes.get('history') is not None)
        self.assertTrue(velpot.attributes.get('STASH') is None)


@unittest.skipUnless('windspharm' in sys.modules, "windspharm module not found")
class TestStreamFunction(unittest.TestCase):
    """Test the StreamFunction diagnostic processor class."""

    def setUp(self):
        self.cubelist = _create_windspeed_cubes()

    def test_run(self):
        from afterburner.processors.diags.atmos.streamfunc_velpot import StreamFunction
        proc = StreamFunction()
        cubes = proc.run(self.cubelist)
        self.assertEqual(len(cubes), 1)
        strmfn = cubes[0]
        self.assertEqual(strmfn.standard_name, 'atmosphere_horizontal_streamfunction')
        self.assertEqual(strmfn.var_name, 'streamfunction')

    # TODO: Add a test which verifies that this class produces correct data values.


@unittest.skipUnless('windspharm' in sys.modules, "windspharm module not found")
class TestVelocityPotential(unittest.TestCase):
    """Test the VelocityPotential diagnostic processor class."""

    def setUp(self):
        self.cubelist = _create_windspeed_cubes()

    def test_run(self):
        from afterburner.processors.diags.atmos.streamfunc_velpot import VelocityPotential 
        proc = VelocityPotential()
        cubes = proc.run(self.cubelist)
        self.assertEqual(len(cubes), 1)
        velpot = cubes[0]
        self.assertEqual(velpot.standard_name, 'atmosphere_horizontal_velocity_potential')
        self.assertEqual(velpot.var_name, 'velocity_potential')

    # TODO: Add a test which verifies that this class produces correct data values.


def _create_windspeed_cubes():
    """Create 3D cubes of u-wind and v-wind for use in the above test classes."""
    lats = np.arange(-90., 91., 30.)
    lons = np.arange(0., 360., 30.)
    shape = (1, len(lats), len(lons))

    loncrd = iris.coords.DimCoord(lons, standard_name='longitude', units='degrees_east')
    latcrd = iris.coords.DimCoord(lats, standard_name='latitude', units='degrees_north')
    levcrd = iris.coords.DimCoord(850, long_name='pressure', units='hPa')

    uwind = iris.cube.Cube(np.ones(shape), standard_name='x_wind', units='m s-1')
    uwind.add_dim_coord(levcrd, 0)
    uwind.add_dim_coord(latcrd, 1)
    uwind.add_dim_coord(loncrd, 2)
    uwind.attributes['STASH'] = STASH.from_msi('m01s30i201')

    vwind = iris.cube.Cube(np.ones(shape), standard_name='y_wind', units='m s-1')
    vwind.add_dim_coord(levcrd, 0)
    vwind.add_dim_coord(latcrd, 1)
    vwind.add_dim_coord(loncrd, 2)
    vwind.attributes['STASH'] = STASH.from_msi('m01s30i202')

    return iris.cube.CubeList([uwind, vwind])


if __name__ == '__main__':
    unittest.main()
