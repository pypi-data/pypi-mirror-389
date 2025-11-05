# (C) British Crown Copyright 2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Implementation of the HistogramMaker processor class, which can be used to
generate scales-of-variability histogram data for one or more diagnostics.
Refer to the :class:`HistogramMaker` class documentation for further details.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import numpy as np

import iris
import iris.analysis
import iris.exceptions

from afterburner.processors import AbstractProcessor
from afterburner.exceptions import DataProcessingError


class HistogramMaker(AbstractProcessor):
    """
    A processor class for generating binned frequency data from one or more Iris
    cubes. Given an array of bin values, each cube is collapsed over a selected
    coordinate axis (time, by default) using the iris.analysis.COUNT aggregator.
    This has the effect of counting the number of data values that occur within
    each bin for all permutations of the remaining axes (e.g. for each grid cell
    if an input cube consists of the dimensions time-lat-long).

    The bin values to use for building the histogram can be passed in either at
    object initialisation time, in which case they act as the defaults for any
    subsequent invocations of the :meth:`run` method, or they can be passed in
    to the latter method, in which case they remain in force unless updated
    during a subsequent call. Failing to define the bin values by one or other
    of these methods will result in an AttributeError being raised.

    It should be noted that, in the case of a list of input cubes, the :meth:`run`
    method will use the same bin values for each cube. It is the responsibility
    of client code, therefore, to ensure that bin values are suitable for each cube.

    The returned cube(s) possess the same ``standard_name`` attribute as the
    corresponding input cube, assuming that attribute is defined. The ``var_name``
    and ``long_name`` attributes are set to 'bin_count' and 'number of values per bin',
    respectively. These can be changed, if desired, via the ``result_metadata``
    argument on the :meth:`__init__` method.

    At the time of writing, Iris adds a cell method named 'count' to each cube
    returned by the run method. This is **not** CF-compliant. If required, this
    cell method can be removed by setting the ``fix_cell_methods`` argument to
    true.
    """

    def __init__(self, bin_array=None, coord_name='time', result_dtype=None,
            result_metadata=None, **kwargs):
        """
        :param np.ndarray bin_array: A 1D array of bin values. Each element of
            the array represents the *lower* bound of the corresponding bin,
            i.e. bin_array[n] is the lower bound of the nth bin (assuming the
            customary 0-based array indexing).
        :param str coord_name: The name of the coordinate axis to collapse over.
            Defaults to 'time'.
        :param numpy.dtype result_dtype: The data type of the returned cubes of
            histogram data. Defaults to numpy.int32.
        :param dict result_metadata: A dictionary of metadata attributes to
            assign to the result cubes returned by the :meth:`run` method.

        Extra Keyword Arguments (`**kwargs`):

        :param bool fix_cell_methods: If true then remove any cell methods named
            'count' from each result cube. A cell method named 'count' is not
            CF-compliant. Defaults to false.
        """
        super(HistogramMaker, self).__init__(**kwargs)

        self.bin_array = bin_array
        self.coord_name = coord_name
        self.result_dtype = result_dtype or np.int32

        # Assign default metadata values to set on the generated cube(s).
        self.result_metadata = {
            'var_name': 'bin_count',
            'long_name': 'number of values per bin',
        }
        if result_metadata: self.result_metadata.update(result_metadata)

        self.fix_cell_methods = kwargs.get('fix_cell_methods', False)

    def run(self, cubes, bin_array=None, **kwargs):
        """
        Run the HistogramMaker processor.

        :param iris.cube.CubeList cubes: An Iris cubelist, each of whose cubes
            will be processed using the parameters defined at initialisation
            time. Each cube must possess a time dimension.
        :param np.ndarray bin_array: A 1D array of bin values. Each element of
            the array represents the *lower* bound of the corresponding bin,
            i.e. bin_array[n] is the lower bound of the nth bin (assuming the
            customary 0-based array indexing).
        :returns: A cubelist containing cubes of histogram data, one for each
            input cube.
        :raises AttributeError: Raised if the bin_array attribute has not been
            defined, either via this method or at initialisation time.
        :raises DataProcessingError: Raised if an error occurred during
            calculation of the histogram data.
        """

        if bin_array is not None:
            self.bin_array = bin_array
        elif self.bin_array is None:
            msg = "The 'bin_array' attribute has not been defined."
            self.logger.error(msg)
            raise AttributeError(msg)

        if isinstance(cubes, iris.cube.Cube):
            cubes = iris.cube.CubeList([cubes])

        cubelist = iris.cube.CubeList()

        for cube in cubes:
            try:
                cubelist.append(self._calc_histogram(cube))
            except Exception as exc:
                self.logger.error(str(exc))
                raise DataProcessingError("Error calculating histogram data "
                    "for diagnostic %s.", cube.name())

        return cubelist

    def _calc_histogram(self, cube):

        self.logger.info("Calculating histogram data for diagnostic %s...",
            cube.name())

        # Generate a cube of counts for the first bin and use it as a template
        # for the remaining bins.
        pbin = self.bin_array
        hist = cube.collapsed(self.coord_name, iris.analysis.COUNT,
            function=lambda values: (pbin[0] <= values) & (values < pbin[1]))

        # Create a new 'bin' dimension coordinate object and use it to create a
        # new cube with that dimension inserted in position 0.
        pbin_coord = iris.coords.DimCoord(pbin, bounds=_make_bin_bounds(pbin),
            long_name='bin_value', var_name='bin_value',  units=cube.units)
        pbin_coord.attributes['comment'] = ("Coordinates represent the lower "
            "bound of each bin.")
        hist_cube = _extend_cube_with_dimcoord(hist, pbin_coord)

        # Loop through the remaining bins, updating the corresponding data slices
        # in hist_cube.
        nbins = pbin.shape[0]
        for x in range(1, nbins-1):
            hist = cube.collapsed(self.coord_name, iris.analysis.COUNT,
                function=lambda values: (pbin[x] <= values) & (values < pbin[x+1]))
            hist_cube.data[x] = hist.data

        # Add the count of any values >= pbin[n-1] to the final bin.
        hist = cube.collapsed(self.coord_name, iris.analysis.COUNT,
            function=lambda values: pbin[nbins-1] <= values)
        hist_cube.data[nbins-1] = hist.data

        # Coerce the cube's data type to that defined by result_dtype.
        hist_cube.data = hist_cube.data.astype(self.result_dtype)

        # Add a scalar coordinate that records the time period of the input data.
        taxis = cube.coord('time')
        nt = len(taxis.points)
        tmin = taxis.bounds[0,0]
        tmax = taxis.bounds[-1,1]
        tbnds = np.array([tmin, tmax])
        tcoord = iris.coords.DimCoord(taxis.points[nt//2], standard_name='time',
            var_name='time', units=taxis.units, bounds=tbnds)
        hist_cube.add_aux_coord(tcoord)

        if self.fix_cell_methods:
            _fix_cell_methods(hist_cube)

        # Set result cube metadata.
        for k, v in self.result_metadata.items():
            try:
                setattr(hist_cube, k, v)
            except iris.exceptions.IrisError:
                self.logger.warning("Unable to set cube attribute '%s' to '%s'.", k, v)

        return hist_cube


def _make_bin_bounds(bin_array, max_bnd=None):
    """
    Make a cell bounds array dimensioned (bin_array.size, 2) from the specified
    array of bin values, which are assumed to represent the *lower* value of
    each bin. If max_bnd is specified then it is assigned to the final upper
    bound value. Otherwise the maximum possible value for the array's data type
    is used.
    """

    try:
        max_val = np.finfo(bin_array.dtype).max
    except ValueError:
        max_val = np.iinfo(bin_array.dtype).max

    bin_bnds = np.zeros([bin_array.size, 2], dtype=bin_array.dtype)
    bin_bnds[:,0] = bin_array[:]
    bin_bnds[:-1,1] = bin_array[1:]
    bin_bnds[-1,1] = max_val if max_bnd is None else max_bnd

    return bin_bnds


def _extend_cube_with_dimcoord(cube, dimcoord, dimcoord_index=0):
    """
    Create a new cube with an extra dimension coordinate in the specified index
    location. Copy the data from the input cube to the first slice of the new
    cube.
    """

    coords = list(cube.dim_coords)
    coords.insert(dimcoord_index, dimcoord)

    dim_coords_and_dims = [(c,i) for i,c in enumerate(coords)]

    newcube_shape = tuple(c.shape[0] for c in coords)

    newcube = iris.cube.Cube(np.zeros(newcube_shape),
        standard_name=cube.standard_name, long_name=cube.long_name,
        var_name=cube.var_name, attributes=cube.attributes,
        units=cube.units, cell_methods=cube.cell_methods,
        dim_coords_and_dims=dim_coords_and_dims)

    newcube.data[0] = cube.data

    return newcube


def _fix_cell_methods(cube):
    """
    Fix the cube's cell methods. Currently this entails removing any cell methods
    named 'count' since this is not a CF-compliant method.
    """
    if not cube.cell_methods: return

    valid_methods = [cm for cm in cube.cell_methods if cm.method != 'count']

    if len(valid_methods) != len(cube.cell_methods):
        cube.cell_methods = tuple(valid_methods) or None
