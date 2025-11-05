Working with Data Caches
========================

Data cache classes, and the associated data store classes, were introduced in the
:ref:`data-caches-and-data-stores` section of this guide. These classes are
provided as a means to set up and manage on-disk caches of model data files in a
consistent manner.

In order to analyse climate model data, most users (and project teams/groups too)
maintain collections of model data files in hierarchies of directories on disk.
The organisation of directories and files tends to follow a handful of common
layout patterns, often reflecting the way in which geophysical data is generated
and output by the source climate model(s)

A typical example would be a collection of UM PP files retrieved from the MASS
archive and laid down on disk in the familiar directory hierarchy based upon
suite name and output stream name, e.g.::

  mi-ab123/
    apy/
      ab123a.py1970.pp
      ab123a.py1971.pp
      ...
    apm/
      ab123a.pm1970dec.pp
      ab123a.pm1971jan.pp
      ...

Afterburner's data cache and data store classes are designed to facilitate
programmatic access to this and other popular variants of on-disk data caches.

Limitations
-----------

By design, Afterburner's implementation of data caching is a simple client-side
solution. It does not pretend to provide an enterprise-scale, multi-user solution:
that would be a significant software development endeavour.

Consequently, developers should be aware of the main limitations of the current
data caching solution, including:

* Data caches are designed primarily for owning-user access, though *read-only*
  access by multiple users should be okay.
* No automated data synchronisation takes place with back-end data stores. An
  on-request, 'client-pull'-style paradigm is assumed.
* Support is currently limited to the four data cache schemes described under the
  relevant classes in the :mod:`afterburner.io.datacaches` module
* All of the schemes assume that the back-end data stores (or their interfaces,
  such as MOOSE) are file-based. No support is provided, for example, to interact
  with relational database systems.
* For practical purposes, the current implementation closely reflects the file
  structure and organisation employed by the MASS data archive.

Core Concepts
-------------

The following core concepts come into play when working with data cache and data
store objects.

Base Directory
  Each on-disk data cache is rooted at some base directory. If the base directory
  does not exist when the cache object is initialised then, by default, it is
  created with read-write permissions for the owner, and read-only permissions
  for everyone else. If required, the cache base directory may be created in
  advance with more open (or more strict) permissions.

  Every cache base directory is identified as such by having a file created within it
  called 00README.TXT which details the cache type and it's date and time of creation.

Meta-Variables
  Meta-variable objects provide the mechanism for identifying which data should
  be fetched into the data cache (from the associated back-end data store), and
  which data should be loaded from the cache into main memory, as and when
  requested.

  For more information on meta-variable objects, refer to the various classes in
  the :mod:`afterburner.metavar` module.

Predictable Data File Contents
  A key principle observed by Afterburner data cache schemes is that file contents
  should be predictable and consistent across successive retrievals of the same
  user-requested data. By this we mean that the set of files placed in the cache
  for variable V, for a given time period T and (optional) metadata attributes,
  is identical to the same file set that would have been retrieved at any earlier
  or later time.

  An important side-effect of this policy is that retrieved files will often
  contain slightly more data than is strictly necessary to satisfy a given data
  request.

  This is best illustrated with an example. Say a client application requests
  files to be fetched into a VarSplit-style cache corresponding to a UM monthly
  mean precipitation variable for the time period 1960-12-01 to 1990-12-01. This
  request might result in the retrieval of some 360 data files from the back-end
  data store (MASS in this example). Those files might each contain a number of
  precipitation fields representing different meaning intervals (e.g. 1h, 6h, 24h).

  So even though the original data request only required the 1h data, the data
  caching code always makes sure to retrieve all the different 'flavours' of the
  requested variable. That way, if the original data files are deleted - whether
  manually or by an automated housekeeping process - a subsequent request for the
  same variable should result in the same files, with the exact same contents,
  appearing in the same directory location within the cache.

  .. note:: One caveat to this behaviour is when the source data is modified in the
     back-end data store. In this case two retrievals which straddle the modification
     timepoint will necessarily yield different results. Although this scenario
     is expected to be quite rare, users should nonetheless be aware of the
     possibility of its occurrence.

Selecting a Data Cache Scheme
-----------------------------

The key features of the currently supported data caching schemes are described
in the :mod:`afterburner.io.datacaches` module. The decision as to which scheme
to use will depend upon a number of factors. In the case where access is required
to an existing on-disk data cache then the decision is straightforward: you'll
choose the scheme which matches the layout of files in the cache.

In the case where you wish to set up and interact with a new data cache, then
you'll want to consider the relative performance trade-offs associated with the
expected total number of files, their typical size in the cache (which might differ
from their size in a back-end data store), likely data access patterns, and so on.

Unfortunately there is no ideal, one-size-fits-all data caching solution.
Rather, it's necessary to choose a data layout that best suits your particular
problem domain and anticipated data access patterns.

The tips below provide some hints regarding the selection of an appropriate cache
scheme. They are mainly focussed on MASS-based applications, since that is the
principal source of climate data at the time of writing.

Use a :class:`VarSplit <afterburner.io.datacaches.VarSplitDataCache>` data cache if...

* your client application is designed to work more efficiently with small subsets
  of a handful of model variables/diagnostics
* you want the ability to treat variables independently from one another, i.e.
  they should not be serialised in the same file (or set of files)
* files in the cache don't need to have long residency times and can thus be
  automatically deleted when they reach system-defined expiry limits

Use a :class:`StreamSplit <afterburner.io.datacaches.StreamSplitDataCache>` data cache if...

* your client application is designed to work more efficiently with large numbers
  of model variables/diagnostics serialised in fewer, larger files
* the performance hit of storing and scanning through large data files is not a
  major consideration
* you want the data cache to be accessible to legacy applications which rely
  upon the suite/stream directory layout scheme.

If source data for a data cache will be obtained from an ensemble of climate
simulations, then you will want to select the ensemble-aware variants of the
aforementioned cache schemes, namely the :class:`EnsembleVarSplit <afterburner.io.datacaches.EnsembleVarSplitDataCache>`
and :class:`EnsembleStreamSplit <afterburner.io.datacaches.EnsembleStreamSplitDataCache>`
schemes. Unfortunately the non-ensemble and ensemble-aware cache schemes are not
currently cross-compatible (this is due to the different ways that directories
and files are named and organised within an ensemble-style data cache).

If none of the existing schemes is sufficient for your needs then it may be necessary
to implement a new Afterburner data cache class, or else devise a bespoke solution
within your client application. Ask the Afterburner development team for advice!

Worked Examples
---------------

**StreamSplit Data Cache Usage**

First, let's create a couple of sample meta-variable objects representing
time-bound geophysical variables of interest::

    >>> from afterburner.metavar import UmMetaVariable
    >>> time_range = ('1998-12-01', '2008-12-01')
    >>> tas = UmMetaVariable('10.3', 'mi-ab123', stream_id='apm',
    ...     stash_code='m01s03i326', time_range=time_range)
    >>> precip = UmMetaVariable('10.3', 'mi-ab123', stream_id='apm',
    ...     stash_code='m01s05i216', time_range=time_range)

Next, we initialise a StreamSplit-type data cache object rooted at the base directory
``/users/mary/caches/stream_split``. In this example we use the ``create_cache``
factory method to initialise the data cache object::

    >>> from afterburner.io.datastores import MassDataStore
    >>> from afterburner.io.datacaches import DataCache, STREAM_SPLIT_SCHEME
    >>> base_dir = '/users/mary/caches/stream_split'
    >>> dstore = MassDataStore()
    >>> dcache = DataCache.create_cache(STREAM_SPLIT_SCHEME, dstore, base_dir)

Although desirable in many scenarios, it's not mandatory to specify a time range.
If a range is not defined then an attempt is made to apply a particular cache
operation (fetch, load, etc) to *all* possible target files, depending on context.

To get a list of paths of *actual* files present in the cache corresponding to the
``tas`` variable::

    >>> actual_files = dcache.get_filepaths([tas])

To get a list of paths of *expected* files corresponding to the ``precip`` variable.
Some or all of the files may actually be present in the cache::

    >>> xpectd_files = dcache.get_filepaths([precip], expected=True)

To fetch files for the tas variable into the data cache from the MASS archive.::

    >>> # default is to fetch files in gap-filling mode
    >>> dcache.fetch_files([tas])
    >>> # but existing files can be overwritten if desired
    >>> dcache.fetch_files([tas], overwrite=True)

Note that, in the case of a StreamSplit cache, *whole* stream files get retrieved.
This means that there is no need to run a separate fetch for precip data since
we'll get that data 'for free' as a result of fetching the tas data. Note, however,
that if the time range for the variables differed then it would be necessary to
issue separate fetch calls.


**VarSplit Data Cache Usage**

Here we initialise a VarSplit-type data cache object rooted at the base directory
``/users/mary/caches/var_split``. In this example the data cache object is
created by direct instantiation of the ``VarSplitDataCache`` class::

    >>> from afterburner.io.datastores import MassDataStore
    >>> from afterburner.io.datacaches import VarSplitDataCache
    >>> dstore = MassDataStore()
    >>> dcache = VarSplitDataCache(dstore, '/users/mary/caches/var_split')

Now fetch files for the tas and precip variables into the data cache. In the case of
a VarSplit cache, data for discrete variables is stored in separate files (same
filename but in different, per-variable directories - whence the scheme name)::

    >>> dcache.fetch_files([tas, precip])

To load data for the precip variable into an in Iris cubelist::

    >>> cubes = dcache.load_data([precip])

The above two operations - fetch and load - may be combined into one by including
the ``do_file_fetch`` argument in the latter method call::

    >>> cubes = dcache.load_data([precip], do_file_fetch=True, minimal_data=True)

The ``minimal_data`` option is also used here as a hint to the ``load_data()``
method to load the *smallest* set of data that matches the constraints specified
by the ``precip`` meta-variable object. For instance, if a UM meta-variable has its
``lbtim`` attribute set to 122, say, then only data for that time-meaning interval
(i.e. 1h) will be loaded.

An alternative to using the ``load_data()`` method involves obtaining the paths
of the relevant files in the data cache, and then passing these paths directly
to one of the Iris load functions, typically with one or more Iris constraints::

    >>> import iris
    >>> # data cache initialisation as above
    >>> paths = dcache.get_filepaths([tas])
    >>> cubes = iris.load(paths, constraints=...)

This approach requires a bit more effort on the part of client code, but provides
the ability to fine-tune the Iris data loading operation, should that be desired.

**Deleting Cache Files**

Data files associated with one or more variables can be deleted from a data cache
using the ``delete_files`` method::

    >>> dcache.delete_files([tas, precip])

For a VarSplit-type data cache this call would delete files (if present) from the
separate directories used to store the tas and precip variables.

.. warning:: Caution needs to be exercised in the case of StreamSplit and
   EnsembleStreamSplit data caches. In these cases the cached data files contain
   *multiple* variables. Issuing the following call, therefore, would end up
   deleting those data files which host not only the tas variable, but also any
   other variables which happen to be contained in them.

   >>> dcache.delete_files([tas])

If you are the owner of a data cache, you may of course delete files manually
(similarly you could place files in the cache manually, if you so desire).

Since it's a potentially dangerous operation, there is no specific function for
deleting an entire data cache. If required, you can do this manually from a shell
terminal. Alternatively you could perform the equivalent operation within client
code using the utility functions in Python's ``os`` and ``shutil`` modules.
