# (C) British Crown Copyright 2016-2020, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Defines the NetcdfFileWriter class, which can be used to write (or append) an
Iris cube or cubelist to a netCDF file. By default the file is written in netCDF4
format, using a compression level of 2, and with no unlimited dimensions.

.. warning:: The Iris documentation cautions against saving a cube (or cubes) to
   the same file that was used as the original source for the cube(s). If the
   cube(s) have been lazily loaded then the data in memory, and in the original
   file, are liable to being lost or corrupted.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import os
import inspect
import shutil
import tempfile

import iris
import iris.util
import iris.exceptions
try:
    from iris.util import equalise_attributes
except ImportError:
    from iris.experimental.equalise_cubes import equalise_attributes

from afterburner import compare_iris_version
from afterburner.processors import AbstractProcessor

# See if the filelock module is available.
try:
    import filelock
except ImportError:
    filelock = None


class NetcdfFileWriter(AbstractProcessor):
    """
    Processor class for writing an Iris cube or cubelist to a netCDF file.
    The following default options are passed to the `iris.fileformats.netcdf.save
    <http://scitools.org.uk/iris/docs/latest/iris/iris/fileformats/netcdf.html#iris.fileformats.netcdf.save>`_
    function. Options not listed below take on Iris' default save settings.

    ====================  ===============
    Save Option           Default Value
    ====================  ===============
    complevel             2
    fletcher32            False
    shuffle               False
    zlib                  True
    unlimited_dimensions  []
    ====================  ===============

    If required, netCDF file writer objects may be initialised using different
    settings to those listed above. For example, data compression might be
    disabled by default as follows::

        >>> from afterburner.processors.writers.netcdf_writer import NetcdfFileWriter
        >>> writer = NetcdfFileWriter(zlib=False)

    Individual save options may then be overridden by passing suitably-named
    keyword arguments to the :meth:`run` (or :meth:`write`) methods, e.g.::

        >>> writer.run(cubes, 'myfile.nc', zlib=True, complevel=6)
        >>> writer.write(cubes, 'myfile.nc', netcdf_format='NETCDF4_CLASSIC')

    Typically, however, the default settings - either those used by Iris or those
    set by the calling client - will be sufficient for a related series of file
    writing operations.

    .. note:: If the ``netcdf_format`` keyword argument is defined so as to
       request the netCDF-3 storage format (i.e. NETCDF3_CLASSIC or NETCDF4_CLASSIC)
       then care is need to ensure that the remaining options, and the passed-in
       cubes, are compatible with that format. In particular, Iris routinely
       stores integer-type cubes using Python's native 64-bit integer data type.
       This data type *cannot be handled by the netCDF-3 storage format*, and
       as such is a common cause of file-writing errors.

    Appending data to an existing netCDF file can be achieved by setting the
    ``append`` keyword argument to True. This results in the following sequence
    of actions:

    * The variables in the existing netCDF file are loaded into a cubelist.
    * An attempt is made to identify variables which are common to the loaded
      cubelist and to the input cubelist specified by the calling program.
    * For each such variable, the corresponding cube in the input cubelist is
      modified so as to make the cube and coordinate object metadata consistent
      (in order to eliminate, or minimise, subsequent cube concatenation errors).
    * The two cubelists are concatenated. Depending upon how the contained cubes
      have been defined, this may result in a smaller, rationalised cubelist.
    * The final cubelist is saved to a temporary file.
    * The temporary file is copied over the existing netCDF file (this should
      be an atomic operation at the OS level).
    * The temporary file is deleted.

    If there are subtle differences in the metadata attached to the cube and/or
    coordinate objects, then the concatenation operation will likely be thwarted.
    As a consequence, the updated netCDF file might contain a simple union of the
    existing and new cubes. This may or may not be helpful!
    """

    def __init__(self, **kwargs):
        """
        Extra Keyword Arguments (`**kwargs`):

        :param bool append: Specifies whether or not to append data to an existing
            output file. If true, then the overwrite option is ignored since
            one can only append to an existing file. (default: False)
        :param bool overwrite: Specifies whether or not an existing output file
            should be overwritten. (default: False)

        Additional keyword arguments may be used to specify any of the arguments
        recognised by the `iris.fileformats.netcdf.save
        <http://scitools.org.uk/iris/docs/latest/iris/iris/fileformats/netcdf.html#iris.fileformats.netcdf.save>`_
        function, e.g. netcdf_format, zlib, complevel, and so on.
        """
        super(NetcdfFileWriter, self).__init__(**kwargs)
        self.append = kwargs.get('append', False)
        self.overwrite = kwargs.get('overwrite', False)

        # Set default options for use with the iris.save() function.
        self.def_save_options = dict(complevel=2, fletcher32=False,
            shuffle=False, zlib=True, unlimited_dimensions=[])

        # Update default options with any user-supplied values.
        for key in _get_iris_save_keywords():
            if key in kwargs:
                self.def_save_options[key] = kwargs[key]

    def run(self, cubelist, filename, **kwargs):
        """
        Save the cubelist to the specified filename. The default save options,
        if any, specified via the :meth:`__init__` method may be overridden or
        supplemented, *for the current invocation only*, by setting the desired
        keyword argument(s). For example::

            >>> writer = NetcdfFileWriter(zlib=True, complevel=6)
            >>> # use default settings
            >>> writer.run(cubes, filename)
            >>> # override selected default settings
            >>> writer.run(cubes, filename, zlib=False, overwrite=True)

        :param iris.cube.CubeList cubelist: The cube or cubelist to write to
            ``filename``.
        :param str filename: The pathname of the output netCDF file.

        Extra Keyword Arguments (`**kwargs`):

        :param bool append: Specifies whether or not to append data to an existing
            output file. This argument temporarily overrides the default value
            for this option as set via the :meth:`__init__` method.
        :param bool overwrite: Specifies whether or not to overwrite ``filename``,
            if it exists. This argument temporarily overrides the default value
            for this option as set via the :meth:`__init__` method.
        :param bool equalise_attrs: If set to true then, in the case of an append
            operation, the attributes of all cubes are equalised as a precursor
            step to concatenation. (default: False)

        :raises IOError: Raised if an error was encountered trying to write to
            the netCDF file, or if the output file exists and the ``overwrite``
            option is set to false.
        """
        append = kwargs.get('append', self.append)
        if append:
            overwrite = True
        else:
            overwrite = kwargs.get('overwrite', self.overwrite)

        file_exists = os.path.exists(filename)
        if file_exists and not overwrite:
            msg = "File '%s' exists but overwrite option is not enabled." % filename
            raise IOError(msg)

        # If a single cube was passed in, make a cubelist from it.
        if isinstance(cubelist, iris.cube.Cube):
            cubelist = iris.cube.CubeList([cubelist])

        try:
            save_options = self.def_save_options.copy()
            for key in _get_iris_save_keywords():
                if key in kwargs:
                    save_options[key] = kwargs[key]

            self.logger.debug("Output file: %s", filename)
            self.logger.debug("Save options: %s", save_options)

            # If destination file exists then perform a two-stage save via a
            # temporary output file.
            if file_exists:
                if append:
                    # Concatenate cubes loaded from file with cubes passed in by
                    # caller. Note that this operation is readily confounded by
                    # small differences in cube metadata.
                    futures = compare_iris_version('2', 'lt') and \
                        {'netcdf_promote': True} or {}
                    with iris.FUTURE.context(**futures):
                        cubes_from_file = iris.load(filename)
                    cubelist = _concatenate_cubes(cubes_from_file, cubelist,
                        equalise_attrs=kwargs.get('equalise_attrs'))
                _two_stage_save(cubelist, filename, save_options)

            # If destination file does not exist then we can save directly.
            else:
                iris.save(cubelist, filename, saver=iris.fileformats.netcdf.save,
                    **save_options)

        except (RuntimeError, IOError, OSError) as exc:
            msg = "Unable to write cubelist to file: " + filename
            self.logger.error(msg)
            self.logger.error(str(exc))
            raise

        except iris.exceptions.ConcatenateError as exc:
            msg = ("Unable to concatenate input cubelist with existing\n"
                "variables in file: " + filename)
            self.logger.error(msg)
            self.logger.error(str(exc))
            raise

    def write(self, *args, **kwargs):
        """
        This is simply a synonym for the :meth:`run` method. It takes the same
        arguments.
        """
        self.run(*args, **kwargs)


def _two_stage_save(cubelist, filename, save_options):
    """
    Perform a two-stage save of a cubelist to an existing file. The cubelist is
    first saved to a temporary file, that file is then copied to the destination
    file. Finally the temporary file is deleted.
    """
    try:
        _fh, tmpfile = tempfile.mkstemp()
        iris.save(cubelist, tmpfile, saver=iris.fileformats.netcdf.save,
            **save_options)

        if filelock:
            try:
                lock = filelock.FileLock(filename)
                with lock.acquire(timeout=5):
                    shutil.copyfile(tmpfile, filename)
            except filelock.Timeout:
                raise OSError("Unable to acquire lock on file " + filename)
        else:
            shutil.copyfile(tmpfile, filename)

    finally:
        os.remove(tmpfile)


def _concatenate_cubes(old_cubes, new_cubes, equalise_attrs=False):
    """
    Perform a smart(er) concatenation operation against two cubelists. The
    old_cubes cubelist is assumed to have been loaded from an existing netCDF
    file, in which case each cube's var_name attribute will, by definition, be
    unique. The new_cubes cubelist is assumed to contain arbitrary cubes, some
    of which may represent the same quantities as contained in old_cubes. The
    intersection, if any, between the two cubelists is determined by examination
    of, among other things, standard_name, long_name, cube dimensionality/shape,
    units, coordinate values, and cell methods.
    """

    for ncube in new_cubes:
        ncoord_names = [c.name() for c in ncube.coords()]

        for ocube in old_cubes:
            # check for same geophysical quantity
            same_quantity = ocube.standard_name == ncube.standard_name
            if not same_quantity:
                same_quantity = ocube.long_name == ncube.long_name
            if not same_quantity:
                continue

            # check for same units
            if ocube.units != ncube.units:
                continue

            # check for same cell methods
            if ocube.cell_methods != ncube.cell_methods:
                continue

            # TODO: check for same cell measures?

            # check for same set of coordinate objects
            ocoord_names = [c.name() for c in ocube.coords()]
            if ocoord_names != ncoord_names:
                continue

            # check for same lat-long (or x-y) coordinate array values
            try:
                nxcoord = ncube.coord(axis='X')
                oxcoord = ocube.coord(axis='X')
                if not _are_coord_arrays_equal(nxcoord, oxcoord): continue
                nycoord = ncube.coord(axis='Y')
                oycoord = ocube.coord(axis='Y')
                if not _are_coord_arrays_equal(nycoord, oycoord): continue
            except iris.exceptions.CoordinateNotFoundError:
                pass

            # equalise attributes on all coordinate objects
            for ocoord in ocube.coords():
                try:
                    ncoord = ncube.coord(ocoord.name())
                    ncoord.var_name = ocoord.var_name
                    if not ncoord.standard_name:
                        ncoord.standard_name = ocoord.standard_name
                    if not ncoord.long_name:
                        ncoord.long_name = ocoord.long_name
                    if hasattr(ocoord, 'circular'):
                        ncoord.circular = ocoord.circular
                except iris.exceptions.CoordinateNotFoundError:
                    pass

            # equalise the cube's name attributes
            ncube.var_name = ocube.var_name
            if not ncube.standard_name:
                ncube.standard_name = ocube.standard_name
            if not ncube.long_name:
                ncube.long_name = ocube.long_name

            # skip any further checks against old_cubes
            break

    cubelist = iris.cube.CubeList(old_cubes + new_cubes)
    if equalise_attrs: equalise_attributes(cubelist)
    cubelist = cubelist.concatenate()

    return cubelist


def _get_iris_save_keywords():
    """
    Return a list of the names of keyword arguments supported by the
    iris.fileformats.netcdf.save() function.
    """

    try:
        # Try to determine keyword arguments via inspection of the save function.
        info = inspect.getfullargspec(iris.fileformats.netcdf.save)
        nargs = len(info[0])
        nkwargs = len(info[3])
        return info[0][nargs-nkwargs:]

    except (AttributeError, TypeError):
        # Otherwise return a best-guess list.
        return ['netcdf_format', 'local_keys', 'unlimited_dimensions', 'zlib',
            'complevel', 'shuffle', 'fletcher32', 'contiguous', 'chunksizes',
            'endian', 'least_significant_digit']


def _are_coord_arrays_equal(coord1, coord2):
    """
    Tests whether or not the points and bounds arrays (if defined) for two
    coordinate objects are equal. The comparison tests are identical to those
    implemented in the iris.coords.Coord class.
    """
    # check the points arrays
    eq = iris.util.array_equal(coord1.points, coord2.points)

    # check the bounds arrays
    if eq:
        if coord1.has_bounds() and coord2.has_bounds():
            eq = iris.util.array_equal(coord1.bounds, coord2.bounds)
        else:
            eq = coord1.bounds is None and coord2.bounds is None

    return eq
