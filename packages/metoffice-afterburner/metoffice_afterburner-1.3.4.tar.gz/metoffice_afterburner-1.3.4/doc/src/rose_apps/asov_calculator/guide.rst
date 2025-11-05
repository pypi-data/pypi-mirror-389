***************
ASoV Calculator
***************

**Status:** Beta-1 Test Version

**Sample Rose Suite:** `u-be543`_ (login required)

**Rose App Name:** asov_calculator

**App Class Path:** :class:`afterburner.apps.asov_calculator.AsovCalculator`

.. contents::
   :depth: 3

Overview
========

The ASoV Calculator app is a Rose-enabled application for calculating histogram
(binned frequency) data from one or more diagnostics output by a climate simulation.
ASoV is short for Analysing Scales of Variability. The original methodology was
applied to precipitation data but the technique ought to be applicable to any
suitable scalar geophysical diagnostics/quantities.

The app can be configured to run either in parallel with a climate simulation
(so-called 'in-line' mode), or else as a separate post-processing task working
with existing model data files on disk ('off-line' mode).

In either mode, the app currently reads diagnostic data from model files in UM
fieldsfile or PP format. By default, required input files are assumed to reside
within a single directory. This is the typical situation in the case of output
from the Met Office Unified Model (where the directory is often named 'History_Data').
As will be described later, it is also possible to load input data from a hierarchy
of data directories.

The actual ASoV histogram data is calculated by counting the number of data values
that fall within each user-defined 'bin' (a value range). In Iris terms this
translates to a collapse operation over the time dimension (by default) of an input
cube using the ``iris.analysis.COUNT`` aggregation method. The binning of data is
applied to each grid cell in the input data. The resulting collection of histogram
data is then saved to disk in netCDF format.

In its default configuration the app appends the data for the current cycle
point to a file of cumulative data, i.e. one containing all histogram data
calculated to date. A scalar time coordinate in the cumulative file records the
*overall* time period spanned by the contained data. Ordinarily the data for the
current cycle point is *not* saved to disk, but this can be enabled if required.
Another app configuration option allows users to save the ASoV data for each
cycle point to an ever-expanding time-series file. This facilitates, for example,
the subsequent computation of cumulative values for arbitrary time periods
(arbitrary within the overall period spanned by the parent suite, that is).

The following fragment of output from the ``ncdump`` command shows the typical
appearance of cumulative histogram data when serialised in netCDF format. The
original precipitation field from which the data was derived has dimensions
``(time, latitude, longitude)``::

    dimensions:
    	bin_value = 100 ;
    	latitude = 144 ;
    	longitude = 192 ;
    	bnds = 2 ;
    variables:
    	int bin_count(bin_value, latitude, longitude) ;
    		bin_count:standard_name = "precipitation_flux" ;
    		bin_count:long_name = "number of values per bin" ;
    		bin_count:units = "1" ;
    		bin_count:um_stash_source = "m01s05i216" ;
    		bin_count:cell_methods = "time: mean (interval: 1 hour)" ;
    		bin_count:coordinates = "time" ;
    	double bin_value(bin_value) ;
    		bin_value:bounds = "bin_value_bnds" ;
    		bin_value:units = "kg m-2 day-1" ;
    		bin_value:long_name = "bin_value" ;
    		bin_value:comment = "Coordinates represent the lower bound of each bin." ;
    	double bin_value_bnds(bin_value, bnds) ;
    	double time ;
    		time:bounds = "time_bnds" ;
    		time:units = "hours since 1970-01-01 00:00:00" ;
    		time:standard_name = "time" ;
    		time:calendar = "360_day" ;
    	double time_bnds(bnds) ;

The ``time`` variable, which now represents a *scalar coordinate*, records the
approximate mid-point of the time period over which data has been accumulated.
The ``time_bnds`` variable records the actual start and end points of the period.

The ``bin_value`` and ``bin_value_bnds`` variables record the lower value, and
the lower/upper bounds, respectively, of the bins used in the frequency analysis.
Defined in this way, there is duplication of the lower bin value across these
two variables. In future, however, the decision might be made to store the mid-value
of the bin in the ``bin_value`` variable.

Application Inputs
==================

The main input to the ASoV Calculator app consists of model data files that
contain the source diagnostics for which to calculate histogram data. In the
current version of the app, binning is achieved by collapsing (aggregating) over
the time axis. Accordingly it is assumed that the source diagnostics have a rank
of 3 or more, with time as the left-most (slowest-varying) dimension, e.g.
``(time, lat, lon)``, ``(time, height, lat, lon)``, and so on.

It is further assumed that all of the model data files reside in a single directory
on the file system since that is the usual layout utilised by the Unified Model
(when the directory is typically the one pointed to by the ``$DATAM`` environment
variable).

If the app is run as a post-processing task then input files can be read from
a hierarchy of data directories conforming to one of Afterburner's supported
data caching schemes - more on this later on in the `Data Reader Options`_ section.

The names of the files to read for a given diagnostic are determined according
to a user-defined filename template, as discussed under the `Filename Templates`_
section below.
 
Application Outputs
===================

The histogram data calculated for a given diagnostic is written to potentially
multiple netCDF files. By default the histogram data generated from a particular
set of input files - e.g. those for a particular suite cycle point - is *appended*
to a netCDF file named ``cumulative.nc``.

As we saw earlier, the file of cumulative binned data doesn't include a time dimension,
merely a scalar time coordinate which records the time period spanned by the 
cumulative data. If desired, a file containing a growing time-series of the binned
data can be requested; by default this file is named ``timeseries.nc``.

Finally, it is also possible to request that the binned data for each cycle point
is saved separately to a file whose name is derived from the cycle point identifier,
e.g. ``20201201T1200.nc`` for the cycle run at 12:00Z on 1 Dec 2020. It shouldn't
normally be required to output these files if the time-series file has also been
requested.

The aforementioned files are saved to the directory defined by the ``[data_writer]output_dir``
app config option (see `Data Writer Options`_). The actual names of the output
files are determined by user-configurable filename templates, as described in the
next section - the filenames shown above are merely the defaults.

To avoid inconveniently long output filenames - and the creation of potentially
large numbers of output files in a single directory - the ASoV Calculator app
writes data to netCDF files stored within a hierarchy of subdirectories, the
names of which are derived from the names of the model streams and diagnostics
specified in the app config file. The hierarchy of subdirectories currently
adheres to the following scheme::

    <output_dir>           # top-level directory defined in the app config file
      <stream_id>
        <var_id>
          <region_name>    # default region is 'global'
            cp1.nc         # per-cyclepoint files
            cp2.nc
            cumulative.nc  # cumulative data for all cyclepoints
            timeseries.nc  # timeseries data covering all cyclepoints
    
    EXAMPLE:
    
    /users/mary/asov_data/
      apa/
        precip/
          global/
            cumulative.nc
            timeseries.nc

This directory hierarchy is merely the default scheme; it may be modified by
customising the templates used to generate the names of output files, as we'll
see in the next section...

Filename Templates
==================

The ASoV Calculator app needs to know the names of the input files from which to
read source diagnostics, and also the names of the output files in which to save
histogram data. This is achieved through the use of user-defined *filename templates*,
one covering input files, and three covering the different kinds of output files
described in the previous section.

Each filename template is a text string containing a combination of free text
and named tokens (from a controlled list - see table below) enclosed in brace
characters, e.g. ``{runid}`` gets replaced by the current model run/job id. 

By way of example, the default template for PP input files, as defined in the
sample app config file, looks something like this:

.. code-block:: ini

   [data_reader]
   input_filename_template={runid}{dotstream}*.pp 

Here, the ``{runid}`` and ``{dotstream}`` tokens get replaced at runtime with
the values associated with the model diagnostic currently being processed. The
``runid`` token is fairly self-explanatory. The ``dotstream`` token represents
the stream name with a '.' character inserted at position 1, e.g. 'a.py', 'o.ny'
and so on.

A comparable filename template for the netCDF output file used to store cumulative
histogram data might look something like this:

.. code-block:: ini

   [data_writer]
   all_cp_filename_template={stream_id}/{var_id}/{region_name}/cumulative.nc

.. note:: In most cases you'll want the filename template to yield *unique names*
   for the set of stream/variable/region combinations configured for a given run
   of the application. If not then the possibility exists that the output file
   created for a given diagnostic may overwrite that used for some other diagnostic
   generated earlier in the processing sequence.

The list of currently recognised filename tokens is shown in the table below.

=========================== =================
Token (and aliases)         Substituted Value
=========================== =================
model, model_name           Model name, e.g. 'UM'
suite, suite_id, suite_name Suite name, e.g. 'mi-ab123'
runid                       Run ID, e.g. 'ab123' (automatically derived from the suite name)
realm                       Realm abbreviation, e.g. 'a' for atmos (automatically derived from the stream name)
realization, realization_id Realization (ensemble member) identifier, e.g. 'r1i2p3'
stream, stream_id           Stream name, e.g. 'apy' (automatically updated as each stream is processed)
dotstream                   Stream name with a '.' in position 1, e.g. 'a.py' (automaticaly derived from the stream name)
var_id                      STASH code or CF standard name
lbproc                      Value of the LBPROC PP header item (default: 128)
lbtim                       Value of the LBTIM PP header item (default: 122)
data_start_date             The start date of the output data (see also `Datetime Format`_)
data_end_date               The end date of the output data (see also `Datetime Format`_)
region_name                 The region name (default: 'global')
cycle_point                 The current cycle point identifier
=========================== =================

The above list may be extended with arbitrary user-defined tokens simply by adding
an option with the desired name (and a default value) to the ``[namelist:diagnostics(_defaults_)]``
section of the app config file. The new option can, and usually should, be
overridden for individual diagnostics.

By way of illustration, to include a custom token named ``mip_name`` in a filename
template one could modify the app config file as follows:

.. code-block:: ini

   [data_writer]
   # amend template to use the mip_name token
   all_cp_filename_template={stream_id}/{var_id}/{region_name}/cumulative_{mip_name}.nc
   ...

   [namelist:diagnostics(_defaults_)]
   # set some default value for mip_name
   mip_name=undefined
   ...

   [namelist:diagnostics(surface_temp)]
   # set mip_name for this diagnostic
   mip_name=tas
   ...

The following modifiers can be appended to any token to handle case conversion:
 
* ``!l`` - convert the token value to lower case
* ``!u`` - convert the token value to upper case
* ``!t`` - convert the token value to title case

To obtain a *lowercase* version of the model_name attribute, for instance, one
would include the token ``{model_name!l}`` in the template string.

As exemplified above, it is possible to configure the filename template so that
output files are stored within a hierarchy of directories. This is achieved by
inserting a '/' character at the appropriate places in the template.

Note that the '/' character is specific to UNIX-like operating systems. Note also
that any missing subdirectories will be created as and when needed, assuming that
your user account has the appropriate filesystem privileges.

Integration With Climate Suites
===============================

The `Running the Application`_ section towards the end of this guide describes
the actual mechanics of invoking the ASoV Calculator app. The present section
provides some hints as regards how best to incorporate the app into a Rose/cylc
suite.

Although the ASoV Calculator app can be run independently within a terminal window,
it is envisaged that invoking it under the control of a Rose/cylc suite will be the
preferred mode of operation.

Lifetime of Model Data Files
----------------------------

An important point to bear in mind is that the ASoV Calculator processes
diagnostic data which it loads from a subset (typically) of the files output by
the climate model at a given cycle point. The particular subset of data files will
depend upon which output streams have been specified in the app config file.

As a consequence of this behaviour it is crucial that, during the execution of
the processing task, the input data files are *neither modified nor deleted by
any other suite task*. In particular, when working with PP files as the input
source, the postproc app must be configured such that the transform and archive
tasks occur either side of the asov_calculator task. In terms of a cylc
dependency graph this can be depicted schematically as follows:

.. code-block:: ini

   [scheduling]
      [[dependencies]]
         graph = postproc => asov_calculator:finish => pparchive

(Note: The actual postproc tasks might have different names in your suites)

The reasoning here is that we want the PP files to remain in situ on disk until
the asov_calculator task has completed. Otherwise, if the postproc tasks
were to run back-to-back, some (or all!) of the PP files would be deleted before
the asov_calculator task had a chance to process them.

There is also an assumption that the postproc tasks for successive cycle points
do not overlap in time (i.e. they execute sequentially). This is important because
otherwise the asov_calculator task would not know which PP files to load and process
at any given cycle point since files from multiple cycles would co-exist in the
suite share directory. Fortuitously, in most standard climate suites, the postproc
task is configured to execute in exactly this manner (though users should verify this). 

Runtime Performance Considerations
----------------------------------

To avoid repeatedly reading a given model data file multiple times (i.e. for multiple
target diagnostics), the ASoV Calculator app uses Iris's load functions to read
the data for *all* required diagnostics at the commencement of processing of each
data stream.

Loading data from large UM fieldsfiles or PP files is known to impose a substantial
drain on system resources. Similarly, the task of processing model diagnostics,
especially high-resolution fields on multiple levels, is a compute-intensive operation.
Taken together, this means that incorporating the ASoV Calculator app into a
climate suite may lead to a significant performance overhead. Attempting to process
a large number of diagnostics might, therefore, lead to exceeding system resource
limits. This will of course depend upon the target runtime platform and the system
load at any given moment. Experimentation may be necessary, therefore, in order to
determine appropriate resource limits.

Handling of Output Files
------------------------

As described in the previous section, the app writes netCDF files of histogram
data to the user-configured output directory. It is the responsibility of
the user or suite creator to configure any additional processing of the output
files that might be required. This might include, for example, copying or moving
the files to some other disk location, or archiving the files to the MASS data
storage system.

If no such additional processing is defined then the files will simply remain
on disk (at least until they get deleted by some or other housekeeping task).

Configuring the Application
===========================

The ASoV Calculator app is configured by specifying properties in a text file
based upon Rose's custom INI file format. This so-called 'app config file' may
be created and updated manually using your favourite text editor, or else by
using Rose's graphical editor tool (invoked by typing ``rose config-edit`` or,
if you're really pressed for time, ``rose edit``).

A sample app config file is included as part of the reference Rose suite named
`u-be543`_. Within that suite the app config file can be found at the path
``app/asov_calculator/rose-app.conf``. It contains all of the properties currently
recognised by the ASoV Calculator app, listed with their default values where
appropriate. Some of the less frequently used properties are hidden (from a Rose
point of view) by placing a '!' character at the front of the property or section
definition.

A brief description of each configuration property is provided below on a section
by section basis.

COMMAND EXECUTION
-----------------

Config file section: ``[command]``

Default Command
~~~~~~~~~~~~~~~

.. code-block:: ini

   default=rose env-cat rose-app-run.conf >rose-app-expanded.conf
          =$AFTERBURNER_HOME_DIR/bin/abrun.sh AsovCalculator -c rose-app-expanded.conf -v

This property defines the command that Rose will invoke in order to run the
ASoV Calculator application. As shown above, the default command makes use of
the ``rose env-cat`` command to expand any environment variables defined in the
runtime version of the app config file (i.e. ``rose-app-run.conf``). The resulting
file is then passed to Afterburner's ``abrun.sh`` script, which loads and executes
the Python-based application code.

Other than to append additional command-line options (as described below under
`Command-Line Options`_), the default command syntax should not normally need to be
modified.

If you're not using Rose to run the ASoV Calculator app then this property is
ignored.

.. note:: At the time of writing (October 2020), Afterburner's ``abrun.sh`` script
   loads a Python2.7-based version of SciTools. If you only plan to run the
   ASoV Calculator app under Python 3.x then it is recommended that you use the
   new ``apprun.sh`` :ref:`wrapper script <apprun.sh>` in the definition of the
   default command. It may be necessary to use that script with the ``--reset-pypath``
   option.

RUNTIME ENVIRONMENT
-------------------

Config file section: ``[env]``

The following environment variables may be defined in the app config file or else
under the appropriate section of either the ``rose-suite.conf`` file or the
``suite.rc`` file (assuming, that is, the ASoV Calculator app is being
executed under the control of a Rose/cylc suite).

Afterburner Home Directory
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   AFTERBURNER_HOME_DIR=/data/users/afterburner/software/turbofan/current

This environment variable is used to define the pathname of the directory within
which the Afterburner software is installed. If this variable is already set
within your runtime environment - e.g. within one of your shell start-up scripts -
then it's not essential to repeat it here (though it doesn't necessarily hurt to
do so). If you're not sure where the Afterburner software is installed at your
site, please contact your local system administrator.

SciTools Module
~~~~~~~~~~~~~~~

.. code-block:: ini

   SCITOOLS_MODULE=scitools/default-current

This environment variable may be used to specify the name of the SciTools module to
load immediately prior to invocation of the ASoV Calculator app. If it's not
defined then the default SciTools module gets loaded. To prevent loading of *any*
SciTools module this environment variable can be set to 'none'. This might be
desirable if the calling environment has already loaded the required module.

GENERAL OPTIONS
---------------

Config file section: ``[general]``

Abort On Error
~~~~~~~~~~~~~~

.. code-block:: ini

   abort_on_error=false

By default, a data processing error will result in the app catching an exception,
reporting (and logging) the associated error message, and skipping to the next
diagnostic, or the next stream, to be processed. Setting the ``abort_on_error``
option to true will cause the ASoV Calculator app to exit immediately.

.. note:: In the current implementation, being unable to find any model data
   for a given diagnostic is *not* considered an error; rather an informational
   message is emitted and processing skips forward to the next diagnostic. If it's
   desired by users, this behaviour could be modified in future versions of the app.   

Default Region Name
~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   default_region_name=global

The region name to use when no specific region has been defined.

Selection Of Output Files
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   update_cumulative_file=true
   update_timeseries_file=false
   save_cyclepoint_file=false

By default calculated histogram data is appended to a single netCDF file of
cumulative data, one file for each source diagnostic. If it's required to save
data to a file containing an expanding time-series of values then the
``update_timeseries_file`` option should be enabled (you might want to modify
the corresponding filename template too).

If the ``save_cyclepoint_file`` option is enabled then the histogram data generated
at each cycle point will be written to a file named according to the unique cycle
point identifier. It shouldn't typically be necessary to enable this option if the
time-series file is being written to.

Datetime Format
~~~~~~~~~~~~~~~

.. code-block:: ini

   datetime_format=%Y%m%d

The ``datetime_format`` option is used to specify the format of datetime strings
incorporated into the names of output files. At present, the filename tokens that
make use of the datetime format are ``{data_start_date}`` and ``{data_end_date}``.

The permitted format codes are as documented for Python's `datetime.strftime`_
function. The default format is ``%Y%m%d``, which yields, for example, a date
string of the form '19701201' for the date 1st Dec 1970.

DATA READER OPTIONS
-------------------

Config file section: ``[data_reader]``

This section is used to specify a number of options pertaining to how source
diagnostics get read from model data files on disk.

Type of Data Source
~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   [data_reader]
   source_type=[single_directory | data_cache]

The ``source_type`` option specifies the nature of the data source from which
model data files will be read. At present this can either be a single directory,
meaning that all data files are stored below that one location, or an
:mod:`Afterburner-style data cache <afterburner.io.datacaches>`,
meaning that data files are stored within a structured hierarchy of
directories based upon runid, stream id, and, where applicable, realization id.

In the case of a model simulation that is writing data files to a single output
directory then it is usual to select the ``single_directory`` option (in which
case the ``[data_cache]`` settings described later on can safely be ignored).

Input Directory
~~~~~~~~~~~~~~~

.. code-block:: ini

   input_dir=${DATAM}

The ``input_dir`` option defines the pathname of the sole directory containing
model data files (in the format specified below). The pathname may contain
environment variables; these are best enclosed within braces so as to avoid
potential ambiguity when the path is expanded.

This option only needs to be defined when the ``source_type`` option (see above)
is set to ``single_directory``. Otherwise, for cache-based data sources, the
``[data_cache]base_dir`` option should be specified.

Input File Format & Filename Template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   input_file_format=pp
   input_filename_template={runid}{dotstream}*.pp

The ``input_file_format`` option defines the format of the input model data.
Currently supported formats include UM PP ('pp', the default), UM fieldsfile ('ff'),
and netCDF ('nc').

The ``input_filename_template`` option specifies the template by which model data
files are identified when the app is run. The list of brace-delimited tokens
which can be used within a template are described under the `Filename Templates`_
section.

DATA CACHE OPTIONS
------------------

Config file section: ``[data_cache]``

Data cache options only need to be specified when the ``[data_reader]source_type``
option has been set to ``data_cache``.

.. code-block:: ini

   [data_cache]
   cache_scheme=StreamSplit
   base_dir=path-to-cache-base-dir
   datastore_id=
   read_only=true

The ``cache_scheme`` option is used to select one of the :mod:`data cache schemes <afterburner.io.datacaches>`
recognised by the Afterburner software package. A stream-based option should
be selected if model data files are stored in a directory hierarchy based upon
a runid/stream or runid/ensemble/stream layout. If model data files are stored
within a single directory then it is usually more straightforward to specify
this via the ``[data_reader]input_dir`` option (as described above), and ignore
the data cache settings.

The ``base_dir`` option is used to specify the path to the top-level (root) of
the data cache directory hierarchy.

Since the data cache is currently only used to read data from in-cache files the
``datastore_id`` option can be left blank, while the ``read_only`` option should
normally be left set to true (these two options are intended for future use in order
to enable data files to be put into the data cache by the ASoV Calculator app).

DATA WRITER OPTIONS
-------------------

Config file section: ``[data_writer]``

This section is used to specify a number of options pertaining to how and where
target diagnostics get written to disk.

Type of Data Target
~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   [data_writer]
   target_type=single_directory

At present output files can only be saved to a single directory (though refer to
the `Filename Templates`_ section for information on defining a filename template
which results in files being saved under a hierarchy of subdirectories below the
target output directory).

Output Directory Path
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   output_dir=${DATAM}/derived

This option specifies the absolute or relative path to the output directory
where netCDF files of calculated histogram data will get saved. If a relative path
is given then it will be relative to the current working directory from which
the app is invoked. In the case of a Rose/cylc suite this will usually be the
task work directory.

Output File Format & Filename Templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   output_file_format=nc
   per_cp_filename_template={stream_id}/{var_id}/{region_name}/{cycle_point}.nc
   all_cp_filename_template={stream_id}/{var_id}/{region_name}/cumulative.nc
   tseries_filename_template={stream_id}/{var_id}/{region_name}/timeseries.nc

The ``output_file_format`` option defines the format of the output data files.
Currently the only supported output format is netCDF.

The three filename template options permit specification of the templates used to
construct filenames for, respectively, individual cycle point data
(``per_cp_filename_template``), cumulative cycle point data (``all_cp_filename_template``),
and cumulative cycle point data as a full time-series (``tseries_filename_template``).

The list of brace-delimited tokens which can be used within a filename template
are described under the `Filename Templates`_ section.

Note: You should normally include a suitable file extension in each template,
e.g. ``.nc`` in the above examples.

NETCDF SAVE OPTIONS
-------------------

Config file section: ``[netcdf_saver]``

NetCDF Format
~~~~~~~~~~~~~

.. code-block:: ini

   netcdf_format=NETCDF4_CLASSIC

The ``netcdf_format`` option is used to specify the format or 'flavour' of netCDF
to use for output files. The default of NETCDF4_CLASSIC is chosen because it
enables data compression to be applied (if required) while maintaining compatibility
with the broadest range of third-party software tools.

This option should be set to 'NETCDF4' if you need to take advantage of the features
provided by the netCDF-4 enhanced data model.

File Overwriting & Appending
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   overwrite=false
   append=false

By default, the ASoV Calculator app will not overwrite existing output files.
However, this behaviour *only* applies when saving histogram data to per-cyclepoint
output files.

The cumulative and time-series files will, by virtue of their intended purpose,
always be appended to (or else created the first time around). Thus, the
``overwrite`` and ``append`` options are ignored in these cases.

Compression Options
~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   zlib=true
   complevel=2

Data compression is enabled by default at the specified compression level. You
may want to experiment with different compression settings. Note, however, that
compression levels above, say, 4 are prone to the law of diminishing returns:
it can take a disproportionate amount of time and CPU resource to achieve a small
amount of extra compression.

Additional NetCDF Options
~~~~~~~~~~~~~~~~~~~~~~~~~

The following options are less frequently needed, but are there if you need them.
Refer to the Iris `netcdf.save`_ function documentation for further details.

.. code-block:: ini

   shuffle=false
   fletcher32=false
   contiguous=false
   least_significant_digit=
   unlimited_dimensions=

PROCESSOR OPTIONS
-----------------

Config file section: ``[processor]``

This section is used to specify the processor class and associated options needed
to generate the required histogram data. At present, this section only contains a
single option - the full path to the Python class that implements the processing
logic.

Processor Class Path
~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   [processor]
   class_path=afterburner.processors.diags.HistogramMaker

The ``class_path`` option is used to define the full path to the Python class
that encapsulates the logic for calculating histogram data for a given diagnostic.
Although this option should not normally need to modified, in principle you
could set it to the path of your own custom Python class (and so long as that
class is accessible on Python's module search path when then app is run).

DIAGNOSTIC DEFINITIONS
----------------------

Config file section: ``[namelist:diagnostics]``

This section is used to define the one or more model diagnostics for which to
calculate histogram data. Default settings that apply to all model diagnostics
can conveniently be defined once under the 'virtual' diagnostic named ``_defaults_``.
Individual settings can then be overridden for specific diagnostics as required.

Enabling/Disabling Diagnostics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   [namelist:diagnostics(tas)]
   enabled=true
   ...

Ordinarily each diagnostic is enabled, meaning that it will get picked up and
processed by the ASoV Calculator app. Sometimes, however, it can be useful
to temporarily disable a diagnostic without having to actually delete it from
the app config file. The ``enabled`` option allows you to conveniently switch
diagnostics on and off.

Model Name, Suite Name & Ensemble Member
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   model_name=UM
   suite_name=u-ab123
   realization=

The ``model_name`` option identifies the climate model responsible for generating
the source diagnostics. It is used to find an associated model definition (in the
``models`` namelist) and to use as a token within filename templates.

The ``suite_name`` option is used to specify the name of the Rose suite that was
used to run the climate simulation.

For ensemble-based simulations the ``realization`` option should be used to specify
the realization identifier denoting the ensemble member, e.g. 'r1i2p3' (as used for
CMIPn-style experiments).

Stream Names
~~~~~~~~~~~~

.. code-block:: ini

   streams=apm,apy

The ``streams`` option is used to specify the default stream, or a list of streams,
for each of which histogram data is to be calculated and saved. This option may be
overridden for indicidual diagnostics so as to either exclude a particular stream
or include additional streams.

Diagnostic Variable Identifier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   [namelist:diagnostics(tas)]
   # defined by STASH code
   var_id=m01s00i024
   # defined by CF standard name
   var_id=surface_temperature

The ``var_id`` option is used to identify the source model diagnostic. It should
either be a STASH code or a CF standard name, as illustrated in the example above.
For processing UM model diagnostics it will usually be convenient to specify a
STASH code. For other climate models, notably those producing netCDF output files,
a standard name will normally be required.

Start & End Dates
~~~~~~~~~~~~~~~~~

When the app is configured to load model data from files output (by a climate
simulation) to a single directory, then the app can determine which files to load
for the current cycle point, typically by looking for the presence of 'sentinel
files' (``*.arch`` files in the case of the UM). This will normally be the
preferred mode of operation.

If, however, the model files are stored within an Afterburner-style :doc:`data cache </dev_guide/datacaches>`
then the app needs to be notified of the time period for which data should be loaded
for the current cycle point. This can be achieved by updating the diagnostic's
``start_date`` and ``end_date`` properties at each cycle point using suitable
environment variables -- START_DATE and END_DATE are used in the example below
but you can use alternative names if you like:

.. code-block:: ini

   [namelist:diagnostics(tas)]
   ...
   start_date=$START_DATE
   end_date=$END_DATE

These environment variables should be updated in the ``suite.rc`` file at each
invocation of the cylc task that runs the ASoV Calculator app. The task
definition shown below uses the ``cylc cyclepoint`` command to set the START_DATE
and END_DATE variables (for successive one-month time periods in this case) within
the cylc task's ``pre-script`` definition:

.. code-block:: ini

    [[asov_calculator]]
        pre-script = """
            export START_DATE=$(cylc cyclepoint --template=CCYY-MM-DD)
            export END_DATE=$(cylc cyclepoint --offset=P1M --template=CCYY-MM-DD)
            """
        ...

If you use this approach you'll want to modify the ``--template`` and ``--offset``
options (to the ``cylc cyclepoint`` command) to suit your particular diagnostic
processing needs.

LBPROC, LBTIM & Calendar Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   [namelist:diagnostics(tas)]
   ...
   lbproc=128
   lbtim=122
   calendar=360_day

The ``lbproc`` and ``lbtim`` options are used to disambiguate those UM diagnostics
which have the same STASH code but which can end up being serialised in the same
output file. A common use is to set the ``lbtim`` option so as to correctly select
the diagnostic at a particular sampling frequency, e.g. 3h, 6h, or 24h.

The ``calendar`` option is used to specify the calendar type associated with a
diagnostics. At present only the 360-day calendar is supported.

Bin Values (Lower Bounds)
~~~~~~~~~~~~~~~~~~~~~~~~~

This mandatory property is used to define the *lower bounds* of the (contiguous)
numerical ranges that will be used to 'bin' the input data. The value of this
property should either be a comma-separated list of bin values, or else a Python
expression that yields a list or numpy.ndarray of such values.

The upper bound of the final bin is set, internally, to the maximum value of the
corresponding data type, i.e. the maximum integer value or maximum float value.

The example below illustrates the use of a Python expression to yield a numpy array
that defines 100 bins for use with precipitation flux data.

.. code-block:: ini

   bin_values=np.concatenate([np.zeros(1),
             =np.exp(np.log(0.005) + np.sqrt(np.linspace(0,98,99) *
             =(np.square(np.log(120.0) - np.log(0.005)) / 59.0)))])

Note: If you need to include Numpy functions then, for app-specific reasons, you
must use the ``np.`` prefix (as above) rather than the ``numpy.`` prefix.

Region Extent and Name
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   region_extent=0,-23.5,360,23.5
   region_name=tropics

If a geographical region is defined then it used to extract data for that region
prior to calculating the histogram data. The extent of the region must be specified
via latitude and longitude values in the following order: min-long, min-lat,
max-long, max-lat. Note that the coordinates are interpreted as defining
*left-closed* intervals along the latitude and longitude axes.

The region name should be a suitable human-readable name for the region; it is
used in naming output files.

Target Units
~~~~~~~~~~~~

.. code-block:: ini

   target_units=kg m-2 day-1

This option makes it possible to convert the units of the source diagnostic to the
specified target units *prior* to binning the data. This might be desired, for
example, if the bins are more conveniently defined in the given target units.

The actual unit conversion is performed by Iris' ``cube.convert_units`` method,
which will raise an exception if the conversion cannot be completed for some
reason (e.g. the source and target units might be incompatible).

Reinitialisation Period
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   [namelist:diagnostics(precip)]
   ...
   reinit=30

If daily or instantaneous model data (e.g. from UM streams apa - apk) is being
loaded from files maintained within an Afterburner-style data cache, then it will
usually be necessary to specify the stream reinitialisation period (in days) via
the ``reinit`` option.

In the case of standard climate mean streams (apm, apy, etc) the app is usually
able to guess the reinitialisation period. It is possible, however, to override
the setting by specifying a negative value, e.g. -90 would enforce a 90-day
reinitialisation period regardless of stream name.

CLIMATE MODEL OPTIONS
---------------------

Config file section: ``[namelist:models]``

The ``models`` namelist is used to configure options that are specific to particular
climate models. At present this capability is limited to a couple of options pertinent
to the Unified Model, as described below.

Cylc Task Name
~~~~~~~~~~~~~~

.. code-block:: ini

   [namelist:models(um)]
   cylc_task_name=atmos_main
   ...

The ``cylc_task_name`` option is used to specify the name of the main task in the
Rose/cylc suite that is responsible for running a particular model code (the UM
in this example). The task name is used to obtain various task-related properties,
such as its work directory.

Sentinel File Extension
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   [namelist:models(um)]
   sentinel_file_ext=.arch
   ...

If the numerical model makes use of sentinel files to flag a subset of model
output files for some purpose, then the extension used for the sentinel files
should be defined here. Currently, the main practical application of this option
is to identify the sentinel files created by the UM postproc app as part of the
PP file transform and archive operations.

Setting this option to the empty string (or deleting it entirely) will disable
any associated functionality in the ASoV Calculator app.  

Running the Application
=======================

The ASoV Calculator app can be run either manually at the shell command
line or automatically under the control of a Rose suite. Both methods are described
in general terms in the :doc:`/invoking` chapter. The guidance in that chapter is
largely applicable to the current context. Some additional app-specific guidance is
included below.

Manual Invocation
-----------------

To run the app manually from the command line, type the following:

.. code-block:: bash

    % export AFTERBURNER_HOME_DIR=<path-to-afterburner-home-dir>
    % $AFTERBURNER_HOME_DIR/bin/abrun.sh AsovCalculator -c <config-file> [options]

An app config file, as described in the previous section, must be specified via
the ``-c`` (or ``--config-file``) option. Additional command-line options are
described below; often it is desirable to turn on the ``-v`` (or ``--verbose``)
option in order to see progress messages.

The initial ``export`` command above is not needed if the AFTERBURNER_HOME_DIR
shell variable is already defined in, for example, one of your shell start-up
scripts. Likewise, if the directory ``$AFTERBURNER_HOME_DIR/bin`` is included in
your command search path, then the second command can be shortened to plain ``abrun.sh``.

If you have checked out (or exported) a working copy of the `Afterburner code base
<https://code.metoffice.gov.uk/trac/afterburner/browser/turbofan/trunk>`_ then you
can, if preferred, set the AFTERBURNER_HOME_DIR variable to point to the directory
containing that working copy.

Invoking the ASoV Calculator app manually will of course only run it once.
Typically, however, you'll want to run the app at regular cycle points during
the execution of a Rose/cylc suite. This approach is described in the next section.

Invocation from a Rose/Cylc Suite
---------------------------------

Firstly, create a copy of the `u-be543`_ sample Rose suite (login required).

Next, modify the app config file for the ASoV Calculator application (i.e.
the file ``app/asov_calculator/rose-app.conf``), and also the ``suite.rc`` file,
to suit your particular data source locations and processing requirements.

At this point you can either run the suite in stand-alone mode, or you can copy
the ``app`` directory over to an existing Rose suite and run (or restart) it.
In the latter case it will be necessary to modify the suite's dependency graph
(in the ``suite.rc`` file) so that the ``asov_calculator`` task is invoked at
the desired cycle points. Please consult the relevant Rose and cylc documentation
-- or a knowledgeable colleague! -- for further guidance on how to do this.

.. note:: When the ASoV Calculator app is executed as part of a Rose/cylc suite,
   any output messages will normally be directed to Rose's standard log files
   (which can be viewed by running the Rose command ``rose suite-log``).

Command-Line Options
--------------------

Command-line options can be viewed by invoking the app with the ``-h`` (or ``--help``)
option, as shown below:

.. code-block:: bash

    % abrun.sh --help
    Usage: abrun.sh <app_name> [options] [arguments]

    % abrun.sh AsovCalculator --help
    usage: AsovCalculator [-h] [-V] [-D | -q | -v] [-c CONFIG_FILE]
                          [--abort-on-error] [-n, --dry-run]

    AsovCalculator: Analysing Scales of Variability (ASoV) Calculator

    optional arguments:
      -h, --help            show this help message and exit
      -V, --version         Show Afterburner version number and exit
      -D, --debug           Enable debug message mode
      -q, --quiet           Enable quiet message mode
      -v, --verbose         Enable verbose message mode
      -c CONFIG_FILE, --config-file CONFIG_FILE
                            Pathname of the app configuration file
      --abort-on-error      Abort processing if an error is encountered
      -n, --dry-run         Dry-run only: do not save results to output files

These options are fairly self-explanatory. Note, however, that the -D, -q and -v
options are mutually exclusive.


.. The links below are referenced elsewhere in this document.

.. _u-be543: https://code.metoffice.gov.uk/trac/roses-u/browser/b/e/5/4/3/trunk

.. _netcdf.save: https://scitools.org.uk/iris/docs/latest/iris/iris/fileformats/netcdf.html#iris.fileformats.netcdf.save

.. _datetime.strftime: https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
