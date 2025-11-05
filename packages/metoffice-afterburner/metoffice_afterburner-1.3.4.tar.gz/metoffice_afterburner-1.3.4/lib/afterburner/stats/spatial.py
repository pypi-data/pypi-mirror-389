# (C) British Crown Copyright 2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The afterburner.stats.spatial module contains a selection of utility functions
for calculating spatial statistics from Iris cubes for a variety of geospatial
domains. Most of the functions are thin wrappers around the data aggregation
and cube-collapsing functionality provided by the Iris package (as documented
`here <https://scitools.org.uk/iris/docs/latest/iris/iris/analysis.html>`_)

The :func:`calc_spatial_stat` function is a general-purpose convenience function
which can be used to calculate any Iris-supported statistical measure for a
single cube or a list of cubes.

For example, the following call could be used to calculate the area-weighted
mean for a single input cube:

>>> result_cube = calc_spatial_stat(cube, iris.analysis.MEAN, area_weighted=True)

The equivalent call for a list of input cubes is as follows:

>>> result_cubes = calc_spatial_stat(cubes, iris.analysis.MEAN, area_weighted=True)

The above calls calculate the mean by collapsing the latitude and longitude
dimensions. The ``coords`` keyword can be used to specify different coordinate
dimensions. For instance, the following call calculates the sum of the input cube
by aggregating over the grid latitude and longitude coordinates:

>>> result_cube = calc_spatial_stat(cube, iris.analysis.SUM,
...                   coords=['grid_latitude', 'grid_longitude'])

If it's required to calculate the statistic over a subset of each cube's grid
cells (just land cells, for example) then this can be achieved by specifying a
suitable mask array via the ``mask`` argument:

>>> result_cube = calc_spatial_stat(cube, iris.analysis.MEAN, mask=ocean_mask)

In this case the mean will be calculated using only those grid cells which are
*not* masked out by the mask array. Or, to put it another way, array elements
that are masked out in the mask array will be masked out in the cube's data array.

(Alternatively, of course, the calling program could extract a spatial subset of
the original cube(s) and pass the resulting cube(s) to the ``calc_spatial_stat``
function.)

If the mask array contains fractional area values then the ``mask_is_area_frac``
argument may be used to request that these are used to multiply through each
input cube before calculating the statistical measure, as illustrated below:

>>> result_cube = calc_spatial_stat(cube, iris.analysis.MEAN, mask=land_area_frac,
...                   mask_is_area_frac=True)
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import logging
import numpy as np
import numpy.ma as ma

import iris
import iris.coords

from afterburner.utils.cubeutils import calc_area_weights

# Obtain a logger object.
_logger = logging.getLogger(__name__)


def calc_spatial_stat(cubes, aggregator, agg_opts=None, coords=None, mask=None,
        mask_is_area_frac=False, area_weighted=False,  **kwargs):
    """
    Calculate a statistical measure for one or more cubes by aggregating data values
    over one or more spatial dimensions. The particular statistic to calculate is
    determined by the ``aggregator`` object: an instance of iris.analysis.Aggregator.

    If not specified by the calling program, the aggregation operation is applied
    over the coordinate dimensions identified as 'latitude' and 'longitude',
    which are assumed to be present on each input cube.

    The statistical measure is calculated by calling Iris' ``cube.collapsed()``
    method on each input cube. In each case the spatial coordinates over which
    the aggregation operation is applied are collapsed down to scalar coordinates
    in the result cube.

    The aggregation operation is applied over the full extent of the nominated
    spatial dimensions, e.g. over the entire globe for a global dataset. If it
    is required to perform the operation over a portion of the domain, e.g. a
    region of the globe, then the input cubes must first be cropped accordingly.
    The ``cube.intersection()`` method may be useful in this situation.

    :param iris.cube.CubeList cubes: A single Iris cube, or a list of cubes, for
        which to generate the requested spatial statistic.
    :param iris.analysis.Aggregator aggregator: An instance of an Iris aggregator
        object, for example ``iris.analysis.MEAN``.
    :param dict agg_opts: An optional dictionary of keyword arguments to pass
        through to the aggregator object. Supported arguments are as described
        in the documentation for the iris.analysis module.
    :param list coords: A list of coordinate names or objects over which the
        spatial statistic is to be calculated. If undefined then a default value
        of ['latitude', 'longitude'] is used.
    :param np.MaskedArray mask: An optional masked array to apply to each input
        cube. The shape of the masked array must be broadcastable to the shape
        of the input cube(s). By default the mask is used simply to mask out
        corresponding values in each input cube. If the ``mask_is_area_frac``
        keyword argument is set to true then each input cube is multiplied by
        the mask, which is assumed to contain area fraction values (in addition
        to possible masked values).
    :param bool mask_is_area_frac: If set to true then the mask array, if
        specified, is assumed to contain area fraction values which are to be
        multiplied with each input cube.
    :param bool area_weighted: If set to true then the statistic is weighted
        according to the area of the cells defined by the requested (or default)
        spatial coordinates. If a given input cube contains a cell measure named
        'area', then the associated data values are used. Otherwise the cell areas
        are computed using the ``iris.analysis.cartography.area_weights()``
        function. Alternatively, the weights can be defined explicitly by the
        calling program setting a 'weights' key in the ``agg_opts`` dictionary.

    Extra Keyword Arguments (`**kwargs`):

    :param bool append_to_cubelist: If set to true then, in the case where ``cubes``
        is a cubelist, the result cubes are appended to that cubelist. The default
        behaviour is to return a new cubelist. This option is ignored if ``cubes``
        is a single cube.
    :param bool cubes_alike: If set to true then all cubes are assumed to have
        the same spatial domain, which means that area weights, for example,
        only need to be computed once. Note that if a weights array is supplied
        via the ``agg_opts`` dictionary argument then the cubes are assumed to
        be alike.
    :param bool stop_on_error: If set to true then, in the case where ``cubes``
        is a cubelist, an exception will be raised if an error is encountered.
        The default behaviour is to log an error message and continue.

    :returns: A cube or cubelist containing the requested statistic calculated
        for each input cube. If a single cube is input then a single cube is
        returned, rather than a length-1 cubelist.
    """

    append_to_cubelist = kwargs.pop('append_to_cubelist', False)
    cubes_alike = kwargs.pop('cubes_alike', False)
    stop_on_error = kwargs.pop('stop_on_error', False)

    input_is_cube = False
    if isinstance(cubes, iris.cube.Cube):
        cubes = iris.cube.CubeList([cubes])
        input_is_cube = True
    elif not isinstance(cubes, iris.cube.CubeList):
        raise TypeError("The 'cubes' argument must be an Iris cube or cubelist.")

    if not agg_opts: agg_opts = {}

    # If a fixed weights array is to be used, either because one was passed in
    # or because the input cubes are alike, then create a variable that points
    # to it.
    fixed_weights = None
    if 'weights' in agg_opts:
        fixed_weights = agg_opts['weights']
        area_weighted = True
    elif area_weighted and cubes_alike:
        fixed_weights = calc_area_weights(cubes[0])
        agg_opts['weights'] = fixed_weights

    if not coords:
        coords = ['latitude', 'longitude']

    stat_cubes = iris.cube.CubeList()

    for cube in cubes:
        try:
            # Calculate area weights if requested (and not already done).
            if area_weighted and fixed_weights is None:
                agg_opts['weights'] = calc_area_weights(cube)

            # Apply a mask if one was specified.
            if mask is not None:
                masked_data = _apply_mask(cube.data, mask, mask_is_area_frac)
                cube = cube.copy(data=masked_data)

            # Calculate the requested statistic by collapsing the cube.
            stat_cube = cube.collapsed(coords, aggregator, **agg_opts)
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


def _apply_mask(data, mask, mask_is_area_frac=False):
    """
    Apply a mask to a data array. The shape of the masked array must be broad-
    castable to the shape of the data array. By default the mask is used simply
    to mask out corresponding elements in the data array. The mask_is_area_frac
    argument, if enabled, will result in the masked array being treated as if
    it were an array of area fraction values.

    :param numpy.ndarray data: The Numpy array to apply the mask to.
    :param numpy.MaskedArray mask: The masked array.
    :param bool mask_is_area_frac: If set to true then the data array is
        multiplied by the mask, which is assumed to contain area fraction values
        (in addition to possible masked values).
    :returns: A copy of the data array masked according to the mask array.
    :raises ValueError: Raised if the ``mask`` argument is not an instance of
        numpy.MaskedArray.
    """

    # If mask contains area fraction values then simply multiply the data array
    # by the mask array.
    if mask_is_area_frac:
        masked_data = data * mask

    # Otherwise mask out elements in the data array where mask.mask is True.
    else:
        if not ma.isMA(mask):
            msg = "The 'mask' argument must be a numpy MaskedArray instance."
            _logger.error(msg)
            raise ValueError(msg)

        if mask.shape == data.shape:
            bool_mask = mask.mask
        else:
            try:
                # if numpy >= v1.10 use the np.broadcast_to() function
                bool_mask = np.broadcast_to(mask.mask, data.shape)
            except AttributeError:
                # else try the iris.util.broadcast_to_shape() function
                bool_mask = iris.util.broadcast_to_shape(mask.mask, data.shape,
                    [data.ndim-2, data.ndim-1])

        masked_data = ma.masked_where(bool_mask, data)

    return masked_data
