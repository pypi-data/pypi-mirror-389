# (C) British Crown Copyright 2017-2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The stockcubes module contains convenience functions for creating synthetic cubes
for use in e.g. sample or test code. They are intended to supplement the test
cubes provided by the iris.tests.stock module. A few usage examples are shown
below.

Create a 2D cube of air temperature on a regular latitude-longitude grid:

>>> from afterburner.misc import stockcubes
>>> cube = stockcubes.geo_yx()

Create a 3D cube (T-Y-X) of monthly-mean precipitation on a rotated
latitude-longitude grid:

>>> cube = stockcubes.rot_tyx(standard_name='rainfall_amount', var_name='precip',
...     long_name='Precipitation Rate', units='kg m-2 s-1')

Create a 3D cube (Z-Y-X) of eastward wind-speed on the British National grid:

>>> cube = stockcubes.bng_zyx(standard_name='x_wind', var_name='uwind',
...     long_name='Eastward Windspeed', units='m s-1')

**Contents**

.. autosummary::
   :nosignatures:

   geo_yx
   geo_zyx
   geo_tyx
   geo_tzyx
   geo_eyx
   geo_etyx
   rot_yx
   rot_zyx
   rot_tyx
   bng_yx
   bng_zyx
   bng_tyx
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import integer_types

import numpy as np
import cf_units
import iris
from iris.coords import AuxCoord, DimCoord
from iris.coord_systems import GeogCS, RotatedGeogCS, OSGB
from iris.analysis.cartography import rotate_pole, unrotate_pole
import afterburner

# Coordinates of rotated pole used by UKV model.
UKV_POLE_LAT = 37.5
UKV_POLE_LON = 177.5

# Default coordinate system.
DEFAULT_CRS = GeogCS(6371229.0)

# Default rotated coordinate system.
DEFAULT_ROT_CRS = RotatedGeogCS(UKV_POLE_LAT, UKV_POLE_LON, ellipsoid=DEFAULT_CRS)

# Default calendar.
DEFAULT_CALENDAR = cf_units.CALENDAR_360_DAY


def geo_yx(data=None, **kwargs):
    """
    Create a 2D cube based on a geodetic lat-lon coordinate system. The returned
    cube has the following default properties:

    * shape: (y=7,x=6)
    * dtype: float32
    * data value: 0
    * X axis: geodetic longitude
    * Y axis: geodetic latitude
    * coordinate reference system: geodetic lat-long on UM sphere
    * standard_name: air_temperature
    * long_name: Air Temperature
    * var_name: air_temp
    * units: degC

    Several of these properties can be overridden via the following keyword
    arguments.

    :param obj data: Either a single number to assign to each element of the cube's
        data array, or a Numpy array of the same shape to replace the data array.
        If not specified then the data array is initialised with zeros.
    :param tuple shape: Shape of the generated cube. If specified then it must be
        a 2-tuple (ny, nx). However, if the data keyword defines a 2D Numpy array
        then the shape of the array is used.
    :param str dtype: The Numpy data type of the cube's data array.
    :param obj coord_sys: An iris.coord_systems.CoordSystem object to use for
        the X and Y axes.
    :param str standard_name: The CF standard name to attach to the cube.
    :param str long_name: The long name to attach to the cube.
    :param str var_name: The variable name to attach to the cube.
    :param str units: The units to associate with the cube's data array.
    :param float start_lat: The start latitude in decimal degrees (default: -90).
    :param float end_lat: The end latitude in decimal degrees (default: 90).
    :param float start_lon: The start longitude in decimal degrees (default: 0).
    :param float end_lon: The end longitude in decimal degrees (default: 360).
        Note that longitude coordinates are generated using the Numpy call
        ``numpy.linspace(start_lon, end_lon, nlons, endpoint=False)``, where
        ``nlons`` is determined from the shape of the cube.
    """
    if isinstance(data, np.ndarray) and data.ndim == 2:
        shape = data.shape
    else:
        shape = kwargs.get('shape', (7,6))
    assert len(shape) == 2, 'shape argument must be of length 2'
    nlats, nlons = shape

    xcoord = _create_lon_coord(npoints=nlons, coord_sys=kwargs.get('coord_sys'),
        start_lon=kwargs.get('start_lon', 0), end_lon=kwargs.get('end_lon', 360))
    ycoord = _create_lat_coord(npoints=nlats, coord_sys=kwargs.get('coord_sys'),
        start_lat=kwargs.get('start_lat', -90), end_lat=kwargs.get('end_lat', 90))

    data = _create_data_array(data, shape, dtype=kwargs.get('dtype'))

    cube = iris.cube.Cube(data,
        standard_name=kwargs.get('standard_name', 'air_temperature'),
        long_name=kwargs.get('long_name', 'Air Temperature'),
        var_name=kwargs.get('var_name', 'air_temp'),
        units=kwargs.get('units', 'degC'))

    cube.add_dim_coord(ycoord, 0)
    cube.add_dim_coord(xcoord, 1)

    return cube


def geo_zyx(data=None, **kwargs):
    """
    Create a 3D cube based on a height-lat-lon coordinate system. The returned
    cube has the following default properties:

    * shape: (z=5,y=7,x=6)
    * dtype: float32
    * data value: 0
    * X axis: geodetic longitude
    * Y axis: geodetic latitude
    * Z axis: pressure level
    * coordinate reference system: geodetic lat-long on UM sphere
    * standard_name: air_temperature
    * long_name: Air Temperature
    * var_name: air_temp
    * units: degC

    Refer to the :func:`geo_yx` function for a description of common keyword
    arguments. Extra arguments relevant to the current function are shown below.

    :param data: Either a single number to assign to each element of the cube's
        data array; or a 1D Numpy array, in which case the ith element value
        is assigned to the ith horizontal slice of the cube array; or a 3D Numpy
        array of the correct shape to replace the data array.
    :param tuple shape: Shape of the generated cube. If specified then it must be
        a 3-tuple (nz, ny, nx). However, if the data keyword defines a 3D Numpy
        array then the shape of the array is used.
    :param str zaxis_type: The type of Z axis to create. Currently supported
        axis types include: pressure (default), height, level
    """

    if isinstance(data, np.ndarray) and data.ndim == 3:
        shape = data.shape
    else:
        shape = kwargs.get('shape', (5,7,6))
    assert len(shape) == 3, 'shape argument must be of length 3'
    nlevels, nlats, nlons = shape

    xcoord = _create_lon_coord(npoints=nlons, coord_sys=kwargs.get('coord_sys'),
        start_lon=kwargs.get('start_lon', 0), end_lon=kwargs.get('end_lon', 360))
    ycoord = _create_lat_coord(npoints=nlats, coord_sys=kwargs.get('coord_sys'),
        start_lat=kwargs.get('start_lat', -90), end_lat=kwargs.get('end_lat', 90))
    zcoord = _create_vert_coord(npoints=nlevels, zaxis_type=kwargs.get('zaxis_type'))

    data = _create_data_array(data, shape, dtype=kwargs.get('dtype'))

    cube = iris.cube.Cube(data,
        standard_name=kwargs.get('standard_name', 'air_temperature'),
        long_name=kwargs.get('long_name', 'Air Temperature'),
        var_name=kwargs.get('var_name', 'air_temp'),
        units=kwargs.get('units', 'degC'))

    cube.add_dim_coord(zcoord, 0)
    cube.add_dim_coord(ycoord, 1)
    cube.add_dim_coord(xcoord, 2)

    return cube


def geo_tyx(data=None, **kwargs):
    """
    Create a 3D cube based on a time-lat-lon coordinate system. The returned
    cube has the following default properties:

    * shape: (t=12,y=7,x=6)
    * dtype: float32
    * data value: 0
    * X axis: geodetic longitude
    * Y axis: geodetic latitude
    * T axis: time as 'days since 1970-01-01' and based upon a 360-day calendar
    * coordinate reference system: geodetic lat-long on UM sphere
    * standard_name: air_temperature
    * long_name: Air Temperature
    * var_name: air_temp
    * units: degC

    Refer to the :func:`geo_yx` function for a description of common keyword
    arguments. Extra arguments relevant to the current function are shown below.

    :param data: Either a single number to assign to each element of the cube's
        data array; or a 1D Numpy array, in which case the ith element value
        is assigned to the ith time slice of the cube array; or a 3D Numpy array
        of the correct shape to replace the data array.
    :param tuple shape: Shape of the generated cube. If specified then it must be
        a 3-tuple (nt, ny, nx). However, if the data keyword defines a 3D Numpy
        array then the shape of the array is used.
    :param cf_units.Unit tunits: The units to assign to the T axis.
    :param str calendar: The calendar type to assign to the T axis if the units
        are not defined via the tunits keyword.
    """
    if isinstance(data, np.ndarray) and data.ndim == 3:
        shape = data.shape
    else:
        shape = kwargs.get('shape', (12,7,6))
    assert len(shape) == 3, 'shape argument must be of length 3'
    ntimes, nlats, nlons = shape

    xcoord = _create_lon_coord(npoints=nlons, coord_sys=kwargs.get('coord_sys'),
        start_lon=kwargs.get('start_lon', 0), end_lon=kwargs.get('end_lon', 360))
    ycoord = _create_lat_coord(npoints=nlats, coord_sys=kwargs.get('coord_sys'),
        start_lat=kwargs.get('start_lat', -90), end_lat=kwargs.get('end_lat', 90))
    tcoord = _create_time_coord(npoints=ntimes, units=kwargs.get('tunits'),
        calendar=kwargs.get('calendar'))

    data = _create_data_array(data, shape, dtype=kwargs.get('dtype'))

    cube = iris.cube.Cube(data,
        standard_name=kwargs.get('standard_name', 'air_temperature'),
        long_name=kwargs.get('long_name', 'Air Temperature'),
        var_name=kwargs.get('var_name', 'air_temp'),
        units=kwargs.get('units', 'degC'))

    cube.add_dim_coord(tcoord, 0)
    cube.add_dim_coord(ycoord, 1)
    cube.add_dim_coord(xcoord, 2)

    cm = iris.coords.CellMethod('mean', coords=('time',), intervals=('1 hour'))
    cube.cell_methods = (cm,)

    return cube


def geo_tzyx(data=None, **kwargs):
    """
    Create a 4D cube based on a time-height-lat-lon coordinate system. The
    returned cube has the following default properties:

    * shape: (t=12,z=5,y=7,x=6)
    * dtype: float32
    * data value: 0
    * X axis: geodetic longitude
    * Y axis: geodetic latitude
    * Z axis: pressure level
    * T axis: time as 'days since 1970-01-01' and based upon a 360-day calendar
    * coordinate reference system: geodetic lat-long on UM sphere
    * standard_name: air_temperature
    * long_name: Air Temperature
    * var_name: air_temp
    * units: degC

    Refer to the :func:`geo_yx` function for a description of common keyword
    arguments. Extra arguments relevant to the current function are shown below.

    :param data: Either a single number to assign to each element of the cube's
        data array; or a 1D Numpy array, in which case the ith element value
        is assigned to the ith time slice of the cube array; or a 4D Numpy array
        of the correct shape to replace the data array.
    :param tuple shape: Shape of the generated cube. If specified then it must be
        a 4-tuple (nt, nz, ny, nx). However, if the data keyword defines a 4D Numpy
        array then the shape of the array is used.
    :param cf_units.Unit tunits: The units to assign to the T axis.
    :param str calendar: The calendar type to assign to the T axis if the units
        are not defined via the tunits keyword.
    """
    if isinstance(data, np.ndarray) and data.ndim == 4:
        shape = data.shape
    else:
        shape = kwargs.get('shape', (12,5,7,6))
    assert len(shape) == 4, 'shape argument must be of length 4'
    ntimes, nlevels, nlats, nlons = shape

    xcoord = _create_lon_coord(npoints=nlons, coord_sys=kwargs.get('coord_sys'),
        start_lon=kwargs.get('start_lon', 0), end_lon=kwargs.get('end_lon', 360))
    ycoord = _create_lat_coord(npoints=nlats, coord_sys=kwargs.get('coord_sys'),
        start_lat=kwargs.get('start_lat', -90), end_lat=kwargs.get('end_lat', 90))
    zcoord = _create_vert_coord(npoints=nlevels, zaxis_type=kwargs.get('zaxis_type'))
    tcoord = _create_time_coord(npoints=ntimes, units=kwargs.get('tunits'),
        calendar=kwargs.get('calendar'))

    data = _create_data_array(data, shape, dtype=kwargs.get('dtype'))

    cube = iris.cube.Cube(data,
        standard_name=kwargs.get('standard_name', 'air_temperature'),
        long_name=kwargs.get('long_name', 'Air Temperature'),
        var_name=kwargs.get('var_name', 'air_temp'),
        units=kwargs.get('units', 'degC'))

    cube.add_dim_coord(tcoord, 0)
    cube.add_dim_coord(zcoord, 1)
    cube.add_dim_coord(ycoord, 2)
    cube.add_dim_coord(xcoord, 3)

    cm = iris.coords.CellMethod('mean', coords=('time',), intervals=('1 hour'))
    cube.cell_methods = (cm,)

    return cube


def geo_eyx(data=None, **kwargs):
    """
    Create a 3D cube based on an ensemble-lat-lon coordinate system. The returned
    cube has the following default properties:

    * shape: (e=3,y=7,x=6)
    * dtype: float32
    * data value: 0
    * X axis: geodetic longitude
    * Y axis: geodetic latitude
    * E axis: ensemble member (a.k.a. realization) number
    * auxiliary coordinate holding a RIP-style ensemble member name
    * scalar time coordinate with units of 'year'
    * coordinate reference system: geodetic lat-long on UM sphere
    * standard_name: air_temperature
    * long_name: Air Temperature
    * var_name: air_temp
    * units: degC

    Refer to the :func:`geo_yx` function for a description of common keyword
    arguments. Extra arguments relevant to the current function are shown below.

    :param data: Either a single number to assign to each element of the cube's
        data array; or a 1D Numpy array, in which case the ith element value
        is assigned to the ith ensemble member of the cube array; or a 3D Numpy
        array of the correct shape to replace the data array.
    :param tuple shape: Shape of the generated cube. If specified then it must be
        a 3-tuple (ne, ny, nx). However, if the data keyword defines a 3D Numpy
        array then the shape of the array is used.
    """
    if isinstance(data, np.ndarray) and data.ndim == 3:
        shape = data.shape
    else:
        shape = kwargs.get('shape', (3,7,6))
    assert len(shape) == 3, 'shape argument must be of length 3'
    nensembles, nlats, nlons = shape

    xcoord = _create_lon_coord(npoints=nlons, coord_sys=kwargs.get('coord_sys'),
        start_lon=kwargs.get('start_lon', 0), end_lon=kwargs.get('end_lon', 360))
    ycoord = _create_lat_coord(npoints=nlats, coord_sys=kwargs.get('coord_sys'),
        start_lat=kwargs.get('start_lat', -90), end_lat=kwargs.get('end_lat', 90))
    rcoord, ecoord = _create_ens_coords(npoints=nensembles)
    tcoord = AuxCoord(1970, standard_name='time', units='year')

    data = _create_data_array(data, shape, dtype=kwargs.get('dtype'))

    cube = iris.cube.Cube(data,
        standard_name=kwargs.get('standard_name', 'air_temperature'),
        long_name=kwargs.get('long_name', 'Air Temperature'),
        var_name=kwargs.get('var_name', 'air_temp'),
        units=kwargs.get('units', 'degC'))

    cube.add_dim_coord(rcoord, 0)
    cube.add_dim_coord(ycoord, 1)
    cube.add_dim_coord(xcoord, 2)
    cube.add_aux_coord(ecoord, 0)
    cube.add_aux_coord(tcoord)

    return cube


def geo_etyx(data=None, **kwargs):
    """
    Create a 4D cube based on an ensemble-time-lat-lon coordinate system.
    The returned cube has the following default properties:

    * shape: (e=3,t=12,y=7,x=6)
    * dtype: float32
    * data value: 0
    * X axis: geodetic longitude
    * Y axis: geodetic latitude
    * T axis: time as 'days since 1970-01-01' and based upon a 360-day calendar
    * E axis: ensemble member id (a.k.a. realization id)
    * auxiliary coordinate holding a RIP-style ensemble member name
    * coordinate reference system: geodetic lat-long on UM sphere
    * standard_name: air_temperature
    * long_name: Air Temperature
    * var_name: air_temp
    * units: degC

    Refer to the :func:`geo_yx` function for a description of common keyword
    arguments. Extra arguments relevant to the current function are shown below.

    :param data: Either a single number to assign to each element of the cube's
        data array; or a 1D Numpy array, in which case the ith element value
        is assigned to the ith ensemble member of the cube array; or a 4D Numpy
        array of the correct shape to replace the data array.
    :param tuple shape: Shape of the generated cube. If specified then it must be
        a 4-tuple (ne, nt, ny, nx). However, if the data keyword defines a 4D Numpy
        array then the shape of the array is used.
    :param cf_units.Unit tunits: The units to assign to the T axis.
    :param str calendar: The calendar type to assign to the T axis if the units
        are not defined via the tunits keyword.
    """
    if isinstance(data, np.ndarray) and data.ndim == 4:
        shape = data.shape
    else:
        shape = kwargs.get('shape', (3,12,7,6))
    assert len(shape) == 4, 'shape argument must be of length 4'
    nensembles, ntimes, nlats, nlons = shape

    xcoord = _create_lon_coord(npoints=nlons, coord_sys=kwargs.get('coord_sys'),
        start_lon=kwargs.get('start_lon', 0), end_lon=kwargs.get('end_lon', 360))
    ycoord = _create_lat_coord(npoints=nlats, coord_sys=kwargs.get('coord_sys'),
        start_lat=kwargs.get('start_lat', -90), end_lat=kwargs.get('end_lat', 90))
    tcoord = _create_time_coord(npoints=ntimes, units=kwargs.get('tunits'),
        calendar=kwargs.get('calendar'))
    rcoord, ecoord = _create_ens_coords(npoints=nensembles)

    data = _create_data_array(data, shape, dtype=kwargs.get('dtype'))

    cube = iris.cube.Cube(data,
        standard_name=kwargs.get('standard_name', 'air_temperature'),
        long_name=kwargs.get('long_name', 'Air Temperature'),
        var_name=kwargs.get('var_name', 'air_temp'),
        units=kwargs.get('units', 'degC'))

    cube.add_dim_coord(rcoord, 0)
    cube.add_dim_coord(tcoord, 1)
    cube.add_dim_coord(ycoord, 2)
    cube.add_dim_coord(xcoord, 3)
    cube.add_aux_coord(ecoord, 0)

    return cube


def rot_yx(data=None, **kwargs):
    """
    Create a 2D cube based on a rotated lat-long coordinate system.
    The returned cube has the following default properties:

    * shape: (y=7,x=6)
    * dtype: float32
    * data value: 0
    * X axis: grid longitude
    * Y axis: grid latitude
    * coordinate reference system: rotated lat-long on UM sphere
    * latitude of grid north pole: 37.5 N
    * longitude of grid north pole: 177.5 E
    * standard_name: air_temperature
    * long_name: Air Temperature
    * var_name: air_temp
    * units: degC

    Several of these properties can be overridden via the following keyword
    arguments.

    :param obj data: Either a single number to assign to each element of the cube's
        data array, or a Numpy array of the same shape to replace the data array.
        If not specified then the data array is initialised with zeros.
    :param tuple shape: Shape of the generated cube. If specified then it must be
        a 2-tuple (ny, nx). However, if the data keyword defines a 2D Numpy array
        then the shape of that array is used.
    :param str dtype: The Numpy data type of the cube's data array.
    :param obj coord_sys: An iris.coord_systems.CoordSystem object to use for
        the X and Y axes.
    :param str standard_name: The CF standard name to attach to the cube.
    :param str long_name: The long name to attach to the cube.
    :param str var_name: The variable name to attach to the cube.
    :param str units: The units to associate with the cube's data array.
    :param float start_lat: The start latitude in decimal degrees (default: -5).
    :param float end_lat: The end latitude in decimal degrees (default: 10).
    :param float start_lon: The start longitude in decimal degrees (default: 350).
    :param float end_lon: The end longitude in decimal degrees (default: 365).
        Note that longitude coordinates are generated using the Numpy call
        ``numpy.linspace(start_lon, end_lon, nlons, endpoint=False)``, where
        ``nlons`` is determined from the shape of the cube.
    """
    if isinstance(data, np.ndarray) and data.ndim == 2:
        shape = data.shape
    else:
        shape = kwargs.get('shape', (7,6))
    assert len(shape) == 2, 'shape argument must be of length 2'
    nlats, nlons = shape

    rlon_coord = _create_rot_lon_coord(npoints=nlons, coord_sys=kwargs.get('coord_sys'),
        start_lon=kwargs.get('start_lon', 350), end_lon=kwargs.get('end_lon', 365))
    rlat_coord = _create_rot_lat_coord(npoints=nlats, coord_sys=kwargs.get('coord_sys'),
        start_lat=kwargs.get('start_lat', -5), end_lat=kwargs.get('end_lat', 10))

    rlons, rlats = np.meshgrid(rlon_coord.points, rlat_coord.points)
    lons, lats = unrotate_pole(rlons, rlats, UKV_POLE_LON, UKV_POLE_LAT)

    lon_coord = AuxCoord(lons, standard_name='longitude', var_name='lon',
        units='degrees_east')
    lat_coord = AuxCoord(lats, standard_name='latitude', var_name='lat',
        units='degrees_north')

    data = _create_data_array(data, shape, dtype=kwargs.get('dtype'))

    cube = iris.cube.Cube(data,
        standard_name=kwargs.get('standard_name', 'air_temperature'),
        long_name=kwargs.get('long_name', 'Air Temperature'),
        var_name=kwargs.get('var_name', 'air_temp'),
        units=kwargs.get('units', 'degC'))

    cube.add_dim_coord(rlat_coord, 0)
    cube.add_dim_coord(rlon_coord, 1)
    cube.add_aux_coord(lat_coord, [0, 1])
    cube.add_aux_coord(lon_coord, [0, 1])

    return cube


def rot_zyx(data=None, **kwargs):
    """
    Create a 3D cube based on a rotated height-lat-long coordinate system.
    The returned cube has the following default properties:

    * shape: (z=5,y=7,x=6)
    * dtype: float32
    * data value: 0
    * X axis: grid longitude
    * Y axis: grid latitude
    * Z axis: pressure level
    * coordinate reference system: rotated lat-long on UM sphere
    * latitude of grid north pole: 37.5 N
    * longitude of grid north pole: 177.5 E
    * standard_name: air_temperature
    * long_name: Air Temperature
    * var_name: air_temp
    * units: degC

    Refer to the :func:`rot_yx` function for a description of common keyword
    arguments. Extra arguments relevant to the current function are shown below.

    :param tuple shape: Shape of the generated cube. If specified then it must be
        a 3-tuple (nz, ny, nx). However, if the data keyword defines a 3D Numpy
        array then the shape of the array is used.
    :param str zaxis_type: The type of Z axis to create. Currently supported
        axis types include: pressure (default), height, level
    """
    if isinstance(data, np.ndarray) and data.ndim == 3:
        shape = data.shape
    else:
        shape = kwargs.get('shape', (5,7,6))
    assert len(shape) == 3, 'shape argument must be of length 3'
    nlevels, nlats, nlons = shape

    rlon_coord = _create_rot_lon_coord(npoints=nlons, coord_sys=kwargs.get('coord_sys'),
        start_lon=kwargs.get('start_lon', 350), end_lon=kwargs.get('end_lon', 365))
    rlat_coord = _create_rot_lat_coord(npoints=nlats, coord_sys=kwargs.get('coord_sys'),
        start_lat=kwargs.get('start_lat', -5), end_lat=kwargs.get('end_lat', 10))
    zcoord = _create_vert_coord(npoints=nlevels, zaxis_type=kwargs.get('zaxis_type'))

    rlons, rlats = np.meshgrid(rlon_coord.points, rlat_coord.points)
    lons, lats = unrotate_pole(rlons, rlats, UKV_POLE_LON, UKV_POLE_LAT)

    lon_coord = AuxCoord(lons, standard_name='longitude', var_name='lon',
        units='degrees_east')
    lat_coord = AuxCoord(lats, standard_name='latitude', var_name='lat',
        units='degrees_north')

    data = _create_data_array(data, shape, dtype=kwargs.get('dtype'))

    cube = iris.cube.Cube(data,
        standard_name=kwargs.get('standard_name', 'air_temperature'),
        long_name=kwargs.get('long_name', 'Air Temperature'),
        var_name=kwargs.get('var_name', 'air_temp'),
        units=kwargs.get('units', 'degC'))

    cube.add_dim_coord(zcoord, 0)
    cube.add_dim_coord(rlat_coord, 1)
    cube.add_dim_coord(rlon_coord, 2)
    cube.add_aux_coord(lat_coord, [1, 2])
    cube.add_aux_coord(lon_coord, [1, 2])

    return cube


def rot_tyx(data=None, **kwargs):
    """
    Create a 3D cube based on a rotated time-lat-long coordinate system.
    The returned cube has the following default properties:

    * shape: (t=12,y=7,x=6)
    * dtype: float32
    * data value: 0
    * X axis: grid longitude
    * Y axis: grid latitude
    * T axis: time as 'days since 1970-01-01' and based upon a 360-day calendar
    * coordinate reference system: rotated lat-long on UM sphere
    * latitude of grid north pole: 37.5 N
    * longitude of grid north pole: 177.5 E
    * standard_name: air_temperature
    * long_name: Air Temperature
    * var_name: air_temp
    * units: degC

    Refer to the :func:`rot_yx` function for a description of common keyword
    arguments. Extra arguments relevant to the current function are shown below.

    :param tuple shape: Shape of the generated cube. If specified then it must be
        a 3-tuple (nt, ny, nx). However, if the data keyword defines a 3D Numpy
        array then the shape of the array is used.
    :param cf_units.Unit tunits: The units to assign to the T axis.
    :param str calendar: The calendar type to assign to the T axis if the units
        are not defined via the tunits keyword.
    """
    if isinstance(data, np.ndarray) and data.ndim == 3:
        shape = data.shape
    else:
        shape = kwargs.get('shape', (12,7,6))
    assert len(shape) == 3, 'shape argument must be of length 3'
    ntimes, nlats, nlons = shape

    rlon_coord = _create_rot_lon_coord(npoints=nlons, coord_sys=kwargs.get('coord_sys'),
        start_lon=kwargs.get('start_lon', 350), end_lon=kwargs.get('end_lon', 365))
    rlat_coord = _create_rot_lat_coord(npoints=nlats, coord_sys=kwargs.get('coord_sys'),
        start_lat=kwargs.get('start_lat', -5), end_lat=kwargs.get('end_lat', 10))
    tcoord = _create_time_coord(npoints=ntimes, units=kwargs.get('tunits'),
        calendar=kwargs.get('calendar'))

    rlons, rlats = np.meshgrid(rlon_coord.points, rlat_coord.points)
    lons, lats = unrotate_pole(rlons, rlats, UKV_POLE_LON, UKV_POLE_LAT)

    lon_coord = AuxCoord(lons, standard_name='longitude', var_name='lon',
        units='degrees_east')
    lat_coord = AuxCoord(lats, standard_name='latitude', var_name='lat',
        units='degrees_north')

    data = _create_data_array(data, shape, dtype=kwargs.get('dtype'))

    cube = iris.cube.Cube(data,
        standard_name=kwargs.get('standard_name', 'air_temperature'),
        long_name=kwargs.get('long_name', 'Air Temperature'),
        var_name=kwargs.get('var_name', 'air_temp'),
        units=kwargs.get('units', 'degC'))

    cube.add_dim_coord(tcoord, 0)
    cube.add_dim_coord(rlat_coord, 1)
    cube.add_dim_coord(rlon_coord, 2)
    cube.add_aux_coord(lat_coord, [1, 2])
    cube.add_aux_coord(lon_coord, [1, 2])

    return cube


def bng_yx(data=None, **kwargs):
    """
    Create a 2D cube based on the British National Grid coordinate system.
    The returned cube has the following default properties:

    * shape: (y=7,x=6)
    * dtype: float32
    * data value: 0
    * X axis: BNG eastings
    * Y axis: BNG northings
    * coordinate reference system: OSGB
    * standard_name: air_temperature
    * long_name: Air Temperature
    * var_name: air_temp
    * units: degC

    Refer to the :func:`geo_yx` function for a description of common keyword
    arguments. Extra arguments relevant to the current function are shown below.

    :param bool aux_lat_lon: If this argument evaluates true then auxiliary
        latitude and longitude coordinates are added to the returned cube.
    """
    if isinstance(data, np.ndarray) and data.ndim == 2:
        shape = data.shape
    else:
        shape = kwargs.get('shape', (7,6))
    assert len(shape) == 2, 'shape argument must be of length 2'
    ny, nx = shape

    xcoord = _create_bng_x_coord(npoints=nx)
    ycoord = _create_bng_y_coord(npoints=ny)

    data = _create_data_array(data, shape, dtype=kwargs.get('dtype'))

    cube = iris.cube.Cube(data,
        standard_name=kwargs.get('standard_name', 'air_temperature'),
        long_name=kwargs.get('long_name', 'Air Temperature'),
        var_name=kwargs.get('var_name', 'air_temp'),
        units=kwargs.get('units', 'degC'))

    cube.add_dim_coord(ycoord, 0)
    cube.add_dim_coord(xcoord, 1)

    if kwargs.get('aux_lat_lon'):
        geog_cs = DEFAULT_CRS.as_cartopy_crs()
        bng_cs = xcoord.coord_system.as_cartopy_crs()
        xc, yc = np.meshgrid(xcoord.points, ycoord.points)
        lon_lat_ht = geog_cs.transform_points(bng_cs, xc, yc)
        lons, lats = lon_lat_ht[:,:,0], lon_lat_ht[:,:,1]
        lon_coord = AuxCoord(lons, standard_name='longitude', var_name='lon',
            units='degrees_east')
        lat_coord = AuxCoord(lats, standard_name='latitude', var_name='lat',
            units='degrees_north')
        cube.add_aux_coord(lat_coord, [0, 1])
        cube.add_aux_coord(lon_coord, [0, 1])

    return cube


def bng_zyx(data=None, **kwargs):
    """
    Create a 3D cube based on the British National Grid coordinate system.
    The returned cube has the following default properties:

    * shape: (z=5,y=7,x=6)
    * dtype: float32
    * data value: 0
    * X axis: BNG eastings
    * Y axis: BNG northings
    * Z axis: height
    * coordinate reference system: OSGB
    * standard_name: air_temperature
    * long_name: Air Temperature
    * var_name: air_temp
    * units: degC

    Refer to the :func:`geo_yx` function for a description of common keyword
    arguments. Extra arguments relevant to the current function are shown below.

    :param tuple shape: Shape of the generated cube. If specified then it must be
        a 3-tuple (nz, ny, nx). However, if the data keyword defines a 3D Numpy
        array then the shape of the array is used.
    :param bool aux_lat_lon: If this argument evaluates true then auxiliary
        latitude and longitude coordinates are added to the returned cube.
    """
    if isinstance(data, np.ndarray) and data.ndim == 3:
        shape = data.shape
    else:
        shape = kwargs.get('shape', (5,7,6))
    assert len(shape) == 3, 'shape argument must be of length 3'
    nlevels, ny, nx = shape

    xcoord = _create_bng_x_coord(npoints=nx)
    ycoord = _create_bng_y_coord(npoints=ny)
    zcoord = _create_vert_coord(npoints=nlevels, zaxis_type='height')

    data = _create_data_array(data, shape, dtype=kwargs.get('dtype'))

    cube = iris.cube.Cube(data,
        standard_name=kwargs.get('standard_name', 'air_temperature'),
        long_name=kwargs.get('long_name', 'Air Temperature'),
        var_name=kwargs.get('var_name', 'air_temp'),
        units=kwargs.get('units', 'degC'))

    cube.add_dim_coord(zcoord, 0)
    cube.add_dim_coord(ycoord, 1)
    cube.add_dim_coord(xcoord, 2)

    if kwargs.get('aux_lat_lon'):
        geog_cs = DEFAULT_CRS.as_cartopy_crs()
        bng_cs = xcoord.coord_system.as_cartopy_crs()
        xc, yc = np.meshgrid(xcoord.points, ycoord.points)
        lon_lat_ht = geog_cs.transform_points(bng_cs, xc, yc)
        lons, lats = lon_lat_ht[:,:,0], lon_lat_ht[:,:,1]
        lon_coord = AuxCoord(lons, standard_name='longitude', var_name='lon',
            units='degrees_east')
        lat_coord = AuxCoord(lats, standard_name='latitude', var_name='lat',
            units='degrees_north')
        cube.add_aux_coord(lat_coord, [1, 2])
        cube.add_aux_coord(lon_coord, [1, 2])

    return cube


def bng_tyx(data=None, **kwargs):
    """
    Create a 3D cube based on the British National Grid coordinate system.
    The returned cube has the following default properties:

    * shape: (t=12,y=7,x=6)
    * dtype: float32
    * data value: 0
    * X axis: BNG eastings
    * Y axis: BNG northings
    * T axis: time as 'days since 1970-01-01' and based upon a 360-day calendar
    * coordinate reference system: OSGB
    * standard_name: air_temperature
    * long_name: Air Temperature
    * var_name: air_temp
    * units: degC

    Refer to the :func:`geo_yx` function for a description of common keyword
    arguments. Extra arguments relevant to the current function are shown below.

    :param tuple shape: Shape of the generated cube. If specified then it must be
        a 3-tuple (nt, ny, nx). However, if the data keyword defines a 3D Numpy
        array then the shape of the array is used.
    :param cf_units.Unit tunits: The units to assign to the T axis.
    :param str calendar: The calendar type to assign to the T axis if the units
        are not defined via the tunits keyword.
    :param bool aux_lat_lon: If this argument evaluates true then auxiliary
        latitude and longitude coordinates are added to the returned cube.
    """
    if isinstance(data, np.ndarray) and data.ndim == 3:
        shape = data.shape
    else:
        shape = kwargs.get('shape', (12,7,6))
    assert len(shape) == 3, 'shape argument must be of length 34'
    ntimes, ny, nx = shape

    xcoord = _create_bng_x_coord(npoints=nx)
    ycoord = _create_bng_y_coord(npoints=ny)
    tcoord = _create_time_coord(npoints=ntimes, units=kwargs.get('tunits'),
        calendar=kwargs.get('calendar'))

    data = _create_data_array(data, shape, dtype=kwargs.get('dtype'))

    cube = iris.cube.Cube(data,
        standard_name=kwargs.get('standard_name', 'air_temperature'),
        long_name=kwargs.get('long_name', 'Air Temperature'),
        var_name=kwargs.get('var_name', 'air_temp'),
        units=kwargs.get('units', 'degC'))

    cube.add_dim_coord(tcoord, 0)
    cube.add_dim_coord(ycoord, 1)
    cube.add_dim_coord(xcoord, 2)

    if kwargs.get('aux_lat_lon'):
        geog_cs = DEFAULT_CRS.as_cartopy_crs()
        bng_cs = xcoord.coord_system.as_cartopy_crs()
        xc, yc = np.meshgrid(xcoord.points, ycoord.points)
        lon_lat_ht = geog_cs.transform_points(bng_cs, xc, yc)
        lons, lats = lon_lat_ht[:,:,0], lon_lat_ht[:,:,1]
        lon_coord = AuxCoord(lons, standard_name='longitude', var_name='lon',
            units='degrees_east')
        lat_coord = AuxCoord(lats, standard_name='latitude', var_name='lat',
            units='degrees_north')
        cube.add_aux_coord(lat_coord, [1, 2])
        cube.add_aux_coord(lon_coord, [1, 2])

    return cube


def _create_lat_coord(start_lat=-90.0, end_lat=90.0, npoints=7, coord_sys=None):
    """Create a geodetic latitude coordinate object."""
    points = np.linspace(start_lat, end_lat, npoints)
    lat_coord = DimCoord(points, standard_name='latitude', var_name='lat',
        units='degrees_north')
    lat_coord.coord_system = coord_sys or DEFAULT_CRS
    lat_coord.guess_bounds()
    if afterburner.compare_iris_version('2', 'lt'):
        np.clip(lat_coord.bounds, -90.0, 90.0, out=lat_coord.bounds)
    return lat_coord


def _create_lon_coord(start_lon=0.0, end_lon=360.0, npoints=6, coord_sys=None):
    """Create a geodetic longitude coordinate object."""
    points = np.linspace(start_lon, end_lon, npoints, endpoint=0)
    lon_coord = DimCoord(points, standard_name='longitude', var_name='lon',
        units='degrees_east')
    lon_coord.coord_system = coord_sys or DEFAULT_CRS
    lon_coord.circular = True
    lon_coord.guess_bounds()
    return lon_coord


def _create_rot_lat_coord(start_lat=-5.0, end_lat=10.0, npoints=7, coord_sys=None):
    """Create a rotated latitude coordinate object for the UKV domain."""
    points = np.linspace(start_lat, end_lat, npoints)
    rlat_coord = DimCoord(points, standard_name='grid_latitude',
        var_name='rlat', units='degrees')
    rlat_coord.coord_system = coord_sys or DEFAULT_ROT_CRS
    rlat_coord.guess_bounds()
    if afterburner.compare_iris_version('2', 'lt'):
        np.clip(rlat_coord.bounds, -90.0, 90.0, out=rlat_coord.bounds)
    return rlat_coord


def _create_rot_lon_coord(start_lon=350.0, end_lon=365.0, npoints=6, coord_sys=None):
    """Create a rotated longitude coordinate object for the UKV domain."""
    points = np.linspace(start_lon, end_lon, npoints, endpoint=0)
    rlon_coord = DimCoord(points, standard_name='grid_longitude',
        var_name='rlon', units='degrees')
    rlon_coord.coord_system = coord_sys or DEFAULT_ROT_CRS
    rlon_coord.guess_bounds()
    return rlon_coord


def _create_bng_x_coord(npoints=6):
    points = np.linspace(100000, 125000, npoints)
    xcoord = DimCoord(points, standard_name='projection_x_coordinate',
        var_name='bng_east', units='m')
    xcoord.coord_system = OSGB()
    xcoord.guess_bounds()
    return xcoord


def _create_bng_y_coord(npoints=7):
    points = np.linspace(200000, 230000, npoints)
    ycoord = DimCoord(points, standard_name='projection_y_coordinate',
        var_name='bng_north', units='m')
    ycoord.coord_system = OSGB()
    ycoord.guess_bounds()
    return ycoord


def _create_vert_coord(npoints=5, zaxis_type=None):
    """Create a vertical coordinate object."""
    if not zaxis_type: zaxis_type = 'pressure'

    if zaxis_type == 'pressure':
        levels = np.linspace(1000, 0, npoints)
        zcoord = DimCoord(levels, long_name='pressure', units='hPa')
    elif zaxis_type == 'height':
        levels = np.linspace(0, 1000, npoints)
        zcoord = DimCoord(levels, standard_name='height', units='m')
    elif zaxis_type == 'level':
        levels = np.arange(npoints)
        zcoord = DimCoord(levels, standard_name='model_level_number', units='1')
    else:
        msg = ("Unsupported Z-axis type: {0}.\nCurrently supported axis types "
               "include: pressure, height, level".format(zaxis_type))
        raise ValueError(msg)

    return zcoord


def _create_time_coord(npoints=12, units=None, calendar=None):
    """Create a time coordinate object."""
    times = np.arange(15, npoints*30+15, 30)
    if not units:
        units = cf_units.Unit('days since 1970-01-01', calendar=calendar or DEFAULT_CALENDAR)
    tcoord = DimCoord(times, standard_name='time', units=units)
    if npoints > 1: tcoord.guess_bounds()
    return tcoord


def _create_ens_coords(npoints=3):
    """Create ensemble number and ensemble id coordinate objects."""
    nums = range(1, npoints+1)
    ids = ['r%si1p1'%i for i in nums]
    rcoord = DimCoord(nums, standard_name='realization', units='1')
    ecoord = AuxCoord(ids, long_name='ensemble_id')
    return rcoord, ecoord


def _create_data_array(data, shape, dtype=None):
    """
    Create a data array of the given shape and type, initialised with the value,
    or values, if any, passed in via the data argument.
    """
    if not dtype: dtype = 'f4'

    _data = np.empty(shape, dtype=dtype)
    if isinstance(data, np.ndarray) and data.shape == shape:
        _data = data[:]
    elif isinstance(data, np.ndarray) and data.shape == shape[0:1]:
        np.rollaxis(_data, 0, _data.ndim)[:] = data
    elif _is_numeric(data):
        _data.fill(data)
    else:
        _data.fill(0)

    return _data


def _is_numeric(x):
    """Test for x being a numeric value."""
    return isinstance(x, (float, integer_types))
