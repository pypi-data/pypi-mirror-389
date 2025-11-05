Tutorial #3: Introduction to Spatial Statistical Functions
==========================================================

This tutorial provides a brief overview of the convenience functions in the
Afterburner package for calculating simple spatial statistics from Iris cubes;
for example the area-weighted mean of a global dataset. A :doc:`separate tutorial </tutorials/temporal_stats>`
covers the analogous functions for generating temporal statistics from Iris cubes

.. tip:: Refer to :doc:`Tutorial #1 </tutorials/accessing_afterburner>` for information
   on how to configure your Python environment to access the afterburner Python
   package.

The spatial statistics functions live in a module named ``afterburner.stats.spatial``.
Here's how you can import the ``spatial`` module. We'll also import the ``iris``
package while we're at it since that is used in the later code examples:

>>> import iris
>>> from afterburner.stats import spatial

At present the spatial module contains just a single function called ``calc_spatial_stat()``.
Essentially this function is a wrapper around Iris's ``cube.collapsed()`` method;
it can conveniently be used to calculate any Iris-supported statistical measure,
either for a single cube or for a list of cubes. The ``calc_spatial_stat()``
function takes care of iterating over multiple cubes (if need be), and of selecting
the appropriate spatial dimensions to use. It will also calculate things like area
weights if they are required.

Calculating Spatial Averages
----------------------------

Assuming that we have previously loaded a cube of global monthly-mean air
temperature data for the 10-year period 2000-01-01 to 2010-01-01, here's how you
could generate a cube of globally-averaged data values for each 2D horizontal
slice of the input cube:

>>> print(cube)
air_temperature / (degC)          (time: 120; latitude: 19; longitude: 36)
    Dimension coordinates:
        time                           x             -             -
        latitude                       -             x             -
        longitude                      -             -             x
    Cell methods:
        mean: time (1 hour)
>>> mean_cube = spatial.calc_spatial_stat(cube, iris.analysis.MEAN)
>>> print(mean_cube)
air_temperature / (degC)          (time: 120)
    Dimension coordinates:
        time                           x
    Scalar coordinates:
        latitude: 0.0 degrees_north, bound=(-90.0, 90.0) degrees_north
        longitude: 180.0 degrees_east, bound=(0.0, 360.0) degrees_east
    Cell methods:
        mean: time (1 hour)
        mean: latitude, longitude

As can be seen, the latitude and longitude dimensions are collapsed to single
points in the resulting cube.

By default, the ``iris.analysis.MEAN`` aggregator computes a simple *unweighted*
mean from the cube's data array. Often, however, it is desirable to compute the
*area-weighted* mean. This is readily achieved by including the ``area_weighted``
argument in the function call, as follows:

>>> mean_cube = spatial.calc_spatial_stat(cube, iris.analysis.MEAN, area_weighted=True)

If the input cube contains a cell measure named ‘area’, then the area values
associated with that measure will be used as the area weights. Otherwise the cell
areas are computed using the ``iris.analysis.cartography.area_weights()`` function.
If necessary the array of area weights will be broadcast to the same shape as the
cube's data array.

Alternatively, an array of area weights can be specified explicitly by adding a
‘weights’ key to the optional ``agg_opts`` dictionary argument. Here's how you
can do this:

>>> weights = calc_area_weights()   # your function for calculating area weights
>>> mean_cube = spatial.calc_spatial_stat(cube, iris.analysis.MEAN, agg_opts={'weights': weights})

Passing a Cube or Cubelist
--------------------------

In each of the code snippets above we specified a single input cube, and received
a single cube by way of a return result. Alternatively, it is possible to pass
in a cubelist -- of any length -- and receive a same-length cubelist in return.
The exception occurs when the ``append_to_cubelist`` keyword argument is set to
true. In this case the new cubes of computed statistical measures get *appended*
to the input cubelist.

Two further keyword arguments come into play when a cubelist is passed to the
``calc_spatial_stat()`` function: ``cubes_alike`` and ``stop_on_error``.

If ``cubes_alike`` is set to true then all cubes are assumed to have the same
spatial domain, which means that area weights (for example) need only be computed
once, with concomitant gains in efficiency.

If ``stop_on_error`` is set to true then an exception will be raised immediately
an error is encountered processing one of the input cubes; no further cubes will
be processed. The default behaviour though is to log an error message and continue
processing the remaining cubes in the input cubelist.

Masking Input Data
------------------

If it’s required to calculate a statistical measure over a *subset*, or region,
of each cube’s grid cells (just land cells, for example) then this can be achieved
by specifying a suitable mask array via the ``mask`` argument to the ``calc_spatial_stat()``
function, like this:

>>> result_cube = calc_spatial_stat(cube, iris.analysis.MEAN, mask=ocean_mask)

In this case the statistic will be calculated using only those grid cells that are
*not* masked out by the mask array. Or, put another way, array elements that are
masked out in the mask array will be masked out in a temporary copy of the cube’s
data array.

The mask array must have the same shape as that of the spatial dimensions over
which the mean (or whatever statistic) is being computed. For instance, if the
input cube has dimensions (t=120, y=181, x=360) then the mask array must have a
shape of (181, 360).

(An alternative approach, of course, is to extract a spatial subset of the original
cube(s) and pass the reduced cube(s) to the ``calc_spatial_stat()`` function. This
method has the disadvantage, when working with large cubelists, of having to create
intermediate copies of those cubes in order to yield the desired results.)

If the mask array contains fractional area values then the ``mask_is_area_frac``
keyword argument may be used to request that these are used to multiply through
each input cube before calculating the statistical measure, as illustrated below:

>>> result_cube = calc_spatial_stat(cube, iris.analysis.MEAN, mask=land_area_frac,
...     mask_is_area_frac=True)

Specifying Spatial Dimensions
-----------------------------

Unless specified otherwise, the ``calc_spatial_stat()`` function assumes that the
coordinate dimensions (the axes) over which to calculate the required statistical
measure are named 'latitude' and 'longitude'. The ``coords`` keyword argument can
be used to specify alternative dimensions over which to aggregate.

In the following example, the standard deviation is calculated for a cube of air
temperature whose horizontal dimensions are defined by rotated grid latitude and
longitude coordinates:

>>> print(cube)
air_temperature / (degC)          (time: 12; grid_latitude: 19; grid_longitude: 36)
    Dimension coordinates:
        time                           x                  -                  -
        grid_latitude                  -                  x                  -
        grid_longitude                 -                  -                  x
>>> std_cube = spatial.calc_spatial_stat(cube, iris.analysis.STD_DEV,
...     coords=['grid_latitude', 'grid_longitude'])
>>> print(std_cube)
air_temperature / (degC)          (time: 12)
    Dimension coordinates:
        time                           x
    Scalar coordinates:
        grid_latitude: 0.0 degrees_north, bound=(-90.0, 90.0) degrees_north
        grid_longitude: 180.0 degrees_east, bound=(0.0, 360.0) degrees_east
    Cell methods:
        mean: time (1 hour)
        standard_deviation: grid_latitude, grid_longitude

The order of the coordinates is not significant. In the above code snippet, for
example, the function call could have been expressed thus:

>>> std_cube = spatial.calc_spatial_stat(cube, iris.analysis.STD_DEV,
...     coords=['grid_longitude', 'grid_latitude'])

The procedure is similar when dealing with data discretised on a *projected*
coordinate reference system, such as the British National Grid. In this case the
coordinates to specify are named 'projection_x_coordinate' and 'projection_y_coordinate',
as illustrated below:

>>> mean_cube = spatial.calc_spatial_stat(cube, iris.analysis.MEAN,
...    coords=['projection_x_coordinate', 'projection_y_coordinate'])

Going Beyond Two Dimensions
---------------------------

Thus far the code examples have been limited to calculating statistics for 2D
(e.g. latitude-longitude or X-Y) slices of the input cube or cubes. However, the
``calc_spatial_stat()`` function, just like the ``cube.collapsed()`` method which
it wraps, will happily work with any or all of the dimensions associated with a
cube.

In the following example, each 3D chunk of a 4D cube of temperature data (again!)
is averaged:

>>> print(cube)
air_temperature / (degC)          (time: 12; pressure: 5; latitude: 19; longitude: 36)
    Dimension coordinates:
        time                           x             -            -              -
        pressure                       -             x            -              -
        latitude                       -             -            x              -
        longitude                      -             -            -              x
     Cell methods:
        mean: time (1 hour)
>>> coord_names = [c.name() for c in cube.coords()]
>>> coord_names
['time', 'pressure', 'latitude', 'longitude']
>>> mean_cube = spatial.calc_spatial_stat(cube, iris.analysis.MEAN, coords=coord_names[1:])
>>> print(mean_cube)
air_temperature / (degC)          (time: 12)
    Dimension coordinates:
        time                           x
    Scalar coordinates:
        latitude: 0.0 degrees_north, bound=(-90.0, 90.0) degrees_north
        longitude: 180.0 degrees_east, bound=(0.0, 360.0) degrees_east
    Cell methods:
        mean: time (1 hour)
        mean: pressure, latitude, longitude

Taken to the limit, we could compute the average over *all* dimensions, i.e. for
the whole data array attached to a cube. In that case, however, it would usually
make more sense -- and be more efficient -- to call the relevant numpy function
directly (``numpy.ma.average`` in this instance):

>>> mean_cube = spatial.calc_spatial_stat(cube, iris.analysis.MEAN, coords=coord_names)
>>> import numpy as np
>>> mean = np.ma.average(cube.data)
>>> mean_cube.data == mean
True


That wraps up this tutorial. You can read more about the ``spatial`` module in
the :mod:`API reference documentation <afterburner.stats.spatial>`.

Back to the :doc:`Tutorial Index <index>`
