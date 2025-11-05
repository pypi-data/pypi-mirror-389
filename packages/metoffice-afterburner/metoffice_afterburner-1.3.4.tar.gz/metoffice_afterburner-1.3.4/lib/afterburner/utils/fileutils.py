# (C) British Crown Copyright 2016-2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The fileutils module contains various utility functions for working with files
and directories, manipulating pathnames, and so on.

**Index of Functions in this Module**

.. autosummary::
   :nosignatures:

   restore_cwd
   expand_path
   expand_filenames
   filter_by_sentinel_files
   list_files_newer_than
   list_files_at_or_newer_than
   list_files_by_mod_time
   serialize_timestamp
   deserialize_timestamp
   truncate_path
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import string_types

import os
import glob
import datetime
import operator
import contextlib

try:
    import filelock
except ImportError:
    filelock = None


@contextlib.contextmanager
def restore_cwd(wd=None):
    """
    Implements a context manager that restores the current working directory
    when it exits. The ``wd`` argument may be used to specify an initial working
    directory to change to when the context manager is initialised. The working
    directory can of course be changed any number of times thereafter within the
    enclosing with-block. For example::

        with restore_cwd(wd='/home/mary/tmp'):
            # do something in directory /home/mary/tmp
            ...
            os.chdir('foo')
            # do something in directory /home/mary/tmp/foo
            ...

    :param str wd: Optionally, the pathname of the initial working directory to
        set at the top of the enclosing with-block.
    """
    cwd = os.getcwd()
    if wd: os.chdir(wd)
    try:
        yield
    finally:
        os.chdir(cwd)


def expand_path(path):
    """
    Simple convenience function for expanding any '~' or '$VARIABLE' tokens
    present within the specified pathname. Additionally, the returned pathname
    is coerced to be absolute.

    :param str path: The pathname to expand.
    :returns: An absolute pathname with any '~' or '$VARIABLE' tokens expanded.
    """
    if path.startswith('~') or '$' in path:
        path = os.path.expanduser(os.path.expandvars(path))
    return os.path.abspath(path)


def expand_filenames(filenames, dirname=None):
    """
    Expand any glob characters present in the specified list of
    filenames.

    :param iterable filenames: An iterable of filenames, none,
        some, or all of which may contain glob characters.
    :param str dirname: The directory within which the files
        reside. Defaults to the current working directory if not
        defined.
    :returns: A list of unique filenames with any glob characters
        expanded.
    """
    input_files = set()

    with restore_cwd(wd=dirname):
        for fname in filenames:
            files = glob.glob(fname)
            input_files.update(files)

    return list(input_files)


def filter_by_sentinel_files(filenames, src_dir, sentinel_dir=None,
        sentinel_file_ext='.arch', ignore_file_ext=''):
    """
    Takes a list of input filenames (from src_dir) and reduces the list to only
    those files that have an associated sentinel file (in sentinel_dir). A common
    usage scenario involves selecting UM model output files for which corresponding
    sentinel files exist with a '.arch' extension, usually in some other directory.

    If the ignore_file_ext argument is undefined (the default), then sentinel
    filenames are assumed to be constructed by simple concatenation of the source
    filename and the sentinel file extension. In the case of a source file named
    ``expida.pm2000jan``, for example, and a default sentinel file extension of
    ``.arch``, a match would be sought against a corresponding sentinel file named
    ``expida.pm2000jan.arch``.

    If the ignore_file_ext argument is defined, on the other hand, then a match
    is sought on the basis that any sentinel file(s) **do not** contain that
    extension. In the case of a source file named ``expida.pm2000jan.pp``, for
    example, then the expected sentinel filename would be ``expida.pm2000jan.arch``
    (as above) rather than ``expida.pm2000jan.pp.arch``.

    .. note:: If no sentinel files are present in the indicated directory then,
       by definition, the function returns an empty list (since no file matches
       are possible). This is intentional: one does not normally want to apply
       some operation to a particular file unless there is a sentinel file present
       which indicates that it is ready for that operation.

    :param list filenames: The list of filenames (not paths) to filter. Individual
        filenames may contain wildcard characters.
    :param str src_dir: The pathname of the directory containing the files
        specified in the ``filenames`` argument. Also acts as the directory in
        which to look for sentinel files if ``sentinel_dir`` is undefined.
    :param str sentinel_dir: The pathname of the directory containing any
        sentinel files. In not specified then use the directory defined by the
        ``src_dir`` argument.
    :param str sentinel_file_ext: The extension used to identify sentinel files.
    :returns: A list, possibly empty, of filtered filenames.
    :raises OSError: Raised if either of the specified directories does not exist.
    """

    # If neither filenames nor sentinel_file_ext is defined then return early.
    if not (filenames and sentinel_file_ext):
        return filenames

    # If the sentinel directory is not specified set it to the source directory.
    if not sentinel_dir:
        sentinel_dir = src_dir

    # Obtain a list of sentinel files. If none found then no match against
    # input data files is possible so return an empty list.
    sentinel_files = expand_filenames(['*'+sentinel_file_ext],
        dirname=sentinel_dir)
    if not sentinel_files:
        return []

    # Convert the list of sentinel files, minus the file extension, to a set.
    sentinel_files = {os.path.splitext(f)[0]+ignore_file_ext for f in sentinel_files}

    # Expand the (possibly wildcarded) names of any/all input data files.
    input_files = set(expand_filenames(filenames, dirname=src_dir))

    # Remove any input files that do not have a matching sentinel file.
    # This is achieved by finding the intersection between the set of input
    # files and the set of sentinel files.
    input_files.intersection_update(sentinel_files)

    return list(input_files)


def list_files_newer_than(path, reftime, abspath=False):
    """
    List files in a directory whose *modification* time is more recent than the
    specified reference time. Subdirectories and symbolic links are ignored.

    This function is a simple wrapper around the :func:`list_files_by_mod_time`
    function, invoked with the appropriate comparison operator.

    :param str path: The pathname of the directory to list.
    :param datetime.datetime reftime: The reference time to test against.
    :param bool abspath: If set to true then absolute pathnames are returned.
        By default only filenames are returned.
    :returns: A list of filenames or, if ``abspath`` evaluates true, absolute
        pathnames.
    """
    return list_files_by_mod_time(path, reftime, operator.gt, abspath=abspath)


def list_files_at_or_newer_than(path, reftime, abspath=False):
    """
    List files in a directory whose *modification* time is the same as or more
    recent than the specified reference time. Subdirectories and symbolic links
    are ignored.

    This function is a simple wrapper around the :func:`list_files_by_mod_time`
    function, invoked with the appropriate comparison operator.

    :param str path: The pathname of the directory to list.
    :param datetime.datetime reftime: The reference time to test against.
    :param bool abspath: If set to true then absolute pathnames are returned.
        By default only filenames are returned.
    :returns: A list of filenames or, if ``abspath`` evaluates true, absolute
        pathnames.
    """
    return list_files_by_mod_time(path, reftime, operator.ge, abspath=abspath)


def list_files_by_mod_time(path, reftime, oper, abspath=False):
    """
    List files in a directory whose *modification* time, when compared against
    the specified reference time using comparison operator ``oper``, yields true.
    Subdirectories and symbolic links are ignored.

    :param str path: The pathname of the directory to list.
    :param datetime.datetime reftime: The reference time to test against.
    :param func_or_str oper: The comparison operator. Either one of the object
        comparison functions defined in Python's `operator <https://docs.python.org/2/library/operator.html>`_
        module, or the equivalent string name, e.g. 'gt', 'ge', etc.
    :param bool abspath: If set to true then absolute pathnames are returned.
        By default only filenames are returned.
    :returns: A list of filenames or, if ``abspath`` evaluates true, absolute
        pathnames.
    """
    if isinstance(oper, string_types):
        oper = getattr(operator, oper)

    path = os.path.abspath(path)
    files = []

    for fname in os.listdir(path):
        fpath = os.path.join(path, fname)
        if os.path.isdir(fpath) or os.path.islink(fpath): continue
        st = os.stat(fpath)
        mtime = datetime.datetime.fromtimestamp(st.st_mtime)
        if oper(mtime, reftime):
            files.append(abspath and fpath or fname)

    return files


def serialize_timestamp(filepath, timestamp):
    """
    Write an ISO-formatted datetime stamp to the first line of the text file
    pointed to by ``filepath``. If the filelock package is available then an
    attempt is made to lock the file during the write operation. If the timestamp
    file needs to be created then any intermediate directories are also created
    if required.

    :param str filepath: The file to which to write the timestamp.
    :param datetime.datetime timestamp: The timestamp to write.
    :raises filelock.Timeout: Raised if a lock could not be acquired on the
        timestamp file.
    """

    # Create intermediate directories to filepath, if necessary.
    dirpath = os.path.dirname(os.path.abspath(filepath))
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    if filelock:
        lockfile = filepath + '.lock'
        with filelock.FileLock(lockfile, timeout=30):
            with open(filepath, 'w') as fh:
                fh.write(timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f') + '\n')
        try:
            os.remove(lockfile)
        except OSError:
            pass

    else:
        with open(filepath, 'w') as fh:
            fh.write(timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f') + '\n')


def deserialize_timestamp(filepath):
    """
    Read an ISO-formatted datetime stamp from the first line of the text file
    pointed to by ``filepath``.

    :param str filepath: The file from which to read a timestamp.
    :returns: A Python datetime object representing the timestamp.
    """

    with open(filepath, 'r') as fh:
        dt_str = fh.readline()
        try:
            # timestamp includes microseconds
            timestamp = datetime.datetime.strptime(dt_str.strip(), '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            # timestamp does not include microseconds
            timestamp = datetime.datetime.strptime(dt_str.strip(), '%Y-%m-%dT%H:%M:%S')

    return timestamp


def truncate_path(path, ancestor, right=False):
    """
    Truncate a pathname at the left-most (by default) or right-most occurrence
    of the directory defined by ``ancestor``. If the ancestor directory only
    occurs once - as is often the case - then the value of the ``right`` option
    is immaterial. The ancestor directory is included as the final element in
    the returned path.

    Some example function calls are shown below::

        >>> truncate_path('/p/x/y/z', 'p')
        '/p'
        >>> truncate_path('/p/x/y/z/', 'x')
        '/p/x'
        >>> truncate_path('p/x/y/z', 'y')  # relative pathname supplied
        'p/x/y'
        >>> truncate_path('/p/x/y/x/z', 'x')  # truncates to left-most occurrence
        '/p/x'
        >>> truncate_path('/p/x/y/x/z', 'x', right=True)
        '/p/x/y/x'
        >>> truncate_path('p/x/y/x/z', 'y', right=True)
        'p/x/y'

    :param str path: The pathname to be truncated. It can be a relative or
        absolute path.
    :param str ancestor: The name of the ancestor directory at which to truncate
        ``path``.
    :param bool right: By default the pathname is truncated at the left-most
        occurrence of ``ancestor``. This option can be used to request truncation
        at the right-most occurrence.
    :returns: The truncated pathname, or None if the specified ancestor directory
        does not occur in ``path``.
    """
    parts = path.split(os.sep)
    if ancestor not in parts: return None
    if right:
        i = _list_rindex(parts, ancestor)
    else:
        i = parts.index(ancestor)
    return os.sep.join(parts[:i+1])


def _list_rindex(alist, item):
    """Return the index of the right-most occurrence of item in alist."""
    if item not in alist: return -1
    nparts = len(alist)
    return (nparts-1) - alist[::-1].index(item)
