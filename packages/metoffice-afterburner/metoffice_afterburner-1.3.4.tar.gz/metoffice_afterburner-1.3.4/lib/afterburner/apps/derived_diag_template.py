# (C) British Crown Copyright 2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Provides an implementation of the DerivedDiagTemplateApp template class, which
may be used to build applications capable of producing so-called derived, or
custom, diagnostics, where each such 'target' diagnostic is derived from one
or more 'source' diagnostics.

Refer to the :class:`DerivedDiagTemplateApp` class documentation for further
information.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import os
import logging
import datetime
from abc import abstractmethod

import cf_units as cfu
import iris
import iris.exceptions

from afterburner.apps import AbstractApp
from afterburner.exceptions import (AfterburnerError, AppConfigError,
    DataProcessingError)
from afterburner.filename_providers import TemplateDrivenFilenameProvider
from afterburner.io import NetcdfFileWriter
from afterburner.io.datacaches import DataCache
from afterburner.io.datastores import DataStore, NullDataStore
from afterburner.metavar import MetaVariable
from afterburner.modelmeta import cf_cell_method_from_lbproc, is_msi_stash_code
from afterburner.utils import (is_true, get_class_object_from_class_path,
    get_cylc_task_work_dir, get_cylc_variables, NamespacePlus)
from afterburner.utils.cubeutils import (make_calendar_type_cube_func,
    make_cell_method_cube_func)
from afterburner.utils.dateutils import DateTimeRange
from afterburner.utils.fileutils import (expand_path, expand_filenames,
    filter_by_sentinel_files, list_files_newer_than, serialize_timestamp,
    deserialize_timestamp)
from afterburner.utils.textutils import decode_string_value

# IDs of sections and namelists used in the application configuration file.
GENERAL_SECTION = 'general'
DATA_CACHE_SECTION = 'data_cache'
DATA_READER_SECTION = 'data_reader'
DATA_WRITER_SECTION = 'data_writer'
NETCDF_SAVER_SECTION = 'netcdf_saver'

MODELS_NAMELIST = 'models'
PROCESSORS_NAMELIST = 'processors'
SOURCE_DIAGS_NAMELIST = 'source_diagnostics'
TARGET_DIAGS_NAMELIST = 'target_diagnostics'

# Name of the entry in the diagnostics namelist which contains default settings.
DEFAULT_DIAGNOSTIC_NAME = '_defaults_'

# Create a logger object.
_logger = logging.getLogger(__name__)


class DerivedDiagTemplateApp(AbstractApp):
    """
    The DerivedDiagTemplateApp class provides a template for building Afterburner
    applications capable of producing so-called derived, or custom, diagnostics.

    Importantly, the application works on the basis that input model data is
    serialised in whole-stream files within a single directory (for any given
    stream). This is a common way of laying down model data on disk. Moreover,
    because the Unified Model is typically configured to serialise diagnostic
    output files within a single directory, applications that subclass the
    DerivedDiagTemplateApp base class should be capable of being executed in
    so-called 'in-line' mode, i.e. as a climate simulation is running.

    The high-level application logic proceeds as follows::

        read app configuration options
        configure I/O sources
        for each data stream:
            load model data for all required source diagnostics
            for each target diagnostic:
                extract source data for the current diagnostic
                create a processor object for the diagnostic
                pass the diagnostic data to the processor object
                calculate the target diagnostic
                save the results (usually a cube or cubelist) to a netcdf file

    The processor object is an instance of a concrete subclass of the
    :class:`afterburner.processors.AbstractProcessor` class. The exact class to
    use is specified in the app config file. It can be one of the ready-made
    classes defined in the afterburner package, or it can be a user-defined class.
    The processor class can implement data processing of arbitrary complexity.

    The reason why the application loads ALL diagnostic data for the current
    stream in one pass is because reading data from large UM fieldsfiles or PP
    files is an expensive process. Hence it is preferable to load the data once
    for each stream rather than multiple times, once for each diagnostic to be
    processed.

    Applications that subclass the DerivedDiagTemplateApp base class need to
    implement, as minimum, the following abstract methods:

    * :meth:`__init__`
    * :meth:`process_diagnostic`

    In fact the above methods have default, albeit basic, implementations. In
    which case concrete subclasses may, if appropriate, simply call the base
    class method using, for example, the ``super()`` built-in function.

    In addition to the aforementioned abstract methods, concrete subclasses are
    free to override any of the other methods. Whether or not this is required
    will depend upon the intended behaviour of the application. Methods that
    might need to be overridden include (in order of appearance):

    * :meth:`cli_spec`
    * :meth:`make_unique_source_diag_key`
    * :meth:`make_unique_target_diag_key`
    * :meth:`get_source_diag_defaults`
    * :meth:`get_source_diag_definitions`
    * :meth:`get_target_diag_defaults`
    * :meth:`get_target_diag_definitions`
    * :meth:`augment_diag_definition`
    * :meth:`load_stream_data`
    """

    @abstractmethod
    def __init__(self, arglist=None, **kwargs):
        """
        :param list arglist: List of raw options and/or arguments passed from the
            calling environment. Typically these will be unprocessed command-line
            arguments, e.g. ``['-f', 'foo', '--foe=fum', 'infile']``.
        """
        super(DerivedDiagTemplateApp, self).__init__(**kwargs)

        # Obtain the app name from the name of the concrete subclass.
        self.app_name = self.__class__.__name__

        # Parse command-line arguments and, if one was specified, a Rose
        # configuration file.
        desc = kwargs.get('description', 'app description')
        self._parse_args(arglist, desc="{0}: {1}".format(self.app_name, desc))
        self._parse_app_config()

        # Set the message/logging level according to standard CLI args, if set.
        self._set_message_level()
        self.logger.info("Initialising the %s app ...", self.app_name)

        # Determines whether or not to abort the app if an error is encountered
        # processing a stream or diagnostic.
        try:
            self.abort_on_error = self.cli_args.abort_on_error
            if self.abort_on_error is None: self.abort_on_error = False
        except AttributeError:
            self.abort_on_error = False

        # Enable or disable (default) dry-run mode.
        try:
            self.dry_run = self.cli_args.dry_run
            if self.dry_run is None: self.dry_run = False
        except AttributeError:
            self.dry_run = False

        # Remember the current working directory.
        self.cwd = os.getcwd()

        #: An instance object whose attributes mirror any CYLC_* environment
        #: variables that have been defined by the calling environment.
        self.cylc = get_cylc_variables()

        #: An instance object whose attributes record general application options
        #: as defined in the app config file.
        self.general_opts = None

        #: An instance object whose attributes record data cache options
        #: as defined in the app config file.
        self.data_cache_opts = None

        #: An instance object whose attributes record data reader options
        #: as defined in the app config file.
        self.data_reader_opts = None

        #: An instance object whose attributes record data writer options
        #: as defined in the app config file.
        self.data_writer_opts = None

        #: An instance object whose attributes record netCDF file saver options
        #: as defined in the app config file.
        self.netcdf_opts = None

        #: A dictionary of instance objects whose attributes record model options
        #: as defined in the app config file.
        self.model_opts = None

        #: A dictionary of instance objects whose attributes record processor
        #: definitions as defined in the app config file.
        self.processor_defns = None

        #: An instance object whose attributes record default settings for
        #: source diagnostics.
        self.source_diag_defaults = None

        #: A dictionary of key: source-diagnostic pairs as defined in the app
        #: config file.
        self.source_diag_defns = None

        #: An instance object whose attributes record default settings for
        #: target diagnostics.
        self.target_diag_defaults = None

        #: A dictionary of key: target-diagnostic pairs as defined in the app
        #: config file.
        self.target_diag_defns = None

        #: A DataCache object which manages access to a cache of on-disk model
        #: data files.
        self.data_cache = None

        #: An Afterburner processor object which handles writing data to disk.
        self.data_writer = None

        #: A FilenameProvider object which yields the names of input files for a
        #: given diagnostic.
        self.input_filename_provider = None

        #: A FilenameProvider object which yields the names of output files for a
        #: given diagnostic.
        self.output_filename_provider = None

        #: A FilenameProvider object which yields the names of files for storing
        #: timestamps (of model input files).
        self.timestamp_filename_provider = None

        #----------------------------------------------------------------------#

        # Dictionary of source diagnostic definitions, with attributes augmented
        # for the current stream being processed.
        self.source_diags_for_stream = None

        # Dictionary of target diagnostic definitions, with attributes augmented
        # for the current stream being processed.
        self.target_diags_for_stream = None

        # Process all app config options.
        self.get_app_config_options()

        # Create any required directories.
        self.create_directories()

        # Create any required filename provider objects.
        self.create_filename_providers()

        # Create a data writer object to handle file output.
        self.create_data_writer()

    @property
    def cli_spec(self):
        """
        Defines the command-line interface specification for the application.
        This property should return a list of dictionary objects, each of which
        specifies a series of parameters to pass through to the add_argument()
        method of the argparse.ArgumentParser class.
        """

        cmd_args = [
            {'names': ['-c', '--config-file'],
                'help': 'Pathname of the app configuration file'},
            {'names': ['--abort-on-error'], 'dest': 'abort_on_error',
                'action': 'store_true', 'default': False,
                'help': 'Abort processing if an error is encountered'},
        ]

        return cmd_args

    def run(self, *args, **kwargs):
        """
        Runs the application.

        Extra Keyword Arguments (`**kwargs`):

        :param bool abort_on_error: If set to true then processing is aborted
            immediately if an error is encountered processing a diagnostic.
            If set to false then processing will skip to the next stream/diagnostic
            combination. This argument overrides the command-line argument of the
            same name and also the corresponding app config file option.
        :param bool dry_run: If set to true then, as a minimum, no output files
            are created. Subclasses may implement additional behaviour.
        """

        self.logger.info("Running the %s app.", self.app_name)

        if kwargs.get('abort_on_error') is not None:
            self.abort_on_error = kwargs['abort_on_error']

        if kwargs.get('dry_run') is not None:
            self.dry_run = kwargs['dry_run']

        # Remember the current working directory.
        self.cwd = os.getcwd()

        # Update cylc parameters.
        self.cylc = get_cylc_variables()
        self.logger.debug("Cylc suite name: '%s'", self.cylc.suite_name)
        self.logger.debug("Cylc task name: '%s'", self.cylc.task_name)

        # Loop over all of the data streams referenced by target diagnostics.
        for stream in _get_stream_list(self.target_diag_defns):
            try:
                self.process_stream(stream)
            except Exception as exc:
                self.logger.error(str(exc))
                if self.abort_on_error:
                    self.logger.info("Error encountered: aborting further processing.")
                    self.returncode = getattr(exc, 'error_code', -1)
                    break
                else:
                    self.logger.info("Error encountered: skipping to next stream.")

        if self.returncode:
            self.logger.info("%s app completed with errors.", self.app_name)
        else:
            self.logger.info("%s app completed successfully.", self.app_name)

    def process_stream(self, stream):
        """
        Process all diagnostics that have been enabled for the specified stream.
        If no data can be found for the stream in the configured model data
        directory then the function emits an info message and returns.

        :param str stream: The name of the stream to process.
        """

        text = "Processing {0}-stream diagnostics".format(stream)
        self.logger.info('\n'+text)
        self.logger.info('='*len(text))

        # Obtain a list of keys of all target diagnostics needed for the current stream.
        target_keys = _get_stream_diag_list(stream, self.target_diag_defns, enabled=True)
        if not target_keys:
            self.logger.info("No target diagnostics enabled for this stream")
            return

        # Obtain a list of keys of all source diagnostics needed for the current stream.
        source_keys = _get_stream_diag_list(stream, self.source_diag_defns, enabled=True)
        if not source_keys:
            self.logger.info("No source diagnostics enabled for this stream")
            return

        # Create a dictionary of source diagnostics, augmented for the current
        # stream.
        self.source_diags_for_stream = {}
        for diag_key in source_keys:
            diag_defn = self.source_diag_defns[diag_key].copy()
            self.augment_diag_definition(diag_defn, stream)
            self.source_diags_for_stream[diag_key] = diag_defn

        # Load data for all diagnostics required from the current stream.
        stream_data = self.load_stream_data(stream, source_keys)

        if not stream_data:
            self.logger.info("No model diagnostic data found for this stream.")
            return

        # Loop over all target diagnostics in the current stream.
        for diag_key in target_keys:
            diag_defn = self.target_diag_defns[diag_key].copy()
            self.augment_diag_definition(diag_defn, stream)
            try:
                self.process_diagnostic(stream_data, diag_defn)
            except Exception as exc:
                if self.abort_on_error:
                    raise
                else:
                    self.logger.error(str(exc))
                    self.logger.info("Error encountered: skipping to next diagnostic.")

        self.logger.info("Completed stream %s.\n", stream)

    @abstractmethod
    def process_diagnostic(self, stream_data, diag_defn):
        """
        Process the specified stream and diagnostic combination. Unless overridden
        by a subclass, the default implementation performs the following operations:

        * extracts cubes for the current diagnostic from the stream_data cubelist
        * hands the diagnostic data over to the processor object
        * save the results (usually a cube or cubelist) to a file on disk

        The name, location and format of the output file is determined by the
        settings in the [data_writer] section of the app config file.

        :param cubelist stream_data: A cubelist containing multiple diagnostics
            from a single model output stream.
        :param afterburner.utils.NamespacePlus diag_defn: A namespace object
            defining the target diagnostic to process.
        """

        text = "Processing target diagnostic {0}".format(diag_defn.name)
        self.logger.info('\n'+text)
        self.logger.info('-'*len(text))

        # Extract data for the specified diagnostic from the batch of cubes
        # loaded for the current stream.
        diag_cubes = self.extract_diag_data(stream_data, diag_defn)
        if not diag_cubes:
            self.logger.info("No model data found for this diagnostic.")
            return
        self.logger.info("Input cubes:\n%s", diag_cubes)

        # Attach start and end date strings (derived from the input data) to the
        # diag_defn object in case they are needed by a filename provider.
        dtr = DateTimeRange.from_cube(diag_cubes[0], use_bounds=True)
        fmt = self.general_opts.datetime_format
        diag_defn.data_start_date = dtr.start_ncdt.strftime(fmt)
        diag_defn.data_end_date = dtr.end_ncdt.strftime(fmt)
        self.logger.debug("Data start & end dates: %s, %s", diag_defn.data_start_date,
            diag_defn.data_end_date)

        # Create the processor associated with the current diagnostic and run it
        # with the loaded source data.
        md = _get_diag_metadata(diag_defn)
        proc = self.create_processor(diag_defn.processor)
        result_cubes = proc.run(diag_cubes, result_metadata=md)
        self.logger.info("Result cubes:\n%s", result_cubes)

        # Save the processed result to disk.
        if isinstance(result_cubes, (iris.cube.Cube, iris.cube.CubeList)):
            self.save_diag_data(result_cubes, diag_defn)

        self.logger.info("Completed diagnostic.\n")

    def make_source_diag_name(self, diag_defn):
        """
        Return a unique name for the specified source diagnostic definition. By
        default this method returns the value of the 'diag_defn.namelist_id'
        attribute, since that is guaranteed to be unique within a Rose-defined
        namelist.

        Subclasses of the current class may wish to override this method in order
        to return an application-specific name.

        :param afterburner.utils.NamespacePlus diag_defn: A namespace object
            defining the diagnostic for which a unique key is to be generated.
        :returns: A unique name for the source diagnostic.
        """
        return diag_defn.namelist_id

    def make_target_diag_name(self, diag_defn):
        """
        Return a unique name for the specified target diagnostic definition. By
        default this method returns the value of the 'diag_defn.namelist_id'
        attribute, since that is guaranteed to be unique within a Rose-defined
        namelist.

        Subclasses of the current class may wish to override this method in order
        to return an application-specific name.

        :param afterburner.utils.NamespacePlus diag_defn: A namespace object
            defining the diagnostic for which a unique key is to be generated.
        :returns: A unique name for the target diagnostic.
        """
        return diag_defn.namelist_id

    def get_app_config_options(self):
        """
        Read all application options from the app config file.
        """
        self.general_opts = self.get_general_options()

        self.data_reader_opts = self.get_data_reader_options()

        # Setup access to a data cache if one has been configured.
        if self.data_reader_opts.source_type == 'data_cache':
            self.data_cache_opts = self.get_data_cache_options()
            self.setup_data_cache()

        self.data_writer_opts = self.get_data_writer_options()

        self.netcdf_opts = self.get_netcdf_saver_options()

        self.model_opts = self.get_model_options()

        self.processor_defns = self.get_processor_definitions()

        self.source_diag_defaults = self.get_source_diag_defaults()

        self.source_diag_defns = self.get_source_diag_definitions()

        self.target_diag_defaults = self.get_target_diag_defaults()

        self.target_diag_defns = self.get_target_diag_definitions()

    def get_general_options(self, section=None):
        """
        Read general application options from the app config file.

        :param str section: The name of the section to read from the app config
            file (default: 'general').
        :returns: An afterburner.utils.NamespacePlus object whose attributes
            record options defined under the [general] section of the app config
            file.
        """

        try:
            section = section or GENERAL_SECTION
            ddict = self.app_config.section_to_dict(section)
            ddict = {k: decode_string_value(v) for k, v in ddict.items()}
            general_opts = NamespacePlus(**ddict)
        except ValueError:
            raise AppConfigError("Unable to find a section named '{0}' in the "
                "app config file".format(section))

        # Check to see if the abort_on_error option is set.
        general_opts.abort_on_error = is_true(general_opts.abort_on_error)
        if general_opts.abort_on_error is not None:
            self.abort_on_error = general_opts.abort_on_error

        # Datetime string format.
        general_opts.datetime_format = general_opts.datetime_format or '%Y%m%d'

        if not general_opts.suite_name:
            general_opts.suite_name = self.cylc.suite_name or 'UNDEF'
            self.logger.debug("Suite name is %s", general_opts.suite_name)

        self.logger.debug("General option names: %s", ','.join(sorted(ddict)))

        return general_opts

    def get_data_cache_options(self, section=None):
        """
        Read options from the [data_cache] section of the app config file.
        This section should contain the following options::

            [data_cache]
            cache_scheme=<scheme-name>    # e.g. SingleDirectory or StreamSplit
            base_dir=<dir-path>
            datastore_id=<datastore-id>   # e.g. MASS or blank
            read_only=<true-or-false>

        :param str section: The name of the section to read from the app config
            file (default: 'data_cache').
        :returns: An afterburner.utils.NamespacePlus object whose attributes
            record options defined under the [data_cache] section of the app
            config file.
        """

        try:
            section = section or DATA_CACHE_SECTION
            ddict = self.app_config.section_to_dict(section)
            ddict = {k: decode_string_value(v) for k, v in ddict.items()}
            cache_opts = NamespacePlus(**ddict)
        except ValueError:
            raise AppConfigError("Unable to find a section named '{0}' in the "
                "app config file".format(section))

        # Add custom code here.

        self.logger.debug("Data cache option names: %s", ','.join(sorted(ddict)))

        return cache_opts

    def get_data_reader_options(self, section=None):
        """
        Read options from the [data_reader] section of the app config file.
        This section should contain the following options::

            [data_reader]
            file_select_method=<method>
            source_type=<type>            # single_directory or data_cache
            input_dir=<dir-path>          # path of single directory
            input_file_format=<format>    # e.g. ff or pp
            input_filename_template=<template-string>
            timestamp_filename_template=<template-string>

        :param str section: The name of the section to read from the app config
            file (default: 'data_reader').
        :returns: An afterburner.utils.NamespacePlus object whose attributes
            record options defined under the [data_reader] section of the app
            config file.
        """

        try:
            section = section or DATA_READER_SECTION
            ddict = self.app_config.section_to_dict(section)
            ddict = {k: decode_string_value(v) for k, v in ddict.items()}
            reader_opts = NamespacePlus(**ddict)
        except ValueError:
            raise AppConfigError("Unable to find a section named '{0}' in the "
                "app config file".format(section))

        if not reader_opts.file_select_method:
            if self.cylc.is_active:
                reader_opts.file_select_method = 'sentinel_files'
            else:
                reader_opts.file_select_method = 'modification_time'

        self.logger.debug("Data reader option names: %s", ','.join(sorted(ddict)))

        return reader_opts

    def get_data_writer_options(self, section=None):
        """
        Read options from the [data_writer] section of the app config file.
        This section should contain the following options::

            [data_writer]
            target_type=<type>      # single_directory only at present
            output_dir=<dir-path>   # path of single directory
            output_file_format=nc   # currently only nc is supported
            output_filename_template=<template-string>

        :param str section: The name of the section to read from the app config
            file (default: 'data_writer').
        :returns: An afterburner.utils.NamespacePlus object whose attributes
            record options defined under the [data_writer] section of the app
            config file.
        """

        try:
            section = section or DATA_WRITER_SECTION
            ddict = self.app_config.section_to_dict(section)
            ddict = {k: decode_string_value(v) for k, v in ddict.items()}
            writer_opts = NamespacePlus(**ddict)
        except ValueError:
            raise AppConfigError("Unable to find a section named '{0}' in the "
                "app config file".format(section))

        # Add custom code here.

        self.logger.debug("Data writer option names: %s", ','.join(sorted(ddict)))

        return writer_opts

    def get_netcdf_saver_options(self, section=None):
        """
        Read netCDF saver options from the [netcdf_saver] section of the app
        config file. This section may contain the following options::

            [netcdf_saver]
            append=<true-or-false>
            complevel=<compression-level>
            contiguous<true-or-false>
            fletcher32=<true-or-false>
            least_significant_digit=<integer>
            netcdf_format=<format>
            overwrite=<true-or-false>
            shuffle=<true-or-false>
            unlimited_dimensions=<dimname1,dimname2,...>
            zlib=<true-or-false>

        :param str section: The name of the section to read from the app config
            file (default: 'netcdf_saver').
        :returns: An afterburner.utils.NamespacePlus object whose attributes
            record options defined under the [netcdf_saver] section of the app
            config file.
        """

        try:
            section = section or NETCDF_SAVER_SECTION
            ddict = self.app_config.section_to_dict(section)
            netcdf_opts = NamespacePlus(**ddict)
        except ValueError:
            raise AppConfigError("Unable to find a section named '{0}' in the "
                "app config file".format(section))

        if netcdf_opts.overwrite:
            netcdf_opts.overwrite = is_true(netcdf_opts.overwrite)

        if netcdf_opts.append:
            netcdf_opts.append = is_true(netcdf_opts.append)

        if netcdf_opts.unlimited_dimensions:
            netcdf_opts.unlimited_dimensions = [s.strip() for s in
                netcdf_opts.unlimited_dimensions.split(',')]

        if netcdf_opts.zlib:
            netcdf_opts.zlib = is_true(netcdf_opts.zlib)

        if netcdf_opts.shuffle:
            netcdf_opts.shuffle = is_true(netcdf_opts.shuffle)

        if netcdf_opts.fletcher32:
            netcdf_opts.fletcher32 = is_true(netcdf_opts.fletcher32)

        if netcdf_opts.contiguous:
            netcdf_opts.contiguous = is_true(netcdf_opts.contiguous)

        if netcdf_opts.complevel:
            netcdf_opts.complevel = int(netcdf_opts.complevel)

        if netcdf_opts.least_significant_digit:
            netcdf_opts.least_significant_digit = int(netcdf_opts.least_significant_digit)

        self.logger.debug("NetCDF option names: %s", ','.join(sorted(ddict)))

        return netcdf_opts

    def get_model_options(self, namelist=None):
        """
        Read config options for one or more climate models and store them in a
        dictionary of afterburner.utils.NamespacePlus objects. At present only
        the following options are recognised (and only for the UM)::

            [namelist:models(um)]
            cylc_task_name=atmos_main
            sentinel_file_ext=.arch

        :param str namelist: The name of the namelist containing model definitions
            (default: 'models').
        :returns: A dictionary of afterburner.utils.NamespacePlus objects, one
            for each model defined in the 'models' namelist.
        """

        model_opts = {}
        namelist = namelist or MODELS_NAMELIST

        for mdict in self.app_config.iter_nl(namelist):
            idx = mdict.pop('_index')
            model_name = idx.upper()
            mdict = {k: decode_string_value(v) for k, v in mdict.items()}
            opts = NamespacePlus(**mdict)
            opts.namelist_id = idx

            # If the sentinel_file_ext option is defined, make sure it starts
            # with a '.' character.
            if opts.sentinel_file_ext and not opts.sentinel_file_ext.startswith('.'):
                opts.sentinel_file_ext = '.' + opts.sentinel_file_ext

            model_opts[model_name] = opts

        self.logger.debug("Model section names: %s", ','.join(sorted(model_opts)))

        return model_opts

    def get_processor_definitions(self, namelist=None):
        """
        Read processor definitions from the app config file.

        :param str namelist: The namelist containing processor definitions
            (default: 'processors').
        :returns: An afterburner.utils.NamespacePlus object whose attributes
            record options defined under the [processor] section of the app config
            file.
        """

        proc_defns = {}
        namelist = namelist or PROCESSORS_NAMELIST
        nerrors = 0

        for ddict in self.app_config.iter_nl(namelist):
            idx = ddict.pop('_index')
            ddict = {k: decode_string_value(v) for k, v in ddict.items()}
            pdefn = NamespacePlus(**ddict)
            pdefn.key = idx
            pdefn.namelist_id = idx
            pdefn.instance = None

            # Check that the class_path option has been specified.
            if not pdefn.class_path:
                self.logger.error("The 'class_path' property must been defined "
                    "for the processor named %s.", idx)
                nerrors += 1
                continue

            # Extract any arguments that will be used to instantiate the processor object.
            init_args = {}
            for key, value in ddict.items():
                if key.startswith('init_') and value is not None:
                    init_args[key[5:]] = value
            pdefn.init_args = init_args

            proc_defns[pdefn.key] = pdefn

        if nerrors:
            msg = "{0} error(s) encountered in processor definitions.".format(nerrors)
            self.logger.error(msg)
            raise AppConfigError(msg)

        ids = [x.namelist_id for x in proc_defns.values()]
        self.logger.debug("Processor ids: %s", ','.join(sorted(ids)))

        if 'null' not in proc_defns:
            null_proc = NamespacePlus(class_path='afterburner.processors.NullProcessor',
                key='null', namelist_id='null')
            proc_defns['null'] = null_proc

        return proc_defns

    def get_source_diag_defaults(self, namelist=None, diag_name=None):
        """
        Read default options from the diagnostic named '_defaults_' in the
        SOURCE_DIAGS_NAMELIST portion of the configuration file.

        For the majority of applications default values should be supplied for
        at least the following options/properties:

        * suite_name (unless this value can be obtained from CYLC_SUITE_NAME)
        * model_name (e.g. 'UM', 'NEMO', etc)
        * streams (e.g. 'apm,apy')

        Depending on the nature of the source model data, other options for which
        default values can usefully be supplied include:

        * realization
        * lbtim
        * lbproc

        :param str namelist: The name of the namelist containing source diagnostic
            definitions (default: 'source_diagnostics').
        :param str diag_name: The name of the diagnostic used to store default
            settings to apply to other diagnostic definitions (default: '_defaults_').
        :returns: An afterburner.utils.NamespacePlus object whose attributes
            record diagnostic default settings.
        :raises AppConfigError: Raised if the expected default diagnostic entry
            does not appear in the app config file.
        """

        diag_defs = None
        namelist = namelist or SOURCE_DIAGS_NAMELIST
        diag_name = diag_name or DEFAULT_DIAGNOSTIC_NAME

        for ddict in self.app_config.iter_nl(namelist):
            if ddict.get('_index', '') == diag_name:
                idx = ddict.pop('_index')
                ddict = {k: decode_string_value(v) for k, v in ddict.items()}
                diag_defs = NamespacePlus(**ddict)
                diag_defs.namelist_id = idx
                break

        if not diag_defs:
            raise AppConfigError("Unable to find a source diagnostic named '{0}' "
                "in the app config file.".format(diag_name))

        if diag_defs.enabled is None:
            diag_defs.enabled = True

        # Copy model and simulation attributes from the general_opts object.
        diag_defs.model_name = self.general_opts.model_name
        diag_defs.suite_name = self.general_opts.suite_name
        diag_defs.realization = self.general_opts.realization
        diag_defs.streams = self.general_opts.streams

        # Create aliases of key attributes for use in metavariables and filename
        # templates.
        diag_defs.model = diag_defs.model_name
        diag_defs.suite = diag_defs.suite_id = diag_defs.suite_name
        diag_defs.runid = diag_defs.suite_name.split('-')[-1]
        diag_defs.realization_id = diag_defs.realization

        # Assign default values for lbtim, lbproc, calendar, and reinit interval.
        if diag_defs.lbtim is None: diag_defs.lbtim = 122
        if diag_defs.lbproc is None: diag_defs.lbproc = 128
        if diag_defs.calendar is None: diag_defs.calendar = cfu.CALENDAR_360_DAY
        if diag_defs.reinit is None: diag_defs.reinit = 0

        return diag_defs

    def get_source_diag_definitions(self, namelist=None):
        """
        Read all of the source diagnostic definitions from the SOURCE_DIAGS_NAMELIST
        portion of the app configuration file. Each diagnostic definition is
        augmented with any additional default options, i.e. those defined against
        the source diagnostic named '_defaults_'.

        :param str namelist: The name of the namelist containing source diagnostic
            definitions (default: 'source_diagnostics').
        :returns: A dictionary of afterburner.utils.NamespacePlus objects, each
            one specifying a diagnostic definition.
        """

        diag_defns = {}
        namelist = namelist or SOURCE_DIAGS_NAMELIST
        defaults = self.source_diag_defaults
        nerrors = 0

        for ddict in self.app_config.iter_nl(namelist):
            if ddict.get('_index', '') == DEFAULT_DIAGNOSTIC_NAME: continue
            idx = ddict.pop('_index')
            ddict = {k: decode_string_value(v) for k, v in ddict.items()}
            ddefn = NamespacePlus(**ddict)
            ddefn.key = idx
            ddefn.namelist_id = idx
            ddefn.role = 'source'

            # Copy over diagnostic default values for any undefined attributes.
            if defaults:
                for att in defaults.iter_names():
                    if getattr(ddefn, att, None) is None:
                        setattr(ddefn, att, getattr(defaults, att))

            # Assign a name for the current diagnostic.
            ddefn.name = self.make_source_diag_name(ddefn)

            diag_defns[ddefn.key] = ddefn

        if nerrors:
            msg = "{0} error(s) encountered in source diagnostic definitions.".format(nerrors)
            self.logger.error(msg)
            raise AppConfigError(msg)

        ids = [x.namelist_id for x in diag_defns.values()]
        self.logger.debug("Source diagnostic ids: %s", ','.join(sorted(ids)))

        return diag_defns

    def get_target_diag_defaults(self, namelist=None, diag_name=None):
        """
        Read default options from the diagnostic named '_defaults_' in the
        TARGET_DIAGS_NAMELIST portion of the configuration file.

        For the majority of applications default values should be supplied for
        at least the following options/properties:

        * streams (e.g. 'apm,apy')

        :param str namelist: The name of the namelist containing target diagnostic
            definitions (default: 'target_diagnostics').
        :param str diag_name: The name of the diagnostic used to store default
            settings to apply to other diagnostic definitions (default: '_defaults_').
        :returns: An afterburner.utils.NamespacePlus object whose attributes
            record diagnostic default settings.
        :raises AppConfigError: Raised if the expected default diagnostic entry
            does not appear in the app config file.
        """

        diag_defs = None
        namelist = namelist or TARGET_DIAGS_NAMELIST
        diag_name = diag_name or DEFAULT_DIAGNOSTIC_NAME

        for ddict in self.app_config.iter_nl(namelist):
            if ddict.get('_index', '') == diag_name:
                idx = ddict.pop('_index')
                ddict = {k: decode_string_value(v) for k, v in ddict.items()}
                diag_defs = NamespacePlus(**ddict)
                diag_defs.namelist_id = idx
                break

        if not diag_defs:
            raise AppConfigError("Unable to find a target diagnostic named '{0}' "
                "in the app config file.".format(diag_name))

        if diag_defs.enabled is None:
            diag_defs.enabled = True

        # Copy model and simulation attributes from the general_opts object.
        diag_defs.model_name = self.general_opts.model_name
        diag_defs.suite_name = self.general_opts.suite_name
        diag_defs.realization = self.general_opts.realization
        diag_defs.streams = self.general_opts.streams

        # Create aliases of key attributes for use in metavariables and filename
        # templates.
        diag_defs.model = diag_defs.model_name
        diag_defs.suite = diag_defs.suite_id = diag_defs.suite_name
        diag_defs.runid = diag_defs.suite_name.split('-')[-1]
        diag_defs.realization_id = diag_defs.realization

        return diag_defs

    def get_target_diag_definitions(self, namelist=None):
        """
        Read all of the target diagnostic definitions from the TARGET_DIAGS_NAMELIST
        portion of the app configuration file. Each diagnostic definition is
        augmented with any additional default options, i.e. those defined against
        the target diagnostic named '_defaults_'.

        Values should be specified for at least the following options/properties:

        * one or more of: standard_name, long_name, or var_name
        * sources

        :param str namelist: The name of the namelist containing target diagnostic
            definitions (default: 'target_diagnostics').
        :returns: A dictionary of afterburner.utils.NamespacePlus objects, each
            one specifying a diagnostic definition.
        """

        diag_defns = {}
        namelist = namelist or TARGET_DIAGS_NAMELIST
        defaults = self.target_diag_defaults
        nerrors = 0

        for ddict in self.app_config.iter_nl(namelist):
            if ddict.get('_index', '') == DEFAULT_DIAGNOSTIC_NAME: continue
            idx = ddict.pop('_index')
            ddict = {k: decode_string_value(v) for k, v in ddict.items()}
            ddefn = NamespacePlus(**ddict)
            ddefn.key = idx
            ddefn.namelist_id = idx
            ddefn.role = 'target'

            # Copy over diagnostic default values for any undefined attributes.
            if defaults:
                for att in defaults.iter_names():
                    if getattr(ddefn, att, None) is None:
                        setattr(ddefn, att, getattr(defaults, att))

            # Assign a name for the current diagnostic.
            ddefn.name = self.make_target_diag_name(ddefn)

            # Check that each source diagnostic referenced by the 'sources'
            # attribute has an associated definition.
            if not ddefn.sources:
                msg = ("The 'sources' property must be defined for target "
                    "diagnostic {0}.".format(idx))
                self.logger.error(msg)
                nerrors += 1
            elif ddefn.enabled:
                for src_idx in [s.strip() for s in ddefn.sources.split(',')]:
                    if src_idx not in self.source_diag_defns:
                        msg = ("Target diagnostic {0} refers to an undefined "
                            "source diagnostic named {1}".format(idx, src_idx))
                        self.logger.error(msg)
                        nerrors += 1

            # Check that the processor referenced by the 'processor' attribute
            # has an associated definition.
            if not ddefn.processor:
                msg = ("The 'processor' property must be defined for target "
                    "diagnostic {0}.".format(idx))
                self.logger.error(msg)
                nerrors += 1
            elif ddefn.enabled:
                if ddefn.processor not in self.processor_defns:
                    msg = ("Target diagnostic {0} refers to an undefined "
                        "processor named {1}".format(idx, ddefn.processor))
                    self.logger.error(msg)
                    nerrors += 1

            diag_defns[ddefn.key] = ddefn

        if nerrors:
            msg = "{0} error(s) encountered in target diagnostic definitions.".format(nerrors)
            self.logger.error(msg)
            raise AppConfigError(msg)

        ids = [x.namelist_id for x in diag_defns.values()]
        self.logger.debug("Target diagnostic ids: %s", ','.join(sorted(ids)))

        return diag_defns

    def get_target_diag_keys(self, enabled=False, sort=False):
        """
        Return a list of target diagnostic keys, optionally sorted.

        :param bool enabled: If this argument evaluates to true then only keys
            for enabled diagnostics are returned.
        :param bool sort: If this argument evaluates to true then the list of
            keys is sorted.
        :returns: A list of target diagnostic keys.
        """
        if enabled:
            keys = [k for k in self.target_diag_defns if k.enabled]
        else:
            keys = list(self.target_diag_defns)

        return sorted(keys) if sort else keys

    def iter_target_diags(self, enabled=False, sort=False):
        """
        Generate a sequence of target diagnostic definition objects, optionally
        sorted by key.

        :param bool enabled: If this argument evaluates to true then only
            enabled diagnostics are returned.
        :param bool sort: If this argument evaluates to true then the diagnostic
            definition objects are returned sorted by their key attribute.
        :returns: A sequence of target diagnostic definition objects.
        """
        for key in self.get_target_diag_keys(enabled=enabled, sort=sort):
            yield self.target_diag_defns[key]

    def iter_source_diags(self, target_diag):
        """
        Generate a sequence of source diagnostic definition objects associated,
        via the 'sources' attribute, with the specified target diagnostic.
        """
        if not target_diag.sources: return

        for key in [s.strip() for s in target_diag.sources.split(',')]:
            yield self.source_diag_defns[key]

    def augment_diag_definition(self, diag_defn, stream):
        """
        Augment a diagnostic definition with attributes taken from the current
        context and stream. This method should be overridden if additional, or
        different, behaviour is required.

        :param afterburner.utils.NamespacePlus diag_defn: A namespace object
            containing the diagnostic definition.
        :param str stream: The name of the current stream.
        """
        diag_defn.stream = diag_defn.stream_id = stream
        diag_defn.realm = stream[0]
        diag_defn.dotstream = stream[0] + '.' + stream[1:]

        if is_msi_stash_code(diag_defn.var_id or ''):
            diag_defn.stash_code = diag_defn.var_id

        diag_defn.cycle_point = self.cylc.task_cycle_point or 'R1'

    def create_processor(self, proc_name):
        """
        Create an instance of the processor class identified by the supplied
        processor namelist id. The created instance is cached and returned if
        a subsequent request is made for the same processor name.

        :param str proc_name: The namelist id of the processor definition.
        :returns: The created processor instance.
        """

        proc_defn = self.processor_defns[proc_name]

        if not proc_defn.instance:
            try:
                klass = get_class_object_from_class_path(proc_defn.class_path)
                self.logger.info("Creating an instance of processor class %s ...",
                    klass.__name__)
                if proc_defn.init_args:
                    processor = klass(**proc_defn.init_args)
                else:
                    processor = klass()
                proc_defn.instance = processor
            except:
                self.logger.error("Error trying to instantiate class '%s'.",
                    proc_defn.class_path)
                raise

        return proc_defn.instance

    def create_metavariable(self, diag_defn):
        """
        Create a MetaVariable object from the specified diagnostic definition. The
        latter object is assumed to contain all the mandatory attributes needed to
        create the MetaVariable instance.

        :param afterburner.utils.NamespacePlus diag_defn: A namespace object
            containing the diagnostic definition.
        :returns: An instance of a subclass of afterburner.metavar.MetaVariable,
            the subclass type depending on the diag_defn.model_name property.
        """

        diag_dict = vars(diag_defn).copy()
        model_name = diag_dict.pop('model_name', 'undefined')
        model_vn = diag_dict.pop('model_vn', '0')
        suite_id = diag_dict.pop('suite_id', 'undefined')

        # Add a time_range key to the dictionary if the diagnostic definition
        # has start_date and/or end_date attributes.
        if 'time_range' not in diag_dict:
            start_date = diag_dict.pop('start_date', None)
            end_date = diag_dict.pop('end_date', None)
            if start_date or end_date:
                diag_dict['time_range'] = (start_date, end_date)

        try:
            metavar = MetaVariable.create_variable(model_name, model_vn, suite_id,
                **diag_dict)
        except AfterburnerError:
            self.logger.error("Error trying to create metavariable object for "
                "source diagnostic %s.", diag_defn.name)
            raise

        return metavar

    def create_directories(self):
        """
        Create any directories required by the app. Typically it is desirable to
        create those directories that will be used to store various output files
        produced by the application.

        By default this method creates any directories that are specified via
        options matching the string pattern "*_dir" in the [data_writer] section
        of the app config file. Intermediate directories are created as necessary.

        This method should be overridden if application-specific behaviour is
        required.
        """
        self.logger.info("Creating directories ...")

        optnames = [opt for opt in self.data_writer_opts.iter_names() if
                    opt.endswith('_dir')]

        for opt in optnames:
            dirpath = getattr(self.data_writer_opts, opt)
            if dirpath:
                dirpath = expand_path(dirpath)
                setattr(self.data_writer_opts, opt, dirpath)
                if not os.path.exists(dirpath):
                    os.makedirs(dirpath)
                    self.logger.debug("Created directory %s.", dirpath)

    def create_filename_providers(self):
        """
        Create any filename provider objects required by the app. By default
        template-driven filename provider objects are created for any options
        matching the string pattern "*_filename_template" in the [data_reader]
        and [data_writer] sections of the app config file.

        This method should be overridden if application-specific behaviour is
        required.
        """
        self.logger.info("Creating filename providers ...")

        for key, value in self.data_reader_opts:
            if key.endswith('_filename_template') and value:
                templ = os.path.expandvars(value)
                fnatt = key.rpartition('_')[0] + '_provider'
                setattr(self, fnatt, TemplateDrivenFilenameProvider(templ))
                self.logger.debug("Created filename provider for template '%s'.", value)

        for key, value in self.data_writer_opts:
            if key.endswith('_filename_template') and value:
                templ = os.path.expandvars(value)
                fnatt = key.rpartition('_')[0] + '_provider'
                setattr(self, fnatt, TemplateDrivenFilenameProvider(templ))
                self.logger.debug("Created filename provider for template '%s'.", value)

    def create_data_writer(self):
        """
        Create a data writer object based on the options specified under the
        [data_writer] section of the app config file.
        """

        # Create a netCDF writer object to handle file output.
        if self.data_writer_opts.output_file_format in ('nc', 'netcdf'):
            self.data_writer = NetcdfFileWriter(**vars(self.netcdf_opts))
            self.logger.info("Instantiated a netCDF-based data writer object.")
        else:
            msg = "Unsupported output file format: {0}".format(
                self.data_writer_opts.output_file_format)
            self.logger.error(msg)
            raise AppConfigError(msg)

    def setup_data_cache(self):
        """
        Set up a connection to the input data cache, if one has been specified
        under the [data_cache] section of the app config file. This section
        should contain the following options::

            [data_cache]
            cache_scheme=<scheme-name>    # e.g. SingleDirectory or StreamSplit
            base_dir=<dir-path>
            datastore_id=<datastore-id>   # e.g. MASS
            read_only=<true-or-false>
        """
        try:
            opts = vars(self.data_cache_opts).copy()
            scheme = opts.pop('cache_scheme', '')
            if not scheme:
                raise AppConfigError("The [data_cache]cache_scheme option is "
                    "not defined in the app config file.")
            base_dir = opts.pop('base_dir')
            dstore_id = opts.pop('datastore_id', '')
            if dstore_id:
                datastore = DataStore.create_store(dstore_id)
            else:
                datastore = NullDataStore()
            self.logger.info("Configuring access to data cache rooted at %s ...",
                base_dir)
            dcache = DataCache.create_cache(scheme, datastore, base_dir, **opts)
            self.data_cache = dcache
        except AfterburnerError:
            self.logger.error("Problem trying to set up a data cache object.")
            raise

    # TODO: implement some manner of data_reader class to replace load methods?

    def load_stream_data(self, stream, diag_keys):
        """
        Load data for all of the diagnostics identified by the diag_keys argument
        and for the specified stream. This is done in order to avoid repeatedly
        reading the same data files for different diagnostics.

        Unless this method is overridden by a concrete subclass then the default
        implementation will attempt to load data either from a data cache, if one
        is configured in the [data_cache] section of the app config file, or else
        from a single directory, this being the one specified in the [data_reader]
        section of the app config file.

        The second of these two options is likely to be convenient in those
        cases where data is to be read from a set of files output to a single
        directory by a climate simulation. In the case of the Unified Model,
        for example, this is typically the directory pointed to by $DATAM.

        :param str stream: The name of the stream for which to load model data.
        :param list diag_keys: A list of source diagnostic keys.
        :returns: An Iris cubelist containing model data for the specified
            stream-plus-diagnostics combination. The cubelist will be empty if
            no data could be loaded.
        """

        if self.data_reader_opts.source_type == 'data_cache':
            cubes = self.load_stream_data_from_cache(stream, diag_keys)
        elif self.data_reader_opts.source_type == 'single_directory':
            cubes = self.load_stream_data_from_single_dir(stream, diag_keys)
        else:
            raise AppConfigError("No data source defined in the app config file.")

        self.logger.debug("Read in %d cubes:\n%s", len(cubes), cubes)

        return cubes

    def load_stream_data_from_cache(self, stream, diag_keys):
        """
        Load data for all diagnostics identified by the diag_keys argument from
        the data cache defined by the options in the [data_cache] section of the
        app config file. Refer to the :meth:`setup_data_cache` method for details.

        It should be noted that data cache classes do not currently support the
        use of sentinel files to filter the list of potential source files. That
        capability may be emulated, however, by attaching approprate time range
        information (i.e. start_date & end_date) to the diagnostic definitions.

        :param str stream: The name of the stream for which to load model data.
        :param list diag_keys: A list of source diagnostic keys.
        :returns: An Iris cubelist containing model data for the specified
            stream-plus-diagnostics combination. The cubelist will be empty if
            no data could be loaded.
        """

        self.logger.info("Loading cached model data for stream %s ...", stream)
        cubes = iris.cube.CubeList()

        # Create metavariable objects for each diagnostic identified by the
        # diag_keys list.
        metavars = []
        for key in diag_keys:
            diag_defn = self.source_diags_for_stream[key]
            metavar = self.create_metavariable(diag_defn)
            metavars.append(metavar)
            self.logger.debug("metavariable: %s", metavar)

        # Load cubes from the data cache.
        cubes = self.data_cache.load_data(metavars, minimal_data=True)

        return cubes

    def load_stream_data_from_single_dir(self, stream, diag_keys):
        """
        Load data for all diagnostics identified by the diag_keys argument from
        files residing in the single directory specified in the [data_reader]
        section of the app config file.

        :param str stream: The name of the stream for which to load model data.
        :param list diag_keys: A list of source diagnostic keys.
        :returns: An Iris cubelist containing model data for the specified
            stream-plus-diagnostics combination. The cubelist will be empty if
            no data could be loaded.
        """

        self.logger.info("Loading model data for stream %s ...", stream)
        cubes = iris.cube.CubeList()

        data_dir = self.data_reader_opts.input_dir
        if not os.path.isdir(data_dir):
            self.logger.warning("Data directory does not exist: %s", data_dir)
            return cubes

        # Obtain a handle to the first diagnostic definition.
        diag_defn = self.source_diags_for_stream[diag_keys[0]]
        model_defn = self.model_opts.get(diag_defn.model_name)

        # Obtain a list of potential input files by calling the input filename
        # provider.
        filenames = self.input_filename_provider.get_filenames(diag_defn)
        self.logger.debug("Candidate model data input filenames:\n%s", filenames)

        # If we're running under the control of a cylc task, check to see if we
        # need to filter the file list by sentinel files.
        if (self.data_reader_opts.file_select_method == 'sentinel_files' and
            self.cylc.is_active):
            filenames = _filter_files_by_sentinels(filenames, data_dir, model_defn)
            self.logger.debug("Filtered model data filenames:\n%s", filenames)

        # Otherwise filter the file list by modification time.
        elif self.data_reader_opts.file_select_method == 'modification_time':
            ts_file = self.make_timestamp_filename(diag_defn,
                self.timestamp_filename_provider)
            filenames = _filter_files_by_time(filenames, data_dir, ts_file)
            self.logger.debug("Filtered model data filenames:\n%s", filenames)

        if not filenames:
            self.logger.warning("No matching filenames found for this stream.")
            return cubes

        # FIXME: the logic below doesn't enable minimal data load operations.
        # Create a list of Iris load constraints, one for each target diagnostic.
        constraints = []
        var_ids = set(self.source_diags_for_stream[k].var_id for k in diag_keys)
        for var_id in var_ids:
            if is_msi_stash_code(var_id):
                constraints.append(iris.AttributeConstraint(STASH=var_id))
            else:
                constraints.append(iris.Constraint(name=var_id))

        # Load cubes from the selected files using the specified constraints.
        filepaths = [os.path.join(data_dir, f) for f in filenames]
        cubes = iris.load(filepaths, constraints)

        return cubes

    def extract_diag_data(self, stream_data, diag_defn):
        """
        Extract model data for the specified diagnostic from the stream_data
        cubelist. Ordinarily the diag_defn object should result in a single cube
        being extracted and returned. However, the application should handle the
        situation where multiple cubes are returned. If no data could be found
        then the function returns an empty cubelist.

        :param cubelist stream_data: A cubelist containing multiple diagnostics
            from a single model output stream.
        :param afterburner.utils.NamespacePlus diag_defn: A namespace object
            defining the diagnostic whose data is to be extracted.
        :returns: An Iris cubelist containing data for the specified diagnostic.
        """

        cubes = iris.cube.CubeList()
        fmt = self.data_reader_opts.input_file_format.lower()

        for source_diag in self.iter_source_diags(diag_defn):
            if fmt in ['ff', 'pp']:
                kubes = _extract_pp_model_data(stream_data, source_diag)
            elif fmt == 'nc':
                kubes = _extract_nc_model_data(stream_data, source_diag)
            else:
                raise AppConfigError("Unsupported input file format: " + fmt)
            cubes.extend(kubes)

        return cubes

    def save_diag_data(self, cubes, diag_defn):
        """
        Save a cubelist of model data to the output directory defined in
        the app config file. The name of the output file is generated from the
        attributes attached to the diag_defn object.

        :param iris.cube.CubeList cubes: The cubes to save.
        :param afterburner.utils.NamespacePlus diag_defn: A namespace object
            containing the diagnostic definition.
        """

        filename = self.make_output_filename(diag_defn, self.output_filename_provider)
        filepath = os.path.join(self.data_writer_opts.output_dir, filename)
        self.logger.info("Saving data to file %s ...", filename)

        if self.dry_run: return

        # The template-supplied filename might include '/' characters so the
        # following code attempts to create any intermediate subdirectories.
        dirpath = os.path.dirname(filepath)
        if not os.path.exists(dirpath): os.makedirs(dirpath)

        self.data_writer.run(cubes, filepath)

    def make_output_filename(self, diag_defn, filename_provider, ext=''):
        """
        Use the filename provider object to construct the name of the output file
        to use for the diagnostic defined by the diag_defn argument. Typically,
        though not always, the filename provider will deal with a file extension.
        If not then it can be specified explicitly via the ext keyword argument.

        :param afterburner.utils.NamespacePlus diag_defn: A namespace object
            containing the diagnostic definition.
        :param FilenameProvider filename_provider: The filename provider object
            that will be used to generate a filename from the diag_defn object.
        :param str ext: The extension, if any, to append to the filename string.
        :returns: The generated filename.
        """

        try:
            filenames = filename_provider.get_filenames(diag_defn)
        except:
            msg = "Unable to construct output filename for diagnostic {0}.".format(
                diag_defn.name)
            self.logger.error(msg)
            raise

        if filenames:
            filename = filenames[0]
            if ext: filename += ext
        else:
            msg = "Unable to construct output filename for diagnostic {0}.".format(
                diag_defn.name)
            raise DataProcessingError(msg)

        return filename

    def make_timestamp_filename(self, diag_defn, filename_provider):
        """
        Construct the full pathname of a timestamp file for use with the specified
        diagnostic.

        :param afterburner.utils.NamespacePlus diag_defn: A namespace object
            containing the diagnostic definition.
        :param FilenameProvider filename_provider: The filename provider object
            that will be used to generate a filename from the diag_defn object.
        :returns: The generated filename.
        """

        if self.cylc.is_active:
            ts_dir = os.path.join(self.cylc.suite_share_dir, self.cylc.task_name)
        else:
            ts_dir = self.data_writer_opts.output_dir

        if filename_provider:
            try:
                filenames = filename_provider.get_filenames(diag_defn)
                ts_file = filenames[0]
            except:
                msg = "Unable to construct timestamp filename for diagnostic {0}.".format(
                    diag_defn.name)
                self.logger.error(msg)
                raise
        else:
            ts_file = "{0}_{1}_timestamp".format(diag_defn.runid, diag_defn.stream)

        return os.path.join(ts_dir, ts_file)


def _get_stream_list(diag_defns):
    """
    Determine the full list of target streams for which diagnostics have been
    specified. The returned list is sorted alphabetically.

    :param dict diag_defns: A dictionary of diagnostic definition objects keyed
        by a unique combination of diagnostic attributes.
    :returns: A sorted list of unique stream names.
    """
    stream_list = set()

    for ddefn in diag_defns.values():
        streams = ddefn.streams
        if streams:
            stream_list.update([s.strip() for s in streams.split(',')])

    return sorted(stream_list)


def _get_stream_diag_list(stream, diag_defns, enabled=False):
    """
    Determine the full list of diagnostic keys associated with the specified
    stream.

    :param str stream: The name of the stream.
    :param dict diag_defns: A dictionary of diagnostic definition objects keyed
        by a unique combination of diagnostic attributes.
    :param bool enabled: If this argument evaluates to true then only
        user-enabled diagnostics are included in the returned list.
    :returns: A sorted list of keys to diagnostic definitions.
    """
    diag_list = []

    for ddefn in diag_defns.values():
        if enabled and not ddefn.enabled:
            continue
        streams = ddefn.streams
        if streams and stream in [s.strip() for s in streams.split(',')]:
            diag_list.append(ddefn.key)

    return sorted(diag_list)


def _get_diag_metadata(diag_defn):
    """
    Return a dictionary of any cube metadata attributes attached to the specified
    diagnostic definition. The current list of searched for attributes includes:
    'standard_name', 'long_name', 'var_name', and 'units'.

    :param afterburner.utils.NamespacePlus diag_defn: A namespace object defining
        the diagnostic from which to obtain metadata attributes.
    :returns: A dictionary of metadata attributes.
    """
    metadata = {}

    for att in ['standard_name', 'long_name', 'var_name', 'units']:
        if getattr(diag_defn, att, None):
            metadata[att] = getattr(diag_defn, att)

    return metadata


def _extract_pp_model_data(stream_data, diag_defn):
    """
    Extract PP-based model data for the specified diagnostic from the stream_data
    cubelist.

    :param cubelist stream_data: A cubelist representing multiple diagnostics
        from a single PP-type model output stream.
    :param afterburner.utils.NamespacePlus diag_defn: A namespace object defining
        the diagnostic to extract from the stream_data cubelist.
    :returns: A cubelist containing all cubes that match the given diagnostic.
    """

    # Add a STASH code or name constraint.
    if is_msi_stash_code(diag_defn.var_id):
        constraints = iris.AttributeConstraint(STASH=diag_defn.var_id)
    else:
        constraints = iris.Constraint(name=diag_defn.var_id)

    # Add a cell method constraint if required.
    if diag_defn.lbproc is not None:
        method = cf_cell_method_from_lbproc(diag_defn.lbproc)
        if diag_defn.lbtim:
            nhours = diag_defn.lbtim // 100
            interval = "{} hour".format(nhours)
        else:
            interval = None
        constraints &= iris.Constraint(cube_func=make_cell_method_cube_func(
            method, 'time', interval=interval))

    # Add a calendar constraint.
    if diag_defn.calendar:
        constraints &= iris.Constraint(cube_func=make_calendar_type_cube_func(
            diag_defn.calendar))

    cubes = stream_data.extract(constraints)

    return cubes


def _extract_nc_model_data(stream_data, diag_defn):
    """
    Extract netCDF-based model data for the specified diagnostic from the
    stream_data cubelist.

    :param cubelist stream_data: A cubelist representing multiple diagnostics
        from a single netCDF-type model output stream.
    :param afterburner.utils.NamespacePlus diag_defn: A namespace object defining
        the diagnostic to extract from the stream_data cubelist.
    :returns: A cubelist containing all cubes that match the given diagnostic.
    """

    constraints = iris.Constraint(name=diag_defn.var_id)
    # or, to constrain explicitly on the cube.var_name attribute
    #constraints = iris.Constraint(cube_func=lambda c: c.var_name == diag_defn.var_id)

    # Add a cell method constraint if required.
    if diag_defn.lbproc is not None:
        method = cf_cell_method_from_lbproc(diag_defn.lbproc)
        if diag_defn.lbtim:
            nhours = diag_defn.lbtim // 100
            interval = "{} hour".format(nhours)
        else:
            interval = None
        constraints &= iris.Constraint(cube_func=make_cell_method_cube_func(
            method, 'time', interval=interval))

    # Add a calendar constraint.
    if diag_defn.calendar:
        constraints &= iris.Constraint(cube_func=make_calendar_type_cube_func(
            diag_defn.calendar))

    cubes = stream_data.extract(constraints)

    return cubes

def _filter_files_by_time(filenames, data_dir, timestamp_file):
    """
    Filters a list of filenames, retaining only those whose modification time is
    more recent than the datetime defined in a timestamp file, the name of which
    is specific to each stream-diagnostic combination. If the timestamp file does
    not exist then it is created and updated with the timestamp of the most
    recent file in the supplied list of filenames.

    :param list filenames: The list of filenames to filter.
    :param str data_dir: The pathname of the directory containing the files.
    :param str timestamp_file: The full pathname of the timestamp file, which
        will be created if it doesn't exist.
    :returns: A filtered list of filenames.
    """

    # Expand the (possibly wildcarded) input filenames.
    input_files = expand_filenames(filenames, dirname=data_dir)

    # If the timestamp file exists then read the timestamp and check to see if
    # any of the passed in files are newer.
    if os.path.exists(timestamp_file):
        timestamp = deserialize_timestamp(timestamp_file)
        _logger.debug("Filtering files newer than %s.", timestamp)
        newer_files = list_files_newer_than(data_dir, timestamp)
        if newer_files:
            filt_files = list(set(input_files) & set(newer_files))
        else:
            filt_files = []
    else:
        filt_files = input_files

    # If some filtered files were found then save the timestamp of the most
    # recent file.
    if filt_files:
        timestamp = _get_latest_mod_time([os.path.join(data_dir, fn)
            for fn in filt_files])
        _logger.debug("Storing timestamp %s in file %s.", timestamp, timestamp_file)
        try:
            serialize_timestamp(timestamp_file, timestamp)
        except Exception as exc:
            _logger.error("Error trying to write to timestamp file %s.", timestamp_file)
            _logger.error(str(exc))

    return filt_files


def _filter_files_by_sentinels(filenames, data_dir, model_defn):
    """
    Filters a list of filenames, removing any files for which a corresponding
    sentinel file does not exist. The filter operation is only applied if the
    app is running under the control of a cylc task, in which case the model_defn
    object is queried to obtain the directory containing sentinel files and also
    the sentinel filename extension.

    :param list filenames: The list of filenames to filter.
    :param str data_dir: The pathname of the directory containing the files.
    :param afterburner.utils.NamespacePlus model_defn: A namespace object that
        contains configuration settings for a climate model, such as the UM.
    :returns: A filtered list of filenames.
    """

    # Check that model_defn is not null.
    if not model_defn:
        return filenames

    # Check that the model definition includes the name of the cylc task that
    # runs the model, and the name of the extension used by sentinel files.
    if not (model_defn.cylc_task_name and model_defn.sentinel_file_ext):
        return filenames

    sentinel_ext = model_defn.sentinel_file_ext
    sentinel_dir = get_cylc_task_work_dir(model_defn.cylc_task_name)
    sentinel_files = expand_filenames(['*'+sentinel_ext], dirname=sentinel_dir)
    _logger.debug("Sentinel files in directory %s:\n%s", sentinel_dir, sentinel_files)

    # This argument is needed to deal with the fact that sentinel files created
    # by the postproc app do not include the '.pp' token.
    ignore_file_ext = '.pp' if filenames[0].endswith('.pp') else ''

    filenames = filter_by_sentinel_files(filenames, data_dir,
        sentinel_dir=sentinel_dir, sentinel_file_ext=sentinel_ext,
        ignore_file_ext=ignore_file_ext)

    return filenames


def _get_latest_mod_time(filepaths):
    """
    Get the latest modified time for the specified list of filepaths.

    :param iterable filepaths: An iterable of filepaths from which to determine
        the latest modified time.
    :returns: A datetime object representing the latest modified time.
    """

    times = []

    for fpath in filepaths:
        st = os.stat(fpath)
        times.append(datetime.datetime.fromtimestamp(st.st_mtime))

    sorted_times = sorted(times)

    return sorted_times[-1]
