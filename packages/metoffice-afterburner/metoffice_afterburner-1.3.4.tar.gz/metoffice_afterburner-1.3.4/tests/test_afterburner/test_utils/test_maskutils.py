# (C) British Crown Copyright 2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.utils.maskutils module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import unittest
import operator

import numpy as np
import numpy.ma as ma
import numpy.testing as npt
import iris

from afterburner.utils import maskutils


class TestApplyMaskToArray(unittest.TestCase):
    """Test the apply_mask_to_array function."""

    def test_using_1d_mask(self):
        a = np.arange(6)
        m = ma.masked_equal(np.array([0, 1] * 3), 0)
        am = maskutils.apply_mask_to_array(a, m)
        npt.assert_equal(am.mask, m.mask)
        npt.assert_equal(ma.count_masked(am), 3)
        npt.assert_equal(am[~am.mask], [1, 3, 5])

    def test_using_2d_mask(self):
        # using a 2d data array
        a = np.array([0, 1, 2, 3] * 3).reshape(3, 4)
        m = ma.masked_equal(np.array([0, 1] * 6).reshape(3, 4), 0)
        am = maskutils.apply_mask_to_array(a, m)
        npt.assert_equal(am.mask, m.mask)
        npt.assert_equal(ma.count_masked(am), 6)
        npt.assert_equal(am[:,1], [1]*3)
        npt.assert_equal(am[:,3], [3]*3)

        # using a 3d data array
        a = np.array([0, 1, 2, 3] * 6).reshape(2, 3, 4)
        am = maskutils.apply_mask_to_array(a, m)
        npt.assert_equal(am.mask[0], m.mask)
        npt.assert_equal(ma.count_masked(am), 12)
        npt.assert_equal(am[0,:,1], [1]*3)
        npt.assert_equal(am[0,:,3], [3]*3)

    def test_using_inverted_1d_mask(self):
        a = np.arange(6)
        m = ma.masked_equal(np.array([0, 1] * 3), 0)
        am = maskutils.apply_mask_to_array(a, m, invert_mask=True)
        npt.assert_equal(am.mask, ~m.mask)
        npt.assert_equal(ma.count_masked(am), 3)
        npt.assert_equal(am[~am.mask], [0, 2, 4])

    def test_using_inverted_2d_mask(self):
        # using a 2d data array
        a = np.array([0, 1, 2, 3] * 3).reshape(3, 4)
        m = ma.masked_equal(np.array([0, 1] * 6).reshape(3, 4), 0)
        am = maskutils.apply_mask_to_array(a, m, invert_mask=True)
        npt.assert_equal(am.mask, ~m.mask)
        npt.assert_equal(ma.count_masked(am), 6)
        npt.assert_equal(am[:,0], [0]*3)
        npt.assert_equal(am[:,2], [2]*3)

    def test_using_custom_fill_values(self):
        a = np.arange(6)
        m = ma.masked_equal(np.array([0, 1] * 3), 0)
        am = maskutils.apply_mask_to_array(a, m, fill_value=-9)
        npt.assert_equal(am.fill_value, -9)

        am = maskutils.apply_mask_to_array(a.astype('f'), m, fill_value=-9.0)
        npt.assert_equal(am.fill_value, -9.0)

    def test_where_mask_array_eq_x(self):
        a = np.arange(6)
        m = np.array([0, 1] * 3)
        am = maskutils.apply_mask_to_array(a, m, mask_only=False, compare_value=0)
        npt.assert_equal(ma.count_masked(am), 3)
        npt.assert_equal(am[~am.mask], [1, 3, 5])

        am = maskutils.apply_mask_to_array(a, m, mask_only=False, compare_value=1)
        npt.assert_equal(ma.count_masked(am), 3)
        npt.assert_equal(am[~am.mask], [0, 2, 4])

        m = ma.masked_equal(np.array([0, 1] * 3), 0)
        am = maskutils.apply_mask_to_array(a, m, mask_only=False, compare_value=0)
        npt.assert_equal(ma.count_masked(am), 3)

        am = maskutils.apply_mask_to_array(a, m, mask_only=False, compare_value=1)
        npt.assert_equal(ma.count_masked(am), 6)

    def test_where_mask_array_lt_x(self):
        a = np.arange(6)
        m = np.array([0, 0.5, 1.0, 0, 0.5, 1.0])
        am = maskutils.apply_mask_to_array(a, m, mask_only=False, compare_value=0.5,
            compare_op='lt')
        npt.assert_equal(ma.count_masked(am), 2)
        npt.assert_equal(am[~am.mask], [1, 2, 4, 5])

    def test_where_mask_array_ge_x(self):
        a = np.arange(6)
        m = np.array([0, 0.5, 1.0, 0, 0.5, 1.0])
        am = maskutils.apply_mask_to_array(a, m, mask_only=False, compare_value=0.5,
            compare_op='ge')
        npt.assert_equal(ma.count_masked(am), 4)
        npt.assert_equal(am[~am.mask], [0, 3])

    def test_add_where_mask_array_is_land(self):
        a = np.arange(6)
        m = np.array([0, 0.5, 1.0, 0, 0.5, 1.0])
        am = maskutils.apply_mask_to_array(a, m, mask_only=False, compare_value=0.5,
            compare_op='lt', np_func=np.add)
        npt.assert_equal(ma.count_masked(am), 2)
        npt.assert_allclose(am[~am.mask], [1.5, 3.0, 4.5, 6.0])

    def test_mult_where_mask_array_is_sea(self):
        a = np.arange(6)
        m = np.array([0.2, 0.4, 1.0, 0.4, 0.5, 1.0])
        am = maskutils.apply_mask_to_array(a, m, mask_only=False, compare_value=0.5,
            compare_op=operator.ge, np_func=np.multiply)
        npt.assert_equal(ma.count_masked(am), 3)
        npt.assert_allclose(am[~am.mask], [0.0, 0.4, 1.2])


class TestApplyMaskedOpToArray(unittest.TestCase):
    """Test the apply_masked_op_to_array function."""

    def test_add_where_mask_array_is_land(self):
        a = np.arange(6)
        m = np.array([0, 0.5, 1.0, 0, 0.5, 1.0])
        am = maskutils.apply_masked_op_to_array(a, m, 0.5, 'lt', np.add)
        npt.assert_equal(ma.count_masked(am), 2)
        npt.assert_allclose(am[~am.mask], [1.5, 3.0, 4.5, 6.0])

    def test_mult_where_mask_array_is_sea(self):
        a = np.arange(6)
        m = np.array([0.2, 0.4, 1.0, 0.4, 0.5, 1.0])
        am = maskutils.apply_masked_op_to_array(a, m, 0.5, operator.ge, np.multiply)
        npt.assert_equal(ma.count_masked(am), 3)
        npt.assert_allclose(am[~am.mask], [0.0, 0.4, 1.2])

    def test_using_custom_fill_values(self):
        a = np.arange(6)
        m = np.array([0, 0.5, 1.0, 0, 0.5, 1.0])
        am = maskutils.apply_masked_op_to_array(a, m, 0.5, 'lt', np.add,
            fill_value=-9)
        npt.assert_equal(am.fill_value, -9)

        am = maskutils.apply_masked_op_to_array(a.astype('f'), m, 0.5, 'lt', np.add,
            fill_value=-9.0)
        npt.assert_equal(am.fill_value, -9.0)


class TestApplyMaskToCube(unittest.TestCase):
    """Test the apply_mask_to_cube function."""

    def test_using_mask_only(self):
        a = np.arange(6)
        c = iris.cube.Cube(a, long_name='humidity', units='1')
        m = ma.masked_equal(np.array([0, 1] * 3), 0)
        maskutils.apply_mask_to_cube(c, m)
        npt.assert_equal(c.data.mask, m.mask)
        npt.assert_equal(ma.count_masked(c.data), 3)
        npt.assert_equal(c.data[~c.data.mask], [1, 3, 5])

    def test_using_inverted_mask_only(self):
        a = np.arange(6)
        c = iris.cube.Cube(a, long_name='humidity', units='1')
        m = ma.masked_equal(np.array([0, 1] * 3), 0)
        maskutils.apply_mask_to_cube(c, m, invert_mask=True)
        npt.assert_equal(c.data.mask, ~m.mask)
        npt.assert_equal(ma.count_masked(c.data), 3)
        npt.assert_equal(c.data[~c.data.mask], [0, 2, 4])

    def test_using_custom_fill_values(self):
        a = np.arange(6)
        c = iris.cube.Cube(a, long_name='humidity', units='1')
        m = ma.masked_equal(np.array([0, 1] * 3), 0)
        maskutils.apply_mask_to_cube(c, m, fill_value=-9)
        npt.assert_equal(c.data.fill_value, -9)

        c.data = a.astype('f')
        maskutils.apply_mask_to_cube(c, m, fill_value=-9.0)
        npt.assert_equal(c.data.fill_value, -9.0)


class TestApplyMaskedOpToCube(unittest.TestCase):
    """Test the apply_masked_op_to_cube function."""

    def test_mult_where_mask_array_is_land(self):
        a = np.arange(6)
        c = iris.cube.Cube(a, long_name='humidity', units='1')
        m = np.array([0, 0.5, 1.0, 0, 0.5, 1.0])
        maskutils.apply_masked_op_to_cube(c, m, 0.5, 'lt', np.multiply)
        npt.assert_equal(ma.count_masked(c.data), 2)
        npt.assert_allclose(c.data[~c.data.mask], [0.5, 2.0, 2.0, 5.0])

    def test_using_custom_fill_values(self):
        a = np.arange(6)
        c = iris.cube.Cube(a, long_name='humidity', units='1')
        m = np.arange(0, 60, 10)
        maskutils.apply_masked_op_to_cube(c, m, 30, 'lt', np.multiply, fill_value=-9)
        npt.assert_equal(c.data.fill_value, -9)

        a = np.arange(6)
        c = iris.cube.Cube(a, long_name='humidity', units='1')
        m = np.array([0, 0.5, 1.0, 0, 0.5, 1.0])
        maskutils.apply_masked_op_to_cube(c, m, 0.5, 'lt', np.multiply, fill_value=-9.0)
        npt.assert_equal(c.data.fill_value, -9.0)


if __name__ == '__main__':
    unittest.main()
