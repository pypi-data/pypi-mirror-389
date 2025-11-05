# (C) British Crown Copyright 2019-2020, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
**Index of Classes in this Module**

.. autosummary::
   :nosignatures:

   ModelEmulator
   UmEmulator
   NemoEmulator
   CiceEmulator

The model_emulators module defines classes which can be used to emulate the
the generation of data by a numerical climate model, such the Unified Model or
the NEMO ocean model. The main purpose of the emulators is for software testing,
and more especially for those occasions when it is desirable to emulate the
availability on disk of data files for a particular model cycle point, or range
of cycle points.

The emulators operate in a simplistic manner by copying (or linking) data files
for a specified combination of suite, stream, diagnostic and time period from a
source directory to a destination directory. Typically the data in the source
directory will have been placed there either directly as a result of a model run,
or as a result of a retrieval request from a long-term data store (such as the
MASS archive).

The required set of model data files to serve up is determined from the
combination of input parameters specifying the target suite id, realization
id (optional), stream id, variable id, and time period. Other parameters are
required for some models (e.g. a grid type in the case of NEMO models). These
parameters can be specified on the command-line, within a Rose app config file,
or a combination of the two. Command-line arguments take precedence over values
defined in an app config file.

A sample Rose app config file showing the core options currently supported by
the model emulator classes is illustrated below (for a UM example use-case):

.. code-block:: ini

    [data_cache]
    cache_scheme=VarSplit
    base_dir=/data/users/mary/modeldata/varsplit
    datastore_id=
    read_only=true

    [data_reader]
    source_type=data_cache
    input_dir=

    [data_request]
    suite_id=anqjm
    realization_id=
    stream_id=apy
    variable_id=m01s00i024   # can be '*' in the case of whole-stream data files
    start_date=
    end_date=
    calendar=360_day
    grid_type=T
    pp_vn=1.0
    reinit=

    [general]
    dest_dir=/place/to/put/emulated/files
    update_only=false
    use_sentinel_files=true
    use_symlinks=true

    [sentinel_files]
    dest_dir=/place/to/put/sentinel/files
    extension=.arch
    mode=replace
    remove_old_files=true

Most of the options available under the ``[general]`` and ``[data_request]``
sections of the config file can be overridden by equivalent command-line options,
as shown below for the UmEmulator class::

    usage: UmEmulator [-h] [-V] [-D | -q | -v] [-c CONFIG_FILE] [-n]
                      [--dest-dir DEST_DIR] [--expected-files] [--update-only]
                      [--use-sentinel-files] [--use-symlinks]
                      [--suite-id SUITE_ID] [--stream-id STREAM_ID]
                      [--realization-id REALIZATION_ID]
                      [--variable_id VARIABLE_ID] [--start-date START_DATE]
                      [--end-date END_DATE] [--calendar CALENDAR] [--pp-vn PP_VN]
                      [--reinit REINIT]

    UmEmulator: Unified Model Emulator: emulates the generation of data by the UM
    atmosphere model

    optional arguments:
      -h, --help            show this help message and exit
      -V, --version         Show Afterburner version number and exit
      -D, --debug           Enable debug message mode
      -q, --quiet           Enable quiet message mode
      -v, --verbose         Enable verbose message mode
      -c CONFIG_FILE, --config-file CONFIG_FILE
                            Pathname of the app configuration file
      -n, --dry-run         Dry-run only: prints names of generated files
      --dest-dir DEST_DIR   Destination directory
      --expected-files      List expected files (in dry-run mode only)
      --update-only         Only update out-of-date or non-existent files in dest-dir
      --use-sentinel-files  Use sentinel files to mark emulated files
      --use-symlinks        Use symbolic links to point to original data files
      --suite-id SUITE_ID   Suite name/id (e.g. u-ab123)
      --stream-id STREAM_ID
                            Stream ID (e.g. apy)
      --realization-id REALIZATION_ID
                            Realization ID (e.g. r1i2p3)
      --variable_id VARIABLE_ID
                            STASH code or variable name (can be set to '*')
      --start-date START_DATE
                            Start date in format YYYY-MM-DD[Thhmmss]
      --end-date END_DATE   End date in format YYYY-MM-DD[Thhmmss]
      --calendar CALENDAR   Calendar type (e.g. 360_day)
      --pp-vn PP_VN         Postproc version number
      --reinit REINIT       Stream reinitialisation period in days

Typically the start and end date values are specified via the command line, with
different values being used to encompass successive contiguous time periods.
Here's an example invocation that uses the ``abrun.sh`` wrapper script to instantiate
and run the :class:`UmEmulator` class. It includes  the ``--use-symlinks`` option
so as to create symbolic links to the original data files, as opposed to creating
copies of those files:

.. code-block:: console

    % abrun.sh UmEmulator -c rose-app.conf --use-symlinks --start=1970-12-01 --end=1980-12-01
    ln -s /my/source/datadir/anqjma.py19711201.pp <dest-dir>/anqjma.py19711201.pp
    ...
    ln -s /my/source/datadir/anqjma.py19801201.pp <dest-dir>/anqjma.py19801201.pp

It should be noted that the model emulators do not currently perform any house-
keeping tasks after the emulated data files have been generated. It is the
responsibility of client programs to carry out any tidy-up work after the files
have been utilised.
"""
# pylint: disable=E1101

from __future__ import (absolute_import, division, print_function)

import os
import abc
import glob
import shutil
import datetime

try:
    # The abstractproperty decorator was deprecated at Python 3.3
    from abc import abstractproperty
except ImportError:
    abstractproperty = lambda f: property(abc.abstractmethod(f))

from six.moves import (filter, input, map, range, zip)
from six import add_metaclass

from afterburner.apps import AbstractApp
from afterburner.exceptions import (AfterburnerError, AppConfigError)
from afterburner.filename_providers import FilenameProvider
from afterburner.metavar import UmMetaVariable, NemoMetaVariable, CiceMetaVariable
from afterburner.io.datacaches import DataCache
from afterburner.io.datastores import DataStore, NullDataStore
from afterburner.utils import is_true, NamespacePlus
from afterburner.utils.fileutils import expand_path, restore_cwd
from afterburner.utils.textutils import decode_string_value

# IDs of sections and namelists used in the application configuration file.
GENERAL_SECTION = 'general'
DATA_CACHE_SECTION = 'data_cache'
DATA_READER_SECTION = 'data_reader'
DATA_REQUEST_SECTION = 'data_request'
SENTINEL_FILE_SECTION = 'sentinel_files'


@add_metaclass(abc.ABCMeta)
class ModelEmulator(AbstractApp):
    """
    Emulates the generation of stream-based diagnostic data by a climate model
    for a specified time period, e.g. for a particular model time step or cycle
    point.
    """

    # Define command-line arguments common to all emulators.
    _common_cli_args = [
        {'names': ['-c', '--config-file'], 'required': True,
            'help': 'Pathname of the app configuration file'},
        {'names': ['-n', '--dry-run'], 'action': 'store_true',
            'help': 'Dry-run only: prints names of generated files'},
        {'names': ['--dest-dir'], 'help': 'Destination directory'},
        {'names': ['--expected-files'], 'action': 'store_true',
            'help': 'List expected files (in dry-run mode only)'},
        {'names': ['--update-only'], 'action': 'store_true',
            'help': 'Only update out-of-date or non-existent files in dest-dir'},
        {'names': ['--use-sentinel-files'], 'action': 'store_true',
            'help': 'Use sentinel files to mark emulated files'},
        {'names': ['--use-symlinks'], 'action': 'store_true',
            'help': 'Use symbolic links to point to original data files'},
        {'names': ['--suite-id'],  'help': 'Suite name/id (e.g. u-ab123)'},
        {'names': ['--stream-id'], 'help': 'Stream ID (e.g. apy)'},
        {'names': ['--realization-id'], 'help': 'Realization ID (e.g. r1i2p3)'},
        {'names': ['--variable_id'], 'help': 'STASH code or variable name'},
        {'names': ['--start-date'], 'help': 'Start date in format YYYY-MM-DD[Thhmmss]'},
        {'names': ['--end-date'], 'help': 'End date in format YYYY-MM-DD[Thhmmss]'},
        {'names': ['--calendar'], 'help': 'Calendar type (e.g. 360_day)'},
    ]

    def __init__(self, arglist=None, **kwargs):
        """
        :param list arglist: List of raw options and/or arguments passed from the
            calling environment. Typically these will be unprocessed command-line
            arguments, e.g. ``['-f', 'foo', '--foe=fum', 'infile']``.
        """
        super(ModelEmulator, self).__init__(arglist=arglist, **kwargs)

        # Obtain the app name from the name of the concrete subclass.
        self.app_name = self.__class__.__name__

        # Parse command-line arguments and read app configuration information
        # from a Rose configuration file.
        desc = kwargs.get('description', 'app description')
        self._parse_args(arglist, desc="{0}: {1}".format(self.app_name, desc))
        self._parse_args(arglist, desc="Model Emulator: emulates the "
            "generation of data by a climate model.")
        self._parse_app_config()

        # Ensure that messages are visible when in dry-run mode.
        if self.cli_args.dry_run and not self.cli_args.debug:
            self.cli_args.verbose = True

        # Set the message/logging level according to standard CLI args, if set.
        self._set_message_level()
        self.logger.info("Initialising %s app...", self.app_name)

        self.general_opts = None
        self.data_cache_opts = None
        self.data_reader_opts = None
        self.data_request_opts = None

        self.data_cache = None
        self.metavar = None

        # Read app config options.
        try:
            self._get_app_config_options()
        except:
            self.logger.error("Problem parsing app config file options.")
            raise

    @abstractproperty
    def cli_spec(self):
        """
        Defines the command-line interface specification for the application.
        """
        raise NotImplementedError()

    def run(self, *args, **kwargs):
        """
        Runs the application.
        """
        self.logger.info("Running %s app...", self.app_name)

        self.metavar = self._create_metavariable()
        self.logger.info("Requested dataset: %s", self.metavar)
        self.logger.info("Destination directory: %s", self.general_opts.dest_dir)

        filenames = self._fetch_files()

        if self.general_opts.use_sentinel_files:
            self._manage_sentinel_files(filenames)

        self.logger.info("\n%s app completed successfully.", self.app_name)

    def _fetch_files(self):
        """
        Fetch all files that match the data request specified via a combination
        of app config file options and command-line arguments. The latter take
        precedence.

        :returns: A list, possibly empty, of the names of new data files copied
            to or linked from the destination directory.
        """

        dry_run = self.cli_args.dry_run
        dest_dir = self.general_opts.dest_dir
        update_only = self.general_opts.update_only
        use_symlinks = self.general_opts.use_symlinks

        # Obtain a list of actual files present in the data cache.
        expected = self.cli_args.expected_files if dry_run else False
        filepaths = self.data_cache.get_filepaths([self.metavar], sort=True,
            expected=expected)
        filenames = []

        if not filepaths:
            self.logger.info("No files matching the input criteria were found "
                "in the source directory.")
            return filenames

        if not os.path.exists(dest_dir):
            try:
                self.logger.info("Creating directory %s", dest_dir)
                os.makedirs(dest_dir)
            except OSError:
                self.logger.error("Unable to create directory %s.\n"
                    "Please check your filesystem permissions.", dest_dir)
                raise

        if dry_run:
            action = 'linked from' if use_symlinks else 'copied to'
            self.logger.info("\n[dry-run] The following files would get %s "
                "the destination directory...", action)
        else:
            action = 'links' if use_symlinks else 'copies'
            self.logger.info("\n[wet-run] Creating file %s in the destination "
                "directory...", action)

        # TODO: add support for preserving original file mod times?

        if use_symlinks:
            nfiles = 0
            with restore_cwd(dest_dir):
                for src in filepaths:
                    linkname = os.path.basename(src)
                    if os.path.islink(linkname) and os.path.samefile(linkname, src):
                        # valid symbolic link exists in dest_dir
                        continue
                    if dry_run:
                        self.logger.info("[dry-run] ln -s %s <dest-dir>/%s", src, linkname)
                    else:
                        if os.path.islink(linkname) or os.path.isfile(linkname):
                            self.logger.info("[wet-run] rm %s", linkname)
                            os.remove(linkname)
                        self.logger.info("[wet-run] ln -s %s <dest-dir>/%s", src, linkname)
                        os.symlink(src, linkname)
                    filenames.append(linkname)
                    nfiles += 1

        else:
            nfiles = 0
            for src in filepaths:
                if update_only and _is_dest_up_to_date(src, dest_dir):
                    # file exists in dest_dir and is up-to-date
                    continue
                if dry_run:
                    self.logger.info("[dry-run] cp %s <dest-dir>", src)
                else:
                    self.logger.info("[wet-run] cp %s <dest-dir>", src)
                    shutil.copy(src, dest_dir)
                filenames.append(os.path.basename(src))
                nfiles += 1

        return filenames

    def _manage_sentinel_files(self, filenames):
        """
        Create sentinel files for the supplied list of filenames, which should
        have been newly copied to/linked from the destination directory.

        :param list filenames: A list of the filenames that were copied/linked
            by the fetch_files method.
        """

        if not filenames:
            return

        dry_run = self.cli_args.dry_run
        dest_dir = self.sentinel_file_opts.dest_dir
        sent_ext = self.sentinel_file_opts.ext

        with restore_cwd(dest_dir):

            # Remove old sentinel files if requested.
            if self.sentinel_file_opts.remove_old_files:
                filepatn = _get_timeless_file_basename(self.metavar)
                filepatn += '*' + sent_ext
                self.logger.debug("Sentinel filename pattern: %s", filepatn)
                old_files = glob.glob(filepatn)
                if old_files and dry_run:
                    self.logger.info("\n[dry-run] The following old sentinel files "
                        "would get deleted from the destination directory.")

                for fname in old_files:
                    if dry_run:
                        self.logger.info("[dry-run] rm <dest-dir>/%s", fname)
                    else:
                        self.logger.info("rm %s", fname)
                        os.remove(fname)

            if dry_run:
                self.logger.info("\n[dry-run] The following new sentinel files would "
                    "get created within the destination directory.")

            # Create a new sentinel file for each filename.
            for fname in filenames:
                if self.sentinel_file_opts.ext_mode == 'replace':
                    # replace an existing extension, if one is present
                    sent_file = os.path.splitext(fname)[0] + sent_ext
                else:
                    # otherwise simply append the sentinel file extension
                    sent_file = fname + sent_ext

                if not os.path.exists(sent_file):
                    if dry_run:
                        self.logger.info("[dry-run] touch <dest-dir>/%s", sent_file)
                    else:
                        self.logger.info("touch <dest-dir>/%s", sent_file)
                        os.system('touch ' + sent_file)   # UN*X only!

    def _get_app_config_options(self):
        """
        Read all sections from the app config file.
        """
        self.logger.debug("Reading app config file...")

        self.general_opts = self._get_general_options()
        self.sentinel_file_opts = self._get_sentinel_file_options()
        self.data_request_opts = self._get_data_request_options()
        self.data_reader_opts = self._get_data_reader_options()
        self.data_cache_opts = self._get_data_cache_options()

        # If the user has requested a single source directory then set the
        # data cache options accordingly.
        if self.data_reader_opts.source_type == 'single_directory':
            self.data_cache_opts.cache_scheme = 'SingleDirectory'
            self.data_cache_opts.base_dir = self.data_reader_opts.input_dir
            self.data_cache_opts.datastore_id = None
            self.data_cache_opts.read_only = True

        # Set up access to the source data cache.
        self._setup_data_cache()

    def _get_general_options(self):
        """
        Read general application options from the app config file.
        This section should contain the following options::

            [general]
            dest_dir=<dir-path>
            update_only=<true-or-false>
            use_sentinel_files=<true-or-false>
            use_symlinks=<true-or-false>

        :returns: An afterburner.utils.NamespacePlus object whose attributes
            record options defined under the [general] section of the app config
            file.
        """

        general_opts = _read_app_config_section(self.app_config, GENERAL_SECTION)

        dest_dir = self.cli_args.dest_dir or general_opts.dest_dir
        if not dest_dir:
            msg = ("A destination directory has not been specified, either via\n"
                "the --dest-dir argument or the [general]dest_dir config option.")
            self.logger.error(msg)
            raise AppConfigError(msg)
        general_opts.dest_dir = expand_path(dest_dir)

        general_opts.update_only = self.cli_args.update_only \
            or is_true(general_opts.update_only)

        general_opts.use_symlinks = self.cli_args.use_symlinks or \
            is_true(general_opts.use_symlinks)

        general_opts.use_sentinel_files = self.cli_args.use_sentinel_files or \
            is_true(general_opts.use_sentinel_files)

        return general_opts

    def _get_sentinel_file_options(self):
        """
        Read options from the [sentinel_files] section of the app config file.
        This section should contain the following options::

            [sentinel_files]
            dest_dir=<dir-path>
            ext=<.ext>
            ext_mode=<append-or-replace>
            remove_old_files=<true-or-false>

        :returns: An afterburner.utils.NamespacePlus object whose attributes
            record options defined under the [data_cache] section of the app
            config file.
        """

        sent_file_opts = _read_app_config_section(self.app_config, SENTINEL_FILE_SECTION)

        if not sent_file_opts.dest_dir:
            sent_file_opts.dest_dir = self.general_opts.dest_dir

        if not sent_file_opts.ext:
            sent_file_opts.ext = '.arch'

        if not sent_file_opts.ext_mode:
            sent_file_opts.ext_mode = 'replace'

        sent_file_opts.remove_old_files = is_true(sent_file_opts.remove_old_files)

        return sent_file_opts

    def _get_data_cache_options(self):
        """
        Read options from the [data_cache] section of the app config file.
        This section should contain the following options::

            [data_cache]
            cache_scheme=<scheme-name>    # e.g. SingleDirectory or StreamSplit
            base_dir=<dir-path>
            datastore_id=<datastore-id>   # Usually blank
            read_only=<true-or-false>

        :returns: An afterburner.utils.NamespacePlus object whose attributes
            record options defined under the [data_cache] section of the app
            config file.
        """

        cache_opts = _read_app_config_section(self.app_config, DATA_CACHE_SECTION)
        cache_opts.read_only = is_true(cache_opts.read_only)

        return cache_opts

    def _get_data_reader_options(self):
        """
        Read options from the [data_reader] section of the app config file.
        This section should contain the following options::

            [data_reader]
            source_type=<type>      # single_directory or data_cache
            input_dir=<dir-path>    # path of single source directory

        :returns: An afterburner.utils.NamespacePlus object whose attributes
            record options defined under the [data_reader] section of the app
            config file.
        """

        reader_opts = _read_app_config_section(self.app_config, DATA_READER_SECTION)

        if reader_opts.source_type not in ['single_directory', 'data_cache']:
            msg = ("Unsupported value specified for the [data_reader]source_type "
                "option: {}".format(reader_opts.source_type))
            self.logger.error(msg)
            raise AppConfigError(msg)

        return reader_opts

    def _get_data_request_options(self):
        """
        Read options from the [data_request] section of the app config file.
        This section may contain some or all of the following options (depending
        upon the type of model being emulated)::

            [data_request]
            suite_id=
            realization_id=
            stream_id=
            variable_id=
            start_date=
            end_date=
            calendar=
            grid_type=
            pp_vn=
            reinit=

        :returns: An afterburner.utils.NamespacePlus object whose attributes
            record options defined under the [data_reader] section of the app
            config file.
        """

        request_opts = _read_app_config_section(self.app_config, DATA_REQUEST_SECTION)

        # Override app config file values with CLI values, if any are set.
        for att_name in ['suite_id', 'realization_id', 'stream_id', 'variable_id',
            'start_date', 'end_date', 'calendar', 'grid_type', 'pp_vn', 'reinit']:
            cli_val = getattr(self.cli_args, att_name, None)
            if cli_val is not None:
                setattr(request_opts, att_name, cli_val)

        return request_opts

    def _setup_data_cache(self):
        """
        Set up a connection to the input data cache, if one has been specified
        under the [data_cache] section of the app config file.
        """
        try:
            opts = vars(self.data_cache_opts).copy()
            scheme = opts.pop('cache_scheme', '')
            if not scheme:
                raise AppConfigError("The [data_cache]cache_scheme option is "
                    "not defined in the app config file.")
            base_dir = opts.pop('base_dir')
            dstore_id = opts.pop('datastore_id', '')
            access = 'read-only' if opts.get('read_only') else 'read-write'
            if dstore_id:
                datastore = DataStore.create_store(dstore_id)
            else:
                datastore = NullDataStore()
            self.logger.info("Configuring %s access to %s data cache rooted at %s ...",
                access, scheme, base_dir)
            dcache = DataCache.create_cache(scheme, datastore, base_dir, **opts)
            self.data_cache = dcache
        except AfterburnerError:
            self.logger.error("Problem trying to set up a data cache object.")
            raise

    @abc.abstractmethod
    def _create_metavariable(self):
        """
        Construct a :class:`afterburner.metavar.MetaVariable` object from relevant
        attributes of the requested dataset.
        """
        raise NotImplementedError()


class UmEmulator(ModelEmulator):
    """
    Emulates the generation of Unified Model output. Refer to the module docstring
    for an overview of how to configure and run instances of this class.
    """

    def __init__(self, arglist=None, **kwargs):
        """
        :param list arglist: List of raw options and/or arguments passed from the
            calling environment. Typically these will be unprocessed command-line
            arguments, e.g. ``['-f', 'foo', '--foe=fum', 'infile']``.
        """
        super(UmEmulator, self).__init__(arglist=arglist, version='1.0.0b1',
            description="Unified Model Emulator: emulates the generation of data "
            "by the UM atmosphere model", **kwargs)

    @property
    def cli_spec(self):
        """
        Defines the command-line interface specification for the application.
        """
        cmd_args = [
            {'names': ['--pp-vn'], 'help': 'Postproc version number'},
            {'names': ['--reinit'], 'type': int,
                'help': 'Stream reinitialisation period in days'},
        ]

        return self._common_cli_args + cmd_args

    def _create_metavariable(self):
        """
        Construct a :class:`afterburner.metavar.UmMetaVariable` object from relevant
        attributes of the requested dataset.
        """

        req = self.data_request_opts

        if not _is_um_stream(req.stream_id):
            raise AppConfigError("Stream '%s' is not a recognised UM stream."
                % req.stream_id)

        model_vn = req.model_vn or '0'
        stash_code = req.variable_id or '*'
        if stash_code == '*': stash_code = 'm00s00i000'   # dummy STASH code
        time_range = (req.start_date, req.end_date)

        try:
            reinit = int(req.reinit)
        except (TypeError, ValueError):
            # Guess the reinitialisation period based on the stream id. Set to
            # 30 days for ap[a-k] and ap[1-9] streams.
            reinit = 30 if req.stream_id[-1] < 'l' else 0
            self.logger.debug("No stream reinitialisation period specified; "
                "using %d based on stream ID", reinit)

        var = UmMetaVariable(model_vn, req.suite_id, realization_id=req.realization_id,
            stream_id=req.stream_id, stash_code=stash_code, time_range=time_range,
            calendar=req.calendar, reinit=reinit)

        return var


class NemoEmulator(ModelEmulator):
    """
    Emulates the generation of NEMO model output. Refer to the module docstring
    for an overview of how to configure and run instances of this class.
    """

    def __init__(self, arglist=None, **kwargs):
        """
        :param list arglist: List of raw options and/or arguments passed from the
            calling environment. Typically these will be unprocessed command-line
            arguments, e.g. ``['-f', 'foo', '--foe=fum', 'infile']``.
        """
        super(NemoEmulator, self).__init__(arglist=arglist, version='1.0.0b1',
            description="NEMO Model Emulator: emulates the generation of data "
            "by the NEMO ocean model", **kwargs)

    @property
    def cli_spec(self):
        """
        Defines the command-line interface specification for the application.
        """
        cmd_args = [
            {'names': ['--grid-type'], 'help': 'Grid type [T,U,V,W]'},
            {'names': ['--pp-vn'], 'help': 'Postproc version number'},
        ]

        return self._common_cli_args + cmd_args

    def _create_metavariable(self):
        """
        Construct a :class:`afterburner.metavar.NemoMetaVariable` object from relevant
        attributes of the requested dataset.
        """

        req = self.data_request_opts

        if not _is_nemo_stream(req.stream_id):
            raise AppConfigError("Stream '%s' is not a recognised NEMO stream."
                % req.stream_id)

        model_vn = req.model_vn or '0'
        var_name = req.variable_id or '*'
        if var_name == '*': var_name = 'undefined'   # dummy variable name
        time_range = (req.start_date, req.end_date)

        var = NemoMetaVariable(model_vn, req.suite_id, realization_id=req.realization_id,
            stream_id=req.stream_id, var_name=var_name, time_range=time_range,
            calendar=req.calendar, grid_type=req.grid_type, postproc_vn=str(req.pp_vn))

        return var


class CiceEmulator(ModelEmulator):
    """
    Emulates the generation of CICE model output. Refer to the module docstring
    for an overview of how to configure and run instances of this class.
    """

    def __init__(self, arglist=None, **kwargs):
        """
        :param list arglist: List of raw options and/or arguments passed from the
            calling environment. Typically these will be unprocessed command-line
            arguments, e.g. ``['-f', 'foo', '--foe=fum', 'infile']``.
        """
        super(CiceEmulator, self).__init__(arglist=arglist, version='1.0.0b1',
            description="CICE Model Emulator: emulates the generation of data "
            "by the CICE sea-ice model", **kwargs)

    @property
    def cli_spec(self):
        """
        Defines the command-line interface specification for the application.
        """
        cmd_args = [
            {'names': ['--grid-type'], 'help': 'Grid type [T,U,V,W]'},
            {'names': ['--pp-vn'], 'help': 'Postproc version number'},
        ]

        return self._common_cli_args + cmd_args

    def _create_metavariable(self):
        """
        Construct a :class:`afterburner.metavar.CiceMetaVariable` object from relevant
        attributes of the requested dataset.
        """

        req = self.data_request_opts

        if not _is_cice_stream(req.stream_id):
            raise AppConfigError("Stream '%s' is not a recognised CICE stream."
                % req.stream_id)

        model_vn = req.model_vn or '0'
        var_name = req.variable_id or '*'
        if var_name == '*': var_name = 'undefined'   # dummy variable name
        time_range = (req.start_date, req.end_date)

        var = CiceMetaVariable(model_vn, req.suite_id, realization_id=req.realization_id,
            stream_id=req.stream_id, var_name=var_name, time_range=time_range,
            calendar=req.calendar, grid_type=req.grid_type, postproc_vn=str(req.pp_vn))

        return var


def _get_timeless_file_basename(metavar):
    """
    Obtain the base part of the filename corresponding to the specified metavariable,
    one who's start and end times are temporarily set to null.
    """

    tmpvar = metavar.copy()
    tmpvar.time_range = None
    fnprov = FilenameProvider.from_metavar(tmpvar)

    it = fnprov.iter_filenames(tmpvar)
    filename = next(it)

    return filename.partition('*')[0]


def _is_um_stream(stream_id):
    """Returns True if stream_id refers to data from a UM stream."""
    return stream_id[0] == 'a'


def _is_nemo_stream(stream_id):
    """Returns True if stream_id refers to data from a NEMO stream."""
    return stream_id[0] == 'o'


def _is_cice_stream(stream_id):
    """Returns True if stream_id refers to data from a CICE stream."""
    return stream_id[0] == 'i'


def _is_dest_up_to_date(src, dest_dir):
    """
    Test to see if the file specified by src exists in dest_dir and has the
    same (or later) modification time. If so, return true. Otherwise return
    false.
    """
    dst = os.path.join(dest_dir, os.path.basename(src))
    if os.path.exists(dst):
        st = os.stat(src)
        src_mtime = datetime.datetime.fromtimestamp(st.st_mtime)
        st = os.stat(dst)
        dst_mtime = datetime.datetime.fromtimestamp(st.st_mtime)
        return dst_mtime >= src_mtime

    return False


def _read_app_config_section(app_config, section):
    """Read all of the options within a section of the app config file."""

    try:
        ddict = app_config.section_to_dict(section)
        ddict = {k: decode_string_value(v) for k, v in ddict.items()}
        return NamespacePlus(**ddict)
    except ValueError:
        raise AppConfigError("Unable to find a section named '{0}' in the "
            "app config file".format(section))
