# (C) British Crown Copyright 2016-2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Implementation of the :class:`PolewardHeatTransport` diagnostic processor class,
which provides the capability to calculate poleward heat transport - either moist
static energy (MSE) or dry static energy (DSE) - from UM STASH diagnostics
30,224 (VT), 30,225 (VQ) and 30,227 (VZ).

The code snippet below shows a basic example of using the PolewardHeatTransport
processor::

    import iris
    from afterburner.processors.diags import PolewardHeatTransport

    # define Iris constraints to select the requisite source diagnostics
    constraints = [iris.Constraint('foo'), ...]
    cubes = iris.load(filenames, constraints)

    try:
        proc = PolewardHeatTransport()
        result_cubes = proc.run(cubes)
        mse = result_cubes[0]
        ...
    except:
        print("Oops!")

And here's an example in which user-defined earth radius and surface pressure
values are passed in, and the returned cubelist includes the underlying heat
transport components::

    try:
        proc = PolewardHeatTransport(earth_radius=6371578, surface_pressure=1050)
        result_cubes = proc.run(cubes, return_components=True)
        mse, sht, lht, pet = result_cubes
        ...
    except:
        print("Oops!")

"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import numpy as np
import scipy.constants
import iris
import iris.analysis.cartography

from afterburner.modelmeta import is_msi_stash_code
from afterburner.processors import AbstractProcessor
from afterburner.exceptions import DataProcessingError
from afterburner.utils.cubeutils import (are_data_shapes_equal,
    set_history_attribute)

# Define the physical constants required by the processor.

# Specific heat of dry air at constant volume (J/kg/K)
CVD = 717.0

# Standard acceleration due to gravity (m/s2)
GRAV = scipy.constants.g

# Latent heat of condensation (J/g)
LHC = 2.501e6

# Default value of the Earth's radius (as used by the UM).
EARTH_RADIUS = 6371229.0

# Default surface air pressure (hPa)
P0 = 1013.25


class PolewardHeatTransport(AbstractProcessor):
    """
    Calculates the poleward heat transport (PHT) diagnostic from the following
    UM STASH diagnostics:

    * 30,224 (VT, CF standard name: 'product_of_northward_wind_and_air_temperature')
    * 30,225 (VQ, CF standard name: 'product_of_northward_wind_and_specific_humidity')
    * 30,227 (VZ, CF standard name: 'product_of_northward_wind_and_geopotential_height').

    This processor class assumes that the prerequisite input diagnostics possess
    the same shape and dimensions, the latter being (time, pressure, latitude,
    longitude). The vertical (pressure) axis may be monotonic increasing or
    decreasing. The time axis is assumed to be monotonic increasing.

    By default the calculated diagnostic is moist static energy (MSE). If desired,
    dry static energy (DSE) can be calculated instead by enabling the ``calc_dse``
    keyword argument.

    MSE is calculated as the sum of the zonally-meaned and vertically-integrated
    input cubes, i.e.::

        MSE = (vizi(VT) * CVD) + (vizi(VQ) * LHC) + (vizi(VZ) * G)

    where ``vizi`` represents the zonal and vertical integration operation, CVD
    is the specific heat of dry air, LHC is the latent heat of condensation, and
    G is acceleration due to gravity.

    The equivalent formula for DSE is as follows::

        DSE = (vizi(VT) * CVD) + (vizi(VZ) * G)

    The units of the returned cube of PHT are given in petawatts (PW). The
    calculation of PHT assumes a spherical Earth, the value of which may be
    specified via the ``earth_radius`` keyword argument. If undefined then the
    radius is determined, if possible, from the first input cube. Failing that,
    a default value of 6371229 m is used (as per the Unified Model).

    .. note:: By default, array elements equal to zero in the input diagnostics
       are masked out. This behaviour can be disabled at object initialisation
       time via the ``mask_zero_values`` keyword argument, as described below.
    """

    def __init__(self, result_metadata=None, **kwargs):
        """
        :param dict result_metadata: A dictionary of metadata attributes to
            assign to the result cube returned by the :meth:`run` method. The
            following attributes are set by default but can be overridden, if
            desired, using the current argument:

            * standard_name = 'northward_atmosphere_heat_transport'
            * long_name = 'Poleward Heat Transport (Moist Static Energy)'
            * var_name = 'moist_static_energy'
            * units = 'PW' (petawatts)

            (NB: for Moist/moist above read Dry/dry in the case of dry static energy)

        Extra Keyword Arguments (`**kwargs`):

        :param bool calc_dse: If set to true then calculate dry static energy
            instead of moist static energy (which is the default).
        :param bool mask_zero_values: If set to true (the default) then zero-valued
            array elements in the input cubes are masked prior to being used.
        :param bool return_components: If set to true then the 3 heat transport
            variables used to compute PHT are appended to the returned cubelist
            when the processor is executed (default: false).
        :param float earth_radius: The radius of the Earth in metres. Used to
            calculate lengths of parallels of latitude (default: the value, if
            any, associated with the input diagnostics, else 6371229 m).
        :param float surface_pressure: The surface pressure in hPa (default: 1013.25)
        """
        super(PolewardHeatTransport, self).__init__(**kwargs)

        self.calc_dse = kwargs.get('calc_dse', False)
        self.calc_mse = not self.calc_dse
        self.mask_zero_values = kwargs.get('mask_zero_values', True)
        self.earth_radius = float(kwargs.get('earth_radius', 0))
        self.surface_pressure = float(kwargs.get('surface_pressure', P0))
        self.return_components = kwargs.get('return_components', False)

        # The Earth radius value to use in calculations. In order of precedence
        # this will be:
        # 1. The user-defined value specified via the earth_radius argument.
        # 2. The value obtained from the latitude coordinate of an input cube.
        # 3. The default value of 6371229 m
        # The value gets set during each invocation of the run() method.
        self._radius = 0

        # Assign default metadata values to set on the result cube.
        if self.calc_mse:
            self.result_metadata = {
                'standard_name': 'northward_atmosphere_heat_transport',
                'long_name': 'Poleward Heat Transport (Moist Static Energy)',
                'var_name': 'moist_static_energy',
                'units': 'PW',
            }
        else:
            self.result_metadata = {
                'standard_name': 'northward_atmosphere_heat_transport',
                'long_name': 'Poleward Heat Transport (Dry Static Energy)',
                'var_name': 'dry_static_energy',
                'units': 'PW',
            }
        if result_metadata: self.result_metadata.update(result_metadata)

        # Assign default identifiers for the required input diagnostics.
        self.input_diagnostic_ids = {
            'sensible_heat_transport': 'm01s30i224',
            'latent_heat_transport': 'm01s30i225',
            'potential_energy_transport': 'm01s30i227'
        }

        # Update any diagnostic identifiers passed in via keyword arguments.
        for var_id in self.input_diagnostic_ids:
            if var_id in kwargs:
                self.input_diagnostic_ids[var_id] = kwargs[var_id]


    def run(self, cubes, *args, **kwargs):
        """
        Run the PolewardHeatTransport processor.

        The dimensions of the input cubes should be (time, pressure, latitude,
        longitude). All input cubes must have the same shape.

        :param iris.cube.CubeList cubes: Cubelist containing cubes representing
            the following UM diagnostics:

            * STASH code m01s30i224 (sensible heat transport, VT)
            * STASH code m01s30i225 (latent heat transport, VQ)
            * STASH code m01s30i227 (potential energy transport, VZ)

            Any other cubes present are silently ignored.
        :param bool return_components: If set to true then the 3 heat transport
            variables used to compute PHT are also appended to the returned
            cubelist in the order: sensible heat transport, latent heat transport,
            potential energy transport (default: false).
        :returns: A cubelist containing a cube of poleward heat transport with
            the dimensions (time, latitude).
        :raises afterburner.exceptions.DataProcessingError: Raised if a problem
            was encountered reading the input cubes or computing the poleward
            heat transport diagnostic data.
        """
        self.logger.info("Calculating Poleward Heat Transport diagnostic...")

        return_components = kwargs.get('return_components', self.return_components)

        # Extract a cube of sensible heat transport.
        sht = self._extract_diagnostic(cubes,
            self.input_diagnostic_ids['sensible_heat_transport'])

        # Extract a cube of latent heat transport.
        lht = self._extract_diagnostic(cubes,
            self.input_diagnostic_ids['latent_heat_transport'])

        # Extract a cube of potential energy transport.
        pet = self._extract_diagnostic(cubes,
            self.input_diagnostic_ids['potential_energy_transport'])

        # Check that the input cubes have the same shape.
        if not are_data_shapes_equal([sht, lht, pet]):
            cbs = [cube.summary(shorten=True) for cube in [sht, lht, pet]]
            msg = ("The input cubes do not all have the same shape.\n"
                "m01s30i224: {0}\nm01s30i225: {1}\nm01s30i227: {2}".format(*cbs))
            self.logger.error(msg)
            raise DataProcessingError(msg)

        # Determine the value of Earth radius to use in calculations.
        self._radius = self.earth_radius or _get_earth_radius(sht, EARTH_RADIUS)

        # Calculate the poleward heat transport diagnostic.
        try:
            pht, shtc, lhtc, petc = self._calc_pht(sht, lht, pet, return_components)
        except Exception as exc:
            msg = ("Error trying to generate poleward heat transport cube from "
                    "input cubes.")
            self.logger.error(msg)
            self.logger.error(str(exc))
            raise DataProcessingError(msg)

        # Set result cube metadata.
        pht.attributes['surface_pressure'] = self.surface_pressure
        if self.earth_radius:
            # Only record the earth radius if it's specified by the calling program.
            pht.attributes['earth_radius'] = self.earth_radius

        for k, v in self.result_metadata.items():
            try:
                setattr(pht, k, v)
            except:
                self.logger.warning("Unable to set cube attribute '%s' to '%s'.", k, v)

        # Set the cube's history attribute.
        if self.calc_mse:
            history = 'Generated moist static energy transport diagnostic.'
        else:
            history = 'Generated dry static energy transport diagnostic.'
        set_history_attribute(pht, history, replace=True)

        self.logger.debug("Generated cube of Poleward Heat Transport:\n\t%s",
            pht.summary(shorten=True))

        if return_components:
            return iris.cube.CubeList([pht, shtc, lhtc, petc])
        else:
            return iris.cube.CubeList([pht])

    def _calc_pht(self, sht, lht, pet, return_components):
        """
        Calculate the poleward heat transport diagnostic from the three input
        diagnostics.

        :param iris.cube.Cube sht: A cube of sensible heat transport.
        :param iris.cube.Cube lht: A cube of latent heat transport.
        :param iris.cube.Cube sht: A cube of potential energy transport.
        :param bool return_components: If set to true then include the 3 heat
            transport components in the returned list of cubes.
        :returns: A length-4 list of cubes. The 0th element is the cube of PHT.
            If return_components is true then elements 1 to 3 are SHT, LHT and
            PET, in that order. Otherwise, they are set to None.
        """

        # Mask out zero values in input cubes if required.
        if self.mask_zero_values:
            sht.data = np.ma.masked_equal(sht.data, 0)
            lht.data = np.ma.masked_equal(lht.data, 0)
            pet.data = np.ma.masked_equal(pet.data, 0)

        # Calculate thickness of pressure levels.
        pcoord = sht.coord('pressure')
        plev_thickness = _calc_pressure_level_thickness(pcoord.points, self.surface_pressure)

        # Calculate lengths of parallels of latitude.
        lat_weights = iris.analysis.cartography.cosine_latitude_weights(sht[0,0,:,:])
        lat_lengths = lat_weights[:,0] * 2 * scipy.constants.pi * self._radius

        # Calculate integrals for sensible heat transport in petawatts.
        sht_vizi = _calc_integrals(sht, plev_thickness, lat_lengths)
        sht_vizi *= CVD * 1e-15

        # Calculate integrals for latent heat transport in petawatts.
        lht_vizi = _calc_integrals(lht, plev_thickness, lat_lengths)
        lht_vizi *= LHC * 1e-15

        # Calculate integrals for potential energy transport in petawatts.
        pet_vizi = _calc_integrals(pet, plev_thickness, lat_lengths)
        pet_vizi *= GRAV * 1e-15

        # Construct an empty cube dimensioned (time, latitude) to hold the PHT
        # diagnostic data.
        tcoord = sht.coord('time').copy()
        ycoord = sht.coord('latitude').copy()
        data = np.zeros([len(tcoord.points), len(ycoord.points)])
        pht = iris.cube.Cube(data, dim_coords_and_dims=[(tcoord, 0), (ycoord, 1)])

        if self.calc_mse:
            # Calculate moist static energy as sum of SHT, LHT and PET.
            pht.data = sht_vizi + lht_vizi + pet_vizi
        else:
            # Calculate dry static energy as sum of SHT and PET
            pht.data = sht_vizi + pet_vizi

        # If requested, create cubes of the 3 underlying heat transport
        # component variables.
        if return_components:
            shtc = iris.cube.Cube(sht_vizi, units='PW',
                long_name='Meridional Sensible Heat Transport',
                var_name='sensible_heat_transport',
                dim_coords_and_dims=[(tcoord, 0), (ycoord, 1)])
            lhtc = iris.cube.Cube(lht_vizi, units='PW',
                long_name='Meridional Latent Heat Transport',
                var_name='latent_heat_transport',
                dim_coords_and_dims=[(tcoord, 0), (ycoord, 1)])
            petc = iris.cube.Cube(pet_vizi, units='PW',
                long_name='Meridional Potential Energy Transport',
                var_name='potential_energy_transport',
                dim_coords_and_dims=[(tcoord, 0), (ycoord, 1)])
        else:
            shtc = lhtc = petc = None

        return pht, shtc, lhtc, petc

    def _extract_diagnostic(self, cubes, diagnostic_id):
        """
        Extract from cubelist the cube corresponding to the specified diagnostic
        ID, which should either be a CF standard name or a STASH code.

        :param iris.cube.CubeList cubes: A list of input cubes.
        :param str diagnostic_id: The CF standard name or STASH code of the
            diagnostic to extract from the cubelist.
        :returns: The cube containing the requested diagnostic.
        :raises DataProcessingError: Raised if a cube corresponding to the
            requested diagnostic could not be found.
        """
        if is_msi_stash_code(diagnostic_id):
            cbs = cubes.extract(iris.AttributeConstraint(STASH=diagnostic_id))
        else:
            cbs = cubes.extract(diagnostic_id)

        if len(cbs) == 1:
            return cbs[0]
        else:
            msg = ("Error extracting diagnostic '{0}' from input cubelist.".format(
                diagnostic_id))
            self.logger.error(msg)
            raise DataProcessingError(msg)


def _calc_pressure_level_thickness(plevels, p0):
    """
    Calculate 'thickness' of layers between successive pressure levels.

    :param np.ndarray plevels: A numpy array of pressure levels.
    :param float p0: Pressure in hPA at surface.
    :returns: A 1D numpy array of layer thicknesses.
    """
    # Ensure that local copy of plevels is monotonic decreasing.
    plev = plevels[::-1] if plevels[0] < plevels[-1] else plevels
    ptop = min(plev)

    idx, = np.where(plev==ptop)
    useplev = plev[0:idx[0]+1]
    nlev = len(useplev)
    dp = np.zeros(nlev, dtype=plevels.dtype)

    # thickness of lowest level = surface pressure - 0th pressure level
    #   + half of thickness between 0th and 1st pressure levels
    dp[0] = 0.5 * (plev[0] - plev[1]) + (p0 - plev[0])

    # thickness of highest level =
    #    half of thickness between highest and 2nd highest pressure levels
    dp[nlev-1] = 0.5 * (plev[nlev-2] - plev[nlev-1])

    # rest = half of thickness between Kth and K+1th pressure levels
    for l in np.arange(1, nlev-1):
        dp[l] = 0.5 * (plev[l-1] - plev[l]) + 0.5 * (plev[l] - plev[l+1])

    return dp[::-1] if plevels[0] < plevels[-1] else dp


def _calc_integrals(cube, plev_thickness, lat_lengths):
    """
    Calculate vertical and zonal integrals.

    :param iris.cube.Cube cube: The cube to integrate over.
    :param np.ndarray plev_thickness: A numpy array of pressure level thicknesses.
    :param np.ndarray lat_lengths: A numpy array of weighted lengths of parallels
        of latitude.
    :returns: A numpy array representing the input cube's data payload integrated
        over the x (longitude) and z (pressure) axes.
    """

    # Calculate zonal mean of right-most (longitude) axis. This should yield a
    # 3D array dimensioned (time, pressure, lat).
    zidata = np.mean(cube.data, axis=3) * lat_lengths

    # Integrate over vertical (pressure) axis. This should yield a 2D array
    # dimensioned (time, lat).
    vizidata = np.ma.sum(zidata*plev_thickness[:,None], axis=1) * 100.0 / GRAV

    return vizidata


def _get_earth_radius(cube, default=0.0):
    """
    Return the value of the Earth's radius if one is defined as part of the
    coordinate system attached to the supplied cube. The cube is assumed to
    possess a latitude coordinate dimension.

    :param iris.cube.Cube cube: The cube from which to obtain the Earth radius.
    :param float default: The default radius value to return if one cannot be
        determined from the specified cube.
    :returns: The Earth radius associated with the specified cube, or the value
        passed in via the ``default`` argument.
    """
    radius = default

    try:
        latcrd = cube.coord('latitude')
        cs = latcrd.coord_system
        invf = cs.inverse_flattening
        if invf == 0:
            radius = cs.semi_major_axis
    except:
        pass

    return radius
