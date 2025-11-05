# (C) British Crown Copyright 2016-2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Script for testing various operations against a StreamSplit data cache.
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
from afterburner.io.datacaches import DataCache, DATA_CACHE_SCHEMES, STREAM_SPLIT_SCHEME
from afterburner.exceptions import DataCacheError


class TestStreamSplitCache(unittest.TestCase):

    def setUp(self):
        # create a MASS data store object
        self.massds = MassDataStore()

        # create a temporary base directory
        self.base_dir = tempfile.mkdtemp()

        # create a data cache object
        self.cache = DataCache.create_cache(STREAM_SPLIT_SCHEME, self.massds,
            self.base_dir)

        # create some UM and NEMO meta-variables to work with
        self.runid = runid = 'abcde'
        self.var_apy_3236 = UmMetaVariable('8.5', runid, stream_id='apy',
            stash_code='m01s03i236', lbproc=128,
            time_range=('1980-12-01T00:00:00', '1985-12-01T00:00:00'))
        self.var_apy_5216 = UmMetaVariable('8.5', runid, stream_id='apy',
            stash_code='m01s05i216', lbproc=128,
            time_range=('1990-12-01T00:00:00', '1995-12-01T00:00:00'))
        self.var_ony_sst = NemoMetaVariable('8.5', runid, stream_id='ony',
            var_name='sosstsst',
            time_range=('1980-12-01T00:00:00', '1985-12-01T00:00:00'))
        self.var_ony_sal = NemoMetaVariable('8.5', runid, stream_id='ony',
            var_name='salinity',
            time_range=('1990-12-01T00:00:00', '1995-12-01T00:00:00'))

    def tearDown(self):
        if os.path.isdir(self.base_dir):
            shutil.rmtree(self.base_dir, ignore_errors=True)

    def test_no_files_present(self):
        varlist = [self.var_ony_sst]
        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(len(actual), 0)
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        self.assertEqual(len(expected), 5)

    def test_some_um_files_present(self):
        varlist = [self.var_apy_3236]
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        _create_cache_files(expected[:3])
        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(len(actual), 3)
        self.assertEqual(sorted(actual), sorted(expected[:3]))
        self.cache.delete_files(varlist)

    def test_some_nemo_files_present(self):
        varlist = [self.var_ony_sst]
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        _create_cache_files(expected[:3])
        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(len(actual), 3)
        self.assertEqual(sorted(actual), sorted(expected[:3]))
        self.cache.delete_files(varlist)

    def test_all_um_files_present(self):
        varlist = [self.var_apy_3236, self.var_apy_5216]
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        _create_cache_files(expected)
        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(sorted(actual), sorted(expected))
        self.cache.delete_files(varlist)

    def test_all_nemo_files_present(self):
        varlist = [self.var_ony_sst, self.var_ony_sal]
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        _create_cache_files(expected)
        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(sorted(actual), sorted(expected))
        self.cache.delete_files(varlist)

    def test_mixed_files_present(self):
        varlist = [self.var_apy_3236, self.var_apy_5216,
                   self.var_ony_sst, self.var_ony_sal]
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        _create_cache_files(expected)
        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(sorted(actual), sorted(expected))
        self.cache.delete_files(varlist)

    def test_delete_um_files(self):
        varlist = [self.var_apy_3236, self.var_apy_5216]
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        _create_cache_files(expected)

        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(sorted(actual), sorted(expected))

        self.cache.delete_files([self.var_apy_3236])
        actual = list(self.cache.iter_filepaths(varlist))
        expected = set(self.cache.iter_filepaths([self.var_apy_5216], expected=True)) - \
            set(self.cache.iter_filepaths([self.var_apy_3236], expected=True))
        self.assertEqual(sorted(actual), sorted(expected))
        self.cache.delete_files(varlist)

    def test_delete_nemo_files(self):
        varlist = [self.var_ony_sst, self.var_ony_sal]
        expected = list(self.cache.iter_filepaths(varlist, expected=True))
        _create_cache_files(expected)

        # test all files present
        actual = list(self.cache.iter_filepaths(varlist))
        self.assertEqual(sorted(actual), sorted(expected))

        # delete files for 'sosstsst' variable and retest remaining files
        self.cache.delete_files([self.var_ony_sst])
        actual = list(self.cache.iter_filepaths(varlist))
        expected = set(self.cache.iter_filepaths([self.var_ony_sal], expected=True)) - \
            set(self.cache.iter_filepaths([self.var_ony_sst], expected=True))
        self.assertEqual(sorted(actual), sorted(expected))
        self.cache.delete_files(varlist)

    def test_cache_type_mismatch(self):
        with self.assertRaises(DataCacheError):
            for scheme in [x for x in DATA_CACHE_SCHEMES if x != STREAM_SPLIT_SCHEME]:
                DataCache.create_cache(scheme, self.massds, self.base_dir)

    def test_cache_type_no_mismatch(self):
        cache = DataCache.create_cache(STREAM_SPLIT_SCHEME, self.massds, self.base_dir)
        self.assertTrue(os.path.exists(cache.readme_file))

    def test_init_in_readonly_mode(self):
        # try with existing (but empty) base directory - should succeed
        base_dir = tempfile.mkdtemp()
        cache = DataCache.create_cache(STREAM_SPLIT_SCHEME, self.massds, base_dir,
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
            DataCache.create_cache(STREAM_SPLIT_SCHEME, self.massds, base_dir,
                read_only=True)

    def test_query_in_readonly_mode(self):
        varlist = [self.var_apy_3236, self.var_ony_sst]
        expected = self.cache.get_filepaths(varlist, expected=True, sort=True)
        _create_cache_files(expected)
        cache = DataCache.create_cache(STREAM_SPLIT_SCHEME, self.massds, self.base_dir,
            read_only=True)
        actual = cache.get_filepaths(varlist, sort=True)
        self.assertEqual(actual, expected)

    def test_fetch_files_in_readonly_mode(self):
        cache = DataCache.create_cache(STREAM_SPLIT_SCHEME, self.massds, self.base_dir,
            read_only=True)
        varlist = [self.var_apy_3236]
        with self.assertRaises(DataCacheError):
            cache.fetch_files(varlist)

    def test_fetch_stream_in_readonly_mode(self):
        cache = DataCache.create_cache(STREAM_SPLIT_SCHEME, self.massds, self.base_dir,
            read_only=True)
        with self.assertRaises(DataCacheError):
            cache.fetch_stream('UM', 'expid', 'apy')

    def test_delete_in_readonly_mode(self):
        varlist = [self.var_apy_3236]
        expected = self.cache.get_filepaths(varlist, expected=True, sort=True)
        _create_cache_files(expected)
        cache = DataCache.create_cache(STREAM_SPLIT_SCHEME, self.massds, self.base_dir,
            read_only=True)
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
