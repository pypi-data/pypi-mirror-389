Afterburner Processors
======================

This page provides a brief synopsis of, and a link to, the current Afterburner
processor classes.

Want to learn how to write your own processor classes? The :doc:`/dev_guide/processors`
chapter shows you how. 

`Data Writers`_
---------------

* :class:`NetcdfFileWriter <afterburner.processors.writers.netcdf_writer.NetcdfFileWriter>` --
  A utility processor class for writing an Iris cube or cubelist to a netCDF file

`Atmosphere Diagnostics`_
-------------------------

* :class:`JetSpeed <afterburner.processors.diags.atmos.jet_speed.JetSpeed>` --
  Calculates jet speed and jet latitude diagnostics from daily-mean u-wind speed data
* :class:`NAOIndex <afterburner.processors.diags.atmos.nao_index.NaoIndex>` --
  Calculates the North Atlantic Ocean Index diagnostic from mean sea level pressure data
* :class:`PolewardHeatTransport <afterburner.processors.diags.atmos.poleward_heat_transport.PolewardHeatTransport>` --
  Calculates a poleward heat transport diagnostic: moist static energy (default) or dry static energy
* :class:`StreamFunction <afterburner.processors.diags.atmos.streamfunc_velpot.StreamFunction>` --
  Calculates the streamfunction diagnostic from global wind speed data on a particular vertical level
* :class:`ToaRadiationBalance <afterburner.processors.diags.atmos.toa_radiation_balance.ToaRadiationBalance>` --
  Calculates the top-of-atmosphere (TOA) radiation balance diagnostic from incoming and outgoing radiative fluxes
* :class:`TransientEddyKineticEnergy <afterburner.processors.diags.atmos.teke.TransientEddyKineticEnergy>` --
  Calculates the transient eddy kinetic energy diagnostic from monthly-mean fields of global u-wind and v-wind
* :class:`VelocityPotential <afterburner.processors.diags.atmos.streamfunc_velpot.VelocityPotential>` --
  Calculates the velocity potential diagnostic from global wind speed data on a particular vertical level

`Ocean Diagnostics`_
--------------------

* :class:`NetHeatFluxIntoOcean <afterburner.processors.diags.ocean.net_heat_flux.NetHeatFluxIntoOcean>` --
  Calculates the Net Heat Flux Into Ocean diagnostic

`Statistical Diagnostics`_
--------------------------

* :class:`DiffOfTimeMeans <afterburner.processors.diags.stats.diff_of_time_means.DiffOfTimeMeans>` --
  Calculates the difference between the time-mean of two diagnostics
* :class:`DiurnalTemperatureRange <afterburner.processors.diags.stats.diff_of_time_means.DiurnalTemperatureRange>` --
  Calculates the diurnal temperature range given cubes of hourly maximum and minimum temperature data
* :class:`HistogramMaker <afterburner.processors.diags.stats.histogram.HistogramMaker>` --
  Generates scales-of-variability histogram data for one or more diagnostics

`Derived Diagnostics`_
----------------------
  
* :class:`MipDerivedDiagnostic <afterburner.processors.diags.derived.MipDerivedDiagnostic>` --
  Implements a MIP-style derived diagnostic based upon the formula syntax utilised
  within the Met Office `Climate Data Dissemination System <https://code.metoffice.gov.uk/trac/cdds>`_
  (CDDS) software package

* :class:`SimpleDerivedDiagnostic <afterburner.processors.diags.derived.SimpleDerivedDiagnostic>` --
  Implements a simple derived diagnostic, one based on a formula involving a
  combination of variable names and optional numeric constants


.. _Data Writers: apidoc/afterburner.processors.writers.html

.. _Atmosphere Diagnostics: apidoc/afterburner.processors.diags.atmos.html

.. _Ocean Diagnostics: apidoc/afterburner.processors.diags.ocean.html

.. _Statistical Diagnostics: apidoc/afterburner.processors.diags.stats.html

.. _Derived Diagnostics: apidoc/afterburner.processors.diags.derived.html
