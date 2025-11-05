# (C) British Crown Copyright 2016-2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Implementation of the TransientEddyKineticEnergy processor class, which provides
the ability to calculate the transient eddy kinetic energy diagnostic from
monthly-mean wind speed data. Refer to the :class:`TransientEddyKineticEnergy`
class documentation for further details.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import iris
from afterburner.processors import AbstractProcessor
from afterburner.utils.cubeutils import set_history_attribute

# TODO: At some point this class should be re-implemented as a generic 'derived
# diagnostic' class based on an arithmetic combination of STASH diagnostics.
class TransientEddyKineticEnergy(AbstractProcessor):
    """
    Calculates the transient eddy kinetic energy diagnostic from monthly-mean
    fields of global u-wind and v-wind, plus their squared sums, u**2 and v**2,
    on a given vertical level. No zonal meaning is applied.
    """

    def __init__(self, result_metadata=None, **kwargs):
        """
        :param dict result_metadata: A dictionary of metadata attributes to
            assign to the result cube returned by the :meth:`run` method. The
            following attributes are set by default but can be overridden, if
            desired, using the current argument:

            * long_name = 'Transient Eddy Kinetic Energy'
            * var_name = 'teke'
            * units = 'm2 s-2'

        .. comment: ignore - sphinx workaround
        """
        super(TransientEddyKineticEnergy, self).__init__(**kwargs)

        # Assign default metadata values to set on the result cube.
        self.result_metadata = {
            'standard_name': None,
            'long_name': 'Transient Eddy Kinetic Energy',
            'var_name': 'teke',
            'units': 'm2 s-2',
        }
        if result_metadata: self.result_metadata.update(result_metadata)

        # Assign STASH codes used to select required wind speed fields.
        self.uwind_stashcode = 'm01s30i201'
        self.vwind_stashcode = 'm01s30i202'
        self.u2wind_stashcode = 'm01s30i211'
        self.v2wind_stashcode = 'm01s30i222'

    def run(self, cubes, **kwargs):
        """
        Run the processor.

        :param iris.cube.CubeList cubes: Cubelist containing cubes representing
            the following monthly-mean global wind speed fields on a *single*
            vertical level:

            * U (STASH code 'm01s30i201')
            * V (STASH code 'm01s30i202')
            * U**2 (STASH code 'm01s30i211')
            * V**2 (STASH code 'm01s30i222')

            Any other cubes present are silently ignored.
        :returns: A cubelist containing a cube of transient eddy kinetic energy.
        """
        self.logger.info("Calculating TEKE diagnostic...")

        # Obtain handles to the 4 wind speed fields needed to compute the TEKE
        # diagnostic.
        try:
            uw = cubes.extract(iris.AttributeConstraint(STASH=self.uwind_stashcode))[0]
            vw = cubes.extract(iris.AttributeConstraint(STASH=self.vwind_stashcode))[0]
            u2 = cubes.extract(iris.AttributeConstraint(STASH=self.u2wind_stashcode))[0]
            v2 = cubes.extract(iris.AttributeConstraint(STASH=self.v2wind_stashcode))[0]
        except:
            self.logger.error("Error trying to extract wind speed data from cubelist:\n%s",
                str(cubes))
            raise

        # Compute TEKE diagnostic and set cube metadata properties.
        teke = (u2 + v2 - uw**2 - vw**2) * 0.5
        for k, v in self.result_metadata.items():
            try:
                setattr(teke, k, v)
            except:
                self.logger.warning("Unable to set cube attribute '%s' to '%s'.", k, v)

        # Set CF history attribute.
        history = ("Generated transient eddy kinetic energy diagnostic data\n"
            "from monthly-mean global u-wind and v-wind data.")
        set_history_attribute(teke, history)

        return iris.cube.CubeList([teke])
