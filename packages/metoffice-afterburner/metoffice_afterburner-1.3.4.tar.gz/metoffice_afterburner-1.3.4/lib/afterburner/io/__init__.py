# (C) British Crown Copyright 2016-2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The afterburner.io package is a container for I/O related functionality. The
package currently contains the following modules:

moose
-----
The moose module has been deprecated in favour of the :mod:`moose2 <afterburner.io.moose2>`
module (see below), which provides equivalent functionality. If existing code
refers to the moose module then this can be re-targeted, if desired, by modifying
the relevant import command. For example::

    >>> # change one of these...
    >>> import afterburner.io.moose
    >>> from afterburner.io import moose
    >>> # to one of these...
    >>> import afterburner.io.moose2 as moose
    >>> from afterburner.io import moose2 as moose

moose2
------
The :mod:`moose2 <afterburner.io.moose2>` module provides functionality for
interacting with the MASS data archive. Functions are available which emulate
a subset of the functionality provided by the MOOSE command-line interface,
including querying, retrieving, and archiving model data files.

datacaches
----------
The :mod:`datacaches <afterburner.io.datacaches>` module provides functionality
for creating and interacting with on-disk caches of model data files. A data cache
is associated with a particular back-end data store, access to which is handled
by functionality provided by the datastores module (see next entry).

datastores
----------
The :mod:`datastores <afterburner.io.datastores>` module provides functionality
for interacting with the popular sources of archived climate model data. At present
support is limited to the MASS data archive.
"""
from __future__ import absolute_import
from afterburner.processors.writers.netcdf_writer import NetcdfFileWriter
