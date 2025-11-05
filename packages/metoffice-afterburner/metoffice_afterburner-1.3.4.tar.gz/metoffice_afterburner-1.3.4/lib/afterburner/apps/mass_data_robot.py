# (C) British Crown Copyright 2017-2020, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
This module contains an implementation of the Mass Data Robot application, which
provides functionality for batch retrievals of data from the MASS data archive.

Refer to the :class:`MassDataRobot` class for further information.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import os
import re
import sys
import pprint
import logging
import cf_units
import itertools
import subprocess
import multiprocessing as mp

import afterburner.io.moose2 as moose
from afterburner.apps import AbstractApp
from afterburner.utils import NamespacePlus
from afterburner.utils.fileutils import expand_path
from afterburner.utils.dateutils import moose_date_to_iso_date
from afterburner.io.datastores import MassDataStore
from afterburner.io.datacaches import (DataCache,
    VAR_SPLIT_SCHEME, ENSEMBLE_VAR_SPLIT_SCHEME,
    STREAM_SPLIT_SCHEME, ENSEMBLE_STREAM_SPLIT_SCHEME)
from afterburner.metavar import UmMetaVariable, NemoMetaVariable, CiceMetaVariable
from afterburner.modelmeta import is_msi_stash_code
from afterburner.filename_providers import FilenameProvider
from afterburner.exceptions import (DataProcessingError, MooseUnsupportedError,
    MooseUnavailableError, AppConfigError, AppRuntimeError)

# MOOSE read-only flags.
MOOSE_READ = moose.MOOSE_GET | moose.MOOSE_SELECT

# Maximum number of MOOSE data requests.
MAX_MOOSE_DATA_REQUESTS = os.environ.get('MAX_MOOSE_DATA_REQUESTS', 100)

# Maximum number of source URIs to pass to a single MOOSE command.
# The default setting below is on the low side: it should be feasible to cope
# with 1,000 or even 10,000 URIs.
MAX_URIS_PER_MOOSE_COMMAND = os.environ.get('MAX_URIS_PER_MOOSE_COMMAND', 100)

# Application return codes.
RETCODE_ABORT_ON_ERROR = 2    #: Abort-on-error return code

# Integer PP header words supported in request definitions.
SUPPORTED_PPH_IVALS = ['lbtim', 'lbproc']

# Create a logger object.
_logger = logging.getLogger(__name__)


class MassDataRobot(AbstractApp):
    """
    This class implements the Mass Data Robot application, which provides the
    capability to configure and execute multiple data retrieval requests against
    the MASS data archive.

    Two modes of task execution are currently supported: parallel (the default),
    and in series. Parallel execution mode is currently achieved using Python's
    `multiprocessing <https://docs.python.org/2.7/library/multiprocessing.html>`_
    module. It is hoped that a future version of the application will exploit
    cylc's task scheduling features.

    The Mass Data Robot application (MDR app, for short) is configured using an
    app config file, the layout of which conforms to Rose's extended INI format.
    The config file contains 4 main sections: general, moose, data_caches, and
    requests.

    The first two sections permit the setting of general application options and
    of MOOSE-specific options. The last two sections are used to specify data
    cache definitions and composite MASS data requests. Both sections are managed
    as namelists so as to make it convenient to add new definitions.

    The MDR app expands the *composite* data requests into discrete data requests
    which can be handed off to the MOOSE command-line interface. For example,
    the following fictional composite data request, if defined within an app
    config file, would result in 4 separate MOOSE data requests::

        [namelist:requests(1)]
        data_class=crum
        data_sets=mi-ab123,mi-cd234
        data_collections=apy.pp,aps.pp
        variables=*

    The resulting MOOSE data requests would target the following MASS URIs:

    - crum/mi-ab123/apy.pp/*
    - crum/mi-ab123/aps.pp/*
    - crum/mi-cd234/apy.pp/*
    - crum/mi-cd234/aps.pp/*

    The model data files retrieved by requests such as these are stored within
    an on-disk data cache, which must adhere to one of the cache schemes recognised
    by the Afterburner library. Different data requests can target different
    data cache areas on disk.

    Full details on configuring data requests and data cache definitions, and on
    setting the various application options, can be found in the documentation
    for the MDR app -- see :doc:`/rose_apps/mass_data_robot/guide`.
    """

    def __init__(self, arglist=None, **kwargs):
        """
        :param list arglist: List of raw options and/or arguments passed from the
            calling environment. Typically these will be unprocessed command-line
            arguments, e.g. ``['-f', 'foo', '--foe=fum', 'infile']``.
        """
        super(MassDataRobot, self).__init__(version='1.0.0b3', **kwargs)

        # Parse command-line arguments and read app configuration information
        # from a Rose configuration file.
        self._parse_args(arglist, desc="MASS Data Robot: retrieve model data "
            "from the MASS data archive.")
        self._parse_app_config()

        self._set_message_level()
        self.logger.info("Initialising MassDataRobot app...")

        if not self.cli_args.dry_run:
            self._check_moose_support()

        self.app_options = self._read_app_options()

        self.moose_options = self._read_moose_options()

        self.cache_defns = self._read_cache_definitions()

        self.raw_requests = self._read_request_definitions()

        self.atomic_requests = None

        # Dictionary to store handles to data caches.
        self.data_caches = {}

    @property
    def cli_spec(self):
        """Defines the command-line interface specification for the application."""
        return [
            {'names': ['-n', '--dry-run'], 'action': 'store_true',
                'help': 'Dry-run only: echoes but does not run MOOSE commands'},
            {'names': ['--no-teardown'], 'action': 'store_true',
                'help': 'Skip final teardown operations (overrides config file setting)'},
            {'names': ['--pmode'], 'dest': 'parallel_mode',
                'choices': ['pymp', 'none'],
                'help': 'Specify parallel mode (overrides config file setting)'},
            {'names': ['-c', '--config-file'], 'required': True,
                'help': 'Pathname of app configuration file'},
        ]

    def run(self):
        """
        Runs the Mass Data Robot application.

        If the ``abort_on_error`` app configuration option is enabled, and an
        error is encountered during a MASS data retrieval operation, then the
        application exits immediately. The ``returncode`` attribute is set to
        :data:`RETCODE_ABORT_ON_ERROR`, the value of which is passed up to the calling
        program.
        """
        self.logger.info("Running MassDataRobot app...")

        if not self.cli_args.dry_run:
            try:
                self._check_moose_status()
            except MooseUnavailableError:
                return

        self._create_runtime_directories()

        self._setup_data_caches()

        self._create_atomic_request_definitions()

        self._make_moose_commands()

        self._create_task_scripts()

        try:
            if self.app_options['parallel_mode'] == 'cylc':
                run_aborted = self._run_in_cylc_mode()
            elif self.app_options['parallel_mode'] == 'pymp':
                run_aborted = self._run_in_mp_mode()
            else:
                run_aborted = self._run_in_serial_mode()
            if run_aborted:
                self.returncode = RETCODE_ABORT_ON_ERROR
        finally:
            if self.app_options['run_teardown']:
                self._teardown()

        self.logger.info("MassDataRobot app run completed.")

    def _check_moose_support(self):
        """Check that the MOOSE command interface is supported."""
        if not moose.has_moose_support():
            msg = ("The runtime environment does not appear to support\n"
                   "the MOOSE command interface to the MASS data archive.")
            self.logger.error(msg)
            raise MooseUnsupportedError(msg)

    def _check_moose_status(self):
        """Check that the MOOSE interface is open for read operations."""
        if not moose.check_moose_commands_enabled(MOOSE_READ):
            msg = "The MASS archive is not currently available for read operations."
            self.logger.warning(msg)
            raise MooseUnavailableError(msg)

    def _read_app_options(self):
        """Read general app config options and store them in a dictionary."""

        section = 'general'
        opts = dict()

        opts['abort_on_error'] = self.app_config.get_bool_property(section,
            'abort_on_error', default=False)

        if self.cli_args.parallel_mode:
            opts['parallel_mode'] = self.cli_args.parallel_mode
        else:
            opts['parallel_mode'] = self.app_config.get_property(section,
                'parallel_mode', default='pymp')

        opts['max_active_tasks'] = self.app_config.get_int_property(section,
            'max_active_tasks', default=10)

        opts['script_dir'] = self.app_config.get_property(section,
            'script_dir', default='mdr_scripts')

        opts['query_file_dir'] = self.app_config.get_property(section,
            'query_file_dir', default='mdr_query_files')

        opts['log_dir'] = self.app_config.get_property(section,
            'log_dir', default='mdr_logs')

        if self.cli_args.no_teardown:
            opts['run_teardown'] = False
        else:
            opts['run_teardown'] = self.app_config.get_bool_property(section,
                'run_teardown', default=True)

        self.logger.debug("General options:\n%s", pprint.pformat(opts))

        return opts

    def _read_moose_options(self):
        """Read MOOSE options and store them in a dictionary."""

        section = 'moose'
        opts = dict()

        opts['dry_run'] = self.app_config.get_bool_property(section,
            'dry_run', default=False)

        opts['fill_gaps'] = self.app_config.get_bool_property(section,
            'fill_gaps', default=True)

        opts['force'] = self.app_config.get_bool_property(section,
            'force', default=False)

        opts['get_if_available'] = self.app_config.get_bool_property(section,
            'get_if_available', default=True)

        opts['large_retrieval'] = self.app_config.get_bool_property(section,
            'large_retrieval', default=False)

        opts['compressed_transfer'] = self.app_config.get_bool_property(section,
            'compressed_transfer', default=False)

        opts['max_transfer_threads'] = self.app_config.get_int_property(section,
            'max_transfer_threads', default=0)

        self.logger.debug("MOOSE options:\n%s", pprint.pformat(opts))

        if opts['fill_gaps'] and opts['force']:
            raise AppConfigError("MOOSE options 'fill_gaps' and 'force' are "
                "mutually incompatible - consider disabling one of them.")

        return opts

    def _read_cache_definitions(self):
        """Read data cache definitions and store them in a dictionary."""

        cache_defns = {}

        for csdict in self.app_config.iter_nl('data_caches'):
            index = csdict.pop('_index', None)
            cache_defn = NamespacePlus(**csdict)
            if not self._validate_cache_definition(cache_defn, index):
                raise AppConfigError("Invalid data cache definition at index %s."
                    % index)
            cache_defn.base_dir = expand_path(cache_defn.base_dir)
            if cache_defn.file_mode:
                cache_defn.file_mode = int(cache_defn.file_mode)
            cache_defns[cache_defn.id] = cache_defn
            self.logger.debug("Cache %s: %s", index, csdict)

        self.logger.info("Read %d data cache definition(s).", len(cache_defns))

        return cache_defns

    def _validate_cache_definition(self, cache_defn, index):
        """Validate the specified cache definition."""
        valid = True
        msg = "'{0}' property not defined for cache definition at index {1}."

        for prop in ['id', 'scheme', 'base_dir']:
            if not getattr(cache_defn, prop, None):
                self.logger.error(msg.format(prop, index))
                valid = False

        return valid

    def _read_request_definitions(self):
        """Read composite requests definitions and store them as a list."""

        requests = []

        for reqdict in self.app_config.iter_nl('requests'):
            index = reqdict.pop('_index', None)
            req = NamespacePlus(**reqdict)
            if not req.data_class: req.data_class = 'crum'
            if not req.variables: req.variables = '*'
            if not req.calendar: req.calendar = cf_units.CALENDAR_360_DAY
            if not req.postproc_vn: req.postproc_vn = '1.0'
            if not self._validate_request_definition(req, index):
                raise AppConfigError("Invalid data request definition at index "
                    "location %s in app configuration file." % index)
            requests.append(req)

        self.logger.info("Read %d data request definition(s).", len(requests))

        return requests

    def _validate_request_definition(self, request, index):
        """Validate the specified data request object."""
        valid = True
        msg = "'{0}' property not defined for data request at index {1}."

        for prop in ['data_class', 'data_sets', 'data_collections', 'cache_id']:
            if not getattr(request, prop, None):
                self.logger.error(msg.format(prop, index))
                valid = False

        if request.data_class not in ['crum', 'ens']:
            self.logger.error("Unrecognised data class: " + request.data_class)
            valid = False

        if request.data_class == 'ens' and not request.realizations:
            self.logger.error("No ensemble members have been defined for "
                "ensemble-based data request.")
            valid = False

        cache_defn = self.cache_defns[request.cache_id]
        if not request.variables or request.variables == '*':
            if cache_defn.scheme not in (STREAM_SPLIT_SCHEME, ENSEMBLE_STREAM_SPLIT_SCHEME):
                self.logger.error("Cache scheme must be stream-based for data "
                    "requests that do not specify selected variables.")
                valid = False
        else:
            if cache_defn.scheme not in (VAR_SPLIT_SCHEME, ENSEMBLE_VAR_SPLIT_SCHEME):
                self.logger.error("Cache scheme must be variable-based for data "
                    "requests that specify selected variables.")
                valid = False

        return valid

    def _create_runtime_directories(self):
        """Create any required runtime directories."""

        for opt_dir in ['query_file_dir', 'script_dir', 'log_dir']:
            pth = self.app_options[opt_dir]
            if pth and not os.path.exists(pth):
                os.makedirs(pth)
                self.logger.info("Created directory " + pth)

    def _setup_data_caches(self):
        """Set up data caches for each of the user-specified cache definitions."""
        self.logger.info("Initialising data cache environments...")

        dstore = MassDataStore()

        for cache_defn in self.cache_defns.values():
            cache_dict = vars(cache_defn).copy()
            cache_id = cache_dict.pop('id')
            scheme = cache_dict.pop('scheme')
            base_dir = cache_dict.pop('base_dir')
            self.data_caches[cache_id] = DataCache.create_cache(scheme, dstore,
                base_dir, **cache_dict)

    def _create_atomic_request_definitions(self):
        """
        Generate a list of atomic data requests from the composite data requests
        defined in the app config file.
        """
        self.logger.info("Generating discrete MOOSE data request definitions...")

        requests = []
        reqnum = 0

        for raw_req in self.raw_requests:
            data_sets = [s.strip() for s in raw_req.data_sets.split(',')]
            data_colls = [s.strip() for s in raw_req.data_collections.split(',')]
            if raw_req.realizations:
                realizations = [s.strip() for s in raw_req.realizations.split(',')]
            else:
                realizations = [None]
            if raw_req.variables:
                variables = [s.strip() for s in raw_req.variables.split(',')]
            else:
                variables = ['*']
            if raw_req.aux_variables:
                aux_variables = [s.strip() for s in raw_req.aux_variables.split(',')]
            else:
                aux_variables = None

            # Create a dictionary of any integer-type PP header items ('lb*')
            # specified as part of the request. Non-integer valued items are
            # silently ignored.
            pph_ivals = {}
            for k, v in iter(raw_req):
                if k in SUPPORTED_PPH_IVALS:
                    try:
                        pph_ivals[k] = int(v)
                    except (TypeError, ValueError):
                        self.logger.warning("Ignoring non-integer value '%s' "
                            "for PP header word '%s'.", v, k)

            # hold pointer to associated data cache object
            cache_defn = self.cache_defns[raw_req.cache_id]
            data_cache_ref = self.data_caches[cache_defn.id]

            for prod in itertools.product(data_sets, realizations, data_colls, variables):
                data_set, realization, data_coll, variable = prod[:]
                reqnum += 1
                req_id = "req{0:03d}".format(reqnum)
                self.logger.debug("Creating atomic request %s for target "
                    "%s/%s/%s/%s", req_id, data_set, realization, data_coll, variable)
                atomic_req = AtomicDataRequest(req_id, raw_req.data_class,
                    data_set, data_coll, data_cache_ref, realization_id=realization,
                    variable=variable, aux_variables=aux_variables,
                    start_date=raw_req.start_date, end_date=raw_req.end_date,
                    calendar=raw_req.calendar, grid_type=raw_req.grid_type,
                    file_glob=raw_req.file_glob, postproc_vn=raw_req.postproc_vn,
                    pph_ivals=pph_ivals)
                requests.append(atomic_req)
                self.logger.debug("%s: %s", atomic_req.req_id, atomic_req.moose_path)

        if reqnum > MAX_MOOSE_DATA_REQUESTS:
            msg = ("Number of MOOSE data requests ({0}) exceeds maximum "
                   "permitted ({1}).".format(reqnum, MAX_MOOSE_DATA_REQUESTS))
            self.logger.error(msg)
            raise DataProcessingError(msg)

        self.logger.info("Generated %d MOOSE data request definition(s).", len(requests))

        self.atomic_requests = requests

    def _make_moose_commands(self):
        """Construct MOOSE commands for each of the atomic requests."""
        self.logger.info("Generating commands for discrete MOOSE data requests...")

        query_file_dir = self.app_options['query_file_dir']

        for request in self.atomic_requests:
            dcache = request.data_cache
            dest_path = dcache.get_cache_dir_for_variable(request.as_metavariable())
            dest_path = os.path.join(dcache.base_dir, dest_path)
            request.dest_path = dest_path
            request.moose_command = _make_moose_command(request, query_file_dir,
                moose_options=self.moose_options)

            self.logger.debug("%s: %s", request.req_id, request.moose_command)

    def _create_task_scripts(self):
        """
        Create task scripts for each of the atomic requests. The intent is for
        these scripts to be invoked, in suitable batches, from cylc tasks.
        """
        self.logger.info("Creating task scripts for discrete MOOSE data requests...")

        script_dir = self.app_options['script_dir']
        log_dir = self.app_options['log_dir']
        if not log_dir: log_dir = '/dev/null'

        for request in self.atomic_requests:
            script_filename = "{0}_script.sh".format(request.req_id)
            script_filename = os.path.join(script_dir, script_filename)
            if log_dir.startswith('/dev'):
                log_filename = log_dir
            else:
                log_filename = "{0}.log".format(request.req_id)
                log_filename = os.path.join(log_dir, log_filename)
            redirect = ">> {0} 2>&1".format(log_filename)
            with open(script_filename, 'w') as fd:
                fd.write("#!/bin/bash\n")
                fd.write("# Task script for data request {0}\n".format(request.req_id))
                fd.write("set -e\n")
                fd.write("date -u > {0}\n".format(log_filename))  # resets log file
                if self.cli_args.dry_run:
                    fd.write("echo '=>' mkdir -p {0}\n".format(request.dest_path))
                    fd.write("echo '=>' {0}\n".format(request.moose_command))
                else:
                    fd.write("mkdir -p {0} {1}\n".format(request.dest_path, redirect))
                    fd.write("{0} {1}\n".format(request.moose_command, redirect))
            os.chmod(script_filename, 0o755)
            request.script_filename = script_filename
            request.log_filename = log_filename

    def _create_cylc_tasks(self):
        """Create cylc tasks for each of the MOOSE data requests."""

        suite_name = os.environ.get('CYLC_SUITE_NAME')
        if suite_name:
            self.logger.info("Inserting cylc tasks into suite %s...", suite_name)
        else:
            self.logger.error("Unable to determine cylc suite name.")
            return

        for _reqno, request in enumerate(self.atomic_requests):
            taskid = 'retrieve_data_{0}.1'.format(request.req_id)
            cmd = "cylc insert {0} {1}".format(suite_name, taskid)
            returncode = os.system(cmd)
            if returncode == 0:
                self.logger.info("Successfully inserted cylc task '%s'", taskid)
            else:
                self.logger.error("Failed to insert cylc task '%s'", taskid)

    def _run_in_cylc_mode(self):
        """Execute MOOSE commands using cylc scheduler."""
        # This method doesn't doing anything at present because the task scripts
        # created during initialisation are run explicitly by the cylc scheduler.
        self.logger.info("Executing MASS data retrieval tasks in cylc mode.")
        return False

    def _run_in_mp_mode(self):
        """Execute MOOSE commands on local system using multiprocessing module."""
        msg = "Executing MASS data retrieval tasks in multiprocessing mode"
        if self.cli_args.dry_run: msg += ' (dry-run only)'
        self.logger.info(msg)
        run_aborted = False

        try:
            max_jobs = self.app_options['max_active_tasks']

            # Create manager and queue objects for passing MOOSE data requests.
            request_manager = mp.Manager()
            request_queue = request_manager.Queue()
            returncodes = request_manager.dict()   # dict for storing return codes
            abort_on_error = request_manager.Value('B', self.app_options['abort_on_error'])
            nerrors = request_manager.Value('B', 0)

            self.logger.info("Initialising %s worker processes...", max_jobs)
            jobs = []
            for _ in range(max_jobs):
                proc = mp.Process(target=_run_task_script,
                    args=(request_queue, returncodes, nerrors, abort_on_error))
                jobs.append(proc)
                proc.start()

            self.logger.info("Queuing data request tasks...")
            for req in self.atomic_requests:
                self.logger.debug("\trequest " + req.req_id)
                request_queue.put((req.req_id, req.moose_command, req.script_filename))
            for _ in range(max_jobs):
                request_queue.put(None)

            self.logger.info("Executing data request tasks...")
            for job in jobs:
                job.join()

            nerrs = sum((1 for x in returncodes.values() if x))
            if nerrs:
                msg = ("%d MOOSE command errors were encountered.\nPlease refer "
                       "to standard output or log files for details." % nerrs)
                raise AppRuntimeError(msg)

        except Exception as exc:
            self.logger.error(str(exc))
            if self.app_options['abort_on_error']:
                run_aborted = True

        return run_aborted

    def _run_in_serial_mode(self):
        """Execute MOOSE commands in series."""
        msg = "Executing MASS data retrieval tasks in serial mode"
        if self.cli_args.dry_run: msg += ' (dry-run only)'
        self.logger.info(msg)
        run_aborted = False

        for request in self.atomic_requests:
            self.logger.info("{0}:\n   command: {1}".format(request.req_id,
                request.moose_command))
            try:
                got_error = False
                subprocess.check_call(request.script_filename)
            except subprocess.CalledProcessError as exc:
                if exc.returncode != moose.MOOSE_ALL_FILES_EXIST:
                    got_error = True
                    self.logger.error(str(exc))
            except Exception as exc:
                got_error = True
                self.logger.error(str(exc))
            finally:
                status = 'error' if got_error else 'okay'
                self.logger.info("   status: %s", status)
                if got_error and self.app_options['abort_on_error']:
                    msg = ("Error running task script for data request {0}.\n"
                           "Check log file {1} for details.".format(request.req_id,
                           request.log_filename))
                    self.logger.error(msg)
                    run_aborted = True
            if run_aborted: break

        return run_aborted

    def _teardown(self):
        """Run desired teardown actions."""
        self.logger.info("Running teardown actions...")

        # Remove query files, script files, and their host directories.
        dirlist = [self.app_options['query_file_dir'], self.app_options['script_dir']]
        for dirpath in dirlist:
            self.logger.info("Deleting contents of directory %s...", dirpath)
            fnames = os.listdir(dirpath)
            for fn in fnames:
                try:
                    os.remove(os.path.join(dirpath, fn))
                except OSError:
                    pass
            try:
                os.rmdir(dirpath)
            except OSError:
                pass


class AtomicDataRequest(object):
    """
    Class for encapsulating an atomic data request, this being a request for the
    data associated with one or all variables from a single data collection /
    realization / data set combination in MASS. The realization component is
    only defined for ensemble-based datasets.
    """

    # TODO: Implement support for a subset of variables.

    def __init__(self, req_id, data_class, data_set, data_collection, data_cache,
        realization_id=None, variable=None, aux_variables=None, calendar=None,
        start_date=None, end_date=None, grid_type=None, file_glob=None,
        postproc_vn=None, pph_ivals=None):

        self.req_id = req_id
        self.data_class = data_class
        self.data_set = data_set
        self.data_collection = data_collection
        self.data_cache = data_cache
        self.realization_id = realization_id
        self.variable = variable or '*'
        self.aux_variables = aux_variables
        self.calendar = calendar or cf_units.CALENDAR_360_DAY
        self.start_date = start_date
        self.end_date = end_date
        self.grid_type = grid_type or 'T'
        self.file_glob = file_glob
        self.postproc_vn = postproc_vn or '1.0'
        self.dest_path = ''
        self.model_vn = '0'
        self._metavar = None

        # For UM variables parse the stash code and optional PP header values
        # from the user-specified variable definition, e.g. 'm01s01i207[lbtim=122]'
        # These will override any request-level values passed in via the pph_ivals
        # argument.
        self._stash_code = ''
        self._pph_ivals = pph_ivals.copy() if isinstance(pph_ivals, dict) else {}
        try:
            self._stash_code, _pph_ivals = _parse_stash_variable(self.variable)
            if _pph_ivals:
                self._pph_ivals.update(_pph_ivals)
        except ValueError:
            pass
        if self._pph_ivals:
            _logger.debug("PP header constraints: %s", self._pph_ivals)

    def __str__(self):
        """Returns a string representation of the data request."""
        return "{0}: {1}".format(self.req_id, self.moose_path)

    @property
    def stream_id(self):
        """Returns the stream identifier associated with a data request."""
        return self.data_collection.partition('.')[0]

    @property
    def moose_url(self):
        """Returns the MOOSE URL for a data request."""

        if self.data_class == 'crum':
            url = "moose:/crum/{0.data_set}/{0.data_collection}".format(self)
        elif self.data_class == 'ens':
            url = "moose:/ens/{0.data_set}/{0.realization_id}/{0.data_collection}".format(self)
        else:
            raise AppConfigError("Unrecognised MASS data class: " + self.data_class)

        return url

    @property
    def moose_path(self):
        """Returns the MOOSE path for a data request, i.e. without the protocol."""
        return self.moose_url.partition(':')[-1]

    @property
    def all_variables(self):
        """Returns a list containing self.variable and self.aux_variables."""
        if self.variable:
            varlist = [self.variable]
            if self.aux_variables: varlist.extend(self.aux_variables)
        else:
            varlist = []
        return varlist

    @property
    def time_range(self):
        """
        Returns the time range associated with data request as the 2-tuple of
        ISO date-time strings (start_date, end_date).
        """
        sdate = self.start_date
        if sdate and '/' in sdate: sdate = moose_date_to_iso_date(sdate)
        edate = self.end_date
        if edate and '/' in edate: edate = moose_date_to_iso_date(edate)
        return sdate, edate

    @property
    def stash_code(self):
        """The MSI-style stash code for UM-type variables."""
        return self._stash_code

    @property
    def pph_ivals(self):
        """The dictionary of PP header integer values for UM-type variables."""
        return self._pph_ivals

    def is_time_bound(self):
        """Returns True if the data request is time-bound."""
        return self.start_date and self.end_date

    def is_um_stream(self):
        """Returns True if the data request refers to data from a UM stream."""
        return self.stream_id[0] == 'a'

    def is_nemo_stream(self):
        """Returns True if the data request refers to data from a NEMO stream."""
        return self.stream_id[0] == 'o'

    def is_cice_stream(self):
        """Returns True if the data request refers to data from a CICE stream."""
        return self.stream_id[0] == 'i'

    def as_metavariable(self):
        """
        Construct a :class:`afterburner.metavar.MetaVariable` object from relevant
        attributes of the atomic data request.
        """
        if self._metavar: return self._metavar

        if self.is_time_bound():
            time_range = self.time_range
        else:
            time_range = None

        if self.is_um_stream():
            stash_code = 'm00s00i000' if self.variable == '*' else self.stash_code
            var = UmMetaVariable(self.model_vn, self.data_set,
                realization_id=self.realization_id, stream_id=self.stream_id,
                stash_code=stash_code, time_range=time_range, calendar=self.calendar,
                **self.pph_ivals)

        elif self.is_nemo_stream():
            var_name = self.variable
            if var_name == '*': var_name = 'undefined'   # dummy variable name
            var = NemoMetaVariable(self.model_vn, self.data_set,
                realization_id=self.realization_id, stream_id=self.stream_id,
                var_name=var_name, time_range=time_range, calendar=self.calendar,
                grid_type=self.grid_type, postproc_vn=self.postproc_vn)

        elif self.is_cice_stream():
            var_name = self.variable
            if var_name == '*': var_name = 'undefined'   # dummy variable name
            var = CiceMetaVariable(self.model_vn, self.data_set,
                realization_id=self.realization_id, stream_id=self.stream_id,
                var_name=var_name, time_range=time_range, calendar=self.calendar,
                postproc_vn=self.postproc_vn)

        else:
            raise NotImplementedError("Stream '%s' is not currently supported."
                % self.stream_id)

        self._metavar = var
        return var


def _parse_stash_variable(variable):
    """
    Parse the stash code and optional lb* PP header values from a STASH-type
    variable definition. The variable must either be an unadorned stash code
    (e.g. 'm01s01i207') or a stash code followed by one or more semicolon-delimited
    tokens of the form 'lb*:<integer>'  (e.g. 'm01s01i207[lbproc=128;lbtim=122]'
    """

    if is_msi_stash_code(variable):
        stash_code = variable
        pph_ivals = {}
    elif '[' in variable:
        stash_code, _, rest = variable.partition('[')
        pph_ivals = {}
        tokens = [t.split('=') for t in rest[:-1].split(';')]
        for k, v in tokens:
            if k in SUPPORTED_PPH_IVALS:
                try:
                    pph_ivals[k] = int(v)
                except (TypeError, ValueError):
                    # ignore non-integer-valued header words
                    pass
    else:
        raise ValueError("Invalid STASH variable definition: %s" % variable)

    return stash_code, pph_ivals


def _make_moose_command(request, query_file_dir, moose_options=None):
    """
    Construct the MOOSE command for the specified atomic data request.
    """

    if request.variable and request.variable != '*':
        variables = [request.variable]
    else:
        variables = None

    if request.is_time_bound():
        time_range = request.time_range
    else:
        time_range = None

    file_glob = request.file_glob or None

    xargs_cmd = ''
    moose_cmd = 'moo get'
    source_uri = ''

    if request.is_um_stream():
        source_uri = request.moose_url
        if variables or time_range or request.pph_ivals:
            fpath = "{0}_query.txt".format(request.req_id)
            fpath = os.path.join(query_file_dir, fpath)
            stashcodes = [request.stash_code] if variables else None
            moose.write_query_file(fpath, stashcodes=stashcodes,
                time_range=time_range, pph_ivals=request.pph_ivals)
            moose_cmd = 'moo select ' + fpath

    elif request.is_nemo_stream() or request.is_cice_stream():
        if variables:
            fpath = "{0}_filter.txt".format(request.req_id)
            fpath = os.path.join(query_file_dir, fpath)
            moose.write_filter_file(fpath, var_names=request.all_variables)
            moose_cmd = 'moo filter ' + fpath

        if time_range:
            metavar = request.as_metavariable()
            fn_provider = FilenameProvider.from_metavar(metavar)
            filenames = fn_provider.get_filenames(metavar)
            fpath = "{0}_filelist.txt".format(request.req_id)
            fpath = os.path.join(query_file_dir, fpath)
            with open(fpath, 'w') as fd:
                for fname in filenames:
                    fd.write(request.moose_url + '/' + fname + '\n')
            xargs_cmd = "xargs -a {0} -n {1} bash -c '{{0}}'".format(fpath,
                MAX_URIS_PER_MOOSE_COMMAND)
            source_uri = '$0 $@'
        else:
            if file_glob:
                source_uri = request.moose_url + '/' + file_glob
            else:
                source_uri = request.moose_url + '/*'

    # Append any options to the MOOSE command.
    if moose_options:
        if moose_options.get('dry_run'):
            moose_cmd += ' --dry-run'

        if moose_options.get('force'):
            moose_cmd += ' -f'
        elif moose_options.get('fill_gaps'):
            moose_cmd += ' -i'

        if moose_options.get('get_if_available') and moose_cmd == 'moo get':
            moose_cmd += ' -g'

        if moose_options.get('large_retrieval'):
            moose_cmd += ' -b'

        if moose_options.get('compressed_transfer'):
            moose_cmd += ' -z'

        if moose_options.get('max_transfer_threads'):
            moose_cmd += ' -j %d' % moose_options['max_transfer_threads']

    # Append source URIs and destination path.
    moose_cmd += " {0} {1}".format(source_uri, request.dest_path)

    # If xargs is being used to handle multiple source URIs, then inject the
    # MOOSE command into the appropriate place in the xargs command.
    if xargs_cmd:
        moose_cmd = xargs_cmd.format(moose_cmd)

    return moose_cmd


def _run_task_script(request_queue, returncodes, nerrors, abort_on_error):
    """Run the task script associated with the specified data request object."""

    while True:
        if nerrors.value and abort_on_error.value:
            print("Error(s) encountered - aborting process:", os.getpid(),
                file=sys.stderr)
            break

        request = request_queue.get()
        if request is None: break
        reqid, command, script = request[:]

        try:
            subprocess.check_call(script)
            returncodes[reqid] = 0

        except subprocess.CalledProcessError as exc:
            if re.match(r'.+dry-?run', command) or \
               exc.returncode == moose.MOOSE_ALL_FILES_EXIST:
                returncodes[reqid] = 0
            else:
                returncodes[reqid] = exc.returncode

        # Increment error count.
        if returncodes[reqid] != 0:
            nerrors.value += 1
