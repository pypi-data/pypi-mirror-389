# (C) British Crown Copyright 2017-2020, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Implementation of the NetHeatFluxIntoOcean processor class, which can be used to
generate the Net Heat Flux Into Ocean diagnostic and, optionally, the area-weighted
mean of that diagnostic.

Refer to the :class:`NetHeatFluxIntoOcean` class documentation for further details.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import logging
import numpy as np

import iris
import iris.coords
import iris.analysis
import iris.exceptions

from afterburner import compare_iris_version
from afterburner.processors import AbstractProcessor
from afterburner.exceptions import DataProcessingError
from afterburner.utils import maskutils
from afterburner.utils.cubeutils import (calc_area_weights, data_shapes_equal,
    find_lat_long_coords, set_history_attribute)

# Definition of constants used in this module.
from scipy.constants import Stefan_Boltzmann   # ~ 5.670373e-08
# Latent heat of vaporization of water at 0 degC (J/kg).
LATENT_HEAT_OF_VAPORIZATION = 2.5e6

# Create a logger object.
_logger = logging.getLogger(__name__)


class NetHeatFluxIntoOcean(AbstractProcessor):
    """
    Calculates the Net Heat Flux Into Ocean diagnostic which, in terms of CF
    standard names, is derived using the following formula::

        net_heat_flux_into_ocean = surface_net_downward_shortwave_flux
                                 + surface_net_downward_longwave_flux
                                 - surface_upward_sensible_heat_flux
                                 - surface_upward_latent_heat_flux

    In terms of UM STASH codes the equivalent formula is::

        net_heat_flux_into_ocean = m01s01i203 + m01s02i201
                                 - m01s03i228 - m01s03i234

    Optionally, the net downward longwave flux quantity may be derived from STASH
    diagnostics 2,207 and 0,507 using the expression ``m01s02i207 - (m01s00i507**4 * SBC)``,
    where SBC is the Stefan Boltzmann constant.

    Similarly, the upward latent heat flux quantity may be derived from STASH
    diagnostic 3,232 using the expression ``m01s03i232 * LHV``, where LHV is the
    latent heat of vaporisation constant.

    The :meth:`run` method will search the input cubelist for these alternative
    diagnostics if the primary diagnostics (m01s02i201 and/or m01s03i234) are
    not present.

    A matching grid of land-area fraction (LAF) data may be supplied, either via
    the ``laf_file`` initialization argument or via the cubelist passed to the
    :meth:`run` method. The LAF grid is used as follows: (i) all land and coastal
    points are masked out in the returned cube(s); and (ii) in the case where the
    area-weighted mean of net heat flux is also requested, then area weights are
    multiplied by the *sea-area* fraction.

    .. note:: If LAF data is not specified via one of the aforementioned methods
       then it is assumed that each of the input cubes has been appropriately
       masked beforehand within client code.

    The ``laf_stashcode`` and ``laf_threshold`` arguments may be used to specify,
    respectively, the STASH code and land/sea threshold to use when loading and
    applying land-area fraction data. Refer to the argument descriptions below
    for information regarding their default values.

    If the ``calc_aw_mean`` argument is enabled for a call to the :meth:`run`
    method then the area-weighted mean of the net heat flux variable is also
    calculated and appended to the returned cubelist. The additional cube is
    assigned a long name of 'Area-weighted Mean of Net Heat Flux Into Ocean'.
    It is also given a CF-style cell method definition of 'area: mean where sea'.
    """

    def __init__(self, result_metadata=None, **kwargs):
        """
        :param dict result_metadata: A dictionary of metadata attributes to
            assign to the cube of net heat flux data returned by the :meth:`run`
            method. The following attributes are set by default (but can be
            overridden if desired):

            * long_name = 'Net Heat Flux Into Ocean'
            * var_name = 'net_heat_flux_into_ocean'
            * units = 'W m-2'

        Extra Keyword Arguments (`**kwargs`):

        :param str laf_file: Pathname to an optional file containing land-area
            fraction values.
        :param str laf_stashcode: The STASH code to use for extracting land-area
            fraction data from the input cubelist or the LAF file, if either of
            these are specified (default: m01s03i395).
        :param float laf_threshold: Specifies the threshold used to distinguish
            land and sea points in a grid of land-area fraction data. LAF values
            which are *greater than or equal* to this threshold value are treated
            as land. If left undefined then a default threshold of 0 is assumed,
            in which case all LAF grid cells having a *non-zero* area fraction are
            considered to represent land.
        """
        super(NetHeatFluxIntoOcean, self).__init__(**kwargs)

        # Assign default metadata values to set on the cube of net heat flux.
        self.result_metadata = {
            'standard_name': None,
            'long_name': 'Net Heat Flux Into Ocean',
            'var_name': 'net_heat_flux_into_ocean',
            'units': 'W m-2'
        }
        if result_metadata: self.result_metadata.update(result_metadata)

        # Assign STASH codes used to select required input fields.
        self.input_fields = {
            'net_dn_sw_flux': {'stash_code': 'm01s01i203',
                'std_name': 'surface_net_downward_shortwave_flux'},
            'net_dn_lw_flux': {'stash_code': 'm01s02i201',
                'std_name': 'surface_net_downward_longwave_flux'},
            'up_sh_flux': {'stash_code': 'm01s03i228',
                'std_name': 'surface_upward_sensible_heat_flux'},
            'up_lh_flux': {'stash_code': 'm01s03i234',
                'std_name': 'surface_upward_latent_heat_flux'},
            'dw_lw_flux': {'stash_code': 'm01s02i207',
                'std_name': 'surface_downwelling_longwave_flux_in_air'},
            'sea_sfc_temp': {'stash_code': 'm01s00i507',
                'std_name': 'surface_temperature'},
            'evap_flux': {'stash_code': 'm01s03i232',
                'std_name': 'water_evaporation_flux'},
        }

        # Record the pathname of a land-area fraction file, if specified. If not
        # then it is assumed that land-area fraction data, if provided at all,
        # is passed in via the cubelist passed to the run() method.
        self.laf_file = kwargs.get('laf_file')
        self.laf_stashcode = kwargs.get('laf_stashcode', 'm01s03i395')
        self.laf_threshold = kwargs.get('laf_threshold', 0)

        # If a LAF file was specified then perform a one-time load of the
        # contained LAF data.
        if self.laf_file:
            self.laf_cube = _read_laf_file(self.laf_file, self.laf_stashcode)
        else:
            self.laf_cube = None

    def run(self, cubes, **kwargs):
        """
        Run the NetHeatFluxIntoOcean diagnostic processor.

        :param iris.cube.CubeList cubes: An Iris cubelist containing the required
            source diagnostics. They should be identifiable either by their CF
            standard name (the preferred option) or by their STASH attribute. All
            source cubes must have the same shape. Optionally, the cubelist may
            contain a cube of land-area fraction data which, if present, will be
            used to mask out *land-only* grid cells.

        Extra Keyword Arguments (`**kwargs`):

        :param bool calc_aw_mean: If set to true (default is false) then the
            area-weighted mean is calculated for each horizontal (i.e. lat-long)
            slice of the cube of net heat flux values. The resulting cube is
            *appended* to the returned cubelist.

        :returns: A cubelist containing a cube of computed net heat flux data
            plus, if ``calc_aw_mean`` is true, a cube of area-weighted mean net
            heat flux values.
        :raises DataProcessingError: Raised if the required diagnostic data
            could not be found in the input cubelist, or if an error occurred
            during calculation of the net heat flux diagnostic.
        """
        self.logger.info("Calculating Net Heat Flux Into Ocean diagnostic...")

        calc_aw_mean = kwargs.get('calc_aw_mean', False)

        # Extract source diagnostics from the passed-in cubelist.
        input_cubes = self._extract_source_diags(cubes)
        net_dn_sw_flux, net_dn_lw_flux, up_sh_flux, up_lh_flux = input_cubes[:4]

        # Check that all source diagnostics have the same shape.
        if not data_shapes_equal(input_cubes):
            msg = "Input fields have inconsistent dimensions or lengths:"
            for cube in input_cubes:
                msg += '\n\t' + cube.summary(shorten=True)
            self.logger.error(msg)
            raise DataProcessingError(msg)

        # If a land-area fraction cube is present then load it.
        laf_data = self._get_laf_data(cubes)
        if laf_data is None:
            self.logger.warning("No land-area fraction data was provided.\n"
                "Assuming therefore that land points have been masked within "
                "the input cubes.")

        try:
            # Calculate the net heat flux field.
            flux_data = net_dn_sw_flux.data + net_dn_lw_flux.data \
                      - up_sh_flux.data - up_lh_flux.data
            net_heat_flux = net_dn_sw_flux.copy(data=flux_data)

            # If a land-area fraction mask has been specified then mask all grid
            # cells where LAF > 0, i.e. only whole-ocean cells preserved.
            if laf_data is not None:
                #laf_reshp = np.broadcast_to(laf_data, net_heat_flux.shape)
                #net_heat_flux.data = ma.masked_where(laf_reshp > self.laf_threshold,
                #    net_heat_flux.data)
                op = 'ge' if self.laf_threshold > 0 else 'gt'
                maskutils.apply_mask_to_cube(net_heat_flux, laf_data,
                    mask_only=False, compare_value=self.laf_threshold,
                    compare_op=op)

        except Exception as exc:
            msg = "Error trying to compute Net Heat Flux Into Ocean diagnostic."
            self.logger.error(msg)
            self.logger.error(str(exc))
            raise DataProcessingError(msg)

        # Set result cube metadata.
        for k, v in self.result_metadata.items():
            try:
                setattr(net_heat_flux, k, v)
            except Exception:
                self.logger.warning("Unable to set cube attribute '%s' to '%s'.", k, v)

        net_heat_flux.attributes = {}
        for key in ['source', 'um_version']:
            if key in net_dn_sw_flux.attributes:
                net_heat_flux.attributes[key] = net_dn_sw_flux.attributes[key]

        # Set the cube's history attribute.
        history = 'Generated net_heat_flux_into_ocean diagnostic.'
        set_history_attribute(net_heat_flux, history, replace=True)

        result_cubes = iris.cube.CubeList([net_heat_flux])

        # If requested, calculate the area-weighted mean of the NHF cube.
        if calc_aw_mean:
            net_heat_flux_awmean = _calc_aw_mean(net_heat_flux, laf_data=laf_data,
                laf_threshold=self.laf_threshold)
            result_cubes.append(net_heat_flux_awmean)

        return result_cubes

    def _extract_source_diags(self, cubes):
        """
        Extract the required source diagnostics from the specified cubelist.
        """

        # Extract cube of net downward shortwave flux.
        field = self.input_fields['net_dn_sw_flux']
        net_dn_sw_flux = self._extract_diagnostic(cubes, field['std_name'],
            field['stash_code'])

        # Extract cube of net downward longwave flux, or else derive it from the
        # formula (downwelling_lw_flux - surface_temp^4 * SBC)
        try:
            field = self.input_fields['net_dn_lw_flux']
            net_dn_lw_flux = self._extract_diagnostic(cubes, field['std_name'],
                field['stash_code'])
        except DataProcessingError:
            self.logger.info("Unable to find cube of net downward longwave flux.\n"
                "Searching for cubes of downwelling longwave flux and SST.")
            field = self.input_fields['dw_lw_flux']
            net_dn_lw_flux = self._extract_diagnostic(cubes, field['std_name'],
                field['stash_code'])
            field = self.input_fields['sea_sfc_temp']
            sea_sfc_temp = self._extract_diagnostic(cubes, field['std_name'],
                field['stash_code'])
            net_dn_lw_flux.data -= sea_sfc_temp.data**4 * Stefan_Boltzmann

        # Extract cube of upward sensible heat flux.
        field = self.input_fields['up_sh_flux']
        up_sh_flux = self._extract_diagnostic(cubes, field['std_name'],
            field['stash_code'])

        # Extract cube of upward latent heat flux, or else derive it from the
        # formula (water_evaporation_flux * LHV)
        try:
            field = self.input_fields['up_lh_flux']
            up_lh_flux = self._extract_diagnostic(cubes, field['std_name'],
                field['stash_code'])
        except DataProcessingError:
            self.logger.info("Unable to find cube of upward latent heat flux.\n"
                "Searching for cube of water evaporation flux.")
            # Extract cube of evaporation flux.
            field = self.input_fields['evap_flux']
            evap_flux = self._extract_diagnostic(cubes, field['std_name'],
                field['stash_code'])
            up_lh_flux = evap_flux * LATENT_HEAT_OF_VAPORIZATION

        return iris.cube.CubeList([net_dn_sw_flux, net_dn_lw_flux, up_sh_flux,
            up_lh_flux])

    def _extract_diagnostic(self, cubes, std_name, stash_code):
        """
        Extract from cubelist the cube corresponding to the specified CF standard
        name or, if that is not found, the STASH code.
        """
        cbs = []
        if std_name:
            cbs = cubes.extract(std_name)
        if not cbs:
            cbs = cubes.extract(iris.AttributeConstraint(STASH=stash_code))

        if len(cbs) != 1:
            msg = ("Unable to extract diagnostic '{0}' (STASH={1}) from input "
                "cubelist.".format(std_name, stash_code))
            raise DataProcessingError(msg)

        return cbs[0]

    def _get_laf_data(self, cubes):
        """
        Obtain a LAF data array either from the LAF file (if one was supplied)
        or from the list of input cubes (if one is present). If neither is
        available then return None.
        """

        laf_data = None

        if self.laf_cube:
            laf_cube = self.laf_cube   # previously loaded from a LAF file
        else:
            try:
                laf_cube = _load_laf_data(cubes, self.laf_stashcode)
            except:
                laf_cube = None

        if laf_cube:
            laf_data = laf_cube.data

        return laf_data


def _load_laf_data(cubes, laf_stashcode=None):
    """
    Load land-area fraction data from the input cubelist.
    """

    constraints = ['land_area_fraction']
    if laf_stashcode:
        constraints.append(iris.AttributeConstraint(STASH=laf_stashcode))

    laf_cubes = cubes.extract(constraints)

    if not laf_cubes:
        raise DataProcessingError("Unable to find any cubes containing "
            "land-area fraction data.")

    return laf_cubes[0]


def _read_laf_file(laf_file, laf_stashcode=None):
    """
    Read land area fraction data from the specified file, which could be in UM
    fieldsfile, pp or netcdf format.
    """

    try:
        # If the passed-in file contains a land area fraction field then the
        # following constraints should load 1 or 2 cubes. In the latter case
        # they'll typically refer to the same field.
        constraints = ['land_area_fraction']
        if laf_stashcode:
            constraints.append(iris.AttributeConstraint(STASH=laf_stashcode))

        futures = {'netcdf_promote': True} if compare_iris_version('2', 'lt') else {}

        with iris.FUTURE.context(**futures):
            laf_cubes = iris.load(laf_file, constraints)

        if not laf_cubes:
            raise DataProcessingError("Unable to find any cubes containing "
                "land-area fraction data.")

        return laf_cubes[0]

    except (IOError, OSError, iris.exceptions.IrisError):
        _logger.error("Problem reading land-area fraction data from file %s",
            laf_file)
        raise


def _calc_aw_mean(cube, laf_data=None, laf_threshold=0):
    """
    Calculate the area-weighted spatial mean of the specified cube of net heat
    flux data.
    """

    # Find the cube's lat & long coordinates and check that they have bounds set.
    lat_coord, lon_coord = find_lat_long_coords(cube)
    if not lat_coord.has_bounds():
        lat_coord.guess_bounds()
    if not lon_coord.has_bounds():
        lon_coord.guess_bounds()

    # Calculate the area weights.
    weights = calc_area_weights(cube)

    # If a LAF data array was supplied then set to zero those elements of the
    # weights array that correspond to land points (as determined by laf_threshold).
    # Other weights elements are multiplied by the sea-area fraction.
    if laf_data is not None:
        saf_data = 1 - np.where(laf_data > laf_threshold, 1, laf_data)
        weights = weights * saf_data

    # Calculate the mean of the input data.
    mean_cube = cube.collapsed([lat_coord, lon_coord], iris.analysis.MEAN,
        weights=weights)

    # Update identification attributes.
    mean_cube.long_name = 'Area-weighted Mean of Net Heat Flux Into Ocean'
    mean_cube.var_name = 'aw_mean_of_net_heat_flux_into_ocean'

    # Update cell method for area-weighted mean from 'mean' to 'mean where sea'.
    areacm = mean_cube.cell_methods[-1]
    mean_cube.cell_methods = mean_cube.cell_methods[:-1] + (iris.coords.CellMethod(
        'mean where sea', coords=['area'], intervals=areacm.intervals,
        comments=areacm.comments),)

    return mean_cube
