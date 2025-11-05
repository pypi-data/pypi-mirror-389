# (C) British Crown Copyright 2016-2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Unit tests for the afterburner.io.moose module
"""
from __future__ import (absolute_import, division, unicode_literals)
from six.moves import (filter, input, map, range, zip)

import unittest
import subprocess
from io import StringIO
from iris.time import PartialDateTime

try:
    # python3
    from unittest import mock
    builtin_open_func = 'builtins.open'
except ImportError:
    # python2
    import mock
    builtin_open_func = '__builtin__.open'

from afterburner.io import moose
import afterburner.exceptions

MOOSE_SYSTEM_OUTAGE = 3
MOOSE_SUCCESS = 0


class TestHasMooseSupport(unittest.TestCase):
    """ Test has_moose_support() """
    def setUp(self):
        patch = mock.patch('afterburner.io.moose.subprocess.check_output')
        self.mock_chk_op = patch.start()
        self.addCleanup(patch.stop)

    def test_moose_available(self):
        self.mock_chk_op.return_value = 'ok'
        self.assertTrue(moose.has_moose_support())

    def test_moo_client_fails(self):
        self.mock_chk_op.side_effect = subprocess.CalledProcessError(1, 'cmd')
        self.assertFalse(moose.has_moose_support())

    def test_moo_client_not_found(self):
        self.mock_chk_op.side_effect = OSError()
        self.assertFalse(moose.has_moose_support())


class TestCheckMooseCommandsEnabled(unittest.TestCase):
    """ Test check_moose_commands_enabled() """
    def setUp(self):
        patch = mock.patch('afterburner.io.moose.subprocess.Popen')
        self.mock_popen = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.io.moose._run_moose_command')
        self.mock_run_cmd = patch.start()
        self.addCleanup(patch.stop)

    # generates an object whose wait() method indicates a failure
    class ReturnFail(object):
        def wait(self):
            return MOOSE_SYSTEM_OUTAGE

    # generates an object whose wait() method indicates success
    class ReturnSuccess(object):
        def wait(self):
            return MOOSE_SUCCESS

    def test_no_tests_specified(self):
        """ Check that if no commands are specified then False is returned """
        self.assertFalse(moose.check_moose_commands_enabled(0))

    def test_moose_unavailable(self):
        """ If moo si -v can't be run then MooseUnavailableError is raised and
        so check that this results in False being returned """
        self.mock_run_cmd.side_effect = \
            afterburner.exceptions.MooseUnavailableError()

        self.assertFalse(moose.check_moose_commands_enabled(moose.MOOSE_PUT))

    def test_ls_enabled(self):
        self.mock_popen.return_value = self.ReturnSuccess()
        self.assertTrue(moose.check_moose_commands_enabled(moose.MOOSE_LS))

    def test_each_command_enabled(self):
        true_tests = {
            '    PUT commands enabled: true': moose.MOOSE_PUT,
            '    GET commands enabled: true': moose.MOOSE_GET,
            '    SELECT commands enabled: true': moose.MOOSE_SELECT,
            '    MDLS commands enabled: true': moose.MOOSE_MDLS}

        for test in true_tests:
            self.mock_run_cmd.return_value = [test]
            self.assertTrue(moose.check_moose_commands_enabled(
                true_tests[test]))

    def test_ls_disabled(self):
        self.mock_popen.return_value = self.ReturnFail()
        self.assertFalse(moose.check_moose_commands_enabled(moose.MOOSE_LS))

    def test_each_command_disabled(self):
        false_tests = {
            '    PUT commands enabled: false': moose.MOOSE_PUT,
            '    GET commands enabled: false': moose.MOOSE_GET,
            '    SELECT commands enabled: false': moose.MOOSE_SELECT,
            '    MDLS commands enabled: false': moose.MOOSE_MDLS}

        for test in false_tests:
            self.mock_run_cmd.return_value = [test]
            self.assertFalse(moose.check_moose_commands_enabled(
                false_tests[test]))

    def test_ls_and_put_enabled(self):
        self.mock_popen.return_value = self.ReturnSuccess()
        self.mock_run_cmd.return_value = ['    PUT commands enabled: true']
        self.assertTrue(moose.check_moose_commands_enabled(
            moose.MOOSE_LS | moose.MOOSE_PUT))

    def test_put_and_get_enabled(self):
        self.mock_run_cmd.return_value = [
            '    PUT commands enabled: true',
            '    GET commands enabled: true']
        self.assertTrue(moose.check_moose_commands_enabled(
            moose.MOOSE_PUT | moose.MOOSE_GET))

    def test_one_disabled_one_enabled(self):
        self.mock_run_cmd.return_value = [
            '    PUT commands enabled: true',
            '    GET commands enabled: false']
        self.assertFalse(moose.check_moose_commands_enabled(
            moose.MOOSE_PUT | moose.MOOSE_GET))

    def test_two_disabled(self):
        self.mock_run_cmd.return_value = [
            '    SELECT commands enabled: false',
            '    MDLS commands enabled: false']
        self.assertFalse(moose.check_moose_commands_enabled(
            moose.MOOSE_SELECT | moose.MOOSE_MDLS))


class TestGetLimits(unittest.TestCase):
    """ Test get_limits() """
    @mock.patch('afterburner.io.moose._run_moose_command')
    def test_normal_operation(self, mock_run_cmd):
        mock_run_cmd.return_value = [
            '    Query-file size-limit (byte): 4096',
            '    Default max. conversion-threads: 15',
            '    Default max. transfer-threads: 3',
            '    MDLS commands enabled: true',
            '    Multiple-put file-number limit: 10000',
            '    Multiple-put volume limit (MB): 5120000',
            '    Multiple-get file-number limit: 20000',
            '    Multiple-get volume limit (MB): 5120000',
            '    Multiple-get tape-number limit: 6',
            '    Cost of storing one Terabyte for one year (GBP): 45.0']

        expected = {
            moose.MOOSE_PUT_MAX_FILES: 10000,
            moose.MOOSE_PUT_MAX_VOLUME: 5120000,
            moose.MOOSE_GET_MAX_FILES: 20000,
            moose.MOOSE_GET_MAX_VOLUME: 5120000,
            moose.MOOSE_GET_MAX_TAPES: 6,
            moose.MOOSE_MAX_QUERY_FILE_SIZE: 4096,
            moose.MOOSE_MAX_CONV_THREADS: 15,
            moose.MOOSE_MAX_XFER_THREADS: 3}

        actual = moose.get_moose_limits()
        self.assertEqual(actual, expected)

    @mock.patch('afterburner.io.moose._run_moose_command')
    def test_non_numeric_value(self, mock_run_cmd):
        mock_run_cmd.return_value = [
            '    Multiple-put file-number limit: 42',
            '    Multiple-put volume limit (MB): apple']

        expected = {moose.MOOSE_PUT_MAX_FILES: 42}

        actual = moose.get_moose_limits()
        self.assertEqual(actual, expected)

    @mock.patch('afterburner.io.moose._run_moose_command')
    @mock.patch('afterburner.io.moose.logger')
    def test_moose_not_available(self, mock_logger, mock_run_cmd):
        mock_run_cmd.side_effect = afterburner.exceptions.MooseUnavailableError

        self.assertRaises(afterburner.exceptions.MooseUnavailableError,
            moose.get_moose_limits)

        mock_logger.error.assert_called_with('MOOSE is currently unavailable.')


class TestListFiles(unittest.TestCase):
    """ Test list_files() """
    @mock.patch('afterburner.io.moose._run_moose_command')
    def test_list_files(self, mock_func):
        mock_func.return_value = ['moose:/fake/uri/one',
            'moose:/fake/uri/two']
        expected_cmd = 'moo ls moose:/fake/uri'
        expected_op = ['moose:/fake/uri/one',
            'moose:/fake/uri/two']

        files = moose.list_files('moose:/fake/uri')

        mock_func.assert_called_with(expected_cmd)
        self.assertEqual(expected_op, files)


class TestListStructFiles(unittest.TestCase):
    """ Test list_struct_files() """
    def setUp(self):
        patch = mock.patch('afterburner.io.moose._run_moose_command')
        self.mock_run_cmd = patch.start()
        self.addCleanup(patch.stop)

    def test_list_crum_data(self):
        self.mock_run_cmd.return_value = [
            'moose:/crum/mi-ab123/apa.pp/ab123a.pa1900jan.pp',
            'moose:/crum/mi-ab123/apa.pp/ab123a.pa1900feb.pp']
        expected = 'moo ls --size moose:/crum/mi-ab123/apa.pp'

        moose.list_struct_files('mi-ab123', 'apa.pp', sort='size')

        self.mock_run_cmd.assert_called_with(expected)

    def test_list_other_data_classes(self):
        self.mock_run_cmd.return_value = [
            'moose:/fake/uri/one/file.txt',
            'moose:/fake/uri/one/file.nc']
        expected_op = ['moose:/fake/uri/one/file.txt',
                       'moose:/fake/uri/one/file.nc']
        expected = 'moo ls --time moose:/fake/uri/one'

        files = moose.list_struct_files('uri', 'one', data_class='fake', sort='time')

        self.mock_run_cmd.assert_called_with(expected)
        self.assertEqual(expected_op, files)


class TestMetadataListStructFiles(unittest.TestCase):
    """ Test metadata_list_struct() """
    def setUp(self):
        patch = mock.patch('afterburner.io.moose._run_moose_command')
        self.mock_run_cmd = patch.start()
        self.addCleanup(patch.stop)
        self.mock_run_cmd.return_value = [
            'moose:/crum/mi-ab123/apa.pp/ab123a.pa1900jan.pp',
            '    pp_file: ab123a.pa1900jan.pp',
            '        atom 360',
            '        atom 361',
            '',
            'moose:/crum/mi-ab123/apa.pp/ab123a.pa1900feb.pp',
            '    pp_file: ab123a.pa1900feb.pp',
            '        atom 178']

        patch = mock.patch('afterburner.io.moose._write_query_file')
        self.mock_file = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.io.moose._delete_file')
        self.mock_delete = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.io.moose.tempfile.mkstemp')
        self.mock_tempfile = patch.start()
        self.addCleanup(patch.stop)
        self.mock_tempfile.return_value = (5, './tmpabc123_query.txt')

        patch = mock.patch('afterburner.io.moose.logger')
        self.mock_logger = patch.start()
        self.addCleanup(patch.stop)

        self.expected_op = [
            'moose:/crum/mi-ab123/apa.pp/ab123a.pa1900jan.pp',
            'moose:/crum/mi-ab123/apa.pp/ab123a.pa1900feb.pp']

    def test_no_parameters_raises_exception(self):
        self.assertRaises(ValueError, moose.metadata_list_struct, 'any', 'any')
        self.mock_logger.error.assert_called_with('A value must be specified '
            'for at least one of: files, stashcodes or time_range.')

    def test_default_input_and_query_file_deleted(self):
        file_list = moose.metadata_list_struct('mi-ai069', 'apa.pp',
            files=['file.pp'])

        self.assertEqual(self.expected_op, file_list)
        self.mock_file.assert_called_with('./tmpabc123_query.txt',
            files=['file.pp'], stashcodes=None, time_range=None,
            attributes=[''], comment='moose:/crum/mi-ai069/apa.pp')
        self.mock_delete.assert_called_with('./tmpabc123_query.txt')

    def test_input_specified_and_query_file_kept(self):
        file_list = moose.metadata_list_struct('mi-ai069', 'apa.pp',
            stashcodes=['m01s00i024'], keep_query_file=True)

        self.assertEqual(self.expected_op, file_list)
        self.mock_file.assert_called_with('./tmpabc123_query.txt', files=None,
            stashcodes=['m01s00i024'], time_range=None, attributes=[''],
            comment='moose:/crum/mi-ai069/apa.pp')
        self.assertEqual(self.mock_delete.call_count, 0)

    def test_with_sort_option(self):
        files = moose.metadata_list_struct('mi-ai069', 'apa.pp', files=['file.pp'],
            sort='T2')
        expected = 'moo mdls --sort=T2 ./tmpabc123_query.txt moose:/crum/mi-ai069/apa.pp'
        self.mock_run_cmd.assert_called_with(expected)
        files = moose.metadata_list_struct('mi-ai069', 'apa.pp', files=['file.pp'],
            sort='pp_file')
        expected = 'moo mdls --sort=pp_file ./tmpabc123_query.txt moose:/crum/mi-ai069/apa.pp'
        self.mock_run_cmd.assert_called_with(expected)
        files = moose.metadata_list_struct('mi-ai069', 'apa.pp', files=['file.pp'],
            sort='')
        expected = 'moo mdls ./tmpabc123_query.txt moose:/crum/mi-ai069/apa.pp'
        self.mock_run_cmd.assert_called_with(expected)


class TestQueryTimeExtent(unittest.TestCase):
    """Test the query_time_extent() function."""

    def setUp(self):
        patch = mock.patch('afterburner.io.moose._run_moose_command')
        self.mock_run_cmd = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.io.moose._write_query_file')
        self.mock_qfile = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.io.moose.tempfile.mkstemp')
        self.mock_tempfile = patch.start()
        self.addCleanup(patch.stop)
        self.mock_tempfile.return_value = (0, './tmp_query.txt')

    def test_with_defaults(self):
        self.mock_run_cmd.return_value = [
            'file_end_date:',
            '  1971/12/01 00:00:00',
            '  1972/12/01 00:00:00',
            'file_start_date:',
            '  1970/12/01 00:00:00',
            '  1971/12/01 00:00:00',
        ]
        times = moose.query_time_extent('expid', 'apy.pp')
        expected_cmd = 'moo mdls --summary ./tmp_query.txt moose:/crum/expid/apy.pp'
        expected_op = ('1970-12-01T00:00:00', '1972-12-01T00:00:00')
        self.mock_run_cmd.assert_called_with(expected_cmd)
        self.assertEqual(expected_op, times)

    def test_with_ens_class(self):
        self.mock_run_cmd.return_value = [
            'file_end_date:',
            '  1971/12/01 00:00:00',
            '  1972/12/01 00:00:00',
            'file_start_date:',
            '  1970/12/01 00:00:00',
            '  1971/12/01 00:00:00',
        ]
        times = moose.query_time_extent('expid', 'apy.pp', data_class='ens')
        expected_cmd = 'moo mdls --summary ./tmp_query.txt moose:/ens/expid/apy.pp'
        expected_op = ('1970-12-01T00:00:00', '1972-12-01T00:00:00')
        self.mock_run_cmd.assert_called_with(expected_cmd)
        self.assertEqual(expected_op, times)

    def test_with_stashcode(self):
        self.mock_run_cmd.return_value = [
            'atom 1:',
            '  t1: 1970/12/01 00:00:00',
            'atom 2:',
            '  t1: 1971/12/01 00:00:00',
        ]
        times = moose.query_time_extent('expid', 'apy.pp', stashcodes='m01s00i024')
        expected_cmd = 'moo mdls --sort=T1 ./tmp_query.txt moose:/crum/expid/apy.pp'
        expected_op = ('1970-12-01T00:00:00', '1971-12-01T00:00:00')
        self.mock_run_cmd.assert_called_with(expected_cmd)
        self.assertEqual(expected_op, times)

    def test_with_t2_attribute(self):
        self.mock_run_cmd.return_value = [
            'atom 1:',
            '  t2: 1970/12/01 00:00:00',
            'atom 2:',
            '  t2: 1980/12/01 00:00:00',
        ]
        times = moose.query_time_extent('expid', 'apy.pp', stashcodes='m01s00i024',
            time_attribute='T2')
        expected_cmd = 'moo mdls --sort=T2 ./tmp_query.txt moose:/crum/expid/apy.pp'
        expected_op = ('1970-12-01T00:00:00', '1980-12-01T00:00:00')
        self.mock_run_cmd.assert_called_with(expected_cmd)
        self.assertEqual(expected_op, times)


class TestRetrieveFiles(unittest.TestCase):
    """ Test retrieve_files() """
    def setUp(self):
        patch = mock.patch('afterburner.io.moose._run_moose_command')
        self.mock_run_cmd = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.io.moose._write_query_file')
        self.mock_file = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.io.moose._delete_file')
        self.mock_delete = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.io.moose.tempfile.mkstemp')
        self.mock_tempfile = patch.start()
        self.addCleanup(patch.stop)
        self.mock_tempfile.return_value = (5, './tmpabc123_query.txt')

    def test_simplest_retrieve(self):
        """ test the simplest retrieve with no keyword arguments """
        expected = 'moo get moose:/crum/mi-ab123/apa.pp /some/dir'

        moose.retrieve_files('/some/dir', 'moose:/crum/mi-ab123/apa.pp')

        self.mock_run_cmd.assert_called_with(expected)
        self.assertEqual(self.mock_delete.call_count, 0)

    def test_stash_codes_specified(self):
        """ test retrieval with STASH codes specified """
        expected = ('moo select ./tmpabc123_query.txt '
            'moose:/crum/mi-ab123/apa.pp .')

        moose.retrieve_files('.', 'moose:/crum/mi-ab123/apa.pp',
            stashcodes=['m01s00i024'])

        self.mock_file.assert_called_with('./tmpabc123_query.txt', files=None,
            stashcodes=['m01s00i024'], time_range=None,
            comment='moose:/crum/mi-ab123/apa.pp')
        self.mock_run_cmd.assert_called_with(expected)
        self.mock_delete.assert_called_with('./tmpabc123_query.txt')

    def test_stash_codes_and_file_specified(self):
        """ test retrieval with STASH codes and files specified """
        expected = ('moo select ./tmpabc123_query.txt '
            'moose:/crum/mi-ab123/apa.pp .')

        moose.retrieve_files('.', 'moose:/crum/mi-ab123/apa.pp',
            stashcodes=['m01s00i024', 'm01s05i216'],
            files=['file_one.pp', 'file_two.pp'])

        self.mock_file.assert_called_with('./tmpabc123_query.txt',
            files=['file_one.pp', 'file_two.pp'],
            stashcodes=['m01s00i024', 'm01s05i216'], time_range=None,
            comment='moose:/crum/mi-ab123/apa.pp')
        self.mock_run_cmd.assert_called_with(expected)

    def test_time_range_and_stash_codes_specified(self):
        """ test retrieval with a time range and STASH codes specified """
        d1 = '1980/07/31'
        d2 = '2233/03/22'
        expected = ('moo select ./tmpabc123_query.txt '
            'moose:/crum/mi-ab123/apa.pp .')

        moose.retrieve_files('.', 'moose:/crum/mi-ab123/apa.pp',
            stashcodes=['m01s00i024', 'm01s05i216'], time_range=(d1, d2))

        self.mock_file.assert_called_with('./tmpabc123_query.txt', files=None,
            stashcodes=['m01s00i024', 'm01s05i216'], time_range=(d1, d2),
            comment='moose:/crum/mi-ab123/apa.pp')
        self.mock_run_cmd.assert_called_with(expected)

    def test_with_force_and_insert(self):
        """ test retrieval with force and insert """
        expected = 'moo get -f -i moose:/crum/mi-ab123/apa.pp .'

        moose.retrieve_files('.', 'moose:/crum/mi-ab123/apa.pp',
            overwrite=True, fill_gaps=True)

        self.mock_run_cmd.assert_called_with(expected)

    def test_record_level_with_force_and_insert(self):
        """ test record level retrieval with force and insert """
        expected = ('moo select -f -i ./tmpabc123_query.txt '
            'moose:/crum/mi-ab123/apa.pp .')

        moose.retrieve_files('.', 'moose:/crum/mi-ab123/apa.pp',
            stashcodes=['m01s08i223'], overwrite=True, fill_gaps=True)

        self.mock_run_cmd.assert_called_with(expected)

    def test_with_just_insert(self):
        """ test retrieval with insert """
        expected = 'moo get -i moose:/crum/mi-ab123/apa.pp .'

        moose.retrieve_files('.', 'moose:/crum/mi-ab123/apa.pp',
            overwrite=False, fill_gaps=True)

        self.mock_run_cmd.assert_called_with(expected)

    def test_record_level_with_force_and_query_file_deleted(self):
        """ test record level retrieval with force and that
        query file is deleted """
        expected = ('moo select -f ./tmpabc123_query.txt '
            'moose:/crum/mi-ab123/apa.pp .')

        moose.retrieve_files('.', 'moose:/crum/mi-ab123/apa.pp',
            stashcodes=['m01s08i223'], overwrite=True)

        self.mock_run_cmd.assert_called_with(expected)
        self.mock_delete.assert_called_with('./tmpabc123_query.txt')

    def test_query_file_retained(self):
        """ test that query file is kept when requested """
        expected = ('moo select ./tmpabc123_query.txt '
            'moose:/crum/mi-ab123/apa.pp .')

        moose.retrieve_files('.', 'moose:/crum/mi-ab123/apa.pp',
            stashcodes=['m01s08i223'], keep_query_file=True)

        self.mock_run_cmd.assert_called_with(expected)
        self.assertEqual(self.mock_delete.call_count, 0)


class TestRetrieveNcFiles(unittest.TestCase):
    """ Test retrieve_nc_files() """
    def setUp(self):
        patch = mock.patch('afterburner.io.moose._run_moose_command')
        self.mock_run_cmd = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.io.moose._write_filter_file')
        self.mock_file = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.io.moose._delete_file')
        self.mock_delete = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.io.moose.tempfile.mkstemp')
        self.mock_tempfile = patch.start()
        self.addCleanup(patch.stop)
        self.mock_tempfile.return_value = (5, './tmpabc123_filter.txt')

        # the default ncks_opts that retrieve_nc_files() uses
        self.ncks_options = '-a'

    def test_get_whole_collection(self):
        expected = 'moo get moose:/crum/mi-ab123/onm.nc.file/* /some/dir'

        moose.retrieve_nc_files('/some/dir', 'moose:/crum/mi-ab123/onm.nc.file')

        self.mock_run_cmd.assert_called_with(expected)
        self.assertEqual(self.mock_delete.call_count, 0)

    def test_get_whole_collection_and_overwrite(self):
        expected = 'moo get -f moose:/crum/mi-ab123/onm.nc.file/* /some/dir'

        moose.retrieve_nc_files('/some/dir', 'moose:/crum/mi-ab123/onm.nc.file',
            overwrite=True)

        self.mock_run_cmd.assert_called_with(expected)
        self.assertEqual(self.mock_delete.call_count, 0)

    def test_get_whole_collection_and_fill_gaps(self):
        expected = 'moo get -i moose:/crum/mi-ab123/onm.nc.file/* /some/dir'

        moose.retrieve_nc_files('/some/dir', 'moose:/crum/mi-ab123/onm.nc.file',
            fill_gaps=True)

        self.mock_run_cmd.assert_called_with(expected)
        self.assertEqual(self.mock_delete.call_count, 0)

    def test_get_whole_collection_fill_gaps_and_overwrite(self):
        expected = 'moo get -f -i moose:/crum/mi-ab123/onm.nc.file/* /some/dir'

        moose.retrieve_nc_files('/some/dir', 'moose:/crum/mi-ab123/onm.nc.file',
            overwrite=True, fill_gaps=True)

        self.mock_run_cmd.assert_called_with(expected)
        self.assertEqual(self.mock_delete.call_count, 0)

    def test_get_whole_file(self):
        expected = 'moo get moose:/crum/mi-ab123/onm.nc.file/file1.nc /some/dir'

        moose.retrieve_nc_files('/some/dir', 'moose:/crum/mi-ab123/onm.nc.file',
            files=['file1.nc'])

        self.mock_run_cmd.assert_called_with(expected)
        self.assertEqual(self.mock_delete.call_count, 0)

    def test_get_whole_files(self):
        expected = ('moo get moose:/crum/mi-ab123/onm.nc.file/file1.nc '
                   'moose:/crum/mi-ab123/onm.nc.file/file2.nc /some/dir')

        moose.retrieve_nc_files('/some/dir', 'moose:/crum/mi-ab123/onm.nc.file',
            files=['file1.nc', 'file2.nc'])

        self.mock_run_cmd.assert_called_with(expected)
        self.assertEqual(self.mock_delete.call_count, 0)

    def test_filter_varname(self):
        expected = ('moo filter ./tmpabc123_filter.txt '
            'moose:/crum/mi-ab123/onm.nc.file/* /some/dir')

        moose.retrieve_nc_files('/some/dir', 'moose:/crum/mi-ab123/onm.nc.file',
            var_names=['var1'])

        self.mock_run_cmd.assert_called_with(expected)
        self.mock_file.assert_called_with('./tmpabc123_filter.txt', ['var1'],
            ncks_opts=self.ncks_options)
        self.mock_delete.assert_called_with('./tmpabc123_filter.txt')

    def test_filter_varnames(self):
        expected = ('moo filter ./tmpabc123_filter.txt '
            'moose:/crum/mi-ab123/onm.nc.file/* /some/dir')

        moose.retrieve_nc_files('/some/dir', 'moose:/crum/mi-ab123/onm.nc.file',
            var_names=['var1', 'var2'])

        self.mock_run_cmd.assert_called_with(expected)
        self.mock_file.assert_called_with('./tmpabc123_filter.txt',
            ['var1', 'var2'], ncks_opts=self.ncks_options)
        self.mock_delete.assert_called_once_with('./tmpabc123_filter.txt')

    def test_filter_varnames_tuples_also_accepted(self):
        expected = ('moo filter ./tmpabc123_filter.txt '
            'moose:/crum/mi-ab123/onm.nc.file/* /some/dir')

        moose.retrieve_nc_files('/some/dir', 'moose:/crum/mi-ab123/onm.nc.file',
            var_names=('var1', 'var2'))

        self.mock_run_cmd.assert_called_with(expected)
        self.mock_file.assert_called_with('./tmpabc123_filter.txt',
            ('var1', 'var2'), ncks_opts=self.ncks_options)
        self.mock_delete.assert_called_once_with('./tmpabc123_filter.txt')

    def test_filter_query_file_preserved(self):
        expected = ('moo filter ./tmpabc123_filter.txt '
            'moose:/crum/mi-ab123/onm.nc.file/* /some/dir')

        moose.retrieve_nc_files('/some/dir', 'moose:/crum/mi-ab123/onm.nc.file',
            var_names=['var1', 'var2'], keep_filter_file=True)

        self.mock_run_cmd.assert_called_with(expected)
        self.mock_file.assert_called_with('./tmpabc123_filter.txt',
            ['var1', 'var2'], ncks_opts=self.ncks_options)
        self.assertEqual(self.mock_delete.call_count, 0)


class TestRetrieveStructFiles(unittest.TestCase):
    """ Test retrieve_struct_files() """
    def setUp(self):
        patch = mock.patch('afterburner.io.moose.retrieve_files')
        self.mock_retrieve = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.io.moose._delete_file')
        self.mock_delete = patch.start()
        self.addCleanup(patch.stop)

    def test_basic_retrieval(self):
        """ test basic retrieval """
        expected_uri = 'moose:/crum/mi-ab123/apa.pp'

        moose.retrieve_struct_files('/some/dir', 'mi-ab123', 'apa.pp')

        self.mock_retrieve.assert_called_with('/some/dir', expected_uri,
            files=None, stashcodes=None, time_range=None, overwrite=False,
            fill_gaps=False, keep_query_file=False)

    def test_record_level_retrieval_with_stash_codes_specified(self):
        """ test record level retrieval with STASH codes specified """
        expected_uri = 'moose:/ens/mi-ae123/ens19/apa.pp'

        moose.retrieve_struct_files('.', 'mi-ae123', 'ens19/apa.pp',
            data_class='ens', stashcodes=['m01s00i024', 'm01s05i216'],
            files=['file_one.pp', 'file_two.pp'], overwrite=True)

        self.mock_retrieve.assert_called_with('.', expected_uri,
            files=['file_one.pp', 'file_two.pp'],
            stashcodes=['m01s00i024', 'm01s05i216'], time_range=None,
            overwrite=True, fill_gaps=False, keep_query_file=False)

    def test_with_stash_codes_and_time_specified(self):
        """ test record level retrieval with STASH codes and
        time range specified """
        d1 = '1980/07/31'
        d2 = '2233/03/22'
        expected_uri = 'moose:/crum/mi-ab123/apa.pp'

        moose.retrieve_struct_files('.', 'mi-ab123', 'apa.pp',
            stashcodes=['m01s00i024', 'm01s05i216'], time_range=(d1, d2),
            overwrite=True, fill_gaps=True)

        self.mock_retrieve.assert_called_with('.', expected_uri, files=None,
            stashcodes=['m01s00i024', 'm01s05i216'],
            time_range=('1980/07/31', '2233/03/22'), overwrite=True,
            fill_gaps=True, keep_query_file=False)


class TestPutFiles(unittest.TestCase):
    """ Test put_files() """
    def setUp(self):
        patch = mock.patch('afterburner.io.moose._run_moose_command')
        self.mock_run_cmd = patch.start()
        self.addCleanup(patch.stop)

        # logger is mocked to prevent messages being output to stderr
        patch = mock.patch('afterburner.io.moose.logger')
        self.mock_logger = patch.start()
        self.addCleanup(patch.stop)

    def test_list_not_supplied(self):
        self.assertRaises(ValueError, moose.put_files, '/some/dir',
            'file_one.pp', 'moose:/crum/mi-ab123/apa.pp')

    def test_simplest_put(self):
        moose.put_files('/some/dir', ['file_one.pp'],
            'moose:/crum/mi-ab123/apa.pp')
        self.mock_run_cmd.assert_called_with('moo put /some/dir/file_one.pp '
            'moose:/crum/mi-ab123/apa.pp')

    def test_put_two_files(self):
        moose.put_files('/some/dir', ['file_one.pp', 'file_two.nc'],
            'moose:/crum/mi-ab123/apa.pp')
        self.mock_run_cmd.assert_called_with('moo put /some/dir/file_one.pp '
            '/some/dir/file_two.nc moose:/crum/mi-ab123/apa.pp')

    def test_overwrite_option(self):
        moose.put_files('/', ['file'], 'uri', overwrite=True)
        self.mock_run_cmd.assert_called_with('moo put -f /file uri')

    def test_overwrite_if_different_option(self):
        moose.put_files('/', ['file'], 'uri', overwrite_if_different=True)
        self.mock_run_cmd.assert_called_with('moo put -F /file uri')

    def test_overwrite_has_precedence(self):
        moose.put_files('/', ['file'], 'uri', overwrite=True,
                        overwrite_if_different=True)
        self.mock_run_cmd.assert_called_with('moo put -f /file uri')


class TestPutStructFiles(unittest.TestCase):
    """ Test put_struct_files() """
    def setUp(self):
        patch = mock.patch('afterburner.io.moose.put_files')
        self.mock_put = patch.start()
        self.addCleanup(patch.stop)

    def test_simplest_uri_formation(self):
        moose.put_struct_files('/some/dir', ['one.pp'], 'mi-ab123', 'apa.pp')
        self.mock_put.assert_called_with('/some/dir', ['one.pp'],
            'moose:/crum/mi-ab123/apa.pp', overwrite=False,
            overwrite_if_different=False)

    def test_different_class(self):
        moose.put_struct_files('/some/dir', ['one.pp'], 'mi-ab123', 'apa.pp',
            data_class='ens')
        self.mock_put.assert_called_with('/some/dir', ['one.pp'],
            'moose:/ens/mi-ab123/apa.pp', overwrite=False,
            overwrite_if_different=False)

    def test_overwrite_passed_through_correctly(self):
        moose.put_struct_files('/some/dir', ['one.pp'], 'mi-ab123', 'apa.pp',
            overwrite=True)
        self.mock_put.assert_called_with('/some/dir', ['one.pp'],
            'moose:/crum/mi-ab123/apa.pp', overwrite=True,
            overwrite_if_different=False)

    def test_overwrite_if_different_passed_through_correctly(self):
        moose.put_struct_files('/some/dir', ['one.pp'], 'mi-ab123', 'apa.pp',
            overwrite_if_different=True)
        self.mock_put.assert_called_with('/some/dir', ['one.pp'],
            'moose:/crum/mi-ab123/apa.pp', overwrite=False,
            overwrite_if_different=True)


class TestWriteQueryFile(unittest.TestCase):
    """ Test _write_query_file() """
    def setUp(self):
        # use StringIO to wrap around the builtin open() function so that the
        # writing of a query file can be simulated in memory without anything
        # being written to disk
        self.io = StringIO()
        io_mock = mock.MagicMock(wraps=self.io)
        io_mock.close = mock.Mock()
        patch = mock.patch(builtin_open_func)
        self.mock_file = patch.start()
        self.mock_file.return_value = io_mock
        self.addCleanup(patch.stop)

    def test_single_stash_code(self):
        """ test a single STASH code """
        stash = ['m01s00i024']
        files = None
        expected = (
            'begin\n' +
            '    stash=24\n' +
            'end\n')

        moose._write_query_file('filename.txt', files=files, stashcodes=stash)

        self.assertEqual(expected, self.io.getvalue())

    def test_multiple_stash_codes(self):
        """ test multiple STASH codes """
        stash = ['m01s00i024', 'm01s05i216']
        expected = (
            'begin\n' +
            '    stash=(24,5216)\n' +
            'end\n')

        moose._write_query_file('filename.txt', stashcodes=stash)

        self.assertEqual(expected, self.io.getvalue())

    def test_stash_code_and_filename(self):
        """ test STASH code and a file """
        stash = ['m01s00i024']
        files = ['moose:/crum/mi-ab123/apa.pp/file_one.pp']
        expected = (
            'begin\n' +
            '    stash=24\n' +
            '    pp_file="file_one.pp"\n' +
            'end\n')

        moose._write_query_file('filename.txt', files=files, stashcodes=stash)

        self.assertEqual(expected, self.io.getvalue())

    def test_multiple_filenames(self):
        """ test multiple files """
        files = ['moose:/crum/mi-ab123/apa.pp/file_one.pp',
            'moose:/crum/mi-ab123/apa.pp/file_two.pp']
        expected = (
            'begin\n' +
            '    pp_file=("file_one.pp","file_two.pp")\n' +
            'end\n')

        moose._write_query_file('filename.txt', files=files)

        self.assertEqual(expected, self.io.getvalue())

    def test_repeated_unsorted_stash_codes(self):
        """ test repeated STASH codes in non-numeric order """
        stash = ['m01s05i216', 'm01s00i024', 'm01s00i024']
        files = None
        expected = (
            'begin\n' +
            '    stash=(24,5216)\n' +
            'end\n')

        moose._write_query_file('filename.txt', files=files, stashcodes=stash)

        self.assertEqual(expected, self.io.getvalue())

    def test_repeated_filenames(self):
        """ test repeated file names """
        files = [
            'moose:/crum/mi-ab123/apa.pp/file_one.pp',
            'moose:/crum/mi-ab123/apa.pp/file_two.pp',
            'moose:/crum/mi-ab123/apa.pp/file_one.pp']
        expected = (
            'begin\n' +
            '    pp_file=("file_one.pp","file_two.pp")\n' +
            'end\n')

        moose._write_query_file('filename.txt', files=files)

        self.assertEqual(expected, self.io.getvalue())

    def test_stash_codes_and_time_range(self):
        """ test STASH codes and a time range """
        d1 = '1978-07-19'
        d2 = '2016-02-29'
        stash = ['m01s05i216', 'm01s00i024']
        expected = (
            'begin\n' +
            '    stash=(24,5216)\n' +
            '    T1>={1978/07/19}\n' +
            '    T1<{2016/02/29}\n' +
            'end\n')

        moose._write_query_file('filename.txt', time_range=(d1, d2),
            stashcodes=stash)

        self.assertEqual(expected, self.io.getvalue())

    def test_single_attribute(self):
        """ test a single attribute """
        stash = ['m01s00i024']
        attributes = ['pp_file']
        expected = (
            'begin\n' +
            '    stash=24\n' +
            'end\n' +
            'begin_attributes\n' +
            'pp_file\n' +
            'end_attributes\n')

        moose._write_query_file('filename.txt', stashcodes=stash,
            attributes=attributes)

        self.assertEqual(expected, self.io.getvalue())

    def test_multiple_attributes(self):
        """ test multiple attributes """
        stash = ['m01s00i024']
        attributes = ['t2', 't1']
        expected = (
            'begin\n' +
            '    stash=24\n' +
            'end\n' +
            'begin_attributes\n' +
            't2\n' +
            't1\n' +
            'end_attributes\n')

        moose._write_query_file('filename.txt', stashcodes=stash,
            attributes=attributes)

        self.assertEqual(expected, self.io.getvalue())

    def test_comment_string(self):
        """ test the comment string """
        stash = ['m01s00i024']
        files = None
        expected = (
            '# Meaningful comment\n' +
            'begin\n' +
            '    stash=24\n' +
            'end\n')

        moose._write_query_file('filename.txt', files=files, stashcodes=stash,
            comment='Meaningful comment')

        self.assertEqual(expected, self.io.getvalue())


class TestWriteQueryFileExceptionHandling(unittest.TestCase):
    """ Tests _write_query_file()'s handling of exceptions """
    @mock.patch(builtin_open_func)
    @mock.patch('afterburner.io.moose.logger')
    def test_exception_handling(self, mock_logger, mock_open):
        mock_open.side_effect = IOError()

        self.assertRaises(afterburner.exceptions.TempFileError,
            moose._write_query_file, 'filename.txt')

        mock_logger.error.assert_called_with('Unable to create temporary file '
            'filename.txt\n')


class TestWriteFilterFile(unittest.TestCase):
    """ Test _write_filter_file() """
    def setUp(self):
        # use StringIO to wrap around the builtin open() function so that the
        # writing of a query file can be simulated in memory without anything
        # being written to disk
        self.io = StringIO()
        io_mock = mock.MagicMock(wraps=self.io)
        io_mock.close = mock.Mock()
        patch = mock.patch(builtin_open_func)
        self.mock_file = patch.start()
        self.mock_file.return_value = io_mock
        self.addCleanup(patch.stop)

    def test_ncks_opts(self):
        """ test a single optional parameter to ncks """
        ncks_options = '-a'

        moose._write_filter_file('filename.txt', ncks_opts=ncks_options)

        self.assertEqual(ncks_options + '\n', self.io.getvalue())

    def test_single_integer_hyperslab(self):
        """ test a single hyperslab with integer bounds """
        hyperslab = [('coordinate', 1, 2)]
        expected = '-d coordinate,1,2\n'

        moose._write_filter_file('filename.txt', dims_and_coords=hyperslab)

        self.assertEqual(expected, self.io.getvalue())

    def test_single_float_hyperslab(self):
        """ test a single hyperslab with floating point bounds """
        hyperslab = [('coordinate', 1., 2.)]
        expected = '-d coordinate,1.0,2.0\n'

        moose._write_filter_file('filename.txt', dims_and_coords=hyperslab)

        self.assertEqual(expected, self.io.getvalue())

    def test_multiple_hyperslabs(self):
        """ test a multiple hyperslab with float and integer bounds """
        hyperslabs = [('coordinate', 1., 2.), ('dimension', 1, 2)]
        expected = (
            '-d coordinate,1.0,2.0\n'
            '-d dimension,1,2\n')

        moose._write_filter_file('filename.txt', dims_and_coords=hyperslabs)

        self.assertEqual(expected, self.io.getvalue())

    def test_single_variable(self):
        """ test a single variable """
        var_names = ['myvar']
        expected = '-v myvar\n'

        moose._write_filter_file('filename.txt', var_names=var_names)

        self.assertEqual(expected, self.io.getvalue())

    def test_multiple_variables(self):
        """ test multiple variables """
        var_names = ['myvar', 'yourvar']
        expected = '-v myvar,yourvar\n'

        moose._write_filter_file('filename.txt', var_names=var_names)

        self.assertEqual(expected, self.io.getvalue())

    def test_all_parameters(self):
        """ test all parameters together """
        ncks_options = '-a'
        hyperslabs = [('coordinate', 1., 2.), ('dimension', 1, 2)]
        var_names = ['myvar', 'yourvar']
        expected = (
            '-a\n'
            '-d coordinate,1.0,2.0\n'
            '-d dimension,1,2\n'
            '-v myvar,yourvar\n')

        moose._write_filter_file('filename.txt', var_names=var_names,
            dims_and_coords=hyperslabs, ncks_opts=ncks_options)

        self.assertEqual(expected, self.io.getvalue())


class TestWriteFilterFileExceptionHandling(unittest.TestCase):
    """ Tests _write_filter_file()'s handling of exceptions """
    @mock.patch(builtin_open_func)
    @mock.patch('afterburner.io.moose.logger')
    def test_exception_handling(self, mock_logger, mock_open):
        mock_open.side_effect = IOError()

        self.assertRaises(afterburner.exceptions.TempFileError,
            moose._write_filter_file, 'filename.txt')

        mock_logger.error.assert_called_with('Unable to open file filename.txt:\n')


class TestPdtFromDateTuple(unittest.TestCase):
    """ Test _pdt_from_date_tuple() """
    def setUp(self):
        # logging is mocked to prevent output to STDOUT or STDERR
        patch = mock.patch('afterburner.io.moose.logger')
        self.mock_logger = patch.start()
        self.addCleanup(patch.stop)

        self.d1 = '2015-12-25'
        self.pdt1 = PartialDateTime(year=2015, month=12, day=25)
        self.d2 = '1982-08-23T11:17:12'
        self.pdt2 = PartialDateTime(year=1982, month=8, day=23,
            hour=11, minute=17, second=12)

    def test_exception_raise_for_wrong_input_combination(self):
        """ test exception raised for all wrong combinations of input """
        self.assertRaises(ValueError, moose._pdt_from_date_tuple, self.d1)
        self.assertRaises(ValueError, moose._pdt_from_date_tuple, (self.d1,))
        self.assertRaises(ValueError, moose._pdt_from_date_tuple,
                          (self.d1, self.d1, self.d2))
        self.assertRaises(ValueError, moose._pdt_from_date_tuple, (self.d1, 1))
        self.assertRaises(ValueError, moose._pdt_from_date_tuple, (1, 1))
        self.assertRaises(ValueError, moose._pdt_from_date_tuple, (1., 1.))

    def test_pdts_returned(self):
        pdts = moose._pdt_from_date_tuple((self.d1, self.d2))
        expected = (self.pdt1, self.pdt2)
        self.assertEqual(pdts, expected)


class TestMooseDataStringFromPdt(unittest.TestCase):
    """ Test _moose_date_string_from_pdt() """
    @mock.patch('afterburner.io.moose.logger')
    def test_missing_date_components(self, mock_logger):
        # mock logger to prevent messages being output
        pdt = PartialDateTime(year=1, month=1)
        self.assertRaises(ValueError, moose._moose_date_string_from_pdt, pdt)
        pdt = PartialDateTime(year=1, day=1)
        self.assertRaises(ValueError, moose._moose_date_string_from_pdt, pdt)
        pdt = PartialDateTime(month=1, day=1)
        self.assertRaises(ValueError, moose._moose_date_string_from_pdt, pdt)

    @mock.patch('afterburner.io.moose.logger')
    def test_zero_date_components(self, mock_logger):
        # mock logger to prevent messages being output
        pdt = PartialDateTime(year=1, month=1, day=0)
        self.assertRaises(ValueError, moose._moose_date_string_from_pdt, pdt)
        pdt = PartialDateTime(year=1, month=0, day=1)
        self.assertRaises(ValueError, moose._moose_date_string_from_pdt, pdt)
        pdt = PartialDateTime(year=0, month=1, day=1)
        self.assertRaises(ValueError, moose._moose_date_string_from_pdt, pdt)

    def test_date_only(self):
        pdt = PartialDateTime(year=1, month=1, day=1)
        expected = '0001/01/01'
        self.assertEqual(moose._moose_date_string_from_pdt(pdt), expected)

    def test_date_hour_minute(self):
        pdt = PartialDateTime(year=1, month=1, day=1, hour=0, minute=0)
        expected = '0001/01/01 00:00'
        self.assertEqual(moose._moose_date_string_from_pdt(pdt), expected)

    def test_date_hour_minute_second(self):
        pdt = PartialDateTime(year=1, month=1, day=1, hour=0, minute=0, second=0)
        expected = '0001/01/01 00:00:00'
        self.assertEqual(moose._moose_date_string_from_pdt(pdt), expected)


class TestRunMooseCommand(unittest.TestCase):
    """ Test _run_moose_command() """
    def setUp(self):
        # logging is mocked to prevent output to STDOUT or STDERR
        patch = mock.patch('afterburner.io.moose.logger')
        self.mock_logger = patch.start()
        self.addCleanup(patch.stop)

    def test_moose_error_2(self):
        """ test Moose error 2 """
        subprocess.check_output = mock.Mock(
            side_effect=subprocess.CalledProcessError(2, 'cmd'))
        self.assertRaises(afterburner.exceptions.MooseCommandError,
            moose._run_moose_command, 'moo ls moose:/crum/mi-ab123')

    def test_moose_error_3(self):
        """ test Moose error 3 """
        subprocess.check_output = mock.Mock(
            side_effect=subprocess.CalledProcessError(3, 'cmd'))
        self.assertRaises(afterburner.exceptions.MooseUnavailableError,
            moose._run_moose_command, 'moo ls moose:/crum/mi-ab123')

    def test_moose_error_5(self):
        """ test Moose error 5 """
        subprocess.check_output = mock.Mock(
            side_effect=subprocess.CalledProcessError(5, 'cmd'))
        self.assertRaises(afterburner.exceptions.MooseUnavailableError,
            moose._run_moose_command, 'moo ls moose:/crum/mi-ab123')

    def test_moose_error_17(self):
        """Test Moose error 17: all files exist."""
        subprocess.check_output = mock.Mock(side_effect=
            subprocess.CalledProcessError(17, 'cmd', output='all files exist'))
        output = moose._run_moose_command('moo get -i moose:/adhoc/users/jrluser')
        self.assertEqual(output, ['all files exist'])

    def test_return_values_handled_correctly(self):
        """ test that return values are handled correctly """
        patch = mock.patch('afterburner.io.moose.subprocess.check_output')
        mock_subprocess = patch.start()

        moo_cmd_return = b'moose:/some.file\nmoose:/other.file'
        mock_subprocess.return_value = moo_cmd_return

        expected = [u'moose:/some.file', u'moose:/other.file']

        actual = moose._run_moose_command('moo ls moose:/crum/mi-ab123')

        self.assertEqual(expected, actual)

        patch.stop()


class TestDeleteFile(unittest.TestCase):
    """ Test _delete_file() """
    def setUp(self):
        patch = mock.patch('afterburner.io.moose.os.remove')
        self.mock_rm = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('afterburner.io.moose.logger')
        self.mock_logger = patch.start()
        self.addCleanup(patch.stop)

    def test_os_remove_called_correctly(self):
        """ check that os.remove is being called correctly """
        moose._delete_file('/some/path_filename')
        self.mock_rm.assert_called_with('/some/path_filename')

    def test_exception_causes_warning_message(self):
        """ check that exceptions generate a warning message """
        self.mock_rm.side_effect = OSError()

        moose._delete_file('/some/path_filename')
        self.mock_logger.warning.assert_called_with('Unable to delete '
            'file: /some/path_filename\n')

if __name__ == '__main__':
    unittest.main()
