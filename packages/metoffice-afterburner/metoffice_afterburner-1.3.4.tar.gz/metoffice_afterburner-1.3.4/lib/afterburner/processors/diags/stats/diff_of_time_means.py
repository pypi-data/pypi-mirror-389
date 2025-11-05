# (C) British Crown Copyright 2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
This module provides an implementation of the :class:`DiffOfTimeMeans` class.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import iris
from iris.exceptions import IrisError

from afterburner.processors import AbstractProcessor
from afterburner.exceptions import DataProcessingError
from afterburner.stats import temporal
from afterburner.modelmeta import is_msi_stash_code
from afterburner.utils.cubeutils import make_cell_method_cube_func


class DiffOfTimeMeans(AbstractProcessor):
    """
    Calculates the difference between the time-mean of two diagnostics.
    """

    def __init__(self, meaning_period='month', result_metadata=None, **kwargs):
        """
        :param str meaning_period: The meaning period. Permitted values are as
            per the TP constants defined in the :mod:`afterburner.stats.temporal`
            module.
        :param dict result_metadata: A dictionary of CF-style metadata attributes
            to assign to the result cube returned by the :meth:`run` method.
            Typical attributes include standard_name, long_name, var_name and
            units.
        """
        super(DiffOfTimeMeans, self).__init__(**kwargs)
        self.result_metadata = result_metadata or {}
        self.meaning_period = meaning_period

    def run(self, cubes, **kwargs):
        """
        Run the processor. The two cubes used to calculate the result may be
        identified by specifying the ``cube1_constraints`` and ``cube2_constraints``
        keyword arguments. Otherwise the first two cubes in the input cubelist are
        used as, respectively, the left-hand and right-hand operands.

        :param iris.cube.CubeList cubes: An Iris cubelist containing the diagnostics
            to be time-meaned and differenced.

        Extra Keyword Arguments (`**kwargs`):

        :param iris.Constraint cube1_constraints: An Iris constraint, or list
            of constraints, used to select the first cube.
        :param iris.Constraint cube2_constraints: An Iris constraint, or list
            of constraints, used to select the second cube.
        :param dict result_metadata: May be used to override the dictionary of
            metadata attributes specified during object initialisation.

        :returns: A cubelist containing the resulting cube.
        :raises DataProcessingError: Raised if the required diagnostic data
            could not be found in the input cubelist, or if an error occurred
            during calculation of the result.
        """

        if len(cubes) < 2:
            msg = ("The input cubelist must contain at least two cubes.")
            raise ValueError(msg)

        if 'result_metadata' in kwargs:
            self.result_metadata = kwargs['result_metadata']

        cube1_constraints = kwargs.get('cube1_constraints')
        cube2_constraints = kwargs.get('cube2_constraints')

        if cube1_constraints:
            try:
                cube1 = cubes.extract(cube1_constraints)[0]
            except IndexError:
                msg = ("Supplied Iris constraints result in an empty cubelist.\n"
                    "Expected a single cube to be selected.")
                raise DataProcessingError(msg)
        else:
            cube1 = cubes[0]

        if cube2_constraints:
            try:
                cube2 = cubes.extract(cube2_constraints)[0]
            except IndexError:
                msg = ("Supplied Iris constraints result in an empty cubelist.\n"
                    "Expected a single cube to be selected.")
                raise DataProcessingError(msg)
        else:
            cube2 = cubes[1]

        try:
            mean_cube1 = _calc_mean(cube1, self.meaning_period)
            mean_cube2 = _calc_mean(cube2, self.meaning_period)
        except IrisError:
            self.logger.error("Problem trying to compute time-mean of input cubes.")
            raise

        try:
            result_cube = mean_cube1 - mean_cube2
        except IrisError:
            self.logger.error("Problem trying to compute difference of meaned cubes.")
            raise

        # Set result cube metadata.
        for k, v in self.result_metadata.items():
            try:
                setattr(result_cube, k, v)
            except:
                self.logger.warn("Unable to set cube attribute '%s' to '%s'.", k, v)

        # Set the cube's history attribute.
        var_name = result_cube.var_name or result_cube.name()
        history = ("Generated variable {0} as time-mean({1}) - time-mean({2})\n"
            "using a meaning period of '{3}'.".format(var_name, cube1.name(),
            cube2.name(), self.meaning_period))
        result_cube.attributes['history'] = history

        return iris.cube.CubeList([result_cube])


class DiurnalTemperatureRange(DiffOfTimeMeans):
    """
    Calculates the diurnal temperature range given cubes of hourly maximum and
    hourly minimum temperature data. The two cubes are first meaned (monthly, by
    default) and then differenced according to the formula (max-temp - min-temp).
    The required input cubes can be identified by STASH code or CF standard name.
    """

    def __init__(self, diagnostic_id='m01s03i236', meaning_period='month',
            result_metadata=None, **kwargs):
        """
        :param str diagnostic_id: The STASH code (in MSI format) or the CF standard
            name of the temperature diagnostic.
        :param str meaning_period: The meaning period. Permitted values are as
            per the TP constants defined in the :mod:`afterburner.stats.temporal`
            module.
        :param dict result_metadata: A dictionary of CF-style metadata attributes
            to assign to the result cube returned by the :meth:`run` method.
            Typical attributes include standard_name, long_name, var_name and
            units.
        """
        super(DiurnalTemperatureRange, self).__init__(meaning_period=meaning_period,
            result_metadata=result_metadata, **kwargs)
        self.diagnostic_id = diagnostic_id

    def run(self, cubes, **kwargs):
        """
        Run the processor.

        :param iris.cube.CubeList cubes: An Iris cubelist containing minimum and
            maximum temperature diagnostics.

        Extra Keyword Arguments (`**kwargs`):

        :param dict result_metadata: May be used to override the dictionary of
            metadata attributes specified during object initialisation.

        :returns: A cubelist containing the resulting cube of diurnal temperature
            range data.
        :raises DataProcessingError: Raised if the required diagnostic data
            could not be found in the input cubelist, or if an error occurred
            during calculation of the result.
        """

        if len(cubes) < 2:
            msg = ("The input cubelist must contain at least two cubes.")
            raise ValueError(msg)

        if is_msi_stash_code(self.diagnostic_id):
            name_constraint = iris.AttributeConstraint(STASH=self.diagnostic_id)
        else:
            name_constraint = iris.Constraint(name=self.diagnostic_id)

        is_max = make_cell_method_cube_func('maximum', 'time', interval='1 hour')
        is_min = make_cell_method_cube_func('minimum', 'time', interval='1 hour')

        kwargs['cube1_constraints'] = name_constraint & iris.Constraint(cube_func=is_max)
        kwargs['cube2_constraints'] = name_constraint & iris.Constraint(cube_func=is_min)

        return super(DiurnalTemperatureRange, self).run(cubes, **kwargs)


# TODO: move to the cubeutils module?
def _remove_unwanted_coords(cubes, coord_names):
    """
    Remove named coordinates from the supplied cubelist. At times this procedure
    is a necessary prerequisite to certain cube operations (e.g. subtracting one
    cube from another with conflicting auxiliary coordinates).

    :param iris.cube.CubeList cubes: The cubes from which to remove coordinates.
    :param list coord_names: An iterable of coordinate names.
    """
    for cube in cubes:
        cube_coords = [c.name() for c in cube.coords()]
        for unwanted in coord_names:
            if unwanted in cube_coords:
                try:
                    cube.remove_coord(unwanted)
                except IrisError:
                    pass


def _calc_mean(cube, meaning_period):
    """
    Calculate the mean of a cube and remove from the result cube those auxiliary
    coordinates that may impede later cube operations.
    """
    old_aux_coords = set(c.name() for c in cube.coords(dim_coords=False))

    mean_cube = temporal.calc_time_stat(cube, iris.analysis.MEAN,
        meaning_period, drop_new_coords=True)

    new_aux_coords = set(c.name() for c in mean_cube.coords(dim_coords=False))
    new_aux_coords.difference_update(old_aux_coords)

    unwanted_coords = set(['forecast_period', 'forecast_reference_time'])
    unwanted_coords.update(new_aux_coords)
    _remove_unwanted_coords([mean_cube], unwanted_coords)

    return mean_cube
