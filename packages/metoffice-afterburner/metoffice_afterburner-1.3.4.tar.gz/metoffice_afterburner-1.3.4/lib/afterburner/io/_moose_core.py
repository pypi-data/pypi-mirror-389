# (C) British Crown Copyright 2017-2022, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.

# The ``_moose_core`` module contains common functions needed by the moose2 and
# _moose* modules.
#
# Client applications should normally access the functions defined here via the
# afterburner.io.moose2 module.

from __future__ import (absolute_import, division, print_function, unicode_literals)
from six.moves import (filter, input, map, range, zip)
from six import string_types

import os
import re
import subprocess
import logging
import iris.fileformats.pp

import afterburner.exceptions
from afterburner.utils.dateutils import pdt_from_date_string
from afterburner.utils import is_non_string_sequence, is_true

#: MOOSE return code in the case of a user error, e.g. a malformed URI.
MOOSE_USER_ERROR = 2

#: MOOSE return code in the case of a system error or outage.
MOOSE_SYSTEM_OUTAGE = 3

#: MOOSE return code in the case of an external client system error.
MOOSE_CLIENT_SYSTEM_ERROR = 4

#: MOOSE return code in the case of a temporarily unavailable feature.
MOOSE_TEMPORARILY_DISABLED = 5

#: MOOSE return code in the case of all files existing in destination directory.
MOOSE_ALL_FILES_EXIST = 17

#: Symbolic constant for identifying the ``moo ls`` command.
MOOSE_LS = 1

#: Symbolic constant for identifying the ``moo put`` command.
MOOSE_PUT = 2

#: Symbolic constant for identifying the ``moo get`` command.
MOOSE_GET = 4

#: Symbolic constant for identifying the ``moo select`` command.
MOOSE_SELECT = 8

#: Symbolic constant for identifying the ``moo mdls`` command.
MOOSE_MDLS = 16

#: Symbolic constant for identifying the ``moo filter`` command.
MOOSE_FILTER = 32

#: Bit mask representing all MOOSE commands subject to service availability,
#: i.e. ls, mdls, get, select, put.
MOOSE_ALL = MOOSE_LS | MOOSE_PUT | MOOSE_GET | MOOSE_SELECT | MOOSE_MDLS

#: Symbolic constant for the MOOSE command-line interface.
MOOSE_CLI = 32768

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

#: Name of the MOOSE logger object.
MOOSE_LOGGER_NAME = 'afterburner.io.moose'

#: Default log level for the MOOSE logger object.
MOOSE_LOG_LEVEL = 'warn'

# MiBytes to Bytes conversion factor.
MIBYTES_TO_BYTES = 1024 * 1024

# Emulation mode settings.
# FOR DEVELOPER USE ONLY: REFER TO THE PRIVATE FUNCTIONS AT THE FOOT OF THIS MODULE.
_emulation_mode_flags = {
    'cli': None,
    'ls': None,
    'mdls': None,
    'get': None,
    'select': None,
    'put': None,
}


class MooseCommand(object):
    """
    Class for representing a MOOSE command, one that is potentially augmented
    with options specified via an environment variable of the form MOOSE_<subcommand>_OPTIONS,
    where <subcommand> is the capitalised name of one of the sub-commands supported
    by the MOOSE client command-line interface, e.g. 'MDLS', 'GET', 'PUT', etc.

    Here's a simple example of using this class:

    >>> import os
    >>> from afterburner.io.moose2 import MooseCommand
    >>> # the following variable would normally be set in the calling environment
    >>> os.environ['MOOSE_MDLS_OPTIONS'] = '--numberofatoms=200000'
    >>> moo_cmd = MooseCommand('mdls', options=['--sort=T1'], arguments=['qfile', 'uri'])
    >>> moo_cmd.raw_command
    'moo mdls --sort=T1 qfile uri'
    >>> moo_cmd.augmented_command
    'moo mdls --numberofatoms=200000 --sort=T1 qfile uri'
    """

    # Implementation Note: An alternative solution to employ here would involve
    # command-specific subclasses of this base class (e.g. MooseMdlsCommand),
    # each one overriding the augmented_command() property. A factory method could
    # then be used to create object instances. This would enable command-specific
    # and/or version-specific options to be handled in a well-defined manner.

    def __init__(self, sub_command, options=None, arguments=None, **kwargs):
        """
        :param str sub_command: The MOOSE client sub-command, e.g. 'select'.
        :param list options: An optional list of sub-command options.
        :param list arguments: An optional list of sub-command arguments.

        Extra Keyword Arguments (`**kwargs`):

        :param bool env_has_precedence: If set to True then command options
            specified via environment variables take precedence over equivalent
            options explicitly passed to this method, i.e. the former options
            are placed later in the command invocation. If undefined then the
            precedence is determined from the environment variable named
            MOOSE_ENV_HAS_PRECEDENCE if it is set, e.g. to 'true' or 'false'.
            Otherwise the default setting is False.
        """

        self._sub_command = sub_command
        self._options = options or []
        self._arguments = arguments or []
        self._raw_command = None
        self._augmented_command = None

        # Determine whether or not command options defined via environment
        # variables take precedence over equivalent ones specified via the
        # options keyword argument.
        if 'env_has_precedence' in kwargs:
            precedence = bool(kwargs['env_has_precedence'])
        else:
            precedence = is_true(os.environ.get('MOOSE_ENV_HAS_PRECEDENCE', 'false'))
        self.env_has_precedence = precedence

    def __str__(self):
        return self.augmented_command

    def __repr__(self):
        return "MooseCommand('{0}')".format(self.raw_command)

    @property
    def sub_command(self):
        """The MOOSE client sub-command, e.g. 'select'. (read-only)"""
        return self._sub_command

    @property
    def options(self):
        """A list of sub-command options. (read-only)"""
        return self._options

    @property
    def arguments(self):
        """A list of sub-command arguments. (read-only)"""
        return self._arguments

    @property
    def raw_command(self):
        """
        The raw MOOSE command as constructed from the arguments passed to the
        __init()__ method. (read-only)
        """
        if not self._raw_command:
            _command = "moo {0} {1} {2}".format(self.sub_command,
                ' '.join(self.options), ' '.join(self.arguments))
            self._raw_command = re.sub(' +', ' ', _command.strip())

        return self._raw_command

    @property
    def augmented_command(self):
        """
        The MOOSE command augmented with any options specified via the environment
        variable corresponding to that command, e.g. MOOSE_MDLS_OPTIONS in the
        case of the 'moo mdls' command. If no such variable has been defined then
        the value of this property is the same as given by the :attr:`raw_command`
        property. (read-only)

        .. note:: The environment is only examined the first time that this
           property is accessed. Any subsequent changes to the environment do
           not get reflected in the property's value.
        """
        if not self._augmented_command:
            var_name = "MOOSE_{0}_OPTIONS".format(self.sub_command.upper())
            var_value = os.environ.get(var_name)
            if var_value:
                if self.env_has_precedence:
                    _options = ' '.join(self.options + [var_value.strip()])
                else:
                    _options = ' '.join([var_value.strip()] + self.options)
                _command = "moo {0} {1} {2}".format(self.sub_command,
                    _options.strip(), ' '.join(self.arguments))
                self._augmented_command = re.sub(' +', ' ', _command.strip())
            else:
                self._augmented_command = self.raw_command

        return self._augmented_command


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
    # Check emulation mode setting for MOOSE cli.
    mode = _check_emulation_mode(MOOSE_CLI)
    if mode is not None: return mode

    try:
        subprocess.check_output(['moo', 'info'])
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def check_moose_commands_enabled(commands):
    """
    Check whether the specified MOOSE commands are currently enabled. The
    commands to check are specified as an OR'd combination of the MOOSE_*
    symbolic constants defined at the top of this module. For example:

    >>> result = check_moose_commands_enabled(moose2.MOOSE_LS|moose2.MOOSE_SELECT)

    :param int commands: The commands to check.
    :returns: True if the all of the specified MOOSE commands are currently
        enabled, otherwise False.
    :rtype: bool
    """
    # Check emulation mode setting for the specified commands.
    mode = _check_emulation_mode(commands)
    if mode is not None: return mode

    # the default return value is False
    ret_val = False

    if commands & MOOSE_LS:
        # redirect stderr so that if commands are disabled then all output is
        # hidden from the user. run_moose_command() isn't used as it would
        # result in additional output to the user.
        sp = subprocess.Popen(['moo', 'ls', 'moose:/'], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        status = sp.wait()
        if status != 0:
            return False
        else:
            ret_val = True

    if commands & (MOOSE_PUT | MOOSE_GET | MOOSE_SELECT | MOOSE_MDLS):
        try:
            status = run_moose_command('moo si -v')
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


def get_moose_logger():
    """Returns the logger object used by all moose2-related modules."""
    return logging.getLogger(MOOSE_LOGGER_NAME)


def get_moose_limits():
    """
    Get the limits from the MOOSE client that the MOOSE system currently
    imposes on get and put commands. The available options are defined in this
    module's symbolic constants. The values are returned as integers in a
    dictionary whose keys are the available options as strings. If the MOOSE
    client does not return a valid integer value for an option, then this
    option is omitted from the returned dictionary. Example usage:

    >>> moo_limits = get_moose_limits()
    >>> max_get = moo_limits[moose2.MOOSE_GET_MAX_FILES]
    >>> max_put = moo_limits[moose2.MOOSE_PUT_MAX_FILES]

    :returns: The limits stated above from the MOOSE client.
    :rtype: dict
    :raises afterburner.exceptions.MooseUnavailableError: If the MOOSE client
        isn't available.
    """
    limits = {}

    try:
        ret_val = run_moose_command('moo si -v')
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


def get_moose_version(controller=False):
    """
    Return the version number of either the MOOSE client interface, or the MOOSE
    controller if the keyword with that name is set to true. A ``Rel_`` prefix,
    if present, is removed from the version string prior to it being returned.

    :param bool controller: If set to true then return the version of the MOOSE
        controller instead of the MOOSE client.
    :returns: The version of the MOOSE client or controller, or an empty string
        if the version could not be determined.
    :raises afterburner.exceptions.MooseUnavailableError: Raised if the MOOSE
        service is unavailable.
    """
    try:
        ret_val = run_moose_command('moo si -v')
    except afterburner.exceptions.MooseUnavailableError:
        msg = 'The MOOSE interface is currently unavailable.'
        raise afterburner.exceptions.MooseUnavailableError(msg)

    if controller:
        pattern = r'Controller:\s+\S+\s+Revision:\s+(\S+)'
    else:
        pattern = r'Client:\s+\S+\s+Revision:\s+(\S+)'

    version = ''

    for line in ret_val:
        result = re.match(pattern, line)
        if result:
            version = result.group(1)
            break

    if version and version.startswith('Rel_'):
        version = version.partition('_')[-1]

    return version


def run_moose_command(command):
    """
    Run the specified MOOSE command and return any output sent to stdout or
    stderr as a list of strings.

    :param str command: Either the complete MOOSE command (string) to run or a
        MooseCommand instance object, in which case the command is obtained from
        the object's :meth:`augmented_command <MooseCommand.augmented_command>` property.
    :returns: Any text output from the command.
    :rtype: list of strings
    :raises afterburner.exceptions.MooseUnavailableError: If MOOSE is not
        currently available.
    :raises afterburner.exceptions.MooseCommandError: If the MOOSE command is
        not valid.
    """
    try:
        if isinstance(command, MooseCommand):
            command = command.augmented_command
        logger.debug("Running MOOSE command: %s", command)
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


def write_query_file(filename, files=None, stashcodes=None, time_range=None,
        levels=None, attributes=None, comment=None, **kwargs):
    """
    Write the file required for MOOSE record level retrievals.

    :param str filename: The full path name of the query file to write to.
    :param list files: A list of file names.
    :param list stashcodes: A list of STASH codes.
    :param tuple time_range: A tuple of date-time strings (T_start, T_end) to
        retrieve the data between. The strings should be in ISO 8601 format
        YYYY-MM-DD[Thh:mm[:ss]], e.g. 1980-07-31 or 1980-07-31T12:34.
        The header attribute ``T1`` is used for data selection, such that
        T_start <= T1 < T_end. Either of T_start or T_end, but not both, may be
        set to None or the empty string. In this case the corresponding T1 test
        condition will be omitted from the query file.
        For instantaneous data, all data points at or after T_start and before
        T_end are selected.
        For time-meaned data, all meaning periods *starting* at or after T_start
        and before T_end are selected.
    :param list levels: An optional list of model levels which may be used to
        add an "lblev=..." clause to the query file.
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
            numeric_stash = convert_msi_to_numeric(sc)
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
        if time_range[0]:
            pdt = pdt_from_date_string(time_range[0])
            fh.write('    T1>={{{0}}}\n'.format(_moose_date_string_from_pdt(pdt)))
        if time_range[1]:
            pdt = pdt_from_date_string(time_range[1])
            fh.write('    T1<{{{0}}}\n'.format(_moose_date_string_from_pdt(pdt)))

    if is_non_string_sequence(levels) and len(levels):
        if len(levels) == 1:
            fh.write('    lblev={0}\n'.format(levels[0]))
        else:
            fh.write('    lblev=({0})\n'.format(','.join([str(x) for x in levels])))

    pph_ivals = kwargs.get('pph_ivals')
    if isinstance(pph_ivals, dict):
        for k, v in pph_ivals.items():
            # client code must ensure that all dict values are of type integer
            fh.write('    {0}={1}\n'.format(k, v))

    fh.write('end\n')

    if attributes:
        fh.write('begin_attributes\n')
        for attr in attributes:
            fh.write(attr + '\n')
        fh.write('end_attributes\n')

    fh.close()


def convert_msi_to_numeric(msi):
    """
    Return the STASH code numeric string.

    :param str msi: The STASH code MSI string in the form `mXXsXXiXXX`.
    :returns: The STASH code numeric string.
    :rtype: str
    """
    stash_object = iris.fileformats.pp.STASH.from_msi(msi)
    numeric_stash = str(stash_object.section * 1000 + stash_object.item)
    return numeric_stash


def write_filter_file(filename, var_names=None, dims_and_coords=None,
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


def request_splitter(req_type, filenames, dirpath=None, file_limit=None,
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


class _ChunkSizeExceededError(Exception):
    """
    Raised when an attempt to split a list of items fails owing to an item being
    larger then the maximum chunk size/cost.
    """
    pass


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


### The functions below are intended for developer use only, and primarily for
### interactive testing purposes (mock typically being used for unit tests).


def _set_emulation_mode_flags(**kwargs):
    """
    Set one or more emulation mode flags, typically to one of None, 0/False, or
    1/True. For example, to emulate disabling the 'moo put' command, even when
    that command is up and running, use::

        _set_emulation_mode_flags(put=0)
    """
    for key in _emulation_mode_flags:
        if key in kwargs:
            _emulation_mode_flags[key] = kwargs[key]


def _reset_emulation_mode_flags():
    """Reset emulation mode flags to default settings, i.e. None."""
    for key in _emulation_mode_flags:
        _emulation_mode_flags[key] = None


def _check_emulation_mode(commands):
    """
    Check the emulation mode for the MOOSE commands defined by the ``commands``
    bitmask. If the emulation mode of *any* command evaluates to False (but not
    None), then the function returns False. If the emulation mode of *all*
    commands evaluates to True, then the function returns True. Otherwise None
    is returned.
    """
    # If the CLI is disabled then assume that no other commands are available.
    mode = _emulation_mode_flags.get('cli')
    if mode is not None:
        if not mode:
            # CLI disabled
            return False
        elif commands == MOOSE_CLI:
            # CLI enabled and no other commands need checking
            return True

    # Check each command in turn, returning False if any one is explicitly
    # disabled.
    modes = []
    for cmd, mode in _emulation_mode_flags.items():
        if cmd == 'cli': continue
        bitmask = globals().get('MOOSE_'+cmd.upper(), 0)
        if commands & bitmask:
            if mode is not None and not mode:
                return False
            modes.append(mode)

    if len(modes) and all(modes):
        # all commands enabled
        return True
    else:
        # 1 or more commands undefined
        return None


def _init_moose_logger():
    """Initialise a logger object for use by all moose2-related modules."""
    logger = logging.getLogger(MOOSE_LOGGER_NAME)
    level_name = os.environ.get('MOOSE_LOG_LEVEL', MOOSE_LOG_LEVEL)
    level = getattr(logging, level_name.upper(), logging.WARN)
    logger.setLevel(level)
    return logger


logger = _init_moose_logger()
