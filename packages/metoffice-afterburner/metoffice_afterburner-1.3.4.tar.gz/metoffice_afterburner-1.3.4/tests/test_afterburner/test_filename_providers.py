# (C) British Crown Copyright 2016-2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.filename_providers module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import assertCountEqual

import unittest
import cf_units
from afterburner.metavar import UmMetaVariable, NemoMetaVariable, CiceMetaVariable
from afterburner.filename_providers import *


class TestCreateFromMetavar(unittest.TestCase):
    """Test the FilenameProvider.from_metavar static method."""

    def test_create_from_um_metavar(self):
        """Test creation from UM meta-variable."""
        var = UmMetaVariable('6.0', 'abcde', stream_id='apy', stash_code='m01s00i024',
            time_range=('1970-12-01T00:00:00', '1972-12-01T00:00:00'))
        fnprovider = FilenameProvider.from_metavar(var)
        self.assertTrue(isinstance(fnprovider, UmFilenameProvider))
        self.assertTrue(fnprovider.ext, '.pp')

    def test_create_from_nemo_metavar(self):
        """Test creation from NEMO meta-variable."""
        var = NemoMetaVariable('1.0', 'abcde', 'ony', var_name='votemper',
            time_range=('1970-12-01T00:00:00', '1972-12-01T00:00:00'))
        fnprovider = FilenameProvider.from_metavar(var)
        self.assertTrue(isinstance(fnprovider, NemoFilenameProvider))
        self.assertTrue(fnprovider.ext, '.nc')

    def test_create_from_non_metavar(self):
        """Test creation from non-meta-variable object."""
        var = 'metavar'
        self.assertRaises(TypeError, FilenameProvider.from_metavar, var)


class TestUmFilenameProvider(unittest.TestCase):
    """Test the UmFilenameProvider class."""

    def test_um_apy_files(self):
        """Test UM apy files using 'classic' filenames."""
        fnprovider = UmFilenameProvider()
        var = UmMetaVariable('6.0', 'abcde', stream_id='apy', stash_code='m01s00i024',
            time_range=('1970-12-01T00:00:00', '1972-12-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY, newmode=False)
        actual = fnprovider.get_filenames(var)
        expect = ['abcdea.pyh1c10.pp', 'abcdea.pyh2c10.pp']
        assertCountEqual(self, actual, expect)

    def test_um_apy_files_newmode(self):
        """Test UM apy files using 'new-style' filenames."""
        fnprovider = UmFilenameProvider()
        var = UmMetaVariable('10.0', 'abcde', stream_id='apy', stash_code='m01s00i024',
            time_range=('1970-12-01T00:00:00', '1972-12-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var)
        expect = ['abcdea.py19711201.pp', 'abcdea.py19721201.pp']
        assertCountEqual(self, actual, expect)

    def test_um_ensemble_apy_files(self):
        """Test UM ensemble apy files using 'classic' filenames."""
        fnprovider = UmFilenameProvider()
        var = UmMetaVariable('10.0', 'abcde', realization_id='r1i2p3',
            stream_id='apy', stash_code='m01s00i024',
            time_range=('1970-12-01T00:00:00', '1972-12-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY, newmode=False)
        actual = fnprovider.get_filenames(var)
        expect = ['abcde-r1i2p3a.pyh1c10.pp', 'abcde-r1i2p3a.pyh2c10.pp']
        assertCountEqual(self, actual, expect)

    def test_um_ensemble_apy_files_newmode(self):
        """Test UM ensemble apy files using 'new-style' filenames."""
        fnprovider = UmFilenameProvider()
        var = UmMetaVariable('10.0', 'abcde', realization_id='r1i2p3',
            stream_id='apy', stash_code='m01s00i024',
            time_range=('1970-12-01T00:00:00', '1972-12-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var)
        expect = ['abcde-r1i2p3a.py19711201.pp', 'abcde-r1i2p3a.py19721201.pp']
        assertCountEqual(self, actual, expect)

    def test_um_aps_files(self):
        """Test UM aps files using 'classic' filenames."""
        fnprovider = UmFilenameProvider()
        var = UmMetaVariable('6.0', 'abcde', stream_id='aps', stash_code='m01s00i024',
            time_range=('1970-12-01T00:00:00', '1971-12-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY, newmode=False)
        actual = fnprovider.get_filenames(var)
        expect = ['abcdea.psh1djf.pp', 'abcdea.psh1mam.pp',
                  'abcdea.psh1jja.pp', 'abcdea.psh1son.pp']
        assertCountEqual(self, actual, expect)

    def test_um_aps_files_newmode(self):
        """Test UM aps files using 'new-style' filenames."""
        fnprovider = UmFilenameProvider()
        var = UmMetaVariable('10.0', 'abcde', stream_id='aps', stash_code='m01s00i024',
            time_range=('1970-12-01T00:00:00', '1971-12-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var)
        expect = ['abcdea.ps1971djf.pp', 'abcdea.ps1971mam.pp',
                  'abcdea.ps1971jja.pp', 'abcdea.ps1971son.pp']
        assertCountEqual(self, actual, expect)

    def test_um_apm_files(self):
        """Test UM apm files using 'classic' filenames."""
        fnprovider = UmFilenameProvider()
        var = UmMetaVariable('6.0', 'abcde', stream_id='apm', stash_code='m01s00i024',
            time_range=('1970-12-01T00:00:00', '1971-03-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY, newmode=False)
        actual = fnprovider.get_filenames(var)
        expect = ['abcdea.pmh0dec.pp', 'abcdea.pmh1jan.pp', 'abcdea.pmh1feb.pp']
        assertCountEqual(self, actual, expect)

    def test_um_apm_files_newmode(self):
        """Test UM apm files using 'new-style' filenames."""
        fnprovider = UmFilenameProvider()
        var = UmMetaVariable('10.0', 'abcde', stream_id='apm', stash_code='m01s00i024',
            time_range=('1970-12-01T00:00:00', '1971-03-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY, newmode=True)  # set newmode explicitly
        actual = fnprovider.get_filenames(var)
        expect = ['abcdea.pm1970dec.pp', 'abcdea.pm1971jan.pp', 'abcdea.pm1971feb.pp']
        assertCountEqual(self, actual, expect)

    def test_um_without_time_range(self):
        """Test UM files (old and new style) without a time range."""
        fnprovider = UmFilenameProvider()
        var = UmMetaVariable('6.0', 'abcde', stream_id='apy', stash_code='m01s00i024')
        actual = fnprovider.get_filenames(var)
        assertCountEqual(self, actual, ['abcdea.py*.pp'])

        var = UmMetaVariable('6.0', 'abcde', stream_id='apy', stash_code='m01s00i024',
            newmode=False)
        actual = fnprovider.get_filenames(var)
        assertCountEqual(self, actual, ['abcdea.py*.pp'])

        var = UmMetaVariable('6.0', 'mi-abcde', stream_id='apm', stash_code='m01s00i024')
        actual = fnprovider.get_filenames(var)
        assertCountEqual(self, actual, ['abcdea.pm*.pp'])

    def test_get_start_end_dates(self):
        """Test the _get_start_end_dates method."""
        fnprovider = UmFilenameProvider()
        var = UmMetaVariable('6.0', 'abcde', stream_id='apy', stash_code='m01s00i024',
            time_range=('1970-12-01T00:00:00', '1972-12-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider._get_start_end_dates(var)
        expect = ('197012010000', '197212010000')
        self.assertEqual(actual, expect)

        # Partial time-of-day info defined.
        var = UmMetaVariable('6.0', 'abcde', stream_id='apy', stash_code='m01s00i024',
            time_range=('1970-12-01T09', '1972-12-01T18'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider._get_start_end_dates(var)
        expect = ('197012010900', '197212011800')
        self.assertEqual(actual, expect)

        # No time-of-day info defined -> defaults to midnight.
        var = UmMetaVariable('6.0', 'abcde', stream_id='apy', stash_code='m01s00i024',
            time_range=('1970-12-01', '1972-12-01'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider._get_start_end_dates(var)
        expect = ('197012010000', '197212010000')
        self.assertEqual(actual, expect)

        # No date or time-of-day info defined --> error.
        var = UmMetaVariable('6.0', 'abcde', stream_id='apy', stash_code='m01s00i024')
        self.assertRaises(ValueError, fnprovider._get_start_end_dates, var)


class TestNemoFilenameProvider(unittest.TestCase):
    """Test the NemoFilenameProvider class."""

    def test_nemo_ony_files(self):
        """Test NEMO annual mean (ony) files."""
        fnprovider = NemoFilenameProvider()
        var = NemoMetaVariable('1.0', 'abcde', stream_id='ony', var_name='votemper',
            time_range=('1970-12-01T00:00:00', '1972-12-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var)
        expect = ['abcdeo_1y_19701201_19711130_grid_T.nc', 'abcdeo_1y_19711201_19721130_grid_T.nc']
        assertCountEqual(self, actual, expect)

    def test_nemo_ons_files(self):
        """Test NEMO seasonal mean (ons) files."""
        fnprovider = NemoFilenameProvider()
        var = NemoMetaVariable('1.0', 'abcde', stream_id='ons', var_name='votemper',
            time_range=('1970-12-01T00:00:00', '1971-12-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var)
        expect = ['abcdeo_1s_19701201_19710230_grid_T.nc', 'abcdeo_1s_19710301_19710530_grid_T.nc',
                  'abcdeo_1s_19710601_19710830_grid_T.nc', 'abcdeo_1s_19710901_19711130_grid_T.nc']
        assertCountEqual(self, actual, expect)

    def test_nemo_onm_files(self):
        """Test NEMO monthly mean (onm) files."""
        fnprovider = NemoFilenameProvider()
        var = NemoMetaVariable('1.0', 'abcde', stream_id='onm', var_name='votemper',
            time_range=('1970-12-01T00:00:00', '1971-03-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var)
        expect = ['abcdeo_1m_19701201_19701230_grid_T.nc', 'abcdeo_1m_19710101_19710130_grid_T.nc',
                  'abcdeo_1m_19710201_19710230_grid_T.nc']
        assertCountEqual(self, actual, expect)

    def test_nemo_onm_files_pad(self):
        """Test NEMO monthly mean (onm) files with non-aligned input dates."""
        fnprovider = NemoFilenameProvider()
        var = NemoMetaVariable('1.0', 'abcde', stream_id='onm', var_name='votemper',
            time_range=('1970-11-16T00:00:00', '1971-02-16T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var, padding=True)
        expect = ['abcdeo_1m_19701101_19701130_grid_T.nc', 'abcdeo_1m_19701201_19701230_grid_T.nc',
                  'abcdeo_1m_19710101_19710130_grid_T.nc', 'abcdeo_1m_19710201_19710230_grid_T.nc']
        assertCountEqual(self, actual, expect)

    def test_nemo_onm_files_no_pad(self):
        """Test NEMO monthly mean (onm) files with non-aligned input dates and no padding."""
        fnprovider = NemoFilenameProvider()
        var = NemoMetaVariable('1.0', 'abcde', stream_id='onm', var_name='votemper',
            time_range=('1970-11-16T00:00:00', '1971-02-16T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var, padding=False)
        expect = ['abcdeo_1m_19701201_19701230_grid_T.nc', 'abcdeo_1m_19710101_19710130_grid_T.nc']
        assertCountEqual(self, actual, expect)

    def test_nemo_ony_diaptr_files(self):
        """Test NEMO annual mean (ony) files on diaptr grid."""
        fnprovider = NemoFilenameProvider()
        var = NemoMetaVariable('1.0', 'abcde', stream_id='ony', var_name='votemper',
            time_range=('1970-12-01T00:00:00', '1972-12-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY, grid_type='diaptr')
        actual = fnprovider.get_filenames(var)
        expect = ['abcdeo_1y_19701201_19711130_diaptr.nc', 'abcdeo_1y_19711201_19721130_diaptr.nc']
        assertCountEqual(self, actual, expect)

    def test_nemo_ony_scalar_files(self):
        """Test NEMO annual mean (ony) files on scalar grid."""
        fnprovider = NemoFilenameProvider()
        var = NemoMetaVariable('1.0', 'abcde', stream_id='ony', var_name='votemper',
            time_range=('1970-12-01T00:00:00', '1972-12-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY, grid_type='scalar')
        actual = fnprovider.get_filenames(var)
        expect = ['abcdeo_1y_19701201_19711130_scalar.nc', 'abcdeo_1y_19711201_19721130_scalar.nc']
        assertCountEqual(self, actual, expect)

    def test_nemo_without_time_range(self):
        """Test NEMO files without a time range."""
        fnprovider = NemoFilenameProvider()
        var = NemoMetaVariable('1.0', 'abcde', stream_id='ony', var_name='sst')
        actual = fnprovider.get_filenames(var)
        expect = ['abcdeo_1y_*_grid_T.nc']
        assertCountEqual(self, actual, expect)

        var = NemoMetaVariable('1.0', 'mi-abcde', stream_id='ons', var_name='sst',
            grid_type='W')
        actual = fnprovider.get_filenames(var)
        expect = ['abcdeo_1s_*_grid_W.nc']
        assertCountEqual(self, actual, expect)

    def test_with_postproc2(self):
        """Test NEMO ony files using postproc 2.0 filenaming convention."""
        fnprovider = NemoFilenameProvider()
        var = NemoMetaVariable('1.0', 'abcde', stream_id='ony', var_name='votemper',
            time_range=('1970-12-01T00:00:00', '1972-12-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY, postproc_vn='2.0')
        actual = fnprovider.get_filenames(var)
        expect = ['nemo_*abcdeo_1y_19701201-19711201_grid-T.nc',
                  'nemo_*abcdeo_1y_19711201-19721201_grid-T.nc']
        assertCountEqual(self, actual, expect)

    def test_with_postproc2_wo_time_range(self):
        """Test NEMO ony files using postproc 2.0 but no time range."""
        fnprovider = NemoFilenameProvider()
        var = NemoMetaVariable('1.0', 'abcde', stream_id='ony', var_name='votemper',
            calendar=cf_units.CALENDAR_360_DAY, postproc_vn='2.0', grid_type='W')
        actual = fnprovider.get_filenames(var)
        expect = ['nemo_*abcdeo_1y_*-*_grid-W.nc']
        assertCountEqual(self, actual, expect)


class TestCiceFilenameProvider(unittest.TestCase):
    """Test the CiceFilenameProvider class."""

    def test_cice_iny_files(self):
        """Test CICE annual mean (iny) files."""
        fnprovider = CiceFilenameProvider()
        var = CiceMetaVariable('1.0', 'abcde', stream_id='iny', var_name='snoice',
            time_range=('1970-12-01T00:00:00', '1972-12-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var)
        expect = ['abcdei.1y.1971-11.nc', 'abcdei.1y.1972-11.nc']
        assertCountEqual(self, actual, expect)

    def test_cice_ins_files(self):
        """Test CICE seasonal mean (ins) files."""
        fnprovider = CiceFilenameProvider()
        var = CiceMetaVariable('1.0', 'abcde', stream_id='ins', var_name='snoice',
            time_range=('1970-12-01T00:00:00', '1971-12-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var)
        expect = ['abcdei.1s.1971-02.nc', 'abcdei.1s.1971-05.nc',
                  'abcdei.1s.1971-08.nc', 'abcdei.1s.1971-11.nc']
        assertCountEqual(self, actual, expect)

    def test_cice_inm_files(self):
        """Test CICE monthly mean (inm) files."""
        fnprovider = CiceFilenameProvider()
        var = CiceMetaVariable('1.0', 'abcde', stream_id='inm', var_name='snoice',
            time_range=('1970-12-01T00:00:00', '1971-03-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var)
        expect = ['abcdei.1m.1970-12.nc', 'abcdei.1m.1971-01.nc',
                  'abcdei.1m.1971-02.nc']
        assertCountEqual(self, actual, expect)

    def test_cice_inm_files_no_pad(self):
        """Test CICE monthly mean (inm) files with non-aligned input dates and no padding."""
        fnprovider = CiceFilenameProvider()
        var = CiceMetaVariable('1.0', 'abcde', stream_id='inm', var_name='snoice',
            time_range=('1970-11-16T00:00:00', '1971-02-16T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var, padding=False)
        expect = ['abcdei.1m.1970-12.nc', 'abcdei.1m.1971-01.nc']
        assertCountEqual(self, actual, expect)

    def test_cice_without_time_range(self):
        """Test CICE files without a time range."""
        fnprovider = CiceFilenameProvider()
        var = CiceMetaVariable('1.0', 'abcde', stream_id='iny', var_name='snoice')
        actual = fnprovider.get_filenames(var)
        expect = ['abcdei.1y.*.nc']
        assertCountEqual(self, actual, expect)

        var = CiceMetaVariable('1.0', 'mi-abcde', stream_id='ins', var_name='snoice')
        actual = fnprovider.get_filenames(var)
        expect = ['abcdei.1s.*.nc']
        assertCountEqual(self, actual, expect)

    def test_with_postproc2(self):
        """Test CICE iny files using postproc 2.0 filenaming convention."""
        fnprovider = CiceFilenameProvider()
        var = CiceMetaVariable('1.0', 'abcde', stream_id='iny', var_name='snoice',
            time_range=('1970-12-01T00:00:00', '1972-12-01T00:00:00'),
            calendar=cf_units.CALENDAR_360_DAY, postproc_vn='2.0')
        actual = fnprovider.get_filenames(var)
        expect = ['cice_*abcdei_1y_19701201-19711201.nc',
                  'cice_*abcdei_1y_19711201-19721201.nc']
        assertCountEqual(self, actual, expect)

    def test_with_postproc2_wo_time_range(self):
        """Test CICE iny files using postproc 2.0 but no time range."""
        fnprovider = CiceFilenameProvider()
        var = CiceMetaVariable('1.0', 'abcde', stream_id='iny', var_name='snoice',
            calendar=cf_units.CALENDAR_360_DAY, postproc_vn='2.0')
        actual = fnprovider.get_filenames(var)
        expect = ['cice_*abcdei_1y_*-*.nc']
        assertCountEqual(self, actual, expect)


class TestTemplateDrivenFilenameProvider(unittest.TestCase):
    """Test the TemplateDrivenFilenameProvider class."""

    def test_plain_metavar(self):
        template = '{model_name}_{run_id}_{stream_id}_{stash_code}.pp'
        fnprovider = TemplateDrivenFilenameProvider(template=template)
        var = UmMetaVariable('6.0', 'expid', stream_id='apy', stash_code='m01s00i024')
        actual = fnprovider.get_filenames(var)
        assertCountEqual(self, actual, ['UM_expid_apy_m01s00i024.pp'])

    def test_augmented_metavar(self):
        # note the use of 'runid' instead of 'run_id' in this template
        template = '{model_id}_{runid}{stream_letter}_{mean_period}_{$enddate}'
        fnprovider = TemplateDrivenFilenameProvider(template=template, ext='.pp')
        var = UmMetaVariable('6.0', 'expid', stream_id='apy', stash_code='m01s00i024')
        var.model_id = 'um'
        var.stream_letter = 'a'
        var.mean_period = '1y'
        actual = fnprovider.get_filenames(var)
        assertCountEqual(self, actual, ['um_expida_1y_*.pp'])

    def test_with_indexed_field(self):
        template = '{run_id}{stream_id[0]}.{stream_id[1]}{stream_id[2]}*.pp'
        fnprovider = TemplateDrivenFilenameProvider(template=template)
        var = UmMetaVariable('6.0', 'expid', stream_id='apy', stash_code='m01s00i024')
        actual = fnprovider.get_filenames(var)
        assertCountEqual(self, actual, ['expida.py*.pp'])

    def test_with_time_range(self):
        template = 'um_{run_id}_{stream_id}_{$startdate}-{$enddate}.pp'
        fnprovider = TemplateDrivenFilenameProvider(template=template)
        var = UmMetaVariable('6.0', 'expid', stream_id='apy', stash_code='m01s00i024',
            time_range=('1970-12-01', '1972-12-01'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var)
        expect = ['um_expid_apy_19701201-19711201.pp',
                  'um_expid_apy_19711201-19721201.pp']
        assertCountEqual(self, actual, expect)

    def test_with_time_range_ignored(self):
        template = 'um_{run_id}_{stream_id}_{stash_code}.pp'   # no date fields!
        fnprovider = TemplateDrivenFilenameProvider(template=template)
        var = UmMetaVariable('6.0', 'expid', stream_id='apy', stash_code='m01s00i024',
            time_range=('1970-12-01', '1972-12-01'),
            calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var)
        expect = ['um_expid_apy_m01s00i024.pp']
        assertCountEqual(self, actual, expect)

    def test_custom_date_fmt(self):
        template = 'um_{run_id}_{stream_id}_{$enddate}.pp'
        fnprovider = TemplateDrivenFilenameProvider(template=template)
        var = UmMetaVariable('6.0', 'expid', stream_id='apy', stash_code='m01s00i024',
            time_range=('1970-12-01', '1972-12-01'), calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var, date_fmt='%Y-%m')
        expect = ['um_expid_apy_1971-12.pp',
                  'um_expid_apy_1972-12.pp']
        assertCountEqual(self, actual, expect)

    def test_lowercase_conversion(self):
        template = '{model_name!l}_{run_id!l}_{stream_id}_{stash_code}.pp'
        fnprovider = TemplateDrivenFilenameProvider(template=template)
        var = UmMetaVariable('6.0', 'EXPID', stream_id='apy', stash_code='m01s00i024')
        actual = fnprovider.get_filenames(var)
        assertCountEqual(self, actual, ['um_expid_apy_m01s00i024.pp'])

    def test_uppercase_conversion(self):
        template = '{model_name!u}_{run_id!u}_{stream_id}_{var_name}.nc'
        fnprovider = TemplateDrivenFilenameProvider(template=template)
        var = NemoMetaVariable('6.0', 'expid', stream_id='ony', var_name='sst')
        actual = fnprovider.get_filenames(var)
        assertCountEqual(self, actual, ['NEMO_EXPID_ony_sst.nc'])

    def test_titlecase_conversion(self):
        template = '{model_name!t}_{run_id}_{stream_id}_{var_name!t}.nc'
        fnprovider = TemplateDrivenFilenameProvider(template=template)
        var = CiceMetaVariable('6.0', 'expid', stream_id='iny', var_name='ice_speed')
        actual = fnprovider.get_filenames(var)
        assertCountEqual(self, actual, ['Cice_expid_iny_Ice_Speed.nc'])

    def test_non_metavar(self):
        # define a variable-like class
        class Varlike(object):
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        template = '{model_name}_{run_id}_{stream_id}_{stash_code}.pp'
        fnprovider = TemplateDrivenFilenameProvider(template=template)
        var = Varlike(model_name='um', run_id='expid', stream_id='apy',
            stash_code='m01s00i024')
        actual = fnprovider.get_filenames(var)
        assertCountEqual(self, actual, ['um_expid_apy_m01s00i024.pp'])

    def test_bad_token(self):
        template = '{model_id}_{run_id}_{stream_id}_{stash_code}.pp'
        fnprovider = TemplateDrivenFilenameProvider(template=template)
        var = UmMetaVariable('6.0', 'expid', stream_id='apy', stash_code='m01s00i024')
        self.assertRaises(KeyError, fnprovider.get_filenames, var)

    def test_postproc1_nemo_template(self):
        fnprovider = TemplateDrivenFilenameProvider(template=POSTPROC_VN1_NEMO_TEMPLATE)
        var = NemoMetaVariable('6.0', 'expid', stream_id='ony', var_name='sst')
        var.start_date = '19701201'
        var.end_date = '19711130'
        var.meaning_period = '1y'
        var.grid_id = 'grid_T'
        actual = fnprovider.get_filenames(var)
        assertCountEqual(self, actual, ['expido_1y_19701201_19711130_grid_T.nc'])

    def test_postproc2_nemo_template(self):
        fnprovider = TemplateDrivenFilenameProvider(template=POSTPROC_VN2_NEMO_TEMPLATE)
        var = NemoMetaVariable('6.0', 'expid', stream_id='ony', var_name='sst')
        var.start_date = '19701201'
        var.end_date = '19711201'
        var.meaning_period = '1y'
        var.grid_id = 'grid-T'
        actual = fnprovider.get_filenames(var)
        assertCountEqual(self, actual, ['nemo_expido_1y_19701201-19711201_grid-T.nc'])

    def test_postproc1_cice_template(self):
        fnprovider = TemplateDrivenFilenameProvider(template=POSTPROC_VN1_CICE_TEMPLATE)
        var = CiceMetaVariable('6.0', 'expid', stream_id='iny', var_name='ice_speed')
        var.end_date = '1970-12'
        var.meaning_period = '1y'
        actual = fnprovider.get_filenames(var)
        assertCountEqual(self, actual, ['expidi.1y.1970-12.nc'])

    def test_postproc2_cice_template(self):
        fnprovider = TemplateDrivenFilenameProvider(template=POSTPROC_VN2_CICE_TEMPLATE)
        var = CiceMetaVariable('6.0', 'expid', stream_id='iny', var_name='ice_speed')
        var.start_date = '19701201'
        var.end_date = '19711201'
        var.meaning_period = '1y'
        actual = fnprovider.get_filenames(var)
        assertCountEqual(self, actual, ['cice_expidi_1y_19701201-19711201.nc'])

    def test_date_chunker_callback(self):
        # define a date chunker generator
        def date_chunker(var, padding=True, date_fmt='%Y-%m-%d', end_offset=0):
            date_pairs = (('1970-12-01', '1971-12-01'), ('1971-12-01', '1972-12-01'))
            for pair in date_pairs:
                yield pair

        template = 'um_{run_id}_{stream_id}_{$startdate}_{$enddate}.pp'
        fnprovider = TemplateDrivenFilenameProvider(template=template)
        var = UmMetaVariable('6.0', 'expid', stream_id='apy', stash_code='m01s00i024',
            time_range=('1970-12-01', '1972-12-01'), calendar=cf_units.CALENDAR_360_DAY)
        actual = fnprovider.get_filenames(var)
        expect = ['um_expid_apy_1970-12-01_1971-12-01.pp',
                  'um_expid_apy_1971-12-01_1972-12-01.pp']


if __name__ == '__main__':
    unittest.main()
