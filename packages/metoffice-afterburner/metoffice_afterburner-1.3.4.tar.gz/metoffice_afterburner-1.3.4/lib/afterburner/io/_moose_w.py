# (C) British Crown Copyright 2017-2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.

# The ``_moose_w`` module contains functions which act as a wrapper around the
# main MOOSE data writing commands, namely 'put'.
#
# Client applications should normally access the functions defined here via the
# afterburner.io.moose2 module.

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import os

from afterburner.io import _moose_core

__all__ = ('put', 'put_files', 'put_struct_files')

logger = _moose_core.get_moose_logger()


def put(src_dir, files, moose_uri, overwrite=False, overwrite_if_different=False,
        splitter_args=None):
    """
    Put the specified files into MASS taking into account the various limits (file
    number, data volume, etc) imposed by the MOOSE interface. This function is
    a wrapper around the :func:`put_files` function. Refer to that function for
    a description of common arguments.

    :param dict splitter_args: If specified, this should be a dictionary of
        keyword arguments to pass through to the :func:`_moose.core.request_splitter`
        function.
    :raises MooseLimitExceededError: Raised if an error was encountered trying
        to split the MOOSE request into chunks.
    """
    if splitter_args is None: splitter_args = {}
    file_chunks = _moose_core.request_splitter('put', files, dirpath=src_dir,
        **splitter_args)

    for chunk in file_chunks:
        put_files(src_dir, chunk, moose_uri, overwrite=overwrite,
            overwrite_if_different=overwrite_if_different)


def put_files(src_dir, files, moose_uri, overwrite=False,
        overwrite_if_different=False):
    """
    Put the specified files into MASS using MOOSE. This function requires the
    ``moo put`` command to be enabled. If necessary, client code can check this
    via a call to :func:`afterburner.io.moose2.check_moose_commands_enabled`.

    :param str src_dir: The local source directory where the files are located.
    :param list files: A list of the files to be copied from ``src_dir`` to MASS.
    :param str moose_uri: The MOOSE URI of the location in the MASS archive in
        which to store the specified files.
    :param bool overwrite: Force the overwriting of existing files (equivalent
        to the ``moo put -f`` option). This argument takes precedence over the
        ``overwrite_if_different`` argument.
    :param bool overwrite_if_different: Force the overwriting of existing files
        unless the source and destination files match in both size and checksum
        (equivalent to the ``moo put -F`` option).
    :raises ValueError: Raised if the ``files`` argument is not a list or tuple.
    """
    if not isinstance(files, (list, tuple)):
        msg = "The 'files' argument must be a list (or tuple) of filenames."
        logger.error(msg)
        raise ValueError(msg)

    opts = []
    if overwrite:
        opts.append('-f')
    elif overwrite_if_different:
        opts.append('-F')

    args = [os.path.join(src_dir, fn) for fn in files]
    args.append(moose_uri)

    command = _moose_core.MooseCommand('put', options=opts, arguments=args)

    _moose_core.run_moose_command(command.augmented_command)


def put_struct_files(src_dir, files, data_set, collection, data_class='crum',
        overwrite=False, overwrite_if_different=False):
    """
    Put the specified files into a MASS structured data class using MOOSE.
    This function requires the ``moo put`` command to be enabled. If necessary,
    client code can check this via a call to
    :func:`afterburner.io.moose2.check_moose_commands_enabled`.

    :param str src_dir: The local source directory where the files are located.
    :param list files: A list of the files to be copied from ``src_dir`` to MASS.
    :param str data_set: The MOOSE data set to put into, e.g. the model name.
    :param str collection: The MOOSE collection to put into, e.g. 'apy.pp' or
        'ens19/apa.pp' in the case of an ensemble run.
    :param str data_class: The MOOSE data class to put into, e.g. 'crum' or 'ens'.
    :param bool overwrite: Force the overwriting of existing files (equivalent
        to the ``moo put -f`` option). This argument takes precedence over the
        ``overwrite_if_different`` argument.
    :param bool overwrite_if_different: Force the overwriting of existing files
        unless the source and destination files match in both size and checksum
        (equivalent to the ``moo put -F`` option).
    """
    moose_uri = 'moose:/{}/{}/{}'.format(data_class, data_set, collection)

    put_files(src_dir, files, moose_uri, overwrite=overwrite,
        overwrite_if_different=overwrite_if_different)
