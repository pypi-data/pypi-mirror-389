Tutorial #4: Querying the MASS Data Archive
===========================================

This tutorial describes the functionality within the Afterburner software package
for querying the data files, and associated metadata, held in the MASS data archive.
Separate tutorials describe :doc:`retrieving data <mass_read>` from, and
:doc:`writing data <mass_write>` to, the MASS archive.

.. tip:: Refer to :doc:`Tutorial #1 </tutorials/accessing_afterburner>` for information
   on how to configure your Python environment to access the afterburner Python
   package.

Getting Started
---------------

The Afterburner package contains two modules that provide a function-based API
to the MOOSE system (as represented by the various ``moo`` command-line utilities).
These two modules are called ``afterburner.io.moose`` and ``afterburner.io.moose2``.
The first module has been deprecated in favour of the second module; it is often
convenient, however, to import the latter module using the name ``moose``, like
this:

>>> import afterburner.io.moose2 as moose

Before querying the MOOSE interface and retrieving files, it is often desirable
for client programs to check that the MOOSE CLI is supported by the current runtime
environment. This can be done using the ``has_moose_support()`` function, as follows:

>>> import afterburner.io.moose2 as moose
>>> moose.has_moose_support()
True

Of course, if you are working within an interactive Python session then you will
usually know whether or not the MOOSE CLI is supported by the current platform.

Even if the MOOSE CLI is supported, this does not necessarily mean that all of its
services are currently available; some or all of them might be down as a result of
scheduled maintenance, for instance.

The ``check_moose_commands_enabled()`` function may be used to determine whether
or not one or more required MOOSE services (commands) are available. For the
purposes of this tutorial, we’ll be using the ``moo ls``, and ``moo mdls``
commands (or, *sensu stricto*, the API functions which wrap those commands). To
verify that these two commands are available we can issue the following API call:

>>> import afterburner.io.moose2 as moose
>>> moose.check_moose_commands_enabled(moose.MOOSE_LS|moose.MOOSE_MDLS)
True

For the remainder of this tutorial we’ll assume that the ``moose2`` module has
been imported as per the eamples above.

.. note:: Afterburner’s MOOSE API is not designed to be a complete interface to
   each and every MOOSE command. Rather it aims to provide a general-purpose
   interface to the more commonly used data retrieval and storage commands.

Querying MOOSE System Limits
----------------------------

The MOOSE interface is constrained by a number of system limits, such as the
maximum number of files that can be archived to, or restored from, MASS during
a single ``moo put`` or ``get`` command.

The various limits can be displayed within a shell terminal by running the
``moo si -v`` command, as shown below.

.. code-block:: sh

    % moo si -v
    Moose User: mary.luser
    Client: vld999; Revision: Rel_6.11.0
        Query-file size-limit (byte): 32768
        Default max. conversion-threads: 15
        Default max. transfer-threads: 3
    Controller: expmooseprd16.metoffice.gov.uk; Revision: Rel_6.11.0
        PUT commands enabled: true
        GET commands enabled: true
        SELECT commands enabled: true
        MDLS commands enabled: true
        Multiple-put file-number limit: 10000
        Multiple-put volume limit (MB): 5120000
        Multiple-get file-number limit: 10000
        Multiple-get volume limit (MB): 5120000
        Multiple-get tape-number limit: 50
        Cost of storing one Terabyte for one year (GBP): 12.0
    Storage: available; Revision: not reported

Alternatively, if you need to access the same information programmatically,
then you can use the ``get_moose_limits()`` function provided by the Afterburner
MOOSE API. This function returns a dictionary with keys matching the symbolic
constants defined for the various MOOSE system limits in the ``moose2`` module.

The code snippet below illustrates how you can determine the maximum number of
files that can be handled by a single MOOSE put or get request:

>>> limits = moose.get_moose_limits()
>>> limits[moose.MOOSE_GET_MAX_FILES]
10000
>>> limits[moose.MOOSE_PUT_MAX_FILES]
10000

Simple File Listings
--------------------

The general-purpose ``list_files()`` function can be used to obtain a list of the
files contained within any directory in MASS for which your account has appropriate
access permissions. The directory is identified by a full MOOSE URI, just as it
would be if you were to issue a ``moo ls`` command in a terminal window.

For example, here's how you could obtain a list of the files contained within a
(fictitious) PP data collection:

>>> files = moose.list_files('moose:/crum/u-xy123/apy.pp')
>>> files[0]
'xy123a.py19701201.pp'

And similarly for a netCDF data collection:

>>> files = moose.list_files('moose:/crum/u-xy123/ony.nc.file')
>>> files[0]
'xy123o_1y_19701201_19711130_grid_T.nc'

The order of the filenames in the returned list is not guaranteed, though it will
usually be the canonical sort order employed by the ``moo ls`` command. The ``sort``
argument can be used to sort the list of filenames either by file size or by
*modification* time, as shown below:

>>> files = moose.list_files('moose:/crum/u-xy123/apy.pp', sort='time')

.. note:: It is not currently possible to sort filenames according to their
   associated *model time*. The time-sorting option shown above is based upon
   file creation (or subsequent modification) time in MASS. Often the file
   creation time order mirrors model time order, but this is not always the case.

As we've just seen, the ``list_files()`` function lists the files for a specific
MOOSE URI. The ``list_struct_files()`` function offers an alternative, and somewhat
terser, way of obtaining similar results for a structured data collection. For
example, the previous query could be achieved as follows:

>>> files = moose.list_struct_files('u-xy123', 'apy.pp', sort='time')
>>> files[0]
'xy123a.py19701201.pp'

Although this function is nominally intended to be used for *structured* data
collections, it is possible to pass in arguments for an *unstructured* data
collection; the behaviour in this case, however, is not defined.

Running More Advanced Queries (PP Specific)
-------------------------------------------

The ``metadata_list_struct()`` function can be used to list files whose metadata
attributes match user-defined values. The function acts as a wrapper around the
``moo mdls`` command, which enables finer-grained queries (i.e. at the file atom
level) to be run against structured MASS data collections. For our purposes that
currently means just PP data collections.

At present, queries can be based upon some combination of filename, STASH code,
and time range. In the following example we want to obtain a list of all PP files
(MOOSE URIs actually) in a given collection that contain STASH diagnostic 24, i.e.
surface air temperature:

>>> uris = moose.metadata_list_struct('anqjm', 'apy.pp', stashcodes=['m01s00i024'])
>>> uris[0]
'moose:/crum/anqjm/apy.pp/anqjma.py19791201.pp'
>>> uris[-1]
'moose:/crum/anqjm/apy.pp/anqjma.py20781201.pp'

We can now constrain this query further by specifying a date-time range:

>>> uris = moose.metadata_list_struct('anqjm', 'apy.pp', stashcodes=['m01s00i024'],
...            time_range=('1999-12-01', '2019-12-01'))
>>> uris[0]
'moose:/crum/anqjm/apy.pp/anqjma.py19991201.pp'
>>> uris[-1]
'moose:/crum/anqjm/apy.pp/anqjma.py20191201.pp'

As before, the order in which filenames appear in the returned list will depend
upon the default sorting mechanism, if any, used by the ``moo mdls`` command.
However, the ``sort`` argument may be used to request that files are sorted
according to the values of a particular attribute. To sort by the start time of
each file, for instance, one would use the 'T1' attribute:

>>> uris = moose.metadata_list_struct('anqjm', 'apy.pp', stashcodes=['m01s00i024'],
...            time_range=('1999-12-01', '2019-12-01'), sort='T1')

The MOOSE documentation describes the PP file attributes (and custom attributes
such as 'T1') that can be used in mdls-based queries.

The ``metadata_list_struct()`` function automatically creates -- and later deletes --
the query file that needs to be passed to the ``moo mdls`` command. On occasions,
e.g. when things are not working as expected, it can be useful to retain the query
file on disk. The ``keep_query_file`` argument fulfils that purpose; it causes the
query file to be retained in the current working directory.

>>> uris = moose.metadata_list_struct('anqjm', 'apy.pp', stashcodes=['m01s00i024'],
...            keep_query_file=True)

The query file is named ``<tmp>_query.txt``, where ``<tmp>`` is some auto-generated
unique text string.

Running Generic Queries
-----------------------

All of the functions we've seen so far are convenience wrappers around the
general-purpose ``moose2.run_moose_command()`` function, which handles the work
of invoking the required MOOSE command-line utility in a subprocess, catching
any error conditions, and passing back any textual output to the calling program
(or your interactive Python session).

Consequently, you can use the ``run_moose_command()`` function to issue more or
less any MOOSE query that you like. For example, if you needed to list the files
in a MASS location by access time rather than modification time, and have the
results output in XML format, then here's how you could do that:

>>> cmd = 'moo ls --access-time --xml :crum/anqjm/apy.pp'
>>> result = moose.run_moose_command(cmd)
>>> # print the first 5 lines of the xml output
>>> print('\n'.join(result[:5]))
<?xml version="1.0"?>
<nodes>
<node
  url="moose:/crum/anqjm/apy.pp/anqjma.py19791201.pp">
</node>

If the command fails for some reason then an ``afterburner.exceptions.MooseCommandError``
exception is raised. You will typically want to catch and act upon any such errors.

Setting Command Options Via Environment Variables
-------------------------------------------------

Lastly, recent versions of the Afterburner package (v1.3.1b1 and later) enable
you to specify extra MOOSE command-line options via appropriately named environment
variables. In the case of the ``moo ls`` command, for example, the variable must
be named MOOSE_LS_OPTIONS. For the ``moo mdls`` command it is MOOSE_MDLS_OPTIONS.
And similarly for other MOOSE commands.

This mechanism allows you to specify command-line options that are not currently
supported directly via arguments to the various functions in the ``moose2`` module.
Naturally it is particularly handy for specifying new command options that post-date
the implementation of the aforementioned functions.

By way of an example, the ``moo mdls`` command was recently updated to support a
new option named ``--numberofatoms``. This option may be used to increase the
maximum number of file atoms that can be returned by the mdls command. Hence, if
you believe that a MOOSE query is likely to exceed the current limit (100,000
atoms at the time of writing), then you can temporarily raise the limit by
specifying the aforementioned option via the MOOSE_MDLS_OPTIONS environment
variable, as shown below:

.. code-block:: sh

    % export MOOSE_MDLS_OPTIONS="--numberofatoms=250000"

Usually you will only need to use this mechanism when the ``moo`` command in question
is being invoked by an Afterburner app or utility that makes use of the MOOSE API;
the Climate Model Monitor is one such app.

Wrap Up
-------

This tutorial has provided a brief tour of the Afterburner functions available for
listing and querying files in the MASS data archive. Further information regarding
the various query functions can be found in the API documentation for the
:mod:`moose2 module <afterburner.io.moose2>`.

The following MOOSE-related tutorials might also be of interest:

* :doc:`mass_read`
* :doc:`mass_write`

Back to the :doc:`Tutorial Index <index>`
