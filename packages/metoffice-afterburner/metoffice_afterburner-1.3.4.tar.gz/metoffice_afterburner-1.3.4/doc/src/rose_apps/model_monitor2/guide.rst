************************
Climate Model Monitor v2
************************

**Sample Rose Suites:** `Index of sample Rose suites`_ (login required)

**Rose App Name:** model_monitor2

**App Class Path:** afterburner.apps.model_monitor2.ModelMonitor2

.. contents::

Overview
========

The Climate Model Monitor v2 application (CMM2 app, for short) allows scientists
to monitor selected diagnostics from one or more climate model runs (or suites),
calculate one or more statistical measures from those diagnostics, and render the
results as a montage of time-series plots within an HTML document. An example of
the output produced by the CMM2 app is shown below.

.. image:: images/cmm_output.png

The original version of the CMM app (which is now deprecated) only supports
calculation of the area-weighted mean of each requested diagnostic, either over
the entire globe (the default) or else over a user-defined geographical region.
The CMM2 app provides the capability to calculate a number of additional statistical
measures, including the simple mean, minimum, maximum, sum, and area-weighted sum.
Moreover, it is also possible to request that a land-area fraction correction be
applied during the calculation of a particular statistic; typically this is
desirable when one is computing area-weighted global totals.

As with the CMM app, the target climate model runs to monitor, and the set of
diagnostics to plot for each model, are configured via a familiar Rose-style app
configuration file (i.e. rose-app.conf). Details of the various configuration
options are described below under the `Configuring the Application`_ section.

.. note:: In the short term, the CMM and CMM2 applications are being maintained as
   distinct code entities. The main reason for this is due to backward compatibility
   issues: the additional statistical measures supported by the CMM2 app mean that
   the naming and layout of netCDF files placed in the ``output/nc`` directory has
   had to be modified. These, and other, changes mean that while the CMM2 app can
   work with a CMM app config file, the opposite is not true. In due course it
   is envisaged that CMM2 will become the application of choice.

Usage Guide
===========

Standard Model Diagnostics
--------------------------

The CMM2 app supports plotting of standard gridded model diagnostics based upon
simple latitude-longitude grids (diagnostics based on rotated latitude-longitude
grids may be used as input, but this functionality is currently experimental
and the results should be treated accordingly). In the case of 4D diagnostics,
i.e. those with T-Z-Y-X axes, a particular horizontal slice must be chosen by
specifying a model or pressure level coordinate; more elaborate vertical coordinates
are not currently supported.

The latest version of the CMM2 app includes the ability to monitor diagnostics
serialized in netCDF format (i.e. in addition to UM atmosphere diagnostics stored
in PP format). In practical terms this means that the CMM2 app may be used to
monitor diagnostics output to netCDF-based data streams by the NEMO and CICE
climate models. Support for additional climate models may be implemented in
future versions of the app.

Source model data is loaded from files held within on-disk data caches. The
current app supports four Afterburner-designed data caching schemes:

1. VarSplit scheme - files are organised on a model/stream/variable basis.
2. EnsembleVarSplit scheme - files are organised on a model/realization/stream/variable basis.
3. StreamSplit scheme - files are organised on a model/stream basis.
4. EnsembleStreamSplit scheme - files are organised on a model/realization/stream basis.

By default the CMM2 app employs the VarSplit data caching scheme as this scheme
minimises the size and number of model data files required to meet the needs
of the app. It is not currently possible to mix-and-match two or more of the
above-mentioned data caching schemes. More information about these schemes can
be found in the :doc:`/dev_guide/datacaches` chapter of the Afterburner documentation.

Each time the CMM2 app is invoked, it queries the the MASS data archive to see
if new model data is available to extend the plotted time-series graphs. This MASS
synchronisation operation can be disabled, if desired, in which case the check
will be limited to looking for new files added to the selected model data cache.
You may wish to adopt this approach if, say, there is some other I/O process that
is automatically updating your on-disk cache of model data.

.. note:: If the CMM2 app is being run on a platform that does not have access
   to the MASS archive (or rather the MOOSE interface to it) then the MASS
   synchronisation option necessarily must be disabled.

To avoid repeatedly having to fetch older model data, the CMM2 app maintains a
separate on-disk cache of computed diagnostic statistics data in netCDF format.
When new model data becomes available it is appended, after averaging or summing,
to the relevant netCDF files. The latter are uniquely identified by model, stream,
variable, region and, if required, vertical level. For example, the file
``ae801_apy_m01s00i024_global.nc`` contains globally-averaged, annual-mean
surface temperature data from UM run ae801.

Custom Model Diagnostics
------------------------

In addition to the standard model diagnostics described above, the CMM2 app is
also able to plot so-called "custom diagnostics". At present only the following
*system-defined* custom diagnostics are supported:

* TOA Radiation Balance ('toa_radiation_balance')
* Net Heat Flux Into Ocean ('net_heat_flux_into_ocean' -- **note: this is an
  experimental diagnostic**)

It is now also possible to generate and plot *user-defined* custom diagnostics
by specifying a formula comprising one or more UM STASH codes, numeric constants,
and basic arithmetic operators. For example, the diagnostic "surface temperature
in degrees Fahrenheit" could be specified in a CMM2 app config file as shown below:

.. code-block:: ini

    [namelist:diags(tas_degf)]
    enabled=true
    formula=(m01s00i024-273) * 1.8 + 32
    var_name=tas_fahrenheit
    standard_name=air_temperature
    long_name=Surface Air Temperature
    units=degF

The ``formula`` and ``var_name`` properties are mandatory; together they signal
to the CMM2 app that a user-defined diagnostic is being defined. The value of the
``var_name`` property must **not** be one of the system-defined custom diagnostics
referred to above.

The ``standard_name``, ``long_name``, and ``units`` properties are optional.
If defined, they are added as metadata attributes to the netCDF file of global
(or regional) mean/sum data generated for the diagnostic. Although they are not
essential to the correct calculation of a custom diagnostic, typically it is
desirable to specify at least the ``units`` property.

At present, only simple algebraic expressions like the one shown in the above
formula property can be specified. The custom diagnostic is generated by Afterburner's
:class:`SimpleDerivedDiagnostic <afterburner.processors.diags.derived.SimpleDerivedDiagnostic>`
class. It is possible, however, to use the ``class_path`` property to specify an
alternative Python class that will be used to parse the supplied formula and generate
the desired diagnostic. This, though, is an advanced capability -- please seek advice
from the Afterburner development team if you wish to exploit this mechanism.

Supported Statistical Measures
------------------------------

The CMM2 app currently supports the following statistical measures, which are
applied either over the full spatial extent of the input field (which usually
means the entire globe), or else over a user-defined region of the globe.

* Simple arithmetic mean
* Area-weighted mean (the default)
* Sum
* Area-weighted sum
* Minimum
* Maximum
* NAO Index

With the exception of the NAO Index statistic, which is custom-generated by the
CMM2 app, all of the other statistics are calculated by Iris (or by Numpy behind
the scenes).

Notes regarding the NAO Index
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ability to calculate the NAO Index from a sea-level pressure model diagnostic
is an **experimental** new feature. In its current implementation, a simple
*non-normalized* index is calculated based upon the default settings as shown
below in the snippet taken from a CMM2 configuration file.

The default stations used are Ponta Delgada in the Azores, and Stykkisholmur in
Iceland. Different stations may be used by defining their latitude and longitude
coordinates (in decimal degrees) via the ``azores_station`` and ``iceland_station``
options.

By default, a nearest-neighbour method is used to select the model data value
closest to each station. As an alternative, a linear interpolation method may be
employed by setting the ``interp_method`` option to 'linear'.

.. code-block:: ini

   [namelist:diags(mslp_nao_index)]
   enabled=true
   stashcode=m01s16i222
   statistic=nao_index
   #azores_station=37.7, -25.7
   #iceland_station=65.0, -22.8
   #interp_method=nearest

Additional details regarding the computation of the NAO Index can be found in the
documentation for the :doc:`nao_index module </apidoc/afterburner.processors.diags.atmos.nao_index>`

Application Outputs
-------------------

The CMM2 app currently produces three kinds of output:

1. NetCDF files containing time-series of computed diagnostic statistics, one
   file for each distinct combination of model, stream, diagnostic, region and,
   if defined, vertical level. These files are stored below the ``nc`` subdirectory
   of the main output directory specified in the app config file (see next section)

2. Images, in PNG format, of time-series plots of computed diagnostic statistics.
   Each plot depicts data for a given diagnostic for all models being monitored.
   These files are stored below the ``images`` subdirectory of the main output
   directory.

3. An HTML file which contains a montage of all the images generated during a
   run of the CMM2 app. This file, named ``cmm.html``, is created in the main
   output directory.

.. note:: The original CMM app stored all netCDF files within the ``output/nc``
   directory. This was practicable because the app did not need to distinguish
   between files used to store different statistical measures. With the CMM2 app,
   netCDF files for each statistical measure are stored in suitably named
   subdirectories; namely ``mean``, ``awmean``, ``sum``, ``awsum``, ``min``,
   ``max``, and ``nao_index``.

Configuring the Application
---------------------------

The CMM2 application is configured by specifying properties in a text file
based upon Rose's custom INI file format. This so-called 'app config file' may
be created and updated manually using your favourite text editor, or else by
using Rose's graphical editor tool (invoked by typing ``rose config-edit`` or,
if you're really pressed for time, ``rose edit``).

You can mix-and-match both of these techniques at different times. One advantage
of editing the configuration file manually is that it doesn't get reformatted
or reordered, which is what happens when you modify and save a config file using
``rose edit``. This can be mildly annoying.

When configuring and running the CMM2 application under Rose control the config
file is invariably named ``rose-app.conf``. If the app is being run manually
at the shell command prompt then the config file may, if desired, be given pretty
much any name you like.

A sample app config file is included as part of the sample Rose suites.
The config file can be found at the path ``app/model_monitor2/rose-app.conf``.
It contains all of the properties currently recognised by the CMM2 app,
listed with their default values where appropriate. Some of the less frequently
used properties are hidden (from a Rose perspective) by placing a '!' character
at the front of the property, or section, definition.

A brief description of each configuration property is provided below on a section
by section basis. If you choose to edit the config file using Rose's config editor
tool then you should see similar, albeit terser, help information within its
graphical interface. The identifier of each config file section is given in
parentheses after the section title. Likewise for the identifier of each config
property within those sections.

.. note:: The CMM2 app config file is a superset of the CMM app config file. As
   such, an instance of the latter should work fine with the CMM2 app. The converse
   is not true, however: a CMM2 app config file will not usually be fully
   comprehensible to the CMM app. Also, and as noted in the previous section, the
   CMM2 app utilises a new directory layout for caching netCDF files on disk.

Command Execution (section: command)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

default
    This property defines the default command that Rose will invoke in order to
    run the CMM2 application code. Other than to append additional command-line options
    (as described below under `Command-Line Options`_), the default command syntax
    should not normally be modified. If you're not using Rose, this property is
    ignored.

Runtime Environment (section: env)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The environment variables described below may be defined in the ``rose-app.conf``
file, the ``rose-suite.conf`` file, or, less commonly, within the ``suite.rc``
file. The optimum location will vary from Rose suite to Rose suite.

AFTERBURNER_HOME_DIR
    This environment variable is used to define the pathname of the directory
    within which the Afterburner software is installed. If this variable is
    already set within your runtime environment - e.g. within one of your shell
    start-up scripts - then it's not essential to repeat it here (though it
    doesn't hurt to do so). If you're not sure where the Afterburner software is
    installed at your site, please contact your local system administrator.

    Alternatively, it is possible to define this variable under the appropriate
    section of either the rose-suite.conf file or the suite.rc file (assuming,
    that is, the CMM2 app is being executed under the control of a Rose suite).

SCITOOLS_MODULE
    By default the wrapper script that invokes the CMM2 app will try to load a
    Python3-based version of the Met Office's Scientific Software Stack (which
    includes packages such as iris, cartopy and matplotlib).

    You can request that a specific SciTools module be loaded by assigning the
    desired module name to this environment variable, e.g.:

    .. code-block:: ini

       [env]
       SCITOOLS_MODULE=scitools/experimental-current

    If you prefer to set up the SciTools module explicitly in the calling
    environment -- e.g. by invoking the ``module load`` command *prior* to running
    the app -- then you should set ``SCITOOLS_MODULE=none``. This will prevent
    the wrapper script from trying to load a default SciTools module.

    .. note:: If you are running the app on a platform that doesn't support SciTools
       as a loadable module, then the wrapper script may emit a warning message to
       this effect. This message can be suppressed (if desired) by setting the
       variable to 'none' as shown in the previous paragraph.

General Options (section: general)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The image below illustrates the General Options panel, as displayed by Rose's
config editor tool (note: the user interface you actually see may differ slightly
from this image).

.. image:: images/general_options.png

Output Directory (option: output_dir)
    Specifies the top-level directory below which various CMM2 outputs are created
    or updated. Refer to the `Application Outputs`_ section above for more details.

    .. note:: If you use an environment variable, such as $LOCALDATA, in the
       definition of the output directory, then your intended runtime environment
       must be able to resolve such variables, otherwise the CMM2 app will either
       fail or else place output files in unexpected locations. The same cautionary
       note applies to the cache directory described next.

Model Data Cache Directory (option: cache_dir)
    Specifies the top-level directory below which model data files will be cached.
    Files are stored in subdirectories, the names and layout of which are determined
    by the selected data caching scheme (see next entry). The data cache directory
    should be visible to the system (such as SPICE) on which the CMM2 app will be
    executed.

    A recommended approach is to create top-level cache directories for each of
    the types of Afterburner data cache you expect to use. For example, on the
    SPICE platform you might create the following directories to store model
    data managed according to the VarSplit and StreamSplit cache schemes:

    .. code-block:: bash

        % mkdir -p $SCRATCH/caches/varsplit
        % mkdir -p $SCRATCH/caches/streamsplit

    where $SCRATCH typically expands to ``/scratch/<userid>``. This way all of your
    cached data resides below a single high-level directory, and can be accessed
    by all processes running on SPICE.

    Note that the top-level data cache directory, plus any required subdirectories,
    will be created on an as-needs basis by the CMM2 app. Your user account will,
    therefore, require the appropriate read-write permissions.

Model Data Cache Type (option: cache_type)
    This option is used to select an Afterburner-supported data caching scheme.
    The default is to use the **VarSplit** scheme, which stores diagnostic data
    in files whose paths are constructed using the convention:

    :file:`/<cache_root_dir>/<suite_id>/<stream_id>/<variable_id>/<datafile>`

    where `<variable_id>` is usually a UM STASH code in the form 'm01s00i024', and
    `<datafile>` is the familiar model-generated filename, e.g. `expida.py1970.pp`

    Use of this cache scheme means that the CMM2 app only needs to retrieve and
    store the minimal amount of model data required to generate the plots of
    selected diagnostics/variables.

    The **StreamSplit** scheme applies the pathname convention:

    :file:`/<cache_root_dir>/<suite_id>/<stream_id>/<datafile>`

    This stream-based data storage scheme is commonly used by other climate model
    software applications. It has the disadvantage of potentially retrieving and
    storing large amounts of model data which is not needed by the CMM2 app. If,
    however, you already have model data files on disk which adhere to this layout
    then choosing the StreamSplit option may make good sense.

    The **EnsembleVarSplit** and **EnsembleStreamSplit** cache schemes are, as
    the names suggest, ensemble-based variants of the above-mentioned schemes.
    In both cases an additional `<realisation_id>` directory is inserted between
    the `<suite_id>` and `<stream_id>` directories.

    Whichever scheme is selected, it is assumed that your user account has write
    permission to the entire directory hierarchy existing below the model data
    cache directory (unless the MASS synchronisation option is disabled, in which
    case no write operations are performed against the data cache).

Model Data Stream (option: stream)
    This option is used to specify the default data stream you wish to use as the
    source of model data. At present the CMM2 app officially only works with data
    from annual-mean (apy, ony, iny) or monthly-mean (apm, onm, inm) streams.
    Some other stream may be specified, but the results are not guaranteed. It's
    possible to override the data stream for individual diagnostics -- refer to
    the *Diagnostics To Plot* section below.

Calendar Type (option: calendar)
    Specifies the calendar type associated with all models and all diagnostics.
    In theory it is not possible to mix data that is associated with different
    calendars. In practice the CMM2 app might complete successfully, though the
    generated outputs might not be directly comparable.

Reinitialisation Period (option: reinit)
    Defines the default reinitialisation period, in days, used by each model suite/run.
    This option usually only needs to be specified when a non climate mean stream
    (e.g. apa-apk) has been selected as the input source. This option may, if required,
    be overridden for individual models -- see the *Source Climate Models* section below.

..  note:: If climate mean data has been output to a non-standard stream, such as apa or
    ap1, then the normal reinitialisation period for the stream needs to be overridden by
    specifying the period as a *negative value*. For example, if annual-mean data has been
    output to, say, the ap1 stream, then the reinitialisation period should be defined as
    ``reinit=-360``.

Sync Model Data Cache With Mass (option: sync_with_mass)
    By default the CMM2 app attempts to retrieve new model data for the selected
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

    Deleting all the files will force the CMM2 app to restore and reload the
    required model data, recompute global/regional means, and save the latter
    afresh to the appropriate netCDF files. If preferred, finer-grained control
    over this process can be achieved by manually deleting individual netCDF
    files...at your own risk!

    .. warning:: If you do enable this option, don't forget to turn it off for
       subsequent runs of the CMM2 app. Otherwise the app will end up repeatedly
       deleting, recomputing, and saving the diagnostic statistics data.

Clear Model Data Cache On Exit (option: clear_model_data)
    By default the CMM2 app will leave any model data files retrieved from MASS
    within the specified data cache directory (see above). This can be beneficial
    if you plan to use the source model data for other purposes. If this option
    is turned on then any data files retrieved during the current invocation of
    the CMM2 app will be deleted at the end of processing. Files residing in the
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
    first plot only; to render it inside an extra (blank) plot at the end of the
    series; or to disable the legend completely.

Legend Style (option: legend_style)
    This option is used to select the text to display within the plot legend
    adjacent to the line symbols used to represent each model run.

Graph Sorting Method (option: sort_graphs_by)
    Specifies the method to utilise for ordering the time-series graphs on
    the generated HTML page. By default the graphs are ordered alphabetically
    based on the concatenated diagnostic name and region name. Alternatively,
    the order of appearance can be controlled by specifying a graph_order
    property against each diagnostic to be plotted -- refer to the `Diagnostics
    To Plot` section below for more information.

Equalise Cube Attributes (option: equalise_attributes)
    If this option is enabled then cube attributes are 'equalised' prior to the
    cube concatenation operation that is performed when new data is loaded from
    the model data cache directory. The process of equalisation discards any
    cube attributes that might impede the concatenation operation. This option
    overrides the Ignoreable Cube Attributes option described below.

Ignoreable Cube Attributes (option: ignoreable_attributes)
    This option may be used to specify a comma-separated list of the names of
    any cube attributes which should be ignored during the cube concatenation
    operation that is performed when new data is loaded from the model data cache
    directory. If this option is not defined then the default setting is the lone
    attribute 'um_version'. Ignoring this attribute is desirable if a diagnostic
    being monitored spans multiple UM versions (rare, but not unknown).

Treatment of Regional Extent Coordinates (option: treat_region_coords_as)
    By default, the latitude and longitude coordinates used to specify the extent
    of a region are treated as defining *left-closed* intervals, i.e. min <= x < max.
    This option may be used to request an alternative treatment of the specified
    latitude and longitude ranges. Permitted values for this option are the text
    strings: open, leftopen, leftclosed, or closed.

Number of Processors (option: num_processors)
    This option is not currently utilised (note, however, that parallelisation
    of data retrievals from MASS may be performed separately using the
    :doc:`/rose_apps/mass_data_robot/guide` application).

Source Climate Models (section: models)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The image below illustrates a model definition panel, as displayed by Rose's
config editor tool (note: the user interface you actually see may differ slightly
from this image).

.. image:: images/model_options.png

The options described below are used to define each of the climate model runs/suites
from which selected diagnostics are to be retrieved, averaged or summed, and plotted.

.. note:: If a new model definition is created by copying an existing entry within Rose's
   config editor, it is recommended that you rename the newly added section to
   something meaningful. This can be achieved by right-clicking on the Rose-generated
   numeric identifier and selecting the 'Rename Section' option. Typically the
   new section is assigned the same name as the model runid or suite-id (which
   must be all lower case).

Enabled (option: enabled)
    Enables/disables processing of a model. Disabling a model is a convenient way of
    turning off the generation of output for a particular model without having to
    remove it completely from the configuration file. It may then be re-enabled
    at a later date, if required.

Suite Name or Run ID (option: name)
    The climate model suite name ('mi-ab123' format) or UMUI runid ('expid' format).
    A couple of edge-cases are handled as follows:

    If the source model is an ensemble member of a simulation, the ensemble member
    identifier should be appended to the suite name (or runid) after a '/' character
    e.g. ``mi-ab123/r01i02p03``.

    If the simulation contains multiple models having different names (from the suite),
    the name of the required model should be appended to the suite name after a '_'
    character e.g. ``mi-ab123_atmos``.

Short Description of Suite/Run (option: label)
    A short-ish human-readable description of the model. This is used to label plots.

Plot Order (option: plot_order)
    Defines the order in which model time-series are drawn in the generated
    plots. Models with lower numbers are drawn before those with higher numbers.

Reinitialisation Period (option: reinit)
    Defines the reinitialisation period, in days, for the current model, thus
    overriding the global setting (see `General Options` above). This option is usually
    only required when a non climate mean stream (e.g. apa-apk) stream has been selected
    as the input source.

..  note:: If climate mean data has been output to a non-standard stream, such as apa or
    ap1, then the normal reinitialisation period for the stream needs to be overridden by
    specifying the period as a *negative value*. For example, if annual-mean data has been
    output to, say, the ap1 stream, then the reinitialisation period should be defined as
    ``reinit=-360``.

Line Style (option: line_style)
    Specifies the line style (e.g. solid, dashed) to use for the current model.
    The default is a solid line.

Line Colour (option: line_colour)
    Specifies the line colour to use for the current model. The value can be any
    colour abbreviation (e.g. 'b' for blue) or colour name (e.g. 'skyblue') recognised
    by Matplotlib (see `Matplotlib colors`_). The default is black.

Line Width (option: line_width)
    Specifies the line width (in points) to use for the current climate model.
    The default width is 1.5.

Marker Type (option: marker_style)
    Specifies the marker type (symbol) to use for the current model.
    The default is 'none', i.e. no marker.

Marker Size (option: marker_size)
    Specifies the marker size (in points) to use for the current climate model.
    The default marker size is 6.

Marker Face Colour (option: marker_face_colour)
    Specifies the marker face colour to use for the current climate model.
    The value can be any colour abbreviation or colour name recognised by Matplotlib
    (see `Matplotlib colors`_). If this option is set to 'auto' (the default) then the
    associated line colour is used as the marker colour. If set to 'none' then the
    marker face is left unfilled.

Marker Edge Colour (option: marker_edge_colour)
    Specifies the marker edge colour to use for the current climate model.
    The value can be any colour abbreviation or colour name recognised by Matplotlib
    (see `Matplotlib colors`_). If this option is set to 'auto' (the default) then the
    marker face colour is also used to render marker edges. If set to 'none' then the
    marker edges are not rendered.

Transparency (Alpha) Level (option: transparency)
    Specifies the transparency (a.k.a. alpha) level to apply to line and marker symbols
    for the current climate model. The default level is 1.0, i.e. fully opaque.

Earliest/Latest Data Retrieval Date (option: start_date/end_date)
    These two options can be used to specify the earliest and/or latest dates
    between which to retrieve diagnostic data for a model. If defined, then the dates
    should normally align with the *climate meaning reference date*, if any, used
    by the parent run/suite. For example, you might specify a date of 1979-12-01
    if the CMR date for a model is 1859-12-01. If undefined (the default) then
    the full time span of available data (either in MASS or on disk) is used.

.. note:: Although they shouldn't normally need to be specified, the start/end
   date options can be useful for application testing or debugging purposes
   since they limit the volume of data retrieved from MASS. Retrieving multiple
   files for centennial and longer model runs can, as you probably know,
   take a LOOOOONG time!)

Time Offset On Plots (option: time_offset)
    This option may be used to specify a time offset, in whole years, to apply
    to the time coordinates for the current model. A positive offset shifts the
    time coordinates of the data forwards in time; a negative offset shifts them
    backwards. Note that the time offset is *only* applied during the generation
    of the time-series plots; the time coordinates recorded in any cached netCDF
    files are not altered. The principal use of this option is to shift the
    plotted data series relative to other models, e.g. to compensate for different
    model run start dates.

Land-area Fraction File (option: laf_file)
    Used to specify the pathname of the file containing land-area fraction data
    associated with the current climate model. The file can be in any format
    recognised by Iris, though typically it will be a UM Fieldsfile or PP file.
    Data is read from this file if a land-area fraction correction is requested
    for any given diagnostic.

Land-area Fraction STASH Code (option: laf_stashcode)
    This is an alternative mechanism for specifying the source of land-area fraction
    data. If defined (and the laf_file option is left blank) then the CMM2 app
    will attempt to retrieve, from the appropriate collection in MASS, a PP file
    containing a field having this STASH code. Upon successful retrieval the
    land-area fraction data is saved in a netCDF file under the ``output/nc/laf``
    output directory.

Land-area Fraction Threshold (option: laf_threshold)
    Used to specify the area fraction threshold *at and above which* a grid cell
    is deemed to represent land as opposed to sea. The default threshold is 0.5.

Postproc Script Version Number (option: postproc_vn)
    This option may be used to specify the version number of the postproc script
    used to post-process model output. If undefined then version 1.0 is assumed.
    Setting this option to 2.0 (or higher) is desirable when monitoring diagnostics
    from NEMO/CICE models configured to use that version of postproc.


Diagnostics To Plot (section: diags)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The image below illustrates a diagnostic definition panel, as displayed by Rose's
config editor tool (note: the user interface you actually see may differ slightly
from this image).

.. image:: images/diag_options.png

.. note:: As with model definitions, if you use rose-edit to create a new diagnostic
   definition by copying an existing entry, then it's worth giving the new
   entry a meaningful name to replace the arbitrary numeric identifier assigned
   by rose-edit. This can be done by right-clicking the entry and selecting the
   'Rename Section' option.

Enabled (option: enabled)
    Enables/disables processing of a diagnostic. Disabling a diagnostic is a convenient
    way of turning off generation of output for a particular diagnostic without
    having to remove it completely from the configuration file. It may then be
    re-enabled at a later date, if required.

STASH code (option: stashcode)
    Specifies the STASH code for UM diagnostics in MSI format, e.g 'm01s05i216'
    for the precipitation flux diagnostic.

Variable Name (option: var_name)
    Specifies the name of either (a) a netCDF-based diagnostic, (b) a CMM2-provided
    custom diagnostic, or (c) a user-defined custom diagnostic. At present the
    only CMM2-provided custom diagnostics are 'toa_radiation_balance' and
    'net_heat_flux_into_ocean'. If some other variable name is specified, and the
    formula option is defined (as described below), then the variable name is
    assumed to represent a user-defined, formula-based custom diagnostic. Otherwise
    the variable name is assumed to refer to a netCDF-based diagnostic as produced,
    for example, by the NEMO or CICE climate models.

CF Standard Name (option: standard_name)
    The CF standard name to use for a netCDF or custom diagnostic.

Long Name (option: long_name)
    The long name to use for a netCDF or custom diagnostic.

Auxiliary Variable Names (option: aux_var_names)
    Used to specify a comma-separated list of the names of any auxiliary variables,
    such as coordinate bounds or cell measures, which are to be retrieved alongside
    the primary diagnostic variable. This option is only relevant to netCDF-based
    diagnostics.

Grid Type (option: grid_type)
    Used to specify the grid type associated with a netCDF-based diagnostic, e.g.
    T, U, V, W, or diaptr.

Custom Diagnostic Formula (option: formula)
    Specifies the formula (a.k.a. expression) that will be used to generate a
    *user-defined* custom diagnostic. The formula should be a combination of one
    or more STASH codes, numeric constants, and arithmetic operators (+,-,*,/).
    Refer to the `Custom Model Diagnostics`_ section for information on configuring
    user-defined custom diagnostics.

Region Extent (option: region_extent)
    By default the CMM2 app calculates the statistical measure for a diagnostic
    over the entire globe. This option can be used to define a particular
    geographical region over which to compute the statistic. If you wish to
    generate the statistic over the globe and also one or more regions, then
    separate diagnostic definitions will need to be specified (copying and
    modifying the global definition is an easy way to achieve this). See also
    the `Treatment of Regional Extent Coordinates` property under the `General
    Options` section.

Region Name (option: region_name)
    Assigns a human-readable name to a region extent. This name is used for
    annotating plots and naming netCDF cache files. If no region extent is
    defined then the name 'Global' is used by default.

Statistical Measure (option: statistic)
    Allows selection of the desired statistical measure to calculate from the
    model diagnostic data. The default is to calculate the area-weighted mean.

Apply Land-area or Sea-area Fraction Correction? (option: apply_laf_corr/apply_saf_corr)
    Indicates whether or not to apply a land-area (or sea-area) fraction correction
    to the source model data *prior* to calculating the desired statistical measure.
    If either option is selected, even if only for a single diagnostic, then either
    the laf_file option or the laf_stashcode option must be specified for *each*
    climate model that is being monitored.

Vertical Level/Coordinate (option: level)
    In the case of 4D (T-Z-Y-X) input fields a vertical level/coordinate must
    be specified. At present the vertical coordinate is assumed to be integer
    valued, e.g. model level number or pressure level. The original CMM app only
    permitted the definition of a single horizontal slice of a 4D diagnostic.
    With the CMM2 app this limitation has been lifted such that multiple
    definitions can refer to different horizontal slices of the same target
    diagnostic, e.g. X on pressure levels 200, 500 and 850 hPa.

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
    honoured when the Graph Sorting Method (see `General Options`) is set to
    By Graph Order Key. The graph_order option must be set to an integer value,
    although it is not necessary for the values to be contiguous across the full
    set of diagnostics (e.g. the sequence 1,2,3,10,11,20,30 is perfectly valid).
    If this property is not set for a particular diagnostic then a value of 0 is
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

The CMM2 application can be run either manually at the shell command line or
automatically under the control of a Rose suite. Both methods are described in
general terms in the :doc:`/invoking` chapter. The guidance in that chapter is
largely applicable to the current context.

Manual Invocation
^^^^^^^^^^^^^^^^^

To run the app manually from the command line, type the following:

.. code-block:: bash

    % export AFTERBURNER_HOME_DIR=<path-to-afterburner-home-dir>
    % $AFTERBURNER_HOME_DIR/bin/abrun.sh ModelMonitor2 -c <config-file> [options]

An app config file, as described in the previous section, must be specified via
the ``-c`` (or ``--config-file``) option. Additional command-line options are
described below; often it is desirable to turn on the ``-v/--verbose`` option in
order to see progress messages.

The initial ``export`` command above is not needed if the AFTERBURNER_HOME_DIR
shell variable is defined in one of your shell start-up scripts. Likewise, if
the directory ``$AFTERBURNER_HOME_DIR/bin`` is included in your command search
path, then the second command can be shortened to plain ``abrun.sh``.

If you have checked out (or exported) a working copy of the `Afterburner code base
<https://code.metoffice.gov.uk/trac/afterburner/browser/turbofan/trunk>`_ then you
can, if preferred, set the AFTERBURNER_HOME_DIR variable to point to the directory
containing that working copy.

Invoking the CMM2 app manually will of course only run it once. Typically, however,
you'll want to run the app at regular intervals in order to monitor on-going climate
simulations. This can be achieved simply by running the aforementioned commands as
part of a cron job scheduled to execute at the time of your choosing (some time
overnight, for example).

Alternatively, periodic execution of the CMM2 app can be controlled by the Rose/cylc
scheduler, as described in the next section.

Invocation from a Rose/Cylc Suite
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Firstly, create a copy of the sample Rose suite (login required).

Next, modify the app config file for the CMM2 application (i.e. the file
``app/model_monitor2/rose-app.conf``), and also the ``suite.rc`` file, to suit
your particular data source locations and processing requirements.

At this point you can either run the suite in stand-alone mode, or you can copy
the ``app`` directory over to an existing Rose suite and run (or restart) it.
In the latter case it will be necessary to modify the suite's dependency graph
(in the ``suite.rc`` file) so that the CMM2 task (named model_monitor2) is invoked
at the desired time points. Please consult the relevant Rose and cylc documentation
for further guidance on how to do this.

Command-Line Options
^^^^^^^^^^^^^^^^^^^^

Command-line options can be viewed by invoking the app with the ``-h`` (or ``--help``)
option, as shown below::

    % abrun.sh -h
    Usage: abrun.sh <app_name> [options] [arguments]

    % abrun.sh ModelMonitor2 -h
    Usage: ModelMonitor2 [-h] [-V] [-D | -q | -v] -c CONFIG_FILE

    Climate Model Monitor v2: generates time-series graphs of climate model diagnostics.

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

* :doc:`Original Climate Model Monitor app (CMM) </rose_apps/model_monitor/guide>`

.. _Index of sample Rose suites: https://code.metoffice.gov.uk/trac/afterburner/wiki/RoseSuiteIndex#ClimateModelMonitorv2

.. _Matplotlib colors: https://matplotlib.org/tutorials/colors/colors.html#sphx-glr-tutorials-colors-colors-py
