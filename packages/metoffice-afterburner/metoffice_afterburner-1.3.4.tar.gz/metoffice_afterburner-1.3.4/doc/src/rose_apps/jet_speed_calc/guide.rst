Jet Speed Calculator
====================

**Status:** Beta-2 Test Version

**Sample Rose Suite:** `u-ag138 <https://code.metoffice.gov.uk/trac/roses-u/browser/a/g/1/3/8/trunk>`_
(login required)

**Rose App Name:** jet_speed_calc

**App Class Path:** afterburner.apps.jet_speed_calc.JetSpeedCalculator

.. contents::

Description
-----------

The Jet Speed Calculator app calculates jet speed (a.k.a. jet strength) and jet
latitude diagnostics from daily-mean wind speed data, either for a single climate
model run or an ensemble of such runs. The computation procedure is based upon
the method described by T. Woollings, C. Czuchnicki & C. Franzke (2014)
[http://dx.doi.org/10.1002/qj.2197].

Jet diagnostics are calculated for a single pressure level (850 hPa by default)
and over a limited geographical region (North Atlantic by default). Both of
these constraints can be modified within the configuration file that is used
to control the application (see :ref:`configuring`).

The calculated diagnostic data is output in netCDF format. By default the jet
speed diagnostic values are encoded as a single netCDF variable, with the
jet latitude values attached as an auxiliary coordinate variable. If desired
the jet latitude values can alternatively be output as a separate netCDF
variable.

In the case where an ensemble of climate runs is being processed the diagnostics
must, by necessity, be output as two netCDF variables. This is because a single
auxiliary latitude variable cannot be used for multiple ensemble members (the
latitude values will vary across members). In addition, both output netCDF variables
will feature an ensemble dimension which, in line with CF metadata conventions,
is named 'realization' by default.

Usage Guide
-----------

Layout of Model Data Files
~~~~~~~~~~~~~~~~~~~~~~~~~~

The application reads daily-mean wind speed data from PP files retrieved (if need
be) from the MASS archive. The layout of the data files on disk differs depending
upon the nature of the climate model configuration.

For single climate runs, PP files are stored under the following directory
hierarchy::

    <data_dir>/    # a temporary directory by default
      <suite_id>/
        <stream_id>/
          *.pp

In the case of an ensemble of climate runs, the hierarchy features an additional
ensemble member directory (mirroring the similar approach as used by MASS)::

    <data_dir>/    # a temporary directory by default
      <suite_id>/
        <ens_member_id>/
          <stream_id>/
            *.pp

The values of ``data_dir``, ``<suite_id``, and ``stream_id`` are as described
in the next section. The value of ``ens_member_id`` will depend upon how the
climate suite has been configured, but will typically follow the pattern 'r1i2p3'.

If the relevant PP files containing wind speed data already reside on disk
according to the appropriate scheme above, and assuming that the ``data_dir``
property is defined correctly, then the app should not need to retrieve data
files from MASS.

.. note:: In the situation whereby PP files are retrieved from MASS, only data
   for the u-wind speed diagnostic is requested (via the 'moo select' command),
   and only for the specified pressure level and optional time range. This
   fact should be borne in mind if the same files are later used as input for
   some other processing activity.

.. _configuring:

Configuring the Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The jet speed application is configured by specifying properties in a text file
based upon Rose's custom INI file format. This so-called 'app config file' may
be created and updated manually using your favourite text editor, or else by
using Rose's graphical editor tool (as invoked by typing ``rose config-edit`` or,
if you're feeling lazy, ``rose edit``).

You can mix-and-match both of these techniques at different times. One advantage
of editing the configuration file manually is that it does not get reformatted
or reordered, which is what happens when you modify and save a config file using
``rose edit``. This can be mildly annoying.

When configuring and running the jet speed application under Rose control the
config file is invariably named ``rose-app.conf``. If the app is being run manually
at the shell command prompt then the file may, if desired, be given pretty much
any name you like.

A sample app config file is included as part of the reference Rose suite named
`u-ag138 <https://code.metoffice.gov.uk/trac/roses-u/browser/a/g/1/3/8/trunk>`_.
This config file can be found at the path ``app/jet_speed_calc/rose-app.conf``.
It contains all of the properties currently recognised by the jet speed app,
listed with their default values where appropriate.

Happily, only two of the properties are mandatory: the ``suite_id`` field under
the [input_data] section; and the ``output_file`` field under the [output_data]
section. If your input data and processing requirements conform to the default
settings then you may only need to set these two properties.

A brief description of each configuration property is provided below on a section
by section basis. If you choose to edit the config file using Rose's config editor
tool then you should see similar, albeit terser, help information within its
graphical interface.

[env] Section
.............

AFTERBURNER_HOME_DIR
    This environment variable is used to define the pathname of the directory
    within which the Afterburner software is installed. If this variable is
    already set within your run-time environment - e.g. within one of your shell
    start-up scripts - then it does not need to be repeated here (though it
    won't hurt to do so). If you're not sure where the Afterburner software is
    installed, please contact your local system administrator.

[command] Section
.................

default
    This property defines the command that Rose will invoke in order to run the
    jet speed calculator app. Other than to append additional command-line options
    (as described below under :ref:`command_opts`), the default value should not
    normally be modified.

[input_data] Section
....................

This section of the configuration file is used to specify various options that
describe the location and structure of the source data.

suite_id
    Specifies the Rose suite id, or old-style 5-letter runid, of the climate
    experiment that will be used as the source of daily-mean wind speed data.

ensemble_members
    Optionally, specifies a *comma-separated* list of ensemble member numbers
    (or number ranges) for use when processing an ensemble of climate experiments.
    For example, the following settings select identical ensemble members::

        ensemble_members = 1,2,3,9,15,16,17
        ensemble_members = 1-3,9,15-17

    If this property is undefined then *all* ensemble members are selected (in
    the case where ``suite_id`` refers to an ensemble of runs).

    If set, the specified numbers are matched against the realization number
    component (the 'r' part) of the ensemble member identifier.

    .. note:: This version of the jet speed application assumes that the
       realization number is unique across the full set of ensemble members.

ensemble_axis_name
    This property is not currently used since the default axis name used by Iris
    follows that prescribed by the CF metadata conventions, i.e. ``realization``.

ensemble_regex
    Specifies the regular expression that is used to extract the realization
    number (the 'r' part) from a MIP-compliant, RIP-style ensemble identifier.
    The default regular expression of ``r(?P<R>\d+)i\d+p\d+`` is suitable for
    extracting the numeric value of 'r' from any ensemble identifier which
    adheres to the ``rLiMpN`` notation, where L, M, and N are decimal numbers,
    optionally left-padded with zeros, e.g. ``r01i02p03``.

    If specified, the regular expression must be enclosed in single quote characters,
    and must contain a token of the form '(?P<R>...)' in order to match the 'r'
    part of the ensemble member identifer.

    The Python library `documentation <https://docs.python.org/2.7/library/re.html>`_
    provides comprehensive guidance on constructing regular expressions. 

stream_id
    Specifies the (typically) 3-letter identifer of the model output stream that
    contains daily-mean wind speed diagnostic data.

stash_code
    Specifies the STASH code, in msi-style format, used to select u-wind speed
    data from source model data files.

plevel
    Specifies the single pressure level, in hPa, for which input data will be
    extracted and jet diagnostics calculated.

time_range
    By default, jet diagnostics are calculated for the full time range represented
    within the input data stream. This property may be used to define start and
    end dates (and, if required, times) over which to perform calculations. Any
    date-times should be specified in ISO-like 'YYYY-MM-DDThh:mm:ss' format. If
    any time components are omitted, they default to 00.

    The specified time range should allow for the fact that the low-pass filter
    applied to the generated jet diagnostics (see [jet_speed] section below) will
    truncate the time series by the length, in days, of the filter window (i.e.
    one half from each end of the time series).

data_dir
    Optionally defines the pathname of a directory below which to store model
    data files retrieved from MASS. If undefined (the default) then a temporary
    directory is created for this purpose. Typical use of this property is, in
    combination with the ``keep_source_data`` option (see below), to restore input
    data files to a known directory for later re-use.

    .. note::
       If this property specifies an *existing* directory, and that directory
       contains PP files, then it is assumed that those files contain the desired
       u-wind diagnostic data, and no attempt is made to retrieve files from MASS.

keep_source_data
    By default, any model data files restored to the directory specified by the
    ``data_dir`` property (or auto-generated by the application in the case of a
    temporary directory) are deleted at the end of processing.

    If enabled, this property instructs the app to leave any data files on disk.
    This can be handy if you are doing a number of trial runs and you don't want
    to restore the same data files repeatedly from the MASS archive.

[output_data] Section
.....................

This section of the configuration file is used to specify output options.

output_file
    Specifies the full pathname of the file in which to save calculated jet
    diagnostics. Data is written out in netCDF format, hence the filename should
    normally end with a '.nc' extension.

overwrite
    Set this property to true if you're content to overwrite an existing output
    file. If the output file exists and this property is not enabled then the
    application quits with a warning message. This is to prevent inadvertent
    overwriting of a previously created file.

[jet_speed] Section
...................

This section of the configuration file is used to configure the jet speed
processor.

lp_cutoff
    Specifies the low-pass filter cutoff value, in units of 1/timesteps, i.e.
    1/days. The default value is 0.1

lp_window
    Specifies the low-pass filter window length, in timesteps. The default is 61
    days.

sector
    Defines the geographical region (sector) over which u-wind data will be
    extracted from the source data files. Coordinates should be specified in
    decimal degrees in the order min-long, max-long, min-lat, max-lat. The
    default region is -60.0, 0.0, 15.0, 75.0 (North Atlantic region).

twocubes
    By default, jet speed values are stored as a single Iris cube which gets
    written out to the netCDF output file as a single variable, and with the
    corresponding jet latitude values saved as an auxiliary coordinate variable
    (which shares the time dimension). If this option is set to true then the
    jet speed and jet latitude values are stored as separate Iris cubes and
    output as two discrete netCDF variables.

    .. note:: This option should be set to true if an ensemble of climate runs is
       being processed. If this option is undefined, or set to false, then it is
       coerced to be true and a warning message displayed to give notice that
       the option value has been reset.  

Running the Application
~~~~~~~~~~~~~~~~~~~~~~~

The Jet Speed Calculator app can be run manually at the shell command line or
automatically under the control of a Rose suite. Both methods are described in
general terms in the :doc:`/invoking` chapter. The guidance in that chapter is
applicable to the current context.

Manual Invocation
.................

To run the app manually from the command line, type the following::

    % export AFTERBURNER_HOME_DIR=<path-to-afterburner-home-dir>
    % $AFTERBURNER_HOME_DIR/bin/abrun.sh afterburner.apps.jet_speed_calc.JetSpeedCalculator -c <config-file> [options]

An app config file, as described in the previous section, must be specified via
the ``-c`` (or ``--config-file``) option. Additional command-line options are
described below.

The first command above is not needed if the AFTERBURNER_HOME_DIR shell variable
is defined in one of your shell start-up scripts. Likewise, if the directory
$AFTERBURNER_HOME_DIR/bin is included in your command search path, then the
second command can be shortened to plain ``abrun.sh``.

Invocation from a Rose Suite
............................

Firstly, create a copy of the `u-ag138 <https://code.metoffice.gov.uk/trac/roses-u/browser/a/g/1/3/8/trunk>`_
sample Rose suite (login required).

Next, modify the app config file for the jet speed app (i.e. the file
``app/jet_speed_calc/rose-app.conf``) to suit your particular input data source
locations and processing requirements.

At this point you can either run the suite in stand-alone mode, or you can copy
the app directory over to an existing Rose suite. In the latter case it will be
necessary to modify the suite's dependency graph (in the ``suite.rc`` file) so
that the jet speed app is invoked at the desired time points. Please consult the
relevant Rose and cylc documentation for further details on how to do this.

.. _command_opts:

Command-Line Options
....................

Command-line options can be viewed by invoking the app with the ``-h`` (or ``--help``)
option::

    % abrun.sh afterburner.apps.jet_speed_calc.JetSpeedCalculator -h
    -h, --help            show this help message and exit
    -c CONFIG_FILE, --config-file CONFIG_FILE
                          Pathname of app configuration file
    --overwrite           Force overwrite of output file if it exists
    -v, --verbose         Enable verbose mode

The purpose of each option is as follows:

config-file
    Specifies the path to the Rose-style application configuration file (often,
    though not necessarily, called ``rose-app.conf``).

overwrite
    If set to true, forces overwriting of the netCDF output file, if it exists.
    This option overrides the setting of the like-named property in the app
    config file.

verbose
    If set to true, results in additional progress messages being emitted to
    standard output (in the case of interactive invocation) or to standard log
    files (in the case of invocation by Rose).

See Also
--------

N/A
