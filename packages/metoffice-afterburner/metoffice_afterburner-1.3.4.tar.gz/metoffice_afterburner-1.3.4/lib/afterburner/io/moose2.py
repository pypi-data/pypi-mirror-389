# (C) British Crown Copyright 2017-2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The ``moose2`` module, which supersedes the earlier :mod:`afterburner.io.moose`
module, provides an interface to a limited subset of the MOOSE command-line toolset,
i.e. 'moo ls', 'moo get', 'moo select', and so on.

Only the more frequently used MOOSE commands are currently supported and, for
each command, only a subset of options. Refer to the documentation below for
details.

If a specific function is not available for your particular data I/O requirements
then the :func:`run_moose_command <afterburner.io._moose_core.run_moose_command>`
function provides a mechanism for executing an arbitrary MOOSE command, and with
useful exception handling.

The ``moose2`` module is essentially a namespace container that provides a
single access point to the underlying support modules (of the form '_moose_*')
which actually implement the MOOSE interface. These modules are as follows:

* `afterburner.io._moose_core` -- core functions used by the other '_moose_*' modules
* `afterburner.io._moose_q` -- MOOSE querying/listing functions
* `afterburner.io._moose_r` -- MOOSE data reading functions
* `afterburner.io._moose_w` -- MOOSE data writing functions

Client code should not normally need to access these support modules directly:
all of the public functions and data members can be accessed via the ``moose2``
module.

If existing code refers to the earlier ``moose`` module, then this can readily
be re-targeted by modifying the relevant import command, e.g.::

    >>> # change...
    >>> import afterburner.io.moose
    >>> # to...
    >>> import afterburner.io.moose2 as moose

** Classes **

* :class:`MooseCommand <afterburner.io._moose_core.MooseCommand>`

**Query Functions**

* :func:`has_moose_support <afterburner.io._moose_core.has_moose_support>`
* :func:`get_moose_limits <afterburner.io._moose_core.get_moose_limits>`
* :func:`get_moose_logger <afterburner.io._moose_core.get_moose_logger>`
* :func:`get_moose_version <afterburner.io._moose_core.get_moose_version>`
* :func:`check_moose_commands_enabled <afterburner.io._moose_core.check_moose_commands_enabled>`
* :func:`run_moose_command <afterburner.io._moose_core.run_moose_command>`
* :func:`list_files <afterburner.io._moose_q.list_files>`
* :func:`list_struct_files <afterburner.io._moose_q.list_struct_files>`
* :func:`metadata_list_struct <afterburner.io._moose_q.metadata_list_struct>`
* :func:`query_time_extent <afterburner.io._moose_q.query_time_extent>`

**Data Reading Functions**

* :func:`get <afterburner.io._moose_r.get>`
* :func:`get_pp <afterburner.io._moose_r.get_pp>`
* :func:`get_nc <afterburner.io._moose_r.get_nc>`
* :func:`retrieve_files <afterburner.io._moose_r.retrieve_files>`
* :func:`retrieve_nc_files <afterburner.io._moose_r.retrieve_nc_files>`
* :func:`retrieve_struct_files <afterburner.io._moose_r.retrieve_struct_files>`

**Data Writing Functions**

* :func:`put <afterburner.io._moose_w.put>`
* :func:`put_files <afterburner.io._moose_w.put_files>`
* :func:`put_struct_files <afterburner.io._moose_w.put_struct_files>`

**Descriptions of Constants and Functions**

.. automodule:: afterburner.io._moose_core
   :members:
   :exclude-members: request_splitter

.. automodule:: afterburner.io._moose_q
   :members:

.. automodule:: afterburner.io._moose_r
   :members:

.. automodule:: afterburner.io._moose_w
   :members:
"""
# pylint: disable=W0611,W0614,W0401

from __future__ import (absolute_import, division, print_function)

from ._moose_core import (
    MOOSE_SYSTEM_OUTAGE, MOOSE_TEMPORARILY_DISABLED, MOOSE_ALL_FILES_EXIST,
    MOOSE_LS, MOOSE_MDLS, MOOSE_PUT, MOOSE_GET,
    MOOSE_SELECT, MOOSE_FILTER, MOOSE_ALL, MOOSE_CLI,
    MOOSE_GET_MAX_FILES, MOOSE_GET_MAX_VOLUME, MOOSE_GET_MAX_TAPES,
    MOOSE_PUT_MAX_FILES, MOOSE_PUT_MAX_VOLUME,
    MOOSE_MAX_QUERY_FILE_SIZE,
    MOOSE_MAX_XFER_THREADS, MOOSE_MAX_CONV_THREADS, MOOSE_LOGGER_NAME,
    MooseCommand,
    has_moose_support, get_moose_logger, get_moose_limits, get_moose_version,
    check_moose_commands_enabled, run_moose_command,
    write_query_file, write_filter_file)

# These 3 modules have the __all__ attribute defined so the impact of 'import *'
# should be minimal.
from ._moose_q import *
from ._moose_r import *
from ._moose_w import *
