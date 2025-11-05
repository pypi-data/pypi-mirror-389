# (C) British Crown Copyright 2016-2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Unit tests for the afterburner.utils.fileutils module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import assertCountEqual

import os
import unittest
import datetime
import tempfile

from afterburner.utils import fileutils


class TestExpandPath(unittest.TestCase):
    """Unit tests for the fileutils.expand_path function."""

    def test_no_tokens(self):
        """Test simple case in which path contains neither '~' nor '$' tokens."""
        self.assertEqual(fileutils.expand_path('/p/x/y/z'), '/p/x/y/z')
        expect = os.getcwd() + '/p/x/y/z'
        self.assertEqual(fileutils.expand_path('p/x/y/z'), expect)

    @unittest.skipUnless('HOME' in os.environ, "$HOME not defined in calling environment")
    def test_user_token(self):
        """Test for '~' token."""
        expect = os.environ['HOME'] + '/x/y/z'
        self.assertEqual(fileutils.expand_path('~/x/y/z'), expect)

    @unittest.skipUnless('HOME' in os.environ, "$HOME not defined in calling environment")
    def test_var_token(self):
        """Test for '$' token."""
        expect = os.environ['HOME'] + '/x/y/z'
        self.assertEqual(fileutils.expand_path('$HOME/x/y/z'), expect)

    @unittest.skipUnless('HOME' in os.environ, "$HOME not defined in calling environment")
    def test_user_and_var_tokens(self):
        """Test for both '~' and '$' tokens."""
        # Atypical usage, but we'll test for it anyway.
        os.environ['FOO'] = 'foo'
        expect = os.environ['HOME'] + '/x/y/foo'
        self.assertEqual(fileutils.expand_path('~/x/y/$FOO'), expect)
        os.environ['BAR'] = 'bar'
        expect = os.environ['HOME'] + '/x/y/foo/bar'
        self.assertEqual(fileutils.expand_path('~/x/y/$FOO/$BAR'), expect)


class TestSentinelFiles(unittest.TestCase):
    """Unit tests for the fileutils.filter_by_sentinel_files function."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.sent_dir = tempfile.mkdtemp()

    def tearDown(self):
        for tmpdir in [self.test_dir, self.sent_dir]:
            if os.path.isdir(tmpdir):
                for fname in os.listdir(tmpdir):
                    os.remove(os.path.join(tmpdir, fname))
        try:
            os.rmdir(self.test_dir)
            os.rmdir(self.sent_dir)
        except OSError:
            pass

    def test_with_all_sentinel_files(self):
        test_files = self._create_test_files(self.test_dir)
        sent_files = self._create_sentinel_files(self.sent_dir, test_files)
        self.assertEqual(len(sent_files), len(test_files))
        self.assertEqual(sent_files, [f+'.arch' for f in test_files])
        filtered = fileutils.filter_by_sentinel_files(test_files, self.test_dir,
            sentinel_dir=self.sent_dir)
        self.assertEqual(len(filtered), len(test_files))

    def test_with_some_sentinel_files(self):
        test_files = self._create_test_files(self.test_dir)
        sent_files = self._create_sentinel_files(self.sent_dir, test_files[:2])
        self.assertEqual(len(sent_files), 2)
        filtered = fileutils.filter_by_sentinel_files(test_files, self.test_dir,
            sentinel_dir=self.sent_dir)
        self.assertEqual(len(filtered), 2)

    def test_with_no_sentinel_files(self):
        test_files = self._create_test_files(self.test_dir)
        filtered = fileutils.filter_by_sentinel_files(test_files, self.test_dir,
            sentinel_dir=self.sent_dir)
        self.assertEqual(len(filtered), 0)

    def test_with_custom_source_file_ext(self):
        test_files = self._create_test_files(self.test_dir, ext='.pp')
        sent_files = self._create_sentinel_files(self.sent_dir, test_files[:2])
        self.assertEqual(len(sent_files), 2)
        filtered = fileutils.filter_by_sentinel_files(test_files, self.test_dir,
            sentinel_dir=self.sent_dir)
        self.assertEqual(len(filtered), 2)

    def test_with_custom_sentinel_file_ext(self):
        test_files = self._create_test_files(self.test_dir)
        sent_files = self._create_sentinel_files(self.sent_dir, test_files[:2],
            ext='.tag')
        self.assertEqual(len(sent_files), 2)
        filtered = fileutils.filter_by_sentinel_files(test_files, self.test_dir,
            sentinel_dir=self.sent_dir, sentinel_file_ext='.tag')
        self.assertEqual(len(filtered), 2)

    def test_with_custom_file_exts(self):
        test_files = self._create_test_files(self.test_dir, ext='.pp')
        sent_files = self._create_sentinel_files(self.sent_dir, test_files[:2],
            ext='.tag')
        self.assertEqual(len(sent_files), 2)
        filtered = fileutils.filter_by_sentinel_files(test_files, self.test_dir,
            sentinel_dir=self.sent_dir, sentinel_file_ext='.tag')
        self.assertEqual(len(filtered), 2)

    def test_with_unmatched_sentinel_files(self):
        test_files = self._create_test_files(self.test_dir, ext='.nc')
        sent_files = self._create_sentinel_files(self.sent_dir, [f[:-3] for f in test_files])
        filtered = fileutils.filter_by_sentinel_files(test_files, self.test_dir,
            sentinel_dir=self.sent_dir)
        self.assertEqual(len(filtered), 0)

        sent_files = self._create_sentinel_files(self.sent_dir, ['foo'+f for f in test_files])
        filtered = fileutils.filter_by_sentinel_files(test_files, self.test_dir,
            sentinel_dir=self.sent_dir)
        self.assertEqual(len(filtered), 0)

    def test_same_directory(self):
        test_files = self._create_test_files(self.test_dir)
        sent_files = self._create_sentinel_files(self.test_dir, test_files[:2])
        self.assertEqual(len(sent_files), 2)
        filtered = fileutils.filter_by_sentinel_files(test_files, self.test_dir)
        self.assertEqual(len(filtered), 2)

        sent_files = self._create_sentinel_files(self.test_dir, test_files)
        self.assertEqual(len(sent_files), len(test_files))
        filtered = fileutils.filter_by_sentinel_files(test_files, self.test_dir)
        self.assertEqual(len(filtered), len(test_files))

    def test_files_with_dot_chars_no_ext(self):
        test_files = self._create_test_files(self.test_dir, prefix='expid.')
        sent_files = self._create_sentinel_files(self.sent_dir, test_files[:2])
        self.assertEqual(len(sent_files), 2)
        filtered = fileutils.filter_by_sentinel_files(test_files, self.test_dir,
            sentinel_dir=self.sent_dir)
        self.assertEqual(len(filtered), 2)

    def test_files_with_dot_chars_plus_ext(self):
        test_files = self._create_test_files(self.test_dir, prefix='expid.', ext='.ff')
        sent_files = self._create_sentinel_files(self.sent_dir, test_files[:2])
        self.assertEqual(len(sent_files), 2)
        filtered = fileutils.filter_by_sentinel_files(test_files, self.test_dir,
            sentinel_dir=self.sent_dir)
        self.assertEqual(len(filtered), 2)

    def _create_test_files(self, tmpdir, prefix='', ext='', nfiles=5):
        tmpfiles = []
        for i in range(nfiles):
            _fh, fname = tempfile.mkstemp(dir=tmpdir, prefix=prefix, suffix=ext)
            tmpfiles.append(os.path.basename(fname))
        return tmpfiles

    def _create_sentinel_files(self, tmpdir, filenames, ext='.arch'):
        tmpfiles = []
        for name in filenames:
            fname = name + ext
            open(os.path.join(tmpdir, fname),  'a').close()
            tmpfiles.append(fname)
        return tmpfiles


class TestTruncatePath(unittest.TestCase):
    """Unit tests for the fileutils.truncate_path function."""

    def test_abs_path(self):
        """Test with absolute pathnames."""
        self.assertEqual(fileutils.truncate_path('/p/x/y/z', 'p'), '/p')
        self.assertEqual(fileutils.truncate_path('/p/x/y/z', 'x'), '/p/x')
        self.assertEqual(fileutils.truncate_path('/p/x/y/z/', 'y'), '/p/x/y')

    def test_rel_path(self):
        """Test with relative pathnames."""
        self.assertEqual(fileutils.truncate_path('p/x/y/z', 'p'), 'p')
        self.assertEqual(fileutils.truncate_path('p/x/y/z', 'x'), 'p/x')
        self.assertEqual(fileutils.truncate_path('p/x/y/z/', 'y'), 'p/x/y')

    def test_leftmost_ancestor(self):
        """Test correct selection of left-most ancestor."""
        self.assertEqual(fileutils.truncate_path('/p/x/y/x/z', 'x'), '/p/x')
        self.assertEqual(fileutils.truncate_path('/p/x/y/x/y/z', 'y'), '/p/x/y')

    def test_rightmost_ancestor(self):
        """Test correct selection of right-most, or only, ancestor."""
        self.assertEqual(fileutils.truncate_path('/p/x/y/x/z', 'x', right=True),
            '/p/x/y/x')
        self.assertEqual(fileutils.truncate_path('/p/x/y/x/z', 'y', right=True),
            '/p/x/y')
        self.assertEqual(fileutils.truncate_path('/p/x/y/x/y/z', 'y', right=True),
            '/p/x/y/x/y')

    def test_missing_ancestor(self):
        """Test missing ancestor."""
        self.assertEqual(fileutils.truncate_path('/p/x/y/z', 'q'), None)
        self.assertEqual(fileutils.truncate_path('/p/qq/x/z', 'q'), None)
        self.assertEqual(fileutils.truncate_path('/q1/q2/q3', 'q'), None)


class TestListFilesNewerThan(unittest.TestCase):
    """Unit tests for the fileutils.list_files_newer_than function."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.isdir(self.tmpdir):
            for fname in os.listdir(self.tmpdir):
                os.remove(os.path.join(self.tmpdir, fname))

    def test_newer_files(self):
        reftime = datetime.datetime.now() - datetime.timedelta(days=1)
        tmpfiles = self._create_test_files()
        files = fileutils.list_files_newer_than(self.tmpdir, reftime, abspath=1)
        assertCountEqual(self, files, tmpfiles)

    def test_older_files(self):
        reftime = datetime.datetime.now() + datetime.timedelta(days=1)
        tmpfiles = self._create_test_files()
        files = fileutils.list_files_newer_than(self.tmpdir, reftime, abspath=1)
        self.assertEqual(len(files), 0)

    def test_same_age_files(self):
        tmpfiles = self._create_test_files()
        st = os.stat(tmpfiles[-1])   # get time info for last file
        reftime = datetime.datetime.fromtimestamp(st.st_mtime)
        files = fileutils.list_files_newer_than(self.tmpdir, reftime, abspath=1)
        self.assertEqual(len(files), 0)

    def _create_test_files(self, nfiles=3):
        tmpfiles = []
        for i in range(nfiles):
            _fh, fname = tempfile.mkstemp(dir=self.tmpdir)
            tmpfiles.append(fname)
        return tmpfiles


class TestListFilesAtOrNewerThan(unittest.TestCase):
    """Unit tests for the fileutils.list_files_at_or_newer_than function."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.isdir(self.tmpdir):
            for fname in os.listdir(self.tmpdir):
                os.remove(os.path.join(self.tmpdir, fname))

    def test_newer_files(self):
        reftime = datetime.datetime.now() - datetime.timedelta(days=1)
        tmpfiles = self._create_test_files()
        files = fileutils.list_files_at_or_newer_than(self.tmpdir, reftime, abspath=1)
        assertCountEqual(self, files, tmpfiles)

    def test_older_files(self):
        reftime = datetime.datetime.now() + datetime.timedelta(days=1)
        tmpfiles = self._create_test_files()
        files = fileutils.list_files_at_or_newer_than(self.tmpdir, reftime, abspath=1)
        self.assertEqual(len(files), 0)

    def test_same_age_files(self):
        tmpfiles = self._create_test_files()
        st = os.stat(tmpfiles[0])   # get time info for first file
        reftime = datetime.datetime.fromtimestamp(st.st_mtime)
        files = fileutils.list_files_at_or_newer_than(self.tmpdir, reftime, abspath=1)
        self.assertGreater(len(files), 0)   # should find at least 1 file

    def _create_test_files(self, nfiles=3):
        tmpfiles = []
        for i in range(nfiles):
            _fh, fname = tempfile.mkstemp(dir=self.tmpdir)
            tmpfiles.append(fname)
        return tmpfiles


if __name__ == '__main__':
    unittest.main()
