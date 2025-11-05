# (C) British Crown Copyright 2016, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
A module to provide a Python interface to the MOOSE command line tools. Only the
most commonly used subset of MOOSE functionality is currently supported.

.. warning:: The afterburner.io.moose module has been deprecated. Please use
   the :mod:`afterburner.io.moose2` module instead. The latter module provides
   equivalent functionality.
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)
from six.moves import (filter, input, map, range, zip)
from six import string_types

import os
import subprocess
import logging
import tempfile
import re
import iris
import afterburner.exceptions
from afterburner.utils.dateutils import pdt_from_date_string

logger = logging.getLogger(__name__)

# MOOSE system return codes
MOOSE_SYSTEM_OUTAGE = 3
MOOSE_TEMPORARILY_DISABLED = 5
MOOSE_ALL_FILES_EXIST = 17

#: Bit mask for checking that the ``moo ls`` command is enabled.
MOOSE_LS = 1

#: Bit mask for checking that the ``moo put`` command is enabled.
MOOSE_PUT = 2

#: Bit mask for checking that the ``moo get`` command is enabled.
MOOSE_GET = 4

#: Bit mask for checking that the ``moo select`` command is enabled.
MOOSE_SELECT = 8

#: Bit mask for checking that the ``moo mdls`` command is enabled.
MOOSE_MDLS = 16

#: Bit mask for checking that all MOOSE commands are enabled.
MOOSE_ALL = MOOSE_LS | MOOSE_PUT | MOOSE_GET | MOOSE_SELECT | MOOSE_MDLS

#: Symbolic constant for the maximum number of files that can be copied to MASS
#: in a single ``moo put`` command.
MOOSE_PUT_MAX_FILES = 'put_max_files'

#: Symbolic constant for the maximum volume of data in MiB that can be copied
#: to MASS in a single ``moo put`` command.
MOOSE_PUT_MAX_VOLUME = 'put_max_volume'

#: Symbolic constant for the maximum number of files that can be fetched from
#: MASS in a single ``moo get``, ``select`` or ``filter`` command.
MOOSE_GET_MAX_FILES = 'get_max_files'

#: Symbolic constant for the maximum volume of data in MiB that can be fetched
#: from MASS in a single ``moo get``, ``select`` or ``filter`` command.
MOOSE_GET_MAX_VOLUME = 'get_max_volume'

#: Symbolic constant for the maximum number of tapes that a single ``moo get``,
#: ``select`` or ``filter`` command's data can span across.
MOOSE_GET_MAX_TAPES = 'get_max_tapes'

#: Symbolic constant for the maximum size of query files in bytes.
MOOSE_MAX_QUERY_FILE_SIZE = 'max_query_file_size'

#: Symbolic constant for the maximum number of conversion threads.
MOOSE_MAX_CONV_THREADS = 'max_conv_threads'

#: Symbolic constant for the maximum number of transfer threads.
MOOSE_MAX_XFER_THREADS = 'max_xfer_threads'

# MiBytes to Bytes conversion factor.
MIBYTES_TO_BYTES = 1024 * 1024


class _ChunkSizeExceededError(Exception):
    """
    Raised when an attempt to split a list of items fails owing to a item being
    larger then the maximum chunk size/cost.
    """
    pass


def has_moose_support():
    """
    Check to see if the MOOSE command interface is supported by the current
    runtime environment. It should be noted that the presence of the MOOSE
    command interface does not imply that all of the underlying services are
    up and running. For example, one or more services may be unavailable as a
    result of scheduled down-time.

    :returns: True if the MOOSE interface is supported by the current runtime
        environment, else False.
    """
    try:
        subprocess.check_output(['moo', 'info'])
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def check_moose_commands_enabled(commands):
    """
    Check whether the specified MOOSE commands are currently enabled. The
    commands to check are specified as an OR'd combination of MOOSE_xxx values,
    e.g.::

        >> check_moose_commands_enabled(MOOSE_LS|MOOSE_SELECT)
        True

    :param int commands: The commands to check.
    :returns: True if the all of the specified MOOSE commands are currently
        enabled, otherwise False.
    :rtype: bool
    """
    # the default return value is False
    ret_val = False

    if commands & MOOSE_LS:
        # redirect stderr so that if commands are disabled then all output is
        # hidden from the user. _run_moose_command() isn't used as it would
        # result in additional output to the user.
        sp = subprocess.Popen(['moo', 'ls', 'moo:/'], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        status = sp.wait()
        if status != 0:
            return False
        else:
            ret_val = True

    if commands & (MOOSE_PUT | MOOSE_GET | MOOSE_SELECT | MOOSE_MDLS):
        try:
            status = _run_moose_command('moo si -v')
        except afterburner.exceptions.MooseUnavailableError:
            return False
        tests = {
            MOOSE_PUT: 'PUT commands enabled: true',
            MOOSE_GET: 'GET commands enabled: true',
            MOOSE_SELECT: 'SELECT commands enabled: true',
            MOOSE_MDLS: 'MDLS commands enabled: true'}
        for test in tests:
            if commands & test:
                if tests[test] not in ''.join(status):
                    return False
        ret_val = True

    return ret_val


def get_moose_limits():
    """
    Get the limits from the MOOSE client that the MOOSE system currently
    imposes on get and put commands. The available options are defined in this
    module's symbolic constants. The values are returned as integers in a
    dictionary, whose keys are the available options as strings. If the MOOSE
    client does not return a valid integer value for an option, then this
    option is omitted from the returned dictionary. An example usage is::

      >> get_moose_limits()[MOOSE_PUT_MAX_FILES]
      10000

    :returns: The limits stated above from the MOOSE client.
    :rtype: dict
    :raises afterburner.exceptions.MooseUnavailableError: If the MOOSE client
        isn't available.
    """
    limits = {}

    try:
        ret_val = _run_moose_command('moo si -v')
        ret_val = ''.join(ret_val)
    except afterburner.exceptions.MooseUnavailableError:
        msg = 'MOOSE is currently unavailable.'
        logger.error(msg)
        raise afterburner.exceptions.MooseUnavailableError(msg)

    patterns = {
        MOOSE_PUT_MAX_FILES: r'\s*Multiple-put file-number limit:\s*(\d+)',
        MOOSE_PUT_MAX_VOLUME: r'\s*Multiple-put volume limit \(MB\):\s*(\d+)',
        MOOSE_GET_MAX_FILES: r'\s*Multiple-get file-number limit:\s*(\d+)',
        MOOSE_GET_MAX_VOLUME: r'\s*Multiple-get volume limit \(MB\):\s*(\d+)',
        MOOSE_GET_MAX_TAPES: r'\s*Multiple-get tape-number limit:\s*(\d+)',
        MOOSE_MAX_QUERY_FILE_SIZE: r'\s*Query-file size-limit \(byte\):\s*(\d+)',
        MOOSE_MAX_CONV_THREADS: r'\s*Default max. conversion-threads:\s*(\d+)',
        MOOSE_MAX_XFER_THREADS: r'\s*Default max. transfer-threads:\s*(\d+)'}

    for option, pattern in patterns.items():
        elements = re.search(pattern, ret_val)
        if elements:
            limits[option] = int(elements.group(1))

    return limits


def list_files(moose_uri, sort=None):
    """
    List the files in MASS at the specified MOOSE URI. This function requires
    the ``moo ls`` command to be enabled, e.g.
    ``check_moose_commands_enabled(MOOSE_LS)`` returns True.

    :param str moose_uri: The MOOSE URI to list.
    :param str sort: Sort option, if any, to pass to the 'moo ls' command.
        Currently supported values are 'size' or 'time'.
    :returns: A list of strings containing file names.
    :rtype: list
    """
    command = 'moo ls'
    if sort in ['size', 'time']:
        command += ' --' + sort
    command += ' ' + moose_uri
    files = _run_moose_command(command)
    return files


def list_struct_files(data_set, collection, data_class='crum', sort=None):
    """
    List the files in the MASS directory specified by the supplied arguments.
    This function requires the ``moo ls`` command to be enabled, e.g.
    ``check_moose_commands_enabled(MOOSE_LS)`` returns True.

    :param str data_set: The MOOSE data set to list, e.g. the model name.
    :param str collection: The MOOSE collection to list, e.g. apy.pp or
        ens19/apa.pp.
    :param str data_class: The MOOSE data class to list, e.g. crum or ens.
    :param str sort: Sort option, if any, to pass to the 'moo ls' command.
        Currently supported values are 'size' or 'time'.
    :returns: A list of strings containing file names.
    :rtype: list
    """
    moose_uri = 'moose:/' + data_class + '/' + data_set + '/' + collection
    return list_files(moose_uri, sort=sort)


def metadata_list_struct(data_set, collection, data_class='crum',
        files=None, stashcodes=None, time_range=None, sort=None,
        keep_query_file=False):
    """
    List the files in the MASS directory containing data specified by the
    supplied arguments. If specifying a time range then the dates
    must surround the required data, e.g. for a file from October 1988 then the
    time range should be from 1988-10-01 to 1988-11-01. At least one of
    ``files``, ``stashcodes`` or ``time_range`` arguments must be supplied or
    else the query file generated will be invalid. This function requires the
    ``moo mdls`` command to be enabled, e.g.
    ``check_moose_commands_enabled(MOOSE_MDLS)`` returns True.

    :param str data_set: The MOOSE data set to list, e.g. the model name.
    :param str collection: The MOOSE collection to list, e.g. apy.pp or
        ens19/apa.pp.
    :param str data_class: The MOOSE data class to list, e.g. crum or ens.
    :param list files: The file basenames in MASS to search for specified data.
        If None then all files are searched.
    :param list stashcodes: A list of STASH codes in MSI format to search for.
        If None then all codes are searched for.
    :param tuple time_range: A tuple of date strings to search for data between.
        The strings are in ISO 8601 format YYYY-MM-DD[Thh:mm[:ss]], e.g.
        1980-07-31 or 1980-07-31T12:34. If None then all data is searched.
    :param str sort: The name of the sort attribute, e.g. 'T1', to pass to the
        '--sort' option of the 'moo mdls' command. By default no sorting is
        applied.
    :param bool keep_query_file: Generate the MOOSE record level retrieval query
        file in the current working directory and do not delete it. If false the
        query file is created as a temporary file and deleted after listing the
        files.
    :returns: A list of strings containing the MOOSE path and file name of the
        files found that contain the specified data.
    :rtype: list
    :raises ValueError: If a value is not supplied for at least one of the
        ``files``, ``stashcodes`` or ``time_range`` arguments.
    """
    # At least one of files, stashcodes or time_range must be supplied or else
    # the query file is invalid.
    if not (files or stashcodes or time_range):
        msg = ('A value must be specified for at least one of: files, '
            'stashcodes or time_range.')
        logger.error(msg)
        raise ValueError(msg)

    moose_uri = 'moose:/' + data_class + '/' + data_set + '/' + collection

    query_file_suffix = '_query.txt'
    if keep_query_file:
        _fh, filename = tempfile.mkstemp(suffix=query_file_suffix, dir='.')
    else:
        _fh, filename = tempfile.mkstemp(suffix=query_file_suffix)
    # include an empty string as part of the attributes as this includes the
    # attribute tags and reduces the unused output from moo mdls by a factor of
    # five
    _write_query_file(filename, files=files, stashcodes=stashcodes,
        time_range=time_range, attributes=[''], comment=moose_uri)

    if sort:
        command = 'moo mdls --sort={0} {1} {2}'.format(sort, filename, moose_uri)
    else:
        command = 'moo mdls {0} {1}'.format(filename, moose_uri)

    ret_val = _run_moose_command(command)

    if not keep_query_file:
        _delete_file(filename)

    files = [line for line in ret_val if 'moose:/' in line]

    return files


def query_time_extent(data_set, collection, data_class='crum', stashcodes=None,
        time_attribute='T1'):
    """
    Query the time extent covered by the files in a MASS data collection. The
    data files to examine can be constrained to a particular STASH code, or a
    list of such codes. At present the MOOSE interface only supports querying
    time information for *structured* data collections (e.g. UM PP data streams).

    If no STASH codes are specified then ``time_attribute`` is ignored and the
    time span of the collection is determined by querying the ``file_start_date``
    and ``file_end_date`` metadata associated with the earliest and latest files
    present in the collection.

    .. note:: Note that running this function with and without STASH codes will
        usually yield different results for a given collection. This is because
        file start and end dates are, as the names imply, *outer* limits for all
        data atoms in the file, whereas the T1 (or T2) values for a given STASH
        code record only the start (or end) time for data atoms in the collection.
        The difference will usually be equal to one time meaning period.

    :param str data_set: The MOOSE data set (runid or suite-id) to query.
    :param str collection: The MOOSE collection to query, e.g. 'apy.pp' or
        'ens19/apa.pp'.
    :param str data_class: The MOOSE data class to query, e.g. 'crum' or 'ens'.
    :param list stashcodes: A list of STASH codes to query in MSI format.
        If used, then typically only a single STASH code will be defined. Defining
        many STASH codes will likely exceed MOOSE query limits.
    :param str time_attribute: The time attribute to query. Typically this will
        be one of 'T1' or 'T2'.
    :returns: A tuple of date-time strings (start_time, end_time) in ISO 8601
        format. Both values are set to the empty string '' if no data atoms were
        found in the MASS data collection matching the input parameters.
    """
    moose_uri = 'moose:/' + data_class + '/' + data_set + '/' + collection
    start_time = end_time = ''

    # If 1 or more stash codes were specified then query on the requested time
    # attribute (e.g. T1).
    if stashcodes:
        try:
            _fh, query_file = tempfile.mkstemp(suffix='_query.txt')
            _write_query_file(query_file, stashcodes=stashcodes,
                attributes=[time_attribute])
            command = 'moo mdls --sort={0} {1} {2}'.format(time_attribute,
                query_file, moose_uri)
            ret_val = _run_moose_command(command)
        finally:
            _delete_file(query_file)

        # Parse the command output checking for lines starting with the requested
        # time attribute, e.g. "T1: 1970/01/01 12:00:00"
        patn = r'\s*%s:\s+([\d\s/:]+)' % time_attribute.lower()
        for line in ret_val:
            match = re.search(patn, line)
            if match:
                if not start_time:
                    start_time = match.group(1)
                end_time = match.group(1)

    # If no stash codes were specified then query on the file_start_date and
    # file_end_date attributes.
    else:
        try:
            _fh, query_file = tempfile.mkstemp(suffix='_query.txt')
            _write_query_file(query_file, files=['*'],
                attributes=['file_start_date', 'file_end_date'])
            command = 'moo mdls --summary {0} {1}'.format(query_file, moose_uri)
            ret_val = _run_moose_command(command)
        finally:
            _delete_file(query_file)

        # Parse the command output checking for lines matching 'YYYY/MM/DD hh:mm:ss'
        patn = r'\s*(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})'
        for line in ret_val:
            match = re.search(patn, line)
            if match:
                dt = match.group(1)
                if start_time:
                    # date-time strings can be compared
                    if dt < start_time:
                        start_time = dt
                    elif dt > end_time:
                        end_time = dt
                else:
                    start_time = dt
                    end_time = dt

    # Convert date-times from MASS format (YYYY/MM/DD hh:mm:ss) to ISO 8601 format.
    if start_time:
        start_time = start_time.replace('/', '-').replace(' ', 'T')
        end_time = end_time.replace('/', '-').replace(' ', 'T')

    return start_time, end_time


def get(dest_dir, moose_uri, files=None, overwrite=False, fill_gaps=False,
        splitter_args=None):
    """
    Get files of arbitrary type from MASS taking account of the various limits
    (file number, data volume, etc) imposed by the MOOSE interface. This function
    is a wrapper around the :func:`retrieve_files` function. Refer to that function
    for a description of common arguments.

    :param dict splitter_args: If specified, this should be a dictionary of
        keyword arguments to pass through to the :func:`_request_splitter` function.
    :raises MooseLimitExceededError: Raised if an error was encountered trying
        to split the MOOSE request into chunks.
    """

    if files:
        if splitter_args is None: splitter_args = {}
        file_chunks = _request_splitter('select', files, **splitter_args)
    else:
        file_chunks = [None]

    for chunk in file_chunks:
        retrieve_files(dest_dir, moose_uri, files=chunk, overwrite=overwrite,
            fill_gaps=fill_gaps)


def get_pp(dest_dir, moose_uri, files=None, stashcodes=None, time_range=None,
        overwrite=False, fill_gaps=False, keep_query_file=False, splitter_args=None):
    """
    Get PP files from MASS taking account of the various limits (file number,
    data volume, etc) imposed by the MOOSE interface. This function is a wrapper
    around the :func:`retrieve_files` function. Refer to that function for
    a description of common arguments.

    :param dict splitter_args: If specified, this should be a dictionary of
        keyword arguments to pass through to the :func:`_request_splitter` function.
    :raises MooseLimitExceededError: Raised if an error was encountered trying
        to split the MOOSE request into chunks.
    """

    if files:
        if splitter_args is None: splitter_args = {}
        if stashcodes or time_range:
            # Determine the fixed space needed by the MOOSE query file to define
            # the requested stash codes and/or time range.
            _fh, tmpfile = tempfile.mkstemp()
            _write_query_file(tmpfile, stashcodes=stashcodes, time_range=time_range,
                comment=moose_uri)
            splitter_args['qfile_space_used'] = os.path.getsize(tmpfile)
            os.remove(tmpfile)
        file_chunks = _request_splitter('select', files, **splitter_args)
    else:
        file_chunks = [None]

    for chunk in file_chunks:
        retrieve_files(dest_dir, moose_uri, files=chunk, stashcodes=stashcodes,
            time_range=time_range, overwrite=overwrite, fill_gaps=fill_gaps,
            keep_query_file=keep_query_file)


def get_nc(dest_dir, moose_uri, files=None, var_names=None, overwrite=False,
        fill_gaps=False, keep_filter_file=False, splitter_args=None):
    """
    Get netCDF files from MASS taking account of the various limits (file number,
    data volume, etc) imposed by the MOOSE interface. This function is a wrapper
    around the :func:`retrieve_nc_files` function. Refer to that function for
    a description of common arguments.

    :param dict splitter_args: If specified, this should be a dictionary of
        keyword arguments to pass through to the :func:`_request_splitter` function.
    :raises MooseLimitExceededError: Raised if an error was encountered trying
        to split the MOOSE request into chunks.
    """

    if files:
        if splitter_args is None: splitter_args = {}
        file_chunks = _request_splitter('get', files, **splitter_args)
    else:
        file_chunks = [None]

    for chunk in file_chunks:
        retrieve_nc_files(dest_dir, moose_uri, files=chunk, var_names=var_names,
            overwrite=overwrite, fill_gaps=fill_gaps,
            keep_filter_file=keep_filter_file)


def retrieve_files(dest_dir, moose_uri, files=None, stashcodes=None,
        time_range=None, overwrite=False, fill_gaps=False, keep_query_file=False):
    """
    Retrieve the specified files from MASS using MOOSE. The MOOSE URI should be
    in the form ``moose:/<data_class>/<data_set>/<collection>`` if the
    ``files``, ``stashcodes`` or ``time_range`` optional arguments are used,
    otherwise any valid MOOSE URI is acceptable. If all of the optional
    ``files``, ``stashcodes`` and ``time_range`` arguments are omitted then a
    ``moo get``  retrieval of an entire directory is performed. Otherwise, if
    any of these optional arguments are present then a record level retrieval
    is performed with ``moo select``. If specifying a time range then the dates
    must surround the required data, e.g. for a file from October 1988 then the
    time range should be 1988-10-01 to 1988-11-01.

    :param str dest_dir: The destination directory to retrieve the files to.
    :param str moose_uri: The MOOSE URI to retrieve data from.
    :param list files: A list of file basenames to retrieve. If None then all
        files are retrieved.
    :param list stashcodes: A list of STASH codes in MSI format to retrieve. If
        None then all codes are retrieved.
    :param tuple time_range: A tuple of date-time strings (T_start, T_end) to
        retrieve the data between. The strings should be in ISO 8601 format
        YYYY-MM-DD[Thh:mm[:ss]], e.g. 1980-07-31 or 1980-07-31T12:34. If no
        time range is defined then all data belonging to ``moose_uri`` is retrieved.
        The header attribute ``T1`` is used for data selection, such that
        T_start <= T1 < T_end.
        For instantaneous data, all data points at or after T_start and before
        T_end are selected.
        For time-meaned data, all meaning periods *starting* at or after T_start
        and before T_end are selected.
    :param bool overwrite: Overwrite existing files in the destination directory
        if True.
    :param bool fill_gaps: Retrieve only files that do not already exist in the
        destination directory.
    :param bool keep_query_file: Generate any MOOSE record level retrieval query
        file in the current working directory and do not delete it. If false the
        query file is created as a temporary file and deleted after retrieval of
        the files.
    """
    args = []

    if overwrite:
        args.append('-f')
    if fill_gaps:
        args.append('-i')

    if not (files or stashcodes or time_range):
        query_file_created = False
        args.append(moose_uri)
        args.append(dest_dir)
        command = 'moo get ' + ' '.join(args)
    else:
        query_file_created = True
        query_file_suffix = '_query.txt'
        if keep_query_file:
            _fh, filename = tempfile.mkstemp(suffix=query_file_suffix, dir='.')
        else:
            _fh, filename = tempfile.mkstemp(suffix=query_file_suffix)
        _write_query_file(filename, files=files, stashcodes=stashcodes,
            time_range=time_range, comment=moose_uri)
        args.append(filename)
        args.append(moose_uri)
        args.append(dest_dir)
        command = 'moo select ' + ' '.join(args)

    _run_moose_command(command)

    if query_file_created and not keep_query_file:
        _delete_file(filename)


def retrieve_nc_files(dest_dir, moose_uri, files=None, var_names=None,
        overwrite=False, fill_gaps=False, keep_filter_file=False):
    """
    Retrieve netCDF files from the MASS data archive. The MOOSE URI should be
    in the form ``moose:/<data_class>/<data_set>/<collection>``. If the optional
    ``var_names`` argument is omitted then a ``moo get`` type retrieval is
    performed, either to an entire directory or else to the files specified via
    the ``files`` argument. If the ``var_names`` argument is specified then
    partial file retrievals are performed using the ``moo filter`` command.

    In the case where a subset of netCDF variables is specified via the
    ``var_names`` argument, a MOOSE filter file is created. By default
    this file is deleted after the file retrieval operation, but this can be
    overridden using the ``keep_filter_file`` option, in which case the file
    will be written to the current working directory. Refer to the MOOSE user
    guide for more information regarding the use of filter files.

    :param str dest_dir: The destination directory for retrieved files.
    :param str moose_uri: URI of the MOOSE directory from which to retrieve data.
    :param list files: A list of file basenames to retrieve. If undefined then
        all files contained within the ``moose_uri`` directory are retrieved.
    :param list var_names: A list of the netCDF variable names to extract from
        each file in MASS. If undefined then whole files are retrieved.
    :param bool overwrite: If set to true then existing files in the destination
        directory will be overwritten.
    :param bool fill_gaps: If set to true then only files that do not already
        exist in the destination directory are retrieved.
    :param bool keep_filter_file: If set to true then do not delete the filter
        file, if any, created as part of the retrieval operation.
    """
    args = []
    if overwrite:
        args.append('-f')
    if fill_gaps:
        args.append('-i')
    filter_file = ''

    # if no files are specified then use a wildcard to get all files
    # moo filter requests will fail if the URI is a collection rather than a file
    if files:
        src_uris = [moose_uri+'/'+fn for fn in files]
    else:
        src_uris = [moose_uri+'/*']

    # Get all or selected netcdf files (whole) from the specified moose directory.
    # No variable names were supplied so no filter file is required.
    if not var_names:
        args.extend(src_uris)
        args.append(dest_dir)
        command = 'moo get ' + ' '.join(args)

    # Get subset of variables from all or selected netcdf files.
    # Filter file needs to be created and passed to the moo filter command.
    else:
        suffix = '_filter.txt'
        if keep_filter_file:
            _fh, filter_file = tempfile.mkstemp(suffix=suffix, dir='.')
        else:
            _fh, filter_file = tempfile.mkstemp(suffix=suffix)
        # write the query file and use -a option to preserve the order of
        # variables in the input file
        _write_filter_file(filter_file, var_names, ncks_opts='-a')
        args.append(filter_file)
        args.extend(src_uris)
        args.append(dest_dir)
        command = 'moo filter ' + ' '.join(args)

    _run_moose_command(command)

    if filter_file and not keep_filter_file:
        _delete_file(filter_file)


def retrieve_struct_files(dest_dir, data_set, collection, data_class='crum',
        files=None, stashcodes=None, time_range=None, overwrite=False,
        fill_gaps=False, keep_query_file=False):
    """
    Retrieve the specified files from  a MASS structured data class using
    MOOSE. If specifying a time range then the dates must surround the required
    data, e.g. for a file from October 1988 then the time range should be
    1988-10-01 to 1988-11-01. This function requires the ``moo get`` command to
    be enabled if none of the files, stashcodes or time_range arguments have
    been specified or the ``moo select`` command to be enabled if at least one
    of these arguments has been specified.

    :param str dest_dir: The directory to retrieve the files to.
    :param str data_set: The MOOSE data set to retrieve, e.g. the model name.
    :param str collection: The MOOSE collection to retrieve, e.g. apy.pp or
        ens19/apa.pp.
    :param str data_class: The MOOSE data class to retrieve, e.g. crum or ens.
    :param list files: A list of filenames to retrieve. If None then all files
        are retrieved.
    :param list stashcodes: A list of STASH codes in MSI format to retrieve. If
        None then all codes are retrieved.
    :param tuple time_range: A tuple of date strings to retrieve the data
        between. The strings are in ISO 8601 format YYYY-MM-DD[Thh:mm[:ss]],
        e.g. 1980-07-31 or 1980-07-31T12:34. If None then all data is retrieved.
    :param bool overwrite: Overwrite existing files in the destination directory
        if True.
    :param bool fill_gaps: Retrieve only files that do not already exist in the
        destination directory.
    :param bool keep_query_file: Generate any MOOSE record level retrieval query
        file in the current working directory and do not delete it. If false the
        query file is created as a temporary file and deleted after retrieval of
        the files.
    """
    moose_uri = 'moose:/' + data_class + '/' + data_set + '/' + collection
    retrieve_files(dest_dir, moose_uri, files=files, stashcodes=stashcodes,
        time_range=time_range, overwrite=overwrite, fill_gaps=fill_gaps,
        keep_query_file=keep_query_file)


def put(src_dir, files, moose_uri, overwrite=False, overwrite_if_different=False,
        splitter_args=None):
    """
    Put the specified files into MASS taking account of the various limits (file
    number, data volume, etc) imposed by the MOOSE interface. This function is
    a wrapper around the :func:`put_files` function. Refer to that function for
    a description of common arguments.

    :param dict splitter_args: If specified, this should be a dictionary of
        keyword arguments to pass through to the :func:`_request_splitter` function.
    :raises MooseLimitExceededError: Raised if an error was encountered trying
        to split the MOOSE request into chunks.
    """
    if splitter_args is None: splitter_args = {}
    file_chunks = _request_splitter('put', files, dirpath=src_dir, **splitter_args)

    for chunk in file_chunks:
        put_files(src_dir, chunk, moose_uri, overwrite=overwrite,
            overwrite_if_different=overwrite_if_different)


def put_files(src_dir, files, moose_uri, overwrite=False,
        overwrite_if_different=False):
    """
    Put the specified files into MASS using MOOSE. This function requires the
    ``moo put`` command to be enabled, e.g.
    ``check_moose_commands_enabled(MOOSE_PUT)`` returns True.

    :param str src_dir: The local source directory where the files are located.
    :param list files: A list of the files to be copied from ``src_dir`` to MASS.
    :param str moose_uri: The MOOSE URI of the location in the MASS archive in
        which to store the specified files.
    :param bool overwrite: Force the overwriting of existing files (e.g. the
        ``moo put -f`` option). This argument takes precedence over the
        ``overwrite_if_different`` argument.
    :param bool overwrite_if_different: Force the overwriting of existing files.
        except if the source and destination files match in size and checksum
        (e.g. the ``moo put -F`` option).
    :raises ValueError: If the ``files`` argument does not receive a list.
    """
    if not isinstance(files, (list, tuple)):
        msg = 'files argument must be a list of filename(s)'
        logger.error(msg)
        raise ValueError(msg)

    args = []
    if overwrite:
        args.append('-f')
    elif overwrite_if_different:
        args.append('-F')

    filepaths = [os.path.join(src_dir, fn) for fn in files]
    args.extend(filepaths)

    args.append(moose_uri)

    command = 'moo put ' + ' '.join(args)

    _run_moose_command(command)


def put_struct_files(src_dir, files, data_set, collection, data_class='crum',
        overwrite=False, overwrite_if_different=False):
    """
    Put the specified files into a MASS structured data class using MOOSE. This
    function requires the ``moo put`` command to be enabled, e.g.
    ``check_moose_commands_enabled(MOOSE_PUT)`` returns True.

    :param str src_dir: The local source directory where the files are located.
    :param list files: A list of the files to be copied from ``src_dir`` to MASS.
    :param str data_set: The MOOSE data set to put into, e.g. the model name.
    :param str collection: The MOOSE collection to put into, e.g. apy.pp or
        ens19/apa.pp.
    :param str data_class: The MOOSE data class to put into, e.g. crum or ens.
    :param bool overwrite: Force the overwriting of existing files (e.g. the
        ``moo put -f`` option). This argument takes precedence over the
        ``overwrite_if_different`` argument.
    :param bool overwrite_if_different: Force the overwriting of existing files
        except if the source and destination files match in size and checksum
        (e.g. the ``moo put -F`` option).
    :raises ValueError: If the ``files`` argument does not receive a list.
    """
    moose_uri = 'moose:/{}/{}/{}'.format(data_class, data_set, collection)

    put_files(src_dir, files, moose_uri, overwrite=overwrite,
        overwrite_if_different=overwrite_if_different)


def _write_query_file(filename, files=None, stashcodes=None, time_range=None,
        attributes=None, comment=None):
    """
    Write the file required for MOOSE record level retrievals.

    :param str filename: The full path name of the query file to write to.
    :param list files: A list of file names.
    :param list stashcodes: A list of STASH codes.
    :param tuple time_range: A tuple of date-time strings (T_start, T_end) to
        retrieve the data between. The strings should be in ISO 8601 format
        YYYY-MM-DD[Thh:mm[:ss]], e.g. 1980-07-31 or 1980-07-31T12:34.
        The header attribute ``T1`` is used for data selection, such that
        T_start <= T1 < T_end.
        For instantaneous data, all data points at or after T_start and before
        T_end are selected.
        For time-meaned data, all meaning periods *starting* at or after T_start
        and before T_end are selected.
    :param list attributes: A list of string attributes to include in the
        optional attributes section that is used by moo mdls.
    :param str comment: A string to include on a comment line at the top of the
        file.
    :raises afterburner.exceptions.TempFileError: If unable to create the file.
    """
    try:
        fh = open(filename, 'w')
    except IOError as error:
        msg = ('Unable to create temporary file ' + filename + '\n' + str(error))
        logger.error(msg)
        raise afterburner.exceptions.TempFileError(msg)

    if comment:
        fh.write('# ' + comment + '\n')

    fh.write('begin\n')

    if stashcodes:
        # get rid of duplicates by putting into a set and then sorting into a
        # list
        temp_list = []
        for sc in stashcodes:
            # convert from msi form to integer form
            stash_object = iris.fileformats.pp.STASH.from_msi(sc)
            numeric_stash = str(stash_object.section * 1000 + stash_object.item)
            temp_list.append(numeric_stash)
        set_of_stash = set(temp_list)
        unique_stash = sorted(set_of_stash)

        if len(unique_stash) == 1:
            fh.write('    stash=' + unique_stash[0] + '\n')
        else:
            fh.write('    stash=(')
            comma_stash_list = ','.join(unique_stash)
            fh.write(comma_stash_list)
            fh.write(')\n')

    if files:
        # get rid of duplicate input files
        unique_filenames = set([os.path.basename(path) for path in files])
        filenames = sorted(unique_filenames)

        if len(filenames) == 1:
            fh.write('    pp_file="' + filenames[0] + '"\n')
        else:
            comma_quoted_list = ','.join(['"%s"' % li for li in filenames])
            fh.write('    pp_file=(')
            fh.write(comma_quoted_list)
            fh.write(')\n')

    if time_range:
        d1, d2 = _pdt_from_date_tuple(time_range)
        fh.write('    T1>={{{0}}}\n'.format(_moose_date_string_from_pdt(d1)))
        fh.write('    T1<{{{0}}}\n'.format(_moose_date_string_from_pdt(d2)))

    fh.write('end\n')

    if attributes:
        fh.write('begin_attributes\n')
        for attr in attributes:
            fh.write(attr + '\n')
        fh.write('end_attributes\n')

    fh.close()


def _write_filter_file(filename, var_names=None, dims_and_coords=None,
        ncks_opts=None):
    """
    Write a file of ncks options for use by the 'moo filter' command. Refer to
    the MOOSE user guide for more information regarding the use of filter files.

    :param str filename: The name of the filter file to write.
    :param list var_names: A list of the variable names to extract from each
        retrieved netCDF file.
    :param list dims_and_coords: A list of 3-tuples defining hyperslabs suitable
        for passing to the ncks -d option. Each 3-tuple comprises a dimension
        name, a minimum index or coordinate, and a maximum index or coordinate.
        If indexes are used, the values must both be integers. If coordinates
        are used the values must both be floats. The stride option is not
        currently supported. Refer to the ncks documentation for further
        details.
    :param str ncks_opts: Any additional command line options to pass to ncks.
    :raises afterburner.exceptions.TempFileError: If unable to create the file
    """
    try:
        fh = open(filename, 'w')
    except IOError as error:
        msg = 'Unable to open file {0}:\n{1}'.format(filename, str(error))
        logger.error(msg)
        raise afterburner.exceptions.TempFileError(msg)

    if ncks_opts:
        fh.write(ncks_opts + '\n')

    # TODO: add support for stride option?
    if dims_and_coords:
        for dim, dmin, dmax in dims_and_coords:
            fh.write('-d {0},{1},{2}\n'.format(dim, dmin, dmax))

    if var_names:
        fh.write('-v {0}\n'.format(','.join(var_names)))

    fh.close()


def _pdt_from_date_tuple(time_pair):
    """
    Generate a tuple of PartialDateTime objects from a tuple of two strings in
    ISO 8601 format. An exception is raised and an error message displayed if
    they're not valid.

    :param tuple time_pair: Two ISO 8601 date and time strings.
    :returns: A tuple of iris.time.PartialDateTime objects containing the dates
        and times from ``time_pair``
    :rtype: tuple
    :raises ValueError: If the argument is not valid
    """
    if not isinstance(time_pair, (tuple, list)):
        msg = 'The two times must be supplied as a tuple or list'
        logger.error(msg)
        raise ValueError(msg)
    num_vals = len(time_pair)
    if num_vals != 2:
        msg = (str(num_vals) + ' time strings supplied. Two strings should '
                               'be supplied.')
        logger.error(msg)
        raise ValueError(msg)
    for val in time_pair:
        if not isinstance(val, string_types):
            msg = 'The dates supplied must be strings.'
            logger.error(msg)
            raise ValueError(msg)

    pdt1 = pdt_from_date_string(time_pair[0])
    pdt2 = pdt_from_date_string(time_pair[1])

    return pdt1, pdt2


def _moose_date_string_from_pdt(pdt):
    """
    Generate a date and time string in MOOSE format (YYYY/MM/DD [hh:mm[:ss]])
    from a PartialDateTime object.

    :param iris.time.PartialDateTime pdt: The partial date time to convert to a
        MOOSE string.
    :returns: A date-time string in MOOSE format.
    :raises ValueError: if year, month or day are not specified or are zero.
    """
    # year, month and day must not be None and must be greater than 0
    if not (pdt.year and pdt.month and pdt.day):
        msg = ('Year, month and day must all be specified in date strings used '
            'by MOOSE.')
        logger.error(msg)
        raise ValueError(msg)
    moose_str = '{:04}/{:02}/{:02}'.format(pdt.year, pdt.month, pdt.day)

    # hour, minute and second should be included if not None, but they can be 0
    if pdt.hour is not None and pdt.minute is not None:
        moose_str += ' {:02}:{:02}'.format(pdt.hour, pdt.minute)
        if pdt.second is not None:
            moose_str += ':{:02}'.format(pdt.second)

    return moose_str


def _run_moose_command(command):
    """
    Run the MOOSE command specified and return any output to stdout or stderr as
    a list of strings.

    :param str command: The complete moose command to run.
    :returns: Any output from the command.
    :rtype: list
    :raises afterburner.exceptions.MooseUnavailableError: If MOOSE is not
        currently available.
    :raises afterburner.exceptions.MooseCommandError: If the MOOSE command is
        not valid.
    """
    try:
        cmd_out = subprocess.check_output(command, stderr=subprocess.STDOUT,
            shell=True)
        cmd_out = cmd_out.decode('utf8')          # for Python 3 compatibility

    except subprocess.CalledProcessError as exc:
        try:
            cmd_out = exc.output.decode('utf8')   # for Python 3 compatibility
        except:
            cmd_out = exc.output or ''
        msg = ('MOOSE command did not complete successfully. Command:\n%s\n'
            'produced error:\n%s' % (command, cmd_out))

        if exc.returncode in [MOOSE_SYSTEM_OUTAGE, MOOSE_TEMPORARILY_DISABLED]:
            logger.error(msg)
            raise afterburner.exceptions.MooseUnavailableError(msg)

        elif exc.returncode == MOOSE_ALL_FILES_EXIST:
            # The MOOSE interface returns error code 17 if the fill gaps option
            # is enabled but all requested files are on disk. This code can be
            # ignored, but log a warning message to record the fact.
            msg = ('MOOSE command resulted in no action: all requested files '
                'are present on disk.')
            logger.warning(msg)

        else:
            logger.error(msg)
            raise afterburner.exceptions.MooseCommandError(msg)

    return cmd_out.rstrip().split('\n')


def _delete_file(filename):
    """
    Deletes the specified file. If the file can't be deleted then a logger
    warning message is created.

    :param str filename: The complete path and name of the file to delete.
    """
    try:
        os.remove(filename)
    except OSError as exc:
        msg = 'Unable to delete file: ' + filename + '\n' + str(exc)
        logger.warning(msg)


def _request_splitter(req_type, filenames, dirpath=None, file_limit=None,
        volume_limit=None, qfile_space_used=None, order=None):
    """
    Split a list of files into chunks whose size is determined by the MOOSE
    command-line interface limits specified via the corresponding keyword
    arguments.

    :param str req_type: The MOOSE request type: one of 'get', 'put' or 'select'.
    :param str filenames: The list of filenames to be split into chunks.
    :param str dirpath: For put requests, the path to the directory containing
        the files specified in ``filenames``.
    :param int file_limit: The maximum number of files to include in each chunk.
        If undefined, the limit is obtained by querying the MOOSE interface. Set
        to -1 to disable chunking by number of files.
    :param int volume_limit: The maximum data volume to include in each chunk.
        If undefined, the volume limit is obtained by querying the MOOSE interface.
        Set to -1 to disable chunking by data volume.
    :param int qfile_space_used: The amount (in bytes) of fixed space used by
        non-filename information in a MOOSE query file. If undefined, the amount
        of space is obtained by querying the the MOOSE interface. Set to -1 to
        disable chunking by query file size. Note: this parameter is only required
        for MOOSE select operations.
    :param str order: The order in which to apply the various MOOSE limits.
        Default settings are 'f' for plain get operations, 'fv' for put operations,
        'qf' for select operations, and 'f' otherwise. The letters f, v, and q
        signify file limit, volume limit, and query file limit, respectively.
    :raises MooseLimitExceededError: Raised if an error was encountered trying
        to split the MOOSE request into chunks.
    """
    # The number of characters included around a filename in a MOOSE query file.
    # 3 characters is derived from a pair of quotation marks and a comma.
    num_padding_chars = 3

    # The number of characters included on the filename line in a MOOSE query file.
    num_file_chars = 15

    moose_limits = get_moose_limits()

    # Set processing order.
    default_order = {'get': 'f', 'put': 'fv', 'select': 'qf'}
    if not order:
        order = default_order.get(req_type, 'f')

    # Set file number limit.
    if file_limit is None:
        if req_type == 'put':
            file_limit = moose_limits[MOOSE_PUT_MAX_FILES]
        else:
            file_limit = moose_limits[MOOSE_GET_MAX_FILES]
    elif file_limit < 0:
        file_limit = 0

    # Set file size limit.
    if volume_limit is None:
        if req_type == 'put':
            volume_limit = moose_limits[MOOSE_PUT_MAX_VOLUME]
        else:
            volume_limit = moose_limits[MOOSE_GET_MAX_VOLUME]
    elif volume_limit < 0:
        volume_limit = 0
    volume_limit *= MIBYTES_TO_BYTES

    # Set query file limit.
    query_file_size = moose_limits[MOOSE_MAX_QUERY_FILE_SIZE]
    if qfile_space_used is None:
        qfile_space_left = query_file_size
    elif qfile_space_used < 0:
        qfile_space_left = 0
    else:
        qfile_space_left = query_file_size - (qfile_space_used + num_file_chars)

    # Initialise with a single chunk containing all filenames.
    chunks = [filenames]

    # Loop over each constraint producing progressively smaller chunks.
    try:
        for limit in order:
            new_chunks = []

            # apply file limits if requested
            if limit == 'f' and file_limit:
                for chunk in chunks:
                    new_chunks.extend(_chunk_items(chunk, file_limit))

            # apply volume limits if requested
            elif limit == 'v' and volume_limit:
                for chunk in chunks:
                    file_sizes = [os.path.getsize(os.path.join(dirpath, f)) for f in chunk]
                    new_chunks.extend(_chunk_items(chunk, volume_limit, file_sizes))

            # apply query file size limits if requested
            elif limit == 'q' and qfile_space_left > 0:
                for chunk in chunks:
                    filename_length = len(os.path.basename(chunk[0])) + num_padding_chars
                    new_chunks.extend(_chunk_items(chunk, qfile_space_left,
                        [filename_length] * len(chunk)))

            if len(new_chunks):
                chunks = new_chunks

    except _ChunkSizeExceededError as exc:
        msg = str(exc)
        msg += "\nProblem trying to split MOOSE {} request into chunks.".format(req_type)
        logger.error(msg)
        raise afterburner.exceptions.MooseLimitExceededError(msg)

    return chunks


def _chunk_items(items, max_chunk_cost, item_costs=None):
    """
    Separate the passed-in list of items into chunks, with each chunk having a
    maximum cost that does not exceed ``max_chunk_cost``. An item cost of
    one is used if ``item_costs`` is None. The units of cost are not specified.
    Typically, costs will represent units such as the number of files, tapes or
    characters, data volume, etc.
    """
    if not item_costs:
        item_costs = [1] * len(items)

    chunks = []
    current_chunk = []
    chunk_cost = 0

    for item, item_cost in zip(items, item_costs):
        if item_cost > max_chunk_cost:
            msg = "Item size of {:s} exceeds max chunk size of {:s}".format(
                item_cost, max_chunk_cost)
            raise _ChunkSizeExceededError(msg)
        elif (chunk_cost + item_cost) > max_chunk_cost:
            chunks.append(current_chunk)
            current_chunk = [item]
            chunk_cost = item_cost
        else:
            current_chunk.append(item)
            chunk_cost += item_cost

    chunks.append(current_chunk)

    return chunks
