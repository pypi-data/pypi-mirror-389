Tutorial #9: Coordinate Transformations
=======================================

This tutorial describes the classes and objects provided by the ``afterburner``
Python package for applying geodetic transformations to geospatial coordinates.
By way of a recap, a coordinate transform operation is a mathematical procedure
for transforming spatial coordinates from a source coordinate reference system
(CRS; e.g. Ordnance Survey GB 1936) to a target coordinate reference system.

The iris package and, more especially, the cartopy package provide some low-level
functionality for performing coordinate transformations. Within the cartopy package
the main functions of relevance are the ``transform_point`` and ``transform_points``
methods attached to the ``cartopy.CRS`` class.

The ``afterburner.coords`` module contains a dedicated Python class - the ``CoordTransformer``
class - which provides a unified interface to the aforementioned cartopy methods
(which present slightly different signatures to client programs). The ``CoordTransformer.transform()``
method accepts either single coordinate values, or arrays of coordinate values,
and takes care of handing these over, in the right order, to the correct cartopy
method.

.. tip:: Refer to :doc:`Tutorial #1 </tutorials/accessing_afterburner>` for information
   on how to configure your Python environment to access the afterburner Python
   package.

Let's kick things off by transforming a single latitude-longitude location --
that of the Met Office HQ -- from the OSGB 1936 CRS to the WGS 1984 CRS. We'll
start off doing this the long, manual way, after which we'll demonstrate a quicker,
more convenient method::

    >>> import cartopy.crs as ccrs
    >>> from afterburner.coords import CoordTransformer

    >>> # define the location of the Met Office HQ in OSGB 1936 lat-long coords
    >>> hq_lon, hq_lat = -3.473658, 50.726728

    >>> # define an OSGB 1936 geodetic coordinate system object.
    >>> osgb36_pcrs = ccrs.OSGB()
    >>> osgb36_pcrs.globe.towgs84 = '446.448,-125.157,542.06'   # WGS84 transform parameters
    >>> osgb36_gcrs = osgb36_pcrs.as_geodetic()

    >>> # define a WGS 1984 geodetic coordinate system object.
    >>> wgs84_gcrs = ccrs.Geodetic(ccrs.Globe(datum='WGS84'))

    >>> # create an OSGB 1936 to WGS 1984 geodetic coordinate transform object.
    >>> coord_trans = CoordTransformer(osgb36_gcrs, wgs84_gcrs, 'OSGB 1936 to WGS 1984')

    >>> # transform the coordinates to WGS 1984 - note the order of the arguments
    >>> coord_trans.transform(hq_lon, hq_lat)
    (-3.474856, 50.727281)

In the case where single coordinate values are passed to the ``transform()`` method,
as done above, then a 2-tuple of transformed coordinates is returned. Later on we'll
see how *arrays* of coordinate values are handled.

So that was the long-hand method of applying this particular coordinate transformation.
However, since the transformation of OSGB 1936 coordinates to WGS 1984 coordinates is
such a commonly-encountered operation (at least for UK users!), the ``afterburner.coords``
module includes a pre-canned instance of the ``CoordTransformer`` class to do just that
operation. The instance is named ``OSGB36_GCRS_TO_WGS84_GCRS``.

Here's how the code would look if we were to use this instance::

    >>> from afterburner.coords import OSGB36_GCRS_TO_WGS84_GCRS

    >>> # define the location of the Met Office HQ in OSGB 1936 lat-long coords
    >>> hq_lon, hq_lat = -3.473658, 50.726728

    >>> # transform the coordinates to WGS 1984
    >>> OSGB36_GCRS_TO_WGS84_GCRS.transform(hq_lon, hq_lat)
    (-3.474856, 50.727281)

In a similar vein, the ``CoordTransformer`` instance named ``OSGB36_PCRS_TO_WGS84_GCRS``
may be used to transform OSGB 1936 *projected X-Y coordinates* to WGS 1984 lat-long
coordinates. The code snippet below illustrates this transformation using the X-Y
coordinates for the Met Office HQ::

    >>> from afterburner.coords import OSGB36_PCRS_TO_WGS84_GCRS

    >>> # define the location of the Met Office HQ in OSGB 1936 projected X-Y (transverse mercator) coords
    hq_x, hq_y = 296000.0, 93000.0

    >>> # transform the X-Y coordinates to WGS 1984 lat-long coordinates
    >>> OSGB36_PCRS_TO_WGS84_GCRS.transform(hq_x, hq_y)
    (-3.474856, 50.727281)

The inverse of the coordinate transformations used in the last two examples are
made available via the objects named ``WGS84_GCRS_TO_OSGB36_GCRS`` and
``WGS84_GCRS_TO_OSGB36_PCRS`` in the ``afterburner.coords module``. These objects
are utilised in a similar manner to that shown above.

So far we have only transformed the coordinates for single point locations. However,
the ``CoordTransformer.transform()`` method can accept accept numpy arrays of x, y,
and optionally z (i.e. height) coordinates. The code snippet below illustrates the
transformation of arrays of latitude-longitude coordinates extracted from a cube.
Notice that the ``numpy.meshgrid()`` function is used here to create a rectangular
array of latitude-longitude coordinate pairs from the corresponding DimCoord objects
attached to the cube::

    >>> import numpy as np
    >>> from afterburner.coords import OSGB36_GCRS_TO_WGS84_GCRS

    >>> # load a cube and read its lat & long coordinates (OSGB 1936)
    >>> cube = iris.load_cube('testfile', 'surface_temperature')
    >>> lat_crd = cube.coord('latitude')
    >>> lat_crd.points.shape
    (19,)
    >>> lon_crd = cube.coord('longitude')
    >>> lon_crd.points.shape
    (18,)

    >>> # create a rectangular array of the lat & long coordinates
    >>> lons, lats = np.meshgrid(lon_crd.points, lat_crd.points)
    >>> lons.shape
    (19, 18)
    >>> lats.shape
    (19, 18)

    >>> # transform the lat-long coordinates to WGS 1984
    >>> lon_lat_ht = OSGB36_GCRS_TO_WGS84_GCRS.transform(lons, lats)
    >>> lon_lat_ht.shape
    (19, 18, 3)
    >>> lon_lat_ht[0,0,:]
    array([-3.474856, 50.727281, 49.281185])

At present the ``transform()`` method does not permit three scalar values to be
passed in for the x/longitude, y/latitude, and z/height coordinates. As a workaround,
however, it is fairly easy to achieve this by passing in length-1 numpy arrays, as
shown below::

    >>> lat, lon, ht = 50.726728, -3.473658, 30.0
    >>> lon_lat_ht = OSGB36_GCRS_TO_WGS84_GCRS.transform(np.array(lon), np.array(lat), np.array(ht))
    >>> lon_lat_ht.shape
    (1, 3)
    >>> lon_lat_ht
    array([-3.474856, 50.727281, 79.280571])

That's all for this tutorial. Further information regarding the ``CoordTransformer``
class can be found in the :class:`API reference documentation <afterburner.coords.CoordTransformer>`.

Back to the :doc:`Tutorial Index <index>`
