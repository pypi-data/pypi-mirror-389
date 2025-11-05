# (C) British Crown Copyright 2018-2020, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.contrib.umfilelist module. Note that this module
is also exercised by the unit tests contained within the test_filename_providers
module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import assertCountEqual

import unittest
from afterburner.contrib import umfilelist


class TestMainFunction(unittest.TestCase):
    """Test the main() function."""

    def test_um_apa_files_oldmode(self):
        """Test the generation of UM 'classic' filenames for the apa stream."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apa')
        args.append('--startdate=197012010000')
        args.append('--enddate=197103010000')
        args.append('--standard_absolute_time')
        actual = umfilelist.main(args)
        expect = ['abcdea.pah0c20.pp', 'abcdea.pah0c30.pp', 'abcdea.pah0c40.pp']
        assertCountEqual(self, actual[:3], expect)

    def test_um_apa_files_newmode(self):
        """Test the generation of UM 'new-style' filenames for the apa stream."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apa')
        args.append('--startdate=197012010000')
        args.append('--enddate=197103010000')
        args.append('--standard_absolute_time')
        args.append('--newmode')
        actual = umfilelist.main(args)
        expect = ['abcdea.pa19701201.pp', 'abcdea.pa19701202.pp', 'abcdea.pa19701203.pp']
        assertCountEqual(self, actual[:3], expect)

        args.append('--reinit=30')
        actual = umfilelist.main(args)
        expect = ['abcdea.pa1970dec.pp', 'abcdea.pa1971jan.pp', 'abcdea.pa1971feb.pp']
        assertCountEqual(self, actual[:3], expect)

    def test_um_apm_files_oldmode(self):
        """Test the generation of UM 'classic' filenames for the apm stream."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apm')
        args.append('--startdate=197012010000')
        args.append('--enddate=197103010000')
        args.append('--standard_absolute_time')
        actual = umfilelist.main(args)
        expect = ['abcdea.pmh0dec.pp', 'abcdea.pmh1jan.pp', 'abcdea.pmh1feb.pp']
        assertCountEqual(self, actual, expect)

    def test_um_apm_files_newmode(self):
        """Test the generation of UM 'new-style' filenames for the apm stream."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apm')
        args.append('--startdate=197012010000')
        args.append('--enddate=197103010000')
        args.append('--standard_absolute_time')
        args.append('--newmode')
        actual = umfilelist.main(args)
        expect = ['abcdea.pm1970dec.pp', 'abcdea.pm1971jan.pp', 'abcdea.pm1971feb.pp']
        assertCountEqual(self, actual, expect)

    def test_um_aps_files_oldmode(self):
        """Test the generation of UM 'classic' filenames for the aps stream."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=aps')
        args.append('--startdate=197012010000')
        args.append('--enddate=197112010000')
        args.append('--standard_absolute_time')
        actual = umfilelist.main(args)
        expect = ['abcdea.psh1djf.pp', 'abcdea.psh1mam.pp', 'abcdea.psh1jja.pp', 'abcdea.psh1son.pp']
        assertCountEqual(self, actual, expect)

    def test_um_aps_files_newmode(self):
        """Test the generation of UM 'new-style' filenames for the aps stream."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=aps')
        args.append('--startdate=197012010000')
        args.append('--enddate=197112010000')
        args.append('--standard_absolute_time')
        args.append('--newmode')
        actual = umfilelist.main(args)
        expect = ['abcdea.ps1971djf.pp', 'abcdea.ps1971mam.pp', 'abcdea.ps1971jja.pp', 'abcdea.ps1971son.pp']
        assertCountEqual(self, actual, expect)

    def test_um_apy_files_oldmode(self):
        """Test the generation of UM 'classic' filenames for the apy stream."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apy')
        args.append('--startdate=197012010000')
        args.append('--enddate=197212010000')
        args.append('--standard_absolute_time')
        actual = umfilelist.main(args)
        expect = ['abcdea.pyh1c10.pp', 'abcdea.pyh2c10.pp']
        assertCountEqual(self, actual, expect)

    def test_um_apy_files_newmode(self):
        """Test the generation of UM 'new-style' filenames for the apy stream."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apy')
        args.append('--startdate=197012010000')
        args.append('--enddate=197212010000')
        args.append('--standard_absolute_time')
        args.append('--newmode')
        actual = umfilelist.main(args)
        expect = ['abcdea.py19711201.pp', 'abcdea.py19721201.pp']
        assertCountEqual(self, actual, expect)

    def test_um_apx_files_oldmode(self):
        """Test the generation of UM 'classic' filenames for the apx stream."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apx')
        args.append('--startdate=197912010000')
        args.append('--enddate=199912010000')
        args.append('--standard_absolute_time')
        actual = umfilelist.main(args)
        expect = ['abcdea.pxi9c10.pp', 'abcdea.pxj9c10.pp']
        assertCountEqual(self, actual, expect)

    def test_um_apx_files_newmode(self):
        """Test the generation of UM 'new-style' filenames for the apx stream."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apx')
        args.append('--startdate=197912010000')
        args.append('--enddate=199912010000')
        args.append('--standard_absolute_time')
        args.append('--newmode')
        actual = umfilelist.main(args)
        expect = ['abcdea.px19891201.pp', 'abcdea.px19991201.pp']
        assertCountEqual(self, actual, expect)

    def test_null_result(self):
        """Test for a null result, i.e. an empty sequence."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apy')
        args.append('--startdate=197012010000')
        args.append('--enddate=197012010000')
        args.append('--standard_absolute_time')
        args.append('--newmode')
        actual = umfilelist.main(args)
        expect = []
        assertCountEqual(self, actual, expect)

    def test_valid_dates_option(self):
        """Test the valid dates option."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apy')
        args.append('--startdate=197012010000')
        args.append('--enddate=197212010000')
        args.append('--standard_absolute_time')
        args.append('--newmode')
        args.append('--valid_dates')
        result = umfilelist.main(args)
        expect = ['abcdea.py19711201.pp', '197012010000', '197112010000']
        assertCountEqual(self, result[0], expect)
        expect = ['abcdea.py19721201.pp', '197112010000', '197212010000']
        assertCountEqual(self, result[1], expect)

    def test_zeropad_dates_option(self):
        """Test the zeropad_dates option."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apy')
        args.append('--startdate=085012010000')
        args.append('--enddate=085212010000')
        args.append('--standard_absolute_time')
        args.append('--newmode')
        args.append('--zeropad_dates')
        actual = umfilelist.main(args)
        expect = ['abcdea.py08511201.pp', 'abcdea.py08521201.pp']
        assertCountEqual(self, actual, expect)

    def test_no_zeropad_dates_option(self):
        """Test the no_zeropad_dates option."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apy')
        args.append('--startdate=085012010000')
        args.append('--enddate=085212010000')
        args.append('--standard_absolute_time')
        args.append('--newmode')
        args.append('--no_zeropad_dates')
        actual = umfilelist.main(args)
        expect = ['abcdea.py8511201.pp', 'abcdea.py8521201.pp']
        assertCountEqual(self, actual, expect)

    def test_forced_reinit_period(self):
        """Test for a forced reinit period."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apa')
        args.append('--startdate=197012010000')
        args.append('--enddate=197212010000')
        args.append('--standard_absolute_time')
        args.append('--newmode')
        args.append('--reinit=-30')  # force monthly-mean reinit period
        actual = umfilelist.main(args)
        self.assertEqual(len(actual), 24)

        args[2] = '--stream=apd'
        args[-1] = '--reinit=90'     # force seasonal-mean reinit period
        actual = umfilelist.main(args)
        self.assertEqual(len(actual), 8)

        args[2] = '--stream=ap1'
        args[-1] = '--reinit=-360'   # force annual-mean reinit period
        actual = umfilelist.main(args)
        self.assertEqual(len(actual), 2)

    def test_invalid_reinit_period(self):
        """Test for an invalid reinit period."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apm')
        args.append('--startdate=197012010000')
        args.append('--enddate=197212010000')
        args.append('--standard_absolute_time')
        args.append('--newmode')
        args.append('--reinit=99')   # invalid period for apm/aps/apm streams
        actual = umfilelist.main(args)
        self.assertEqual(len(actual), 24)

        args[2] = '--stream=aps'
        actual = umfilelist.main(args)
        self.assertEqual(len(actual), 8)

        args[2] = '--stream=apy'
        actual = umfilelist.main(args)
        self.assertEqual(len(actual), 2)

    def test_stream_out_option(self):
        """Test use of the --stream_out option."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apa')
        args.append('--stream_out=apl')
        args.append('--startdate=197012010000')
        args.append('--enddate=197112010000')
        args.append('--standard_absolute_time')
        args.append('--newmode')
        args.append('--reinit=30')
        actual = umfilelist.main(args)
        self.assertEqual(len(actual), 12)
        expect = ['abcdea.pl1970dec.pp', 'abcdea.pl1971jan.pp', 'abcdea.pl1971feb.pp']
        assertCountEqual(self, actual[:3], expect)

        # force 30-day reinit period
        args[-1] = '--reinit=-30'
        actual = umfilelist.main(args)
        self.assertEqual(len(actual), 12)
        assertCountEqual(self, actual[:3], expect)

        # incorrect number of filenames are returned when default reinit period is used
        args[-1] = '--reinit=0'
        actual = umfilelist.main(args)
        self.assertNotEqual(len(actual), 12)


class TestMainAsIteratorFunction(unittest.TestCase):
    """Test the main_as_iterator() function."""

    def test_um_apy_files_oldmode(self):
        """Test the generation of UM 'classic' filenames."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apy')
        args.append('--startdate=197012010000')
        args.append('--enddate=197212010000')
        args.append('--standard_absolute_time')
        it = umfilelist.main_as_iterator(args)
        self.assertEqual(next(it), 'abcdea.pyh1c10.pp')
        self.assertEqual(next(it), 'abcdea.pyh2c10.pp')
        self.assertRaises(StopIteration, next, it)

    def test_um_apy_files_newmode(self):
        """Test the generation of UM 'new-style' filenames."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apy')
        args.append('--startdate=197012010000')
        args.append('--enddate=197212010000')
        args.append('--standard_absolute_time')
        args.append('--newmode')
        it = umfilelist.main_as_iterator(args)
        self.assertEqual(next(it), 'abcdea.py19711201.pp')
        self.assertEqual(next(it), 'abcdea.py19721201.pp')
        self.assertRaises(StopIteration, next, it)

    def test_null_result(self):
        """Test for a null result, i.e. an empty iterator."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apy')
        args.append('--startdate=197012010000')
        args.append('--enddate=197012010000')
        args.append('--standard_absolute_time')
        args.append('--newmode')
        it = umfilelist.main_as_iterator(args)
        self.assertRaises(StopIteration, next, it)

    def test_valid_dates_option(self):
        """Test the valid dates option."""
        args = []
        args.append('--prefix=abcde')
        args.append('--suffix=.pp')
        args.append('--stream=apy')
        args.append('--startdate=197012010000')
        args.append('--enddate=197212010000')
        args.append('--standard_absolute_time')
        args.append('--newmode')
        args.append('--valid_dates')
        it = umfilelist.main_as_iterator(args)
        expect = ['abcdea.py19711201.pp', '197012010000', '197112010000']
        assertCountEqual(self, next(it), expect)
        expect = ['abcdea.py19721201.pp', '197112010000', '197212010000']
        assertCountEqual(self, next(it), expect)


if __name__ == '__main__':
    unittest.main()
