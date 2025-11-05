# (C) British Crown Copyright 2016, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.utils.textutils module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import unittest
from afterburner.utils import textutils
from afterburner.modelmeta import RIPF_REGEX


class TestIntListFromString(unittest.TestCase):
    """Test the int_list_from_string function."""

    def test_simple_case(self):
        expect = [1, 2, 3, 4]
        actual = textutils.int_list_from_string("1,2,3,4")
        self.assertEqual(actual, expect)
        actual = textutils.int_list_from_string("1, 2, 3, 4")
        self.assertEqual(actual, expect)

    def test_simple_case_desc(self):
        expect = [4, 3, 2, 1]
        actual = textutils.int_list_from_string("4,3,2,1")
        self.assertEqual(actual, expect)
        actual = textutils.int_list_from_string("4, 3, 2, 1")
        self.assertEqual(actual, expect)

    def test_simple_case_with_space_sep(self):
        expect = [1, 2, 3, 4]
        actual = textutils.int_list_from_string("1 2 3 4", sep=' ')
        self.assertEqual(actual, expect)
        actual = textutils.int_list_from_string("1  2  3  4", sep=' ')
        self.assertEqual(actual, expect)
        actual = textutils.int_list_from_string("1 2 3 4", sep=None)
        self.assertEqual(actual, expect)
        actual = textutils.int_list_from_string("1  2  3  4", sep=None)
        self.assertEqual(actual, expect)

    def test_simple_case_with_ranges(self):
        expect = [0, 2, 4, 5, 8, 9, 10, 99]
        actual = textutils.int_list_from_string("0,2,4-5,8-10,99")
        self.assertEqual(actual, expect)
        actual = textutils.int_list_from_string("0 2 4-5 8-10 99", sep=' ')
        self.assertEqual(actual, expect)

    def test_single_integer(self):
        actual = textutils.int_list_from_string("1")
        expect = [1]
        self.assertEqual(actual, expect)

    def test_single_negative_integer(self):
        actual = textutils.int_list_from_string("-1")
        expect = [-1]
        self.assertEqual(actual, expect)

    def test_with_extra_whitespace(self):
        actual = textutils.int_list_from_string("0, 2,4-5, 8-10,99")
        expect = [0, 2, 4, 5, 8, 9, 10, 99]
        self.assertEqual(actual, expect)

    def test_with_duplicate_values(self):
        actual = textutils.int_list_from_string("0,2,4-5,8-10,9,2")
        expect = [0, 2, 4, 5, 8, 9, 10, 9, 2]
        self.assertEqual(actual, expect)

    def test_with_unique_option(self):
        actual = textutils.int_list_from_string("0,2,4-5,8-10,9,2", unique=True)
        expect = [0, 2, 4, 5, 8, 9, 10]
        self.assertEqual(actual, expect)

    def test_with_unique_option_desc(self):
        actual = textutils.int_list_from_string("5,4,3,4,2,1,2,0", unique=True)
        expect = [0, 1, 2, 3, 4, 5]
        self.assertEqual(actual, expect)

    def test_negative_numbers(self):
        actual = textutils.int_list_from_string("-3,-2,-1")
        expect = [-3, -2, -1]
        self.assertEqual(actual, expect)

    def test_empty_string(self):
        self.assertRaises(ValueError, textutils.int_list_from_string, "")
        self.assertRaises(ValueError, textutils.int_list_from_string, "  ")

    def test_negative_number_range(self):
        self.assertRaises(ValueError, textutils.int_list_from_string, "-3-1,2")

    def test_with_hyphen_sep(self):
        self.assertRaises(ValueError, textutils.int_list_from_string, "1-4", sep='-')


class TestRipfMatcher(unittest.TestCase):
    """Test the textutils.ripf_matcher function."""

    def test_rip_patterns(self):
        self.assertTrue(textutils.ripf_matcher('r1i2p3', rnum='1'))
        self.assertTrue(textutils.ripf_matcher('r1i2p3', rnum='1', inum='2', pnum='3'))
        self.assertTrue(textutils.ripf_matcher('r02i01p01', rnum=2, pnum=1))
        self.assertTrue(textutils.ripf_matcher('R002I1P001', rnum=2, inum=1, pnum=1))
        self.assertTrue(textutils.ripf_matcher('R1I2P3', rnum=1, inum=2))

    def test_ripf_patterns(self):
        self.assertTrue(textutils.ripf_matcher('r1i2p3f0', rnum=1, fnum=0))
        self.assertTrue(textutils.ripf_matcher('r1i2p3f4', rnum=1, inum=2, pnum=3, fnum=4))
        self.assertTrue(textutils.ripf_matcher('r02i01p01f0', rnum=2, pnum=1))
        self.assertTrue(textutils.ripf_matcher('R002I1P001F04', rnum=2, fnum=4))
        self.assertTrue(textutils.ripf_matcher('R1I2P3F4', rnum=1, inum=2, pnum=3, fnum=4))

    def test_invalid_patterns(self):
        self.assertFalse(textutils.ripf_matcher('r1p3'))
        self.assertFalse(textutils.ripf_matcher('r1i2p3'))
        self.assertFalse(textutils.ripf_matcher('r1i2f3', rnum=1))
        self.assertFalse(textutils.ripf_matcher('r1i2f3', rnum=3))
        self.assertFalse(textutils.ripf_matcher('r1i2f3', rnum=1, inum=1))
        self.assertFalse(textutils.ripf_matcher('r1i2p3', rnum=1, fnum=1))
        self.assertFalse(textutils.ripf_matcher('r1i2p3f4xxx', rnum=1, fnum=4))


if __name__ == '__main__':
    unittest.main()
