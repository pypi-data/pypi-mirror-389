# (C) British Crown Copyright 2016-2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Unit tests for the afterburner.processors.writers.netcdf_writer module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import assertCountEqual

import os
import unittest

try:
    # python3
    from unittest import mock
except ImportError:
    # python2
    import mock

import iris
from afterburner import compare_iris_version
from afterburner.processors.writers.netcdf_writer import NetcdfFileWriter
from afterburner.misc.stockcubes import geo_tyx


class TestNetcdfFileWriter(unittest.TestCase):
    """Test the NetcdfFileWriter class."""

    def setUp(self):
        # Construct a temp filename. We don't use the mkstemp function from the
        # standard tempfile module because that actually creates the temp file
        # and, in most cases, we don't want that to happen.
        tmpdir = os.environ.get('TMPDIR', '/var/tmp')
        tmpfile = "tmp_u{0}_p{1}.nc".format(os.getuid(), os.getpid())
        self.ncfile = os.path.join(tmpdir, tmpfile)

        # Create a netCDF file writer object.
        self.writer = NetcdfFileWriter()

        # Obtain some test cubes.
        self.tyz_cube = geo_tyx(standard_name='air_temperature')

    def tearDown(self):
        try:
            os.remove(self.ncfile)
        except OSError:
            pass

    @mock.patch('iris.save')
    def test_default_usage(self, mock_save):
        self.writer.run(self.tyz_cube, self.ncfile)
        mock_save.assert_called_once()

    @mock.patch('afterburner.processors.writers.netcdf_writer.NetcdfFileWriter.run')
    def test_write_method(self, mock_run_method):
        self.writer.write(self.tyz_cube, self.ncfile)
        mock_run_method.assert_called_with(self.tyz_cube, self.ncfile)

    @mock.patch('iris.save')
    def test_with_overwrite_option(self, mock_save):
        open(self.ncfile, 'w')   # touch the output file
        self.writer.run(self.tyz_cube, self.ncfile, overwrite=True)
        mock_save.assert_called_once()

    def test_without_overwrite_option(self):
        open(self.ncfile, 'w')   # touch the output file
        self.assertRaises(IOError, self.writer.run, self.tyz_cube, self.ncfile)

    @mock.patch('iris.save')
    def test_append_to_nonexistent_file(self, mock_save):
        # appending to a non-existent file is equivalent to a plain write
        self.writer.run(self.tyz_cube, self.ncfile, append=True)
        mock_save.assert_called_once()

    def test_append_to_extant_file1(self):
        # first create the output file
        self.writer.run(self.tyz_cube, self.ncfile)
        self.assertTrue(os.path.exists(self.ncfile))
        # then try appending an extra cube (of a different quantity) to it
        extra_cube = geo_tyx(standard_name='rainfall_amount', units='kg m-2 s-1')
        self.writer.run(extra_cube, self.ncfile, append=True)
        futures = compare_iris_version('2', 'lt') and {'netcdf_promote': True} or {}
        with iris.FUTURE.context(**futures):
            cubes = iris.load(self.ncfile)
        self.assertEqual(len(cubes), 2)
        assertCountEqual(self, ['air_temperature', 'rainfall_amount'],
            [c.name() for c in cubes])

    def test_append_to_extant_file2(self):
        # first create the output file
        self.writer.run(self.tyz_cube, self.ncfile)
        self.assertTrue(os.path.exists(self.ncfile))
        # then try appending an extra cube (of the same quantity) to it
        extra_cube = geo_tyx()
        taxis = self.tyz_cube.coord('time')
        tcoord = taxis.copy(points=taxis.points+360)
        tcoord.guess_bounds()
        ntimes = len(taxis.points)
        extra_cube.replace_coord(tcoord)
        self.writer.run(extra_cube, self.ncfile, append=True, equalise_attrs=True)
        futures = compare_iris_version('2', 'lt') and {'netcdf_promote': True} or {}
        with iris.FUTURE.context(**futures):
            cubes = iris.load(self.ncfile)
        self.assertEqual(len(cubes), 1)
        self.assertEqual(len(cubes[0].coord('time').points), ntimes*2)

    @mock.patch('iris.save')
    def test_init_save_options(self, mock_save):
        writer = NetcdfFileWriter(complevel=4, shuffle=True)
        writer.run(self.tyz_cube, self.ncfile)
        self.assertEqual(mock_save.call_args[1]['complevel'], 4)
        self.assertTrue(mock_save.call_args[1]['shuffle'])

    @mock.patch('iris.save')
    def test_runtime_save_options(self, mock_save):
        self.writer.run(self.tyz_cube, self.ncfile, netcdf_format='NETCDF3_CLASSIC',
            zlib=False)
        self.assertEqual(mock_save.call_args[1]['netcdf_format'], 'NETCDF3_CLASSIC')
        self.assertFalse(mock_save.call_args[1]['zlib'])


if __name__ == '__main__':
    unittest.main()
