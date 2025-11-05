# (C) British Crown Copyright 2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Test the afterburner.apps.model_monitor2.ModelMonitor2 application using diagnostics
from ensemble model runs.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import assertCountEqual

import os
import sys
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
    from afterburner.apps.model_monitor2 import ModelMonitor2
    from afterburner.misc import stockcubes
    got_rose_config = True
except ImportError:
    got_rose_config = False


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestEnsembleRuns(unittest.TestCase):
    """
    Test the afterburner.apps.model_monitor2.ModelMonitor2 application using diagnostics
    from ensemble model runs.
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

    def test_one_model_multi_sims_one_diag(self):
        "Test single diag from multiple simulations of a single model."

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=EnsembleVarSplit
            cache_dir=$RUNTIME_DIR/ensvarsplit
            output_dir=$RUNTIME_DIR/output

            [namelist:models(anqjm-m1)]
            enabled=true
            label=ANQJM/m1
            name=anqjm/m1
            plot_order=1

            [namelist:models(anqjm-m2)]
            enabled=true
            label=ANQJM/m2
            name=anqjm/m2
            plot_order=2

            [namelist:diags(tas_global)]
            enabled=true
            stashcode=m01s00i024
        """

        test_cube = stockcubes.geo_tyx()
        test_cube.attributes['STASH'] = STASH.from_msi('m01s00i024')
        self.mock_load_model_data.side_effect = [iris.cube.CubeList([x]) for x in
            (test_cube,)*2]

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.assertEqual(self.mock_load_model_data.call_count, 2)

        # test for existence of html output file
        html_file = os.path.join(app.html_output_dir, 'cmm.html')
        self.assertTrue(os.path.isfile(html_file))

        # test for existence of 2 netcdf files
        nc_dir = os.path.join(app.nc_output_dir, 'awmean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 2)

        # test for existence of 1 image file
        img_dir = os.path.join(app.img_output_dir, 'awmean')
        img_files = os.listdir(img_dir)
        self.assertEqual(len(img_files), 1)

        ens_ids = [x.ens_id for x in app.model_defns.values()]
        assertCountEqual(self, ens_ids, ['m1', 'm2'])

    def test_multi_models_multi_sims_one_diag(self):
        "Test single diag from multiple simulations of multiple models."

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=EnsembleVarSplit
            cache_dir=$RUNTIME_DIR/ensvarsplit
            output_dir=$RUNTIME_DIR/output

            [namelist:models(anqjm-m1)]
            enabled=true
            label=ANQJM/m1
            name=anqjm/m1
            plot_order=1

            [namelist:models(anqjm-m2)]
            enabled=true
            label=ANQJM/m2
            name=anqjm/m2
            plot_order=2

            [namelist:models(anqjn-n1)]
            enabled=true
            label=ANQJN/n1
            name=anqjn/n1
            plot_order=1

            [namelist:models(anqjn-n2)]
            enabled=true
            label=ANQJN/n2
            name=anqjn/n2
            plot_order=2

            [namelist:diags(tas_global)]
            enabled=true
            stashcode=m01s00i024
        """

        test_cube = stockcubes.geo_tyx()
        test_cube.attributes['STASH'] = STASH.from_msi('m01s00i024')
        self.mock_load_model_data.side_effect = [iris.cube.CubeList([x]) for x in
            (test_cube,)*4]

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.assertEqual(self.mock_load_model_data.call_count, 4)

        # test for existence of html output file
        html_file = os.path.join(app.html_output_dir, 'cmm.html')
        self.assertTrue(os.path.isfile(html_file))

        # test for existence of 4 netcdf files
        nc_dir = os.path.join(app.nc_output_dir, 'awmean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 4)

        # test for existence of 1 image file
        img_dir = os.path.join(app.img_output_dir, 'awmean')
        img_files = os.listdir(img_dir)
        self.assertEqual(len(img_files), 1)

        ens_ids = [x.ens_id for x in app.model_defns.values()]
        assertCountEqual(self, ens_ids, ['m1', 'm2', 'n1', 'n2'])

    def test_multi_models_multi_sims_multi_diags(self):
        "Test multiple diags from multiple simulations of multiple models."

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=EnsembleVarSplit
            cache_dir=$RUNTIME_DIR/ensvarsplit
            output_dir=$RUNTIME_DIR/output

            [namelist:models(anqjm-m1)]
            enabled=true
            label=ANQJM/m1
            name=anqjm/m1
            plot_order=1

            [namelist:models(anqjm-m2)]
            enabled=true
            label=ANQJM/m2
            name=anqjm/m2
            plot_order=2

            [namelist:models(anqjn-n1)]
            enabled=true
            label=ANQJN/n1
            name=anqjn/n1
            plot_order=1

            [namelist:models(anqjn-n2)]
            enabled=true
            label=ANQJN/n2
            name=anqjn/n2
            plot_order=2

            [namelist:diags(tas_global)]
            enabled=true
            stashcode=m01s00i024

            [namelist:diags(tas_tropics)]
            enabled=true
            region_name=Tropics
            region_extent=0,-30,360,30
            stashcode=m01s00i024
        """

        test_cube = stockcubes.geo_tyx()
        test_cube.attributes['STASH'] = STASH.from_msi('m01s00i024')
        self.mock_load_model_data.side_effect = [iris.cube.CubeList([x]) for x in
            (test_cube,)*8]

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file, '-q']
        app = ModelMonitor2(args)
        app.run()

        self.assertEqual(self.mock_load_model_data.call_count, 8)

        # test for existence of html output file
        html_file = os.path.join(app.html_output_dir, 'cmm.html')
        self.assertTrue(os.path.isfile(html_file))

        # test for existence of 8 netcdf files
        nc_dir = os.path.join(app.nc_output_dir, 'awmean')
        nc_files = os.listdir(nc_dir)
        self.assertEqual(len(nc_files), 8)

        # test for existence of 2 image file
        img_dir = os.path.join(app.img_output_dir, 'awmean')
        img_files = os.listdir(img_dir)
        self.assertEqual(len(img_files), 2)

        ens_ids = {x.ens_id for x in app.model_defns.values()}
        assertCountEqual(self, ens_ids, {'m1', 'm2', 'n1', 'n2'})


def _create_app_config_file(config_file, config_text):
    with open(config_file, 'w') as fh:
        fh.writelines([line.strip()+'\n' for line in config_text.split('\n')])


if __name__ == '__main__':
    unittest.main()
