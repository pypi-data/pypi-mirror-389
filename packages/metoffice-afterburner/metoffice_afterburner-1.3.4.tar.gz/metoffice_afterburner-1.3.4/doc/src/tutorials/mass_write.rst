Tutorial #6: Copying Files to the MASS Data Archive
===================================================

In :doc:`Tutorial #5 <mass_read>` we saw how Afterburner’s application programming
interface (API) to the MOOSE system could be used to retrieve model data in UM PP
or netCDF format from the MASS data archive. The current tutorial takes a brief
look at the functions for putting model data into the MASS archive.

It should be noted that the Afterburner MOOSE API is not designed to be used to
carry out bulk uploads of large volumes of data to MASS. For that task it is
better to use the MOOSE command-line utilities directly (alternatively, the
:doc:`MASS Data Robot </rose_apps/mass_data_robot/guide>` app provides the
capability to configure and run multiple concurrent data retrieval jobs).

Tutorial #5 introduced a couple of helper functions which can be used to verify
that i) the MOOSE service is accessible from the current runtime environment, and
ii) that a required service is available (PUT operations for the purposes of this
tutorial). The following code snippet recaps the relevant functions::

    >>> import afterburner.io.moose2 as moose
    >>> moose.has_moose_support()
    True
    >>> moose.check_moose_commands_enabled(moose.MOOSE_PUT)
    True

.. tip:: You can hop over to the API documentation for the :mod:`afterburner.io.moose2`
   module any time you need to check out the description and calling signature for a
   particular function.

Basic Usage
-----------

The ``put_files()`` function is the basic function for copying a set of files to
a specific location within MASS. Here’s the signature of that function::

    put_files(src_dir, files, moose_uri, overwrite=False, overwrite_if_different=False)

The ``src_dir`` argument specifies the pathname of the directory within which all
of the data files to be archived are located. The ``files`` argument defines the
list of filenames to archive, while ``moose_uri`` specifies the location in MASS
in which to put the files. The code snippet below shows a toy example::

    >>> import afterburner.io.moose2 as moose
    >>> src_dir = '/home/mary/modeldata'
    >>> files = ['xy123a.pm1979djan.pp', 'xy123a.pm1979feb.pp']
    >>> moose_uri = 'moose:/crum/mi-xy123/apm.pp'
    >>> try: 
    >>>     moose.put_files(src_dir, files, moose_uri)
    >>> except afterburner.exceptions.DataStoreError:
    >>>     handle_error()   # insert your own exception-handling code

The ``put_files()`` function constructs and executes the appropriate ``moo put``
command. If the command completes successfully then the function exits silently.
Otherwise an exception is raised which you will usually wish to catch and act upon,
as illustrated (very simplistically!) above. Afterburner might raise one of a
small number of exceptions following the pattern ``afterburner.exceptions.Moose*``,
e.g. ``afterburner.exceptions.MooseCommandError``. The API documentation notes
the exceptions that can be raised by different functions. Afterburner’s MOOSE-related
exceptions all inherit from the exception class named ``afterburner.exceptions.DataStoreError``
so this can conveniently be used (as shown above) to catch a variety of error
conditions, the specifics of which are not of immediate interest to the calling
program.

The ``put_files()`` function assumes that the specified files are of the correct
type and/or format for the given destination within MASS, e.g. UM PP files in the
case of a PP data collection, netCDF files for a netCDF collection, and so on.

By default, attempts to overwrite existing files in MASS will result in an exception
being raised. This behaviour can be modified via the ``overwrite`` or ``overwrite_if_different``
keyword arguments which are supported by the ``put_files`` function. The first
keyword, when set to True, will result in any existing files being overwritten;
the second keyword will cause to be overwritten only those files whose size and
checksum differ from the files being archived. These keyword arguments are
equivalent to the ``moo put -f`` and ``moo put -F`` command options, respectively::

    >>> try:
    >>>     # overwrite existing files...but only if they are different
    >>>     moose.put_files(src_dir, files, moose_uri, overwrite_if_different=True)
    >>> except afterburner.exceptions.DataStoreError:
    >>>     handle_error()

The ``put_struct_files()`` function is a slight variant on the ``put_files()``
function. Instead of passing in a fully-formed MOOSE URI, in this case you specify
the MOOSE data class, data set, and data collection via separate arguments. These
are then stitched together to construct the destination URI. For convenience, the
data class defaults to ‘crum’. Here’s the function signature::

    put_struct_files(src_dir, files, data_set, collection, data_class='crum',
        overwrite=False, overwrite_if_different=False)

Depending on the nature of your interactive session or calling program, you may
find this function’s signature more convenient to use; the behaviour of the two
functions is otherwise identical. (NB: Despite the function name, it is possible
to specify the function arguments such that they reference a directory within an
*unstructured* data class. This usage is not recommended however.)

Handling MOOSE System Limits
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
MOOSE API.

The ``put_files()`` and ``put_struct_files()`` functions that we visited earlier
in this tutorial do not include any capability to handle the MOOSE system limits.
If you run a MOOSE command that exceeds one or other limit then the called function
will generally throw an exception, usually either ``afterburner.exceptions.MooseLimitExceededError``
or ``afterburner.exceptions.MooseCommandError``.

The ``put()`` function, on the other hand, is a convenience wrapper around the
``put_files()`` function. It attempts to decompose the passed-in MOOSE request
into a series of smaller MOOSE requests each of which is (hopefully) smaller than
the associated MOOSE limits, e.g. total number of files and total volume of data
in the case of a ``moo get`` request.

Although there are likely to be some pathological edge cases where a MOOSE command
cannot be decomposed reliably in this way, the ``put()`` function probably
represents the go-to function for copying data to MASS using Afterburner’s MOOSE API.

That wraps up this brief tour of the functions provided by Afterburner for
archiving files to the MASS data archive. Full details of all the functions, plus
their various arguments and options, can be found in the API documentation for the
:mod:`moose2 module <afterburner.io.moose2>`

Back to the :doc:`Tutorial Index <index>`
