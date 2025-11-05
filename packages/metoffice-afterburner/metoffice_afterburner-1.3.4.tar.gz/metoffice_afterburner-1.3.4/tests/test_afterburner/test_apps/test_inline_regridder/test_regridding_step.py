# (C) British Crown Copyright 2021, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Contains unit tests for the regridding step in the InlineRegridder class.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import os
import shutil
import tempfile
import unittest
import logging

try:
    # python3
    from unittest import mock
except ImportError:
    # python2
    import mock

import iris
from iris.fileformats.pp import STASH

try:
    from afterburner.apps.inline_regridder import InlineRegridder
    from afterburner.misc import stockcubes
    from afterburner.utils import NamespacePlus
    got_rose_config = True
except ImportError:
    got_rose_config = False


def cube_compare(self, other):
    """
    Function for comparing selected attributes of two Iris cubes.

    :param self: A synthetic cube representing the expected result cube.
    :param other: The actual result cube to compare against.
    """

    if type(self) != type(other):
        raise AssertionError("cube_compare: object types differ.")

    # Check that shapes are equal.
    if self.shape != other.shape:
        raise AssertionError("cube_compare: cube shapes are unequal."
            "{} != {}".format(self.shape, other.shape))

    lat_s_coord = self.coord('latitude')
    lon_s_coord = self.coord('longitude')

    lat_o_coord = other.coord('latitude')
    lon_o_coord = other.coord('longitude')

    # Check that length of latitude axes are equal.
    if len(lat_s_coord.points) != len(lat_o_coord.points):
        raise AssertionError("cube_compare: latitude dimensions have unequal lengths.")

    # Check that length of longitude axes are equal.
    if len(lon_s_coord.points) != len(lon_o_coord.points):
        raise AssertionError("cube_compare: longitude dimensions have unequal lengths.")

    return True


def diag_compare(self, other):
    """
    Function for comparing selected attributes of two diagnostic definition objects.

    :param self: A synthetic diagnostic definition representing the expected result.
    :param other: The actual diagnostic definition to compare against.
    """

    if type(self) != type(other):
        raise AssertionError("diag_compare: object types differ.")

    for attname in ['runid', 'stream', 'var_id']:
        if getattr(self, attname, None) != getattr(other, attname, None):
            raise AssertionError("diag_compare: values differ for attribute %s." % attname)

    return True


class Matcher:
    """Class for comparing objects in mock calls."""

    def __init__(self, compare, some_obj):
        self.compare = compare
        self.some_obj = some_obj
    def __eq__(self, other):
        return self.compare(self.some_obj, other)


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestRegridData(unittest.TestCase):
    """
    Test the InlineRegridder app's regridding step.
    """

    def setUp(self):
        self.runtime_dir = tempfile.mkdtemp()
        os.environ['RUNTIME_DIR'] = self.runtime_dir
        _fd, self.cfg_file = tempfile.mkstemp(suffix='.conf', dir=self.runtime_dir)

        # Patch the InlineRegridder._load_stream_data() method.
        patch = mock.patch('afterburner.apps.inline_regridder.InlineRegridder._load_stream_data')
        self.mock_load_stream_data = patch.start()
        self.addCleanup(patch.stop)

        # Patch the inline_regridder._load_grid_data() function.
        patch = mock.patch('afterburner.apps.inline_regridder._load_grid_data')
        self.mock_load_grid_data = patch.start()
        self.addCleanup(patch.stop)

        # Patch the InlineRegridder._save_data() method.
        patch = mock.patch('afterburner.apps.inline_regridder.InlineRegridder._save_data')
        self.mock_save_data = patch.start()
        self.addCleanup(patch.stop)

        # Disable logging.
        lgr = logging.getLogger('afterburner.apps')
        lgr.disabled = True

    def tearDown(self):
        if os.path.isdir(self.runtime_dir):
            shutil.rmtree(self.runtime_dir, ignore_errors=True)

        # Re-enable logging
        lgr = logging.getLogger('afterburner.apps')
        lgr.disabled = False

    def test_with_defaults(self):
        """
        Test the regridding step with the default settings, i.e. no rim removal.

        The methods for loading diagnostic data and the target grid are mocked
        but the Iris-based regridding step is called for real so that we can
        assert that the regridded result has the expected coordinate dimensions
        and attributes.
        """

        app_config = """
            [general]
            model_data_dir=$RUNTIME_DIR/datam
            output_dir=$RUNTIME_DIR/output
            input_file_format=pp
            input_filename_template={runid}{dotstream}*.pp
            output_file_format=nc
            output_filename_template={runid}_{stream}_{var_name}.nc

            [um]
            cylc_task_name=atmos_main
            sentinel_file_ext=

            [netcdf_saver]
            netcdf_format=NETCDF4_CLASSIC

            [file:grids.nl]
            source=namelist:grids(:)

            [namelist:grids(um_n48e_lsm)]
            file_path=/data/users/mary/testdata/qrparm.mask.n48e
            var_id=land_binary_mask

            [namelist:grids(um_n96e_lsm)]
            file_path=/data/users/mary/testdata/qrparm.mask.n96e
            var_id=land_binary_mask

            [file:regridders.nl]
            source=namelist:regridders(:)

            [namelist:regridders(n48e_reg_lat_lon)]
            target_grid=um_n48e_lsm
            scheme=iris.analysis.AreaWeighted

            [file:diagnostics.nl]
            source=namelist:diagnostics(:)

            [namelist:diagnostics(_defaults_)]
            enabled=true
            var_id=m??s??i???
            model_name=UM
            suite_name=mi-ad191
            streams=apm
            calendar=360_day
            regridder=n48e_reg_lat_lon

            [namelist:diagnostics(tas)]
            enabled=true
            var_id=m01s00i024
            var_name=tas
        """

        # Create the app config file for the text string above.
        _create_app_config_file(self.cfg_file, app_config)

        # Create a synthetic cube of air temperature data to regrid.
        stashcode = STASH.from_msi('m01s00i024')
        diag_cube = stockcubes.geo_tyx(shape=(2, 144, 192))
        diag_cube.attributes['STASH'] = stashcode
        self.mock_load_stream_data.return_value = iris.cube.CubeList([diag_cube])

        # Create the cube that contains the target grid.
        grid_cube = stockcubes.geo_yx(shape=(72, 96))
        self.mock_load_grid_data.return_value = grid_cube

        # Create the result cube.
        result_cube = stockcubes.geo_tyx(shape=(2, 72, 96))
        result_cube.attributes['STASH'] = stashcode
        result_cube.attributes['history'] = "Data generated by the InlineRegridder app"

        # Create and run the InlineRegridder app.
        args = ['-c', self.cfg_file, '-q']
        app = InlineRegridder(args)
        app.run()

        # Verify that mocked functions were called.
        self.mock_load_stream_data.assert_called_once()
        self.mock_load_grid_data.assert_called_once()
        self.mock_save_data.assert_called_once()

        # Verify that the cube passed to the save operation has the expected
        # shape. This is done using Matcher objects which call the appropriate
        # comparison function on the 'real' and mock objects.
        diag_defn = NamespacePlus(runid='ad191', stream='apm', var_id=stashcode)
        match_diag = Matcher(diag_compare, diag_defn)
        match_result = Matcher(cube_compare, result_cube)
        self.mock_save_data.assert_called_with(match_diag, match_result)

    def test_with_rim_removal(self):
        """
        Test the regridding step with rim removal.

        The methods for loading diagnostic data and the target grid are mocked
        but the Iris-based regridding step is called for real so that we can
        assert that the regridded result has the expected coordinate dimensions
        and attributes.
        """

        app_config = """
            [general]
            model_data_dir=$RUNTIME_DIR/datam
            output_dir=$RUNTIME_DIR/output
            input_file_format=pp
            input_filename_template={runid}{dotstream}*.pp
            output_file_format=nc
            output_filename_template={runid}_{stream}_{var_name}.nc

            [um]
            cylc_task_name=atmos_main
            sentinel_file_ext=

            [netcdf_saver]
            netcdf_format=NETCDF4_CLASSIC

            [file:grids.nl]
            source=namelist:grids(:)

            [namelist:grids(um_n48e_lsm)]
            file_path=/data/users/mary/testdata/qrparm.mask.n48e
            var_id=land_binary_mask

            [namelist:grids(um_n96e_lsm)]
            file_path=/data/users/mary/testdata/qrparm.mask.n96e
            var_id=land_binary_mask

            [file:regridders.nl]
            source=namelist:regridders(:)

            [namelist:regridders(n48e_reg_lat_lon)]
            target_grid=um_n48e_lsm
            scheme=iris.analysis.AreaWeighted

            [file:diagnostics.nl]
            source=namelist:diagnostics(:)

            [namelist:diagnostics(_defaults_)]
            enabled=true
            var_id=m??s??i???
            model_name=UM
            suite_name=mi-ad191
            streams=apm
            calendar=360_day
            regridder=n48e_reg_lat_lon

            [namelist:diagnostics(tas)]
            enabled=true
            remove_rim=true
            rim_width=2
            var_id=m01s00i024
            var_name=tas
        """

        # Create the app config file for the text string above.
        _create_app_config_file(self.cfg_file, app_config)

        # Patch the InlineRegridder._regrid_data() method.
        patch = mock.patch('afterburner.apps.inline_regridder.InlineRegridder._regrid_data')
        self.mock_regrid_data = patch.start()
        self.addCleanup(patch.stop)

        # Create a synthetic cube of air temperature data to regrid.
        stashcode = STASH.from_msi('m01s00i024')
        diag_cube = stockcubes.geo_tyx(shape=(2, 144, 192))
        diag_cube.attributes['STASH'] = stashcode
        self.mock_load_stream_data.return_value = iris.cube.CubeList([diag_cube])

        # Create the cube that contains the target grid.
        grid_cube = stockcubes.geo_yx(shape=(72, 96))
        self.mock_load_grid_data.return_value = grid_cube

        # Create the de-rimmed cube, which should be sized to account for the
        # removed rim.
        trimmed_cube = stockcubes.geo_tyx(shape=(2, 140, 188))
        trimmed_cube.attributes['STASH'] = stashcode

        # Create the result cube.
        result_cube = stockcubes.geo_tyx(shape=(2, 72, 96))
        result_cube.attributes['STASH'] = stashcode
        result_cube.attributes['history'] = "Data generated by the InlineRegridder app"
        self.mock_regrid_data.return_value = result_cube

        # Create and run the InlineRegridder app.
        args = ['-c', self.cfg_file, '-q']
        app = InlineRegridder(args)
        app.run()

        # Verify that mocked functions were called.
        self.mock_load_stream_data.assert_called_once()
        self.mock_save_data.assert_called_once()

        # Verify that the cube passed to the regrid operation has the expected
        # shape. This is done using Matcher objects which call the appropriate
        # comparison function on the 'real' and mock objects.
        diag_defn = NamespacePlus(runid='ad191', stream='apm', var_id=stashcode)
        match_diag = Matcher(diag_compare, diag_defn)
        match_result = Matcher(cube_compare, trimmed_cube)
        self.mock_regrid_data.assert_called_with(match_diag, match_result)

        match_result = Matcher(cube_compare, result_cube)
        self.mock_save_data.assert_called_with(match_diag, match_result)


def _create_app_config_file(config_file, config_text):
    with open(config_file, 'w') as fh:
        fh.writelines([line.strip()+'\n' for line in config_text.split('\n')])


if __name__ == '__main__':
    unittest.main()
