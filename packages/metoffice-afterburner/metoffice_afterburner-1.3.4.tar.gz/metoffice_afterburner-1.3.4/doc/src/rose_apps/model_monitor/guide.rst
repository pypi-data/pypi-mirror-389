*********************
Climate Model Monitor
*********************

**Status:** Beta-5 test version

**Sample Rose Suite:** `u-ap367`_
(login required)

**Rose App Name:** model_monitor

**App Class Path:** afterburner.apps.model_monitor.ModelMonitor

.. contents::

.. warning:: This app is now deprecated and no longer supported. Please migrate
   over to using the Climate Model Monitor v2 (CMM2) app, for which documentation
   can be found :doc:`here </rose_apps/model_monitor2/guide>`.

Description
===========

The Climate Model Monitor (CMM) app allows scientists to monitor chosen diagnostics
from one or more climate model runs (or suites), and plot the results as a series
of graphs of the *area-weighted* global (or regional) mean of each diagnostic
against time. An example plot is shown below.

.. image:: images/sample_plot.png

The number of climate models to monitor, and the number of diagnostics to plot
for each model, are user-configurable. Typically, however, the number of models
is of the order of 4-6 since any more than that number will likely result in
overly cluttered line graphs.

The current version of the app only supports monitoring of UM atmosphere
diagnostics taken from either the annual-mean (apy) or monthly-mean (apm) streams.
Support for NEMO ocean model diagnostics (and potentially those from other
models) is planned for a future release.

Source model data is loaded from files held within on-disk data caches. The
current app supports four Afterburner-designed data caching schemes:

1. Organising files on a per-variable, i.e. UM diagnostic, basis (VarSplit scheme)
2. Organising files on a per-ensemble, per-variable basis (EnsembleVarSplit scheme)
3. Organising files on a per-stream basis (StreamSplit scheme).
4. Organising files on a per-ensemble, per-stream basis (EnsembleStreamSplit scheme).

By default the CMM app employs the VarSplit caching scheme as this scheme
minimises the size and number of model data files required to meet the needs
of the app. It is not currently possible to mix-and-match two or more of the
above data caching schemes.

Each time the CMM app is invoked, it checks to see if new model data is available
to extend the plotted time-series graphs. By default, the MASS data archive is
checked for new data files. The MASS option can be turned off, however, in which
case the check will be limited to new files added to the selected model data
cache. You may wish to adopt this approach if you have some other process that
is automatically updating your on-disk cache of model data.

To avoid repeatedly having to fetch older model data, the CMM app maintains a
separate on-disk cache of spatially-averaged diagnostic data in netCDF format.
When new model data becomes available it is appended, after spatial-averaging,
to the relevant netCDF files. The latter are uniquely identified by model, stream,
variable, region and, in certain cases, vertical level. For example, the file
``ae801_apy_m01s00i024_global.nc`` contains globally-averaged, annual-mean
temperature data from UM run ae801.

Usage Guide
===========

Diagnostic Input
----------------

The current version of the CMM app supports plotting of standard gridded UM
diagnostics based on simple latitude-longitude grids (diagnostics on rotated
grids have yet to be tested). In the case of 4D diagnostics (those with T-Z-Y-X
axes) a particular vertical field must be chosen by specifying a model or pressure
level coordinate; more elaborate vertical coordinates are not currently supported.

In due course it is hoped to extend the CMM app to support diagnostics produced
by the NEMO and CICE earth system models.

Custom Diagnostics
------------------

In addition to the standard UM diagnostics described above, the CMM app is also
able to plot so-called "custom diagnostics". At present only the following
*system-defined* custom diagnostics are supported:

* TOA Radiation Balance ('toa_radiation_balance')
* Net Heat Flux Into Ocean ('net_heat_flux_into_ocean' -- **note: this is an
  experimental diagnostic**)

It is now also possible to generate and plot *user-defined* custom diagnostics
by specifying a formula comprising one or more UM STASH codes, numeric constants,
and basic arithmetic operators. For example, the diagnostic "surface temperature
in degrees Fahrenheit" could be specified in a CMM app config file as shown below:

.. code-block:: ini

    [namelist:diags(tas_degf)]
    enabled=true
    formula=(m01s00i024-273) * 1.8 + 32
    var_name=tas_fahrenheit
    standard_name=air_temperature
    long_name=Surface Air Temperature
    units=degF

The ``formula`` and ``var_name`` properties are mandatory; together they signal
to the CMM app that a user-defined diagnostic is being defined. The value of the
``var_name`` property must **not** be one of the system-defined custom diagnostics
referred to above.

The ``standard_name``, ``long_name``, and ``units`` properties are optional.
If defined, they are added as metadata attributes to the netCDF file of global
(or regional) mean data generated for the diagnostic. Although they are not
essential to the correct calculation of a custom diagnostic, typically it is
desirable to specify at least the ``units`` property.

At present, only simple algebraic expressions like the one shown in the above
formula property can be specified. The custom diagnostic is generated by Afterburner's
:class:`SimpleDerivedDiagnostic <afterburner.processors.diags.derived.SimpleDerivedDiagnostic>`
class. It is possible, however, to use the ``class_path`` property to specify an
alternative Python class that will be used to parse the supplied formula and generate
the desired diagnostic. This, though, is an advanced capability -- please seek advice
from the Afterburner development team if you wish to exploit this mechanism.

Application Outputs
-------------------

The CMM app produces three kinds of outputs:

1. NetCDF files containing area-weighted, spatially-averaged diagnostic data, one
   file for each distinct combination of model, stream, diagnostic, and region.
2. Images in PNG format of time-series plots of spatially-averaged diagnostics.
   Each plot contains data for a selected diagnostic for all configured models.
3. An HTML file which contains a montage of all the images generated during a
   run of the CMM app. This file is called ``cmm.html``.

NetCDF files are stored in the ``nc`` subdirectory of the main output directory
defined in the app config file (see next section). Similarly, image files are
stored in the ``images`` subdirectory.

Configuring the Application
---------------------------

The CMM application is configured by specifying properties in a text file
based upon Rose's custom INI file format. This so-called 'app config file' may
be created and updated manually using your favourite text editor, or else by
using Rose's graphical editor tool (as invoked by typing ``rose config-edit`` or,
if you're really pressed for time, ``rose edit``).

You can mix-and-match both of these techniques at different times. One advantage
of editing the configuration file manually is that it doesn't get reformatted
or reordered, which is what happens when you modify and save a config file using
``rose edit``. This can be mildly annoying.

When configuring and running the CMM application under Rose control the config
file is invariably named ``rose-app.conf``. If the app is being run manually
at the shell command prompt then the config file may, if desired, be given pretty
much any name you like.

A sample app config file is included as part of the reference Rose suite named `u-ap367`_.
This config file can be found at the path ``app/model_monitor/rose-app.conf``.
It contains all of the properties currently recognised by the CMM app,
listed with their default values where appropriate.

A brief description of each configuration property is provided below on a section
by section basis. If you choose to edit the config file using Rose's config editor
tool then you should see similar, albeit terser, help information within its
graphical interface. The identifier of each config file section is given in
parentheses after the section title. Likewise for the identifier of each config
option within those sections.

.. note:: The format of the Rose app config file used by the CMM app is broadly
   similar to the one used by the earlier prototype version of the application.
   Although there isn't a specific conversion tool available for upgrading an
   old config file, it should be fairly straightforward to perform a manual
   upgrade using your favourite text editor. The easiest option, however, is to
   use rose-edit to create a new config file from the sample Rose suite mentioned
   above.

Command Execution (section: command)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

default
    This property defines the default command that Rose will invoke in order to
    run the model monitor app. Other than to append additional command-line options
    (as described below under :ref:`cmm_command_opts`), the default command syntax
    should not normally be modified.

Runtime Environment (section: env)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

AFTERBURNER_HOME_DIR
    This environment variable is used to define the pathname of the directory
    within which the Afterburner software is installed. If this variable is
    already set within your run-time environment - e.g. within one of your shell
    start-up scripts - then it does not need to be repeated here (though it
    doesn't hurt to do so). If you're not sure where the Afterburner software is
    installed, please contact your local system administrator.

General Options (section: general)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The image below illustrates the General Options panel, as displayed by Rose's
config editor tool (note: the image may differ slightly from the user interface
displayed by the Rose config editor).

.. image:: images/general_options.png

Output Directory (option: output_dir)
    Specifies the directory within which various CMM outputs are created or
    updated. Spatial-mean diagnostic data is written to netCDF files below a
    subdirectory called ``nc``. Images files are saved in a subdirectory called
    ``images``. The main HTML document generated by the app is saved in the file
    ``cmm.html``.

    .. note:: If you use an environment variable, such as $LOCALDATA, in the
       definition of the output directory, then your intended runtime environment
       must be able to resolve such variables. Otherwise the CMM app will fail.
       The same cautionary note applies to the cache directory described next.

Model Data Cache Directory (option: cache_dir)
    Specifies the directory under which model data files are cached. Files are
    stored in subdirectories, the names and layout of which are determined by
    the selected data caching scheme (see next entry). The data cache directory
    should be visible to the system (such as SPICE) on which the CMM app will be
    executed.

    A recommended approach is to create top-level cache directories for each of
    the types of Afterburner data cache you expect to use. For example, on the
    SPICE platform you might create the following directories to store model
    data managed according to the VarSplit and StreamSplit cache schemes::

        % mkdir -p $SCRATCH/caches/varsplit
        % mkdir -p $SCRATCH/caches/streamsplit

    where $SCRATCH typically expands to ``/scratch/user``. This way all of your
    cached data resides below a single top-level directory, and can be accessed
    by all processes running on SPICE.

    Note that the top-level data cache directory, plus any required sub-directories,
    will be created on an as-needs basis by the CMM app. Your user account will,
    therefore, require the appropriate read-write permissions.

Model Data Cache Type (option: cache_type)
    This option is used to select an Afterburner-supported data caching scheme.
    The default is to use the **VarSplit** scheme, which stores diagnostic data
    in files whose paths are constructed using the convention:

    `/<cache_root_dir>/<suite_id>/<stream_id>/<variable_id>/<datafile>`

    where `<variable_id>` is usually a UM STASH code in the form 'm01s00i024', and
    `<datafile>` is the familiar model-generated filename, e.g. `expida.py1970.pp`

    Use of this cache scheme means that the CMM app only needs to retrieve and
    store the minimal amount of model data required to generate the plots of
    selected diagnostics/variables.

    The **StreamSplit** scheme applies the pathname convention:

    `/<cache_root_dir>/<suite_id>/<stream_id>/<datafile>`

    This stream-based data storage scheme is commonly used by other climate model
    software applications. It has the disadvantage of potentially retrieving and
    storing large amounts of model data which is not needed by the CMM app. If,
    however, you already have model data files on disk which adhere to this layout
    then choosing the StreamSplit option may make good sense.

    The **EnsembleVarSplit** and **EnsembleStreamSplit** cache schemes are, as
    the names suggest, ensemble-based variants of the above-mentioned schemes.
    In both cases an additional `<realisation_id>` directory is inserted between
    the `<suite_id>` and `<stream_id>` directories.

    Whichever scheme is selected, it is assumed that your user account has write
    permission to the entire directory hierarchy existing below the model data
    cache directory (unless the MASS synchronisation option is disabled - see below).

Model Data Stream (option: stream)
    This option is used to select the data stream you wish to use as the source
    of model data. At present the CMM app officially only works with UM data
    from the annual-mean (apy) or monthly-mean (apm) streams. It is possible,
    however, to define an alternative stream (e.g. apa) by manually editing the
    app config file. Please note that this is currently an unsupported,
    experimental feature.

Reinitialisation Period (option: reinit)
    Defines the default reinitialisation period, in days, to apply to all models.
    This option usually only needs to be specified when a UM daily-mean stream
    has been selected as the input source. It may, if required, be overridden
    for individual models -- see the *Source Climate Models* section below.

Sync Model Data Cache With Mass (option: sync_with_mass)
    By default the CMM app attempts to retrieve new model data for the selected
    data stream (see previous entry) from the MASS data archive. If MASS is **not**
    available in your runtime environment, or you are updating the model data
    cache by some other means, then this option should be disabled.

Read-only Access to Model Data Cache (option: cache_readonly)
    If enabled then the model data cache is accessed in read-only mode. This
    option is useful if you are accessing a data cache that is owned by another
    user and therefore not accessible for write operations, e.g. by adding new
    data files. The sync_with_mass option (see previous entry) is automatically
    turned off if this option is enabled.

Clear NetCDF Cache On Start-Up (option: clear_netcdf_cache)
    If this option is enabled, then **ALL** netCDF files residing in the ``nc``
    output directory (see above) will be deleted when the app starts up. Usually
    this only needs to be done if there has been an application error which has
    resulted in the data in the netCDF files becoming out of sync with the
    corresponding model data.

    Deleting all the files will force the CMM app to restore and reload the
    required model data, recompute global/regional means, and save the latter
    afresh to the appropriate netCDF files. If preferred, finer-grained control
    over this process can be achieved by manually deleting individual netCDF
    files...at your own risk!

    .. warning:: If you do enable this option, don't forget to turn it off for
       subsequent runs of the CMM app. Otherwise the app will end up repeatedly
       deleting, recomputing, and saving the spatially-averaged diagnostic data.

Clear Model Data Cache On Exit (option: clear_model_data)
    By default the CMM app will leave any model data files retrieved from MASS
    within the specified data cache directory (see above). This can be beneficial
    if you plan to use the source model data for other purposes. If this option
    is turned on then any data files retrieved during the current invocation of
    the CMM app will be deleted at the end of processing. Files residing in the
    data cache before the app was started will not be affected.

Include STASH Code In Plot Title (option: include_stash)
    If enabled then, for UM diagnostics, the STASH code is included in the plot
    title.

Include Timestamp In Plot (option: include_date)
    If enabled then the generated plots are annotated with their date and time
    of creation.

Include Region Coordinates In Plot (option: include_region)
    If enabled then, for region-delimited diagnostics, the generated plots are
    annotated with the latitude and longitude coordinates of the region.

Legend Visibility (option: legend_vis)
    This option controls the visibility and location of the plot legend, i.e.
    the key to the various climate models on each plot. The default is to draw
    the legend on all plots. Other options allow you to limit the legend to the
    first plot only; to render it within an extra plot at the end of the series;
    or to disable the legend completely.

Legend Style (option: legend_style)
    This option is used to select the text to display within the plot legend
    adjacent to the line symbols used to represent each model.

Graph Sorting Method (option: sort_graphs_by)
    Specifies the method to utilise for ordering the time-series graphs on
    the generated HTML page. By default the graphs are ordered alphabetically
    based on the concatenated diagnostic name and region name. Alternatively,
    the order of appearance can be controlled by specifying a ``graph_order``
    property against each diagnostic to be plotted -- refer to the Diagnostics
    To Plot section below for more information.

Calendar Type (option: calendar)
    Specifies the calendar type associated with all models and all diagnostics.
    In theory it is not possible to mix data that is associated with different
    calendars. In practice the CMM app might complete successfully, though the
    generated outputs might not be meaningfully comparable.

Number of Processors (option: num_processors)
    This option is not currently utilised (a new parallelisation solution based
    upon the cylc task scheduler is currently being investigated).

Source Climate Models (section: models)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The image below illustrates a model definition panel, as displayed by Rose's
config editor tool (note: the image may differ slightly from the user interface
displayed by the Rose config editor).

.. image:: images/model_options.png

The options described below are used to define each of the climate model runs/suites
from which selected diagnostics are to be retrieved, spatially-averaged, and plotted.

.. note:: If a new model definition is created by copying an existing entry within Rose's
   config editor, it is recommended that you rename the newly added section to
   something meaningful. This can be achieved by right-clicking on the Rose-generated
   numeric identifier and selecting the 'Rename Section' option. Typically the
   new section is assigned the same name as the model runid or suite-id (which
   must be all lower case).

Enabled (option: enabled)
    Turns on processing of a model. Disabling a model is a convenient way of
    turning off the generation of output for a particular model without having to
    remove it completely from the configuration file. It may then be re-enabled
    at a later date, if required.

Model Name (option: name)
    The model name. This is in fact a slight misnomer as it refers either to a
    UMUI-style climate model *runid* ('expid' format), or a Rose-style *suite-id*
    ('mi-xxnnn' format).

Model Description (option: label)
    A longer human-readable description of the model. This is used to label plots.

Plot Order (option: plot_order)
    Defines the order in which models are drawn in the generated time-series
    plots. Models with lower numbers are drawn before those with higher numbers.

Reinitialisation Period (option: reinit)
    Defines the reinitialisation period, in days, for a specific model, thus
    overriding the default (see *General Options* above). This option is usually
    only required when a UM daily-mean stream has been selected as the input
    source.

Line Colour (option: line_colour)
    Specifies the line colour to use for a model. The default is black.

Line Style (option: line_style)
    Specifies the line style (e.g. solid, dashed) to use for a model. The default
    is a solid line.

Marker Style (option: marker_style)
    Specifies the marker style (e.g. cross, circle) to use for a model. The
    default is no marker.

Earliest/Latest Data Retrieval Date (option: start_date/end_date)
    These two options can be used to specify the earliest and/or latest dates
    between which to retrieve diagnostic data for a model. If defined, then the dates
    should normally align with the *climate meaning reference date*, if any, used
    by the parent run/suite. For example, you might specify a date of 1979-12-01
    if the CMR date for a model is 1859-12-01. If undefined (the default) then
    the full time span of available data (in MASS or on disk) is used.

.. note:: Although they shouldn't normally need to be specified, the start/end
   date options can be useful for application testing or debugging purposes
   since they limit the volume of data retrieved from MASS. Retrieving multiple
   files for centennial and longer model runs can, as you probably know,
   take a LONGGGG time!)

Time Offset On Plots (option: time_offset)
    This option may be used to specify a time offset, in whole years, to apply
    to the time coordinates for the current model. A positive offset shifts the
    time coordinates of the data forwards in time; a negative offset shifts them
    backwards. Note that the time offset is *only* applied during the generation
    of the time-series plots; the time coordinates recorded in any cached netCDF
    files are not altered. The principal use of this option is to shift the
    plotted data series relative to other models, e.g. to compensate for different
    model start dates.

Diagnostics To Plot (section: diags)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The image below illustrates a diagnostic definition panel, as displayed by Rose's
config editor tool (note: the image may differ slightly from the user interface
displayed by the Rose config editor).

.. image:: images/diag_options.png

.. note:: As with model definitions, if you use rose-edit to create a new diagnostic
   definition by copying an existing entry, then it's worth giving the new
   entry a meaningful name to replace the arbitrary numeric identifier assigned
   by rose-edit. This can be done by right-clicking the entry and selecting the
   'Rename Section' option.

Enabled (option: enabled)
    Turns on processing of a diagnostic. Disabling a diagnostic is a convenient
    way of turning off generation of output for a particular diagnostic without
    having to remove it completely from the configuration file. It may then be
    re-enabled at a later date, if required.

STASH code (option: stashcode)
    Specifies the STASH code for UM diagnostics in MSI format, e.g 'm01s05i216'
    for the precipitation flux diagnostic.

Custom Diagnostic Name (option: var_name)
    Specifies the name of a CMM-supported custom diagnostic. At present the only
    such diagnostics are 'toa_radiation_balance' and 'net_heat_flux_into_ocean'.
    If some other variable name is specified then it is assumed to refer to a
    user-defined, formula-based custom diagnostic, in which case the formula
    option must be defined, as described in the next entry.

Custom Diagnostic Formula (option: formula)
    Specifies the formula (a.k.a. expression) that will be used to generate a
    *user-defined* custom diagnostic. The formula should be a combination of one
    or more STASH codes, numeric constants, and arithmetic operators. Refer to
    the `Custom Diagnostics`_ section for information on configuring user-defined
    custom diagnostics.

Region Extent (option: region_extent)
    By default the CMM app calculates the area-weighted global average of a diagnostic at each
    time point. If required, a regional average can be requested by defining the
    geographical region of interest. If you wish to output both a global average
    and a regional average then separate diagnostic definitions will need to be
    specified (copying the global definition is an easy way to do this).

Region Name (option: region_name)
    Assigns a human-readable name to a region extent. This name is used for
    annotating plots and naming netCDF cache files. If no region extent is
    defined then the name 'Global' is used by default.

Vertical Level/Coordinate (option: level)
    In the case of 4D (T-Z-Y-X) input fields a vertical level/coordinate must
    be specified. At present the vertical coordinate is assumed to be integer
    valued, e.g. model level number or pressure level. It should be noted that
    it is not currently possible to define multiple diagnostic definitions based
    on different vertical slices of the same input field (this constraint is a
    result of the current mechanism used to cache spatially-averaged data on
    disk).

Earliest/Latest Year To Plot (options: xmin/xmax)
    By default the full time period available for a given diagnostic gets used
    when generating time-series plots. These two options can be used to constrain
    the earliest and/or latest dates for plotting purposes.

Minimum/Maximum Y Value (options: ymin/ymax)
    By default the range of the time-series plot Y axes will be set to match the
    range of the data being plotted. These two options can be used to define
    specific minimum and/or maximum Y-axis values. This can be useful when you
    want to have consistent axis ranges across multiple comparable diagnostics.

Graph Order (option: graph_order)
    This option may be used to define the order of appearance of a diagnostic's
    time-series graph on the output HTML page. Note, however, that it is only
    honoured when the Graph Sorting Method (see General Options) is set to
    By Graph Order Key. The graph order option must be set to an integer value,
    although it is not necessary for the values to be contiguous across the full
    set of diagnostics (e.g. the sequence 1,2,3,10,11,20,30 is perfectly valid).
    If the property is not set for a particular diagnostic then a value of 0 is
    assumed, in which case that diagnostic's graph will appear at the top of the
    HTML page.

UM/PP Time-meaning Flags (options: lbtim/lbproc)
    Originally, the CMM app only supported plotting of time-mean diagnostics
    with a LBTIM value of 122 and a LBPROC value of 128. While those are still
    the assumed default values it is possible to specify alternative values for
    these header fields, if necessary. Since this is likely to be a fairly rare
    scenario, however, these two options must be specified by manually editing
    the app config file as they are not currently defined in the sample Rose
    suite cited at the top of this page.

Running the Application
-----------------------

The CMM application can be run either manually at the shell command line or
automatically under the control of a Rose suite. Both methods are described in
general terms in the :doc:`/invoking` chapter. The guidance in that chapter is
applicable to the current context.

Manual Invocation
^^^^^^^^^^^^^^^^^

To run the app manually from the command line, type the following::

    % export AFTERBURNER_HOME_DIR=<path-to-afterburner-home-dir>
    % $AFTERBURNER_HOME_DIR/bin/abrun.sh ModelMonitor -c <config-file> [options]

An app config file, as described in the previous section, must be specified via
the ``-c`` (or ``--config-file``) option. Additional command-line options are
described below; often it is desirable to turn on the ``-v/--verbose`` option.

The ``export`` command above is not needed if the AFTERBURNER_HOME_DIR shell variable
is defined in one of your shell start-up scripts. Likewise, if the directory
$AFTERBURNER_HOME_DIR/bin is included in your command search path, then the
second command can be shortened to plain ``abrun.sh``.

If you have checked out (or exported) a working copy of the `Afterburner code base
<https://code.metoffice.gov.uk/trac/afterburner/browser/turbofan/trunk>`_ then you
can, if preferred, set the AFTERBURNER_HOME_DIR to point to the directory
containing that working copy.

Invoking the CMM app manually will of course only run it once. Typically, however,
you'll want to run it at regular intervals in order to monitor running climate
models. This can be achieved by running the aforementioned commands as a cron
job scheduled to execute at the time of your choosing (overnight, for example).

Alternatively, periodic execution of the CMM app can be controlled by the Rose/cylc
scheduler, as described in the next section.

Invocation from a Rose Suite
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Firstly, create a copy of the `u-ap367`_ sample Rose suite (login required).

Next, modify the app config file for the CMM application (i.e. the file
``app/model_monitor/rose-app.conf``), and also the ``suite.rc`` file, to suit
your particular data source locations and processing requirements.

At this point you can either run the suite in stand-alone mode, or you can copy
the app directory over to an existing Rose suite and run (or restart) that. In
the latter case it will be necessary to modify the suite's dependency graph (in
the ``suite.rc`` file) so that the CMM app is invoked at the desired time points.
Please consult the relevant Rose and cylc documentation for further guidance on
how to do this.

.. _cmm_command_opts:

Command-Line Options
^^^^^^^^^^^^^^^^^^^^

Command-line options can be viewed by invoking the app with the ``-h`` (or ``--help``)
option, as shown below::

    % abrun.sh -h
    Usage: abrun.sh <app_name> [options] [arguments]

    % abrun.sh ModelMonitor -h

    Climate Model Monitor: generates time-series graphs of climate model diagnostics.

    optional arguments:
      -h, --help            show this help message and exit
      -V, --version         Show Afterburner version number and exit
      -D, --debug           Enable debug message mode
      -q, --quiet           Enable quiet message mode
      -v, --verbose         Enable verbose message mode
      -c CONFIG_FILE, --config-file CONFIG_FILE
                            Pathname of app configuration file

These options are fairly self-explanatory. Note, however, that the -D, -q and -v
options are mutually exclusive.

Acknowledgments
===============

Thanks to Dan Copsey for developing the original IDL-based version of the CMM
application, and to Jon Seddon for converting this to the initial Afterburner
prototype version.

See Also
========

N/A

.. _u-ap367: https://code.metoffice.gov.uk/trac/roses-u/browser/a/p/3/6/7/trunk
