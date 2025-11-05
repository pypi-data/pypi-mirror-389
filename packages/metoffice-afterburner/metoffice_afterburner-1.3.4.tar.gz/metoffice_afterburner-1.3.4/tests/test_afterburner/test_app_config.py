# (C) British Crown Copyright 2016-2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Unit tests for the afterburner.app_config module.
"""
from __future__ import (absolute_import, division)
from six.moves import (filter, input, map, range, zip)
from six import StringIO

import sys
import unittest

try:
    # python3
    from unittest import mock
except ImportError:
    # python2
    import mock

try:
    if sys.version_info.major == 3:
        # Python 3 compatible implementation of the rose.config module.
        from afterburner.contrib.rose_config import ConfigNode, ConfigLoader
    else:
        from rose.config import ConfigNode, ConfigLoader
    from afterburner.app_config import AppConfig
    got_rose_config = True
except ImportError:
    got_rose_config = False


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestInit(unittest.TestCase):
    """ Test AppConfig.__init__(). """
    def test_empty(self):
        cfg = AppConfig()
        self.assertEqual(cfg.value, {})
        self.assertEqual(cfg.state, ConfigNode.STATE_NORMAL)
        self.assertEqual(cfg.comments, [])

    def test_with_value(self):
        cfg = AppConfig({'food': ConfigNode('yummy')},
            ConfigNode.STATE_USER_IGNORED, 'one line file')
        self.assertEqual(cfg.value, {'food': ConfigNode('yummy')})
        self.assertEqual(cfg.state, ConfigNode.STATE_USER_IGNORED)
        self.assertEqual(cfg.comments, 'one line file')

    def test_invalid_state(self):
        expected_msg = "State 'a' is not an allowed value."
        with self.assertRaises(ValueError) as cm:
            AppConfig(state='a')
        self.assertEqual(str(cm.exception), expected_msg)


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestRoseConfigNodeMethodsWork(unittest.TestCase):
    """
    Test that rose.ConfigNodes are wrapped by AppConfig and their data can be
    accessed through AppConfig's methods.
    """
    def setUp(self):
        self.cfg = AppConfig({'food': ConfigNode('yummy')})

    def test_get(self):
        self.assertEqual(self.cfg.get(['food']), ConfigNode('yummy'))

    def test_get_value(self):
        self.assertEqual(self.cfg.get_value(['', 'food']), 'yummy')


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestFromFile(unittest.TestCase):
    """ Test AppConfig.from_file(). """
    @mock.patch('afterburner.app_config.rose_config.load')
    def test_loaded(self, mock_rose_load):
        mock_rose_load.return_value = ConfigNode('pate',
            ConfigNode.STATE_NORMAL, 'toast')
        desired = AppConfig('pate', ConfigNode.STATE_NORMAL, 'toast')

        cfg = AppConfig.from_file('food_file.ini')

        mock_rose_load.assert_called_with('food_file.ini')
        self.assertEqual(cfg.value, desired.value)
        self.assertEqual(cfg.state, desired.state)
        self.assertEqual(cfg.comments, desired.comments)


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestGetProperty(unittest.TestCase):
    """ Test AppConfig.get_property(). """
    def setUp(self):
        self.cfg = _simulated_load()

    def test_get_property(self):
        str_value = self.cfg.get_property('', 'jon_likes')
        self.assertEqual(str_value, 'food')

    def test_get_missing_property(self):
        empty_value = self.cfg.get_property('', 'jon_dislikes')
        self.assertEqual(empty_value, None)

    def test_get_default_property(self):
        default_value = self.cfg.get_property('', 'jon_dislikes', 'liver')
        self.assertEqual(default_value, 'liver')


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestGetIntProperty(unittest.TestCase):
    """ Test AppConfig.get_int_property(). """
    def setUp(self):
        self.cfg = _simulated_load()

    def test_get_int_property(self):
        int_value = self.cfg.get_int_property('dinner', 'num_courses')
        self.assertEqual(int_value, 4)

    def test_get_missing_int_property(self):
        empty_value = self.cfg.get_int_property('', 'jon_dislikes')
        self.assertEqual(empty_value, None)

    def test_get_default_int_property(self):
        default_value = self.cfg.get_int_property('', 'jon_dislikes', 101)
        self.assertEqual(default_value, 101)

    def test_get_empty_int_property(self):
        expected_msg = ("Could not convert section '' and property name "
            "'empty_str' to an integer: ''")
        with self.assertRaises(ValueError) as cm:
            self.cfg.get_int_property('', 'empty_str')
        self.assertEqual(str(cm.exception), expected_msg)

    def test_raises_value_error(self):
        expected_msg = ("Could not convert section 'dinner' and property name "
            "'dessert' to an integer: 'custard'")
        with self.assertRaises(ValueError) as cm:
            self.cfg.get_int_property('dinner', 'dessert')
        self.assertEqual(str(cm.exception), expected_msg)


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestGetFloatProperty(unittest.TestCase):
    """ Test AppConfig.get_float_property(). """
    def setUp(self):
        self.cfg = _simulated_load()

    def test_get_float_property(self):
        float_value = self.cfg.get_float_property('dinner', 'main_course_mass')
        self.assertAlmostEqual(float_value, 0.212)

    def test_get_missing_float_property(self):
        empty_value = self.cfg.get_float_property('', 'jon_dislikes')
        self.assertEqual(empty_value, None)

    def test_get_default_float_property(self):
        default_value = self.cfg.get_float_property('', 'jon_dislikes', 10.1)
        self.assertAlmostEqual(default_value, 10.1)

    def test_get_empty_float_property(self):
        expected_msg = ("Could not convert section '' and property name "
            "'empty_str' to a float: ''")
        with self.assertRaises(ValueError) as cm:
            self.cfg.get_float_property('', 'empty_str')
        self.assertEqual(str(cm.exception), expected_msg)

    def test_raises_value_error(self):
        expected_msg = ("Could not convert section 'dinner' and property name "
            "'dessert' to a float: 'custard'")
        with self.assertRaises(ValueError) as cm:
            self.cfg.get_float_property('dinner', 'dessert')
        self.assertEqual(str(cm.exception), expected_msg)


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestGetBoolProperty(unittest.TestCase):
    """ Test AppConfig.get_bool_property(). """
    def setUp(self):
        self.cfg = _simulated_load()

    def test_get_bool_property(self):
        bool_value = self.cfg.get_bool_property('dinner',
            'feel_too_full_afterwards')
        self.assertTrue(bool_value)

    def test_get_bool_property_case_insensitive(self):
        bool_value = self.cfg.get_bool_property('dinner',
            'first_meal_of_day')
        self.assertFalse(bool_value)

    def test_get_bool_with_non_bool(self):
        expected_msg = ("Could not convert section '' and property name "
            "'jon_likes' to a boolean: 'food'")
        with self.assertRaises(ValueError) as cm:
            self.cfg.get_bool_property('', 'jon_likes')
        self.assertEqual(str(cm.exception), expected_msg)

    def test_get_missing_bool_property(self):
        empty_value = self.cfg.get_bool_property('', 'jon_dislikes')
        self.assertFalse(empty_value)

    def test_get_default_bool_property(self):
        default_value = self.cfg.get_bool_property('', 'jon_dislikes', True)
        self.assertTrue(default_value)


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestGetNLProperty(unittest.TestCase):
    """ Test AppConfig.get_nl_property(). """
    def setUp(self):
        self.cfg = _simulated_load()

    def test_get_nl_property(self):
        str_value = self.cfg.get_nl_property('fruits', '0', 'colour')
        self.assertEqual(str_value, 'yellow')

    def test_get_nl_missing_index(self):
        empty_value = self.cfg.get_nl_property('fruits', '101', 'colour')
        self.assertEqual(empty_value, None)

    def test_get_nl_missing_property(self):
        empty_value = self.cfg.get_nl_property('fruits', '0', 'jon_dislikes')
        self.assertEqual(empty_value, None)

    def test_get_default_nl_property(self):
        default_value = self.cfg.get_nl_property('fruits', '0',
            'jon_dislikes', 'wasting food')
        self.assertEqual(default_value, 'wasting food')

    def test_get_default_from_missing_namelist(self):
        self.assertIsNone(self.cfg.get_nl_property('diet', '0',
            'colour'))


@unittest.skipUnless(got_rose_config, "rose config module not found")
class TestIterator(unittest.TestCase):
    """ Test AppConfig.iter_nl(). """
    def setUp(self):
        self.cfg = _simulated_load()

    def test_iterator(self):
        app_config_iterator = iter(self.cfg.iter_nl('fruits'))

        op_dict = next(app_config_iterator)
        self.assertEqual(op_dict, {'_index': '0', 'colour': 'yellow',
            'diameter': '2.4', 'name': 'banana', 'shape': 'long'})

        op_dict = next(app_config_iterator)
        self.assertEqual(op_dict, {'_index': '1', 'colour': 'green',
            'diameter': '6.7', 'name': 'apple', 'shape': 'round'})

        op_dict = next(app_config_iterator)
        self.assertEqual(op_dict, {'_index': '2', 'colour': 'green',
            'diameter': None, 'name': 'kiwi', 'shape': 'oval'})

        op_dict = next(app_config_iterator)
        self.assertEqual(op_dict, {'_index': 'letters', 'colour': 'orange',
            'diameter': '3.0', 'name': 'kumquat', 'shape': 'oval'})

        self.assertRaises(StopIteration, next, app_config_iterator)

    def test_skips_ignored(self):
        self.cfg.set(['namelist:fruits(1)'], value=self.cfg.get_value(
            ['namelist:fruits(1)']), state=ConfigNode.STATE_USER_IGNORED)

        expected_keys = ['0', '2', 'letters']
        self.assertEqual([d['_index'] for d in self.cfg.iter_nl('fruits')],
            expected_keys)

    def test_callback(self):
        for op_dict in self.cfg.iter_nl('fruits',
                callback=lambda dd: dd['shape'] == 'oval'):
            self.assertEqual(op_dict['shape'], 'oval')

    def test_nonexistant_namelist(self):
        app_config_iterator = iter(self.cfg.iter_nl('vegetables'))

        self.assertRaises(StopIteration, next, app_config_iterator)


def _simulated_load():
    """
    Load an example Rose configuration file from the contained string and return
    the configuration as an AppConfig object.

    :returns: An AppConfig object containing example configuration data.
    :rtype: afterburner.app_config.AppConfig
    """
    source = StringIO('''
jon_likes=food
empty_str=

[dinner]
dessert=custard
feel_too_full_afterwards=True
first_meal_of_day=false
main_course=fish
main_course_mass=0.212
num_courses=4

[file:fruits.nl]
source=namelist:fruits(:)

[namelist:fruits(0)]
colour=yellow
diameter=2.4
name=banana
shape=long

[namelist:fruits(1)]
colour=green
diameter=6.7
name=apple
shape=round

[namelist:fruits(2)]
colour=green
!diameter=4.1
name=kiwi
shape=oval

[namelist:fruits(letters)]
colour=orange
diameter=3.0
name=kumquat
shape=oval
''')
    rose_cfg = ConfigNode()
    loader = ConfigLoader()
    loader.load(source, rose_cfg)
    source.close()
    app_cfg = AppConfig(rose_cfg.value, rose_cfg.state, rose_cfg.comments)
    return app_cfg


if __name__ == '__main__':
    unittest.main()
