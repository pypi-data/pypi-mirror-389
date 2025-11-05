# (C) British Crown Copyright 2016, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Implementation of the StreamFuncVelPot processor class, which provides the ability
to calculate streamfunction and velocity potential diagnostics from global wind
speed data. Refer to the :class:`StreamFuncVelPot` class documentation for further
details.

These two diagnostics may be obtained separately, if required, using the
:class:`StreamFunction` and :class:`VelocityPotential` classes. These are merely
lightweight wrappers around the :class:`StreamFuncVelPot` class.

.. note:: This module has a dependency on the `windspharm <https://github.com/ajdawson/windspharm>`_
   and `pyspharm <https://github.com/jswhit/pyspharm>`_ packages. Unless they are
   already available, these packages (plus their own package dependencies) should
   be installed into your Python environment prior to using the code in this module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import iris
try:
    import windspharm
    from windspharm.iris import VectorWind
except:
    pass

from afterburner.processors import AbstractProcessor
from afterburner.utils.cubeutils import set_history_attribute


class StreamFuncVelPot(AbstractProcessor):
    """
    Calculates streamfunction and velocity potential diagnostics from global wind
    speed data on a particular vertical level.
    """

    def __init__(self, earth_radius=6371229.0, truncation=None, **kwargs):
        """
        :param float earth_radius: Radius of the Earth, in metres, to pass to
            the windspharm package (for versions >= 1.5.0 only).
        :param int truncation: Truncation limit (triangular truncation) to pass
            to the windspharm functions used to calculate the streamfunction and
            velocity potential diagnostics.
        """
        super(StreamFuncVelPot, self).__init__(**kwargs)
        self.rsphere = earth_radius
        self.truncation = truncation

        # Assign the STASH codes used to select the required wind speed fields.
        self.uwind_stashcode = 'm01s30i201'
        self.vwind_stashcode = 'm01s30i202'

    def run(self, cubes, **kwargs):
        """
        Run the processor.

        :param iris.cube.CubeList cubes: Cubelist containing cubes representing
            the following global wind speed fields on a *single* vertical level:

            * U (STASH code 'm01s30i201')
            * V (STASH code 'm01s30i202')

            Any other cubes present are silently ignored.
        :returns: A cubelist containing cubes of streamfunction and velocity
            potential.
        """
        self.logger.info("Calculating streamfunction diagnostic...")

        # Extract u-wind and v-wind fields from the input cubelist.
        try:
            uwind = cubes.extract(iris.AttributeConstraint(STASH=self.uwind_stashcode))[0]
            vwind = cubes.extract(iris.AttributeConstraint(STASH=self.vwind_stashcode))[0]
        except:
            self.logger.error("Error trying to extract wind speed data from cubelist:\n%s",
                str(cubes))
            raise

        # Calculate streamfunction and velocity potential using windspharm package.
        try:
            kwargs = {}
            if _vector_wind_has_radius_support(): kwargs['rsphere'] = self.rsphere
            vecwind = VectorWind(uwind, vwind, **kwargs)
            strmfn, velpot = vecwind.sfvp(truncation=self.truncation)
        except:
            self.logger.error("Error computing vector wind fields.")
            raise

        # Set some useful cube metadata properties not set by the windspharm package.
        strmfn.var_name = 'streamfunction'
        strmfn.units = 'm2 s-1'
        velpot.var_name = 'velocity_potential'
        velpot.units = 'm2 s-1'

        # Set the CF history attribute.
        set_history_attribute(strmfn, "Generated streamfunction diagnostic from "
            "global u-wind and v-wind data.")
        set_history_attribute(velpot, "Generated velocity potential diagnostic "
            "from global u-wind and v-wind data.")

        return iris.cube.CubeList([strmfn, velpot])


class StreamFunction(StreamFuncVelPot):
    """
    Calculates the streamfunction diagnostic from global wind speed data on a
    particular vertical level.
    """

    def __init__(self, earth_radius=6371229.0, truncation=None, **kwargs):
        """
        See :class:`StreamFuncVelPot` for argument descriptions.
        """
        super(StreamFunction, self).__init__(earth_radius=earth_radius,
            truncation=truncation, **kwargs)

    def run(self, cubes, **kwargs):
        """
        Run the processor. See :class:`StreamFuncVelPot` for argument descriptions.

        :returns: A cubelist containing a single cube of streamfunction data.
        """
        strmfn, _velpot = super(StreamFunction, self).run(cubes, **kwargs)
        return iris.cube.CubeList([strmfn])


class VelocityPotential(StreamFuncVelPot):
    """
    Calculates the velocity potential diagnostic from global wind speed data on
    a particular vertical level.
    """

    def __init__(self, earth_radius=6371229.0, truncation=None, **kwargs):
        """
        See :class:`StreamFuncVelPot` for argument descriptions.
        """
        super(VelocityPotential, self).__init__(earth_radius=earth_radius,
            truncation=truncation, **kwargs)

    def run(self, cubes, **kwargs):
        """
        Run the processor. See :class:`StreamFuncVelPot` for argument descriptions.

        :returns: A cubelist containing a single cube of velocity potential data.
        """
        _strmfn, velpot = super(VelocityPotential, self).run(cubes, **kwargs)
        return iris.cube.CubeList([velpot])


def _vector_wind_has_radius_support():
    """
    Test to see if the windspharm.VectorWind class supports the rsphere argument,
    which was added at windspharm v1.5.0.
    """
    try:
        from pkg_resources import parse_version
        return parse_version(windspharm.__version__) >= parse_version('1.5')
    except:
        return False
