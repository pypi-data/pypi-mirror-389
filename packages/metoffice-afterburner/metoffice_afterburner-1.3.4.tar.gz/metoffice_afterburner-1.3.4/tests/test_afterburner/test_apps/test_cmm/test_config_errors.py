# (C) British Crown Copyright 2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Test the afterburner.apps.model_monitor.ModelMonitor application with various
config file errors.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

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

try:
    from afterburner.apps.model_monitor import ModelMonitor
    from afterburner.exceptions import AppConfigError
    got_rose_config = True
except ImportError:
    got_rose_config = False


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestConfigErrors(unittest.TestCase):
    """
    Test the afterburner.apps.model_monitor.ModelMonitor application with various
    config file errors.
    """

    def setUp(self):
        self.runtime_dir = tempfile.mkdtemp()
        os.environ['RUNTIME_DIR'] = self.runtime_dir
        _fd, self.cfg_file = tempfile.mkstemp(suffix='.conf', dir=self.runtime_dir)

        # Patch the ModelMonitor._load_latest_model_data() function.
        patch = mock.patch('afterburner.apps.model_monitor.ModelMonitor._load_latest_model_data')
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

    def test_no_stashcode(self):
        "Test for a missing stashcode."

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=VarSplit
            cache_dir=$RUNTIME_DIR/varsplit
            output_dir=$RUNTIME_DIR/output

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(tas_global)]
            enabled=true
        """

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file]
        self.assertRaises(AppConfigError, ModelMonitor, args)

    def test_invalid_stashcode(self):
        "Test for an invalid stashcode."

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=VarSplit
            cache_dir=$RUNTIME_DIR/varsplit
            output_dir=$RUNTIME_DIR/output

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(tas_global)]
            enabled=true
            stashcode=m1s0i024
        """

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file]
        app = ModelMonitor(args)
        self.assertRaises(AppConfigError, app.run)

    def test_stashcode_and_var_name(self):
        "Test for the presence of both stashcode and var_name properties."

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=VarSplit
            cache_dir=$RUNTIME_DIR/varsplit
            output_dir=$RUNTIME_DIR/output

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(tas_global)]
            enabled=true
            stashcode=m01s00i024
            var_name=tas_global
        """

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file]
        self.assertRaises(AppConfigError, ModelMonitor, args)

    def test_var_name_without_formula(self):
        "Test for the presence of a var_name property without a formula definition."

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=VarSplit
            cache_dir=$RUNTIME_DIR/varsplit
            output_dir=$RUNTIME_DIR/output

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(albedo)]
            enabled=true
            var_name=albedo
        """

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file]
        app = ModelMonitor(args)
        self.assertRaises(AppConfigError, app.run)

    def test_unexpected_ensemble_defn(self):
        """Test for an unexpected ensemble-style model definition."""

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=VarSplit
            cache_dir=$RUNTIME_DIR/varsplit
            output_dir=$RUNTIME_DIR/output

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm/r1i1p1
            plot_order=1

            [namelist:diags(tas_global)]
            enabled=true
            stashcode=m01s00i024
        """

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file]
        self.assertRaises(AppConfigError, ModelMonitor, args)

    def test_unexpected_nonensemble_defn(self):
        """Test for an unexpected non-ensemble-style model definition."""

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

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(tas_global)]
            enabled=true
            stashcode=m01s00i024
        """

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file]
        self.assertRaises(AppConfigError, ModelMonitor, args)

    def test_invalid_data_cache_type(self):
        "Test for an invalid data cache type."

        app_config = """
            [file:models.nl]
            source=namelist:models(:)

            [file:diags.nl]
            source=namelist:diags(:)

            [general]
            sync_with_mass=false
            cache_type=BananaSplit
            cache_dir=$RUNTIME_DIR/bananasplit
            output_dir=$RUNTIME_DIR/output

            [namelist:models(anqjm)]
            enabled=true
            label=ANQJM
            name=anqjm
            plot_order=1

            [namelist:diags(tas_global)]
            enabled=true
            stashcode=m1s0i024
        """

        _create_app_config_file(self.cfg_file, app_config)
        args = ['-c', self.cfg_file]
        self.assertRaises(ValueError, ModelMonitor, args)


def _create_app_config_file(config_file, config_text):
    with open(config_file, 'w') as fh:
        fh.writelines([line.strip()+'\n' for line in config_text.split('\n')])


if __name__ == '__main__':
    unittest.main()
