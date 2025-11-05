Tutorial #7: Cube Utility Functions
===================================

This tutorial demonstrates a number of the utility functions for working with Iris
cubes that are provided by the :mod:`afterburner.utils.cubeutils` module.

.. tip:: Refer to :doc:`Tutorial #1 </tutorials/accessing_afterburner>` for information
   on how to configure your Python environment to access the afterburner Python
   package.

Extracting a Time Slice from a Cube
-----------------------------------

Extracting a subset of a cube along its time axis (aka dimension) is a fairly
common operation. Curiously, however, the Iris package does not (yet) include a
convenience function for achieving this task. The ``cubeutils.extract_time_slice()``
function provides a quick-and-easy method for doing so. The code fragment below
illustrates how to extract a 2-year chunk of data from a cube of monthly-mean
surface temperature data for the 10-year period 2000-01-01 to 2010-01-01 (outer
time bounds)::

    >>> import iris
    >>> from afterburner.utils import cubeutils
    >>> testcube = iris.load_cube('testfile.nc', 'surface_temperature')
    >>> print(testcube.summary(shorten=True))
    air_temperature / (degC)            (time: 120; latitude: 19; longitude: 36)
    >>> tcoord = testcube.coord('time')
    >>> print(tcoord[0], tcoord[-1])
    DimCoord([2000-01-16 00:00:00], ...), DimCoord([2009-12-16 00:00:00], ...)
    >>> # extract 2-year chunk of data
    >>> subcube = cubeutils.extract_time_slice(testcube, ('2003-01-01', '2005-01-01'))
    >>> print(subcube.summary(shorten=True))
    air_temperature / (degC)            (time: 24; latitude: 19; longitude: 36)
    >>> tcoord = subcube.coord('time')
    >>> print(tcoord[0], tcoord[-1])
    DimCoord([2003-01-16 00:00:00], ...), DimCoord([2004-12-16 00:00:00], ...)

By default the ``extract_time_slice()`` function looks for a time coordinate named
‘time’. If the time coordinate in your cube is named differently then it can be
specified via the ``coord_name`` keyword argument, as the code example below shows::

    >>> subcube = cubeutils.extract_time_slice(testcube, ('2003-01-01', '2005-01-01'),
    ...     coord_name='someothertime')

The time range to extract can be specified either as a tuple (or list) of date-time
strings, as shown in the previous examples, or as an ``afterburner.utils.dateutils.DateTimeRange``
object. However, unless your code has already created an instance of the latter
class (e.g. as part of some earlier task) then there is no real advantage to
creating one just for the time-slicing operation since passing a tuple of strings
will usually be quicker and easier.

Note that the time range is treated as a *left-closed* interval, i.e.
start-time <= T < end-time, where T represents the set of time instants attached
to the cube’s time dimension. Thus, for the cube of monthly-mean data used above,
we could have defined the time range as follows and obtained the same result::

    >>> # add a small increment (1 hour in this case) to the desired end date
    >>> subcube = cubeutils.extract_time_slice(testcube, ('2003-01-16', '2004-12-16T01'))
    >>> print(subcube.summary(shorten=True))
    air_temperature / (degC)            (time: 24; latitude: 7; longitude: 6)
    >>> tcoord = subcube.coord('time')
    >>> print(tcoord[0], tcoord[-1])
    DimCoord([2003-01-16 00:00:00], ...), DimCoord([2004-12-16 00:00:00], ...)

Extracting a Geographical Region from a Cube
--------------------------------------------

Another common cube subsetting operation is to extract a geographical region.
The ``cubeutils.extract_lat_long_region()`` function allows you to extract a
rectangular region defined by latitude/longitude or grid-latitude/grid-longitude
coodinates. Taking the example cube of global monthly-mean temperature data used
above, we could extract the data covering the (approximate) tropical region of
the eastern hemisphere as follows::

    >>> import iris
    >>> import iris.coords
    >>> from afterburner.utils import cubeutils
    >>> testcube = iris.load_cube('testfile.nc', 'surface_temperature')
    >>> lat_extent = iris.coords.CoordExtent('latitude', -23.5, 23.5)
    >>> lon_extent = iris.coords.CoordExtent('longitude', 0.0, 180.0)
    >>> subcube = cubeutils.extract_lat_long_region(testcube, lat_extent, lon_extent)

The region to extract can be specified using either ``iris.coords.CoordExtent``
objects (as shown above) or ``afterburner.coords.CoordRange`` objects. The latter
can be useful when you wish to extract a number of contiguous, *non-overlapping*
regions from a parent cube. By way of illustration, the following code based on
``CoordExtent`` objects would result in two regions (the southern and northern
hemispheres) in which data points along the Equator would be present in *both*
cubes. In many data analysis scenarios this duplication of data points would
typically be undesirable::

    >>> lat_extent = iris.coords.CoordExtent('latitude', -90, 0.0)
    >>> lon_extent = iris.coords.CoordExtent('longitude', 0.0, 360.0)
    >>> region1 = cubeutils.extract_lat_long_region(testcube, lat_extent, lon_extent)
    >>> lat_extent = iris.coords.CoordExtent('latitude', 0.0, 90.0)
    >>> region2 = cubeutils.extract_lat_long_region(testcube, lat_extent, lon_extent)

This issue can be addressed in a couple of ways. Firstly, by using the ``min_exclusive``
and/or ``max_exclusive`` keyword arguments supported by the ``iris.coords.CoordExtent``
class. Or, secondly, by specifying closed or half-closed intervals using the
``afterburner.coords.CoordRange`` class, thus::

    >>> import afterburner.coords
    >>> lat_extent = afterburner.coords.CoordRange([-90, 0.0], leftclosed=True)
    >>> lon_extent = afterburner.coords.CoordRange([0.0, 360.0], leftclosed=True)
    >>> region1 = cubeutils.extract_lat_long_region(testcube, lat_extent, lon_extent)
    >>> lat_extent = afterburner.coords.CoordRange([0.0, 90.0], , closed=True)
    >>> region2 = cubeutils.extract_lat_long_region(testcube, lat_extent, lon_extent)

NB: The above example assumes that there are data points at the north and south
poles, and that these points are required in the extracted regional cube. If that’s
not the case then the interval types for the two *latitude* extent objects above
should be set to ``open`` and ``leftclosed``, respectively.

By default the test for a grid point falling within, or on, the boundaries of the
rectangle defined by ``lat_extent`` and ``lon_extent`` is done using each grid
cell’s *bounding coordinates*, assuming these are present. If it is desired to
perform the containment test using just the grid point coordinates then the
``extract_lat_long_region()`` function’s ``ignore_bounds`` keyword should be set
to True. If the coordinate axis in question does not possess cell bounds then
this argument is silently ignored.

Creating Decadal and Multi-Year Categorical Coordinates
-------------------------------------------------------

The Iris package contains a number of convenience functions for adding time-related
categorical coordinates to a cube. These are provided by the ``iris.coord_categorisation``
module.

The existing coordinate categorisation functions cover the commonly-used time periods,
namely hours, days, months, seasons and years. The ``afterburner.utils.cubeutils``
module includes additional functions for creating auxiliary categorical coordinates
spanning decades, model decades, and multiple years. These can be of utility in
generating, for example, multi-year climatological statistics.

To create an auxiliary coordinate that categorises the decadal periods associated
with a cube’s time dimension one would call the ``cubeutils.add_decade_aux_coord()``
function, which has the following signature::

    add_decade_aux_coord(cube, time_coord, name='decade')

The ``time_coord`` argument should either be an ``iris.coords.DimCoord`` object
or the name of the time dimension.

By ‘decade’ we mean the familiar 10-year periods commencing at midnight Jan 1 on
years that are whole multiples of 10, e.g. 1970-1980, 1980-1990, and so on. The
values of the newly created auxiliary coordinate are the mid-years of the decade,
e.g. 1975, 1985, etc. The month number and day-of-month number are both implied,
each having the value 1.

The following code snippet illustrates adding a decade auxiliary coordinate to a
cube::

    >>> from afterburner.utils import cubeutils
    >>> cubeutils.add_decade_aux_coord(testcube, 'time')
    >>> print(testcube)
    air_temperature / (degC)            (time: 120; latitude: 19; longitude: 36)
         Dimension coordinates:
              time                           x             -             -
              latitude                       -             x             -
              longitude                      -             -             x
         Auxiliary coordinates:
              decade                         x             -             -

By default the ``add_decade_aux_coord()`` function creates an auxiliary coordinate
called ‘decade’ associated with the specified time dimension. If desired, the ``name``
keyword argument can be used to specify an alternative name.

The equivalent function for generating an auxiliary coordinate containing model
decades is ``cubeutils.add_model_decade_aux_coord()``, which has the following signature::

    add_model_decade_aux_coord(cube, time_coord, name='model_decade', ref_date=None)

The key difference with this particular function is that the start of each decadal
period is offset by multiples of 10 years from a given reference date, the default
for which is midnight on 1859-12-01. A custom reference date can be specified,
however, via the ``ref_date`` keyword argument. In the following code snippet a
model decade auxiliary coordinate is created based on a reference date of
March 1st, 1970 (i.e. the start of meteorological Spring). Notice, too, that we
pass in an Iris DimCoord object (instead of a text string) as the value of the
``time_coord`` argument::

    >>> from afterburner.utils import cubeutils
    >>> tcoord = testcube.coord('time')
    >>> cubeutils.add_model_decade_aux_coord(testcube, tcoord, ref_date='1970-03-01')
    >>> print(testcube)
    air_temperature / (degC)            (time: 120; latitude: 19; longitude: 36)
         Dimension coordinates:
              time                           x             -             -
              latitude                       -             x             -
              longitude                      -             -             x
         Auxiliary coordinates:
              model_decade                   x             -             -

From the previous two code examples we can see that the ``add_decade_aux_coord()``
function is essentially just a specialisation of the ``add_model_decade_aux_coord()``
function, with the ``name`` and ``ref_date`` arguments taking on custom values.

Finally, the general-purpose ``add_multi_year_aux_coord()`` function can be used
to add a multi-year categorical coordinate of user-defined length to a cube. The
function signature is as follows::

    add_multi_year_aux_coord(cube, time_coord, num_years, name='multi_year', ref_date=None, add_bounds=False)

Most of the arguments are as per the other two functions described above. The
``num_years`` argument specifies the length of the categorisation period in whole
years, while the ``add_bounds`` argument may be used to attach cell bounds to the
newly created auxiliary coordinate. The code snippet below illustrates creating
a fifty-year categorical coordinate based on a reference date of 1900-01-01::

    >>> from afterburner.utils import cubeutils
    >>> cubeutils.add_multi_year_aux_coord(testcube, 'time', 50, ref_date='1900-01-01')
    >>> print(testcube)
    air_temperature / (degC)            (time: 120; latitude: 19; longitude: 36)
         Dimension coordinates:
              time                           x             -             -
              latitude                       -             x             -
              longitude                      -             -             x
         Auxiliary coordinates:
              multi_year                     x             -             -

This tutorial has demonstrated a handful of the convenience functions provided
by Afterburner's ``cubeutils`` module. But there are many more: why not have a
browse through the :mod:`module documentation <afterburner.utils.cubeutils>`
:-)

Back to the :doc:`Tutorial Index <index>`
