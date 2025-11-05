Tutorial #2: Introduction to Time-based Statistical Functions
=============================================================

This tutorial provides a gentle introduction to the convenience functions in the
Afterburner package for calculating basic time-based statistics from Iris cubes;
for example the monthly-mean of a time-series dataset. A :doc:`separate tutorial </tutorials/spatial_stats>`
covers the analogous functions for generating spatial statistics such as global
area-weighted means.

.. tip:: Refer to :doc:`Tutorial #1 </tutorials/accessing_afterburner>` for information
   on how to configure your Python environment to access the afterburner Python
   package.

The time-based statistical functions live in a module named ``afterburner.stats.temporal``.
Here's how you can import the temporal module. We'll also import the ``iris`` package
while we're at it::

    >>> import iris
    >>> from afterburner.stats import temporal

.. note:: Most of the functions contained in the ``afterburner.stats.temporal``
   module act as lightweight wrappers around the functionality provided by the
   `iris.analysis <https://scitools.org.uk/iris/docs/latest/iris/iris/analysis.html>`_
   module. The main advantages of using the afterburner functions are that they
   are centrally maintained, tested and supported, and because they take care of
   creating and, if required, removing categorical coordinates as and when these
   are needed.

The ``temporal`` module includes a general-purpose function called ``calc_time_stat()``
which, as the name suggests, can be used to calculate any Iris-supported time
statistic from the specified cube (or cubes, if you pass in a cubelist). Assuming
that we have previously loaded a cube of global monthly-mean surface temperature
data for the 10-year period 2000-01-01 to 2010-01-01, here's how you could generate
a cube of annual-mean values::

    >>> print(cube)
    air_temperature / (degC)            (time: 120; latitude: 7; longitude: 6)
         Dimension coordinates:
              time                           x             -             -
              latitude                       -             x             -
              longitude                      -             -             x
         Cell methods:
              mean: time (1 hour)
    >>> ann_mean = temporal.calc_time_stat(cube, iris.analysis.MEAN, temporal.TP_YEAR)
    >>> print(ann_mean)
    air_temperature / (degC)            (time: 10; latitude: 7; longitude: 6)
         Dimension coordinates:
              time                           x             -             -
              latitude                       -             x             -
              longitude                      -             -             x
         Auxiliary coordinates:
              year                           x             -             -
         Cell methods:
              mean: time (1 hour)
              mean: year

Notice that the ``ann_mean`` cube contains a new auxiliary coordinate called year,
and that this coordinate is referenced by a new cell method representing the
annual meaning operation.

The function call shown above calculates what one might call the 'true' annual mean,
i.e. for the calendar year running from Jan 1 to Dec 31. To calculate the mean over
(climate) model years one would replace the third argument above -- the aggregation
period -- with the symbolic constant ``temporal.TP_MODEL_YEAR``, as shown below.
A couple of things to note: (i) the name of the auxiliary coordinate now reflects
the model year aggregation period; and (ii) the time dimension contains an additional
coordinate (11 rather than 10, presumably because the input data straddles model year
boundaries)::

    >>> ann_mean = temporal.calc_time_stat(cube, iris.analysis.MEAN, temporal.TP_MODEL_YEAR)
    >>> print(ann_mean)
    air_temperature / (degC)            (time: 11; latitude: 7; longitude: 6)
         Dimension coordinates:
              time                           x             -             -
              latitude                       -             x             -
              longitude                      -             -             x
         Auxiliary coordinates:
              model_year                     x             -             -
         Cell methods:
              mean: time (1 hour)
              mean: model_year

By default all of the functions in the temporal module search the input cube for
a time dimension named, unsurprisingly, 'time'. If the cube's time dimension has
some other name then this can be specified via the ``time_coord`` keyword argument.
In the seasonal mean example below, the time dimension is called 'modeltime'::

    >>> seas_mean = temporal.calc_seasonal_stat(cube, iris.analysis.MEAN, time_coord='modeltime')
    >>> print(seas_mean)
    air_temperature / (degC)           (modeltime: 41; latitude: 19; longitude: 18)
         Dimension coordinates:
              modeltime                      x             -              -
              latitude                       -             x              -
              longitude                      -             -              x
         Auxiliary coordinates:
              season                         x             -              -
              season_year                    x             -              -
         Cell methods:
              mean: modeltime (1 hour)
              mean: season, season_year

As mentioned earlier, ``calc_time_stat()`` is a general-purpose wrapper function.
However, the ``temporal`` module also contains convenience functions for specific,
commonly-used time periods (e.g. months, seasons and decades). In the case of the
examples above we could have used the ``calc_annual_stat()`` and ``calc_model_annual_stat()``
functions. The code snippet below shows the use of these functions to calculate
the standard deviation and variance measures for a cube::

    >>> # calculate standard deviation over calendar years
    >>> ann_std = temporal.calc_annual_stat(cube, iris.analysis.STD_DEV)
    >>> # calculate variance over model years
    >>> ann_var = temporal.calc_model_annual_stat(cube, iris.analysis.VARIANCE)

Thus far we have passed a single cube to each statistical function, and received
a single cube in return. The ``calc_time_stat()`` function will, however, accept a
cubelist and return a corresponding cubelist containing cubes of statistical
measures. This capability is currently limited to the ``calc_time_stat`` function;
the low-level, period-specific functions only work with single cubes.

Alternatively, it's possible to have the new cubes of statistics *appended* to the
input cubelist. This is achieved by setting the ``append_to_cubelist`` keyword
argument. The code fragment below shows these extra usage patterns::

    >>> print(cubelist)
    0: air_temperature / (degC)            (time: 120; latitude: 19; longitude: 18)
    1: precipitation_flux / (kg m-2 s-1)   (time: 120; latitude: 19; longitude: 18)
    >>> result = temporal.calc_time_stat(cubelist, iris.analysis.MEAN, temporal.TP_YEAR)
    >>> print(result)
    0: air_temperature / (degC)            (time: 10; latitude: 19; longitude: 18)
    1: precipitation_flux / (kg m-2 s-1)   (time: 10; latitude: 19; longitude: 18)
    >>> result = temporal.calc_time_stat(cubelist, iris.analysis.MEAN, temporal.TP_YEAR,
    ...                                  append_to_cubelist=True)
    >>> print(result)
    0: air_temperature / (degC)            (time: 120; latitude: 19; longitude: 18)
    1: precipitation_flux / (kg m-2 s-1)   (time: 120; latitude: 19; longitude: 18)
    2: air_temperature / (degC)            (time: 10; latitude: 19; longitude: 18)
    3: precipitation_flux / (kg m-2 s-1)   (time: 10; latitude: 19; longitude: 18)
    >>> result is cubelist   # returned result is just a pointer to the cubelist object
    True

We conclude this tutorial with a brief mention of *categorical coordinates*. These
are the auxiliary coordinates that get added to the input cube(s) in order to
calculate the desired statistical measure. In the code snippets above they are the
coordinates such as year, model_year, season, month_number, etc. What this means
is that the input cube(s) are modified, transparently, as a side effect of calculating
and returning a statistical cube. Often this is harmless, but not always.

If you wish the input cube(s) to be restored to their original form, then the
``drop_new_coords`` keyword argument, when set to True, causes any *new* auxiliary
coordinates to be dropped from the input cube(s) before the function returns. If
an input cube already has one or much such auxiliary coordinates then these are
utilised as-is and retained on the cube::

    >>> cube = iris.load_cube(...)
    >>> print([crd.name() for crd in cube.coords()])                                                                                                
    ['time', 'latitude', 'longitude']

    # without the drop_new_coords argument, the input cube retains the new 'year' coord
    >>> ann_mean = temporal.calc_time_stat(cube, iris.analysis.MEAN, temporal.TP_YEAR)
    >>> print([crd.name() for crd in cube.coords()])                                                                                                
    ['time', 'latitude', 'longitude', 'year']

    # with the drop_new_coords argument, the 'year' coord is dropped from the input cube
    >>> cube = iris.load_cube(...) # reloads the input cube
    >>> ann_mean = temporal.calc_time_stat(cube, iris.analysis.MEAN, temporal.TP_YEAR,
    ...                                    drop_new_coords=True)
    >>> print([crd.name() for crd in cube.coords()])                                                                                                
    ['time', 'latitude', 'longitude']

That's all for this tutorial. You can find a full description of the functions
provided by the ``temporal`` module in the :mod:`API reference documentation <afterburner.stats.temporal>`.

Back to the :doc:`Tutorial Index <index>`
