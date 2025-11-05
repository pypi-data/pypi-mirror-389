# (C) British Crown Copyright 2016-2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Script for testing various operations against an EnsembleVarSplit data cache.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import os
import shutil
import tempfile
import unittest
import random

from afterburner.metavar import UmMetaVariable, NemoMetaVariable
from afterburner.io.datastores import MassDataStore
from afterburner.io.datacaches import DataCache, DATA_CACHE_SCHEMES, ENSEMBLE_VAR_SPLIT_SCHEME
from afterburner.exceptions import DataCacheError


class TestEnsembleVarSplitCache(unittest.TestCase):

    def setUp(self):
        # create a MASS data store object
        self.massds = MassDataStore(data_class='ens')
        
        # create a temporary base directory
        self.base_dir = tempfile.mkdtemp()

        # create a temporary base directory
        self.cache = DataCache.create_cache(ENSEMBLE_VAR_SPLIT_SCHEME, self.massds,
            self.base_dir)

        # create some ensemble-style UM and NEMO meta-variables to work with
        runid = 'abcde'
        time_range = ('1980-12-01T00:00:00', '1985-12-01T00:00:00')
        for i in range(1, 4):
            rip = 'r%di1p1' % i
            um_var = UmMetaVariable('8.5', runid, realization_id=rip,
                stream_id='apy', stash_code='m01s03i236', lbproc=128,
                time_range=time_range)
            setattr(self, 'um_var_r%d'%i, um_var)

            nemo_var = NemoMetaVariable('8.5', runid, realization_id=rip,
                stream_id='ony', var_name='sosstsst', time_range=time_range)
            nemo_var.realization_id = 'r%di1p1' % i
            setattr(self, 'nemo_var_r%d'%i, nemo_var)

    def tearDown(self):
        if os.path.isdir(self.base_dir):
            shutil.rmtree(self.base_dir, ignore_errors=True)

    def test_no_files_present(self):
        varlist = [self.um_var_r1]
        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(len(actual), 0)
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        self.assertEqual(len(expected), 5)

    def test_some_um_files_present(self):
        varlist = [self.um_var_r1]
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        _create_cache_files(expected[:3])
        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(len(actual), 3)
        self.assertEqual(sorted(actual), sorted(expected[:3]))
        self.cache.delete_files(varlist)

    def test_some_nemo_files_present(self):
        varlist = [self.nemo_var_r1]
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        _create_cache_files(expected[:3])
        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(len(actual), 3)
        self.assertEqual(sorted(actual), sorted(expected[:3]))
        self.cache.delete_files(varlist)

    def test_all_um_files_present(self):
        varlist = [self.um_var_r1, self.um_var_r2, self.um_var_r3]
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        _create_cache_files(expected)
        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(sorted(actual), sorted(expected))
        self.cache.delete_files(varlist)

    def test_all_nemo_files_present(self):
        varlist = [self.nemo_var_r1, self.nemo_var_r2, self.nemo_var_r3]
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        _create_cache_files(expected)
        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(sorted(actual), sorted(expected))
        self.cache.delete_files(varlist)

    def test_mixed_files_present(self):
        varlist = [self.um_var_r1, self.um_var_r2,
                   self.nemo_var_r1, self.nemo_var_r2]
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        _create_cache_files(expected)
        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(sorted(actual), sorted(expected))
        self.cache.delete_files(varlist)

    def test_delete_um_files(self):
        varlist = [self.um_var_r1, self.um_var_r2]
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        _create_cache_files(expected)

        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(sorted(actual), sorted(expected))

        self.cache.delete_files([self.um_var_r1])
        actual = list(self.cache.iter_filepaths(varlist))
        expected = [fn for fn in expected if self.um_var_r1.realization_id not in fn]
        self.assertEqual(sorted(actual), sorted(expected))
        self.cache.delete_files(varlist)

    def test_delete_nemo_files(self):
        varlist = [self.nemo_var_r1, self.nemo_var_r2]
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        _create_cache_files(expected)

        # test all files present
        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(sorted(actual), sorted(expected))

        # delete files for 'sosstsst' variable and retest remaining files
        self.cache.delete_files([self.nemo_var_r1])
        actual = list(self.cache.iter_filepaths(varlist))
        expected = [fn for fn in expected if self.nemo_var_r1.realization_id not in fn]
        self.assertEqual(sorted(actual), sorted(expected))
        self.cache.delete_files(varlist)

    def test_missing_realization_id(self):
        um_var = self.um_var_r1.copy()
        um_var.realization_id = None
        self.assertRaises(AttributeError, self.cache.get_cache_dir_for_variable, um_var)

        nemo_var = self.nemo_var_r1.copy()
        nemo_var.realization_id = None
        self.assertRaises(AttributeError, self.cache.get_cache_dir_for_variable, nemo_var)

    def test_null_realization_dir(self):
        cache = DataCache.create_cache(ENSEMBLE_VAR_SPLIT_SCHEME, self.massds,
            base_dir=self.base_dir, null_realization_dir='r0')

        um_var = self.um_var_r1.copy()
        um_var.realization_id = None
        actual = cache.get_cache_dir_for_variable(um_var)
        expected = os.path.join(um_var.suite_id, 'r0', um_var.stream_id, um_var.slug)
        self.assertEqual(actual, expected)

        nemo_var = self.nemo_var_r1.copy()
        nemo_var.realization_id = None
        actual = cache.get_cache_dir_for_variable(nemo_var)
        expected = os.path.join(nemo_var.suite_id, 'r0', nemo_var.stream_id, nemo_var.slug)
        self.assertEqual(actual, expected)

    def test_cache_type_mismatch(self):
        with self.assertRaises(DataCacheError):
            for scheme in [x for x in DATA_CACHE_SCHEMES if x != ENSEMBLE_VAR_SPLIT_SCHEME]:
                DataCache.create_cache(scheme, self.massds, self.base_dir)

    def test_cache_type_no_mismatch(self):
        cache = DataCache.create_cache(ENSEMBLE_VAR_SPLIT_SCHEME, self.massds, self.base_dir)
        self.assertTrue(os.path.exists(cache.readme_file))

    def test_init_in_readonly_mode(self):
        # try with existing (but empty) base directory - should succeed
        base_dir = tempfile.mkdtemp()
        cache = DataCache.create_cache(ENSEMBLE_VAR_SPLIT_SCHEME, self.massds, base_dir,
            read_only=True)
        self.assertFalse(os.path.exists(cache.readme_file))
        try:
            os.rmdir(base_dir)
        except OSError:
            pass

        # try with non-existent base directory - should fail
        leaf_dir = "pid{0}_{1}".format(os.getpid(), random.randint(0, int(1e6)))
        base_dir = os.path.join(os.environ.get('TMPDIR', '/tmp'), leaf_dir)
        with self.assertRaises(DataCacheError):
            DataCache.create_cache(ENSEMBLE_VAR_SPLIT_SCHEME, self.massds, base_dir,
                read_only=True)

    def test_query_in_readonly_mode(self):
        varlist = [self.um_var_r1, self.nemo_var_r1]
        expected = self.cache.get_filepaths(varlist, expected=True, sort=True)
        _create_cache_files(expected)
        cache = DataCache.create_cache(ENSEMBLE_VAR_SPLIT_SCHEME, self.massds,
            self.base_dir, read_only=True)
        actual = cache.get_filepaths(varlist, sort=True)
        self.assertEqual(actual, expected)

    def test_fetch_files_in_readonly_mode(self):
        cache = DataCache.create_cache(ENSEMBLE_VAR_SPLIT_SCHEME, self.massds,
            self.base_dir, read_only=True)
        varlist = [self.um_var_r1]
        with self.assertRaises(DataCacheError):
            cache.fetch_files(varlist)

    def test_delete_in_readonly_mode(self):
        varlist = [self.um_var_r1]
        expected = self.cache.get_filepaths(varlist, expected=True, sort=True)
        _create_cache_files(expected)
        cache = DataCache.create_cache(ENSEMBLE_VAR_SPLIT_SCHEME, self.massds,
            self.base_dir, read_only=True)
        with self.assertRaises(DataCacheError):
            cache.delete_files(varlist)


def _create_cache_files(filenames):
    """Creates empty files in a data cache."""
    for fn in filenames:
        leafdir = os.path.dirname(fn)
        if not os.path.isdir(leafdir): os.makedirs(leafdir)
        os.system('touch ' + fn)


if __name__ == '__main__':
    unittest.main()
