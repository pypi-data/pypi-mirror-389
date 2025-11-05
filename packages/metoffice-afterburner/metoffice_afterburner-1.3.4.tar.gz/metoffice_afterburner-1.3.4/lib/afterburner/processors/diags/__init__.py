# (C) British Crown Copyright 2018-2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
This is the afterburner.processors.diags package, a logical container for
diagnostic-type processors.
"""
from __future__ import absolute_import

from .atmos.jet_speed import JetSpeed
from .atmos.nao_index import NaoIndex
from .atmos.poleward_heat_transport import PolewardHeatTransport
from .atmos.streamfunc_velpot import StreamFuncVelPot, StreamFunction, VelocityPotential
from .atmos.teke import TransientEddyKineticEnergy
from .atmos.toa_radiation_balance import ToaRadiationBalance

from .ocean.net_heat_flux import NetHeatFluxIntoOcean

from .stats.diff_of_time_means import DiffOfTimeMeans, DiurnalTemperatureRange
from .stats.histogram import HistogramMaker
