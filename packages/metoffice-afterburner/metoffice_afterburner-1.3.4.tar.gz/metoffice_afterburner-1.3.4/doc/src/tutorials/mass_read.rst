Tutorial #5: Retrieving Files from the MASS Data Archive
========================================================

This tutorial describes the functionality within the Afterburner software package
for retrieving model data files from the MASS data archive. A :doc:`separate tutorial <mass_write>`
describes archiving model data to the MASS archive. Note that Afterburner’s MOOSE
API is not designed to be a complete interface to each and every MOOSE command.
Rather it aims to provide a general-purpose interface to the more frequently used
data retrieval and storage commands and options.

.. tip:: Refer to :doc:`Tutorial #1 </tutorials/accessing_afterburner>` for information
   on how to configure your Python environment to access the afterburner Python
   package.

Getting Started
---------------

The Afterburner package contains two modules which provide a function-based API
to the MOOSE command-line interface (as represented by the various ``moo`` utilities).
These two modules are called ``afterburner.io.moose`` and ``afterburner.io.moose2``.
The first module has been deprecated in favour of the second module; it is often
convenient, however, to import the latter module using the name ``moose``, e.g.
like this::

    >>> import afterburner.io.moose2 as moose

Before querying the MOOSE interface and retrieving files, it is often desirable
for client programs to check that the MOOSE CLI is supported by the current runtime
environment. This can be done using the ``has_moose_support()`` function, as follows::

    >>> import afterburner.io.moose2 as moose
    >>> moose.has_moose_support()
    True

Of course, if you are working within an interactive Python session then you will
usually know whether or not the MOOSE CLI is supported by the current platform.

Even if the MOOSE CLI is supported, this does not necessarily mean that all of its
services are currently available; some or all of them might be down as a result of,
for instance, a planned outage.

The ``check_moose_commands_enabled()`` function may be used to determine whether
or not one or more required MOOSE services (commands) are available. For the
purposes of this tutorial, we’ll be using the ``get``, ``select`` and ``filter``
commands (or, *sensu stricto*, the API functions which wrap those commands). To
verify that all of these commands are available we can issue the following API call::

    >>> import afterburner.io.moose2 as moose
    >>> moose.check_moose_commands_enabled(moose.MOOSE_GET|
    ...     moose.MOOSE_SELECT|moose.MOOSE_FILTER)
    True

For the remainder of this tutorial we’ll assume that you have imported the ``moose2``
module, as above.

Retrieving PP Files
-------------------

If the MOOSE URI and the list of UM PP files to fetch are known in advance then
perhaps the easiest way to retrieve the files is to use the high-level ``get()``
function::

    >>> dest_dir = '/my/local/data/space'
    >>> moose_uri = 'moose:/crum/mi-xy123/apy.pp'      # URI for a PP collection
    >>> filenames = moose.list_files(moose_uri, ...)   # Could be supplied by calling program/user
    >>> try:
    >>>     # note: this function call blocks until the moo command finishes (or fails)
    >>>     moose.get(dest_dir, moose_uri, files=filenames)
    >>> except afterburner.exceptions.DataStoreError:
    >>>     handle_error()

If the `files` argument is omitted then **ALL** files in the specified data collection
will be retrieved. Typically you will NOT wish to do this, at least not for large data
collections! The files will be restored to the directory defined by ``dest_dir``.

If you need to subset the restored files by STASH code(s) and/or time range, then this
can be achieved via the ``get_pp()``` function. For example, here's how you could request
that the restored files only contain data for two particular STASH codes (assume that
the other arguments are as defined above)::

    >>> try:
    >>>     # note: this function call blocks until the moo command finishes (or fails)
    >>>     moose.get_pp(dest_dir, moose_uri, files=filenames, stashcodes=['m01s00i023', 'm01s00i024'])
    >>> except afterburner.exceptions.DataStoreError:
    >>>     handle_error()

To retrieve data for a particular time range you should define the `time_range`
argument. This must be a tuple, or list, consisting of (start-date, end-date),
where the dates are strings conforming to the ISO 8601 standard, e.g. ‘1980-07-31’
(date only) or ‘1980-07-31T12:30’ (date and time). If the time component is omitted
then 'T00:00:00' is used as the default. The time range represents a *left-closed
interval*, i.e. start <= T < end, where T is the actual time instant for
instantaneous model data, or the *start* of the aggregation period for time-meaned
model data.

So, extending the previous example, we could fetch 10 years worth of data, as shown
below. Since we are specifying a time range it isn't necessary to also define a list
of files: for most (all?) PP data collections the time range will naturally constraint
the set of files that encompass the requested time period::

    >>> try:
    >>>     moose.get_pp(dest_dir, moose_uri, stashcodes=['m01s00i023', 'm01s00i024'],
    ...         time_range=('1979-12-01', '1989-12-01'))
    >>> except afterburner.exceptions.DataStoreError:
    >>>     handle_error()

Note: It is the responsibility of the user, or the calling program, to ensure that
the start and end dates are appropriate for the calendar type (360-day, for example)
associated with the data collection.

The ``get()`` and ``get_pp()`` functions shown above are convenience wrappers
around the ``retrieve_files()`` function. They accept the same keyword arguments
as the latter but have the added capability that they attempt to decompose a MOOSE
data retrieval request into multiple chunks, with each chunk sized to (hopefully)
avoid exceeding one or other of the various MOOSE system limits, such as maximum
number of files or total file size.

If the ``retrieve_files()`` function is used to submit a large data retrieval
request then, because it does not apply chunking, it is quite possible that one
of more of the MOOSE limits will be exceeded, in which case the request will fail.
On the other hand, even though the same request might succeed -- eventually! --
using one of the ``get*()`` functions, it should be borne in mind that Afterburner's
MOOSE API is neither intended nor designed to manage very large data retrievals
from MASS. (The :doc:`MASS Data Robot </rose_apps/mass_data_robot/guide>`
app represents one potentially better solution for such situations; there may well
be others.)

A couple of useful keyword arguments supported by the aforementioned functions
are ``overwrite`` and ``fill_gaps``. The overwrite option should be enabled if
you wish to overwrite any existing files (otherwise the command will fail).
Alternatively, the gap-filling option can be used to retrieve *only* those files
that do not already exist in the destination directory. If ``fill_gaps`` is
enabled then the ``overwrite`` option is silently ignored (since there should be
no conflicts).

Note: In some of the code snippets above we saw comments to the effect that the
moo command will block the running (parent) process until it had completed, or
failed. At present all of the functions in Afterburner's MOOSE API are *blocking
functions*. If required, client programs should spawn a separate process to
execute a MOOSE function if it is desirable to avoid blocking the parent process.
For information, the MASS Data Robot app executes MOOSE requests via multiple
child processes, thus circumventing this particular issue.

Retrieving netCDF Files
-----------------------

The approach to retrieving netCDF files from MASS is similar to that described
above for UM PP files. The high-level ``get()`` and ``get_nc()`` wrapper functions
cover the basic use-cases (and have the added benefit of chunking up large MOOSE
requests as and when needed). The low-level ``retrieve_nc_files()`` function
provides access to the full range of currently-supported retrieval options.

As with PP files, if the MOOSE URI and the list of netCDF files to fetch are known
in advance then the basic ``get()`` function is the simplest option, as illustrated
below::

    >>> dest_dir = '/my/local/data/space'
    >>> moose_uri = 'moose:/crum/mi-xy123/ony.nc.file'   # URI for a netCDF data collection
    >>> filenames = moose.list_files(moose_uri, ...)     # Could be supplied by calling program/user
    >>> try:
    >>>     moose.get(dest_dir, moose_uri, files=filenames)
    >>> except afterburner.exceptions.DataStoreError:
    >>>     handle_error()

In the same way that the ``get_pp()`` function supports the specification of a
particular list of STASH codes to retrieve, the ``get_nc()`` function allows you
to specify a list of netCDF variable names via the ``var_names`` keyword. In the
example below we request a couple of ocean variables::

    >>> try:
    >>>     moose.get_nc(dest_dir, moose_uri, files=filenames, var_names=['sosstsst', 'votemper'])
    >>> except afterburner.exceptions.DataStoreError:
    >>>     handle_error()

Unlike the ``get_pp()`` function, however, the ``get_nc()`` function does not
support the ``time_range`` keyword. This is because, at present, netCDF data
collections in MASS do not have sufficient associated record-level time metadata.

The ``retrieve_nc_files()`` function is to netCDF files what ``retrieve_files()``
is to PP files. If the ``var_names`` keyword is defined, as shown above, then the
request is handled by the ``moo filter`` command; otherwise it is handled by
``moo get``. The usage of the ``overwrite`` and ``fill_gaps`` keyword arguments
is as described under the `Retrieving PP Files`_ section above.

If any of the aforementioned functions are used to retrieve a specified list of
files, and one or more of those files is missing, then the ``moo get`` command will,
by default, throw an error. If desired, such errors can be ignored by setting the
``ignore_missing`` keyword to True. This option is ignored in the case of ``moo filter``
operations (as these don’t currently support the ``--get-if-available`` command
option).

That concludes this whistle-stop tour of some of the Afterburner functions for
retrieving PP and netCDF files from the MASS data archive. Full details of all
the functions, plus their various arguments and options, can be found in the
:mod:`moose2 module documentation <afterburner.io.moose2>`.

:doc:`Tutorial #6 <mass_write>` describes the functions available for archiving
files to MASS.

Back to the :doc:`Tutorial Index <index>`
