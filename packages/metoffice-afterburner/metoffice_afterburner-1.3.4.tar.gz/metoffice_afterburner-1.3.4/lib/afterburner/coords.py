# (C) British Crown Copyright 2016-2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The afterburner.coords module contains a selection of classes and functions for
creating or manipulating objects pertinent to geospatial coordinates.

**Index of Classes and Functions in this Module**

.. autosummary::
   :nosignatures:

   OSGB36_GCRS_TO_WGS84_GCRS
   OSGB36_PCRS_TO_WGS84_GCRS
   WGS84_GCRS_TO_OSGB36_GCRS
   WGS84_GCRS_TO_OSGB36_PCRS
   CoordRange
   CoordTransformer
   rectangular_region_as_2d_mask
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import re
import operator
import numbers
import numpy as np
import numpy.ma as ma

import cartopy.crs as ccrs
import iris.util
from iris.coords import Coord, CoordExtent

from afterburner.utils import (OpenInterval, LeftOpenInterval,
    LeftClosedInterval, ClosedInterval)

__all__ = ('INTERVAL_CLASS_MAP', 'NUMBER_REGEX', 'INTERVAL_REGEX',
           'OSGB36_GCRS_TO_WGS84_GCRS', 'OSGB36_PCRS_TO_WGS84_GCRS',
           'WGS84_GCRS_TO_OSGB36_GCRS', 'WGS84_GCRS_TO_OSGB36_PCRS',
           'CoordRange', 'CoordTransformer', 'rectangular_region_as_2d_mask')

# Mapping between numeric interval names and the classes that implement them.
INTERVAL_CLASS_MAP = {
    'open': OpenInterval,
    'leftopen': LeftOpenInterval,
    'leftclosed': LeftClosedInterval,
    'closed': ClosedInterval
}

# Regular expression for identifying +/- integers or floating-point numbers.
NUMBER_REGEX = r'[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|[+-]?inf'

# Regular expression for identifying a text-encoded interval definition of the form
# (m,n), (m,n], [m,n) or [m,n], potentially with intervening whitespace.
INTERVAL_REGEX = r'^(\(|\[)\s*(' + NUMBER_REGEX + r')\s*,\s*(' + NUMBER_REGEX + r')(\)|\])'


class CoordRange(object):
    """
    Class for representing a range of coordinate values, possibly non-contiguous,
    to select from a 1-dimensional coordinate axis. Data arrays used to specify
    coordinate axes are commonly monotonic in form, and although the CoordRange
    class does not mandate this, the behaviour is likely to be unpredictable if
    a CoordRange object is used to subset a non-monotonic coordinate axis.

    CoordRange objects store the desired target coordinate values, rather than
    index positions into a coordinate array. In certain application domains
    (the GIS world, for instance) such data values are commonly referred to as
    'world coordinates'.

    The principal use-case for CoordRange objects is to define points or regions
    of interest to extract from a multi-dimensional dataset. For example, one
    might want to subset the data for a single longitude coordinate value or a
    range of contiguous latitude values, as a means of constraining some data
    processing task (such as a spatial averaging operation).

    A coordinate range can be defined in one of the following three ways::

        >>> # As a single coordinate value
        >>> crange = CoordRange(60)
        >>> crange = CoordRange(-273, dtype='float32')   # specific data type requested

        >>> # As a sequence of coordinate values
        >>> crange = CoordRange([0, 2, 4, 6])
        >>> crange = CoordRange((-60.0, -30.0, 0.0, 30.0, 60.0))
        >>> crange = CoordRange(np.arange(0.0, 90.0, 10.0))

        >>> # As a numeric interval (open, left-open, left-closed, or closed)
        >>> crange = CoordRange([1, 10], open=True)
        >>> crange = CoordRange([10, 1], leftopen=True)  # note decreasing range!
        >>> crange = CoordRange([0.0, 360.0], leftclosed=True)
        >>> crange = CoordRange([-90.0, 90.0], closed=True)

    The selection of coordinates <= a particular value, or >= a particular value,
    can be achieved by defining a numeric interval in which either the lower bound
    is set to -infinity or the upper bound is set to +infinity. For example::

        >>> # Select coordinate values <= -23.5
        >>> crange = CoordRange([float('-inf'), -23.5], leftopen=True)
        >>> # Select coordinate values >= 0
        >>> crange = CoordRange([0.0, float('inf')], leftclosed=True)

    Naturally, for coordinate axes which have well-known lower and upper bounds
    - latitude and longitude, for instance - then it's simpler to just use those
    bounds instead of +/- infinity.

    It should be noted that the CoordRange class does not include any special
    intelligence for dealing with circular coordinates, such as longitudes.
    Iris's CoordExtent class may be of utility in such situations (in which case
    the :meth:`as_coord_extent` method may be useful).

    .. note:: CoordRange objects are immutable, at least in as much as the
       :attr:`interval` property (if set) and the :attr:`values` property cannot
       be modified. This is done so as to enable CoordRange objects to be compared
       and hashed (e.g. for dictionary lookups and inclusion within sets).
    """

    def __init__(self, values, dtype=None, **kwargs):
        """
        :param values: Either a single number or a sequence of numbers (which
            should normally be monotonic increasing or decreasing, though this
            is not enforced).
        :param dtype: A Numpy datatype specifier, e.g. 'i4', 'float32'. If not
            set explicitly then the datatype is determined from the type of the
            input value(s).

        Extra Keyword Arguments (`**kwargs`):

        :param bool open: Indicates that the values array defines the end points
            of an open interval, i.e. (m,n). Default = False.
        :param bool leftopen: Indicates that the values array defines the end points
            of a left-open interval, i.e. (m,n]. Default = False.
        :param bool leftclosed: Indicates that the values array defines the end points
            of a left-closed interval, i.e. [m,n). Default = False.
        :param bool closed: Indicates that the values array defines the end points
            of a closed interval, i.e. [m,n]. Default = False.

        :raises ValueError: Raised if the ``values`` argument is invalid.
        """

        # Initialise interval indicator flags to false.
        for arg in INTERVAL_CLASS_MAP:
            setattr(self, arg, kwargs.get(arg, False))

        # Convert input values to a numpy array.
        if isinstance(values, (numbers.Number, np.number)):
            values = np.array([values], dtype=dtype)
        elif not isinstance(values, np.ndarray):
            values = np.array(values, dtype=dtype)
        elif dtype:
            values = values.astype(dtype)

        # Set to an instance of a subclass of afterburner.utils.NumericInterval
        # if the coordinate range is defined as an interval.
        self._interval = None

        # Check to see if an interval was defined.
        if any([self.open, self.leftopen, self.leftclosed, self.closed]):
            if len(values) != 2:
                raise ValueError("CoordRange: The 'values' argument must be a "
                    "length-2 sequence when defining an interval.")
            for interval_type, cls in INTERVAL_CLASS_MAP.items():
                if getattr(self, interval_type):
                    self._interval = cls(values[0], values[1])
                    break

        # A read-only Numpy array representation of the coordinate range value(s).
        self._values = values
        self._values.flags.writeable = False

    def __eq__(self, other):
        """
        Compare this object for equality with other. The objects compare equal
        if the following items on both objects are all equal: the interval type
        (which might be None), the data type of the values array, and the
        array values themeselves.

        :param CoordRange other: The CoordRange object to compare with this object.
        :returns: True if the objects are equal, else False.
        """
        return (type(self.interval) is type(other.interval) and
                self.values.dtype == other.values.dtype and
                np.array_equal(self.values, other.values))

    def __hash__(self):
        """
        Return a hash value for this object. The hash value is derived from the
        interval type (which might be None), the array data type, and the array
        data values, converted to a string. The latter operation may be slow for
        very large arrays (which is unlikely for a set of coordinates).

        :returns: A hash key for this object.
        """
        return hash((self.interval.__class__.__name__, str(self.values.dtype),
            self.values.tostring()))

    @property
    def interval(self):
        """
        An instance of a subclass of :class:`afterburner.utils.NumericInterval`
        if the coordinate range is defined as an interval, otherwise None.
        """
        return self._interval

    @property
    def points(self):
        """An alias for the :attr:`values` property (for Iris users!)."""
        return self.values

    @property
    def values(self):
        """A read-only Numpy array representing the coordinate range."""
        return self._values

    @staticmethod
    def from_string(strval, dtype=None):
        """
        Create a CoordRange object from a text string. The following forms are
        recognised:

        * a single integer, e.g. '42'
        * a single floating point number, e.g. '2.718'
        * a comma-separated list of numeric values, e.g. '0,1,3,5,7,9'
        * an interval definition, e.g. '[0,10)'

        Note that the list-of-values form should NOT include enclosing '(...)'
        or '[...]' characters as these are used to indicate intervals.

        Interval definitions may contain +/- infinity, for example '[0,inf)',
        '[10,+inf)', '(-inf,32)', or even '(-inf,+inf)'!

        :param str strval: A text string containing a coordinate range definition.
        :param dtype: A Numpy datatype specifier, e.g. 'i4', 'float32'. If not
            set explicitly then the datatype is determined from the type of the
            value(s) in ``strval``.
        """

        # If strval contains a ',' then it must represent either a list of values
        # or an interval definition.
        if ',' in strval:

            # Check for an interval definition.
            mtch = re.search(INTERVAL_REGEX, strval)
            if mtch:
                try:
                    start = int(mtch.group(2))
                    end = int(mtch.group(3))
                except ValueError:
                    start = float(mtch.group(2))
                    end = float(mtch.group(3))
                values = [start, end]
                itype = mtch.group(1) + mtch.group(4)
                if itype == '()':
                    return CoordRange(values, dtype=dtype, open=True)
                elif itype == '(]':
                    return CoordRange(values, dtype=dtype, leftopen=True)
                elif itype == '[)':
                    return CoordRange(values, dtype=dtype, leftclosed=True)
                else:
                    return CoordRange(values, dtype=dtype, closed=True)

            # Try decoding a list of numbers.
            else:
                try:
                    values = [int(x) for x in strval.split(',')]
                except ValueError:
                    values = [float(x) for x in strval.split(',')]
                return CoordRange(values, dtype=dtype)

        # Otherwise, try decoding a single integer or real number.
        else:
            value = None
            for func in (int, float):
                try:
                    value = func(strval)
                    break
                except ValueError:
                    pass

            if value is not None:
                return CoordRange(value, dtype=dtype)
            else:
                raise ValueError("Invalid coordinate range definition: %r", strval)

    def is_interval(self):
        """
        Returns True if the coordinate range represents a numeric interval.
        """
        return self.interval is not None

    def contains(self, value, rtol=1e-05, atol=1e-08):
        """
        Returns True if the specified value is contained within the coordinate
        range's value set.

        :param value: The number to test for containment.
        :param float rtol: Passed to numpy.isclose() function if the coordinate
            range is defined as a sequence of floating-point numbers.
        :param float atol: Passed to numpy.isclose() function if the coordinate
            range is defined as a sequence of floating-point numbers.
        """
        if self.is_interval():
            return self.interval.contains(value)
        else:
            if self.values.dtype.kind == 'i':
                return value in self.values
            else:
                return any(np.isclose(value, self.values, rtol=rtol, atol=atol))

    def as_coord_extent(self, name_or_coord):
        """
        Convert an interval-based coordinate range to an ``iris.coords.CoordExtent``
        object.

        :param str name_or_coord: Either the name of a coordinate (e.g. 'latitude')
            or an instance of a subclass of iris.coords.Coord. This argument is
            simply passed through to the init method of the ``iris.coords.CoordExtent``
            class.
        :raises TypeError: Raised if the current CoordRange object is not based
            on a numeric interval.
        """
        if not self.is_interval():
            raise TypeError("CoordRange object is not based on a numeric interval.")

        if self.open:
            min_inclusive, max_inclusive = False, False
        elif self.leftopen:
            min_inclusive, max_inclusive = False, True
        elif self.leftclosed:
            min_inclusive, max_inclusive = True, False
        elif self.closed:
            min_inclusive, max_inclusive = True, True

        if self.interval.ascending:
            minimum, maximum = self.values[0], self.values[1]
        else:
            # swap values for descending intervals
            minimum, maximum = self.values[1], self.values[0]
            min_inclusive, max_inclusive = max_inclusive, min_inclusive

        return CoordExtent(name_or_coord, minimum, maximum, min_inclusive, max_inclusive)


class CoordTransformer(object):
    """
    Class for transforming coordinates from a source coordinate reference system
    to a target coordinate reference system, both of which are objects of type
    `cartopy.crs.CRS <https://scitools.org.uk/cartopy/docs/latest/crs/index.html>`_

    The :meth:`transform` method provides a unified mechanism for invoking
    cartopy's ``CRS.transform_point()`` or ``CRS.transform_points()`` methods, the
    choice of which to use being determined by the type of the input coordinates
    - plain numbers or arrays.

    The current module provides pre-canned CoordTransformer objects for a small
    number of a popular coordinate transformations, as follows:

    * :data:`OSGB36_GCRS_TO_WGS84_GCRS`
    * :data:`OSGB36_PCRS_TO_WGS84_GCRS`
    * :data:`WGS84_GCRS_TO_OSGB36_GCRS`
    * :data:`WGS84_GCRS_TO_OSGB36_PCRS`

    Here's an example of how you might create a CoordTransformer object that
    could be used to transform lat/long coordinates from the OSNI 1952 datum
    to the WGS 1984 datum:

    >>> source_crs = ccrs.Geodetic(ccrs.Globe(ellipse='airy',
    ...     semimajor_axis=6377563.396, inverse_flattening=299.3249646,
    ...     towgs84='482.5,-130.6,564.6'))   # 3-parameter transformation
    >>> target_crs = ccrs.Geodetic(ccrs.Globe(datum='WGS84'))
    >>> osni52_wgs84 = CoordTransformer(source_crs, target_crs, 'OSNI 1952 to WGS 1984')
    >>> lon, lat = osni52_wgs84.transform(-5.9301, 54.5973)   # Belfast city location
    >>> np.round([lon, lat], 4).tolist()
    [-5.9313, 54.5973]

    .. note:: Most transformation operations between different geodetic datums
       yield approximate results. Depending on the datums involved, the accuracy
       of a coordinate transformation will typically be of the order of a few
       metres to a few tens of metres. This should be acceptable for most climate
       and weather applications.
    """

    def __init__(self, source_crs, target_crs, name):
        """
        :param cartopy.crs.CRS source_crs: The source coordinate reference system.
        :param cartopy.crs.CRS target_crs: The target coordinate reference system.
        :param str name: A descriptive name for the coordinate transformation,
            e.g. 'OSGB 1936 lat/long to WGS 1984 lat/long'.
        """
        self._source_crs = source_crs
        self._target_crs = target_crs
        self._name = name

    def __str__(self):
        """Returns the name of the coordinate transformation."""
        return self.name

    @property
    def source_crs(self):
        """Source coordinate reference system (read-only)."""
        return self._source_crs

    @property
    def target_crs(self):
        """Target coordinate reference system (read-only)."""
        return self._target_crs

    @property
    def name(self):
        """Descriptive name for the coordinate transformation (read-only)."""
        return self._name

    def transform(self, xcoords, ycoords, zcoords=None):
        """
        Transform one or more coordinate tuples from the source CRS to the target
        CRS. Depending on the type of the source and target CRS's the input and
        output coordinates may be either geodetic latitude-longitude coordinates
        or projected X-Y coordinates.

        .. note:: The input coordinates are assumed to fall within the valid
           range associated with the source CRS. For example, -90 to 90 degrees
           in the case of latitude coordinates. No range-checking is carried out
           by the ``transform`` method itself.

        Example call using single coordinate values:

        >>> lon, lat = OSGB36_GCRS_TO_WGS84_GCRS.transform(-3.4737, 50.7267)
        >>> np.round([lon, lat], 4).tolist()
        [-3.4749, 50.7273]

        Example call using coordinate arrays:

        >>> lons = np.linspace(0., 10., 5, endpoint=False)
        >>> lats = np.linspace(50., 60., 5, endpoint=False)
        >>> lon_lat_ht = OSGB36_GCRS_TO_WGS84_GCRS.transform(lons, lats)
        >>> lon_lat_ht.shape
        (5, 3)

        :param xcoords: A single longitude or X coordinate value in the source CRS,
            or a numpy array of such values.
        :param ycoords: A single latitude or Y coordinate value in the source CRS,
            or a numpy array of such values.
        :param zcoords: An optional numpy array of vertical coordinate values. If
            defined then the array shape must match that of the x and y arrays.
        :returns: A (longitude, latitude) or (x, y) tuple in the target CRS if
            single coordinate values are input, or a numpy array of shape
            ``x.shape + (3,)`` if coordinate arrays are input. Each 'row' in the
            returned array comprises the values (longitude, latitude, height) or
            (x, y, height).
        :raises ValueError: Raised if the input arguments comprise a mixture of
            numbers and arrays.
        """

        inputs = [xcoords, ycoords, zcoords] if zcoords else [xcoords, ycoords]

        if _all_ndarrays(inputs):
            return self.target_crs.transform_points(self.source_crs, xcoords,
                ycoords, z=zcoords)

        elif _all_numbers(inputs):
            return self.target_crs.transform_point(xcoords, ycoords, self.source_crs)

        else:
            raise ValueError("Arguments must be all numbers or all numpy arrays.")


# Define a WGS 1984 geodetic coordinate system object.
WGS84_GCRS = ccrs.Geodetic(ccrs.Globe(datum='WGS84'))

# Define an OSGB 1936 projected coordinate system object, set its 'towgs84' attribute,
# and obtain a handle to the associated geodetic coordinate system object.
OSGB36_TO_WGS84_PARAMS = [446.448, -125.157, 542.06, 0.1502, 0.247, 0.8421, -20.4894]
OSGB36_PCRS = ccrs.OSGB()
OSGB36_PCRS.globe.towgs84 = ','.join([str(_x) for _x in OSGB36_TO_WGS84_PARAMS])
OSGB36_GCRS = OSGB36_PCRS.as_geodetic()

#: Defines a :class:`CoordTransformer` object for transforming from OSGB 1936
#: lat-long coordinates to WGS 1984 lat-long coordinates.
OSGB36_GCRS_TO_WGS84_GCRS = CoordTransformer(OSGB36_GCRS, WGS84_GCRS,
    'OSGB 1936 latitude-longitude to WGS 1984 latitude-longitude')

#: Defines a :class:`CoordTransformer` object for transforming from OSGB 1936
#: projected X-Y coordinates (Transverse Mercator) to WGS 1984 lat-long coordinates.
OSGB36_PCRS_TO_WGS84_GCRS = CoordTransformer(OSGB36_PCRS, WGS84_GCRS,
    'OSGB 1936 projected X-Y to WGS 1984 latitude-longitude')

#: Defines a :class:`CoordTransformer` object for transforming from WGS 1984
#: lat-long coordinates to OSGB 1936 lat-long coordinates.
WGS84_GCRS_TO_OSGB36_GCRS = CoordTransformer(WGS84_GCRS, OSGB36_GCRS,
    'WGS 1984 latitude-longitude to OSGB 1936 latitude-longitude')

#: Defines a :class:`CoordTransformer` object for transforming from WGS 1984
#: lat-long coordinates to OSGB 1936 projected X-Y coordinates (Transverse Mercator).
WGS84_GCRS_TO_OSGB36_PCRS = CoordTransformer(WGS84_GCRS, OSGB36_PCRS,
    'WGS 1984 latitude-longitude to OSGB 1936 projected X-Y')


def rectangular_region_as_2d_mask(coord_extents, cube=None, ignore_bounds=False):
    """
    Create a 2D masked array representation of the rectangular geographical
    region defined by two iris.coords.CoordExtent objects. The masked array so
    created could, for example, be element-wise combined with other like-shaped
    masks in order to constrain the spatial extent of an operation applied to a
    cube or sequence of cubes.

    The coordinate axes referenced by the CoordExtent objects are assumed to be
    orthogonal, such as geodetic latitude and longitude or grid latitude and
    longitude. Both must be dimension coordinates; that is, they should be
    1-dimensional and monotonic increasing.

    The resulting 2D masked array has the combined dimensions of the two input
    coordinate axes, i.e. (nlat, nlon) in the case of latitude and longitude
    coordinates. Masked array elements are assigned the value 0, while unmasked
    elements are assigned the value 1.

    In the case of cyclic coordinate axes, such as longitude, an attempt is made
    to take account of the fact that the specified extent for the axis might be
    shifted relative to the actual coordinate points (and bounds) comprising the
    axis. The magnitude of the shift will be +/- the modulus value defined for
    the axis, e.g. 360 in the case of a longitude axis.

    :param list coord_extents: A length-2 iterable of iris.coords.CoordExtent
        objects which define the coordinate axes that will be used to generate
        the regional mask. If either CoordExtent object references a coordinate
        by name, then the ``cube`` argument must be specified.
    :param iris.cube.Cube cube: An Iris cube that will be used as the source of
        any coordinate objects mentioned by name in either of the CoordExtent
        objects. If the latter reference actual coordinate objects (i.e. instances
        of iris.coords.DimCoord) then a cube object does not need to be passed in.
    :param bool ignore_bounds: If set to true then all coordinate comparison
        operations (to test for points in/outside the region) are performed
        against coordinate point locations rather than cell boundaries. If the
        latter are not present then they must necessarily be ignored. (This
        argument mirrors the argument of the same name and behaviour as used by
        the ``cube.intersection()`` method.)
    :returns: A masked array having shape [len(coord1), len(coord2)]. Masked
        array elements indicate locations *outside* the region and are assigned
        the value 0. Unmasked elements indicate locations *inside* the region
        and are assigned the value 1. The array datatype is np.int8.
    :raises ValueError: Raised either if ``coord_extents`` is not a length-2
        iterable, or if the ``cube`` argument is required but has not been
        defined.
    """

    if len(coord_extents) != 2:
        msg = ("Invalid number of CoordExtent objects specified. "
            "Expected 2. Got {0}.".format(len(coord_extents)))
        raise ValueError(msg)

    # Create 1D masked arrays from each coordinate referenced by the passed in
    # coordinate extents.
    coord_masks = []
    for cex in coord_extents:

        if isinstance(cex.name_or_coord, Coord):
            coord = cex.name_or_coord
        elif cube is not None:
            coord = cube.coord(cex.name_or_coord)
        else:
            msg = ("A CoordExtent object references a coordinate named '{0}',\nbut "
                "no cube was specified in which to look up that coordinate.".format(
                cex.name_or_coord))
            raise ValueError(msg)

        # Check to see if the current coordinate is an X axis, i.e. longitude.
        # If it is then it may be necessary to do an additional cyclicity test
        # using the input extent shifted by +/- 360 degrees.
        axis = iris.util.guess_coord_axis(coord)
        if axis == 'X':
            do_cyclic_check = False
            if cex.minimum < coord.points[0]:
                cex_min = cex.minimum + coord.units.modulus
                cex_max = cex.maximum + coord.units.modulus
                do_cyclic_check = True
            elif cex.maximum > coord.points[-1]:
                cex_min = cex.minimum - coord.units.modulus
                cex_max = cex.maximum - coord.units.modulus
                do_cyclic_check = True

        # Define comparison operators according to the min_inclusive/max_inclusive
        # attributes attached to the passed-in coordinate extents.
        min_op = operator.ge if cex.min_inclusive else operator.gt
        max_op = operator.le if cex.max_inclusive else operator.lt

        if ignore_bounds or not coord.has_bounds():
            pnts = coord.points
            marr = np.where(min_op(pnts, cex.minimum) & max_op(pnts, cex.maximum),
                1, 0)
            # If required, do an additional check for cyclic coordinates.
            if axis == 'X' and do_cyclic_check:
                marr = np.where(min_op(pnts, cex_min) & max_op(pnts, cex_max),
                    1, marr)
        else:
            pnts = coord.points
            min_bnds = coord.bounds[:,0]
            max_bnds = coord.bounds[:,1]
            marr = np.where(min_op(max_bnds, cex.minimum) & max_op(min_bnds, cex.maximum),
                1, 0)
            # If required, do an additional check for cyclic coordinates.
            if axis == 'X' and do_cyclic_check:
                marr = np.where(min_op(max_bnds, cex_min) & max_op(min_bnds, cex_max),
                    1, marr)

        # Mask out 0-valued array elements and convert array to int8 (byte) type.
        marr = ma.masked_equal(marr, 0)
        marr = marr.astype(np.int8)
        coord_masks.append(marr)

    # Return the product of the two 1D coordinate masks.
    a1, a2 = coord_masks[:]
    masked_array = a1[:,None] * np.repeat(a2[None,:], a1.size, axis=0)
    masked_array.data[masked_array.mask] = 0

    return masked_array


def _all_ndarrays(items):
    """Returns true if all elements in items are numpy ndarray objects."""
    return all([isinstance(x, np.ndarray) for x in items])


def _all_numbers(items):
    """Returns true if all elements in items are subtypes of numpy.number."""
    return all([np.issubdtype(type(x), np.number) for x in items])
