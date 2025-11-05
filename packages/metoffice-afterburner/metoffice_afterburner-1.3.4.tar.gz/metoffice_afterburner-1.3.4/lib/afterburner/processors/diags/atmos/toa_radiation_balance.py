# (C) British Crown Copyright 2016-2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Implementation of the ToaRadiationBalance processor class, which can be used to
generate the top-of-atmosphere (TOA) radiation balance diagnostic. Refer to the
:class:`ToaRadiationBalance` class documentation for further details.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import iris
from afterburner.processors import AbstractProcessor
from afterburner.exceptions import DataProcessingError
from afterburner.utils.cubeutils import set_history_attribute


# TODO: At some point this class should be re-implemented as a generic 'derived
# diagnostic' class based on an arithmetic combination of STASH diagnostics.
class ToaRadiationBalance(AbstractProcessor):
    """
    Calculates the top-of-atmosphere (TOA) radiation balance diagnostic which,
    in CF parlance, is described using the formula::

        toa_net_downward_radiative_flux = toa_incoming_shortwave_flux -
            toa_outgoing_shortwave_flux - toa_outgoing_longwave_flux

    In the case of the Unified Model the aforementioned geophysical quantities
    correspond to the three STASH diagnostics ``m01s01i207``, ``m01s01i208`` and
    ``m01s03i332``, respectively.
    """

    def __init__(self, result_metadata=None, **kwargs):
        """
        :param dict result_metadata: A dictionary of metadata attributes to
            assign to the result cube returned by the :meth:`run` method. The
            following attributes are set by default but can be overridden, if
            desired, using the current argument:

            * standard_name = 'toa_net_downward_radiative_flux'
            * long_name = 'Top of Atmosphere Radiation Balance'
            * var_name = 'toa_net_downward_radiative_flux'

        .. comment: ignore - sphinx workaround
        """
        super(ToaRadiationBalance, self).__init__(**kwargs)

        # Assign default metadata values to set on the result cube.
        self.result_metadata = {
            'standard_name': 'toa_net_downward_radiative_flux',
            'long_name': 'Top of Atmosphere Radiation Balance',
            'var_name': 'toa_net_downward_radiative_flux',
        }
        if result_metadata: self.result_metadata.update(result_metadata)

        # Assign STASH codes used to select required radiation fields.
        self.sw_in_std_name = 'toa_incoming_shortwave_flux'
        self.sw_in_stash_code = 'm01s01i207'
        self.sw_out_std_name = 'toa_outgoing_shortwave_flux'
        self.sw_out_stash_code = 'm01s01i208'
        self.lw_out_std_name = 'toa_outgoing_longwave_flux'
        self.lw_out_stash_code = 'm01s03i332'

    def run(self, cubes, **kwargs):
        """
        Run the processor.

        :param iris.cube.CubeList cubes: An Iris cubelist containing the three
            required diagnostics (and ideally **only** those diagnostics). They
            should be identifiable either by their CF standard name (the preferred
            option) or by their STASH attribute. All three cubes must have the
            same shape.
        :returns: A cubelist containing a cube of computed TOA radiation balance
            data. The cube is identified by the CF standard name
            'toa_net_downward_radiative_flux'.
        :raises DataProcessingError: Raised if the required diagnostic data
            could not be found in the input cubelist, or if an error occurred
            during calculation of the radiation balance diagnostic.
        """
        self.logger.info("Calculating TOA Radiation Balance diagnostic...")

        # Extract cube of toa_incoming_shortwave_flux (m01s01i207).
        sw_in = self._extract_diagnostic(cubes, self.sw_in_std_name,
            self.sw_in_stash_code)

        # Extract cube of toa_outgoing_shortwave_flux (m01s01i208).
        sw_out = self._extract_diagnostic(cubes, self.sw_out_std_name,
            self.sw_out_stash_code)

        # Extract cube of toa_outgoing_longwave_flux (m01s03i332).
        lw_out = self._extract_diagnostic(cubes, self.lw_out_std_name,
            self.lw_out_stash_code)

        # Remove any coordinates that will disrupt the ensuing cube arithmetic.
        self._remove_unwanted_coords([sw_in, sw_out, lw_out])

        try:
            # Calculate the TOA radiation balance.
            rad_balance = sw_in - sw_out - lw_out
        except Exception as exc:
            msg = "Error trying to generate TOA radiation balance cube from input cubes."
            self.logger.error(msg)
            self.logger.error(str(exc))
            raise DataProcessingError(msg)

        # Set result cube metadata.
        for k, v in self.result_metadata.items():
            try:
                setattr(rad_balance, k, v)
            except:
                self.logger.warning("Unable to set cube attribute '%s' to '%s'.", k, v)

        # Set the cube's history attribute.
        history = 'Generated TOA radiation balance diagnostic.'
        set_history_attribute(rad_balance, history, replace=True)

        return iris.cube.CubeList([rad_balance])

    def _extract_diagnostic(self, cubes, std_name, stash_code):
        """
        Extract from cubelist the cube corresponding to the specified CF standard
        name or, if that is not found, STASH code.
        """
        cbs = cubes.extract(std_name)
        if not cbs:
            cbs = cubes.extract(iris.AttributeConstraint(STASH=stash_code))

        if len(cbs) == 1:
            return cbs[0]
        else:
            msg = "Unable to extract diagnostic '{0}' (STASH={1}) from input cubelist."
            msg = msg.format(std_name, stash_code)
            self.logger.error(msg)
            raise DataProcessingError(msg)

    def _remove_unwanted_coords(self, cubes):
        """
        Remove from the passed-in cubes any coordinates which are known to
        disrupt the calculation of the target diagnostic.
        """
        unwanted_coords = ['forecast_period', 'forecast_reference_time']

        for cube in cubes:
            cube_coords = [c.name() for c in cube.coords()]
            for unwanted in unwanted_coords:
                if unwanted in cube_coords:
                    cube.remove_coord(unwanted)
