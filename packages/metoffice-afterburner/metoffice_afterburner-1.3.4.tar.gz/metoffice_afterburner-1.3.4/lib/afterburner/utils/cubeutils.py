# (C) British Crown Copyright 2016-2023, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Various utility functions that work with Iris cubes and cubelists.

**Index of Functions in this Module**

.. autosummary::
   :nosignatures:

   add_decade_aux_coord
   add_model_decade_aux_coord
   add_multi_year_aux_coord
   are_data_shapes_equal
   are_time_axes_equal
   augment_cube_class
   calc_area_weights
   compare_cubes
   convert_aux_coord_to_dim_coord
   extract_lat_long_region
   extract_time_slice
   find_lat_long_coords
   get_earliest_time_datum
   guess_aggregation_period
   has_global_domain
   is_circular
   is_mean_of_all_time_steps
   is_scalar_coord
   is_time_mean
   is_time_maximum
   is_time_minimum
   make_calendar_type_cube_func
   make_cell_method_cube_func
   rebase_time_coords
   set_history_attribute
   vsummary
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import create_bound_method, create_unbound_method, string_types

import sys
import datetime
import numpy as np
import cf_units as cfu

try:
    import cftime as cft
except ImportError:
    import netcdftime as cft

import iris
import iris.coords
import iris.exceptions

import afterburner
from afterburner.utils import _cubecomp
from afterburner.coords import CoordRange


def add_decade_aux_coord(cube, time_coord, name='decade'):
    """
    Add a decade auxiliary 'categorical' coordinate to the specified cube. In
    this case 'decade' means the familiar 10-year periods commencing at midnight
    Jan 1 on years that are whole multiples of 10, e.g. 1970-1980, 1980-1990,
    and so on.

    The newly created auxiliary coordinate comprises an integer array of year
    numbers representing the *mid-point* of the decade, e.g. [1975, 1985, ...].
    The month and day numbers are implicit (both being equal to 1).

    The :func:`add_model_decade_aux_coord` function provides a convenient mechanism
    for generating a categorical coordinate based on model decades (i.e. offset
    from midnight Dec 1).

    :param iris.cube.Cube cube: The cube on which to attach a 'decade' auxiliary
        coordinate.
    :param str time_coord: The name of the cube's time coordinate, or an instance
        of iris.coords.DimCoord.
    :param str name: The name to give to the new decade coordinate.
    :raises ValueError: Raised if the input cube already possesses a coordinate
        (of any type) with the given name.
    """

    if name in [c.name() for c in cube.coords()]:
        raise ValueError("A coordinate named '{0}' already exists on the "
            "input cube.".format(name))

    if isinstance(time_coord, iris.coords.Coord):
        tcoord = time_coord
    else:
        tcoord = cube.coord(time_coord)

    tunits = tcoord.units
    dates = tunits.num2date(tcoord.points)

    mid_decade = [x.year // 10 * 10 + 5 for x in dates]
    mid_decade = np.array(mid_decade, dtype=np.int32)

    decade_coord = iris.coords.AuxCoord(mid_decade, long_name=name, var_name=name,
        units='1')
    cube.add_aux_coord(decade_coord, cube.coord_dims(time_coord))


def add_model_decade_aux_coord(cube, time_coord, name='model_decade', ref_date=None):
    """
    Add a model decade auxiliary 'categorical' coordinate to the specified cube.
    In this case 'model decade' means the 10-year periods whose start and end
    dates are offset from the specified reference date by whole multiples of 10
    years. For example, 1969-12-01 to 1979-12-01, 1979-12-01 to 1989-12-01, and
    so on.

    The newly created auxiliary coordinate comprises an integer array of ordinal
    dates representing the *mid-point* of the decade, e.g. [19741201, 19841201, ...]

    The :func:`add_decade_aux_coord` function provides a convenient mechanism
    for generating a categorical coordinate consisting of regular decades, i.e.
    ones aligned with the standard calendar year, rather than the climate model
    year.

    :param iris.cube.Cube cube: The cube on which to attach a 'model_decade'
        auxiliary coordinate.
    :param str time_coord: The name of the cube's time coordinate, or an instance
        of iris.coords.DimCoord.
    :param str name: The name to give to the new model decade coordinate.
    :param datetime ref_date: The reference date (as a datetime-like object)
        used to determine the start (ergo end) dates of consecutive time periods.
        If undefined then a default reference date of 1859-12-01 is used.
    :raises ValueError: Raised if the input cube already possesses a coordinate
        (of any type) with the given name.
    """

    if name in [c.name() for c in cube.coords()]:
        raise ValueError("A coordinate named '{0}' already exists on the "
            "input cube.".format(name))

    if not ref_date:
        ref_date = cft.datetime(1859, 12, 1, 0, 0, 0)

    ref_date_units = "days since {0:04d}-{1:02d}-{2:02d}".format(ref_date.year,
        ref_date.month, ref_date.day)

    if isinstance(time_coord, iris.coords.Coord):
        tcoord = time_coord
    else:
        tcoord = cube.coord(time_coord)

    tunits = tcoord.units
    xunits = cfu.Unit(ref_date_units, calendar=tunits.calendar)
    xcoord = tcoord.copy()
    xcoord.convert_units(xunits)

    mid_decade = np.zeros(len(xcoord.points), dtype=np.int32)
    ndays_per_decade = _num_days_per_year(tunits.calendar) * 10

    for iy, ndays in enumerate(xcoord.points):
        ndecades = int(ndays // ndays_per_decade)
        mid_year = ref_date.year + ndecades * 10 + 5
        mid_decade[iy] = (mid_year * 10000) + (ref_date.month * 100) + ref_date.day

    decade_coord = iris.coords.AuxCoord(mid_decade, long_name=name, var_name=name,
        units='1')
    cube.add_aux_coord(decade_coord, cube.coord_dims(time_coord))


def add_multi_year_aux_coord(cube, time_coord, num_years, name='multi_year',
        ref_date=None, add_bounds=False):
    """
    Add a multi-year auxiliary 'categorical' coordinate to the specified cube.
    The newly created coordinate comprises an integer array of ordinal dates
    representing the *approximate* mid-point of each time period having length
    ``num_years`` years (relative to the origin defined by the reference date).

    In the case of a 30-year time period, for example, the mid-points, assuming
    a 1970-01-01 reference date, might be [19850101, 20150101, 20450101, ...].
    Using the default reference date, 1859-12-01, the categorical coordinates
    might be [18741201, 19041201, 19341201, ...]. If ``num_years`` is odd then
    the mid-point year is truncated down to the nearest integer.

    The month and day components are always equal to the respective values taken
    from the reference date, hence the reason why the categorical coordinate is
    only an *approximate* mid-point. For the purposes of aggregation-over-time
    operations the exact coordinate value is largely immaterial.

    Multiple time coordinates falling within the same time period would, of course,
    have the same value in the new categorical coordinate axis.

    :param iris.cube.Cube cube: The cube on which to attach a 'multi_year'
        auxiliary coordinate.
    :param str time_coord: The name of the cube's time coordinate, or an instance
        of iris.coords.DimCoord.
    :param int num_years: The length of the time period in whole years.
    :param str name: The name to give to the new auxiliary coordinate. It will
        often be useful to specify a name which indicates the length of the time
        period, e.g. '25_years', 'fifty_years', etc.
    :param datetime ref_date: The reference date (as a datetime-like object)
        used to determine the start (ergo end) dates of consecutive time periods.
        If undefined then a default reference date of 1859-12-01 is used.
    :param bool add_bounds: If set to true then bounds are added to the newly
        created auxiliary coordinate.
    :raises ValueError: Raised if the input cube already possesses a coordinate
        (of any type) with the given name.
    """

    if name in [c.name() for c in cube.coords()]:
        raise ValueError("A coordinate named '{0}' already exists on the "
            "input cube.".format(name))

    if not ref_date:
        ref_date = cft.datetime(1859, 12, 1, 0, 0, 0)

    ref_date_units = "days since {0:04d}-{1:02d}-{2:02d}".format(ref_date.year,
        ref_date.month, ref_date.day)

    if isinstance(time_coord, iris.coords.Coord):
        tcoord = time_coord
    else:
        tcoord = cube.coord(time_coord)

    tunits = tcoord.units
    xunits = cfu.Unit(ref_date_units, calendar=tunits.calendar)
    xcoord = tcoord.copy()
    xcoord.convert_units(xunits)
    ndays_per_period = _num_days_per_year(tunits.calendar) * num_years

    mid_points = np.zeros(len(xcoord.points), dtype=np.int32)
    if add_bounds:
        bnds = np.zeros([len(xcoord.points),2], dtype=np.int32)
    else:
        bnds = None

    for iy, ndays in enumerate(xcoord.points):
        nperiods = int(ndays // ndays_per_period)
        stt_year = ref_date.year + (nperiods * num_years)
        mid_year = stt_year + (num_years // 2)
        end_year = stt_year + num_years
        mid_points[iy] = (mid_year * 10000) + (ref_date.month * 100) + ref_date.day
        if add_bounds:
            bnds[iy,0] = (stt_year * 10000) + (ref_date.month * 100) + ref_date.day
            bnds[iy,1] = (end_year * 10000) + (ref_date.month * 100) + ref_date.day

    aux_coord = iris.coords.AuxCoord(mid_points, long_name=name, var_name=name,
        units='1', bounds=bnds)
    cube.add_aux_coord(aux_coord, cube.coord_dims(time_coord))


def data_shapes_equal(cubelist):
    """
    This function has been deprecated. Please use :func:`are_data_shapes_equal`
    instead.
    """
    return are_data_shapes_equal(cubelist)


def are_data_shapes_equal(cubelist):
    """
    Test to see if the data payload of all cubes in ``cubelist`` have the same
    shape.

    :param iris.cube.CubeList cubelist: The list of cubes to test.
    :returns: True if all the cubes have the same shape, else False.
    :raises ValueError: Raised if the input ``cubelist`` is empty.
    """
    if not cubelist:
        raise ValueError("Empty cubelist specified.")

    for cube in cubelist[1:]:
        if cube.shape != cubelist[0].shape: return False

    return True


def are_time_axes_equal(cubelist, coord_name='time'):
    """
    Test to see if all of the cubes in ``cubelist`` have equivalent time axes,
    after converting time coordinates to a common reference date if required.
    Iris does not perform the latter step if one applies a straightforward
    equality test against two coordinate objects.

    :param iris.cube.CubeList cubelist: The list of cubes whose time axes are to
        be examined.
    :param str coord_name: The name of the time coordinate to check.
    :returns: True if all time axes are equivalent, else False.
    :raises ValueError: Raised if the input ``cubelist`` is empty.
    :raises iris.exceptions.CoordinateNotFoundError: Raised if a time coordinate
        is absent from any of the input cubes.
    """
    if not cubelist:
        raise ValueError("Empty cubelist specified.")

    tcoord0 = cubelist[0].coord(coord_name)
    tunits0 = tcoord0.units

    for cube in cubelist[1:]:
        tcoord = cube.coord(coord_name)
        if tcoord == tcoord0:
            # time axes are identical so skip to next cube
            continue
        elif tcoord.units.is_convertible(tunits0):
            # time units differ but are inter-convertible
            _coord = tcoord.copy()
            _coord.convert_units(tunits0)
            if _coord != tcoord0:
                return False
        else:
            # time axes are unequal and not inter-convertible
            return False

    return True


def calc_area_weights(cube):
    """
    Calculate area weights for the specified cube. If a cell measure named 'area'
    is present then the data array associated with that cell measure is used to
    provide the area weights. Otherwise the area weights are computed using the
    ``iris.analysis.cartography.area_weights()`` function.

    :param iris.cube.Cube cube: The Iris cube for which to calculate area weights.
    :returns: An array of area weights, the shape of which is broadcast, if need
        be, to match that of the input cube.
    :raises ValueError: Raised by Iris < 3.4 if an attempt is made to calculate area
        weights for a cube that has multi-dimensional horizontal coordinates.
    """

    # First check to see if the cube possesses a cell measure named 'area'.
    area_cms = None
    if hasattr(cube, 'cell_measures'):
        area_cms = [cm for cm in cube.cell_measures() if cm.measure == 'area']

    # If an area cell measure is present then broadcast its associated data
    # array to match the shape of the host cube.
    if area_cms:
        area = area_cms[0]
        cm_dims = cube.cell_measure_dims(area)
        weights = iris.util.broadcast_to_shape(area.data, cube.shape, cm_dims)

    # If not then try the usual method of generating weights from the latitude
    # and longitude axes (which must be full dimension coords, not aux coords).
    else:
        weights = iris.analysis.cartography.area_weights(cube)

    return weights


def convert_aux_coord_to_dim_coord(cube, coord_name):
    """
    Convert the type of a cube's auxiliary coordinate from iris.coords.AuxCoord
    to iris.coords.DimCoord.

    The cubes loaded by Iris from some netCDF files can have coordinates set as
    auxiliary coordinates with type ``iris.coords.AuxCoord`` rather than
    dimension coordinates, which are 1d, numeric and monotonic auxiliary
    coordinates with type ``iris.coords.DimCoord``. This can prevent cubes
    loaded from netCDF files from being concatenated with other cubes. This
    function modifies the cube in situ to ensure that the specified coordinate
    is set as a dimension coordinate. If the coordinate is already a dimension
    coordinate then it's ignored. If the coordinate doesn't exist then an
    exception is raised.

    :param iris.cube.Cube cube: The cube to fix.
    :param str coord_name: The name of the coordinate to fix.
    :raises iris.exceptions.CoordinateNotFoundError: If ``cube`` does not
        have a coordinate called ``coord_name``.

    .. seealso:: The `iris.util.promote_aux_coord_to_dim_coord() <https://scitools.org.uk/iris/docs/latest/iris/iris/util.html#iris.util.promote_aux_coord_to_dim_coord>`_
       function which post-dated the current function.
    """
    coord_to_fix = cube.coord(coord_name)
    if isinstance(coord_to_fix, iris.coords.AuxCoord):
        cube.remove_coord(coord_name)
        dim_coord = iris.coords.DimCoord.from_coord(coord_to_fix)
        cube.add_aux_coord(dim_coord, 0)


def extract_lat_long_region(cube, lat_extent, lon_extent, ignore_bounds=False):
    """
    Extract a regional subset of data from the specified cube. The coordinate
    ranges defined via the lat_extent and lon_extent arguments are compared
    directly to the corresponding cube coordinate objects; no transformation of
    coordinates (e.g. from a rotated pole coordinate system) is undertaken.

    :param lat_extent: An instance object of type iris.coords.CoordExtent or
        afterburner.coords.CoordRange defining the latitude extent/range.
    :param lon_extent: An instance object of type iris.coords.CoordExtent or
        afterburner.coords.CoordRange defining the longitude extent/range.
    :param iris.cube.Cube cube: The cube from which to extract a regional subset.
    :param bool ignore_bounds: If set to true then any cell bounds attached to
        the lat/long coordinate axes will be ignored.
    :returns: An Iris cube containing the regional extract. If no data points
        fall within the specified region then the return value is None.
    :raises iris.exceptions.CoordinateNotFoundError: Raised if suitable latitude
        and/or longitude coordinate objects could not be found on the input cube.
    """

    if isinstance(lat_extent, CoordRange):
        try:
            # check for a 'latitude' dimension coordinate
            lat_coord = cube.coord('latitude', dim_coords=True)
        except iris.exceptions.CoordinateNotFoundError:
            try:
                # check for a 'grid_latitude' dimension coordinate
                lat_coord = cube.coord('grid_latitude', dim_coords=True)
            except iris.exceptions.CoordinateNotFoundError:
                # check for a 'latitude' auxiliary coordinate
                lat_coord = cube.coord('latitude', dim_coords=False)
        lat_extent = lat_extent.as_coord_extent(lat_coord)

    if isinstance(lon_extent, CoordRange):
        try:
            # check for a 'longitude' dimension coordinate
            lon_coord = cube.coord('longitude', dim_coords=True)
        except iris.exceptions.CoordinateNotFoundError:
            try:
                # check for a 'grid_longitude' dimension coordinate
                lon_coord = cube.coord('grid_longitude', dim_coords=True)
            except iris.exceptions.CoordinateNotFoundError:
                # check for a 'longitude' auxiliary coordinate
                lon_coord = cube.coord('longitude', dim_coords=False)
        lon_extent = lon_extent.as_coord_extent(lon_coord)

    return cube.intersection(lon_extent, lat_extent, ignore_bounds=ignore_bounds)


def extract_time_slice(cube, datetime_range, coord_name='time'):
    """
    Extract a time slice of data from a cube. Data points in the input cube are
    selected where: datetime_range.start <= t < datetime_range.end.

    :param iris.cube.Cube cube: The cube from which to extract a time slice.
    :param DateTimeRange datetime_range: The date-time range of the data to
        extract. The argument value should either be an instance object of type
        :class:`afterburner.utils.dateutils.DateTimeRange`, or else a length-2
        iterable of strings defining the start and end date-times in ISO 8601 or
        CF format.
    :param str coord_name: The name of the time coordinate.
    :returns: The desired subset of ``cube``, or None if no data falls within
        the specified date-time range.
    :raises iris.exceptions.CoordinateNotFoundError: Raised if the specified
        time coordinate is not present on the passed-in cube.
    """
    from afterburner.utils.dateutils import DateTimeRange

    # Raise an exception if the cube does not have a time coordinate.
    try:
        _tcoord = cube.coord(coord_name)
    except:
        msg = "Cube does not contain a coordinate named '{0}'.".format(coord_name)
        raise iris.exceptions.CoordinateNotFoundError(msg)

    if isinstance(datetime_range, (list, tuple)):
        datetime_range = DateTimeRange(*datetime_range)
    elif not isinstance(datetime_range, DateTimeRange):
        raise ValueError("extract_time_slice: datetime_range argument must be "
            "of type DateTimeRange, or an iterable of date-time strings.")

    time_cons = iris.Constraint(coord_values={coord_name:
        lambda cell: datetime_range.start_ncdt <= cell.point < datetime_range.end_ncdt})
    futures = afterburner.compare_iris_version('2', 'lt') and \
        {'cell_datetime_objects': True} or {}
    with iris.FUTURE.context(**futures):
        subcube = cube.extract(time_cons)

    return subcube


def find_lat_long_coords(cube):
    """
    Return the latitude and longitude coordinates associated with the specified
    cube. Typically these will be the coordinates named 'latitude' and 'longitude'.
    In the case of rotated pole datasets, however, the coordinates will be named
    'grid_latitude' and 'grid_longitude'. The search order is as follows:

    1. Dimension coordinates named 'latitude' and 'longitude'
    2. Dimension coordinates named 'grid_latitude' and 'grid_longitude'
    3. Auxiliary coordinates named 'latitude' and 'longitude'

    :param iris.cube.Cube cube: The cube to search for latitude/longitude coordinates.
    :returns: A 2-tuple of Iris coordinate objects representing the cube's latitude
        and longitude coordinate dimensions, respectively.
    :raises iris.exceptions.CoordinateNotFoundError: Raised if no latitude/longitude
        coordinates could be found on the passed-in cube.
    """
    try:
        # check for 'latitude' and 'longitude' dimension coordinates
        latcrd = cube.coord('latitude', dim_coords=True)
        loncrd = cube.coord('longitude', dim_coords=True)
    except iris.exceptions.CoordinateNotFoundError:
        try:
            # check for 'grid_latitude' and 'grid_longitude' dimension coordinates
            latcrd = cube.coord('grid_latitude', dim_coords=True)
            loncrd = cube.coord('grid_longitude', dim_coords=True)
        except iris.exceptions.CoordinateNotFoundError:
            # check for 'latitude' and 'longitude' auxiliary coordinates
            latcrd = cube.coord('latitude', dim_coords=False)
            loncrd = cube.coord('longitude', dim_coords=False)

    return (latcrd, loncrd)


def has_global_domain(cube, rtol=1e-5, atol=1e-8):
    """
    Test to see if the spatial domain of the specified cube extends across the
    entire globe. The test is performed using either regular latitude and longitude
    coordinates or, for rotated pole datasets, grid_latitude and grid_longitude
    coordinates. If neither pair of coordinates is detected on the cube then the
    function returns None. If either of the selected coordinate objects has
    associated cell bounds, then these are used to determine the extent of the
    spatial domain.

    .. note:: The latitude and longitude coordinates can exist on the cube as
       either dimension coordinates or auxiliary coordinates; the former, if
       present, being checked before the latter. In both cases, however, the
       coordinates must be 1-dimensional.

    In the case of the latitudinal extent, pole-to-pole coverage is assumed if
    the minimum latitude (or cell bound) is less than or equal, within tolerance,
    to -90, and the maximum latitude (or cell bound) is greater than or equal,
    within tolerance, to +90.

    In the case of the longitudinal extent, global coverage is determined by
    calling the :func:`is_circular` function to determine the circularity of
    the longitude coordinates (or cell bounds) attached to the cube. For example,
    the following longitude ranges would all evaluate as circular: [0, 360],
    [-90, 270], [-180, 180].

    The tolerance parameters are passed through to the ``numpy.allclose()``
    function.

    :param iris.cube.Cube cube: The cube whose spatial domain is to be tested.
    :param float rtol: The relative tolerance to use in coordinate equality tests.
    :param float atol: The absolute tolerance to use in coordinate equality tests.
    :returns: True if the cube's spatial domain covers the entire globe, False
        if it is not global, or None if the extent cannot be determined.
    """

    # Obtain handles to the cube's latitude and longitude coordinate objects.
    # First look for dimension coordinates, then auxiliary coordinates.
    found_coords = False
    for dim_coord_opt in [True, False]:
        try:
            latcrd = cube.coord('latitude', dim_coords=dim_coord_opt)
            loncrd = cube.coord('longitude', dim_coords=dim_coord_opt)
            found_coords = True
        except iris.exceptions.CoordinateNotFoundError:
            try:
                latcrd = cube.coord('grid_latitude', dim_coords=dim_coord_opt)
                loncrd = cube.coord('grid_longitude', dim_coords=dim_coord_opt)
                found_coords = True
            except iris.exceptions.CoordinateNotFoundError:
                pass
        if found_coords: break

    # No suitable coordinates were found so return None.
    if not found_coords:
        return None

    # Check that the coordinates are 1-dimensional and have sufficient points
    # (or bounds) to enable the extent of the domain to be determined.
    lat_ok = latcrd.ndim == 1 and (latcrd.has_bounds() or len(latcrd.points) > 1)
    lon_ok = loncrd.ndim == 1 and (loncrd.has_bounds() or len(loncrd.points) > 1)
    if not (lat_ok and lon_ok):
        return None

    # Obtain the minimum and maximum latitude values.
    if latcrd.has_bounds():
        latmin = min(latcrd.bounds[0,0], latcrd.bounds[-1,1])
        latmax = max(latcrd.bounds[0,0], latcrd.bounds[-1,1])
    else:
        latmin = min(latcrd.points[0], latcrd.points[-1])
        latmax = max(latcrd.points[0], latcrd.points[-1])

    # Check to see if either of the min or max latitude values is less than 90,
    # thus indicating that the cube is non-global in extent.
    latmin_check = np.allclose(latmin, -90.0, rtol=rtol, atol=atol) or latmin < -90.0
    latmax_check = np.allclose(latmax,  90.0, rtol=rtol, atol=atol) or latmax >  90.0
    if not (latmin_check and latmax_check):
        return False

    # Check to see if the longitude bounds or coordinates are circular. If so,
    # then the cube is global in extent.
    return is_circular(loncrd.points, 360, bounds=loncrd.bounds, rtol=rtol, atol=atol)


def is_circular(points, modulus, bounds=None, rtol=1e-5, atol=1e-8):
    """
    Test to see if the specified points or bounds arrays are circular in nature
    relative to the given modulus value.

    If the bounds are provided then these are checked for circularity rather
    than the points.

    .. note:: This function is a slight adaptation of the private Iris function
       ``iris.util._is_circular``. It can usefully be employed to determine the
       circularity, or otherwise, of an array of longitude coordinates.

    The tolerance parameters are passed through to the ``numpy.allclose()``
    function.

    :param array points: A numpy.ndarray of points, monotonic increasing.
    :param float modulus: The circularity modulus value, e.g. 360 for longitude
        coordinates.
    :param array bounds: A numpy.ndarray of cell bounds corresponding to the
        points array.
    :param float rtol: The relative tolerance to use in coordinate equality tests.
    :param float atol: The absolute tolerance to use in coordinate equality tests.
    :returns: True if the array of points (or bounds) is circular with respect to
        the given modulus value, else False.
    """
    circular = False

    if bounds is not None:
        # Set circular to True if the bounds outer limits are equivalent.
        first_bound = last_bound = None
        if bounds.ndim == 1 and len(bounds) == 2:
            first_bound = bounds[0]
            last_bound = bounds[1]
        elif bounds.ndim == 2 and bounds.shape[-1] == 2:
            first_bound = bounds[0, 0]
            last_bound = bounds[-1, 1]

        if first_bound is not None and last_bound is not None:
            # If either bound value is equal, within tolerance, to the modulus
            # value then set it to zero.
            if np.allclose(first_bound, modulus, rtol=rtol, atol=atol):
                first_bound = 0
            else:
                first_bound %= modulus
            if np.allclose(last_bound, modulus, rtol=rtol, atol=atol):
                last_bound = 0
            else:
                last_bound %= modulus
            circular = np.allclose(first_bound, last_bound, rtol=rtol, atol=atol)

    else:
        # Set circular to True if points are evenly spaced and last-first+step is
        # approx equal to the modulus.
        if len(points) > 1:
            diffs = np.diff(points)
            diff = np.mean(diffs)
            abs_tol = diff * 1.0e-4
            diff_approx_equal = np.max(np.abs(diffs - diff)) < abs_tol
            if diff_approx_equal:
                last_bound = points[-1] - points[0] + diff
                circular = np.allclose(last_bound, modulus, rtol=rtol, atol=atol)
        else:
            # Inherited behaviour from NetCDF PyKE rules.
            circular = points[0] >= modulus

    return circular


def is_scalar_coord(cube, coord_name):
    """
    Test to see whether or not a cube's named coordinate is scalar. A coordinate
    is scalar if it is neither a dimension coordinate nor an auxiliary coordinate.

    :param iris.cube.Cube cube: The cube to test.
    :param str coord_name: The name of the coordinate to examine.
    :returns: True if the nominated coordinate is present and scalar, or False if
        it is present but non-scalar (i.e. a dimension coordinate or auxiliary
        coordinate). If the cube does not feature the target coordinate then the
        function returns None.
    """
    try:
        axis = cube.coord(coord_name)
        if (coord_name in [c.name() for c in cube.coords(dim_coords=False)] and
            not cube.coord_dims(axis)):
            return True
        else:
            return False
    except iris.exceptions.CoordinateNotFoundError:
        return None


def is_mean_of_all_time_steps(cube):
    """
    A load constraint that returns True if the cube comes from a monthly or
    annual mean and the time interval is **not** 24 hours. This corresponds to a
    mean of all time steps and so excludes diurnal cycle diagnostics.

    :param iris.cube.Cube cube: The cube to test.
    :returns: True if ``cube``'s cell methods indicate a mean of all time steps.
    """
    if cube.cell_methods:
        for cm in cube.cell_methods:
            mean_test = cm.method == 'mean'
            coord_test = 'time' in cm.coord_names
            interval_test = '24' not in str(cm.intervals)
            if mean_test and coord_test and interval_test:
                return True

    # if not returned already then the patterns weren't found so...
    return False


def is_time_mean(cube):
    """
    A load constraint that returns True if the cube's cell methods indicate that
    the cube data represents a mean over time.

    :param iris.cube.Cube cube: The cube to test.
    :returns: True if the cube data represents a mean over time.

    .. seealso:: :func:`make_cell_method_cube_func`
    """
    return _check_cell_method(cube, 'mean', coord_name='time')


def is_time_maximum(cube):
    """
    A load constraint that returns True if the cube's cell methods indicate that
    the cube data represents a maximum over time.

    :param iris.cube.Cube cube: The cube to test.
    :returns: True if the cube data represents a maximum over time.

    .. seealso:: :func:`make_cell_method_cube_func`
    """
    return _check_cell_method(cube, 'maximum', coord_name='time')


def is_time_minimum(cube):
    """
    A load constraint that returns True if the cube's cell methods indicate that
    the cube data represents a minimum over time.

    :param iris.cube.Cube cube: The cube to test.
    :returns: True if the cube data represents a minimum over time.

    .. seealso:: :func:`make_cell_method_cube_func`
    """
    return _check_cell_method(cube, 'minimum', coord_name='time')


def _check_cell_method(cube, method_name, coord_name=None):
    """
    Return True if any of the cell methods defined on ``cube`` contain the
    specified method name and coordinate name combination.

    :param iris.cube.Cube cube: The cube to test.
    :param str method_name: The method name to check.
    :param str coord_name: The optional coordinate name to check.
    :returns: True if any of the cube's cell methods matches the specified
        method name and optional coordinate name.
    """
    if cube.cell_methods:
        for cm in cube.cell_methods:
            if method_name == cm.method:
                if not coord_name or (coord_name in cm.coord_names):
                    return True

    # if not returned already then the patterns weren't found so...
    return False


def make_cell_method_cube_func(method_name, coord_name, interval=None):
    """
    Make a callback function suitable for loading or extracting cubes according
    to their cell method(s), if defined. The callback function returns True if
    any of the cell method objects attached to the cube(s) being constrained
    match **all** of the cell method properties supplied as arguments to this
    function.

    The code snippet below illustrates extracting those cubes from a cubelist
    which represent a maximum over time, based on a 24 hour sampling interval::

       callback = make_cell_method_cube_func('maximum', 'time', interval='24 hour')
       cons = iris.Constraint(cube_func=callback)
       cubes = cubelist.extract(cons)

    Typically a cell method constraint such as shown above would be used in
    combination with other constraints, e.g. ones based on cube name.

    Note that the make_cell_method_cube_func() function represents a general-purpose
    solution to the specific capabilities provided by the :func:`is_time_mean`,
    :func:`is_time_minimum`, and :func:`is_time_maximum` functions within this
    module. As such it can be utilised in a wider variety of situations.

    :param str method_name: The CF cell method name, e.g. 'mean'.
    :param str coord_name: The name of the coordinate dimension (axis) over which
        the method is applied, .e.g. 'time'.
    :param str interval: An optional CF interval string of the form 'value unit',
        e.g. '1 hour'. The unit must be a udunits-compatible unit identifier.
    :returns: A function object which can be assigned to the ``cube_func``
        argument of an Iris load or extract constraint.
    """

    def _cell_method_cube_func(cube):
        """A callback function for checking cell methods on a cube."""

        if cube.cell_methods:
            for cm in cube.cell_methods:
                name_test = (method_name == cm.method)
                coord_test = (coord_name in cm.coord_names)
                if interval:
                    interval_test = (interval in cm.intervals)
                else:
                    interval_test = True
                if name_test and coord_test and interval_test:
                    return True

        # No cell methods match.
        return False

    return _cell_method_cube_func


def make_calendar_type_cube_func(calendar, coord_name='time'):
    """
    Make a callback function suitable for loading or extracting cubes according
    to their calendar type, if defined. The callback function returns True if
    the calendar type associated with a cube's time coordinate is the same as
    that specified by the ``calendar`` argument. Otherwise the function returns
    False, including the case where a cube does not possess a time dimension.

    :param str calendar: The calendar type, e.g. '360_day'.
    :param str coord_name: The name of the cube's time coordinate dimension.
    :returns: A function object which can be assigned to the ``cube_func``
        argument of an Iris load or extract constraint.
    """

    def _calendar_type_cube_func(cube):
        """A callback function for checking the calendar type of a cube."""

        try:
            time_coord = cube.coord(coord_name)
            result = time_coord.units.calendar == calendar
        except (AttributeError, iris.exceptions.CoordinateNotFoundError):
            result = False

        return result

    return _calendar_type_cube_func


def set_history_attribute(cube, text, replace=False):
    """
    Set a cube's history attribute using the specified text, which is prefixed
    with the boilerplate text "<timestamp>: Afterburner vM.N.P: " before being
    written to the cube.

    :param iris.cube.Cube cube: The cube to modify.
    :param str text: The raw history text, i.e. without timestamp information.
    :param bool replace: If true then ``text`` will replace any existing
        history attribute value. If false (the default) then ``text`` is
        added to the *front* of the existing value, in accordance with the
        CF metadata conventions.
    """
    now = datetime.datetime.utcnow().replace(microsecond=0)
    text = "{0}Z: Afterburner v{1}: {2}".format(now.isoformat(),
        afterburner.__version__, text)
    history = cube.attributes.get('history', '')
    if history and not replace: text += ';\n' + history
    cube.attributes['history'] = text


def guess_aggregation_period(cube, coord_name='time'):
    """
    Guess the aggregation period, as used for meaning or accumulation purposes,
    associated with the data payload of a cube. The aggregation period, if any,
    is determined by examining the cube's time coordinates, cell methods, and
    cell bounds.

    The aggregation period is indicated by returning a string of the form '1h'
    (hourly mean), '1d' (daily mean), '1m' (monthly mean), '1s' (seasonal mean),
    '1y' (annual mean), and so on. The initial number can be greater than 1, e.g.
    '6h' for a 6-hourly mean, or '10d' for a 10-day mean.

    :param iris.cube.Cube: The cube to examine.
    :param str coord_name: The name of the time coordinate to examine.
    :returns: A code string identifying the aggregation period. The string is
        constructed as '<count><time-period>', where <count> is a positive
        integer and <time-period> is one of the letters 'h', 'd', 'm', 's',
        'y'. The latter signify hours, days, months, climate seasons, and years,
        respectively. A value of None is returned if the cube is not associated
        with a cell method based on a time, or if the interval between time
        coordinates (or their cell bounds) does not match a regular aggregation
        period.
    """
    agg_period = None

    # Check that the cube has a time coordinate.
    try:
        time_coord = cube.coord(coord_name)
        time_pts = time_coord.points
        if len(time_pts) == 1 and not time_coord.has_bounds():
            return agg_period
        time_bnds = time_coord.bounds
    except iris.exceptions.CoordinateNotFoundError:
        return agg_period


    # Check that the cube has cell methods.
    if not cube.cell_methods:
        return agg_period

    # Check that the cube has at least one cell method based on time.
    time_methods = []
    for cm in cube.cell_methods:
        if 'time' in cm.coord_names: time_methods.append(cm.method)

    if not time_methods:
        return agg_period

    year_lengths = {'360_day': 360, '365_day': 365, '366_day': 366}
    ndays_in_year = year_lengths.get(time_coord.units.calendar, 365)

    # Determine the average difference between coords along the time axis.
    ts_hours = _calc_time_step_in_hours(time_pts, time_bnds, time_coord.units)

    if ts_hours >= 24:
        #tol = 0.05
        ts_days = ts_hours // 24
        ts_years = ts_days // ndays_in_year
        if ts_years >= 1:
            agg_period = '%dy' % int(round(ts_years))
        elif abs(ts_days-90) < 3:
            agg_period = '1s'
        elif abs(ts_days-30) < 3:
            agg_period = '1m'
        elif ts_days >= 1:
            agg_period = '%dd' % int(round(ts_days))

    elif ts_hours >= 1:
        agg_period = '%dh' % int(round(ts_hours))

    return agg_period


def _calc_time_step_in_hours(points, bounds, tunits):
    """
    Calculate the average time step, in hours, between points along the time
    axis defined by the points and bounds arrays.
    """

    if bounds is None:
        # no bounds defined so analyse coord steps in points array
        ts = np.diff(points).mean()
    else:
        # bounds are defined so analyse cell sizes in bounds array
        ts = np.diff(bounds).mean()

    # Convert time units to hours if necessary.
    if not tunits.origin.startswith('hour'):
        origin = 'hours since' + tunits.origin.partition('since')[-1]
        tu = cfu.Unit(origin, calendar=tunits.calendar)
        ts = tunits.convert(ts, tu)

    return ts


def _num_days_per_year(calendar):
    """Return the number of days per year for the specified calendar."""

    if calendar == cfu.CALENDAR_360_DAY:
        ndays_per_year = 360
    elif calendar in [cfu.CALENDAR_365_DAY, cfu.CALENDAR_NO_LEAP]:
        ndays_per_year = 365
    elif calendar in [cfu.CALENDAR_366_DAY, cfu.CALENDAR_ALL_LEAP]:
        ndays_per_year = 366
    else:
        ndays_per_year = 365

    return ndays_per_year


def augment_cube_class(cube=None):
    """
    Augment the iris.cube.Cube class, or else a specific cube object, with the
    following convenience methods:

    stash_code()
      Returns the MSI-style STASH code, if any, associated with a cube.

    meaning_period()
      Returns the meaning/aggregation period, if any, associated with a cube.
      Refer to :func:`guess_aggregation_period` for meaning of return value.

    vsummary()
      Returns a text string containing a verbose summary (if that isn't oxymoronic!)
      of the cube.

    Example code::

        augment_cube_class()
        mycube.stash_code()
        'm01s00i024'
        mycube.meaning_period()
        '1m'

    :param iris.cube.Cube cube: If a cube object is passed in then only that
        instance object is augmented with the functions described above; the
        Cube class is not modified.
    """
    from iris.cube import Cube

    def _get_stash_code(self) :
        if 'STASH' in self.attributes:
            return str(self.attributes['STASH'])
        else:
            return None

    target = cube or Cube
    obj = cube

    if not hasattr(target, 'stash_code'):
        if obj:
            target.stash_code = create_bound_method(_get_stash_code, obj)
        else:
            target.stash_code = create_unbound_method(_get_stash_code, Cube)

    if not hasattr(target, 'meaning_period'):
        if obj:
            target.meaning_period = create_bound_method(guess_aggregation_period, obj)
        else:
            target.meaning_period = create_unbound_method(guess_aggregation_period, Cube)

    if not hasattr(target, 'vsummary'):
        if obj:
            target.vsummary = create_bound_method(vsummary, obj)
        else:
            target.vsummary = create_unbound_method(vsummary, Cube)


def compare_cubes(cube1, cube2, stream=None, **kwargs):
    """
    Compare two Iris cubes and report differences on the stream pointed to by
    the stream argument. Note that the numerical arrays making up the cube data
    payloads are *not* currently compared.

    As well as comparing metadata attributes attached directly to both cubes
    (e.g. the various `*_name` attributes), this function also recursively examines
    the main composite cube objects: coordinates, cell_methods and cell_measures.

    :param iris.cube.Cube cube1: The first cube to compare.
    :param iris.cube.Cube cube2: The second cube to compare.
    :param file stream: The output stream (a file-like object) on which to print
        messages. The default stream is sys.stdout.

    The following boolean keyword arguments may be used to enable/disable any of
    the cube elements being compared. By default all elements are examined.

    :param bool shapes_and_types: Compare the shape and type of the data arrays.
    :param bool metadata: Compare the metadata properties of the cubes.
    :param bool cell_methods: Compare the cell methods of the cubes.
    :param bool cell_measures: Compare the cell measures of the cubes.
    :param bool coordinates: Compare the coordinates of the cubes.

    :returns: True if the cubes are equal (ignoring data arrays), otherwise false.
    """
    return _cubecomp.compare_cubes(cube1, cube2, stream=stream, **kwargs)


def get_earliest_time_datum(coord_list) :
    """
    Return the earliest time datum (aka time origin) associated with a list of
    Iris time coordinate objects.

    :param list/tuple coord_list: The list of time coordinate objects to examine.
    :returns: The date or date-time string representing the earliest time datum
        associated with the list of time coordinates.
    """
    try:
        ref_origin = coord_list[0].units.origin
        ref_cal = coord_list[0].units.calendar
        min_offset = 0
        _, min_datum = ref_origin.split('since')
    except:
        raise ValueError("Unable to read first element of coordinate list.")

    for crd in coord_list[1:] :
        crd_date = cfu.num2date(0, crd.units.origin, crd.units.calendar)
        crd_offset = cfu.date2num(crd_date, ref_origin, ref_cal)
        if crd_offset < min_offset :
            min_offset = crd_offset
            _, min_datum = crd.units.origin.split('since')

    return min_datum.strip()


def rebase_time_coords(coord_list, target_unit=None) :
    """
    Rebase a list of Iris time coordinate objects so that they all reference the
    same time datum. The new time datum may be specified via the ``target_unit``
    argument, which should be a string of the form 'time-units since time-datum'
    or else a ``cf_units.Unit`` object which carries the same information. In the
    latter case, the calendar attribute must match the equivalent attribute on each
    passed-in coordinate object.

    If the ``target_unit`` argument is not specified then the output time datum
    is set equal to the *earliest* datum associated with the list of input coordinate
    objects.

    The input time coordinate objects are modified *in situ*. If a coordinate object
    contains cell bounds then those values are also rebased to the new time datum.
    Naturally, the time units attached to each coordinate object are updated to
    reflect the as-specified or as-determined time datum.

    If the passed-in coordinate objects happen to use different base units -- a
    mix of days, hours, and seconds, for example -- then those units are preserved
    and the time coordinate values are calculated with respect to the new time datum.

    :param list/tuple coord_list: The list of time coordinate objects to operate on.
    :param str/object target_unit: Optionally, the CF-style time units from which
        to obtain the time datum to use to rebase each of the supplied coordinate
        objects. The argument value may be a string of the form 'time-units since time-datum'
        or else a ``cf_units.Unit`` object
    :raises ValueError: Raised if the time units associated with the supplied
        coordinate objects are in some way incompatible, e.g. possess mixed
        calendars. Also raised if the units specified via ``target_unit`` are
        incompatible with the coordinate objects.
    :raises iris.exceptions.UnitConversionError: Raised if a coordinate object's
        units cannot be converted to the as-specified or as-determined target units.
    """

    # Convenience function for extracting the base unit, datum and calendar
    # properties from a CF-style time unit definition.
    def _parse_time_units(tunits):
        unit, datum = map(str.strip, tunits.origin.split('since'))
        return unit, datum, tunits.calendar

    # Check that all coordinate objects use CF-style time units.
    if not all([c.units.is_time_reference() for c in coord_list]):
        raise ValueError("Not all units associated with the input coordinate "
            "objects are CF-style time-since-datum units.")

    # Check that all coordinate objects share the same calendar.
    cals = set()
    for crd in coord_list:
        _unit, _datum, cal = _parse_time_units(crd.units)
        cals.add(cal)

    if len(cals) > 1:
        raise ValueError("Input time coordinate objects use different calendars.")

    source_cal = coord_list[0].units.calendar
    target_datum = None

    # Determine the target datum if not specified by calling program.
    if target_unit is None:
        # Find the earliest time datum in the input coordinate list
        target_datum = get_earliest_time_datum(coord_list)
    elif isinstance(target_unit, string_types):
        target_unit = cfu.Unit(target_unit, calendar=source_cal)
    elif isinstance(target_unit, cfu.Unit):
        if not target_unit.is_time_reference():
            raise ValueError("Target unit does not define a CF-style "
                "time-since-datum unit.")
        elif target_unit.calendar != source_cal:
            raise ValueError("The source calendar ({0}) and target calendar ({1}) "
                "do not match".format(source_cal, target_unit.calendar))
    else:
        raise ValueError("The target_unit argument must be of type string or "
            "cf_units.Unit")

    if not target_datum:
        _unit, target_datum, _cal = _parse_time_units(target_unit)

    # Check that all coordinate objects are unit-convertible prior to converting
    # any of them to avoid the situation where only a subset of coordinates are
    # handled.
    for crd in coord_list:
        unit, _datum, cal = _parse_time_units(crd.units)
        tu = cfu.Unit(unit + ' since ' + target_datum, calendar=cal)
        if not crd.units.is_convertible(tu):
            raise iris.exceptions.UnitConversionError("Cannot convert {0!r} to "
                " {1!r}".format(crd.units, tu))

    # OK, now we can convert all time coordinates (and bounds, if present) to the
    # new target unit.
    for crd in coord_list:
        unit, _datum, cal = _parse_time_units(crd.units)
        tu = cfu.Unit(unit + ' since ' + target_datum, calendar=cal)
        if crd.units != tu:
            crd.convert_units(tu)


def vsummary(cube, realise_data=False):
    """
    A verbose alternative to the ``cube.summary()`` method. The returned text
    string includes extra information as follows:

    * all name/identity metadata
    * a guess as to the meaning/aggregation period
    * for a cube's data payload:
        - the array object type (ndarray or masked array)
        - the array data type (e.g. float32)
        - the fill value (for non-lazy masked arrays)
        - the number of masked values (for non-lazy masked arrays)
        - the minimum and maximum data values (for non-lazy data)
    * for the T, X, Y and Z axes:
        - the axis units
        - the shape and data type of the points array
        - the calendar type (for time axes)
        - the horizontal coordinate system (for X and Y axes)
        - the spatial domain (for X and Y axes)
    * extra details for any cell measures present

    Certain items of information can only be determined when the cube's data array
    has been realised, i.e. made non-lazy. This can be enforced, if required, by
    enabling the ``realise_data`` argument.

    Below can be seen example output for a cube annual-mean temperature data derived
    from the Met Office Unified Model::

        >>> print(cubeutils.vsummary(cube, realise_data=True))
        --------------------------------------------------------------------------------
        Surface Temperature   (latitude: 144; longitude: 192)
        --------------------------------------------------------------------------------
        standard name  : surface_temperature
        variable name  : not defined
        long name      : not defined
        units          : K
        meaning period : appears to be 1y

        lazy data?     : no
        array type     : ndarray
        array shape    : (144, 192)
        data type      : float32
        fill value     : n/a
        missing values : 0
        minimum value  : 215.552978515625
        maximum value  : 309.45458984375

                                       (latitude: 144; longitude: 192)
        Dimension coordinates:
             latitude                           x               -
             longitude                          -               x
        Scalar coordinates:
             forecast_period: 792720.0 hours, bound=(788400.0, 797040.0) hours
             forecast_reference_time: 1978-09-01 00:00:00
             time: 2070-06-01 00:00:00, bound=(2069-12-01 00:00:00, 2070-12-01 00:00:00)
        Attributes:
             STASH: m01s00i024
             source: Data from Met Office Unified Model
             um_version: 8.5
        Cell methods:
             mean: time (1 hour)

        Cell measure details:
             none found

        T axis: not found

        X axis  : longitude
          shape : (192,)
          dtype : float32
          units : degrees
          crs   : GeogCS(6371229.0)
          domain: appears to be global

        Y axis  : latitude
          shape : (144,)
          dtype : float32
          units : degrees
          crs   : GeogCS(6371229.0)
          domain: appears to be global

        Z axis: not found
        --------------------------------------------------------------------------------

    If a cube (or the ``Cube`` class) has been augmented via a call to the
    :func:`augment_cube_class` function, then the ``vsummary()`` function can be
    used as a method, as the following code snippet illustrates:

    >>> cubeutils.augment_cube_class(cube)
    >>> print(cube.vsummary())

    :param iris.cube.Cube cube: The cube for which to return verbose summary
        information.
    :param bool realise_data: If this evaluates to true then the cube's data
        payload is realised, if it hasn't been already.
    :returns: A text string containing the verbose summary.
    """

    try:
        text = _vsummary(cube, realise_data=realise_data)
    except:
        text = ("ERROR: Problem trying to generate verbose summary for cube:\n"
                "       {}".format(cube.summary(shorten=True)))

    return text


def _vsummary(cube, realise_data=False):
    """
    Actual implementation of the vsummary() method, primarily so that the latter
    method can more conveniently wrap the construction of the text within a
    try/except block (rather than have a very long indented block).
    """

    values = dict()

    # Identity information.
    std_name = cube.standard_name or 'not defined'
    quantity = cube.long_name or std_name
    values['quantity'] = quantity.replace('_', ' ').title()
    values['hrule'] = '-' * 80
    values['std_name'] = std_name
    values['long_name'] = cube.long_name or 'not defined'
    values['var_name'] = cube.var_name or 'not defined'
    values['units'] = cube.units
    agg_period = guess_aggregation_period(cube)
    if agg_period:
        values['agg_period'] = 'appears to be ' + agg_period
    else:
        values['agg_period'] = 'indeterminate'

    # Data type information.
    if realise_data:
        data = cube.data
    else:
        data = cube.core_data()
    values['dtype'] = data.dtype
    values['array_type'] = 'masked array' if np.ma.isMA(data) else 'ndarray'
    values['array_shape'] = data.shape

    if cube.has_lazy_data():
        values['lazy'] = 'yes'
        values['fill_value'] = 'indeterminate (lazy data)'
        values['nmasked'] = 'indeterminate (lazy data)'
        values['minval'] = 'indeterminate (lazy data)'
        values['maxval'] = 'indeterminate (lazy data)'
    else:
        values['lazy'] = 'no'
        values['fill_value'] = getattr(data, 'fill_value', 'n/a')
        values['nmasked'] = np.ma.count_masked(data)
        values['minval'] = data.min()
        values['maxval'] = data.max()

    # General dimension/axis information.
    dim_hdr, _, dim_info = str(cube).partition('\n')
    idx = dim_hdr.rindex('(')
    dim_hdr = ' ' * (idx-5) + dim_hdr[idx:]
    dim_info = '\n'.join([s[5:] for s in dim_info.split('\n')])
    values['dims'] = '; '.join(["{0}: {1}".format(c.name(), len(c.points))
        for c in cube.dim_coords])
    values['dim_hdr'] = dim_hdr
    values['dim_info'] = dim_info

    taxis = xaxis = yaxis = zaxis = None

    # T axis information.
    try:
        taxis = cube.coord(dim_coords=True, axis='T')
        values['taxis']  = "T axis  : {0}\n".format(taxis.name())
        values['taxis'] += "  shape : {0}\n".format(taxis.shape)
        values['taxis'] += "  dtype : {0}\n".format(taxis.points.dtype)
        values['taxis'] += "  units : {0}\n".format(taxis.units)
        values['taxis'] += "  cal   : {0}\n".format(taxis.units.calendar)
    except iris.exceptions.CoordinateNotFoundError:
        values['taxis'] = "T axis: not found\n"

    # X axis information.
    try:
        try:
            xaxis = cube.coord(dim_coords=True, axis='X')
        except iris.exceptions.CoordinateNotFoundError:
            xaxis = cube.coord(dim_coords=False, axis='X')
        if not xaxis.has_bounds(): xaxis.guess_bounds()
        values['xaxis']  = "X axis  : {0}\n".format(xaxis.name())
        values['xaxis'] += "  shape : {0}\n".format(xaxis.shape)
        values['xaxis'] += "  dtype : {0}\n".format(xaxis.points.dtype)
        values['xaxis'] += "  units : {0}\n".format(xaxis.units)
        values['xaxis'] += "  crs   : {0}\n".format(xaxis.coord_system or 'not defined')
    except iris.exceptions.CoordinateNotFoundError:
        values['xaxis'] = "X axis: not found\n"

    # Y axis information.
    try:
        try:
            yaxis = cube.coord(dim_coords=True, axis='Y')
        except iris.exceptions.CoordinateNotFoundError:
            yaxis = cube.coord(dim_coords=False, axis='Y')
        if not yaxis.has_bounds(): yaxis.guess_bounds()
        values['yaxis']  = "Y axis  : {0}\n".format(yaxis.name())
        values['yaxis'] += "  shape : {0}\n".format(yaxis.shape)
        values['yaxis'] += "  dtype : {0}\n".format(yaxis.points.dtype)
        values['yaxis'] += "  units : {0}\n".format(yaxis.units)
        values['yaxis'] += "  crs   : {0}\n".format(yaxis.coord_system or 'not defined')
    except iris.exceptions.CoordinateNotFoundError:
        values['yaxis'] = "Y axis: not found\n"

    # Z axis information.
    try:
        try:
            zaxis = cube.coord(dim_coords=True, axis='Z')
        except iris.exceptions.CoordinateNotFoundError:
            zaxis = cube.coord(dim_coords=False, axis='Z')
        values['zaxis']  = "Z axis   : {0}\n".format(zaxis.name())
        values['zaxis'] += "  shape  : {0}\n".format(zaxis.shape)
        values['zaxis'] += "  dtype  : {0}\n".format(zaxis.points.dtype)
        values['zaxis'] += "  units  : {0}".format(zaxis.units)
    except iris.exceptions.CoordinateNotFoundError:
        values['zaxis'] = "Z axis: not found"


    # Spatial domain: one of global, regional or indeterminate.
    if xaxis and yaxis:
        domain_dict = {True: 'appears to be global', False: 'appears to be regional'}
        domain = domain_dict.get(has_global_domain(cube), 'indeterminate')
        values['xaxis'] += "  domain: {0}\n".format(domain)
        values['yaxis'] += "  domain: {0}\n".format(domain)

    # Cell measure details.
    cube_measures = cube.cell_measures()
    if cube_measures:
        measures = ""
        for cm in cube_measures:
            name = cm.name()
            measures += ("\n     {0}: measure={1.measure}, var_name={1.var_name}, "
                "units={1.units}, shape={1.shape}".format(name, cm))
    else:
        measures = '\n     none found'
    values['measures'] = measures

    text = """
{hrule}
{quantity}   ({dims})
{hrule}
standard name  : {std_name}
variable name  : {var_name}
long name      : {long_name}
units          : {units}
meaning period : {agg_period}

lazy data?     : {lazy}
array type     : {array_type}
array shape    : {array_shape}
data type      : {dtype}
fill value     : {fill_value}
missing values : {nmasked}
minimum value  : {minval}
maximum value  : {maxval}

{dim_hdr}
{dim_info}

Cell measure details: {measures}

{taxis}
{xaxis}
{yaxis}
{zaxis}
{hrule}
"""

    return text.format(**values)
