# (C) British Crown Copyright 2016-2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.utils.__init__ module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import text_type

import os
import unittest
from afterburner import utils


class TestGetCylcVariables(unittest.TestCase):
    """Test the get_cylc_variables function."""

    def tearDown(self):
        keys = list(os.environ)
        for name in keys:
            if name.startswith('CYLC_'):
                os.environ.pop(name)

    def test_with_no_cylc_env(self):
        cylc_vars = utils.get_cylc_variables()
        self.assertFalse(cylc_vars.is_active)
        self.assertTrue(cylc_vars.suite_name is None)

    def test_with_cylc_env(self):
        os.environ['CYLC_SUITE_NAME'] = 'mi-ab123'
        os.environ['CYLC_TASK_NAME'] = 'mytask'
        cylc_vars = utils.get_cylc_variables()
        self.assertTrue(cylc_vars.is_active)
        self.assertEqual(cylc_vars.suite_name, 'mi-ab123')
        self.assertEqual(cylc_vars.task_name, 'mytask')
        self.assertTrue(cylc_vars.SUITE_NAME is None)
        self.assertTrue(cylc_vars.TASK_NAME is None)


class TestIsNumeric(unittest.TestCase):
    """Test the is_numeric function."""

    def test_valid_values(self):
        self.assertTrue(utils.is_numeric(0))
        self.assertTrue(utils.is_numeric(3.14))
        self.assertTrue(utils.is_numeric(0.314e1))
        self.assertTrue(utils.is_numeric(complex(1, 2)))
        self.assertTrue(utils.is_numeric((1+2j)))

    def test_invalid_values(self):
        self.assertFalse(utils.is_numeric(None))
        self.assertFalse(utils.is_numeric(True))
        self.assertFalse(utils.is_numeric(False))
        self.assertFalse(utils.is_numeric(''))
        self.assertFalse(utils.is_numeric('foo'))
        self.assertFalse(utils.is_numeric([1]))
        self.assertFalse(utils.is_numeric((1, 2)))
        self.assertFalse(utils.is_numeric({1, 2}))
        self.assertFalse(utils.is_numeric({'f': 'foo'}))
        self.assertFalse(utils.is_numeric(bytearray(range(3))))


class TestIsString(unittest.TestCase):
    """Test the is_string function."""

    def test_valid_values(self):
        self.assertTrue(utils.is_string(''))
        self.assertTrue(utils.is_string('foo'))
        self.assertTrue(utils.is_string(('foo')))   # str expression, not tuple!

    def test_invalid_values(self):
        self.assertFalse(utils.is_string(None))
        self.assertFalse(utils.is_string(True))
        self.assertFalse(utils.is_string(False))
        self.assertFalse(utils.is_string(0))
        self.assertFalse(utils.is_string(3.14))
        self.assertFalse(utils.is_string((1+2j)))
        self.assertFalse(utils.is_string(['foo']))
        self.assertFalse(utils.is_string(('foo', 'bar')))
        self.assertFalse(utils.is_string({1, 2}))
        self.assertFalse(utils.is_string({'f': 'foo'}))
        self.assertFalse(utils.is_string(bytearray(range(3))))


class TestIsIterable(unittest.TestCase):
    """Test the is_iterable function."""

    def test_valid_values(self):
        self.assertTrue(utils.is_iterable(''))
        self.assertTrue(utils.is_iterable('foo'))
        self.assertTrue(utils.is_iterable(('foo')))   # str expression, not tuple!
        self.assertTrue(utils.is_iterable([]))
        self.assertTrue(utils.is_iterable([1, 2]))
        self.assertTrue(utils.is_iterable((1, 2)))
        self.assertTrue(utils.is_iterable({1, 2}))
        self.assertTrue(utils.is_iterable({'f': 'foo'}))
        self.assertTrue(utils.is_iterable(bytearray(range(3))))

    def test_invalid_values(self):
        self.assertFalse(utils.is_iterable(None))
        self.assertFalse(utils.is_iterable(True))
        self.assertFalse(utils.is_iterable(0))
        self.assertFalse(utils.is_iterable(3.14))
        self.assertFalse(utils.is_iterable((1+2j)))


class TestIsSequence(unittest.TestCase):
    """Test the is_sequence function."""

    def test_valid_values(self):
        self.assertTrue(utils.is_sequence(''))
        self.assertTrue(utils.is_sequence('foo'))
        self.assertTrue(utils.is_sequence(('foo')))   # str expression, not tuple!
        self.assertTrue(utils.is_sequence([]))
        self.assertTrue(utils.is_sequence([1, 2]))
        self.assertTrue(utils.is_sequence((1, 2)))
        self.assertTrue(utils.is_sequence(bytearray(range(3))))

    def test_invalid_values(self):
        self.assertFalse(utils.is_sequence(None))
        self.assertFalse(utils.is_sequence(True))
        self.assertFalse(utils.is_sequence(0))
        self.assertFalse(utils.is_sequence(3.14))
        self.assertFalse(utils.is_sequence((1+2j)))
        self.assertFalse(utils.is_sequence({1, 2}))
        self.assertFalse(utils.is_sequence({'f': 'foo'}))


class TestIsNonStringIterable(unittest.TestCase):
    """Test the is_non_string_iterable function."""

    def test_valid_values(self):
        self.assertTrue(utils.is_non_string_iterable([]))
        self.assertTrue(utils.is_non_string_iterable([1, 2]))
        self.assertTrue(utils.is_non_string_iterable((1, 2)))
        self.assertTrue(utils.is_non_string_iterable({1, 2}))
        self.assertTrue(utils.is_non_string_iterable({'f': 'foo'}))
        self.assertTrue(utils.is_non_string_iterable(bytearray(range(3))))

    def test_invalid_values(self):
        self.assertFalse(utils.is_non_string_iterable(''))
        self.assertFalse(utils.is_non_string_iterable('foo'))
        self.assertFalse(utils.is_non_string_iterable(('foo')))   # str expression, not tuple!
        self.assertFalse(utils.is_non_string_iterable(None))
        self.assertFalse(utils.is_non_string_iterable(True))
        self.assertFalse(utils.is_non_string_iterable(0))
        self.assertFalse(utils.is_non_string_iterable(3.14))
        self.assertFalse(utils.is_non_string_iterable((1+2j)))


class TestIsNonStringSequence(unittest.TestCase):
    """Test the is_non_string_sequence function."""

    def test_valid_values(self):
        self.assertTrue(utils.is_non_string_sequence([]))
        self.assertTrue(utils.is_non_string_sequence([1, 2]))
        self.assertTrue(utils.is_non_string_sequence((1, 2)))
        self.assertTrue(utils.is_non_string_sequence(bytearray(range(3))))

    def test_invalid_values(self):
        self.assertFalse(utils.is_non_string_sequence(''))
        self.assertFalse(utils.is_non_string_sequence('foo'))
        self.assertFalse(utils.is_non_string_sequence(('foo')))   # str expression, not tuple!
        self.assertFalse(utils.is_non_string_sequence(None))
        self.assertFalse(utils.is_non_string_sequence(True))
        self.assertFalse(utils.is_non_string_sequence(0))
        self.assertFalse(utils.is_non_string_sequence(3.14))
        self.assertFalse(utils.is_non_string_sequence((1+2j)))
        self.assertFalse(utils.is_non_string_sequence({1, 2}))
        self.assertFalse(utils.is_non_string_sequence({'f': 'foo'}))


class TestIsTrue(unittest.TestCase):
    """Test the is_true function."""

    def test_with_booleans(self):
        self.assertTrue(utils.is_true(True))
        self.assertFalse(utils.is_true(False))

    def test_with_ints(self):
        self.assertEqual(utils.is_true(-1), None)
        self.assertEqual(utils.is_true(0), False)
        self.assertTrue(utils.is_true(1))
        self.assertEqual(utils.is_true(2), None)

    def test_with_floats(self):
        self.assertEqual(utils.is_true(-1.0), None)
        self.assertEqual(utils.is_true(0.0), None)
        self.assertEqual(utils.is_true(1.0), None)
        self.assertEqual(utils.is_true(2.0), None)

    def test_with_strings(self):
        for value in ['t', 'true', '.true.', 'on', 'y', 'yes', '1']:
            self.assertTrue(utils.is_true(value))
            self.assertTrue(utils.is_true(value.upper()))
            self.assertTrue(utils.is_true(text_type(value)))

        for value in ['f', 'false', '.false.', 'off', 'n', 'no', '0']:
            self.assertEqual(utils.is_true(value), False)
            self.assertEqual(utils.is_true(value.upper()), False)
            self.assertEqual(utils.is_true(text_type(value)), False)

        self.assertEqual(utils.is_true(''), None)
        self.assertEqual(utils.is_true('0.0'), None)
        self.assertEqual(utils.is_true('1.0'), None)
        self.assertEqual(utils.is_true('untrue'), None)

    def test_other_types(self):
        self.assertEqual(utils.is_true(None), None)
        self.assertEqual(utils.is_true([1]), None)
        self.assertEqual(utils.is_true((1,2,3)), None)
        self.assertEqual(utils.is_true(dict(a=1)), None)


class TestNamespacePlus(unittest.TestCase):
    """Test the NamespacePlus class."""

    def test_getattr_method(self):
        ns = utils.NamespacePlus(foo=1, bar=2, baz=3)
        self.assertEqual(ns.foo, 1)
        self.assertEqual(ns.bar, 2)
        self.assertEqual(ns.baz, 3)
        self.assertEqual(ns.cov, None)
        ns.cov = 'fefe'
        self.assertEqual(ns.cov, 'fefe')
        del ns.cov
        self.assertEqual(ns.cov, None)

    def test_iter_method(self):
        ns = utils.NamespacePlus(foo=1, bar=2, baz=3)
        it = iter(ns)
        expected = (('foo', 1), ('bar', 2), ('baz', 3))
        self.assertTrue(next(it) in expected)
        self.assertTrue(next(it) in expected)
        self.assertTrue(next(it) in expected)
        self.assertRaises(StopIteration, next, it)

    def test_iter_names_method(self):
        ns = utils.NamespacePlus(foo=1, bar=2, baz=3)
        for name in ns.iter_names():
            self.assertTrue(name in ['foo', 'bar', 'baz'])
        self.assertEqual(sorted(ns.iter_names()), ['bar', 'baz', 'foo'])

    def test_has_name_method(self):
        ns = utils.NamespacePlus(foo=1, bar=2, baz=3)
        for name in ns.iter_names():
            self.assertTrue(ns.has_name(name))
            self.assertTrue(hasattr(ns, name))
        self.assertFalse(ns.has_name('xxx'))
        self.assertTrue(hasattr(ns, 'xxx'))

    def test_equality(self):
        ns1 = utils.NamespacePlus(foo=1, bar=2, baz=3)
        ns2 = utils.NamespacePlus(foo=1, bar=2, baz=3)
        self.assertEqual(ns1, ns2)
        ns2 = utils.NamespacePlus(baz=3, bar=2, foo=1)
        self.assertEqual(ns1, ns2)
        ns1.cov = 4
        self.assertNotEqual(ns1, ns2)


if __name__ == '__main__':
    unittest.main()
