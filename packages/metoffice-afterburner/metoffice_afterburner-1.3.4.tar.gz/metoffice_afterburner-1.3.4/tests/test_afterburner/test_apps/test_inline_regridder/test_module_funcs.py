# (C) British Crown Copyright 2021, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Test selected top-level functions in the afterburner.apps.inline_regridder module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import unittest

from afterburner.apps import inline_regridder
from afterburner.misc import stockcubes


class TestGetDatetimeExtentFunc(unittest.TestCase):
    """Test the afterburner.apps.inline_regridder._get_datetime_extent function."""

    def test_with_default_fmt(self):

        # create a test cube with shape (t=12, y=7, x=6)
        test_cube = stockcubes.geo_tyx()

        # obtain start and end dates from the test cube
        start_date, end_date = inline_regridder._get_datetime_extent(test_cube)

        self.assertEqual(start_date, '19700101')
        self.assertEqual(end_date, '19710101')

    def test_with_default_fmt_no_bounds(self):

        # create a test cube with shape (t=12, y=7, x=6)
        test_cube = stockcubes.geo_tyx()

        # nullify the time bounds
        tcoord = test_cube.coord('time')
        tcoord.bounds = None

        # obtain start and end dates from the test cube
        start_date, end_date = inline_regridder._get_datetime_extent(test_cube)

        self.assertEqual(start_date, '19700116')
        self.assertEqual(end_date, '19701216')

    def test_with_custom_fmt(self):

        # create a test cube with shape (t=12, y=7, x=6)
        test_cube = stockcubes.geo_tyx()

        # obtain start and end dates from the test cube
        start_date, end_date = inline_regridder._get_datetime_extent(test_cube,
            dtformat='%Y-%m-%dT%H:%M')

        self.assertEqual(start_date, '1970-01-01T00:00')
        self.assertEqual(end_date, '1971-01-01T00:00')

    def test_with_custom_coord_name(self):

        # create a test cube with shape (t=12, y=7, x=6)
        test_cube = stockcubes.geo_tyx()

        # unset the time coordinate's standard_name attribute, then set the
        # long_name attribute
        tcoord = test_cube.coord('time')
        tcoord.standard_name = None
        tcoord.long_name = 'time_counter'

        # check that at least 1 time axis is identifiable
        tcoords = test_cube.coords(axis='T')
        self.assertTrue(len(tcoords) > 0)

        # obtain start and end dates from the test cube
        start_date, end_date = inline_regridder._get_datetime_extent(test_cube)

        self.assertEqual(start_date, '19700101')
        self.assertEqual(end_date, '19710101')


class TestRemoveRimFunc(unittest.TestCase):
    """Test the afterburner.apps.inline_regridder._remove_rim function."""

    def test_remove_rim(self):

        # create a 10 x 10 degree test cube
        test_cube = stockcubes.geo_yx(shape=(19, 36))

        # remove a width-3 rim from the test cube
        trimmed_cube = inline_regridder._remove_rim(test_cube, 3)

        self.assertEqual(trimmed_cube.shape, (13, 30))

    def test_remove_zero_width_rim(self):

        # create a 10 x 10 degree test cube
        test_cube = stockcubes.geo_yx(shape=(19, 36))

        # remove a zero-width rim from the test cube - this just results in the
        # original cube being returned
        trimmed_cube = inline_regridder._remove_rim(test_cube, 0)

        self.assertEqual(trimmed_cube.shape, (19, 36))
        self.assertIs(trimmed_cube, test_cube)


if __name__ == '__main__':
    unittest.main()
