# (C) British Crown Copyright 2016-2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The datacaches module contains a collection of Python classes for managing
access to disk-based caches of model data files organised according to different
layout schemes.

The current implementations target disk-based caches of model data retrieved
from the MASS archive system operated by the Met Office. In future the class
hierarchy may be extended to interface with other data sources. Refer to module
:mod:`afterburner.io.datastores` for details of the currently supported
data stores that can be used as the back-end for data caches.

The data cache classes are not designed to implement automated file removal. It is
assumed that the file systems on which data caches are deployed (e.g. the scratch
file system on the SPICE platform) will be running some manner of scheduled file
deletion service.

**Index of Classes in this Module**

.. autosummary::
   :nosignatures:

   DataCache
   VarSplitDataCache
   StreamSplitDataCache
   EnsembleVarSplitDataCache
   EnsembleStreamSplitDataCache
   SingleDirectoryDataCache
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import add_metaclass

import os
import re
import abc
import fnmatch
import logging
import iris
from datetime import datetime

from afterburner.exceptions import DataCacheError, DataStoreError, MissingDataFilesError
from afterburner.filename_providers import FilenameProvider

#: Symbolic constant used to select the VarSplit data caching scheme.
VAR_SPLIT_SCHEME = 'VarSplit'

#: Symbolic constant used to select the EnsembleVarSplit data caching scheme.
ENSEMBLE_VAR_SPLIT_SCHEME = 'EnsembleVarSplit'

#: Symbolic constant used to select the StreamSplit data caching scheme.
STREAM_SPLIT_SCHEME = 'StreamSplit'

#: Symbolic constant used to select the EnsembleStreamSplit data caching scheme.
ENSEMBLE_STREAM_SPLIT_SCHEME = 'EnsembleStreamSplit'

#: Symbolic constant used to select the SingleDirectory data caching scheme.
SINGLE_DIRECTORY_SCHEME = 'SingleDirectory'

# List of supported data caching schemes.
DATA_CACHE_SCHEMES = (VAR_SPLIT_SCHEME, ENSEMBLE_VAR_SPLIT_SCHEME,
    STREAM_SPLIT_SCHEME, ENSEMBLE_STREAM_SPLIT_SCHEME, SINGLE_DIRECTORY_SCHEME)

# Metacharacters used for filename 'globing'.
GLOB_CHARS = r'[*?[]'

# Name of README file created in base directory to record cache details.
README_FILENAME = '00README.TXT'


@add_metaclass(abc.ABCMeta)
class DataCache(object):
    """
    Abstract base class for data cache managers. Concrete classes implement
    a particular caching scheme, a number of which are defined in this module.
    By using a data cache manager, client code does not need to have knowledge
    of the names of model data files, nor how they are laid out in a directory
    hierarchy.
    """

    def __init__(self, datastore, base_dir, file_mode=None, read_only=False,
            missing_data_action='error', **kwargs):
        """
        :param afterburner.io.datastores.DataStore datastore: A data store
            object which provides functionality for loading data files into
            a data cache.
        :param str base_dir: The pathname of the directory which forms the base,
            or root, of the data cache. For user-specific data caches this path
            will often be equivalent to the expansion of $SCRATCH/<scheme-name>.
        :param int file_mode: Mode to apply to any files added to the data cache.
            If not set then the mode of any cached files will be determined by
            the umask of the calling user.
        :param bool read_only: Access an existing data cache in read-only mode.
        :param str missing_data_action: The action to take if data is found to be
            missing from the cache, even after a file fetch operation has been
            requested. Currently supported values are: 'error', 'log' or 'ignore'.
        :raises OSError: Raised if the cache base directory could not be created.
        :raises afterburner.exceptions.DataCacheError: Raised if an error was
            encountered trying to initialise the data cache, e.g. attempting to
            create the base directory while in read-only mode.
        """
        self.datastore = datastore
        base_dir = os.path.expanduser(os.path.expandvars(base_dir))
        base_dir = os.path.abspath(base_dir)
        self.base_dir = base_dir

        self.file_mode = file_mode
        self.read_only = read_only
        self.missing_data_action = missing_data_action
        self.logger = logging.getLogger(__name__)

        if not os.path.exists(base_dir):
            if read_only:
                raise DataCacheError("Cannot create data cache base directory\n"
                    "because read-only access mode has been enabled.")
            else:
                os.makedirs(base_dir)

        self.readme_file = os.path.join(self.base_dir, README_FILENAME)
        if os.path.exists(self.readme_file):
            self._check_readme_file()
        else:
            if read_only:
                self.logger.warning("Cannot create data cache README file\n"
                    "because read-only access mode has been enabled.")
            else:
                self._create_readme_file()

    @staticmethod
    def create_cache(cache_scheme, datastore, base_dir, file_mode=None,
            read_only=False, missing_data_action='error', **kwargs):
        """
        Factory method for creating a data cache object based on the specified
        cache scheme. The data cache is rooted at the directory defined by
        ``base_dir``. This is purely a convenience function: if preferred, cache
        objects may be instantiated directly using the appropriate subclass
        defined within this module.

        :param str cache_scheme: The scheme used to organise directories and
            files within the data cache. This argument should be set using one
            of the symbolic constants defined at the top of this module.
        :param object datastore: Handle to an :class:`afterburner.io.datastores.DataStore`
            object from which data files can be fetched if necessary.
        :param str base_dir: The pathname of the directory which forms the base,
            or root, of the data cache. For user-specific data caches this path
            will often be equivalent to the expansion of $SCRATCH/<scheme-name>.
        :param int file_mode: Mode to apply to any files added to the data cache.
            If not set then the mode of any cached files will be determined by
            the umask of the calling user.
        :param bool read_only: Access an existing data cache in read-only mode.
        :param str missing_data_action: The action to take if data is found to be
            missing from the cache, even after a file fetch operation has been
            requested. Currently supported values are: 'error', 'log' or 'ignore'.
        :raises ValueError: Raised if the specified cache scheme is not recognised.
        :raises afterburner.exceptions.DataCacheError: Raised if an error was
            encountered trying to initialise the data cache, e.g. attempting to
            create the base directory while in read-only mode.
        """
        if cache_scheme not in DATA_CACHE_SCHEMES:
            raise ValueError("Unrecognised data cache scheme identifier: %s" % cache_scheme)
        else:
            klass = globals()[cache_scheme + 'DataCache']
            cache = klass(datastore, base_dir, file_mode=file_mode,
                read_only=read_only, missing_data_action=missing_data_action,
                **kwargs)
            return cache

    def get_cache_dir_for_variable(self, var):
        """
        Return the path, relative to the cache's base directory, of the subdirectory
        used to store data files associated with meta-variable ``var``.

        As well as being used internally by DataCache subclasses, this function is
        also designed to be passed as a callback function to remote objects which
        need to query a variable's cache directory path.

        :param object var: The meta-variable object whose *relative* cache directory
            is to be returned.
        """
        raise NotImplementedError()

    def load_data(self, varlist, constraints=None, callback=None,
            do_file_fetch=False, do_gap_check=False, minimal_data=False):
        """
        Load data corresponding to the variables defined in ``varlist`` and
        return the data in an Iris cubelist.

        This is a general-purpose convenience method, one which by default *may
        return a more extensive list of cubes than expected*. This is because the
        cached files passed to the iris.load function often contain data fields
        over and above those needed to satisfy the list of passed-in meta-variable
        objects.

        The ``minimal_data`` keyword argument can be used to signal that the
        load_data method should *attempt* to identify and return the smallest
        cubelist matching the specified meta-variables. Owing, however, to the
        sometimes arbitrary contents of model data files, plus the intentionally
        'fuzzy' nature of meta-variables, even the minimal dataset may not be
        strictly that. Consequently, client code should check, and if necessary
        filter, the desired data from the returned cubelist.

        If finer-grained control is needed over which cubes are loaded from which
        files, then this may be achieved by calling the :meth:`get_filepaths` method
        and passing the returned files to one of the Iris data load functions with
        appropriate constraints and/or callback functions.

        :param list varlist: A list of :class:`afterburner.metavar.MetaVariable`
            objects defining the variables for which data is to be loaded from the
            cache.
        :param constraints: Optional constraint, or list of constraints, to
            pass through to the ``iris.load`` function.
        :param callback: Optionally, the name of a callback function which will
            get called for each cube loaded from the underlying data files.
            Note: this argument is ignored if the ``minimal_data`` option is
            enabled.
        :param bool do_file_fetch: If enabled then file retrieval requests are
            submitted to the associated data store for each input variable.
        :param bool do_gap_check: If enabled then a check is performed, after
            any file retrievals (if turned on), to see if there are gaps in the
            collection of files on disk, compared with what's expected. This
            option only checks for missing files, not missing data within files.
        :param bool minimal_data: If enabled then this method attempts to return
            the minimal dataset as determined by the properties attached to the
            meta-variables passed in via ``varlist``. This option will likely be
            slower than the default behaviour, which is to load all of the data
            contained in the file set associated with the specified meta-variables.
        :returns: An Iris cubelist containing data for the variables defined in
            ``varlist``.
        :raises afterburner.exceptions.DataCacheError: Raised if the ``do_file_fetch``
            argument is enabled and the cache is being accessed in read-only mode.
        :raises afterburner.exceptions.DataStoreError: Raised if a problem is
            encountered retrieving data from the back-end data store.
        """
        # If requested, fetch data from the back-end data store before loading.
        if do_file_fetch:
            for var in varlist:
                try:
                    self.fetch_files([var])
                except DataStoreError:
                    self.logger.error("Problem trying to fetch data from %s.\n"
                        "Target variable: %s", self.datastore.name, str(var))
                    raise

        cubes = iris.cube.CubeList()
        missing_files = []

        # Load data for each meta-variable in turn, appending the resultant
        # cubes to the final cubelist.
        for var in varlist:
            actual_files = self.get_filepaths([var])

            # Gap checks can only be done for time-bound meta-variables.
            if do_gap_check and var.time_range:
                expected_files = set(self.get_filepaths([var], expected=True))
                missing = expected_files - set(actual_files)
                if missing: missing_files.extend(list(missing))

            if not actual_files: continue

            if minimal_data:
                # Attempt to load the minimal dataset for the current meta-variable.
                var_cubes = iris.load(actual_files,
                    constraints=var.make_id_constraint(),
                    callback=var.make_load_callback(id_only=None, do_time_check=True))
                # Apply any additional user-defined constraints.
                if constraints:
                    var_cubes = var_cubes.extract(constraints)

            else:
                # First load all cubes matching the current meta-variable.
                var_cubes = iris.load(actual_files,
                    constraints=var.make_id_constraint(), callback=callback)
                # Then apply any additional user-defined constraints.
                if constraints:
                    var_cubes = var_cubes.extract(constraints)

            if var_cubes: cubes.extend(var_cubes)

        # If requested, report any data gaps.
        if do_gap_check and missing_files:
            nmiss = len(missing_files)
            nshow = min(nmiss, 10)
            mshow = '\n'.join(missing_files[:nshow])
            msg = ("{0} expected files are missing from the data cache. First "
                   "{1} files are as follows:\n{2}".format(nmiss, nshow, mshow))
            if self.missing_data_action == 'error':
                self.logger.error(msg)
                raise MissingDataFilesError(msg)
            elif self.missing_data_action == 'log':
                self.logger.warning(msg)

        return cubes

    @abc.abstractmethod
    def fetch_files(self, varlist, overwrite=False, **kwargs):
        """
        Fetch files corresponding to ``varlist`` from the data store and add them
        to the data cache. By default, files are retrieved in gap-filling mode so
        that files already in the cache get used as-is. The overwrite option can
        be used to turn off gap-filling and enable file overwriting.

        :param list varlist: A list of :class:`afterburner.metavar.MetaVariable`
            objects defining the model variables for which data files are to be
            retrieved.
        :param bool overwrite: Set to true to force overwriting of existing
            files in the cache. Disables gap-filling mode.
        :raises afterburner.exceptions.DataCacheError: Raised if an attempt is
            made to add files to the data cache when accessed in read-only mode.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def fetch_stream(self, model_name, suite_id, stream_id, **kwargs):
        """
        Fetch all data files for the specified model, suite and stream. By default
        files are retrieved in gap-filling mode such that files already in the
        cache get used as-is. The overwrite option can be used to turn off
        gap-filling and enable file overwriting.

        .. warning:: Fetching a whole data stream will in many cases be a resource
           intensive operation. Wherever practicable therefore it is recommended
           that the :meth:`fetch_files` method is used to retrieve the smallest
           subset of a stream needed to perform the task in hand.

        :param str model_name: The acronym of the climate model associated with
            ``stream_id``, e.g. 'UM', 'NEMO'. Symbolic constants for recognised
            climate models are defined in the :mod:`afterburner.modelmeta`
            module.
        :param str suite_id: The id of the suite that produced the stream output.
            This should either be a Rose suite name (e.g. 'mi-ab123') or a UMUI
            runid (e.g. 'abcde').
        :param str stream_id: The stream identifer, e.g. 'apy', 'onm'.
        :param bool overwrite: Set to true to force overwriting of existing
            files in the cache. Disables gap-filling mode.
        """
        raise NotImplementedError()

    def iter_files(self, varlist, expected=False, sort=False):
        """
        Iterate over the list of actual or expected filepaths corresponding to
        the variables defined in ``varlist``.

        .. deprecated:: 1.2.0
           Use the :meth:`iter_filepaths` method instead.
        """
        for fpath in self.get_filepaths(varlist, expected=expected, sort=sort):
            yield fpath

    def iter_filepaths(self, varlist, expected=False):
        """
        Iterate over the set of actual or expected filepaths corresponding to
        the variables defined in ``varlist``. While the variables are processed
        in the order in which they appear in the list, client code should not
        assume that the set of paths generated for a given variable are in any
        particular order (though typically they will be in ASCII sort order).

        Note that, if more than one variable object is passed in, then the set
        of returned filepaths might not be unique. If uniqueness is required
        then the :meth:`get_filepaths` method should be used (with the proviso
        that that method returns a list object).

        :param list varlist: A list of :class:`afterburner.metavar.MetaVariable`
            objects defining the variables for which file paths are to be returned.
            In order to correctly identify the relevant file names, each of the
            meta-variables must have their time range attribute defined.
        :param bool expected: By default only the paths of actual files in the
            data cache are returned. Set this argument to true to return the
            full list of expected files for the requested variables.
        :returns: A sequence of absolute paths of actual or expected files in the
            data cache.
        """
        actual = not expected

        for var in varlist:
            # Get an iterator over the expected filenames for the current variable.
            fn_provider = FilenameProvider.from_metavar(var)
            it = fn_provider.iter_filenames(var)

            # If actual files were requested, but the pertinent cache directory
            # does not exist, skip to the next variable.
            vardir = os.path.join(self.base_dir, self.get_cache_dir_for_variable(var))
            vardir = os.path.normpath(vardir)
            if actual and not os.path.isdir(vardir): continue

            # If only the actual files on disk are required then include a test
            # for the existence of a given file in the target cache directory.
            if actual:
                actual_files = os.listdir(vardir)
                for fname in it:
                    if re.search(GLOB_CHARS, fname):
                        # filename contains wildcard character(s)
                        for fn in fnmatch.filter(actual_files, fname):
                            yield os.path.join(vardir, fn)
                    elif fname in actual_files:
                        # plain filename
                        yield os.path.join(vardir, fname)

            # Yield the names of all expected files.
            else:
                for fname in it:
                    yield os.path.join(vardir, fname)

    def get_filepaths(self, varlist, expected=False, sort=False):
        """
        Return a list of the actual or expected filepaths corresponding to the
        variables defined in ``varlist``. In theory, the returned paths should
        not contain any duplicates.

        Note that if time range metadata is omitted from any of the meta-variable
        objects passed in via ``varlist``, then the filenames generated for those
        meta-variables will contain wildcard characters - typically '*' - in place
        of the time elements in the name. The particular wildcard characters used,
        and their position in a filename, will depend on the meta-variable type.
        It is the responsibility of calling code to handle such filenames in a
        context-dependent manner.

        :param list varlist: A list of :class:`afterburner.metavar.MetaVariable`
            objects defining the variables for which file paths are to be returned.
            In order to correctly identify the relevant file names, each of the
            meta-variables must have their time range attribute defined.
        :param bool expected: By default only the paths of actual files in the
            data cache are returned. Set this argument to true to return the
            full list of expected files for the requested variables.
        :param bool sort: Specifies whether or not to ASCII-sort the list of
            returned file names. For large lists this might be an expensive operation.
        :returns: A list of absolute paths of actual or expected files in the
            data cache.
        """
        filenames = set()

        for var in varlist:
            for fpath in self.iter_filepaths([var], expected=expected):
                filenames.add(fpath)

        if sort:
            return sorted(filenames)
        else:
            return list(filenames)

    def delete_files(self, varlist):
        """
        Delete files from the data cache corresponding to the variables defined
        in ``varlist``.

        .. warning:: If a data cache implementation stores multiple variables
           within each file then this method can have the potential side effect
           of deleting files which contain variables not specified via ``varlist``.

        :param list varlist: A list of :class:`afterburner.metavar.MetaVariable`
            objects defining the variables whose associated files are to be deleted.
        :raises afterburner.exceptions.DataCacheError: Raised if an attempt is
            made to delete files in read-only mode.
        """
        if self.read_only:
            raise DataCacheError("Attempt to delete data cache files in read-only mode.")

        for fpath in self.get_filepaths(varlist):
            if os.path.isfile(fpath):
                try:
                    os.remove(fpath)
                except OSError:
                    self.logger.warning("Unable to delete file: %s", fpath)

    def _check_readme_file(self):
        """
        Check that the cache type encoded in the README file matches the type
        of the data cache object being initialised. If the file checks out fine
        then the method returns True. Otherwise a DataCacheError is raised.
        """
        cls_cache_type = self.__class__.__name__
        dsk_cache_type = 'unknown'

        try:
            lines = [l[:-1] for l in open(self.readme_file).readlines()]
            for line in lines:
                if line.startswith('Cache-Type:'):
                    dsk_cache_type = line.split(':')[-1].strip()
                    break
        except IOError:
            msg = "Unable to determine data cache type from file: " + self.readme_file
            raise DataCacheError(msg)

        if dsk_cache_type != cls_cache_type:
            msg = ("Data cache type mismatch: unable to access an existing {0}-style"
                   "\ndata cache using the {1}-style data cache interface.".format(
                   dsk_cache_type, cls_cache_type))
            raise DataCacheError(msg)

        return True

    def _create_readme_file(self):
        """Create a README text file in the cache's base directory."""
        now = datetime.utcnow().replace(microsecond=0)
        timestr = now.strftime('%H:%M:%SZ')
        datestr = now.strftime('%d %b, %Y')
        text = [
            "Cache-Type: {0}\n\n".format(self.__class__.__name__),
            "This data cache directory was created by the Afterburner package\n",
            "at {0} on {1}.\n\n".format(timestr, datestr),
            "Unless you are the owner of the directory containing this README\n",
            "file you should NOT delete any of its contents without permission.\n",
        ]
        with open(self.readme_file, 'w') as fh:
            fh.writelines(text)

        if self.file_mode:
            try:
                os.chmod(self.readme_file, self.file_mode)
            except OSError:
                self.logger.warning("Unable to set access mode for README file: %s",
                    self.readme_file)

    def _check_writeable(self):
        """
        Check that the data cache is writeable. If not raise a DataCacheError
        exception.
        """
        if self.read_only:
            raise DataCacheError("Attempt to update/modify a disk-based data "
                "cache accessed in read-only mode.")
        return True


class VarSplitDataCache(DataCache):
    """
    Manage access to a data cache organised according to the VarSplit scheme.
    This scheme splits data into a directory hierarchy based on suite-id,
    stream-id and variable/diagnostic name. Filenames are the same as used in
    MASS. However, the cached version of a file only contains data for a single
    UM diagnostic or netCDF variable, albeit on all vertical levels and for all
    combinations of LBPROC and LBTIM (or the equivalent attributes for those
    models, such as NEMO, which generate model output in netCDF format).

    The VarSplit scheme is designed to achieve an optimum balance between the
    total number of files in any leaf directory, and the size of those files.
    The use of per-variable directories keeps the total number of files in any
    one directory to a manageable level, and also ensures that no one file is
    excessively large.

    File paths in this scheme are uniquely constructed as follows::

      <base_dir>/<suite-id>/<stream-id>/<variable-id>/<file-name>

    Example VarSplit directory and file layout for a user called mary::

      scratch/
        mary/
          var_split_cache/    <-- cache base directory
            mi-ab123/
              apy/
                m01s00i024/
                  abcdea.py1970.pp
                  abcdea.py1971.pp
                  ...
                m01s03i236/
                  abcdea.py1970.pp
                  abcdea.py1971.pp
                  ...
              apm/
                m01s00i024/
                  abcdea.pm1970jan.pp
                  abcdea.pm1970feb.pp
                  ...
                m01s03i236/
                  abcdea.pm1970jan.pp
                  abcdea.pm1970feb.pp
                  ...
              ony/
                sosstsst/
                  abcdeo_1y_19691201_19701130_grid_T.nc
                  abcdeo_1y_19701201_19711130_grid_T.nc
                  ...
    """

    def __init__(self, datastore, base_dir, file_mode=None, read_only=False,
            missing_data_action='error', **kwargs):
        """
        :param afterburner.io.datastores.DataStore datastore: A data store
            object which provides functionality for loading data files into
            the data cache.
        :param str base_dir: The pathname of the directory which forms the base,
            or root, of the data cache. For user-specific data caches this path
            will often be equivalent to the expansion of $SCRATCH/<scheme-name>.
        :param int file_mode: Mode to apply to any files added to the data cache.
            If not set then the mode of any cached files will be determined by
            the umask of the calling user.
        :param bool read_only: Access an existing data cache in read-only mode.
        :param str missing_data_action: The action to take if data is found to be
            missing from the cache, even after a file fetch operation has been
            requested. Currently supported values are: 'error', 'log' or 'ignore'.
        :raises OSError: Raised if the cache base directory could not be created.
        """
        super(VarSplitDataCache, self).__init__(datastore, base_dir,
            file_mode=file_mode, read_only=read_only,
            missing_data_action=missing_data_action, **kwargs)

    def get_cache_dir_for_variable(self, var):
        """
        Return the path, relative to the cache's base directory, of the subdirectory
        used to store data files associated with meta-variable ``var``.

        As well as being used internally by DataCache subclasses, this function is
        also designed to be passed as a callback function to remote objects which
        need to query a variable's cache directory path.

        :param object var: The meta-variable object whose *relative* cache directory
            is to be returned.
        """
        for name in ['suite_id', 'stream_id']:
            if not getattr(var, name, None):
                raise AttributeError("Attribute '{0}' is not defined for "
                    "meta-variable: {1}".format(name, var))

        return os.path.join(var.suite_id, var.stream_id, var.slug)

    def fetch_files(self, varlist, overwrite=False, **kwargs):
        """
        Fetch files from the data store corresponding to ``varlist`` and add them
        to the data cache. By default, files are retrieved in gap-filling mode so
        that files already in the cache get used as-is. The overwrite option can
        be used to turn off gap-filling and enable file overwriting.

        :param list varlist: A list of :class:`afterburner.metavar.MetaVariable`
            objects defining the model variables for which data files are to be
            retrieved.
        :param bool overwrite: Set to true to force overwriting of existing
            files in the cache. Disables gap-filling mode.
        """
        self._check_writeable()
        try:
            self.logger.info("Fetching files for %d variables from %s...",
                len(varlist), self.datastore.name)

            # Delegate retrieval of files to the associated data store object.
            self.datastore.fetch_files_by_variable(varlist, overwrite=overwrite,
                dest_dir=self.base_dir, callback=self.get_cache_dir_for_variable,
                file_mode=self.file_mode)

        except DataStoreError as exc:
            self.logger.error(str(exc))
            raise

    def fetch_stream(self, model_name, suite_id, stream_id, **kwargs):
        """This operation is not yet supported for VarSplit-based data caches."""
        raise NotImplementedError("fetch_stream operation not yet supported.")


# The following class could be subclassed from VarSplitDataCache. For now it has
# been left as a direct subclass of DataCache in case it requires custom behaviour.
class EnsembleVarSplitDataCache(DataCache):
    """
    An ensemble-based variant of the :class:`VarSplit <VarSplitDataCache>` data
    cache scheme.

    File paths in this scheme are uniquely constructed as follows::

      <base_dir>/<suite-id>/<realization_id>/<stream-id>/<variable-id>/<file-name>

    If the ``null_realization_dir`` initialisation argument is specified then a
    data cache based on this scheme can also be used to store non-ensemble data
    alongside ensemble data.

    Example EnsembleVarSplit directory and file layout for a user called mary::

      scratch/
        mary/
          ens_var_split_cache/    <-- cache base directory
            mi-ab123/
              r1i1p1/             <-- ensemble member 1
                apy/
                  m01s00i024/
                    abcdea.py1970.pp
                    abcdea.py1971.pp
                    ...
                  m01s03i236/
                    ...
                apm/
                  m01s00i024/
                    ...
                  m01s03i236/
                    ...
                ony/
                  sosstsst/
                    ...
              r2i1p1/             <-- ensemble member 2
                apy/
                  ...
    """

    def __init__(self, datastore, base_dir, file_mode=None, read_only=False,
            missing_data_action='error', **kwargs):
        """
        :param afterburner.io.datastores.DataStore datastore: A data store
            object which provides functionality for loading data files into
            the data cache.
        :param str base_dir: The pathname of the directory which forms the base,
            or root, of the data cache. For user-specific data caches this path
            will often be equivalent to the expansion of $SCRATCH/<scheme-name>.
        :param int file_mode: Mode to apply to any files added to the data cache.
            If not set then the mode of any cached files will be determined by
            the umask of the calling user.
        :param bool read_only: Access an existing data cache in read-only mode.
        :param str missing_data_action: The action to take if data is found to be
            missing from the cache, even after a file fetch operation has been
            requested. Currently supported values are: 'error', 'log' or 'ignore'.

        Extra Keyword Arguments (`**kwargs`):

        :param str null_realization_dir: Name of the cache directory (e.g. 'r0')
            under which to store data files associated with variables for which
            no realization id is defined. By default this argument is undefined,
            in which case an attempt to cache non-ensemble data will result in an
            exception being raised (an AttributeError in the case of this class).

        :raises OSError: Raised if the cache base directory could not be created.
        """
        super(EnsembleVarSplitDataCache, self).__init__(datastore, base_dir,
            file_mode=file_mode, read_only=read_only,
            missing_data_action=missing_data_action, **kwargs)
        self.null_realization_dir = kwargs.get('null_realization_dir', '')

    def get_cache_dir_for_variable(self, var):
        """
        Return the path, relative to the cache's base directory, of the subdirectory
        used to store data files associated with meta-variable ``var``.

        As well as being used internally by DataCache subclasses, this function is
        also designed to be passed as a callback function to remote objects which
        need to query a variable's cache directory path.

        :param object var: The meta-variable object whose *relative* cache directory
            is to be returned.
        """
        realization_id = var.realization_id or self.null_realization_dir
        if not realization_id:
            raise AttributeError("Realization ID is not defined for "
                "meta-variable: {0}".format(var))

        for name in ['suite_id', 'stream_id']:
            if not getattr(var, name, None):
                raise AttributeError("Attribute '{0}' is not defined for "
                    "meta-variable: {1}".format(name, var))

        return os.path.join(var.suite_id, realization_id, var.stream_id, var.slug)

    def fetch_files(self, varlist, overwrite=False, **kwargs):
        """
        Fetch files from the data store corresponding to ``varlist`` and add them
        to the data cache. By default, files are retrieved in gap-filling mode so
        that files already in the cache get used as-is. The overwrite option can
        be used to turn off gap-filling and enable file overwriting.

        :param list varlist: A list of :class:`afterburner.metavar.MetaVariable`
            objects defining the model variables for which data files are to be
            retrieved.
        :param bool overwrite: Set to true to force overwriting of existing
            files in the cache. Disables gap-filling mode.
        """
        self._check_writeable()
        try:
            self.logger.info("Fetching files for %d variables from %s...",
                len(varlist), self.datastore.name)

            # Delegate retrieval of files to the associated data store object.
            self.datastore.fetch_files_by_variable(varlist, overwrite=overwrite,
                dest_dir=self.base_dir, callback=self.get_cache_dir_for_variable,
                file_mode=self.file_mode)

        except DataStoreError as exc:
            self.logger.error(str(exc))
            raise

    def fetch_stream(self, model_name, suite_id, stream_id, **kwargs):
        """This operation is not yet supported for EnsembleVarSplit-based data caches."""
        raise NotImplementedError("fetch_stream operation not yet supported.")


class StreamSplitDataCache(DataCache):
    """
    Manage access to a data cache organised according to the StreamSplit scheme.
    This scheme splits data into a simple directory hierarchy based on suite-id
    and stream-id, mirroring the similar layout employed by the MASS data archive.

    The cached version of each data file contains *all* model diagnostics/variables
    associated with a particular stream. Although it would be feasible to store
    a subset of diagnostics/variables in each file, doing so would mean that
    successive read operations could not guarantee that the file contents had not
    changed since the last file retrieval operation.

    The StreamSplit scheme has the advantage of a shallower directory hierarchy
    and fewer data files compared, say, to the VarSplit caching scheme. Those
    data files will, however, be much larger in size. This scheme is likely to be
    of overall benefit, therefore, in those cases where a large proportion of the
    model diagnostics/variables need to be accessed on a regular basis.

    File paths in this scheme are uniquely constructed as follows::

      <base_dir>/<suite-id>/<stream-id>/<file-name>

    Example StreamSplit directory and file layout for a user called mary::

      scratch/
        mary/
          stream_split_cache/    <-- cache base directory
            mi-ab123/
              apy/
                abcdea.py1970.pp
                abcdea.py1971.pp
                ...
              apm/
                abcdea.pm1970jan.pp
                abcdea.pm1970feb.pp
                ...
              ony/
                abcdeo_1y_19691201_19701130_grid_T.nc
                abcdeo_1y_19701201_19711130_grid_T.nc
                ...
    """

    def __init__(self, datastore, base_dir, file_mode=None, read_only=False,
            missing_data_action='error', **kwargs):
        """
        :param afterburner.io.datastores.DataStore datastore: A data store
            object which provides functionality for loading data files into
            the data cache.
        :param str base_dir: The pathname of the directory which forms the base,
            or root, of the data cache. For user-specific data caches this path
            will often be equivalent to the expansion of $SCRATCH/<scheme-name>.
        :param int file_mode: Mode to apply to any files added to the data cache.
            If not set then the mode of any cached files will be determined by
            the umask of the calling user.
        :param bool read_only: Access an existing data cache in read-only mode.
        :param str missing_data_action: The action to take if data is found to be
            missing from the cache, even after a file fetch operation has been
            requested. Currently supported values are: 'error', 'log' or 'ignore'.
        :raises OSError: Raised if the cache base directory could not be created.
        """
        super(StreamSplitDataCache, self).__init__(datastore, base_dir,
            file_mode=file_mode, read_only=read_only,
            missing_data_action=missing_data_action, **kwargs)

    def get_cache_dir_for_variable(self, var):
        """
        Return the path, relative to the cache's base directory, of the subdirectory
        used to store data files associated with meta-variable ``var``.

        As well as being used internally by DataCache subclasses, this function is
        also designed to be passed as a callback function to remote objects which
        need to query a variable's cache directory path.

        :param object var: The meta-variable object whose *relative* cache directory
            is to be returned.
        """
        # Check that the required attributes are defined on the meta-variable.
        for name in ['suite_id', 'stream_id']:
            if not getattr(var, name, None):
                raise AttributeError("Attribute '{0}' is not defined for "
                    "meta-variable: {1}".format(name, var))

        return os.path.join(var.suite_id, var.stream_id)

    def fetch_files(self, varlist, overwrite=False, **kwargs):
        """
        Fetch files for the run/stream combinations in ``varlist`` and add them
        to the data cache. By default, files are retrieved in gap-filling mode so
        that files already in the cache get used as-is. The overwrite option can
        be used to turn off gap-filling and enable file overwriting.

        :param list varlist: A list of :class:`afterburner.metavar.MetaVariable`
            objects defining the model variables for which data files are to be
            retrieved.
        :param bool overwrite: Set to true to force overwriting of existing
            files in the cache. Disables gap-filling mode.
        """
        self._check_writeable()
        try:
            self.logger.info("Fetching whole stream files for %d variables from %s...",
                len(varlist), self.datastore.name)

            # Delegate retrieval of files to the associated data store object.
            self.datastore.fetch_streams_by_variable(varlist, overwrite=overwrite,
                dest_dir=self.base_dir, callback=self.get_cache_dir_for_variable,
                file_mode=self.file_mode, **kwargs)

        except DataStoreError as exc:
            self.logger.error(str(exc))
            raise

    def fetch_stream(self, model_name, suite_id, stream_id, overwrite=False,
            **kwargs):
        """
        Fetch all data files for the specified model, suite and stream. By default
        files are retrieved in gap-filling mode such that files already in the
        cache get used as-is. The overwrite option can be used to turn off
        gap-filling and enable file overwriting.

        This is a convenience method for retrieving an **entire** data stream.
        The equivalent functionality can be achieved by constructing a single
        meta-variable object with the appropriate attributes, and then passing
        that object to the :meth:`fetch_files` method.

        :param str model_name: The acronym of the climate model associated with
            ``stream_id``, e.g. 'UM', 'NEMO'. Symbolic constants for recognised
            climate models are defined in the :mod:`afterburner.modelmeta`
            module.
        :param str suite_id: The id of the suite that produced the stream output.
            This should either be a Rose suite name (e.g. 'mi-ab123') or a UMUI
            runid (e.g. 'abcde').
        :param str stream_id: The stream identifer, e.g. 'apy', 'onm'.
        :param bool overwrite: Set to true to force overwriting of existing
            files in the cache. Disables gap-filling mode.
        """
        self._check_writeable()
        try:
            self.logger.info("Fetching all data files for suite %s, stream %s...",
                suite_id, stream_id)

            # Delegate retrieval of files to the associated data store object.
            dest_dir = os.path.join(self.base_dir, suite_id, stream_id)
            if not os.path.exists(dest_dir): os.makedirs(dest_dir)
            self.datastore.fetch_stream(model_name, suite_id, stream_id,
                overwrite=overwrite, dest_dir=dest_dir, file_mode=self.file_mode)

        except DataStoreError as exc:
            self.logger.error(str(exc))
            raise


# The following class could be subclassed from StreamSplitDataCache. For now it has
# been left as a direct subclass of DataCache in case it requires custom behaviour.
class EnsembleStreamSplitDataCache(DataCache):
    """
    An ensemble-based variant of the :class:`StreamSplit <StreamSplitDataCache>`
    data cache scheme.

    File paths in this scheme are uniquely constructed as follows::

      <base_dir>/<suite-id>/<realization-id>/<stream-id>/<file-name>

    If the ``null_realization_dir`` initialisation argument is specified then a
    data cache based on this scheme can also be used to store non-ensemble data
    alongside ensemble data.

    Example EnsembleStreamSplit directory and file layout for a user called mary::

      scratch/
        mary/
          ens_stream_split_cache/    <-- cache base directory
            mi-ab123/
              r1i1p1/                <-- ensemble member 1
                apy/
                  abcdea.py1970.pp
                  abcdea.py1971.pp
                  ...
                apm/
                  abcdea.pm1970jan.pp
                  abcdea.pm1970feb.pp
                  ...
                ony/
                  abcdeo_1y_19691201_19701130_grid_T.nc
                  abcdeo_1y_19701201_19711130_grid_T.nc
                  ...
              r2i1p1/                <-- ensemble member 2
                apy/
                  ...
    """

    def __init__(self, datastore, base_dir, file_mode=None, read_only=False,
            missing_data_action='error', **kwargs):
        """
        :param afterburner.io.datastores.DataStore datastore: A data store
            object which provides functionality for loading data files into
            the data cache.
        :param str base_dir: The pathname of the directory which forms the base,
            or root, of the data cache. For user-specific data caches this path
            will often be equivalent to the expansion of $SCRATCH/<scheme-name>.
        :param int file_mode: Mode to apply to any files added to the data cache.
            If not set then the mode of any cached files will be determined by
            the umask of the calling user.
        :param bool read_only: Access an existing data cache in read-only mode.
        :param str missing_data_action: The action to take if data is found to be
            missing from the cache, even after a file fetch operation has been
            requested. Currently supported values are: 'error', 'log' or 'ignore'.

        Extra Keyword Arguments (`**kwargs`):

        :param str null_realization_dir: Name of the cache directory (e.g. 'r0')
            under which to store data files associated with variables for which
            no realization id is defined. By default this argument is undefined,
            in which case an attempt to cache non-ensemble data will result in an
            exception being raised (an AttributeError in the case of this class).

        :raises OSError: Raised if the cache base directory could not be created.
        """
        super(EnsembleStreamSplitDataCache, self).__init__(datastore, base_dir,
            file_mode=file_mode, read_only=read_only,
            missing_data_action=missing_data_action, **kwargs)
        self.null_realization_dir = kwargs.get('null_realization_dir', '')

    def get_cache_dir_for_variable(self, var):
        """
        Return the path, relative to the cache's base directory, of the subdirectory
        used to store data files associated with meta-variable ``var``.

        As well as being used internally by DataCache subclasses, this function is
        also designed to be passed as a callback function to remote objects which
        need to query a variable's cache directory path.

        :param object var: The meta-variable object whose *relative* cache directory
            is to be returned.
        """
        realization_id = var.realization_id or self.null_realization_dir
        if not realization_id:
            raise AttributeError("Realization ID is not defined for "
                "meta-variable: {0}".format(var))

        # Check that the required attributes are defined on the meta-variable.
        for name in ['suite_id', 'stream_id']:
            if not getattr(var, name, None):
                raise AttributeError("Attribute '{0}' is not defined for "
                    "meta-variable: {1}".format(name, var))

        return os.path.join(var.suite_id, realization_id, var.stream_id)

    def fetch_files(self, varlist, overwrite=False, **kwargs):
        """
        Fetch files for the run/stream combinations in ``varlist`` and add them
        to the data cache. By default, files are retrieved in gap-filling mode so
        that files already in the cache get used as-is. The overwrite option can
        be used to turn off gap-filling and enable file overwriting.

        :param list varlist: A list of :class:`afterburner.metavar.MetaVariable`
            objects defining the model variables for which data files are to be
            retrieved.
        :param bool overwrite: Set to true to force overwriting of existing
            files in the cache. Disables gap-filling mode.
        """
        self._check_writeable()
        try:
            self.logger.info("Fetching whole stream files for %d variables from %s...",
                len(varlist), self.datastore.name)

            # Delegate retrieval of files to the associated data store object.
            self.datastore.fetch_streams_by_variable(varlist, overwrite=overwrite,
                dest_dir=self.base_dir, callback=self.get_cache_dir_for_variable,
                file_mode=self.file_mode, **kwargs)

        except DataStoreError as exc:
            self.logger.error(str(exc))
            raise

    def fetch_stream(self, model_name, suite_id, stream_id, realization_id=None,
            overwrite=False, **kwargs):
        """
        Fetch all data files for the specified model, suite and stream. By default
        files are retrieved in gap-filling mode such that files already in the
        cache get used as-is. The overwrite option can be used to turn off
        gap-filling and enable file overwriting.

        This is a convenience method for retrieving an **entire** data stream.
        The equivalent functionality can be achieved by constructing a single
        meta-variable object with the appropriate attributes, and then passing
        that object to the :meth:`fetch_files` method.

        :param str model_name: The acronym of the climate model associated with
            ``stream_id``, e.g. 'UM', 'NEMO'. Symbolic constants for recognised
            climate models are defined in the :mod:`afterburner.modelmeta`
            module.
        :param str suite_id: The id of the suite that produced the stream output.
            This should either be a Rose suite name (e.g. 'mi-ab123') or a UMUI
            runid (e.g. 'abcde').
        :param str stream_id: The stream identifer, e.g. 'apy', 'onm'.
        :param str realization_id: The realization identifer, e.g. 'r1i2p3'.
        :param bool overwrite: Set to true to force overwriting of existing
            files in the cache. Disables gap-filling mode.
        """
        self._check_writeable()
        try:
            self.logger.info("Fetching all data files for suite %s, stream %s...",
                suite_id, stream_id)

            # Delegate retrieval of files to the associated data store object.
            dest_dir = os.path.join(self.base_dir, suite_id, realization_id,
                stream_id)
            if not os.path.exists(dest_dir): os.makedirs(dest_dir)
            self.datastore.fetch_stream(model_name, suite_id, stream_id,
                realization_id=realization_id, overwrite=overwrite,
                dest_dir=dest_dir, file_mode=self.file_mode)

        except DataStoreError as exc:
            self.logger.error(str(exc))
            raise


class SingleDirectoryDataCache(DataCache):
    """
    Manage access to a data cache organised according to the SingleDirectory scheme.

    This simple data cache class manages access to files in a single directory,
    this being the base directory specified at initialisation time. One intended
    use-case for this class is to specify the main output directory of a climate
    simulation as the source of a data cache. Typically such a cache would be set
    up in *read-only* mode, since it wouldn't normally be desirable to write to
    the cache directory while the simulation is running (though this isn't
    necessarily precluded).

    .. note:: Since all files within the cache reside in the same single directory
       it is essential that any operations which insert new files into the data
       cache ensure that the names of the files are unique. If not then overwriting
       of existing files/data may result.
    """

    def __init__(self, datastore, base_dir, file_mode=None, read_only=False,
            missing_data_action='error', **kwargs):
        """
        :param afterburner.io.datastores.DataStore datastore: A data store
            object which provides functionality for loading data files into
            the single directory associated with the data cache.
        :param str base_dir: The pathname of the directory which forms the base,
            or root, of the data cache.
        :param int file_mode: Mode to apply to any files added to the data cache.
            If not set then the mode of any cached files will be determined by
            the umask of the calling user.
        :param bool read_only: Access an existing data cache in read-only mode.
        :param str missing_data_action: The action to take if data is found to be
            missing from the cache, even after a file fetch operation has been
            requested. Currently supported values are: 'error', 'log' or 'ignore'.
        :raises OSError: Raised if the cache base directory could not be created.
        """
        super(SingleDirectoryDataCache, self).__init__(datastore, base_dir,
            file_mode=file_mode, read_only=read_only,
            missing_data_action=missing_data_action, **kwargs)

    def get_cache_dir_for_variable(self, var):
        """
        Return the path, relative to the cache's base directory, of the subdirectory
        used to store data files associated with meta-variable ``var``.

        In the case of the SingleDirectory caching scheme (and as the name suggests)
        this function always returns the directory name ``'.'``, which in effect
        means the cache's base directory. Note, however, that the ``'.'`` element
        is normalised away in any file paths returned by the :meth:`iter_filepaths`
        or :meth:`get_filepaths` methods.

        :param object var: The meta-variable object whose *relative* cache directory
            is to be returned.
        :returns: Always returns the directory name ``'.'``.
        """
        return '.'

    def fetch_files(self, varlist, overwrite=False, **kwargs):
        """
        Fetch files from the data store corresponding to ``varlist`` and add them
        to the data cache. By default, files are retrieved in gap-filling mode so
        that files already in the cache get used as-is. The overwrite option can
        be used to turn off gap-filling and enable file overwriting.

        :param list varlist: A list of :class:`afterburner.metavar.MetaVariable`
            objects defining the model variables for which data files are to be
            retrieved.
        :param bool overwrite: Set to true to force overwriting of existing
            files in the cache. Disables gap-filling mode.
        """
        self._check_writeable()
        try:
            self.logger.info("Fetching files for %d variables from %s...",
                len(varlist), self.datastore.name)

            # Delegate retrieval of files to the associated data store object.
            self.datastore.fetch_files_by_variable(varlist, overwrite=overwrite,
                dest_dir=self.base_dir, callback=self.get_cache_dir_for_variable,
                file_mode=self.file_mode)

        except DataStoreError as exc:
            self.logger.error(str(exc))
            raise

    def fetch_stream(self, model_name, suite_id, stream_id, realization_id=None,
            overwrite=False, **kwargs):
        """
        Fetch all data files for the specified model, suite and stream. By default
        files are retrieved in gap-filling mode such that files already in the
        cache get used as-is. The overwrite option can be used to turn off
        gap-filling and enable file overwriting.

        This is a convenience method for retrieving an **entire** data stream.
        The equivalent functionality can be achieved by constructing a single
        meta-variable object with the appropriate attributes, and then passing
        that object to the :meth:`fetch_files` method.

        :param str model_name: The acronym of the climate model associated with
            ``stream_id``, e.g. 'UM', 'NEMO'. Symbolic constants for recognised
            climate models are defined in the :mod:`afterburner.modelmeta`
            module.
        :param str suite_id: The id of the suite that produced the stream output.
            This should either be a Rose suite name (e.g. 'mi-ab123') or a UMUI
            runid (e.g. 'abcde').
        :param str stream_id: The stream identifer, e.g. 'apy', 'onm'.
        :param str realization_id: An optional realization identifer, e.g. 'r1i2p3'.
        :param bool overwrite: Set to true to force overwriting of existing
            files in the cache. Disables gap-filling mode.
        """
        self._check_writeable()
        try:
            self.logger.info("Fetching all data files for suite %s, stream %s...",
                suite_id, stream_id)

            # Delegate retrieval of files to the associated data store object.
            self.datastore.fetch_stream(model_name, suite_id, stream_id,
                realization_id=realization_id, overwrite=overwrite,
                dest_dir=self.base_dir, file_mode=self.file_mode)

        except DataStoreError as exc:
            self.logger.error(str(exc))
            raise
