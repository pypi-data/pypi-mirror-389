# (C) British Crown Copyright 2016-2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Calculate jet speed diagnostic from daily-mean wind speed data, either for a
single climate model run or an ensemble of runs.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import os
import re
import ast
import glob
import shutil
import logging
import tempfile
import datetime

import iris
try:
    from iris.util import equalise_attributes
except ImportError:
    from iris.experimental.equalise_cubes import equalise_attributes

from afterburner import compare_iris_version
from afterburner.io import moose
from afterburner.apps import AbstractApp
from afterburner.exceptions import AppConfigError, DataProcessingError
from afterburner.processors.diags.atmos.jet_speed import JetSpeed
from afterburner.utils.dateutils import pdt_from_date_string, pdt_to_nc_datetime
from afterburner.utils.fileutils import expand_path
from afterburner.utils.textutils import int_list_from_string


class JetSpeedCalculator(AbstractApp):
    """
    This app class calculates jet speed and jet latitude diagnostic data for a
    single climate model run or an ensemble of such runs. The computation procedure
    is based upon the method of T. Woollings, C. Czuchnicki & C. Franzke (2014)
    [http://dx.doi.org/10.1002/qj.2197].

    The diagnostics are calculated for a single pressure level (850 hPa by default)
    and over a limited geographical region (North Atlantic by default). Both of
    these constraints can be modified within the configuration file that is used
    to control the application. The calculation of the diagnostics is performed
    by the :class:`afterburner.processors.diags.atmos.jet_speed.JetSpeed` class.

    Calculated diagnostic data is output in netCDF format. By default the jet
    speed diagnostic values are encoded as a single netCDF variable, with the
    jet latitude values attached as an auxiliary coordinate variable. If desired
    the jet latitude values can alternatively be output as a separate netCDF
    variable.

    In the case where an ensemble of climate runs is being processed, the output
    netCDF variable(s) also feature an ensemble dimension which, in line with
    the CF conventions, is named 'realization' by default.

    For further details regarding how the jet speed application is configured
    please refer to the main app documentation, a link to which can be found
    under the Rose Applications :doc:`index page </rose_apps/index>`.
    """

    def __init__(self, arglist=None, **kwargs):
        """
        :param list arglist: List of raw options and/or arguments passed from the
            calling environment. Typically these will be unprocessed command-line
            arguments, e.g. ``['-f', 'foo', '--foe=fum', 'infile']``.
        """
        super(JetSpeedCalculator, self).__init__(version='1.0.0b2', **kwargs)

        # Parse command-line arguments and, if one was specified, a Rose
        # configuration file.
        self._parse_args(arglist, desc="Jet Speed Calculator: calculates jet "
            "speed and jet latitude from daily-mean wind speed data.")
        self._parse_app_config()
        self._set_message_level()

        # Default MASS data class from which to obtain input model data.
        self.moose_class = 'crum'

        # Default ensemble indicator. Gets set to true when the input data
        # represents an ensemble of climate simulations.
        self.is_ensemble = False

        # Model runid (e.g. abcde) or suite id (e.g. mi-ab123).
        self.suite_id = ''

        # Default model stream to use.
        self.stream_id = 'apa'

        # Default STASH code used to identify the u-windspeed diagnostic.
        self.stash_code = 'm01s30i201'

        # Default vertical coordinate (pressure level) to use.
        self.plevel = 850.0

        # Default time range to use. If undefined (the default) then the full
        # time range of data available within MASS is used.
        self.time_range = None

        # Default ensemble members to process. '*' selects all members.
        self.ensemble_members = '*'

        # Default ensemble axis name.
        self.ensemble_axis_name = 'realization'

        # Default regular expression used to decode ensemble number from
        # ensemble member name.
        self.ensemble_regex = r'r(?P<R>\d+)i\d+p\d+'

        # Pathname of directory in which to store input model data, possibly
        # temporarily depending on the value of :attr:`keep_source_data`.
        self.input_data_dir = ''

        # Indicates whether or not to keep source data on disk after completion.
        self.keep_source_data = False

        # Default output filename.
        self.outfile = 'jet_speed.nc'

        # Default file overwrite setting.
        self.overwrite = False

        # Initialise cubes used to store final jet speed and latitude data.
        self.jet_speed_cube = None
        self.jet_lat_cube = None

    @property
    def cli_spec(self):
        """An argparse.Namespace object containing command-line option settings."""
        return [
            {'names': ['-c', '--config-file'],
                'help': 'Pathname of app configuration file'},
            {'names': ['--overwrite'], 'action': 'store_true',
                'default': False,
                'help': 'Force overwrite of output file if it exists'},
        ]

    def run(self):
        """Run the application."""

        self.logger.info("Started jet diagnostic processing...")
        self._get_app_options()
        self._get_sim_list()

        # Create an instance of the JetSpeed processor.
        proc_opts = self._get_jet_proc_options()
        jet_proc = JetSpeed(**proc_opts)

        # This variable is set to the length of the time axis of the first run.
        # Thereafter it is used to check that subsequent runs have the same length.
        ntimes = 0

        # Loop over the target model simulation(s).
        for sim_num, sim in self.sim_list:
            msg = "Processing simulation {0}: {1}".format(sim_num, sim)
            div = '-' * len(msg)
            self.logger.info('\n'.join(['', div, msg, div]))
            member = sim if sim != self.suite_id else None
            ucube = self._get_uwind_data(member=member)

            # Check for consistent time axis length.
            nt = len(ucube.coord('time').points)
            if ntimes == 0:
                ntimes = nt
            elif nt != ntimes:
                msg = "Length of time axis ({0}) in run '{1}' does not match\n" \
                      "length of time axis ({2}) in first run.".format(nt, sim, ntimes)
                raise DataProcessingError(msg)

            self.logger.info("Calculating jet speed and jet latitude data...")
            jet_cubes = jet_proc.run(ucube)
            if self.is_ensemble:
                self._concat_jet_cubes(jet_cubes)
            else:
                self.jet_speed_cube = jet_cubes[0]
                if len(jet_cubes) > 1: self.jet_lat_cube = jet_cubes[1]

        self._write_jet_data()

        self.logger.info("Processing completed.")

    def _get_app_options(self):
        """Read various properties from the app configuration file."""

        ### Read properties from the [input_data] section ###
        section = 'input_data'

        # Suite identifier.
        suite_id = self.app_config.get_property(section, 'suite_id')
        if not suite_id :
            raise AppConfigError("The 'suite_id' app configuration property ",
                "must be defined.")
        if suite_id.startswith('ens/'):
            self.suite_id = suite_id.split('/')[1]
            self.moose_class = 'ens'
            self.is_ensemble = True
        else:
            self.suite_id = suite_id

        # Ensemble properties.
        prop_names = ['ensemble_members', 'ensemble_axis_name']
        for name in prop_names:
            prop_val = self.app_config.get_property(section, name)
            if prop_val: setattr(self, name, prop_val)

        regex = self.app_config.get_property(section, 'ensemble_regex')
        if regex:
            try:
                # Usually it will be necessary to evaluate quoted regex strings
                # defined in the config file.
                regex = ast.literal_eval(regex)
            except:
                pass
            setattr(self, 'ensemble_regex', regex)

        # Stream, stashcode and pressure level settings.
        prop_names = ['stream_id', 'stash_code']
        for name in prop_names:
            prop_val = self.app_config.get_property(section, name)
            if prop_val: setattr(self, name, prop_val)
        prop_val = self.app_config.get_float_property(section, 'plevel')
        if prop_val is not None: self.plevel = prop_val

        # Time range setting.
        time_range_str = self.app_config.get_property(section, 'time_range')
        if time_range_str:
            time_range = time_range_str.strip().split()
            try:
                # Check that the date-time strings are valid.
                self.start_pdt = pdt_from_date_string(time_range[0], default=0)
                self.end_pdt = pdt_from_date_string(time_range[1], default=0)
                self.time_range = time_range
            except ValueError:
                msg = "Invalid time range definition: " + time_range_str
                msg += "\nPlease check date-time format and numeric values."
                self.logger.error(msg)
                raise AppConfigError(msg)

        # Directory in which to temporarily store model data files, or else
        # load data from existing files.
        data_dir = self.app_config.get_property(section, 'data_dir')
        if data_dir:
            data_dir = expand_path(data_dir)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            self.input_data_dir = data_dir
        else:
            self.input_data_dir = tempfile.mkdtemp(prefix='tmp_')
            self.logger.info("Created temporary directory '%s' to store model data.",
                self.input_data_dir)

        # Whether or not to keep source data on disk.
        prop_val = self.app_config.get_bool_property(section, 'keep_source_data')
        if prop_val is not None: self.keep_source_data = prop_val

        ### Read properties from the [output_data] section ###
        section = 'output_data'

        # Whether or not to overwrite output file if it exists.
        if self.cli_args.overwrite:
            self.overwrite = True   # overridden by command-line --overwrite option
        else:
            prop_val = self.app_config.get_bool_property(section, 'overwrite')
            if prop_val is not None: self.overwrite = prop_val

        # Pathname of netcdf output file.
        outfile = self.app_config.get_property(section, 'output_file')
        if not outfile :
            raise AppConfigError("The 'outfile' app configuration property ",
                "must be defined.")
        outfile = os.path.abspath(expand_path(outfile))
        if os.path.exists(outfile) and not self.overwrite:
            msg = "Output file exists but overwrite option was not enabled.\n" \
                  "Output file is: " + outfile
            self.logger.error(msg)
            raise AppConfigError(msg)
        outdir = os.path.dirname(outfile)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        self.outfile = outfile

    def _get_jet_proc_options(self):
        """
        Get jet diagnostic processing options from the application configuration
        file.
        """
        section = 'jet_speed'
        proc_opts = {}

        cutoff = self.app_config.get_float_property(section, 'lp_cutoff')
        if cutoff is not None: proc_opts['lp_cutoff'] = cutoff

        window = self.app_config.get_int_property(section, 'lp_window')
        if window is not None: proc_opts['lp_window'] = window

        twocubes = self.app_config.get_bool_property(section, 'twocubes')
        if twocubes is not None: proc_opts['twocubes'] = twocubes

        # The twocubes option must be set to True if an ensemble of climate
        # runs is being processed.
        if not proc_opts['twocubes'] and len(self.sim_list) > 1:
            proc_opts['twocubes'] = True
            self.logger.warning("Overriding the 'twocubes' option (from false to true).\n"
                "This option must be set to true for an ensemble of climate runs.")

        region = self.app_config.get_property(section, 'sector')
        if region:
            region = [float(x) for x in region.split(',')]
            proc_opts['sector'] = region

        # Pass current log level across to processor object.
        proc_opts['log_level'] = logging.getLevelName(self.logger.getEffectiveLevel())

        return proc_opts

    def _get_sim_list(self):
        """Build a list of the climate model simulations to be processed."""
        if self.is_ensemble:
            self.sim_list = self._get_ensemble_members()
        else:
            self.sim_list = [(1, self.suite_id)]

    def _get_ensemble_members(self):
        """Return a list of the ensemble member runs to be processed."""
        self.logger.info("Querying MASS to find ensemble members in suite %s...",
            self.suite_id)

        moose_uri = "moose:/ens/" + self.suite_id
        members = moose.list_files(moose_uri)
        if not members:
            raise DataProcessingError("No ensemble members found in suite %s" +
                self.suite_id)
        members = [m.rpartition('/')[2] for m in members]
        members.sort()   # sort into alphanumeric order

        # If all ensemble member runs were requested then return the full list.
        if self.ensemble_members == '*':
            all_members = True
            enums = []

        # Decode ensemble member numbers from the 'ensemble_members' property.
        else:
            all_members = False
            enums = int_list_from_string(self.ensemble_members)

        # Obtain the corresponding ensemble member runids by matching against the
        # regular expression defined in self.ensemble_regex.
        subset = []
        for m, member in enumerate(members):
            match = re.match(self.ensemble_regex, member)
            try:
                enum = int(match.group('R'))
                if all_members or enum in enums:
                    subset.append((enum, member))
            except:
                if all_members:
                    subset.append((m, member))

        if not subset:
            raise DataProcessingError("Unable to find any ensemble members "
                "matching numbers: " + self.ensemble_members)

        if len(subset) > 3:
            self.logger.info("Selected %s ensemble members: %s ... %s", len(subset),
                subset[0][1], subset[-1][1])
        else:
            self.logger.info("Selected %s ensemble members: %s", len(subset),
                ' '.join([x[1] for x in subset]))

        return subset

    def _get_uwind_data(self, member=None):
        """
        Return daily-mean u-windspeed data from the specified model run or ensemble
        member, retrieving input data from the MASS archive if necessary.
        """
        suite_id = self.suite_id
        runid = suite_id.split('-')[-1]
        collection = self.stream_id + '.pp'

        if member:
            # ensemble member
            dest_dir = os.path.join(self.input_data_dir, suite_id, member, self.stream_id)
            file_pttn = '{0}/{1}*{2}*.pp'.format(dest_dir, runid, member)
            moose_uri = "moose:/ens/{0}/{1}/{2}".format(suite_id, member, collection)

        else:
            # single runid
            dest_dir = os.path.join(self.input_data_dir, suite_id, self.stream_id)
            file_pttn = '{0}/{1}*.pp'.format(dest_dir, runid)
            moose_uri = "moose:/crum/{0}/{1}".format(suite_id, collection)

        # If necessary, create subdirectory in which to store temp PP data.
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        # Retrieve PP files from MASS if none already present.
        filelist = glob.glob(file_pttn)
        if filelist:
            self.logger.info("Using existing PP files in directory %s", dest_dir)
        else:
            self.logger.info("Retrieving u-windspeed data from MASS...")
            moose.retrieve_files(dest_dir, moose_uri, stashcodes=[self.stash_code],
                time_range=self.time_range, fill_gaps=True)

        # Load u-windspeed data for requested pressure level into an Iris cube.
        try:
            self.logger.info("Loading u-windspeed data into Iris cube...")
            stash_cons = iris.AttributeConstraint(STASH=self.stash_code)
            level_cons = iris.Constraint(pressure=self.plevel)
            ucube = iris.load_cube(dest_dir+'/*.pp', stash_cons & level_cons)
            self.logger.debug("Initial cube: %s", ucube.summary(shorten=True))
            if self.time_range:
                ucube = self._extract_time_slice(ucube)
            # load cube data into memory in case source file is deleted
            data = ucube.data
            time = ucube.coord('time')
            self.logger.info("Number of time steps: %s", len(time.points))
        except:
            self.logger.error("Problem trying to create Iris cube from PP data.")
            raise
        finally:
            # Remove the temp data directory and its contents.
            if not self.keep_source_data:
                shutil.rmtree(dest_dir, ignore_errors=True)

        return ucube

    def _extract_time_slice(self, cube):
        """Extract a user-defined time slice from the passed-in cube."""
        self.logger.info("Extracting data for time period %s to %s...",
            self.time_range[0], self.time_range[1])

        tcoord = cube.coord('time')
        tunits = tcoord.units
        tstart, tend = tcoord.points[0], tcoord.points[-1]
        start_ncdt = pdt_to_nc_datetime(self.start_pdt, calendar=tunits.calendar)
        end_ncdt = pdt_to_nc_datetime(self.end_pdt, calendar=tunits.calendar)
        start = tunits.date2num(start_ncdt)
        end = tunits.date2num(end_ncdt)
        self.logger.debug("Actual start/end T coords: %s, %s", tstart, tend)
        self.logger.debug("Needed start/end T coords: %s, %s", start, end)

        if start > tend or end < tstart:
            msg = "Specified time range falls outside time coordinates\n" \
                  "associated with input data."
            raise DataProcessingError(msg)

        time_cons = iris.Constraint(time=lambda cell: start_ncdt < cell.point < end_ncdt)
        futures = compare_iris_version('2', 'lt') and {'cell_datetime_objects': True} or {}
        with iris.FUTURE.context(**futures):
            newcube = cube.extract(time_cons)

        if newcube:
            self.logger.debug("Time-sliced cube: %s", newcube.summary(shorten=True))

        return newcube

    def _concat_jet_cubes(self, jet_cubes):
        """
        For ensemble input data, append the latest data to a cube with an
        ensemble dimension. This relies on the time dimension being the same
        length for *all* ensemble members.
        """
        self.logger.info("Appending diagnostic data to ensemble-aware cube...")

        # Jet speed is stored in jet_cubes[0]
        jspeed = iris.util.new_axis(jet_cubes[0], scalar_coord='realization')
        if self.jet_speed_cube:
            self.logger.debug("old cube:\n%s", str(self.jet_speed_cube))
            self.logger.debug("new cube:\n%s", str(jspeed))
            cl = iris.cube.CubeList([self.jet_speed_cube, jspeed])
            equalise_attributes(cl)
            try:
                # Iris 1.10+
                self.jet_speed_cube = cl.concatenate_cube(check_aux_coords=False)
            except:
                self.jet_speed_cube = cl.concatenate_cube()
        else:
            self.jet_speed_cube = jspeed

        # Jet latitude is optionally stored in jet_cubes[1]
        if len(jet_cubes) > 1:
            jlat = iris.util.new_axis(jet_cubes[1], scalar_coord='realization')
            if self.jet_lat_cube:
                cl = iris.cube.CubeList([self.jet_lat_cube, jlat])
                equalise_attributes(cl)
                try:
                    # Iris 1.10+
                    self.jet_lat_cube = cl.concatenate_cube(check_aux_coords=False)
                except:
                    self.jet_lat_cube = cl.concatenate_cube()
            else:
                self.jet_lat_cube = jlat

    def _write_jet_data(self):
        """Save jet diagnostic data to a netcdf file."""
        # file layout will differ for ensemble/non-ensemble input data
        self.logger.info("\nWriting jet diagnostics to file %s...", self.outfile)

        jet_cubes = iris.cube.CubeList([self.jet_speed_cube])
        if self.jet_lat_cube: jet_cubes.append(self.jet_lat_cube)

        # Set CF history attribute.
        now = datetime.datetime.utcnow().replace(microsecond=0)
        history = now.isoformat() + 'Z'
        history += ": Jet speed diagnostics produced by Afterburner app " + \
            self.__class__.__name__
        for cube in jet_cubes:
            cube.attributes['history'] = history

        # TODO: append to existing file if requested (--append option?)

        self.logger.debug("Final cube info:\n%s", str(jet_cubes))
        futures = compare_iris_version('2', 'lt') and {'netcdf_no_unlimited': True} or {}
        with iris.FUTURE.context(**futures):
            iris.save(jet_cubes, self.outfile)
