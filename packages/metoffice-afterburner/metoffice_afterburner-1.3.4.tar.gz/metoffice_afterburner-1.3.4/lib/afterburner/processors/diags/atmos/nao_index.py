# (C) British Crown Copyright 2018-2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Implementation of the ``NaoIndex`` diagnostic processor class, which encapsulates
a method for calculating the North Atlantic Oscillation Index ('NAO Index')
from mean sea level pressure (MSLP) data. Refer to the :class:`NaoIndex` class
documentation below for further details.

The :func:`calc_nao_index` function also included here is a convenience function
for calculating NAO Index values given a single cube of MSLP data. The
:class:`NaoIndex` class itself makes use of this function.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import numpy as np
import iris
from iris.exceptions import CoordinateNotFoundError
from iris.analysis.trajectory import interpolate

from afterburner.exceptions import DataProcessingError
from afterburner.processors import AbstractProcessor
from afterburner.utils.cubeutils import set_history_attribute, is_scalar_coord


class NaoIndex(AbstractProcessor):
    """
    Calculates the NAO Index from mean sea level pressure (MSLP) data passed in
    via an Iris cube. The input cube will typically be dimensioned (time, latitude,
    longitude) though cubes of higher rank may be specified so long as the last
    two dimensions are latitude and longitude.

    By default the sea level pressure data is identified by STASH code 'm01s16i222'.
    This may be overridden by specifying the ``mslp_stashcode`` keyword argument
    during object initialisation. If a cube of MSLP data cannot be found by STASH
    code, then a search is made for a cube having the CF standard name
    'air_pressure_at_sea_level'.

    The NAO Index is calculated as the air pressure difference between a location
    in the Azores region and a location in the Iceland region, i.e.

       nao_index = azores_mslp - iceland_mslp

    By default the Azores location is taken to be the station at Ponta Delgada,
    which lies at 37.7N, 25.7W. Likewise, the default Icelandic location is the
    station at Stykkisholmur, which lies at 65.0N, 22.8W.

    Either, or both, locations can be changed via the ``azores_station`` and/or
    ``iceland_station`` keyword arguments (see below).

    Finally, the ``interp_method`` keyword argument may be used to specify the
    preferred interpolation method for deriving the MSLP value at both stations.
    The default is to use nearest-neighbour interpolation.
    """

    #: Coordinates of the default Azores station (Ponta Delgada).
    AZORES_STATION_COORDS = (37.7, -25.7)
    #: Coordinates of the default Icelandic station (Stykkisholmur).
    ICELAND_STATION_COORDS = (65.0, -22.8)


    def __init__(self, result_metadata=None, **kwargs):
        """
        :param dict result_metadata: A dictionary of metadata attributes to
            assign to the result cube returned by the :meth:`run` method. The
            following attributes are set by default but can be overridden, if
            desired, using the current argument:

            * long_name = 'Difference in MSLP'
            * var_name = 'nao_index'

        Extra Keyword Arguments (`**kwargs`):

        :param str mslp_stashcode: The STASH code used to identify the cube
            containing mean sea level pressure data. If undefined then a default
            value of 'm01s16i222' is used.
        :param tuple azores_station: If specified, this keyword argument should
            define a (latitude, longitude) tuple representing the coordinates of
            the Azores station.
        :param tuple iceland_station: If specified, this keyword argument should
            define a (latitude, longitude) tuple representing the coordinates of
            the Icelandic station.
        :param str interp_method: This argument may be used to specify the
            interpolation method that will be used to derive the MSLP values at
            the Azores and Icelandic reference locations. Recognised interpolation
            methods include 'nearest' (the default) and 'linear'.
        """
        super(NaoIndex, self).__init__(**kwargs)

        # Assign default metadata values to set on the result cube.
        self.result_metadata = {
            'standard_name': None,
            'long_name': 'Difference in MSLP',
            'var_name': 'nao_index',
        }
        if result_metadata: self.result_metadata.update(result_metadata)

        # Define STASH code used to select required MSLP field.
        self.mslp_stashcode = kwargs.get('mslp_stashcode', 'm01s16i222')

        # Define the lat/long coordinates of the Azores and Iceland stations.
        # The default locations are as follows:
        # - Ponta Delgada, Azores (37.7N, 25.7W)
        # - Stykkisholmur, Iceland (65.0N, 22.8W)
        self.azores_station_loc = np.array(kwargs.get('azores_station',
            self.AZORES_STATION_COORDS), dtype=float)
        self.iceland_station_loc = np.array(kwargs.get('iceland_station',
            self.ICELAND_STATION_COORDS), dtype=float)

        # Define the default interpolation method.
        self.interp_method = kwargs.get('interp_method', 'nearest')

    def run(self, cubes, **kwargs):
        """
        Runs the processor instance, which causes the following steps to be
        executed:

        1. Extract the cube of MSLP data from the passed-in cubelist.
        2. Calculate the NAO Index value for each horizontal slice in the MSLP cube.
        3. Store the resulting NAO data in a new cube and attach appropriate metadata.
        4. Return the cube of NAO data within a length-1 cubelist.

        :param iris.cube.CubeList cubes: Cubelist containing, as a minimum, a
            cube of mean sea level pressure (default STASH code: 'm01s16i222').
            Any other cubes present are silently ignored.
        :returns: A cubelist containing a single cube of NAO Index data.
        """
        self.logger.info("Calculating NAO Index diagnostic...")

        # Load a cube of MSLP data from the input cubelist.
        # First check for the specified MSLP STASH code.
        mslp = cubes.extract(iris.AttributeConstraint(STASH=self.mslp_stashcode))
        if not mslp:
            # If STASH code not found, try extracting by standard name.
            mslp = cubes.extract('air_pressure_at_sea_level')
            if not mslp:
                msg = "Error trying to extract MSLP data from cubelist:\n" + str(cubes)
                raise DataProcessingError(msg)
        mslp = mslp[0]

        # Check that the cube of MSLP data is valid.
        if not _is_valid_mslp_cube(mslp):
            raise DataProcessingError("The last two dimensions of the cube of\n"
                "MSLP data must be latitude and longitude.")

        # Create a cube of NAO Index data.
        nao_cube = calc_nao_index(mslp, self.azores_station_loc,
            self.iceland_station_loc, self.interp_method)

        # Set cube metadata properties.
        for k, v in self.result_metadata.items():
            try:
                setattr(nao_cube, k, v)
            except:
                self.logger.warning("Unable to set cube attribute '%s' to '%s'.", k, v)

        # Set CF history attribute.
        history = ("Generated NAO Index variable ({0}) from mean sea level "
            "pressure data.").format(nao_cube.var_name)
        set_history_attribute(nao_cube, history)

        return iris.cube.CubeList([nao_cube])


def calc_nao_index(mslp_cube, azores_station, iceland_station, interp_method):
    """
    Calculate the NAO Index for all horizontal latitude-longitude slices of the
    specified cube of gridded MSLP data, which should be of rank 2 or higher,
    and have latitude and longitude as the fastest-varying dimensions.

    :param iris.cube.Cube mslp_cube: A cube of MSLP data discretised on a regular
        latitude-longitude grid.
    :param tuple azores_station: A (latitude, longitude) tuple representing the
        coordinates of the Azores station.
    :param tuple iceland_station: A (latitude, longitude) tuple representing the
        coordinates of the Icelandic station.
    :param string interp_method: Specifies the interpolation method that will be
        used to derive the MSLP values at the Azores and Icelandic reference
        locations. Recognised interpolation methods include 'nearest' (the default)
        and 'linear'.
    :returns: A cube of NAO Index data having a rank two less than that of the
        input cube, i.e. with the latitude and longitude dimensions removed.
        The units of the cube are the same as for the MSLP input cube.
    """
    # Initialize an empty array to hold NAO Index data.
    if mslp_cube.ndim > 2:
        nslices = np.prod(mslp_cube.shape[:-2])
    else:
        nslices = 1
    nao_data = np.ma.zeros(nslices, dtype=np.float32)

    # Define sample points to use during interpolation from grid to station.
    sample_points = [('latitude', [azores_station[0], iceland_station[0]]),
        ('longitude', [azores_station[1], iceland_station[1]])]

    # Loop over all lat-long slices of the MSLP input cube, calculating the
    # NAO index value for each slice.
    for i, subcube in enumerate(mslp_cube.slices(['latitude', 'longitude'])):
        # Determine the values of MSLP at the Azores and Iceland stations.
        stn_mslp = interpolate(subcube, sample_points, method=interp_method)
        # Compute the pressure difference between the two stations.
        nao_data[i] = stn_mslp.data[0] - stn_mslp.data[1]

    # Define scalar lat/long coordinates with global bounds (for later use).
    midlat = (azores_station[0] + iceland_station[0]) / 2.0
    latbnds = [-90.0, 90.0]
    latcrd = iris.coords.DimCoord(midlat, standard_name='latitude',
        units='degrees_north', bounds=latbnds)
    midlon = (azores_station[1] + iceland_station[1]) / 2.0
    lonbnds = [0.0, 360.0] if midlon > 0 else [-180.0, 180.0]
    loncrd = iris.coords.DimCoord(midlon, standard_name='longitude',
        units='degrees_east', bounds=lonbnds)

    # Create a cube from the NAO Index data array. If the input cube is 3D or
    # above, the NAO cube is initialised from a slice of it. For a 2D input cube,
    # the NAO cube must be created from scratch.
    if mslp_cube.ndim > 2:
        nao_data.shape = mslp_cube.shape[:-2]
        nao_cube = mslp_cube[...,0,0]
        nao_cube.data[:] = nao_data
        # Replace scalar lat/long coords with global equivalents. NB: for some
        # reason the cube.replace_coord() method throws an error if used here.
        for crd in ['latitude', 'longitude']:
            try:
                nao_cube.remove_coord(crd)
            except CoordinateNotFoundError:
                pass
        nao_cube.add_aux_coord(latcrd)
        nao_cube.add_aux_coord(loncrd)
    else:
        nao_cube = iris.cube.Cube(nao_data, units=mslp_cube.units)
        nao_cube.add_aux_coord(latcrd)
        nao_cube.add_aux_coord(loncrd)
        # Copy over any other *scalar* coordinates from MSLP cube to NAO cube.
        # This is mainly done to preserve a scalar time coordinate, if present.
        for coord in mslp_cube.coords(dim_coords=False):
            if coord.standard_name in ['latitude', 'longitude']:
                continue
            elif is_scalar_coord(mslp_cube, coord.name()):
                nao_cube.add_aux_coord(coord.copy())

    # Attach a comment describing the method for calculating the NAO Index.
    nao_cube.attributes['comment'] = ("NAO Index values calculated as air pressure "
        "difference between the following locations: Azores: {0:.3f}N, {1:.3f}E ; "
        "Iceland: {2:.3f}N, {3:.3f}E").format(azores_station[0], azores_station[1],
        iceland_station[0], iceland_station[1])

    return nao_cube


def _is_valid_mslp_cube(mslp):
    """
    Check that the cube of MSLP data contains (latitude, longitude) as the
    fastest-varying dimensions.
    """
    mslp_coords = [c.name() for c in mslp.coords(dim_coords=True)]
    return (mslp_coords[-2:] == ['latitude', 'longitude'])
