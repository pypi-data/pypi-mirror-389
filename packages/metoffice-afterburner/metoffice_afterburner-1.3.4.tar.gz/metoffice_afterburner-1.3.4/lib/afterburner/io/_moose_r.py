# (C) British Crown Copyright 2017-2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.

# The ``_moose_r`` module contains functions which act as a wrapper around the
# main MOOSE data retrieval commands, namely 'get', 'select' and 'filter'.
#
# Client applications should normally access the functions defined here via the
# afterburner.io.moose2 module.

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import os
import tempfile

from afterburner.io import _moose_core

__all__ = ('get', 'get_pp', 'get_nc', 'retrieve_files', 'retrieve_struct_files',
    'retrieve_nc_files')

logger = _moose_core.get_moose_logger()


def get(dest_dir, moose_uri, files=None, splitter_args=None, **kwargs):
    """
    Get files of arbitrary type from MASS taking into account the various limits
    (file number, data volume, etc) imposed by the MOOSE interface. This function
    is a wrapper around the :func:`retrieve_files` function. Refer to that function
    for a description of additional keyword arguments.

    :param dict splitter_args: If specified, this should be a dictionary of
        keyword arguments to pass through to the :func:`_moose_core.request_splitter`
        function. For example, to split ``files`` (if defined) by both number of
        files and query file size limit, set this argument to `{'order': 'fq'}`.
    :raises MooseLimitExceededError: Raised if an error was encountered trying
        to split the MOOSE request into chunks.
    """

    if files:
        if splitter_args is None: splitter_args = {}
        file_chunks = _moose_core.request_splitter('get', files, **splitter_args)
    else:
        file_chunks = [None]

    for chunk in file_chunks:
        retrieve_files(dest_dir, moose_uri, files=chunk, **kwargs)


def get_pp(dest_dir, moose_uri, files=None, stashcodes=None, time_range=None,
        splitter_args=None, **kwargs):
    """
    Get PP files from MASS taking into account the various limits (file number,
    data volume, etc) imposed by the MOOSE interface. This function is a wrapper
    around the :func:`retrieve_files` function. Refer to that function for
    a description of additional keyword arguments.

    :param dict splitter_args: If specified, this should be a dictionary of
        keyword arguments to pass through to the :func:`_moose_core.request_splitter`
        function.
    :raises MooseLimitExceededError: Raised if an error was encountered trying
        to split the MOOSE request into chunks.
    """

    if files:
        if splitter_args is None: splitter_args = {}
        if stashcodes or time_range:
            # Determine the fixed space needed by the MOOSE query file to define
            # the requested stash codes and/or time range.
            _fh, tmpfile = tempfile.mkstemp()
            _moose_core.write_query_file(tmpfile, stashcodes=stashcodes,
                time_range=time_range, comment=moose_uri)
            splitter_args['qfile_space_used'] = os.path.getsize(tmpfile)
            os.remove(tmpfile)
        file_chunks = _moose_core.request_splitter('select', files, **splitter_args)
    else:
        file_chunks = [None]

    for chunk in file_chunks:
        retrieve_files(dest_dir, moose_uri, files=chunk, stashcodes=stashcodes,
            time_range=time_range, **kwargs)


def get_nc(dest_dir, moose_uri, files=None, var_names=None, splitter_args=None,
        **kwargs):
    """
    Get netCDF files from MASS taking into account the various limits (file number,
    data volume, etc) imposed by the MOOSE interface. This function is a wrapper
    around the :func:`retrieve_nc_files` function. Refer to that function for
    a description of additional keyword arguments.

    :param dict splitter_args: If specified, this should be a dictionary of
        keyword arguments to pass through to the :func:`_moose_core.request_splitter`
        function.
    :raises MooseLimitExceededError: Raised if an error was encountered trying
        to split the MOOSE request into chunks.
    """

    if files:
        if splitter_args is None: splitter_args = {}
        file_chunks = _moose_core.request_splitter('get', files, **splitter_args)
    else:
        file_chunks = [None]

    for chunk in file_chunks:
        retrieve_nc_files(dest_dir, moose_uri, files=chunk, var_names=var_names,
            **kwargs)


def retrieve_files(dest_dir, moose_uri, files=None, stashcodes=None,
        time_range=None, overwrite=False, fill_gaps=False, ignore_missing=False,
        keep_query_file=False, **kwargs):
    """
    Retrieve files from MASS using the MOOSE interface. The MOOSE URI should be
    in the form ``moose:/<data_class>/<data_set>/<collection>`` if any of the
    ``files``, ``stashcodes`` or ``time_range`` arguments are defined. Otherwise
    any valid MOOSE URI is acceptable.

    If none of the ``files``, ``stashcodes`` or ``time_range`` arguments are
    defined then a 'moo get' retrieval of an entire collection is performed.

    If any of those keyword arguments are defined then a record level retrieval
    is performed using 'moo select'. If specifying a time range then the dates
    should surround the required data, e.g. for a file from October 1988 the
    time range end-points should be '1988-10-01' to '1988-11-01'.

    :param str dest_dir: The destination directory for retrieved files.
    :param str moose_uri: The MOOSE URI from which to retrieve data.
    :param list files: A list of file basenames to retrieve. If None then all
        files are retrieved from ``moose_uri``.
    :param list stashcodes: A list of STASH codes, in MSI format, to retrieve.
        If None then whole files are retrieved.
    :param tuple time_range: A tuple of date-time strings (T_start, T_end) to
        retrieve the data between. The strings should be in ISO 8601 format
        'YYYY-MM-DD[Thh:mm[:ss]]', e.g. '1980-07-31' or '1980-07-31T12:34'. If no
        time range is defined then all data belonging to ``moose_uri`` is retrieved.
        The PP header attribute 'T1' is used for data selection, such that
        T_start <= T1 < T_end.

        For *instantaneous data*, all data points at or after T_start and before
        T_end are selected.

        For *time-meaned data*, all meaning periods *starting* at or after T_start
        and before T_end are selected.
    :param bool overwrite: If set to true then overwrite existing files in the
        destination directory.
    :param bool fill_gaps: If set to true then only retrieve files that do not
        already exist in the destination directory.
    :param bool ignore_missing: If set to true then, for MOOSE GET operations,
        potential errors caused by missing files are ignored. This is effected
        by passing the '-g' option to the 'moo get' command, though *only* in
        the case where a list of files is requested (i.e. no STASH codes or time
        range as these require use of 'moo select').
    :param bool keep_query_file: If set to true then retain any MOOSE record
        level retrieval query file in the current working directory. If false,
        the query file is created as a temporary file and deleted after the
        retrieval operation.
    """
    opts = []
    args = []

    if overwrite:
        opts.append('-f')
    if fill_gaps:
        opts.append('-i')
    query_file = ''

    raw_get = not (files or stashcodes or time_range)
    files_get = files and not (stashcodes or time_range)

    # If no files/stashcodes/times defined then 'moo get' whole collection.
    if raw_get:
        args.append(moose_uri)
        args.append(dest_dir)
        command = 'get'

    # If file list defined and '-g' option requested then 'moo get' just those files.
    elif files_get and ignore_missing:
        src_uris = [moose_uri+'/'+fn for fn in files]
        opts.append('-g')
        args.extend(src_uris)
        args.append(dest_dir)
        command = 'get'

    # Otherwise use 'moo select' to perform a record-level retrieval.
    else:
        suffix = '_query.txt'
        if keep_query_file:
            _fh, query_file = tempfile.mkstemp(suffix=suffix, dir='.')
        else:
            _fh, query_file = tempfile.mkstemp(suffix=suffix)
        _moose_core.write_query_file(query_file, files=files, stashcodes=stashcodes,
            time_range=time_range, comment=moose_uri)
        args.append(query_file)
        args.append(moose_uri)
        args.append(dest_dir)
        command = 'select'

    command = _moose_core.MooseCommand(command, options=opts, arguments=args)

    _moose_core.run_moose_command(command.augmented_command)

    if query_file and not keep_query_file:
        _delete_file(query_file)


def retrieve_nc_files(dest_dir, moose_uri, files=None, var_names=None,
        overwrite=False, fill_gaps=False, ignore_missing=False,
        keep_filter_file=False, **kwargs):
    """
    Retrieve netCDF files from the MASS data archive. The MOOSE URI should be
    in the form ``moose:/<data_class>/<data_set>/<collection>``. If the optional
    ``var_names`` argument is omitted then a 'moo get' type retrieval is
    performed, either to an entire directory or else to the filenames specified
    via the ``files`` argument. If the ``var_names`` argument is specified then
    partial file retrievals are performed using the 'moo filter' command.

    In the case where a subset of netCDF variables is specified via the
    ``var_names`` argument, a MOOSE filter file is created. By default
    this file is deleted after the file retrieval operation, but this can be
    overridden using the ``keep_filter_file`` option, in which case the file
    will be retained in the current working directory. Refer to the MOOSE user
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
        exist in the destination directory will be retrieved.
    :param bool ignore_missing: If set to True then, for MOOSE GET operations,
        potential errors caused by missing files are ignored. This is effected
        by passing the '-g' option to the 'moo get' command.
    :param bool keep_filter_file: If set to true then do not delete the filter
        file, if any, created as part of the retrieval operation.
    """
    opts = []
    args = []

    if overwrite:
        opts.append('-f')
    if fill_gaps:
        opts.append('-i')
    filter_file = ''

    # If no files are specified then use a wildcard to get all files.
    # moo filter requests will fail if the URI is a collection rather than a file.
    if files:
        src_uris = [moose_uri+'/'+fn for fn in files]
    else:
        src_uris = [moose_uri+'/*']

    # Get all or selected netcdf files (whole) from the specified moose directory.
    # No variable names were supplied so no filter file is required.
    if not var_names:
        if ignore_missing: opts.append('-g')
        args.extend(src_uris)
        args.append(dest_dir)
        command = 'get'

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
        _moose_core.write_filter_file(filter_file, var_names, ncks_opts='-a')
        args.append(filter_file)
        args.extend(src_uris)
        args.append(dest_dir)
        command = 'filter'

    command = _moose_core.MooseCommand(command, options=opts, arguments=args)

    _moose_core.run_moose_command(command.augmented_command)

    if filter_file and not keep_filter_file:
        _delete_file(filter_file)


def retrieve_struct_files(dest_dir, data_set, collection, data_class='crum',
        files=None, stashcodes=None, time_range=None, overwrite=False,
        fill_gaps=False, ignore_missing=False, keep_query_file=False):
    """
    Retrieve the specified files from a MASS structured data class using
    MOOSE. This function is a thin wrapper around the :func:`retrieve_files`
    function; refer to the latter for more detailed documentation.

    :param str dest_dir: The directory to retrieve the files to.
    :param str data_set: The MOOSE data set to retrieve, e.g. the model name.
    :param str collection: The MOOSE collection to retrieve, e.g. 'apy.pp' or
        'ens19/apa.pp' in the case of an ensemble run.
    :param str data_class: The MOOSE data class to retrieve, e.g. 'crum' or 'ens'.
    :param list files: A list of filenames to retrieve. If None then all files
        are retrieved.
    :param list stashcodes: A list of STASH codes in MSI format to retrieve. If
        None then whole files are retrieved.
    :param tuple time_range: A tuple of date strings to retrieve the data
        between. The strings are in ISO 8601 format 'YYYY-MM-DD[Thh:mm[:ss]]',
        e.g. '1980-07-31' or '1980-07-31T12:34'. If None then all data is retrieved.
    :param bool overwrite: If set to true then overwrite existing files in the
        destination directory.
    :param bool fill_gaps: If set to true then only retrieve files that do not
        already exist in the destination directory.
    :param bool ignore_missing: If set to true then, for MOOSE GET operations,
        potential errors caused by missing files are ignored. This is effected
        by passing the '-g' option to the 'moo get' command.
    :param bool keep_query_file: If set to true then retain any MOOSE record
        level retrieval query file in the current working directory. If false,
        the query file is created as a temporary file and deleted after the
        retrieval operation.
    """
    moose_uri = 'moose:/' + data_class + '/' + data_set + '/' + collection
    retrieve_files(dest_dir, moose_uri, files=files, stashcodes=stashcodes,
        time_range=time_range, overwrite=overwrite, fill_gaps=fill_gaps,
        ignore_missing=ignore_missing, keep_query_file=keep_query_file)


def _delete_file(filename):
    """
    Deletes the specified file. If the file can't be deleted then a logger
    warning message is created.

    :param str filename: The full pathname of the file to delete.
    """
    try:
        os.remove(filename)
    except OSError as exc:
        msg = 'Unable to delete file: ' + filename + '\n' + str(exc)
        logger.warning(msg)
