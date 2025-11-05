Tutorial #11: Generating Derived Diagnostics
============================================

This tutorial describes the functionality within Afterburner for generating
so-called *custom* or *derived diagnostics*. Such diagnostics are defined via
mathematical formulae whose terms comprise combinations of named variables (i.e.
geophysical fields) plus numerical constants.

.. contents:: Table of Contents
   :local:

Introduction
------------

By way of context, the :mod:`afterburner.processors.diags` package contains a
number of subpackages which act as containers (via their enclosed modules) for
Python classes which can be used to generate *pre-defined*, bespoke diagnostics
from one or more Iris cubes (each cube representing one of the required input
variables). One such example is the :class:`JetSpeed <afterburner.processors.diags.atmos.jet_speed.JetSpeed>`
class which, as the name suggests, may be used to generate jet speed diagnostics
from u-wind speed data.

Currently these diagnostic processor classes are grouped -- in a somewhat arbitrary
manner in some cases -- into atmosphere diagnostics, ocean diagnostics, and
general statistical diagnostics (in future, additional subpackages may be created
to act as containers for classes pertaining to other earth system domains -- land,
sea-ice, and so on).

The :mod:`afterburner.processors.diags.derived` module, by way of contrast, contains
general-purpose classes which can be used to generate arbitrary, formula-based
derived diagnostics -- the subject of this tutorial.

Two such classes exist at present:

* :class:`SimpleDerivedDiagnostic <afterburner.processors.diags.derived.SimpleDerivedDiagnostic>`
  -- used to generate derived diagnostics based on a simple formula involving some
  combination of variable names (e.g. UM STASH codes or CF standard names) and
  optional numeric constants.

* :class:`MipDerivedDiagnostic <afterburner.processors.diags.derived.MipDerivedDiagnostic>`
  -- used to generate derived diagnostics based on the richer formula syntax
  employed by the Met Office’s `CDDS`_ software package.

.. note:: In the ensuing discussion the terms 'diagnostic' and 'variable' are used
   more or less interchangeably to signify a geophysical field of some sort and,
   in the current context, ones that typically are produced by climate or weather
   models. In popular usage, 'diagnostic' might be thought of as the established
   scientific concept of the field (e.g. 'air temperature'), whereas 'variable'
   represents a multi-dimensional, spatio-temporal representation of the field
   serialised in some or other digital format (e.g. as a netCDF variable).

Example Usage Scenarios
-----------------------

There are a number of situations where the derived diagnostic classes can be of
utility.

* They are currently used, for example, within a number of Afterburner apps,
  including the :doc:`/rose_apps/model_monitor2/guide` app. Refer to the respective
  app documentation for further information on working with derived diagnostics.

* You could utilise the derived diagnostic functionality directly within your
  interactive Python sessions; for example, to create new diagnostics 'on-the-fly'
  from existing diagnostics represented by Iris cubes. The code fragments shown
  later in this tutorial essentially demonstrate this usage.

* Likewise, you can place equivalent code within your Python apps, scripts and
  utilities. Naturally this will make it simpler, and more efficient, to run the
  code repeatedly against different inputs. Plus, you can share the code with your
  colleagues.

Generating Simple Derived Diagnostics
-------------------------------------

As mentioned above, these kinds of diagnostics can be defined as a simple formula
involving one or more existing diagnostics (variables), and zero or more numerical
constants.

A trivial example of a simple derived diagnostic would be the one that generates
air temperature in degrees Celsius from air temperature in degrees Fahrenheit.
Assuming we have an input field named 'air_temperature', then the formula string
could be expressed as follows::

    formula = "(air_temperature - 32.0) * (5.0 / 9.0)"

In practice one would usually replace the term "(5.0 / 9.0)" with an appropriate
constant.

Here's how one might use this formula within an interactive Python session to
generate the desired target diagnostic from data loaded from a netCDF file:

>>> import iris
>>> from afterburner.processors.diag.derived import SimpleDerivedDiagnostic
>>> # assume input field is identified by the CF standard name 'air_temperature'
>>> cubes = iris.load('myfile.nc', 'air_temperature')
>>> print(cubes)
0: air_temperature / (degF)    (time: 12; latitude: 145; longitude: 192)
>>> # define formula and create an instance of the SimpleDerivedDiagnostic class
>>> formula = "(air_temperature - 32.0) * (5.0 / 9.0)"
>>> degc_diag = SimpleDerivedDiagnostic(formula)
>>> # invoke the run() method to generate the derived diagnostic
>>> result_cubes = degc_diag.run(cubes)
>>> print(result_cubes)
0: air_temperature / (degC)    (time: 12; latitude: 145; longitude: 192)

Note that the ``run()`` method expects a cubelist as the first argument and, by
default, it returns a cubelist. Depending upon the nature of the derived diagnostic
the cubelists might only contain a single cube each; that's fine.

If you know for sure that the result will always be a single cube then you can
use the ``return_single_cube`` argument to return a cube instead of a cubelist,
as shown below:

>>> result_cube = degc_diag.run(cubes, return_single_cube=True)

The above example of generating a derived diagnostic is clearly quite trivial: one
would usually just employ standard cube arithmetic to create the desired result
cube. However, it serves to illustrate the basic coding pattern that is needed to
create and then use an instance of the ``SimpleDerivedDiagnostic`` class.

By way of a slightly more advanced -- and realistic! -- example, the code fragment
below illustrates how one might generate the top-of-atmosphere (TOA) radiation
balance diagnostic assuming that the three UM STASH diagnostics '1,207', '1,208'
and '3,332' will be used as input fields:

>>> # assume imports as per previous example
>>> cubes = iris.load('myfile.pp')
>>> formula = "m01s01i207 - m01s01i208 - m01s03i332"
>>> metadata = {'standard_name': 'toa_net_downward_radiative_flux'}
>>> toa_rad_bal = SimpleDerivedDiagnostic(formula, result_metadata=metadata)
>>> result_cubes = toa_rad_bal.run(cubes)
>>> print(result_cubes)
0: toa_net_downward_radiative_flux / (W m-2)    (time: 12; latitude: 145; longitude: 192)

There are a couple of new things to note in this example. Firstly, the list of
input cubes was not reduced in any way (e.g. by name). By default, however, the
``SimpleDerivedDiagnostic.run()`` method will try to extract the variables specified
in the formula. It will raise an exception if a required cube is missing. To maximise
the chances that the correct input cubes will get selected it is good practice
to pass in only those cubes that are required to generate the derived diagnostic.

Secondly, the ``result_metadata`` keyword argument was used to define metadata
to attach to the resulting cube. In this case only the CF standard name was
defined, but any of the familiar cube identity attributes can be specified, i.e.
standard_name, long_name, var_name, and units.

Generating MIP-style Derived Diagnostics
----------------------------------------

The ``MipDerivedDiagnostic`` class provides the capability to generate MIP-style
derived diagnostics, which can be defined using the richer formula syntax employed
by the Met Office’s Climate Data Dissemination System (`CDDS`_) software package.

The MIP formula grammar is similar to that used by the ``SimpleDerivedDiagnostic``,
but includes the following refinements:

* A number of CDDS-specific constants are recognised, e.g. ICE_DENSITY and
  MOLECULAR_MASS_OF_AIR. The full list of currently supported constants is
  documented :data:`here <afterburner.processors.diags.derived.CDDS_CONSTANTS>`.

* STASH-type variables may be augmented with constraints comprising one or more
  UM PP 'header-word=value' pairs enclosed in square brackets. The currently
  supported PP header words are lbproc, lbtim, lblev, lbplev and blev.

Multiple STASH constraints are permissible and should be separated by commas,
thus: ``stashcode[word1=value1,word2=value2,...]``.

The value encoded on the right-hand side of a STASH constraint should be either
an integer or float, depending on the header word on the left-hand side.

Whitespace is prohibited within STASH constraints (but *is* recommended for visually
separating successive terms in a formula - see the examples below).

The following formula definitions illustrate a handful of semi-realistic examples.

* 6-hourly values of maximum precipitation flux, converted (somewhat dubiously!)
  into units of mm/day::

    formula = "m01s05i216[lbproc=8192,lbtim=622] * 86400.0"

* Product of the mean eastward and northward wind speed fields on the 800 hPa
  pressure level::

    formula = "m01s30i201[lbproc=128,blev=800.0] * m01s30i202[lbproc=128,blev=800.0]"

* Sum of soil moisture content fields on pseudo-levels 3 and 4::

    formula = "m01s08i223[lbplev=3] + m01s08i223[lbplev=4]"

Other than the additional grammar features summarised above, the general approach
to creating and running an instance of the ``MipDerivedDiagnostic`` class is very
similar to that previously illustrated for the ``SimpleDerivedDiagnostic`` class.

The example below shows how one could generate a diagnostic representing the sum
of the squares of the u-wind and v-wind fields on the 500 hPa pressure level:

>>> import iris
>>> from afterburner.processors.diag.derived import MipDerivedDiagnostic
>>> cubes = iris.load('myfile.pp')
>>> formula = "m01s30i201[blev=500.0] ^ 2 + m01s30i202[blev=500.0] ^ 2"
>>> metadata = {'long_name': 'U**2 + V**2', 'units': 'm2 s-2'}
>>> uvsq_diag = MipDerivedDiagnostic(formula, result_metadata=metadata)
>>> result_cubes = uvsq_diag.run(cubes)
>>> print(result_cubes)
0: U**2 + V**2 / (m2 s-2)    (level: 1, time: 12; latitude: 145; longitude: 192)

NB: In the formula assignment above, one could insert parentheses around the
exponentiation operations just so as to make clear the order of precedence,
although in this particular case the default order yields the expected result.

The next section describes a couple of convenience functions that offer an
alternative, short-hand approach to generating derived diagnostics.

Use of Convenience Functions
----------------------------

As we've seen in the previous examples, the basic coding pattern for using the
existing derived diagnostic classes looks like this:

>>> formula = "..."
>>> metadata = {...}
>>> diag = SimpleDerivedDiagnostic(formula, result_metadata=metadata)
>>> result_cubes = diag.run(cubes, ...)

If desired, this can be expressed more concisely using the ``create_simple_derived_diagnostic()``
convenience function, which can be found in the same module as the derived diagnostic
classes:

>>> from afterburner.processors.diag.derived import create_simple_derived_diagnostic
>>> result_cubes = create_simple_derived_diagnostic(formula, cubes, result_metadata=metadata)

The convenience function creates an instance of the ``SimpleDerivedDiagnostic``
class using the specified formula, then invokes the ``run()`` method, passing
over the list of input cubes together with any other keyword arguments that might
have been specified, and finally returning the result cube(s).

The ``create_mip_derived_diagnostic()`` convenience function fulfils the same role
in relation to the ``MipDerivedDiagnostic`` class.

Additional Usage Guidance
-------------------------

Formula Specification
~~~~~~~~~~~~~~~~~~~~~

Formula variables can refer to any of the following three types of diagnostic
identifier:

* UM STASH codes in so-called 'MSI' format (e.g. 'm01s00i024' for surface air
  temperature).
* CF standard names (e.g. 'air_temperature' for surface air temperature).
* netCDF variable names (e.g. 'tas' for surface air temperature).

Variables identified by STASH code are extracted from the input cubelist by
examination of each cube's ``STASH`` dictionary attribute, if present.

Variables identified by CF standard name are extracted from the input cubelist by
examination, as one might imagine, of each cube's ``standard_name`` attribute.

Variables identified by netCDF variable name are extracted from the input
cubelist by examination of each cube's ``var_name`` attribute.

At run time, the diagnostic formula is evaluated by replacing variable terms with the
corresponding input cubes, and not the cube's data payload objects (dask or numpy
arrays). The result is determined, therefore, by Iris's rules for evaluating
expressions containing cube objects. This might be different from the result
obtained from evaluating the equivalent expression using the underlying numpy arrays.

It is noted here that Iris can, at times, be somewhat unpredictable as regards
whether and how it assigns certain metadata attributes (particular names and units)
in the result cube. See the `Handling Metadata` section below.

The following basic mathematical operators are currently supported: ``+, -, *, /, ^``,
the last operator referring to exponentiation.

The use of parenthesis characters (``(...)``) to explicitly define correct operation
order is both supported and encouraged.

Data Type Promotion
~~~~~~~~~~~~~~~~~~~

The normal Python type-promotion rules apply when evaluating expressions whose
terms, be they numerical constants or cube data arrays, are associated with
objects of different types (ints, floats, doubles, etc).

Be careful, in particular, of inadvertent truncation/rounding caused by the use
of integer constants within the diagnostic formula. For example, the naive formula
``(air_temperature-32) * (5/9)`` may yield erroneous results depending on the version
of Python being used and the type of the air_temperature field's data values.

Handling Metadata
~~~~~~~~~~~~~~~~~

As we saw in some of the earlier code examples, the ``result_metadata`` keyword
argument may be used to specify common attributes to attach to the result cube
returned when a derived diagnostic is computed.

Since Iris will not normally know what values to assign to these attributes it
is invariably a good idea to assign them explicitly, either via the ``result_metadata``
argument or else by updating them directly in your own code as soon as the cube
has been returned.

The ``units`` attribute can be especially troublesome, so it is usually recommended
to set this attribute explicitly rather than rely on any in-built rules for guessing
the units based on the formula and the input variables (= cubes).

Limitations and Gotchas
~~~~~~~~~~~~~~~~~~~~~~~

The input cubes must all have the same shape (number and length of dimensions),
or else be broadcastable as such. It is also assumed that the data arrays attached
to the input cubes are type-compatible when they are evaluated together within an
expression. Currently no checks are performed to verify such compatibility.

The derived diagnostic classes possess no special logic for handling masked values
in the data arrays attached to input cubes. The normal numpy rules apply, which
essentially means that if any element(s) of the input arrays are masked then the
corresponding elements in the returned cube will also be masked.

At present there is no capability to constrain (e.g. by subsetting) the spatial
or temporal extent over which the derived diagnostic is computed. If necessary,
subsetting/extraction of particular vertical levels or time points, say, should
be applied to the input cubes before passing them to the ``run()`` method of the
derived diagnostic instance object.

Similarly there is currently no mechanism for passing and applying a land-sea
mask (or similar) to the input and/or output cube(s). Again, this must be done as
a separate pre- or post-processing step.

Wrap Up
-------

That concludes this tutorial. Further information regarding the various functions
and classes for working with derived diagnostics can be found in the Afterburner
:mod:`API documentation <afterburner.processors.diags.derived>`.

Back to the :doc:`Tutorial Index <index>`

.. _CDDS: https://code.metoffice.gov.uk/trac/cdds