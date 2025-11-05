# (C) British Crown Copyright 2016-2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The datastores module contains classes which implement a simple, high-level
interface to selected file-based climate model data stores. At present support
is limited to the MASS data archive.

The main application for data store objects in the current Afterburner system
is to act as read-only data sources for disk-based data caches of climate model
output files. Refer to the :mod:`afterburner.io.datacaches` module for details
of the currently supported data caching schemes.

**Index of Classes in this Module**

.. autosummary::
   :nosignatures:

   DataStore
   MassDataStore
   NullDataStore
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import add_metaclass

import os
import abc
import logging
import tempfile
import datetime
import time

from afterburner.modelmeta import (MODEL_UM, MODEL_NEMO, MODEL_CICE, KNOWN_MODELS,
    mass_collection_from_stream)
from afterburner.exceptions import MooseUnavailableError, UnknownModelNameError
from afterburner.io import moose2 as moose
from afterburner.metavar import UmMetaVariable, NemoMetaVariable, CiceMetaVariable
from afterburner.filename_providers import FilenameProvider
from afterburner.utils.fileutils import list_files_at_or_newer_than

#: Symbolic constant used to select the MASS data store.
MASS_DATA_STORE = 'MASS'

# List of supported data stores.
DATA_STORE_IDS = (MASS_DATA_STORE, )


@add_metaclass(abc.ABCMeta)
class DataStore(object):
    """
    Abstract base class defining the public interface to a model data store.
    Application developers should instantiate one of the concrete subclasses
    defined later in this module.
    """

    def __init__(self, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.name = "Unnamed Data Store"

    @staticmethod
    def create_store(store_id):
        """
        Factory method for creating a data store object based on the specified
        data store identifier.

        :param str store_id: The identifier of the back-end data store. At
            present, support is limited to the MASS data archive, which can be
            selected using the :attr:`MASS_DATA_STORE` symbolic constant.
        :raises ValueError: Raised if ``store_id`` is invalid.
        :raises MooseUnavailableError: Raised if a MASS data store is specified
            but that system is not supported by the current runtime environment.
        """
        if store_id == MASS_DATA_STORE:
            if not moose.has_moose_support():
                msg = ("The MASS archive system does not appear to be supported "
                       "on the current platform.")
                raise MooseUnavailableError(msg)
            return MassDataStore()
        else:
            raise ValueError("Unrecognised data store identifier: %s" % store_id)

    def fetch_files_by_variable(self, varlist, overwrite=False, dest_dir=None,
            callback=None, file_mode=None, **kwargs):
        """
        Fetch files from the data store corresponding to the data variables
        specified in ``varlist``.

        :param list varlist: A list of :class:`afterburner.metavar.MetaVariable`
            objects defining the variables for which files are to be retrieved.
        :param bool overwrite: Set to true to force overwriting of existing
            files. Disables gap-filling mode.
        :param str dest_dir: Pathname of directory in or below which to store
            retrieved files. If this argument is not defined then it is set to
            the current working directory.
        :param func callback: The name of a callback function which returns a
            relative directory for a given meta-variable object. The absolute
            path of the directory in which to store files for the variable is
            obtained by appending the relative path to the path defined by the
            ``dest_dir`` argument. The signature of the function should be
            ``callback(metavar)``.
        :param int file_mode: Mode to apply to any retrieved files. If not set
            then the mode of any retrieved files will be determined by the umask
            of the calling user.
        :param kwargs: Data store-specific keyword arguments - refer to specific
            subclasses for details.
        """
        raise NotImplementedError()

    def fetch_streams_by_variable(self, varlist, overwrite=False, dest_dir=None,
            callback=None, file_mode=None, **kwargs):
        """
        Fetch files from the data store corresponding to the streams associated
        with the model diagnostics/variables specified in ``varlist``.

        :param list varlist: A list of :class:`afterburner.metavar.MetaVariable`
            objects defining the model-stream permutations for which files are
            to be retrieved.
        :param bool overwrite: Set to true to force overwriting of existing
            files. Disables gap-filling mode.
        :param str dest_dir: Pathname of directory in or below which to store
            retrieved files. If this argument is not defined then it is set to
            the current working directory.
        :param func callback: The name of a callback function which returns a
            relative directory for a given meta-variable object. The absolute
            path of the directory in which to store files for the variable is
            obtained by appending the relative path to the path defined by the
            ``dest_dir`` argument. The signature of the function should be
            ``callback(metavar)``.
        :param int file_mode: Mode to apply to any retrieved files. If not set
            then the mode of any retrieved files will be determined by the umask
            of the calling user.
        :param kwargs: Data store-specific keyword arguments - refer to specific
            subclasses for details.
        """
        raise NotImplementedError()

    def fetch_stream(self, model_name, suite_id, stream_id, realization_id=None,
            overwrite=False, dest_dir=None, file_mode=None, **kwargs):
        """
        Fetch *all* data files for the specified suite and stream.

        :param str model_name: The name of the model associated with the stream,
            e.g. 'UM', 'NEMO'. Used to determine the MASS data collection.
        :param str suite_id: The id of the suite that produced the stream. This
            should be a Rose suite name, e.g. 'mi-abcde', or a UM runid, e.g. 'abcde'.
        :param str stream_id: The stream identifer, e.g. 'apy', 'onm'.
        :param str realization_id: The realization identifier, e.g. 'r1i2p3'.
            This argument should be specified if the stream belongs to an
            ensemble member run.
        :param bool overwrite: Set to true to force overwriting of existing
            files in the cache. Disables gap-filling mode.
        :param str dest_dir: Pathname of directory in or below which to store
            retrieved files. If this argument is not defined then it is set to
            the current working directory.
        :param int file_mode: Mode to apply to any retrieved files. If not set
            then the mode of any retrieved files will be determined by the umask
            of the calling user.
        """
        raise NotImplementedError()


class NullDataStore(object):
    """
    The NullDataStore class implements a 'no-op' data store. In addition to its use
    for code testing purposes, instances of this class should also be of utility
    when creating read-only data caches for which a do-nothing data store object
    is required.
    """

    def __init__(self, **kwargs):
        super(NullDataStore, self).__init__(**kwargs)
        self.name = "Null Data Store"

    def fetch_files_by_variable(self, varlist, **kwargs):
        """Calls to this method result in no action."""
        pass

    def fetch_streams_by_variable(self, varlist, **kwargs):
        """Calls to this method result in no action."""
        pass

    def fetch_stream(self, model_name, suite_id, stream_id, **kwargs):
        """Calls to this method result in no action."""
        pass


class MassDataStore(DataStore):
    """
    Interface to the MASS data archive. MASS datastore objects can potentially
    be used to support a variety of disk-based data caching strategies. The
    various file fetch methods allow data to be retrieved in different sized
    chunks, as appropriate to the target data caching scheme.
    """

    def __init__(self, data_class='crum', **kwargs):
        """
        :param str data_class: The default MASS data class from which to retrieve
            data files. In some circumstances this value may be overridden; for
            example, if files are retrieved for a diagnostic that belongs to an
            ensemble climate model run (such files being held in the 'ens' class
            in MASS).
        :param kwargs: No extra keyword arguments used at present.
        """
        super(MassDataStore, self).__init__(**kwargs)
        self.name = "MASS Data Archive"
        self.data_class = data_class
        self.chunked_moose_requests = True

    def fetch_files_by_variable(self, varlist, overwrite=False, dest_dir=None,
            callback=None, file_mode=None, **kwargs):
        """
        Fetch files from the MASS data archive corresponding to the model
        diagnostic(s) or variable(s) specified in ``varlist``.

        By default files are restored to the current working directory. This
        behaviour can be modified by setting one or both of the ``dest_dir``
        and ``callback`` arguments. Indeed, doing so will be desirable in most
        scenarios since restoring to a single directory may result in multiple
        attempts to retrieve data into the same filename (MASS not yet providing
        the capability to *append* data to existing files).

        Similarly, by default files are retrieved in gap-filling mode. The
        ``overwrite`` option can be used to disable gap-filling and enable file
        overwriting.

        :param list varlist: A list of :class:`afterburner.metavar.MetaVariable`
            objects defining the variables for which files are to be retrieved.
        :param bool overwrite: Set to true to force overwriting of existing
            files. Disables gap-filling mode.
        :param str dest_dir: Pathname of directory in or below which to store
            retrieved files. If this argument is not defined then it is set to
            the current working directory.
        :param func callback: The name of a callback function which returns a
            relative directory for a given meta-variable object. The absolute
            path of the directory in which to store files for the variable is
            obtained by appending the relative path to the path defined by the
            ``dest_dir`` argument. The signature of the function should be
            ``callback(metavar)``.
        :param int file_mode: Mode to apply to any retrieved files. If not set
            then the mode of any retrieved files will be determined by the umask
            of the calling user.
        :raises MooseUnavailableError: Raised if MOOSE get operations are not
            currently available.
        """
        if not moose.check_moose_commands_enabled(moose.MOOSE_GET|moose.MOOSE_SELECT):
            msg = "MOOSE retrieval operations are not currently available."
            self.logger.error(msg)
            raise MooseUnavailableError(msg)

        # Check to see if calling code specified destination directories.
        base_dir = dest_dir or os.getcwd()
        fill_gaps = not overwrite

        for var in varlist:
            # Set destination directory.
            if callback:
                dest_dir = os.path.join(base_dir, callback(var))
            else:
                dest_dir = base_dir
            if not os.path.exists(dest_dir): os.makedirs(dest_dir)

            # Get filenames for current variable.
            fn_provider = FilenameProvider.from_metavar(var)
            filenames = fn_provider.get_filenames(var)
            if not filenames: continue

            # Following file check should no longer be necessary as new MOOSE
            # error code 17 is now handled by afterburner.io.moose functions.
            #if fill_gaps and _all_files_exist(dest_dir, filenames):
            #    continue

            collection = mass_collection_from_stream(var.model_name, var.stream_id)
            if var.realization_id:
                moose_uri = '/'.join(['moose:', 'ens', var.suite_id, var.realization_id,
                    collection])
            else:
                moose_uri = '/'.join(['moose:', self.data_class, var.suite_id,
                    collection])

            reftime = _get_reference_time(dest_dir)

            if isinstance(var, UmMetaVariable):
                if self.chunked_moose_requests:
                    moose.get_pp(dest_dir, moose_uri, files=filenames,
                        stashcodes=[var.stash_code], overwrite=overwrite,
                        fill_gaps=fill_gaps)
                else:
                    moose.retrieve_files(dest_dir, moose_uri, files=filenames,
                        stashcodes=[var.stash_code], overwrite=overwrite,
                        fill_gaps=fill_gaps)

            elif isinstance(var, (NemoMetaVariable, CiceMetaVariable)):
                var_names = [var.var_name]
                if var.aux_var_names: var_names += var.aux_var_names
                if self.chunked_moose_requests:
                    moose.get_nc(dest_dir, moose_uri, files=filenames,
                        var_names=var_names, overwrite=overwrite,
                        fill_gaps=fill_gaps)
                else:
                    moose.retrieve_nc_files(dest_dir, moose_uri, files=filenames,
                        var_names=var_names, overwrite=overwrite,
                        fill_gaps=fill_gaps)

            # If file_mode was passed in then apply it to any new/modified files.
            if file_mode:
                for pth in list_files_at_or_newer_than(dest_dir, reftime, abspath=True):
                    try:
                        os.chmod(pth, file_mode)
                    except OSError:
                        pass

    def fetch_streams_by_variable(self, varlist, overwrite=False, dest_dir=None,
            callback=None, file_mode=None, **kwargs):
        """
        Fetch files from the MASS data archive corresponding to the streams
        associated with the model diagnostics/variables specified in ``varlist``.

        By default files are restored to the current working directory. This
        behaviour can be modified by setting one or both of the ``dest_dir``
        and ``callback`` arguments. Indeed, doing so will be desirable in most
        scenarios since restoring to a single directory may result in multiple
        attempts to retrieve data into the same filename (MASS not yet providing
        the capability to *append* data to existing files).

        Similarly, by default files are retrieved in gap-filling mode. The
        ``overwrite`` option can be used to disable gap-filling and enable file
        overwriting.

        .. note:: The list of meta-variables passed in via the ``varlist`` argument
           will typically define diagnostics/variables that are derived either wholly
           from traditional, *non-ensemble* model runs, or else wholly from an *ensemble*
           of model runs. If a mix of such variables is supplied then the behaviour of
           this method may not be reliable since the two kinds of runs employ different
           data storage mechanisms.

        :param list varlist: A list of :class:`afterburner.metavar.MetaVariable`
            objects defining the model-stream permutations for which files are
            to be retrieved. Any time range information attached to individual
            variable definitions is ignored. The optional ``time_range`` keyword
            argument (see below) may be used to define a time range to apply to
            all retrieved data files. (NOTE: Only applies to UM streams)
        :param bool overwrite: Set to true to force overwriting of existing
            files. Disables gap-filling mode.
        :param str dest_dir: Pathname of directory in or below which to store
            retrieved files. If this argument is not defined then it is set to
            the current working directory.
        :param func callback: The name of a callback function which returns a
            relative directory for a given meta-variable object. The absolute
            path of the directory in which to store files for the variable is
            obtained by appending the relative path to the path defined by the
            ``dest_dir`` argument. The signature of the function should be
            ``callback(metavar)``.
        :param int file_mode: Mode to apply to any retrieved files. If not set
            then the mode of any retrieved files will be determined by the umask
            of the calling user.

        Extra Keyword Arguments (`**kwargs`):

        :param bool part_files: If set to true then retrieved files contain just
            those diagnostics/variables defined by varlist. By default whole files
            are retrieved, i.e. they contain all diagnostics (UM) or variables
            (NEMO, CICE, etc) associated with a given stream.
        :param list/tuple time_range: An optional 2-tuple specifying the start
            and end dates (in YYYY-MM-DDThh:mm:ss format) to apply to retrieved
            data files. (NOTE: Only applies to UM streams)

        :raises MooseUnavailableError: Raised if MOOSE get operations are not
            currently available.
        """
        if not moose.check_moose_commands_enabled(moose.MOOSE_GET|moose.MOOSE_SELECT):
            msg = "MOOSE retrieval operations are not currently available."
            self.logger.error(msg)
            raise MooseUnavailableError(msg)

        base_dir = dest_dir or os.getcwd()
        part_files = kwargs.get('part_files', False)
        time_range = kwargs.get('time_range')
        fill_gaps = not overwrite

        # Convert varlist to nested dictionary keyed by suite-realization-stream.
        # The realization part may be null, of course.
        varsets = _group_vars_by_unique_streams(varlist)
        varset_keys = [(suite, ens, strm) for suite in sorted(varsets)
            for ens in sorted(varsets[suite])
            for strm in sorted(varsets[suite][ens])]

        # Loop over each (suite, realization, stream) combination, retrieving
        # data files from the associated MASS dataset and collection.
        for suite_id, realization_id, stream_id in varset_keys:
            varset = varsets[suite_id][realization_id][stream_id]
            varnames = sorted({v.slug for v in varset})

            # Set destination directory.
            if callback:
                dest_dir = os.path.join(base_dir, callback(varset[0]))
            else:
                dest_dir = base_dir
            if not os.path.exists(dest_dir): os.makedirs(dest_dir)

            model_name = varset[0].model_name
            collection = mass_collection_from_stream(model_name, stream_id)
            if realization_id:
                moose_uri = '/'.join(['moose:', 'ens', suite_id, realization_id,
                    collection])
            else:
                moose_uri = '/'.join(['moose:', self.data_class, suite_id,
                    collection])

            reftime = _get_reference_time(dest_dir)

            # UM model stream.
            if model_name == MODEL_UM:
                stashcodes = part_files and varnames or None
                if self.chunked_moose_requests:
                    moose.get_pp(dest_dir, moose_uri, stashcodes=stashcodes,
                        time_range=time_range, overwrite=overwrite,
                        fill_gaps=fill_gaps)
                else:
                    moose.retrieve_files(dest_dir, moose_uri, stashcodes=stashcodes,
                        time_range=time_range, overwrite=overwrite,
                        fill_gaps=fill_gaps)

            # NEMO/CICE model streams.
            elif model_name in (MODEL_NEMO, MODEL_CICE):
                var_names = part_files and varnames or None
                if self.chunked_moose_requests:
                    moose.get_nc(dest_dir, moose_uri, var_names=var_names,
                        overwrite=overwrite, fill_gaps=fill_gaps)
                else:
                    moose.retrieve_nc_files(dest_dir, moose_uri, var_names=var_names,
                        overwrite=overwrite, fill_gaps=fill_gaps)

            # If file_mode was passed in then apply it to any new/modified files.
            if file_mode:
                for pth in list_files_at_or_newer_than(dest_dir, reftime, abspath=True):
                    try:
                        os.chmod(pth, file_mode)
                    except OSError:
                        pass

    def fetch_stream(self, model_name, suite_id, stream_id, realization_id=None,
            overwrite=False, dest_dir=None, file_mode=None, **kwargs):
        """
        Fetch *all* data files for the specified suite and stream. By default
        files are retrieved in gap-filling mode so that files already in the
        cache get used as-is. The overwrite option can be used to turn off
        gap-filling and enable file overwriting.

        :param str model_name: The name of the model associated with the stream,
            e.g. 'UM', 'NEMO'. Used to determine the MASS data collection.
        :param str suite_id: The id of the suite that produced the stream. This
            should be a Rose suite name, e.g. 'mi-abcde', or a UM runid, e.g. 'abcde'.
        :param str stream_id: The stream identifer, e.g. 'apy', 'onm'.
        :param str realization_id: The realization identifier, e.g. 'r1i2p3'.
            This argument should be specified if the stream belongs to an
            ensemble member run.
        :param bool overwrite: Set to true to force overwriting of existing
            files in the cache. Disables gap-filling mode.
        :param str dest_dir: Pathname of directory in or below which to store
            retrieved files. If this argument is not defined then it is set to
            the current working directory.
        :param int file_mode: Mode to apply to any retrieved files. If not set
            then the mode of any retrieved files will be determined by the umask
            of the calling user.
        :raises MooseUnavailableError: Raised if MOOSE get operations are not
            currently available.
        :raises UnknownModelNameError: Raised if ``model_name`` is not recognised.
        """
        if not moose.check_moose_commands_enabled(moose.MOOSE_GET):
            msg = "MOOSE retrieval operations are not currently available."
            self.logger.error(msg)
            raise MooseUnavailableError(msg)

        if model_name not in KNOWN_MODELS:
            raise UnknownModelNameError("Unrecognised model name: " + model_name)

        fill_gaps = not overwrite
        if not dest_dir: dest_dir = os.getcwd()
        if not os.path.exists(dest_dir): os.makedirs(dest_dir)
        collection = mass_collection_from_stream(model_name, stream_id)

        if realization_id:
            moose_uri = '/'.join(['moose:', 'ens', suite_id, realization_id, collection])
        else:
            moose_uri = '/'.join(['moose:', self.data_class, suite_id, collection])

        reftime = _get_reference_time(dest_dir)

        moose.retrieve_files(dest_dir, moose_uri, overwrite=overwrite, fill_gaps=fill_gaps)

        # If file_mode was passed in then apply it to any new/modified files.
        if file_mode:
            for pth in list_files_at_or_newer_than(dest_dir, reftime, abspath=True):
                try:
                    os.chmod(pth, file_mode)
                except OSError:
                    pass


def _all_files_exist(dest_dir, filenames):
    """
    Check to see if all files listed in ``filenames`` exist in ``dest_dir``.
    This may be used as a workaround for the issue whereby the MOOSE -i
    option (fill gaps) raises error code 2 if all requested files exist,
    instead of just completing silently, as might be expected.

    :param str dest_dir: The path of the directory to check for files.
    :param list filenames: The list of file names (NOT paths) to check.
    """
    files_on_disk = os.listdir(dest_dir)
    for fn in filenames:
        if fn not in files_on_disk: return False
    return True


def _group_vars_by_unique_streams(varlist):
    """
    Convert ``varlist`` into a nested dictionary keyed by suite-id, realization-id
    and stream-id. Each dictionary value is a list of the metavariable objects
    associated with a unique suite-realization-stream combination.
    """
    varsets = {}
    for var in varlist:
        suite_dict = varsets.setdefault(var.suite_id, {})
        # Realization might be undefined so set consistently to the empty string.
        ens = var.realization_id or ''
        ens_dict = suite_dict.setdefault(ens, {})
        varset = ens_dict.setdefault(var.stream_id, list())
        varset.append(var)
    return varsets


def _get_reference_time(dirpath='.', sleep_time=0):
    """
    Obtain a reference time suitable for identifying files created subsequently
    to a call to this function. Rather than simply querying the current system
    time (which can be prone to system-to-system differences), a temporary file
    is first created within the directory (default '.') specified by the dirpath
    argument. The modification time of this file is then used as the function's
    return value. Any subsequently created files - at least those on the same
    file system as dirpath - should necessarily have a later creation time.
    """
    now = datetime.datetime.now()

    try:
        fd, tmpfile = tempfile.mkstemp(dir=dirpath)
        with os.fdopen(fd, 'w') as fh:
            fh.write(str(now)+'\n')
        st = os.stat(tmpfile)
        os.remove(tmpfile)
        reftime = datetime.datetime.fromtimestamp(st.st_mtime)
    except OSError:
        reftime = now

    # If sleep_time is defined then honour it. This can be useful to avoid the
    # issue whereby, owing to time-rounding, files created shortly *after* the
    # temporary file appear to have the same creation time.
    if sleep_time > 0: time.sleep(sleep_time)

    return reftime.replace(microsecond=0)
