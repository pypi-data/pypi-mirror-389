Change Log
==========

Version 1.3.4
-------------

**Release Date:** 28 October 2025

**Summary**

This represents the v1.3.4 release of the Afterburner software suite.

* Fixed the issue with Gregorian calendar data using Iris versions 3.3 and later.
* Updated afterburner tests to use pytest.
* This release provides compatibility with Numpy v2.

Version 1.3.3
-------------

**Release Date:** 16 January 2023

**Summary**

This represents the v1.3.3 release of the Afterburner software suite. This
release incorporates a handful of minor enhancements and bug fixes identified
since the v1.3.2b2 release.

* The issue that caused the exception
  ``module 'iris' has no attribute 'fileformats'`` to be raised when using the
  MASS Data Robot has now been resolved.
* This release provides compatibility with Python v3.10, Iris v3.4 and cftime
  v1.5.2.

Version 1.3.2b2
---------------

**Release Date:** 17 August, 2021

**Summary**

* Updated the ``setup.py`` file and added new metadata description files (``MANIFEST.in``,
  ``README.md``, ``pyproject.toml``) so as to enable the ``afterburner`` package to be
  uploaded to `PyPI <https://pypi.org/project/metoffice-afterburner/>`_ and
  `conda-forge <https://anaconda.org/conda-forge/metoffice-afterburner>`_.

* Added an initial beta version of the new :doc:`Inline Regridder app <rose_apps/inline_regridder/guide>`,
  which can be used to regrid climate model data in 'in-line' mode i.e. as a climate
  simulation/experiment is running.

* The ``abrun.sh`` script now displays a deprecation warning when it is invoked.
  Users should now use the Python3-specific :ref:`apprun.sh script <apprun.sh>`
  as a like-for-like replacement.

**Noteworthy tickets addressed in this release**

Ticket #319:
    Updated the :doc:`Installing Afterburner Software </installing>` chapter to
    reflect the latest installation advice.

Ticket #316:
    Updated the ``abrun.sh`` script to use 'production_legacy-os43-2' as the default
    scitools module (Met Office platforms only).

Ticket #315:
    Removed the ``lib/bootstrap module`` and all references to it. This module
    had ceased to serve a useful purpose and was liable to give rise to module
    conflicts if the afterburner package was installed into, for example, a
    conda environment.

Ticket #313:
    Added a new Afterburner app - the Inline Regridder - which is designed to be
    used for regridding climate model data in 'in-line' mode, i.e. as a climate
    simulation is running (e.g. under the control a Rose suite).
    For details on configuring and running this new app please refer to the
    :doc:`app documentation <rose_apps/inline_regridder/guide>`.

Version 1.3.2b1
---------------

**Release Date:** 29 April, 2021

**Summary**

This beta release includes a small number of enhancements and bug fixes to the
core Afterburner library code and documentation. The principal changes are
summarised below.

This release provides compatibility with Iris version 3.0.

**Noteworthy tickets addressed in this release**

Ticket #310:
    Updated the MASS Data Robot app to include support for specifying ``lbproc``
    and/or ``lbtim`` options when retrieving files from UM data collections.
    Refer to the :doc:`user guide <rose_apps/mass_data_robot/guide>` for further
    information.

Ticket #308:
    Added the ``--stream_out`` option to the :mod:`afterburner.contrib.umfilelist`
    module. This new option may be used in those cases where instantaneous model
    data (e.g. at timestep frequency) has been output to a climate meaning stream
    such as ``apl``. In this case the ``--stream_out`` option can be used to specify
    the desired stream name to use in output filenames, e.g. ``expida.pl1970dec.pp``
    in the case of, say, ``apa`` model data being stored in ``apl``-stamped files.

Ticket #307:
    Updated the ASoV Calculator app so as to correctly load and process 'instantaneous'
    model data, i.e. at timestep frequency rather than meaned or otherwise aggregated.

Ticket #305:
    Made a small number of updates in order to achieve compatibility with Iris v3.0.
    Most of the changes were related to the relocation of the ``equalise_attributes()``
    function to the ``iris.util`` module.

Ticket #303:
    Added the first cut of a user guide for the :doc:`ASoV Calculator app <rose_apps/asov_calculator/guide>`

Ticket #300:
    Applied fix for a bug whereby dates earlier than the year 1000 for data held
    in MASS were not being handled correctly.

Version 1.3.1
-------------

**Release Date:** 6 August, 2020

**Summary**

This represents the v1.3.1 release of the Afterburner software suite. This release
incorporates a handful of minor enhancements and bug fixes identified since the
v1.3.1rc1 candidate release.

**Noteworthy tickets addressed in this release**

Ticket #297:
    Enhanced the Climate Model Monitor v2 (CMM2) app so as to enable users to
    specify the name of the model run to use when the parent suite contains
    multiple climate models, and those models have names that are different
    from the suite name. In such cases the the (sub)model name should be appended
    to the suite name, separated by a '_' character, e.g 'u-xy123_atmos' for
    a model named 'atmos' executed as part of suite 'u-xy123'.

Ticket #296:
    Implemented the :func:`afterburner.utils.cubeutils.vsummary` function for
    generating a verbose text description of a cube. The description includes extra
    information over and above that provided by the ``cube.summary()`` method.

Ticket #293:
    Added the ``bin/apprun.sh`` shell script as a more capable replacement of
    the ``abrun.sh`` script for running Afterburner apps. Featuring a richer set
    of command-line options, the new script also runs apps against Python 3 by
    default. Refer to the :ref:`script documentation <apprun.sh>` for details.

Ticket #269:
    Added a new :doc:`/tutorials/derived_diags` tutorial.

Version 1.3.1rc1
----------------

**Release Date:** 26 February, 2020

**Summary**

This release candidate wraps up a small number of enhancements and bug fixes to
the core library code and documentation. The main updates are summarised below.

**Noteworthy tickets addressed in this release**

Ticket #288:
    Updated the documentation for the Diagnostic Generator app with a subsection
    on how to utilise Afterburner's general-purpose derived diagnostic classes
    within processor definitions. This new subsection can be found under the
    Configuring The Application > Processor Definitions > Utilising Derived
    Diagnostic Classes subsection of the :doc:`app documentation <rose_apps/diagnostic_generator/guide>`.

Ticket #286:
    Fixed a couple of minor issues in the way that the ``ModelEmulator`` classes
    handle postproc version numbers. Firstly, the command-line option was renamed
    from ``pp_vn`` to ``pp-vn`` to conform to the customary hyphen-based syntax
    used to name such options. Secondly, the value of this option is coerced to
    be a string, thus covering those cases where the value is read as an integer
    or float from, for example, an app config file.

Ticket #284:
    Updated a small number of date-time utility functions so as to check that any
    user-defined calendar is valid; that is, it is one of the calendars recognised
    by the ``cf_units`` module.

Ticket #283:
    Updated the ``setup.py`` script such that it now installs the new ``tools``
    directory when the script is invoked with the ``install`` command. If need be,
    this behaviour can be disabled using the new ``--no-tools-dir`` option
    recognised by the script.

Ticket #281:
    Updated the Climate Model Monitor v2 app (CMM2) to enable users to specify
    the line width, marker size, marker colour and transparency level to use when
    producing time-series plots.

Ticket #269:
    Added a new software tutorial, :doc:`/tutorials/derived_diags`, which describes
    Afterburner's classes and functions for generating arbitrary derived diagnostics.

Version 1.3.1b2
---------------

**Release Date:** 19 December, 2019

**Summary**

This beta release incorporates a number of bug fixes and enhancements, the main
ones of which are summarised below. In addition, this release includes a
collection of new tutorials focussed on some of the key areas of Afterburner
software functionality (see :doc:`tutorials/index`).

**Noteworthy tickets addressed in this release**

Ticket #280:
    Added a small number of scripts (in the newly created ``tools`` directory)
    which can be used for logging usage of the afterburner package and its apps.
    This is *prototype code* that is intended to be used by local administrators
    of the Afterburner software package.

Ticket #275:
    Updated and improved the documentation for the Diagnostic Generator app.

Ticket #273:
    Added a new software tutorial, :doc:`/tutorials/climatology_stats`, which
    describes the convenience functions available for calculating climatological
    statistics from Iris cubes.

Ticket #271:
    Added a new software tutorial, :doc:`tutorials/mass_query`, which describes
    the functionality provided for querying model data and metadata held in the
    MASS data archive

Ticket #268:
    Updated the :class:`NetHeatFluxIntoOcean <afterburner.processors.diags.ocean.net_heat_flux.NetHeatFluxIntoOcean>`
    diagnostic processor class to accept, as optional inputs, diagnostics representing
    net surface downward longwave flux and/or surface upward latent heat flux.
    These can be used in place of the existing diagnostics that are currently used
    to derive these quantities.

Ticket #267:
    Added a new software tutorial, :doc:`/tutorials/spatial_stats`, which describes
    Afterburner's convenience functions for computing spatial statistics.

Ticket #266:
    Added the :func:`afterburner.utils.dateutils.iter_dates` generator function,
    which may be used to generate a sequence of datetime objects or numeric
    time-since-refdate values covering a user-defined time range at a specified
    time step.

Ticket #264:
    Added an initial collection of :doc:`tutorials/index` to the Afterburner
    documentation set.

Ticket #263:
    Added the :func:`afterburner.utils.cubeutils.rebase_time_coords` function,
    which may be used to rebase a list of Iris time coordinate objects to a
    common time datum -- either one specified by the user or else the earliest
    datum occurring in the list.

Ticket #239:
    Updated the :mod:`afterburner.contrib.umfilelist` module to allow users to
    override the reinitialisation period for a daily or instantaneous stream that
    is being used, in a non-standard manner, to hold climate mean data. This is
    achieved by negating the required value, e.g. -30 (days) in the case of
    monthly-mean data, -90 for seasonal-mean data, -360 for annual-mean data,
    and so on.

Version 1.3.1b1
---------------

**Release Date:** 23 August, 2019

**Summary**

This is the initial beta release of Afterburner version 1.3.1. In addition to
a number of enhancements and new features, the most notable of which are summarised
below, this release includes an initial beta version of the Diagnostic Generator
app. This new Afterburner app enables users to generate custom (aka derived) model
diagnostics as a climate simulation is running. Refer to the
:doc:`app user guide <rose_apps/diagnostic_generator/guide>` for more information.

**Noteworthy tickets addressed in this release**

Ticket #261:
    Added the :mod:`afterburner.utils.maskutils` module, which contains utility
    functions for performing a selection of common array masking operations.

Ticket #260:
    When executing a MOOSE command using the functions in the :mod:`afterburner.io.moose2`
    module it is now possible to specify additional command options via environment
    variables of the form MOOSE_<subcommand>_OPTIONS, where <subcommand> is the
    capitalised name of one of the sub-commands supported by the MOOSE command-line
    interface, e.g. 'MDLS'. Refer to the :class:`MooseCommand <afterburner.io._moose_core.MooseCommand>`
    class for further information.

Ticket #258:
    Enhancements to the :class:`NetHeatFluxIntoOcean <afterburner.processors.diags.ocean.net_heat_flux.NetHeatFluxIntoOcean>`
    diagnostic processor class, including the ability to specify land-area fraction
    data either via the input cubelist or via an Iris-supported input file. The
    land-area fraction is then used to mask the input diagnostics.

Ticket #256:
    Updated the Afterburner documentation with improved information concerning
    the currently available Afterburner processor classes. See the new
    :doc:`processors` index page.

Ticket #253:
    Added the :class:`PolewardHeatTransport <afterburner.processors.diags.atmos.poleward_heat_transport.PolewardHeatTransport>`
    class for generating a Poleward Heat Transport diagnostic: moist static energy
    (the default) or dry static energy.

Ticket #252:
    Applied a small fix to work around the issue whereby a request to set the
    extent of the X axis in a matplotlib axis object using Gregorian date-time
    coordinates raises an exception. This fix is mainly of interest to users of
    the Climate Model Monitor app.

Ticket #251:
    Added the ``bin/abdiagnose.py`` utility script, which may be used to print useful
    diagnostic information relating to the Afterburner runtime environment. Refer
    to the script's docstring for further details.

Ticket #249:
    Added the :mod:`afterburner.apps.model_emulators` module, which contains
    classes for emulating the generating of data files for a user-specified time
    period and climate model. The initial implementation includes support for
    the UM, NEMO and CICE models.

Ticket #246:
    Updated the various MOOSE interface modules, and the ``model_monitor2`` module,
    to optimise MOOSE commands used to query the time extent of a PP-based
    data collection in MASS. The updated command syntax limits a MOOSE query to
    one (or a few) vertical levels. This means that it is now possible to query
    very long model runs without hitting up against certain MOOSE query limits
    (typically the 'maximum number of file atoms' limit).

Ticket #238:
    Implemented an initial beta version of the new Diagnostic Generator app which
    can be used to generate custom/derived model diagnostics, either off-line or
    on-the-fly as a climate suite is running. Refer to the :doc:`rose_apps/diagnostic_generator/guide`
    user guide for details.

Version 1.3.0
-------------

**Release Date:** 2 April, 2019

**Summary**

This represents the v1.3.0 release of the Afterburner software suite. This release
incorporates some minor enhancements and bug fixes identified since the v1.3.0rc1
candidate release.

**Noteworthy tickets addressed in this release**

Ticket #245:
    Updated the Afterburner app documentation to include a description of the
    use of the SCITOOLS_MODULE environment variable to specify the name of a
    Met Office SciTools module to load prior to invoking an app.

Ticket #243:
    Updated the :doc:`Writing Processor Classes </dev_guide/processors>` chapter
    in the Afterburner documentation, including new sections on writing diagnostic
    processor classes, and on following the recommended development methodology.

Ticket #242:
    Updated the various MOOSE interface modules so as to use a single logger
    object named 'afterburner.io.moose'. This logger object can be obtained from
    within client code by calling the function :func:`afterburner.io.moose2.get_moose_logger`.

Ticket #240:
    Applied an update to the Climate Model Monitor v2 (CMM2) app to work around
    an issue whereby the MOOSE interface hits the 'maximum number of query items'
    limit for very long climate simulations (> several hundred years).

Version 1.3.0rc1
----------------

**Release Date:** 4 March, 2019

**Summary**

* This release candidate mainly bundles up a number of minor enhancements and
  bug fixes to the core Afterburner Python library in readiness for a formal
  v1.3.0 software release.

* This release includes a preliminary beta version of a new ASoV Calculator
  application for Analysing Scales of Variance associated with model diagnostics.
  Refer to the :mod:`afterburner.apps.asov_calculator` module documentation for
  more information.

* Implemented the new :class:`afterburner.coords.CoordTransformer` class, instances
  of which can be used to transform geodetic coordinates between two `cartopy`_
  coordinate reference systems. Pre-canned instances exist for transforming
  coordinates between OSGB 1936 and WGS 1984 coordinate systems.

**Noteworthy tickets addressed in this release**

Ticket #234:
    Updated the :class:`afterburner.utils.NamespacePlus` class with methods to
    support iteration over an instance object's attributes and/or names, and
    for testing for the presence of a given attribute.

Ticket #230:
    Modified the :class:`afterburner.coords.CoordRange` class such that instances
    can now be compared for equality and, by virtue of being hashable, can now
    be added to, for example, set objects.

Ticket #228:
    Modified the :mod:`afterburner.contrib.umfilelist` module to handle the case
    where a reinitialisation period is specified in combination with one of the
    meaning period streams ap1-ap4.

Ticket #226:
    Added the :class:`afterburner.io.datacaches.SingleDirectoryDataCache` class
    and the :class:`afterburner.io.datastores.NullDataStore` class. The former
    class is intended for use where, as the name suggests, all input files reside
    within a single directory. The latter class can be used to specify a no-op
    back-end data store object to use, for example, with read-only data caches.

Ticket #224:
    Added two utility functions - get_cylc_task_work_dir and get_cylc_variables -
    to the :mod:`afterburner.utils` module for querying cylc-related run-time
    properties.

Ticket #223:
    Added the :func:`afterburner.modelmeta.cf_cell_method_from_lbproc` function
    and the :func:`afterburner.utils.fileutils.filter_by_sentinel_files` function.

Ticket #222:
    Developed an initial beta version of the new ASoV Calculator application for
    Analysing Scales of Variance. See :mod:`afterburner.apps.asov_calculator` for
    more information.

Ticket #221:
    Updated the ``abrun.sh`` shell script to enable users to specify an Afterburner
    module to load via the AFTERBURNER_MODULE environment variable. At present
    this feature is mainly intended for use on the Met Office HPC. For more
    information see :ref:`abrun.sh`.

Ticket #219:
    Added the :class:`afterburner.coords.CoordTransformer` class, instances of
    which can be used to transform geodetic coordinates between two `cartopy`_
    coordinate reference systems. Pre-canned instances exist for transforming
    coordinates between OSGB 1936 and WGS 1984 coordinate systems.

Version 1.3.0b2
---------------

**Release Date:** 18 October, 2018

**Summary**

* Two new modules - :mod:`afterburner.stats.temporal` and :mod:`afterburner.stats.spatial`
  - have been written which contain convenience functions for calculating commonly
  required temporal and spatial statistics, respectively.

* Modules which previously depended upon the ``netcdftime`` package (for handling
  datetime objects) have been updated to use the newer `cftime`_ package, if the
  latter is present in the Python run-time environment.

* A new utility function, :func:`afterburner.utils.cubeutils.compare_cubes`, has
  been written which, as the name suggests, enables the comparison of two Iris
  cube objects. This is a useful facility when trying, for example, to isolate
  cube concatenation/merge problems.

**Noteworthy tickets addressed in this release**

Ticket #216:
    Updated the core library code to use the new `cftime`_ package, if it is
    present, in preference to the older ``netcdftime`` package.

Ticket #214:
    Introduced the new :mod:`afterburner.stats.spatial` module as a container
    for spatial statistical functions. The initial implementation includes the
    calc_spatial_stat() utility function, which provides a general-purpose
    interface to the spatial aggregation capabilities supported by Iris.

Ticket #211:
    Implemented a compare_cubes() function, which can be accessed via the
    :mod:`afterburner.utils.cubeutils` module. As the name suggests, this function
    can be used to compare two cubes, reporting any differences in attributes or
    attached objects, such as coordinates and cell methods. This can be useful
    when trying to resolve cube concatenation/merge problems.

Ticket #210:
    Fixed an issue in the Climate Model Monitor v2 (CMM2) application whereby
    extending the time-series for a diagnostic failed with a cube concatenation
    error if the diagnostic was associated with a long name but not a CF standard
    name. Note that this fix will **not** be back-ported to the original CMM app.

Ticket #205:
     Implemented a number of basic convenience functions for calculating time-based
     statistics and climatologies from Iris cubes. These functions are provided in
     the new :mod:`afterburner.stats.temporal` module.

Version 1.3.0b1
---------------

**Release Date:** 8 August, 2018

**Summary**

The main focus of this release is the ability to run Afterburner software under
both Python 2.7 and Python 3 (more specifically 3.5 or later). This capability
has been achieved by making use of the cross-compatiblity features provided by
the `six <https://pythonhosted.org/six/>`_ module.

The ``abrun.sh`` shell script has also been updated to recognize a new ``--py``
option. This option may be used to specify a particular version of Python under
which to invoke an Afterburner application. One can specify just the major version,
e.g. ``--py3``, or the major and minor version, e.g. ``--py2.7`` or ``--py3.6``.

**Noteworthy tickets addressed in this release**

Ticket #190:
    Major code changes implemented in order to provide code compatibility with
    both Python 2.7 and Python 3.5 (or later).

Version 1.2.1
-------------

**Release Date:** 30 July, 2018

**Summary**

This minor release fixes an issue masking land-area fraction data within the
Climate Model Monitor v2 application. It also adds the capability to apply a
sea-area fraction correction to user-selected diagnostics (view the
:doc:`app documentation <rose_apps/model_monitor2/guide>`).

An enhancement to the ``abrun.sh`` shell wrapper script allows users to define
the name of the scitools module to load prior to running an Afterburner
application.

**Noteworthy tickets addressed in this release**

Ticket #206:
    Fixed the masking of sea grid cells in land-area fraction data loaded by the
    Climate Model Monitor v2 application. A default area-fraction threshold of
    0.5 is used to differentiate land and sea cells; a different threshold may be
    specified by the user (via the app config file). See also the summary of
    ticket #182 below.

Ticket #204:
    Updated the ``abrun.sh`` shell script to handle the specification and loading
    of a scitools module if one is defined via the SCITOOLS_MODULE environment
    variable. This should be a useful feature if you are invoking Afterburner
    apps from a Rose/cylc suite.

Ticket #201:
    Added the :class:`NaoIndex <afterburner.processors.diags.atmos.nao_index.NaoIndex>`
    diagnostic processor class, and incorporated *experimental* support for a new
    NAO Index statistic to the CMM2 app.

Ticket #199:
    Applied enhancements to the :mod:`afterburner.misc.stockcubes` module.

Ticket #182:
    Updated the Climate Model Monitor v2 application to enable a sea-area fraction
    correction to be applied to selected diagnostics. This new feature is primarily
    aimed at UM diagnostics since ocean diagnostics (e.g. as output by the NEMO
    model) have normally had a land-sea mask applied.

Version 1.2.0
-------------

**Release Date:** 26 April, 2018

**Summary**

This represents the v1.2.0 release of the Afterburner software suite. This release
mainly just incorporates some minor enhancements and bug fixes identified since
the v1.2.0rc1 candidate release described below.

This latest release has been successfully tested against Iris version 2.0.0.
Since this major new version of Iris is associated with a number of significant
underlying code changes (the replacement of the biggus module by
`dask <https://dask.pydata.org/en/latest/>`_, for example), there may
be code compatibility issues which have not yet been exposed by the Afterburner
test suite. Any such issues may usefully be reported to the development team at
afterburner@metoffice.gov.uk.

Python 3 Compliance Note: Although the Afterburner code base is Python 3 compliant
(and has been for some time), a small number of prerequisite packages/modules are
not yet compliant. It is hoped that these packages/modules can be ported, by their
respective maintainers, in the near future.

**Noteworthy tickets addressed in this release**

Ticket #200:
    Added support for a ``postproc_vn`` configuration option to be applied to
    definitions of climate models within the Climate Model Monitor v2 application.
    This option enables users to monitor diagnostics serialized in netCDF files,
    the names of which adhere to the naming conventions encapsulated in the
    postproc v2.x model post-processing scripts. At present this new option is
    mainly of relevance to NEMO and CICE model output.

Ticket #198:
    Added the has_global_domain() function to the :mod:`afterburner.utils.cubeutils`
    module. This function can be used to determine if an Iris cube is associated
    with a regular gridded dataset whose spatial domain is of global extent.

Ticket #197:
    Applied conditional logic to calls to the iris.FUTURE.context() function in
    order to prevent warnings being emitted as a result of the use of deprecated
    future options at Iris v2.0 and later.

Ticket #195:
    Resolved the issue whereby the latitude and longitude ranges used to define
    geographical regions for the Climate Model Monitor app were being interpreted
    as *closed* intervals. The behaviour has been updated so that the ranges are
    now interpreted as *left-closed* intervals, meaning that contiguous regions
    (such as the southern and northern hemispheres) do not, by default, select
    overlapping rows or columns. A new application configuration option, named
    ``treat_region_coords_as``, may be used to request an alternative treatment
    of the latitude and longitude ranges.

Version 1.2.0rc1
----------------

**Release Date:** 22 March, 2018

**Summary**

This v1.2.0 release candidate is primarily focussed on minor code enhancements
and bug fixes in advance of the final v1.2.0 release. No major new features have
been introduced.

The v1.2.0rc1 release candidate has been tested against Iris v2.0.0rc1. With
the exception of a solitary Iris-related issue, all of the Afterburner unit tests
pass. It is envisaged, therefore, that the Afterburner v1.2.0 release should be
compatible with Iris v2.0.0.

**Noteworthy tickets addressed in this release**

Ticket #189:
    The stream identifier (apy, apm, etc) is now included within the legend labels
    depicted on plots produced by the Climate Model Monitor v2 app. Previously,
    it was not obvious from the plots whether they were derived from annual-mean
    or monthly-mean source data.

Ticket #188:
    Added filename and filepath generator functions, respectively, to the
    :class:`FilenameProvider <afterburner.filename_providers.FilenameProvider>`
    base class and the :class:`DataCache <afterburner.io.datacaches.DataCache>`
    base class. These functions may be used to iterate efficiently over long
    sequences of filenames/paths (compared with the equivalent get_* functions,
    which return lists). With the addition of these new generator functions, the
    existing :func:`afterburner.io.datacaches.DataCache.iter_files` function
    (which was implemented in an inefficient manner) has been marked as deprecated.

Ticket #185:
    Refactored the :mod:`afterburner.contrib.umfilelist` module to include support
    for *iteration* over UM filenames (in addition, that is, to the original,
    and potentially less efficient method, of returning a complete list of filenames).

Ticket #184:
    Updated the :class:`DateTimeRange <afterburner.utils.dateutils.DateTimeRange>`
    class to allow the start or end date (but not both) to be set to None at
    initialisation time. If this mechanism is used then the start date gets reset
    to the date-time equivalent of negative infinity, while the end date gets reset
    to the date-time equivalent of positive infinity.

Ticket #180:
    Refreshed the :doc:`Introduction chapter <intro>` in the Afterburner
    documentation.

Version 1.2.0b1
---------------

**Release Date:** 1 February, 2018

**Summary**

Key features and new functionality incorporated into this release include:

* An initial beta version of the **Climate Model Monitor v2** application (CMM2).
  Key features of this new app include: the ability to calculate a wider variety
  of statistical measures (e.g. sum, minimum, maximum), and the ability to handle
  simple diagnostics serialized in netCDF format. For more information please
  refer to the :doc:`app documentation <rose_apps/model_monitor2/guide>`.

* A number of enhancements to the date-time classes and functions provided by
  the :mod:`afterburner.utils.dateutils` module. The main enhancements are
  summarised below under their respective ticket entries.

**Noteworthy tickets addressed in this release**

Ticket #175:
    Updated the :mod:`afterburner.processors.diags.derived` module in order to
    address issues running against Iris v2.0a.

Ticket #172:
    Implemented the :func:`afterburner.utils.dateutils.iter_date_chunks` function
    which can be used to iterate over the meaning/accumulation periods comprising
    a specified time interval.

Ticket #171:
    Added support for the new 'scalar' grid type to the NemoFilenameProvider and
    NemoMetaVariable classes.

Ticket #167:
    Added an interval_type attribute to the afterburner.utils.dateutils.DateTimeRange class
    so as to enable the nature of the time interval to be defined, i.e. open,
    left-open, left-closed, closed.

Ticket #166:
    Added the :class:`ImmutableDateTime <afterburner.utils.dateutils.ImmutableDateTime>`
    class to the afterburner.utils.dateutils module. This class may be used to
    create immutable date-time objects, such as the DATETIME_POS_INF and
    DATETIME_NEG_INF constants, also defined in the dateutils module.

Ticket #165:
    Enhanced the :class:`NetcdfFileWriter <afterburner.processors.writers.netcdf_writer.NetcdfFileWriter>`
    class to supporting appending a cubelist to an existing netCDF file.

Ticket #162:
    Improved the Installing Afterburner Software chapter in the documentation.

Ticket #160:
    Added a contains() method to the :class:`afterburner.utils.dateutils.DateTimeRange`
    class. This new method may be used to check if a particular date-time instant
    occurs within the time range associated with an instance of this class.

Ticket #159:
    Updated various functions in the :mod:`afterburner.utils.dateutils` module to
    provide support for negative dates and dates with years larger than 9999.

Ticket #157:
    Updated the :class:`afterburner.utils.dateutils.DateTimeRange` class with the
    addition of properties `start_ncdt` and `end_ncdt`. These return the start and
    end times, respectively, of the date-time range as netcdftime.datetime objects.

Ticket #126:
    Added an index of contents near the top of most of the afterburner modules.
    This makes is easy to see which classes and/or functions are contained in a
    particular module, and enables quick navigation to each one.

Version 1.1.0
-------------

**Release Date:** 12 October, 2017

**Summary**

This represents the v1.1.0 release of the Afterburner software suite. There are
no significant changes over and above the rc1 release candidate described below.

**Noteworthy tickets addressed in this release**

Ticket #154:
    Added the TemplateDrivenFilenameProvider class to the :mod:`afterburner.filename_providers`
    module.

Version 1.1.0rc1
----------------

**Release Date:** 18 September, 2017

**Summary**

This represents the first release candidate for version 1.1.0 of the Afterburner
software suite. As well as a number of minor enhancements and bug fixes, the
following new capabilities have been added:

* Updated the Climate Model Monitor application to enable users to define their
  own custom diagnostics based on simple formulas involving STASH codes and,
  optionally, numeric constants.

* Developed an experimental Rose/cylc suite (`u-aq151 <https://code.metoffice.gov.uk/trac/roses-u/browser/a/q/1/5/1/trunk>`_)
  that uses rose-bunch and cylc to parallelise data retrieval tasks configured by
  the MASS Data Robot application.

**Noteworthy tickets addressed in this release**

Ticket #151:
    Updated the MASS Data Robot app to enable data retrieval tasks to be parallelised
    using the cylc scheduling framework.

Ticket #147:
    Added support for a new `postproc_vn` option to data request definitions supplied
    to the MASS Data Robot application. If set, for example, to '2.0' then the names
    of requested files comply with those generated by the postproc vn2 post-processing
    script (which essentially means that the filenames are CMIP6-compliant).

Ticket #144:
    Added support for a non-zero return code to the MASS Data Robot app so that
    the completion status can be detected and acted upon by the calling program,
    such as a Rose suite.

Ticket #134:
    Resolved the issue whereby the `file_mode` parameter (used to set a file's
    access permissions) was not being fully honoured by the afterburner.io.datacaches
    and afterburner.io.datastores modules.

Ticket #115: Added functionality to the Climate Model Monitor application to enable
    users to generate and plot simple formula-based custom diagnostics.

Version 1.1.0b2
---------------

**Release Date:** 16 August, 2017

**Summary**

This is primarily a bugfix release, the main thrust of which has been to add
defensive code to handle the substantial changes that have recently been made
to the API of the `netcdftime package <https://github.com/Unidata/netcdftime>`_

**Noteworthy tickets addressed in this release**

Ticket #142:
    Added a new `time_offset` option to the Climate Model Monitor application.
    This option allows users to specify a time offset to apply to the time-series
    plots for all diagnostics from a particular climate model.

Ticket #138:
    Added a :doc:`citation section <citing>` to the Afterburner documentation.

Ticket #137:
    Added a number of utility functions to the :mod:`afterburner.processors.diags.derived`
    module to simplify the process of creating formula-based derived diagnostics.

Ticket #88:
    Added support for read-only access to disk-based model data caches. This
    option will be useful when users wish to access an on-disk data cache owned
    by another user.

Version 1.1.0b1
---------------

**Release Date:** 31 July, 2017

**Summary**

The main pieces of new functionality incorporated into version 1.1.0b1 are as follows:

* An initial beta version of a new MASS Data Robot application. Refer to the
  :doc:`app documentation <rose_apps/mass_data_robot/guide>` for more information.

* New features added to the Climate Model Monitor application, including: the
  ability to control the display order for generated time-series graphs; ability
  to plot diagnostics which straddle multiple UM model versions.

**Noteworthy tickets addressed in this release**

Ticket #139:
    Updated the Climate Model Monitor app to check for unequal time axes on input
    fields when computing custom diagnostics. This can happen if the source data
    files contain data for different time periods (which is usually indicative
    of some earlier data retrieval problem).

Ticket #136:
    Fixed a problem in the Climate Model Monitor app whereby cubes with mis-matched
    time coordinates (scalar v non-scalar) give rise to an Iris cube concatenation
    error. This may happen, for example, if a retrieval of new files from MASS
    for a given diagnostic results in just a single year's worth of data being
    fetched. In such cases Iris demotes the time axis to a scalar coordinate in
    the resulting cube.

Ticket #135:
    Updated the :class:`afterburner.io.datacaches.DataCache` class to check for
    the correct cache scheme type when connecting to an existing data cache
    directory structure.

Ticket #131:
    Updated the :mod:`afterburner.io.datastores` module to handle requests for
    CICE model data.

Ticket #130:
    Updated the Climate Model Monitor app to ignore differences in UM version
    number across a set of input model files.

Ticket #127:
    Made modifications to the :mod:`afterburner.io.datacaches` module to speed
    up Iris data loading operations, especially with regard to large UM PP files.

Ticket #121:
    Updated the Climate Model Monitor app to allow the user to control the order
    in which the time-series graphs are displayed on the output HTML page.

Ticket #109:
    Developed an initial beta version of a new :doc:`MASS Data Robot <rose_apps/mass_data_robot/guide>`
    application.

Ticket #79:
    Added functionality to construct the names of NEMO/CICE files generated by the
    Met Office postproc 2.0 package.

Version 1.0.0
-------------

**Release Date:** 9 May, 2017

**Summary**

This constitutes the v1.0.0 release of the Afterburner software suite. There are
no substantive changes over the v1.0.0rc1 candidate release described below.

**Noteworthy tickets addressed in this release**

Ticket #122:
    Added the :class:`afterburner.metavar.CiceMetaVariable` and
    :class:`afterburner.filename_providers.CiceFilenameProvider` classes as a
    means of supporting CICE model output.

Ticket #120:
    Added the :func:`afterburner.utils.lru_cache` function.

Ticket #117:
     Updated the ensemble-aware data cache classes to optionally handle variables
     with no defined realization identifier (e.g. by placing data files in a
     cache subdirectory called 'r0').

Version 1.0.0rc1
----------------

**Release Date:** 7 April, 2017

**Summary**

This is the first candidate release of version 1.0.0 of the Afterburner software
suite.

The main changes incorporated into this release are as follows:

* Updates to the documentation for the :doc:`Climate Model Monitor <rose_apps/model_monitor/guide>`
  application.

* Added the :class:`afterburner.processors.diags.derived.MipDerivedDiagnostic`
  class. This class can be used to generate derived diagnostics based on a
  CMIP-style formula for a target variable.

* Additional enhancements and fixes applied to the core Afterburner packages.

**Noteworthy tickets addressed in this release**

Ticket #113:
    Resolved an issue in the Climate Model Monitor application whereby the time
    axis range was ignored if only one end of the range was defined.

Ticket #112:
    Added the from_cube() method to the :class:`afterburner.utils.dateutils.DateTimeRange`
    class.

Ticket #107:
    Added the :mod:`afterburner.misc.stockcubes` module, which contains functions
    for generating synthetic Iris cubes which can be useful both for ad hoc
    exploration of Afterburner functionality and for developing formal test code.

Ticket #106:
    Fixed an issue with the Climate Model Monitor app whereby diagnostics with
    a vertical coordinate named 'pseudo-level' were not being handled correctly.

Version 1.0.0b4
---------------

**Release Date:** 14 Feb, 2017

**Summary**

The principal features incorporated into version 1.0.0b4 are:

* A beta-3 release of the Climate Model Monitor application which, in addition
  to some minor bug fixes, includes the ability to control the appearance of the
  plot legend. It can now be restricted to the first plot, drawn separately in
  an extra plot, or disabled altogether. Refer to the :doc:`app documentation
  <rose_apps/model_monitor/guide>` for further details.

* Completely refactored the afterburner.io.moose module as the new
  :mod:`afterburner.io.moose2` module. The latter should now be used for new
  development work, while the original moose module should be considered deprecated.

* Further enhancements and fixes applied to the core Afterburner packages.

**Noteworthy tickets addressed in this release**

Ticket #96:
    Added the capability to control the appearance of the legend in time-series
    plots generated by the Climate Model Monitor application.

Ticket #87:
    Improvements to the various logger objects used by the Afterburner library.
    These are described in a new :doc:`dev_guide/loggers` chapter in the
    Developers Guide.

Ticket #69:
    Implemented the :class:`afterburner.processors.diags.derived.SimpleDerivedDiagnostic`
    class which provides the ability to generate derived diagnostics from
    existing diagnostics based upon simple arithmetic expressions.

Ticket #65:
    Significant refactoring of the afterburner.io.moose module into the new
    afterburner.io.moose2 module. See longer note under the Summary section.

Ticket #62:
    Added a new :doc:`dev_guide/datacaches` chapter to the Developers Guide.

Version 1.0.0b3
---------------

**Release Date:** 19 Jan, 2017

**Summary**

The principal features incorporated into version 1.0.0b3 are:

* A second beta release of the Climate Model Monitor application. This version
  includes, among other things, the ability to monitor climate runs that are part
  of an ensemble. Refer to the :doc:`app documentation <rose_apps/model_monitor/guide>`
  for further details.

* Several new classes and functions added to Afterburner's core Python packages.
  Highlights of these new features are given below.

* Lots of additional enhancements and fixes applied to the core packages.

**Noteworthy tickets addressed in this release**

Ticket #94:
    Added the net-heat-flux-into-ocean custom diagnostic to the Climate Model
    Monitor application. **NOTE:** This diagnostic requires scientific validation
    and should be considered 'experimental' until further notice.

Ticket #93:
    Modified the setup.py script to automatically install the 'etc' directory
    into the target location. This task no longer needs to be done manually.

Ticket #91:
    Added capability to convert an afterburner.coords.CoordRange object to an
    iris.coords.CoordExtent object.

Ticket #90:
    Added support for specifying a time range using DateTimeRange objects when
    creating instances of afterburner.metavar.MetaVariable subclasses.

Ticket #86:
    Fixed a minor bug whereby the size of the query file used during chunked
    'moo select' operations was being calculated incorrectly.

Ticket #74:
    Added the capability to monitor ensemble climate runs within the Climate
    Model Monitor application.

Ticket #66:
    Extended the afterburner.metavar.MetaVariable subclasses so that they can now
    carry spatial coordinate extent metadata.

Ticket #52:
    Implemented the afterburner.utils.dateutils.DateTimeRange class.

Version 1.0.0b2
---------------

**Release Date:** 28 Nov, 2016

**Summary**

The principal features incorporated into version 1.0.0b2 are as follows:

* Initial beta release of the Climate Model Monitor application (refer to the
  :doc:`app documentation <rose_apps/model_monitor/guide>` for full details).

* Several new classes and functions added to Afterburner's core Python packages.
  Highlights of these new features are given below.

* Numerous enhancements and fixes applied to Afterburner's core Python packages.

**Noteworthy tickets addressed in this release**

Ticket #75:
    Added TOA Radiation Balance diagnostic processor class.

Ticket #73:
    Added support for popular command-line arguments (--version, --quiet,
    --verbose, --debug) to the afterburner.apps.AbstractApp class.

Ticket #70:
    Added guess_aggregation_period() function to the afterburner.utils.cubeutils
    module. This function may be used to guess the aggregation period associated
    with a cube, e.g. daily-mean, monthly-mean, and so on.

Ticket #67:
    Added new processor classes to generate Streamfunction and Velocity Potential
    diagnostics from global wind speed data.

Ticket #63:
    Added the from_datetime() static method to the DateTimeRange class in
    order that instances of the class may be constructed from 'datetime.datetime'
    or iris.time.PartialDateTime objects.

Ticket #60:
    Enhancements to callback functions in afterburner.utils.cubeutils module.
    Added/renamed following Iris callback functions: is_time_mean, is_time_minimum,
    is_time_maximum.

Ticket #59:
    Added the NetcdfFileWriter class to the afterburner.processors.writers module.
    This class can also be imported via afterburner.io.NetcdfFileWriter.

Ticket #58:
    Fixed issue whereby the abrun.sh script failed when invoked on Mac OS X
    systems without the AFTERBURNER_HOME_DIR shell variable having being defined.

Ticket #56:
    Added query_time_extent() function to the afterburner.io.moose module. This
    new function may be used to determine the time extent covered by a MASS
    data collection.

Ticket #54:
    Added minimal_data keyword argument to load_data() method in class
    afterburner.io.datacaches.DataCache.

Ticket #51:
    Added a new processor class to generate the Transient Eddy Kinetic Energy
    diagnostic from global wind speed data.

Ticket #50:
    Added support for the PYTHON_EXEC and SCITOOLS_PATH variables in the abrun.sh
    script. These optional variables allow specification of the Python command
    to use, and the location of MOSciTools packages.

Ticket #47:
    Added partial support for handling null-valued time ranges passed to
    meta-variables.

Ticket #31:
    Added the afterburner.modelmeta module, which acts as a central container
    for key pieces of climate model metadata.

.. _cartopy: https://github.com/SciTools/cartopy

.. _cftime: https://github.com/Unidata/cftime
