# (C) British Crown Copyright 2017-2020, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.

# The ``_moose_q`` module contains functions which act as a wrapper around the
# main MOOSE data query commands, namely 'ls' and 'mdls'.
#
# Client applications should normally access the functions defined here via the
# afterburner.io.moose2 module.

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import os
import re
import tempfile

from afterburner.io import _moose_core
from afterburner.utils.dateutils import moose_date_to_iso_date, MOOSE_DATETIME_REGEX

__all__ = ('list_files', 'list_struct_files', 'metadata_list_struct',
    'query_time_extent')

logger = _moose_core.get_moose_logger()


def list_files(moose_uri, sort=None):
    """
    List the files in MASS at the specified MOOSE URI. This function requires
    the ``moo ls`` command to be enabled. If necessary, client code can check
    this via a call to :func:`afterburner.io.moose2.check_moose_commands_enabled`.

    :param str moose_uri: The MOOSE URI to list.
    :param str sort: Sort option, if any, to pass to the 'moo ls' command.
        Currently supported values are 'size' or 'time'.
    :returns: A list of file names.
    :rtype: list
    """
    opts = ['--' + sort] if sort in ['size', 'time'] else []
    command = _moose_core.MooseCommand('ls', options=opts, arguments=[moose_uri])

    files = _moose_core.run_moose_command(command.augmented_command)

    return files


def list_struct_files(data_set, collection, data_class='crum', sort=None):
    """
    List the files in the MASS directory defined by the specified data class,
    set and collection. This function requires the ``moo ls`` command to be
    enabled. If necessary, client code can check this via a call to
    :func:`afterburner.io.moose2.check_moose_commands_enabled`.

    :param str data_set: The MOOSE data set to list, e.g. the model name.
    :param str collection: The MOOSE collection to list, e.g. 'apy.pp' or
        'ens19/apa.pp' in the case of an ensemble run.
    :param str data_class: The MOOSE data class to list, e.g. 'crum' or 'ens'.
    :param str sort: Sort option, if any, to pass to the 'moo ls' command.
        Currently supported values are 'size' or 'time'.
    :returns: A list of file names.
    :rtype: list
    """
    moose_uri = 'moose:/' + data_class + '/' + data_set + '/' + collection
    return list_files(moose_uri, sort=sort)


def metadata_list_struct(data_set, collection, data_class='crum',
        files=None, stashcodes=None, time_range=None, sort=None,
        keep_query_file=False):
    """
    List the files in the MASS directory defined by the specified data class,
    set and collection. If specifying a time range then the dates should surround
    the required data, e.g. for a file from October 1988 then the time range
    end-points should be '1988-10-01' to '1988-11-01'.

    At least one of ``files``, ``stashcodes`` or ``time_range`` arguments must
    be supplied otherwise the generated query file will be invalid.

    This function requires the ``moo mdls`` command to be enabled. If necessary,
    client code can check this via a call to
    :func:`afterburner.io.moose2.check_moose_commands_enabled`.

    :param str data_set: The MOOSE data set to list, e.g. the model name.
    :param str collection: The MOOSE collection to list, e.g. 'apy.pp' or
        'ens19/apa.pp' in the case of an ensemble run.
    :param str data_class: The MOOSE data class to list, e.g. 'crum' or 'ens'.
    :param list files: The file basenames in MASS to search for specified data.
        If None then all files are searched.
    :param list stashcodes: A list of STASH codes in MSI format to search for.
        If None then all codes are searched for.
    :param tuple time_range: A tuple of date strings to search for data between.
        The strings are in ISO 8601 format 'YYYY-MM-DD[Thh:mm[:ss]]', e.g.
        '1980-07-31' or '1980-07-31T12:34'. If None then all data is searched.
    :param str sort: The name of the sort attribute, e.g. 'T1', to pass to the
        '--sort' option of the 'moo mdls' command. By default no sorting is
        applied.
    :param bool keep_query_file: Generate the MOOSE record level retrieval query
        file in the current working directory and do not delete it. If false the
        query file is created as a temporary file and deleted after listing the
        files.
    :returns: A list of MOOSE URIs specifying the files which match the specified
        constaints.
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
    _moose_core.write_query_file(filename, files=files, stashcodes=stashcodes,
        time_range=time_range, attributes=[''], comment=moose_uri)

    opts = ['--sort=%s' % sort] if sort else []
    command = _moose_core.MooseCommand('mdls', options=opts, arguments=[filename,
        moose_uri])

    ret_val = _moose_core.run_moose_command(command.augmented_command)

    if not keep_query_file:
        _delete_file(filename)

    files = [line for line in ret_val if 'moose:/' in line]

    return files


def query_time_extent(data_set, collection, data_class='crum', stashcodes=None,
        levels=None, time_attribute='T1'):
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
    :param list levels: An optional list of model levels which may be used to
        constrain the query to specific values of the 'lblev' PP header field.
        Supplying a subset of levels will typically lead to more efficient queries
        against multi-level diagnostics since, for these, the date-time value is
        usually constant across all levels. For example, specifying levels=[0,1,9999]
        would limit the query to the lowest or, for surface fields, only model level.
    :param str time_attribute: The time attribute to query. Typically this will
        be one of 'T1' or 'T2'.
    :returns: A tuple of date-time strings (start_time, end_time) in ISO 8601
        format. Both values are set to the empty string if no data atoms
        matching the input parameters were found in the MASS data collection.
    """
    moose_uri = 'moose:/' + data_class + '/' + data_set + '/' + collection
    start_time = end_time = query_file = ''

    # If 1 or more stash codes were specified then query on the requested time
    # attribute (e.g. T1).
    if stashcodes:
        try:
            _fh, query_file = tempfile.mkstemp(suffix='_query.txt')
            _moose_core.write_query_file(query_file, stashcodes=stashcodes,
                levels=levels, attributes=[time_attribute])
            command = _moose_core.MooseCommand('mdls',
                options=['--sort=%s' % time_attribute],
                arguments=[query_file, moose_uri])
            ret_val = _moose_core.run_moose_command(command.augmented_command)
        finally:
            _delete_file(query_file)

        # Parse the command output checking for lines starting with the requested
        # time attribute, e.g. "T1: 1970/01/01 12:00:00"
        patn = r'\s*{0}:\s+({1})'.format(time_attribute.lower(), MOOSE_DATETIME_REGEX)
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
            _moose_core.write_query_file(query_file, files=['*'],
                levels=levels, attributes=['file_start_date', 'file_end_date'])
            command = _moose_core.MooseCommand('mdls', options=['--summary'],
                arguments=[query_file, moose_uri])
            ret_val = _moose_core.run_moose_command(command.augmented_command)
        finally:
            _delete_file(query_file)

        # Parse the command output checking for lines matching 'YYYY/MM/DD hh:mm:ss'
        # Note: Within MASS, dates < 1000/1/1 do NOT appear with zero-padded years.
        patn = r'\s*({0})'.format(MOOSE_DATETIME_REGEX)
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
        start_time = moose_date_to_iso_date(start_time)
        end_time = moose_date_to_iso_date(end_time)

    return start_time, end_time


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
