# (C) British Crown Copyright 2016, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Unit tests for the afterburner.config module.
"""
from __future__ import (absolute_import, division)
from six.moves import (filter, input, map, range, zip)

import os
import tempfile
import unittest
import afterburner
from afterburner.config import ConfigProvider


class TestConfig(unittest.TestCase):

    def setUp(self):
        home_dir = afterburner.__file__
        for i in range(3): home_dir = os.path.dirname(home_dir)
        self.home_dir = home_dir

    def test_home_dir(self):
        config = ConfigProvider()
        self.assertEqual(config.home_dir, self.home_dir)

    def test_bin_dir(self):
        config = ConfigProvider()
        expected = os.path.join(self.home_dir, 'bin')
        self.assertEqual(config.bin_dir, expected)

    def test_etc_dir(self):
        config = ConfigProvider()
        expected = os.path.join(self.home_dir, 'etc')
        self.assertEqual(config.etc_dir, expected)

    def test_template_dir(self):
        config = ConfigProvider()
        expected = os.path.join(self.home_dir, 'etc', 'templates')
        self.assertEqual(config.template_dir, expected)

    def test_get_site_option(self):
        _fh, fpath = tempfile.mkstemp()
        with open(fpath, 'w') as fh:
            fh.write('[site_section]\n')
            fh.write('foo=bar\n')

        config = ConfigProvider()
        config._site_config_file = fpath
        # test for valid section and option
        value = config.get_config_option('site_section', 'foo')
        self.assertEqual(value, 'bar')
        # test for missing option
        value = config.get_config_option('site_section', 'MISSING', 'null')
        self.assertEqual(value, 'null')
        # test for missing section
        value = config.get_config_option('MISSING', 'foo', 'null')
        self.assertEqual(value, 'null')

        try:
            os.remove(fpath)
        except OSError:
            pass

    def test_get_user_option(self):
        _fh, fpath = tempfile.mkstemp()
        with open(fpath, 'w') as fh:
            fh.write('[user_section]\n')
            fh.write('foe=fum\n')

        config = ConfigProvider()
        config._user_config_file = fpath
        # test for valid section and option
        value = config.get_config_option('user_section', 'foe')
        self.assertEqual(value, 'fum')
        # test for missing option
        value = config.get_config_option('user_section', 'MISSING', 'null')
        self.assertEqual(value, 'null')
        # test for missing section
        value = config.get_config_option('MISSING', 'foe', 'null')
        self.assertEqual(value, 'null')

        try:
            os.remove(fpath)
        except OSError:
            pass
