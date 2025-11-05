# (C) British Crown Copyright 2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The afterburner.stats.temporal module contains a selection of utility functions
for calculating temporal statistics from Iris cubes for a variety of aggregation
periods. Most of the functions are thin wrappers around the data aggregation
functionality provided by the Iris package (as documented
`here <https://scitools.org.uk/iris/docs/latest/iris/iris/analysis.html>`_)

The :func:`calc_time_stat` function provides a general-purpose convenience wrapper
around the various low-level, time period specific calculation functions. For
example, the following call generates a cube of monthly-mean values from a single
input cube:

>>> result_cube = calc_time_stat(cube, iris.analysis.MEAN, TP_MONTH)

This function also accepts an Iris cubelist as the first argument, by default
returning a new cubelist of corresponding statistics cubes.

The equivalent low-level call to that shown above would be:

>>> result_cube = calc_monthly_stat(cube, iris.analysis.MEAN)

Calculating some other statistical measure - the variance, say - is achieved
simply by passing the appropriate iris.Aggregator instance object:
``iris.analysis.VARIANCE`` in this case.

>>> result_cube = calc_seasonal_stat(cube, iris.analysis.VARIANCE)

If there is a requirement to pass one or more keyword arguments through to the
iris.Aggregator object, this can be achieved via the ``agg_opts`` argument, which
is accepted by all of the statistical functions. So, for example, calculating
the standard deviation with a custom 'delta degrees of freedom' option could be
achieved as follows:

>>> result_cube = calc_annual_stat(cube, iris.analysis.STD_DEV, agg_opts={'ddof': 0})

Note that a default side effect of all of the statistical functions provided here
is to attach one or more auxiliary 'categorical' coordinates ('month', 'season',
'year', etc) to the input cube or cubes. This behaviour can be undone by setting
the ``drop_new_coords`` keyword argument to True.

.. warning:: Care should be exercised if one wishes to calculate multiple
   statistics from a given cube using different values of the same categorical
   coordinate (e.g. meteorological seasons vs calendar year seasons). If the
   coordinate already exists - as it typically will after the first calculation
   - then it will not be regenerated, meaning that incorrect values may be used
   for subsequent calculations. The aforementioned ``drop_new_coords`` keyword
   argument can be useful in this situation.

**Index of Functions in this Module**

.. autosummary::
   :nosignatures:

   calc_time_stat
   calc_monthly_stat
   calc_seasonal_stat
   calc_annual_stat
   calc_model_annual_stat
   calc_decadal_stat
   calc_model_decadal_stat
   calc_monthly_clim
   calc_seasonal_clim
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import logging

import iris
import iris.coords
import iris.coord_categorisation as coord_cat

from afterburner.utils import cubeutils


#: Symbolic constant indicating a month period.
TP_MONTH = 'month'
#: Symbolic constant indicating a season period.
TP_SEASON = 'season'
#: Symbolic constant indicating a model season period.
TP_MODEL_SEASON = 'model_season'
#: Symbolic constant indicating a year period.
TP_YEAR = 'year'
#: Symbolic constant indicating a model year period.
TP_MODEL_YEAR = 'model_year'
#: Symbolic constant indicating a decade period.
TP_DECADE = 'decade'
#: Symbolic constant indicating a model decade period.
TP_MODEL_DECADE = 'model_decade'
#: Symbolic constant indicating an arbitrary multi-year period.
TP_MULTI_YEAR = 'multi_year'


# Dictionary which maps time periods to corresponding functions.
_TP_FUNCTION_MAP = {
    TP_MONTH: 'calc_monthly_stat',
    TP_SEASON: 'calc_seasonal_stat',
    TP_MODEL_SEASON: 'calc_seasonal_stat',
    TP_YEAR: 'calc_annual_stat',
    TP_MODEL_YEAR: 'calc_model_annual_stat',
    TP_DECADE: 'calc_decadal_stat',
    TP_MODEL_DECADE: 'calc_model_decadal_stat',
}

# Obtain a logger object.
_logger = logging.getLogger(__name__)


def calc_time_stat(cubes, aggregator, agg_period, agg_opts=None, time_coord='time',
        **kwargs):
    """
    Calculate an aggregated-by-time statistic for each cube passed in via the
    list of ``cubes``. The particular statistic to generate is determined by the
    ``aggregator`` object: an instance of iris.analysis.Aggregator. The time
    period over which to perform the aggregation is controlled by the ``agg_period``
    argument; currently supported time periods include month, season, model season,
    year, model year, decade, and model decade.

    :param iris.cube.CubeList cubes: A single Iris cube, or a list of cubes, for
        which to generate the requested time-aggregated statistic.
    :param iris.analysis.Aggregator aggregator: An instance of an Iris aggregator
        object, for example iris.analysis.MEAN.
    :param string agg_period: The time period over which to perform the
        aggregation. Currently supported time periods are those represented by
        the symbolic constants starting with a `TP_` prefix at the top of this
        module.
    :param dict agg_opts: An optional dictionary of keywords arguments to pass
        through to the aggregator object. Supported arguments are as described
        in the documentation for the iris.analysis module.
    :param str time_coord: The name of the time coordinate over which to perform
        the aggregation operation.

    Extra Keyword Arguments (`**kwargs`):

    :param bool append_to_cubelist: If set to true then, in the case where ``cubes``
        is a cubelist, the result cubes are appended to that cubelist. The default
        behaviour is to return a new cubelist. This option is ignored if ``cubes``
        is a single cube.
    :param bool drop_new_coords: If set to true then any auxiliary coordinates
        (such as 'season') which get added to the input cube(s) are dropped
        before the function returns. The default behaviour is to retain any such
        coordinates.
    :param bool stop_on_error: If set to true then, in the case where ``cubes``
        is a cubelist, an exception will be raised if an error is encountered.
        The default behaviour is to log an error message and continue.

    :returns: A cube or cubelist containing the requested statistic calculated
        for each input cube.
    """

    stop_on_error = kwargs.pop('stop_on_error', False)
    append_to_cubelist = kwargs.pop('append_to_cubelist', False)
    input_is_cube = False

    func_name = _TP_FUNCTION_MAP.get(agg_period)
    if not func_name:
        raise ValueError("Unsupported aggregation period: " + agg_period)
    else:
        stat_func = globals()[func_name]

    if isinstance(cubes, iris.cube.Cube):
        cubes = iris.cube.CubeList([cubes])
        input_is_cube = True
    elif not isinstance(cubes, iris.cube.CubeList):
        raise TypeError("The 'cubes' argument must be an Iris cube or cubelist.")

    stat_cubes = iris.cube.CubeList()

    for cube in cubes:
        try:
            stat_cube = stat_func(cube, aggregator, agg_opts=agg_opts,
                time_coord=time_coord, **kwargs)
            stat_cubes.append(stat_cube)
        except Exception as exc:
            msg = ("Error calculating '{0}' statistic for the following cube:"
                "\n{1}".format(aggregator.name(), cube.summary(shorten=True)))
            _logger.error(msg)
            _logger.error(str(exc))
            if stop_on_error or input_is_cube: raise

    if input_is_cube:
        return stat_cubes[0]
    elif append_to_cubelist:
        cubes.extend(stat_cubes)
        return cubes
    else:
        return stat_cubes


def calc_monthly_stat(cube, aggregator, agg_opts=None, time_coord='time',
        drop_new_coords=False):
    """
    Calculate a monthly statistic from the data payload associated with the
    specified cube.

    A side effect of calling this function is that, unless ``drop_new_coords``
    is set to true, the input cube is modified to include auxiliary coordinates
    named 'month_number' and 'year'.

    :param iris.cube.Cube cube: The Iris cube from which to generate the monthly
        statistic.
    :param iris.analysis.Aggregator aggregator: An instance of an Iris aggregator
        object, for example iris.analysis.MEAN.
    :param dict agg_opts: An optional dictionary of keywords arguments to pass
        through to the aggregator object. Supported arguments are as described
        in the documentation for the iris.analysis module.
    :param str time_coord: The name of the time coordinate over which to perform
        the aggregation operation.
    :param bool drop_new_coords: If set to true then any auxiliary coordinates
        (such as 'month_number') which get added to the input cube are dropped
        before the function returns. The default behaviour is to retain any such
        coordinates.
    :returns: A cube containing the requested statistic calculated from the input
        cube.
    """

    new_coords = []

    # add a month_number coordinate
    if 'month_number' not in [c.name() for c in cube.coords()]:
        coord_cat.add_month_number(cube, time_coord, name='month_number')
        new_coords.append('month_number')

    # add a year coordinate
    if 'year' not in [c.name() for c in cube.coords()]:
        coord_cat.add_year(cube, time_coord, name='year')
        new_coords.append('year')

    if not agg_opts: agg_opts = {}
    result = cube.aggregated_by(['month_number', 'year'], aggregator, **agg_opts)

    if drop_new_coords:
        for coord in new_coords:
            cube.remove_coord(coord)

    return result


def calc_seasonal_stat(cube, aggregator, agg_opts=None, time_coord='time',
        seasons=None, drop_new_coords=False):
    """
    Calculate a seasonal statistic from the data payload associated with the
    specified cube. By default the standard meteorological seasons are used, i.e.
    the 3-month periods ('djf', 'mam', 'jja', 'son'). Alternative seasons may
    be specified via the ``seasons`` argument.

    A side effect of calling this function is that, unless ``drop_new_coords``
    is set to true, the input cube is modified to include auxiliary coordinates
    named 'season' and 'season_year'

    :param iris.cube.Cube cube: The Iris cube from which to generate the seasonal
        statistic.
    :param iris.analysis.Aggregator aggregator: An instance of an Iris aggregator
        object, for example iris.analysis.MEAN.
    :param dict agg_opts: An optional dictionary of keywords arguments to pass
        through to the aggregator object. Supported arguments are as described
        in the documentation for the iris.analysis module.
    :param str time_coord: The name of the time coordinate over which to perform
        the aggregation operation.
    :param tuple seasons: A tuple of strings defining the months comprising the
        seasons. If undefined then the standard meteorological seasons are used
        i.e. ('djf', 'mam', 'jja', 'son').
    :param bool drop_new_coords: If set to true then any auxiliary coordinates
        (such as 'season') which get added to the input cube are dropped before
        the function returns. The default behaviour is to retain any such
        coordinates.
    :returns: A cube containing the requested statistic calculated from the input
        cube.
    """

    new_coords = []

    if not seasons:
        seasons = ('djf', 'mam', 'jja', 'son')

    # add a season coordinate
    if 'season' not in [c.name() for c in cube.coords()]:
        coord_cat.add_season(cube, time_coord, name='season', seasons=seasons)
        new_coords.append('season')

    # add a season-year coordinate
    if 'season_year' not in [c.name() for c in cube.coords()]:
        coord_cat.add_season_year(cube, time_coord, name='season_year', seasons=seasons)
        new_coords.append('season_year')

    if not agg_opts: agg_opts = {}
    result = cube.aggregated_by(['season', 'season_year'], aggregator, **agg_opts)

    if drop_new_coords:
        for coord in new_coords:
            cube.remove_coord(coord)

    return result


def calc_annual_stat(cube, aggregator, agg_opts=None, time_coord='time',
        drop_new_coords=False):
    """
    Calculate an annual statistic from the data payload associated with the
    specified cube. In this case 'annual' refers to the standard calendar year,
    i.e. midnight Jan 1 to midnight Jan 1, rather than a climate model year. See
    the :func:`calc_model_annual_stat` function for a way to calculate statistics
    over climate model years.

    A side effect of calling this function is that, unless ``drop_new_coords``
    is set to true, the input cube is modified to include an auxiliary coordinate
    named 'year'

    :param iris.cube.Cube cube: The Iris cube from which to generate the annual
        statistic.
    :param iris.analysis.Aggregator aggregator: An instance of an Iris aggregator
        object, for example iris.analysis.MEAN.
    :param dict agg_opts: An optional dictionary of keywords arguments to pass
        through to the aggregator object. Supported arguments are as described
        in the documentation for the iris.analysis module.
    :param str time_coord: The name of the time coordinate over which to perform
        the aggregation operation.
    :param bool drop_new_coords: If set to true then any auxiliary coordinates
        (such as 'year') which get added to the input cube are dropped before
        the function returns. The default behaviour is to retain any such
        coordinates.
    :returns: A cube containing the requested statistic calculated from the input
        cube.
    """

    new_coords = []

    # add a year coordinate
    if 'year' not in [c.name() for c in cube.coords()]:
        coord_cat.add_year(cube, time_coord, name='year')
        new_coords.append('year')

    if not agg_opts: agg_opts = {}
    result = cube.aggregated_by('year', aggregator, **agg_opts)

    if drop_new_coords:
        for coord in new_coords:
            cube.remove_coord(coord)

    return result


def calc_model_annual_stat(cube, aggregator, agg_opts=None, time_coord='time',
        drop_new_coords=False):
    """
    Calculate a model year statistic from the data payload associated with the
    specified cube. In this case 'annual' refers to the climate model year,
    i.e. midnight Dec 1 to midnight Dec 1, rather than the standard calendar year.
    See the :func:`calc_annual_stat` function for a way to calculate statistics
    over calendar years.

    A side effect of calling this function is that, unless ``drop_new_coords``
    is set to true, the input cube is modified to include an auxiliary coordinate
    named 'model_year'

    :param iris.cube.Cube cube: The Iris cube from which to generate the model
        year statistic.
    :param iris.analysis.Aggregator aggregator: An instance of an Iris aggregator
        object, for example iris.analysis.MEAN.
    :param dict agg_opts: An optional dictionary of keywords arguments to pass
        through to the aggregator object. Supported arguments are as described
        in the documentation for the iris.analysis module.
    :param str time_coord: The name of the time coordinate over which to perform
        the aggregation operation.
    :param bool drop_new_coords: If set to true then any auxiliary coordinates
        (such as 'model_year') which get added to the input cube are dropped
        before the function returns. The default behaviour is to retain any such
        coordinates.
    :returns: A cube containing the requested statistic calculated from the input
        cube.
    """

    new_coords = []

    # add a season-year coordinate
    if 'model_year' not in [c.name() for c in cube.coords()]:
        coord_cat.add_season_year(cube, time_coord, name='model_year')
        new_coords.append('model_year')

    if not agg_opts: agg_opts = {}
    result = cube.aggregated_by('model_year', aggregator, **agg_opts)

    if drop_new_coords:
        for coord in new_coords:
            cube.remove_coord(coord)

    return result


def calc_decadal_stat(cube, aggregator, agg_opts=None, time_coord='time',
        drop_new_coords=False):
    """
    Calculate a decadal statistic from the data payload associated with the
    specified cube. In this case 'decadal' means the familiar 10-year periods
    commencing at midnight Jan 1 on years that are whole multiples of 10. See
    the :func:`calc_model_decadal_stat` function for a way to calculate statistics
    over climate model decades.

    A side effect of calling this function is that, unless ``drop_new_coords``
    is set to true, the input cube is modified to include an auxiliary coordinate
    named 'decade'

    :param iris.cube.Cube cube: The Iris cube from which to generate the decadal
        statistic.
    :param iris.analysis.Aggregator aggregator: An instance of an Iris aggregator
        object, for example iris.analysis.MEAN.
    :param dict agg_opts: An optional dictionary of keywords arguments to pass
        through to the aggregator object. Supported arguments are as described
        in the documentation for the iris.analysis module.
    :param str time_coord: The name of the time coordinate over which to perform
        the aggregation operation.
    :param bool drop_new_coords: If set to true then any auxiliary coordinates
        (such as 'decade') which get added to the input cube are dropped before
        the function returns. The default behaviour is to retain any such
        coordinates.
    :returns: A cube containing the requested statistic calculated from the input
        cube.
    """

    new_coords = []

    # add a decade coordinate
    if 'decade' not in [c.name() for c in cube.coords()]:
        cubeutils.add_decade_aux_coord(cube, time_coord)
        new_coords.append('decade')

    if not agg_opts: agg_opts = {}
    result = cube.aggregated_by('decade', aggregator, **agg_opts)

    if drop_new_coords:
        for coord in new_coords:
            cube.remove_coord(coord)

    return result


def calc_model_decadal_stat(cube, aggregator, agg_opts=None, time_coord='time',
        drop_new_coords=False, ref_date=None):
    """
    Calculate a model decade statistic from the data payload associated with the
    specified cube. In this case 'model decade' means the 10-year periods
    commencing at midnight on the specified reference day (default: Dec 1), for
    those years that are whole multiples of 10 offset from the reference year
    (default: 1859). See the :func:`calc_decadal_stat` function for a way to
    calculate statistics over normal calendar decades.

    A side effect of calling this function is that, unless ``drop_new_coords``
    is set to true, the input cube is modified to include an auxiliary coordinate
    named 'decade'

    :param iris.cube.Cube cube: The Iris cube from which to generate the decadal
        statistic.
    :param iris.analysis.Aggregator aggregator: An instance of an Iris aggregator
        object, for example iris.analysis.MEAN.
    :param dict agg_opts: An optional dictionary of keywords arguments to pass
        through to the aggregator object. Supported arguments are as described
        in the documentation for the iris.analysis module.
    :param str time_coord: The name of the time coordinate over which to perform
        the aggregation operation.
    :param bool drop_new_coords: If set to true then any auxiliary coordinates
        (such as 'decade') which get added to the input cube are dropped before
        the function returns. The default behaviour is to retain any such
        coordinates.
    :param datetime ref_date: The reference date (as a datetime-like object)
        used to determine the start (ergo end) dates of consecutive time periods.
        If undefined then a default reference date of 1859-12-01 is used.
    :returns: A cube containing the requested statistic calculated from the input
        cube.
    """

    new_coords = []

    # add a model decade coordinate
    if 'model_decade' not in [c.name() for c in cube.coords()]:
        cubeutils.add_model_decade_aux_coord(cube, time_coord, ref_date=ref_date)
        new_coords.append('model_decade')

    if not agg_opts: agg_opts = {}
    result = cube.aggregated_by('model_decade', aggregator, **agg_opts)

    if drop_new_coords:
        for coord in new_coords:
            cube.remove_coord(coord)

    return result


def calc_monthly_clim(cube, aggregator, agg_opts=None, time_coord='time',
        drop_new_coords=False):
    """
    Calculate a multi-year monthly climatology from the data payload associated
    with the specified cube.

    A side effect of calling this function is that, unless ``drop_new_coords``
    is set to true, the input cube is modified to include an auxiliary coordinate
    named 'month_number'.

    :param iris.cube.Cube cube: The Iris cube from which to generate the monthly
        climatology.
    :param iris.analysis.Aggregator aggregator: An instance of an Iris aggregator
        object, for example iris.analysis.MEAN.
    :param dict agg_opts: An optional dictionary of keywords arguments to pass
        through to the aggregator object. Supported arguments are as described
        in the documentation for the iris.analysis module.
    :param str time_coord: The name of the time coordinate over which to perform
        the aggregation operation.
    :param bool drop_new_coords: If set to true then any auxiliary coordinates
        (such as 'month_number') which get added to the input cube are dropped
        before the function returns. The default behaviour is to retain any such
        coordinates.
    :returns: A cube containing the requested climatology calculated from the input
        cube.
    """

    new_coords = []

    # add a month_number coordinate
    if 'month_number' not in [c.name() for c in cube.coords()]:
        coord_cat.add_month_number(cube, time_coord, name='month_number')
        new_coords.append('month_number')

    if not agg_opts: agg_opts = {}
    result = cube.aggregated_by(['month_number'], aggregator, **agg_opts)

    if drop_new_coords:
        for coord in new_coords:
            cube.remove_coord(coord)

    return result


def calc_seasonal_clim(cube, aggregator, agg_opts=None, time_coord='time',
        seasons=None, drop_new_coords=False):
    """
    Calculate a multi-year seasonal climatology from the data payload associated
    with the specified cube. By default the standard meteorological seasons are
    used, i.e. the 3-month periods ('djf', 'mam', 'jja', 'son'). Alternative
    seasons may be specified via the ``seasons`` argument.

    A side effect of calling this function is that, unless ``drop_new_coords``
    is set to true, the input cube is modified to include an auxiliary coordinate
    named 'season'.

    :param iris.cube.Cube cube: The Iris cube from which to generate the seasonal
        climatology.
    :param iris.analysis.Aggregator aggregator: An instance of an Iris aggregator
        object, for example iris.analysis.MEAN.
    :param dict agg_opts: An optional dictionary of keywords arguments to pass
        through to the aggregator object. Supported arguments are as described
        in the documentation for the iris.analysis module.
    :param str time_coord: The name of the time coordinate over which to perform
        the aggregation operation.
    :param tuple seasons: A tuple of strings defining the months comprising the
        seasons. If undefined then the standard meteorological seasons are used
        i.e. ('djf', 'mam', 'jja', 'son').
    :param bool drop_new_coords: If set to true then any auxiliary coordinates
        (such as 'season') which get added to the input cube are dropped before
        the function returns. The default behaviour is to retain any such
        coordinates.
    :returns: A cube containing the requested climatology calculated from the input
        cube.
    """

    new_coords = []

    if not seasons:
        seasons = ('djf', 'mam', 'jja', 'son')

    # add a season coordinate
    if 'season' not in [c.name() for c in cube.coords()]:
        coord_cat.add_season(cube, time_coord, name='season', seasons=seasons)
        new_coords.append('season')

    if not agg_opts: agg_opts = {}
    result = cube.aggregated_by(['season'], aggregator, **agg_opts)

    if drop_new_coords:
        for coord in new_coords:
            cube.remove_coord(coord)

    return result
