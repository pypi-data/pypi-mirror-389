Tutorial #10: Introduction to Climatology Functions
===================================================

This tutorial introduces the convenience functions implemented in the Afterburner
package for calculating climatological statistics from Iris cubes; for example the
multi-year average of daily-mean temperature data for each month or season of the year.
In the met-ocean community such multi-year statistics are usually referred to more
succinctly as 'climatologies', so that's the term we'll use here.

The climatology functions live in a module named ``afterburner.stats.temporal`` (which we also
encountered in :doc:`Tutorial #2 </tutorials/temporal_stats>`). Here's how you can
import the ``temporal`` module. We'll also import the ``iris.analysis`` module while we're at it:

>>> import iris.analysis
>>> from afterburner.stats import temporal

The sample code snippets included in this tutorial assume that these two modules
have been imported as shown above.

.. tip:: Refer to :doc:`Tutorial #1 </tutorials/accessing_afterburner>` for information
   on how to configure your Python environment to access the afterburner Python
   package.

Currently the ``temporal`` module contains just two climatology functions: one for calculating
month-based climatologies (``calc_monthly_clim``), the other for calculating
season-based climatologies (``calc_seasonal_clim``). Both functions act as convenience
wrappers around the underlying data aggregation capabilities provided by the Iris package.
They represent two of the more commonly encountered climatological measures, though other
measures are employed of course.

Both functions employ the same analytical approach, which goes like this:

1. Unless it's already present, create a categorical coordinate (e.g. month number or season name)
   on the input cube using Iris's ``coord_categorisation`` functions.
2. Calculate the desired statistical measure (mean, variance, etc) by invoking the ``cube.aggregated_by()``
   method with (i) the coordinate created at step 1, and (ii) the name of an Iris aggregator object.
3. If required, remove the categorical coordinate that was added to the *input cube*. By default
   any such coordinate is retained.

With that in mind let's see the climatology functions in action.

Producing Multi-Year Month-based Climatologies
----------------------------------------------

By way of example, if we wish to calculate the average of the daily-maximum surface
temperature values for each month of the year for a 30-year long time series, here's
how we could do that. Firstly, here's what our imaginary input cube looks like:

>>> print(cube)
air_temperature / (degC)            (time: 10800; latitude: 19; longitude: 36)
     Dimension coordinates:
          time                           x                -              -
          latitude                       -                x              -
          longitude                      -                -              x
     Cell methods:
          maximum: time

Now we compute the monthly-mean climatology from the daily-maximum input values:

>>> mon_mean_clim = temporal.calc_monthly_clim(cube, iris.analysis.MEAN)
>>> print(mon_mean_clim)
air_temperature / (degC)            (time: 12; latitude: 19; longitude: 36)
     Dimension coordinates:
          time                           x             -             -
          latitude                       -             x             -
          longitude                      -             -             x
     Auxiliary coordinates:
          month_number                   x             -             -
     Cell methods:
          maximum: time
          mean: month_number

Notice that the time dimension has been collapsed down to 12 coordinates, one for each month of the
calendar year. If we were to print out the result cube's time dimension object we'd see that the cell
bounds encompass the full 30-year period covered by the input cube. The time coordinate values will
usually fall around the mid-point of the month, e.g. the 15th or the 16th, though the precise value is
largely immaterial for multi-year climatologies. This is in accordance with the recommended definition
of climatological variables as prescribed by the Climate and Forecast (CF) metadata conventions.

Producing Multi-Year Season-based Climatologies
-----------------------------------------------

Producing long-term seasonal averages for key meteorological variables is a frequently-used analytical
technique. So let's extend our earlier month-based analysis to seasons assuming we have an input cube
of daily-mean surface temperature values covering a 30-year period.

To obtain the long-term average temperature for each of the standard meteorological seasons -- these
being DJF, MAM, JJA, SON -- we could run the following code:

>>> print(cube)
air_temperature / (degC)            (time: 10800; latitude: 19; longitude: 36)
     Dimension coordinates:
          time                           x                -              -
          latitude                       -                x              -
          longitude                      -                -              x
     Cell methods:
          mean: time
>>> seasonal_clim = temporal.calc_seasonal_clim(cube, iris.analysis.MEAN)
>>> print(seasonal_clim)
air_temperature / (degC)              (--: 4; latitude: 19; longitude: 36)
     Dimension coordinates:
          latitude                       -             x             -
          longitude                      -             -             x
     Auxiliary coordinates:
          season                         x             -             -
          time                           x             -             -
     Cell methods:
          mean: time
          mean: season

Note, in this case, that the time dimension has been collapsed down to just 4 coordinates, one for
each of the seasons, just as we'd expect.

To obtain a climatology for custom seasons it's necessary to specify the ``seasons`` argument, which
should be a tuple of strings comprising month letters. For example, to calculate the seasonal *maximum*
temperature based on simple calendar-year seasons, the function call would appear thus:

>>> seasonal_clim = temporal.calc_seasonal_clim(cube, iris.analysis.MAX,
...     seasons=('JFM', 'AMJ', 'JAS', 'OND'))

Note that the seasons do not have to be defined in 3-month chunks; they could be 2 or 4 months in
length, or some combination of lengths (though this would certainly be unusual!).

Handling Auxiliary Categorical Coordinates
------------------------------------------

A side effect of calls to the climatology functions is that the required categorical coordinate
(e.g. month_number or season) must be added to the *input cube* in order to generate the desired
statistical measure. Naturally enough, the categorical coordinate is also copied over to the resulting
output cube.

If it's desired to have the input cube restored to its original state then the ``drop_new_coords``
keyword argument can be used to achieve that goal. It should be noted, however, that if the categorical
coordinate happens to be present already on the input cube then it won't be removed -- the aforementioned
argument will only affect *newly added* coordinates.

By way of example, here are the dimensions of our original input cube:

>>> print([crd.name() for crd in cube.coords()])
['time', 'latitude', 'longitude']

By default the categorical coordinate -- month_number in this instance -- gets added to the input cube
following a call to one of the climatology functions:

>>> result = temporal.calc_monthly_clim(cube, iris.analysis.MEAN)
>>> print([crd.name() for crd in cube.coords()])
['time', 'latitude', 'longitude', 'month_number']

But when the ``drop_new_coords`` argument is enabled the categorical coordinate gets removed immediately
prior to the function returning the result:

>>> result = temporal.calc_monthly_clim(cube, iris.analysis.MEAN, drop_new_coords=True)
>>> print([crd.name() for crd in cube.coords()])
['time', 'latitude', 'longitude']

Passing Optional Arguments To Iris Aggregator Objects
-----------------------------------------------------

As we've seen in the examples above, the second argument to the climatology functions is the name of
an Iris aggregator object (MEAN, SUM, VARIANCE, etc). Some of these aggregators accept optional
arguments that control how the aggregator operates. These options are described in the documentation
for the `iris.analysis <https://scitools.org.uk/iris/docs/latest/iris/iris/analysis.html>`_ module.

You can pass any such options by making use of the ``agg_opts`` dictionary argument supported by the
climatology functions. For example, the ``iris.analysis.MEAN`` aggregator recognises optional keyword
arguments named ``mdtol`` and ``weights``. These can be used to define, respectively, a missing data
tolerance (as a fraction), and a weights array. The code snippet below illustrates how to specify
these two options in a call to ``calc_monthly_clim()``:

>>> wts = calc_weights(cube)   # some function for calculating weights
>>> opts = {'mdtol': 0.5, 'weights': wts}
>>> result = temporal.calc_monthly_clim(cube, iris.analysis.MEAN, agg_opts=opts)

Or, using a terser coding style...

>>> result = temporal.calc_monthly_clim(cube, iris.analysis.MEAN,
...     agg_opts={'mdtol': 0.5, 'weights': calc_weights(cube)})

Wrap Up
-------

That concludes this brief tutorial. You can view a full description of all the statistical functions
contained in the ``temporal`` module by visiting the :mod:`API reference documentation <afterburner.stats.temporal>`.

Back to the :doc:`Tutorial Index <index>`
