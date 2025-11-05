# (C) British Crown Copyright 2016-2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Implementation of the JetSpeed processor class, which provides the functionality
to calculate jet speed and latitude from daily-mean wind speed. Refer to the
:class:`JetSpeed` class documentation for further details.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import iris
import iris.analysis
import iris.coords
import iris.exceptions

import cf_units
import numpy as np

from afterburner.processors import AbstractProcessor
from afterburner.utils.cubeutils import set_history_attribute


class JetSpeed(AbstractProcessor):
    """
    Calculates jet speed and jet latitude diagnostics from daily-mean u-wind
    speed data using the method of T. Woollings, C. Czuchnicki & C. Franzke (2014)
    [http://dx.doi.org/10.1002/qj.2197]

    The jet diagnostics are calculated for a defined geographical region, which
    by default is the North Atlantic sector. A different region can be defined
    via the :attr:`sector` keyword argument.

    By default, when the processor is executed the computed jet speed values
    are returned as an Iris cube on which jet latitude values are attached as
    an auxiliary coordinate. The :attr:`twocubes` option may be used to request
    that these data arrays be returned as two separate cubes.
    """

    #: Default geographical region over which to compute jet diagnostics.
    #: Coordinates are defined in the order: min-lon, max-lon, min-lat, max-lat
    STANDARD_SECTOR = [-60, 0, 15, 75]

    def __init__(self, lp_cutoff=0.1, lp_window=61, sector=None, twocubes=False,
            result_metadata=None, **kwargs):
        """
        :param float lp_cutoff: Low-pass filter cut-off value in inverse-timesteps
            (i.e. 1/days).
        :param int lp_window: Low-pass filter window length in timesteps (days).
        :param list/tuple sector: Specifies the geographical region over which
            to compute jet diagnostics. Coordinates should be defined in decimal
            degrees and in the order: [min-lon, max-lon, min-lat, max-lat].
        :param bool twocubes: If set to false (the default) then a single cube
            of jet speed data is returned, with corresponding jet latitude
            values encoded as an auxiliary coordinate on the cube. If :attr:`twocubes`
            is set true then the jet speed and jet latitude arrays are returned
            as two discrete cubes.
        :param dict result_metadata: A dictionary of metadata attributes to
            assign to the jet speed cube returned by the :meth:`run` method. The
            following attributes are set by default (but can be overridden if
            desired):

            * long_name = 'Jet Strength'
            * var_name = 'jet_strength'
        """
        super(JetSpeed, self).__init__(**kwargs)
        self.lp_cutoff = lp_cutoff
        self.lp_window = lp_window
        self.sector = sector
        self.twocubes = twocubes

        # Assign default metadata values to set on the result cube.
        self.result_metadata = {
            'standard_name': None,
            'long_name': 'Jet Strength',
            'var_name': 'jet_strength',
        }
        if result_metadata: self.result_metadata.update(result_metadata)

    def run(self, cubes, **kwargs):
        """
        Run the processor.

        :param iris.cube.CubeList cubes: A cubelist containing a single cube of
            daily-mean global u-wind speed data for which jet speed and latitude
            values are to be calculated. (For historical reasons a single cube
            is also an acceptable argument value.)
        :returns: A cubelist containing a cube of jet speed data and, if the
            :attr:`twocubes` option is enabled, a cube of jet latitude
            data.
        :raises ValueError: Raised if the length of the time axis in the input
            field is less than the low-pass filter window length.
        """
        self.logger.info("Calculating Jet Speed diagnostic...")

        if isinstance(cubes, iris.cube.Cube):
            uwind = cubes
        else:
            uwind = cubes[0]

        time_coord = uwind.coord('time')
        if len(time_coord.points) < self.lp_window:
            raise ValueError("Length of time axis ({0}) is less than the low-pass"
                " filter window length ({1})".format(len(time_coord.points),
                self.lp_window))

        # Calculate jet speed and latitude values.
        jet_speed, jet_lat_values = self._calc_jet_speed(uwind)

        # Set the history attribute.
        history = "Generated jet speed and jet latitude diagnostic data."
        set_history_attribute(jet_speed, history)

        if self.twocubes:
            self.logger.info("Making cube of jet latitude...")
            # Make the jet_latitude cube from the jet cube. This method ensures
            # that all coords (inc scalars) and attributes are copied across.
            jet_latitude = jet_speed.copy()
            jet_latitude.standard_name = None
            jet_latitude.var_name = 'jet_latitude'
            jet_latitude.long_name = 'Jet Latitude'
            jet_latitude.units = cf_units.Unit('degrees_north')
            jet_latitude.data = jet_lat_values
            cubelist = iris.cube.CubeList([jet_speed, jet_latitude])
        else:
            # Add the jet latitude data manually as an Iris aux coordinate.
            self.logger.info("Making latitude aux coord in jet speed cube...")
            jet_lat_coord = iris.coords.AuxCoord(jet_lat_values,
                standard_name='latitude', var_name='latitude',
                units=cf_units.Unit('degrees_north'))
            jet_speed.remove_coord('latitude')
            jet_speed.add_aux_coord(jet_lat_coord, data_dims=0)
            cubelist = iris.cube.CubeList([jet_speed])

        return cubelist

    def _calc_jet_speed(self, uwind):
        """Calculate jet speed and latitude using the Woollings method."""

        # Extract the wind data for the required geographical region.
        region = self.sector or self.STANDARD_SECTOR
        self.logger.info("Extracting data for region %s...", str(region))
        usector = uwind.intersection(longitude=region[0:2],
            latitude=region[2:4])

        # Zonally-average the wind data in that sector.
        self.logger.info("Calculating zonal average...")
        uzonavg = usector.collapsed('longitude', iris.analysis.MEAN)
        # Should be a cube with time and longitude dimensions.

        # Low-pass filter the field to remove the features associated with
        # individual synoptic systems.
        self.logger.info("Applying low-pass filter...")
        uzonavg_lpf = _lanczos_filter(uzonavg, self.lp_window, self.lp_cutoff)

        # Extract the jet speed as the westerly wind speed in this profile,
        # and the jet latitude as the latitude of that maximum.
        self.logger.info("Calculating meridional maximum of zonal mean...")
        jet_speed = uzonavg_lpf.collapsed('latitude', iris.analysis.MAX)

        # Set result cube metadata.
        for k, v in self.result_metadata.items():
            try:
                setattr(jet_speed, k, v)
            except iris.exceptions.IrisError:
                self.logger.warning("Unable to set cube attribute '%s' to '%s'.", k, v)

        # Find the array indices of the maximum jet speed and from those obtain
        # the corresponding latitude values.
        jet_lat_indices = np.argmax(uzonavg_lpf.data, axis=1)
        jet_lat_values = uzonavg_lpf.coord('latitude').points[jet_lat_indices]

        return jet_speed, jet_lat_values


def _lanczos_filter(field, window, cutoff):
    """
    Based on http://scitools.org.uk/iris/docs/latest/examples/General/SOI_filtering.html

    Duchon, 1979, J. Appl. Meteor. 18, 1016-1022.
    http://journals.ametsoc.org/doi/abs/10.1175/1520-0450%281979%29018%3C1016:LFIOAT%3E2.0.CO;2

    :param iris.cube.Cube field: An iris cube containing the field to filter.
    :param int window: The window length (in timesteps) of the low-pass filter,
        and is typically longer than 1/cutoff.
    :param float cutoff: The low-pass filter cutoff value (in inverse-timesteps).
        Defines the length of the low-frequencies that we want to retain.
    """

    weights = _lanczos_weights(window, cutoff)
    # This might need jiggling so it has the same shape as the field?

    # I think we want ia.SUM rather than ia.MEAN because the window is normalised... ?
    field_filtered = field.rolling_window('time', iris.analysis.SUM,
        len(weights), weights=weights)

    return field_filtered


def _lanczos_weights(window, cutoff):
    """
    Get the weights defining the window for the Lanczos filter.
    http://scitools.org.uk/iris/docs/latest/examples/General/SOI_filtering.html

    :param int window: The window length (in timesteps) of the low-pass filter,
        and is typically longer than 1/cutoff.
    :param float cutoff: The low-pass filter cutoff value (in inverse-timesteps).
        Defines the length of the low-frequencies that we want to retain.
    """

    order = (window - 1) // 2 + 1
    nwts = 2 * order + 1
    wts = np.zeros([nwts])

    n = nwts // 2
    wts[n] = 2 * cutoff

    k = np.arange(1.0, n)

    x = k / n
    sigma = np.sinc(x)   # yields np.sin(np.pi*x) / (np.pi*x)

    firstfactor = np.sin(2.0*np.pi*cutoff*k) / (np.pi*k)

    wts[(n-1):0:-1] = firstfactor * sigma
    wts[(n+1):-1] = firstfactor * sigma

    return wts[1:-1]
