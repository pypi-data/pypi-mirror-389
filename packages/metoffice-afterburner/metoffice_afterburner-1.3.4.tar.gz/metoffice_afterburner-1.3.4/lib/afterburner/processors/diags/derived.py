# (C) British Crown Copyright 2017-2023, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
This module contains classes, plus some utility functions, that provide various
implementations of so-called derived diagnostics.

**Index of Classes and Functions in this Module**

.. autosummary::
   :nosignatures:

   create_simple_derived_diagnostic
   create_mip_derived_diagnostic
   SimpleDerivedDiagnostic
   MipDerivedDiagnostic
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import string_types

import re
import logging
import pyparsing as pp
try:
    # Python <= 3.9
    from collections import Iterable
except ImportError:
    # Python > 3.9
    from collections.abc import Iterable

import cf_units
import operator
import iris
from iris.exceptions import CoordinateNotFoundError

from afterburner.exceptions import InvalidDiagnosticFormulaError
from afterburner.processors import AbstractProcessor
from afterburner.modelmeta import is_msi_stash_code
from afterburner.utils import cubeutils

MATH_OPERATORS = {
    '+': operator.add, '-': operator.sub,
    '*': operator.mul, '/': operator.truediv, '//': operator.floordiv,
    '^': operator.pow, '%': operator.mod,
}

#: Constants recognised by the CDDS package.
CDDS_CONSTANTS = {
    'DAYS_IN_YEAR': 360,                 # days
    'ICE_DENSITY': 917,                  # kg m-3
    'LATENT_HEAT_OF_FREEZING': 334000,   # J kg-1
    'MOLECULAR_MASS_OF_AIR': 28.97,      # g mol-1
    'REF_SALINITY': 4,
    'SEAWATER_DENSITY': 1026,            # kg m-3
    'SECONDS_IN_DAY': 86400,             # s
    'SNOW_DENSITY': 330,                 # kg m-3
}

logger = logging.getLogger(__name__)


def create_simple_derived_diagnostic(formula, cubes, **kwargs):
    """
    Convenience function for creating and then running an instance of the
    SimpleDerivedDiagnostic class.

    Refer to the :class:`class documentation <SimpleDerivedDiagnostic>` for
    information regarding function arguments, optional keyword arguments, and
    exceptions which might get raised.

    :returns: An Iris cubelist containing a single cube representing the derived
        diagnostic.
    """
    metadata = kwargs.pop('result_metadata', None)
    proc = SimpleDerivedDiagnostic(formula, result_metadata=metadata, **kwargs)
    result = proc.run(cubes, **kwargs)
    return result


def create_mip_derived_diagnostic(formula, cubes, **kwargs):
    """
    Convenience function for creating and then running an instance of the
    MipDerivedDiagnostic class.

    Refer to the :class:`class documentation <MipDerivedDiagnostic>` for
    information regarding function arguments, optional keyword arguments, and
    exceptions which might get raised.

    :returns: An Iris cubelist containing a single cube representing the derived
        diagnostic.
    """
    metadata = kwargs.pop('result_metadata', None)
    proc = MipDerivedDiagnostic(formula, result_metadata=metadata, **kwargs)
    result = proc.run(cubes, **kwargs)
    return result


class SimpleDerivedDiagnostic(AbstractProcessor):
    """
    Implements a so-called *simple* derived diagnostic; that is, one based on
    a formula involving some combination of variable names (e.g. UM STASH
    diagnostics) and optional numeric constants.

    The following example shows a very simple formula which could be used to
    derive the `TOA radiation balance` quantity from three UM diagnostics:

    ``m01s01i207 - m01s01i208 - m01s03i332``

    Alternatively, the same diagnostic could be expressed in terms of CF standard
    names, as follows:

    ``toa_incoming_shortwave_flux - toa_outgoing_shortwave_flux - toa_outgoing_longwave_flux``

    Variable names must be one of the following:

    * a UM STASH code in MSI format (e.g. m01s03i236)
    * a CF standard name (e.g. air_temperature)
    * a cube var_name (e.g. tas)

    A particular formula might use any combination of the aforementioned names,
    though in practice this is likely to be rare.

    The following mathematical operators are currently supported: ``+, -, *, /, ^``.

    Numeric constants may be integers or floating-point reals. In the former
    case, the normal rules of integer division apply, i.e. *truncation of results
    may occur*. In the case of real constants, data type promotion - e.g. from
    integer to float - may get applied to the data payload of the result cube.

    Executing an instance of this class (see :meth:`run` method) results in
    evaluation of the diagnostic formula by substituting the appropriate input
    cube for each named variable in the formula.

    If metadata attributes are passed in via the :attr:`result_metadata` attribute
    - and typically they should be - then these are attached to the result cube
    returned (via a length-1 cubelist) by the :meth:`run` method (NB: the result
    cube can also be obtained via the :attr:`result_cube` instance attribute).
    Naturally, additional metadata may also be attached to the cube once it has
    been created.

    Within client code, the creation and invocation of an instance of this class
    may conveniently and concisely be rolled up into a single statement, as shown
    below (assuming the relevant classes have been imported)::

        try:
            result = SimpleDerivedDiagnostic(formula).run(cubes)
        except InvalidDiagnosticFormulaError:
            pass
    """

    def __init__(self, formula, result_metadata=None, **kwargs):
        """
        :param str formula: A text string providing the formula for the derived
            diagnostic. Whitespace in the formula is not mandatory, but is
            recommended for reasons of legibility.
        :param dict result_metadata: Optional dictionary, or iris.cube.CubeMetadata
            object, which supplies the metadata to attach to the result cube.
            Typical attributes include standard_name, long_name, units, and so on.
        :raises afterburner.exceptions.InvalidDiagnosticFormulaError: Raised if
            the specified formula is invalid.
        """
        super(SimpleDerivedDiagnostic, self).__init__(**kwargs)

        #: The formula defining the derived diagnostic.
        self.formula = formula

        #: The metadata attributes, if any, to assign to the result cube.
        self.result_metadata = result_metadata

        #: The cube result produced when the diagnostic formula is evaluated.
        self.result_cube = None

        self._plain_grammar = self._eval_grammar = None
        self._construct_grammar()

        self._validate_formula()

    def run(self, cubes, result_metadata=None, **kwargs):
        """
        Run the diagnostic processor.

        :param iris.cube.CubeList cubes: A cubelist containing all of the cubes
            referenced by the specified formula. Any other cubes present in the
            cubelist are ignored. There must be a *single* cube for each variable
            named in the formula since the latter contains no information that
            would allow multiple like-named cubes to be disambiguated. See also
            the note below regarding mutually-compatible input cubes.
        :param dict result_metadata: May be used to reset the :attr:`result_metadata`
            instance attribute on a per-invocation basis.
        :returns: A cubelist containing the single cube representing the derived
            diagnostic. Returning a cubelist is intended to achieve uniformity
            with other diagnostic processors, all of which return cubelists.
            To force the return of a single cube object, set the keyword argument
            ``return_single_cube=True``.
        :raises iris.exceptions.ConstraintMismatchError: Raised if an input cube
            could not be found for a named variable in the diagnostic formula.

        .. note:: The input cubes must all have the same shape (number and length
           of dimensions), or else be broadcastable as such. It is also assumed
           that the data arrays attached to the input cubes are type-compatible.
           Currently no checks are performed to verify such compatibility.
        """
        if result_metadata:
            self.result_metadata = result_metadata

        var_dict = self._map_vars_to_cubes(cubes)

        self.result_cube = result = self.evaled_formula.eval(var_dict)

        self._assign_metadata()

        if kwargs.get('return_single_cube', False):
            return result
        else:
            return iris.cube.CubeList([result])

    @property
    def formula_terms(self):
        """The list of all terms (operands) in the formula, including constants."""
        return [t for t in _flatten(self.parsed_formula) if t not in MATH_OPERATORS]

    @property
    def formula_vars(self):
        """The list of named variable terms in the formula, excluding constants."""
        return [t for t in self.formula_terms if re.match(r'[a-zA-Z][\w]+', t)]

    def _construct_grammar(self):
        """
        Build the grammar used to define a derived diagnostic formula. In fact two
        grammars are returned: the first is a plain, non-evaluating grammar which
        can be used to query terms in the formula. The second is an eval-aware
        grammar which may be used to evaluate the formula given a dictionary of
        values (i.e. cubes) for the variables in the formula.
        """

        # Define atomic operands: integers, floats and variables.
        int_term = pp.Word(pp.nums)
        real_term = (
            pp.Combine(pp.Word(pp.nums) + pp.Optional('.' + pp.Word(pp.nums)) +
                pp.oneOf('E e') + pp.Optional(pp.oneOf('+ -')) + pp.Word(pp.nums)) |
            pp.Combine(pp.Word(pp.nums) + '.' + pp.Optional(pp.Word(pp.nums)))
        )
        var_term = pp.Word(pp.alphas, pp.alphanums+'_')

        # Define plain grammar.
        base_expr = real_term | int_term | var_term
        expn_op = pp.Literal('^')
        sign_op = pp.oneOf('+ -')
        mult_op = pp.oneOf('* /')
        plus_op = pp.oneOf('+ -')
        op_list = [
            (expn_op, 2, pp.opAssoc.RIGHT),
            (sign_op, 1, pp.opAssoc.RIGHT),
            (mult_op, 2, pp.opAssoc.LEFT),
            (plus_op, 2, pp.opAssoc.LEFT),
        ]
        self._plain_grammar = pp.infixNotation(base_expr, op_list)

        # Define evaluation-aware grammar
        base_expr = real_term | int_term | var_term
        base_expr.setParseAction(_EvalOperand)
        op_list = [
            (expn_op, 2, pp.opAssoc.RIGHT, _MulDivOperator),
            (sign_op, 1, pp.opAssoc.RIGHT, _SignOperator),
            (mult_op, 2, pp.opAssoc.LEFT, _MulDivOperator),
            (plus_op, 2, pp.opAssoc.LEFT, _AddSubOperator),
        ]
        self._eval_grammar = pp.infixNotation(base_expr, op_list)

    def _validate_formula(self):
        """Parse and validate the specified diagnostic formula."""
        try:
            self.parsed_formula = self._plain_grammar.parseString(self.formula,
                parseAll=True)
            self.logger.debug("Parsed formula: %s", self.parsed_formula)

            self.evaled_formula = self._eval_grammar.parseString(self.formula,
                parseAll=True)[0]

        except pp.ParseBaseException as exc:
            msg = "Unable to parse derived diagnostic formula:\n" + self.formula
            self.logger.error(str(exc))
            raise InvalidDiagnosticFormulaError(msg, self.formula)

    def _map_vars_to_cubes(self, cubes):
        """
        Create a dictionary that maps variable names defined in the formula to
        the corresponding input cubes.
        """
        var_dict = {}
        terms = self.formula_vars
        self.logger.debug('Formula terms: %r', terms)

        for term in terms:
            try:
                cube = _find_cube_by_name(cubes, term)
                var_dict[term] = cube
            except iris.exceptions.IrisError as exc:
                self.logger.error(str(exc))
                raise

        self.logger.debug("var_dict: %r", var_dict)

        return var_dict

    def _assign_metadata(self):
        """Assign metadata to the result cube."""

        if self.result_metadata:
            if isinstance(self.result_metadata, iris.cube.CubeMetadata):
                try:
                    self.result_metadata = self.result_metadata._asdict()
                except AttributeError:
                    self.result_metadata = {k: getattr(self.result_metadata, k)
                        for k in ['standard_name', 'long_name', 'var_name',
                        'units', 'attributes', 'cell_methods']}

            for k, v in self.result_metadata.items():
                try:
                    setattr(self.result_cube, k, v)
                except iris.exceptions.IrisError:
                    self.logger.warning("Unable to set cube attribute '%s' to '%s'.", k, v)

        # Set the cube's history attribute.
        history = ("Derived diagnostic named '{0}' generated using the "
            "formula:\n{1}".format(self.result_cube.name(), self.formula))
        cubeutils.set_history_attribute(self.result_cube, history, replace=True)


class MipDerivedDiagnostic(SimpleDerivedDiagnostic):
    """
    Provides an implementation of MIP-style derived diagnostics based upon the
    formula syntax employed by the Met Office's Climate Data Dissemination System
    (CDDS) software package.

    The MIP formula grammar is similar to that used by the :class:`SimpleDerivedDiagnostic`
    class, but with the following refinements:

    * A number of CDDS-specific constants are recognised. These are listed under
      the :attr:`CDDS_CONSTANTS` attribute.
    * STASH-type variables may be augmented with one or more PP header word
      constraints enclosed in brackets, e.g. 'm01s01i207[lbproc=4096]'. Multiple
      constraints are permissible and should be separated by commas, e.g.
      'm01s01i207[lbproc=4096,blev=250]'. Whitespace is **prohibited** in STASH
      constraints.

    Currently recognised PP header words include: lbproc, lbtim, lblev, lbplev
    and blev. The value encoded on the right-hand side of a STASH constraint
    should be an integer or float (depending on the header word), or a *colon-
    separated* list of such values. NB: commas are used to separate adjacent
    constraints.

    Here are some examples (albeit contrived) of syntactically valid diagnostic
    formulas based on a combination of STASH codes and variable names::

        'm01s00i024 - 273.15'
        'm01s01i207 - m01s01i208 - m01s03i332'
        'tas * 9./5. + 32'
        'x_wind^2 + y_wind^2'
        'm01s30i201^2 + m01s30i202^2'
        'm01s30i201[lbproc=128,blev=800.0]'
        'm01s30i202[blev=250:500:800]'
        'm01s05i216[lbtim=122] * ICE_DENSITY'
        'm01s08i223[lbplev=3] + m01s08i223[lbplev=4]'
    """

    # Standard constants mirror those defined in the CDDS package.
    _constants = dict(CDDS_CONSTANTS)

    # Character used to separate keyword=value constraints in STASH expressions.
    _pp_constraint_sep = ','

    # Character used to separate list values in STASH constraints.
    _pp_constraint_list_sep = ':'


    def __init__(self, formula, result_metadata=None, **kwargs):
        """
        :param str formula: A text string providing the formula for the derived
            diagnostic. Whitespace in the formula is not mandatory, but is
            recommended for reasons of legibility.
        :param dict result_metadata: Optional dictionary, or iris.cube.CubeMetadata
            object, which supplies the metadata to attach to the result cube.
            Typical attributes include standard_name, long_name, units, and so on.
        :raises afterburner.exceptions.InvalidDiagnosticFormulaError: Raised if
            the specified formula is invalid.
        """
        super(MipDerivedDiagnostic, self).__init__(formula, result_metadata=result_metadata,
            **kwargs)

    def run(self, cubes, result_metadata=None, **kwargs):
        """
        Run the diagnostic processor.

        :param iris.cube.CubeList cubes: A cubelist containing all of the cubes
            referenced by the specified formula. Any other cubes present in the
            cubelist are ignored. There must be a *single* cube for each variable
            named in the formula since the latter contains no information that
            would allow multiple like-named cubes to be disambiguated. See also
            the note below regarding mutually-compatible input cubes.
        :param dict result_metadata: May be used to reset the :attr:`result_metadata`
            instance attribute on a per-invocation basis.
        :returns: A cubelist containing the single cube representing the derived
            diagnostic. Returning a cubelist is intended to achieve uniformity
            with other diagnostic processors, all of which return cubelists.
            To force the return of a single cube object, set the keyword argument
            ``return_single_cube=True``.
        :raises iris.exceptions.ConstraintMismatchError: Raised if an input cube
            could not be found for a named variable in the diagnostic formula.

        .. note:: The input cubes must all have the same shape (number and length
           of dimensions), or else be broadcastable as such. It is also assumed
           that the data arrays attached to the input cubes are type-compatible.
           Currently no checks are performed to verify such compatibility.
        """
        return super(MipDerivedDiagnostic, self).run(cubes, result_metadata=result_metadata,
            **kwargs)

    def _construct_grammar(self):
        """
        Build the grammar used to define a derived diagnostic formula. In fact two
        grammars are returned: the first is a plain, non-evaluating grammar which
        can be used to query terms in the formula. The second is an eval-aware
        grammar which may be used to evaluate the formula given a dictionary of
        values (i.e. cubes) for the variables in the formula.
        """
        # Define upper and lower case letters.
        lowers = pp.srange('[a-z]')
        uppers = pp.srange('[A-Z]')

        # Define expressions for various types of numbers.
        integer = pp.Optional(pp.oneOf('+ -')) + pp.Word(pp.nums)
        real = (
            pp.Combine(pp.Word(pp.nums) + pp.Optional('.' + pp.Word(pp.nums)) +
                pp.oneOf('E e') + pp.Optional(pp.oneOf('+ -')) + pp.Word(pp.nums)) |
            pp.Combine(pp.Word(pp.nums) + '.' + pp.Optional(pp.Word(pp.nums)))
        )
        number = integer ^ real

        # Define expression for a constant term.
        constant = pp.Word(uppers, uppers+pp.nums+'_')
        # alternative definition as list of keywords
        #constant = pp.Keyword('PLEV3') ^ pp.Keyword('PLEV4')

        # Define STASH constraint syntax.
        cons_name = pp.oneOf(['lbproc', 'lbtim', 'lblev', 'lbplev', 'blev'])
        cons_num_list = pp.delimitedList(number, combine=True, delim=':')
        cons_value = pp.Or([constant, cons_num_list])
        cons = pp.Combine(cons_name + pp.Literal('=') + cons_value)
        cons_list = pp.Literal('[') \
                  + pp.delimitedList(cons, combine=True, delim=self._pp_constraint_sep) \
                  + pp.Literal(']')

        # Define expression for a STASH variable.
        stash_code = pp.Regex(r'm\d{2}s\d{2}i\d{3}')
        stash_var = pp.Combine(stash_code + pp.Optional(cons_list))

        # Define expression for a MIP variable.
        mip_var = pp.Word(lowers, lowers+pp.nums+'_')

        # Define expression for a variable term: a STASH code or MIP var name
        var_term = stash_var ^ mip_var

        # Define plain, non-evaluating grammar.
        base_expr = number ^ constant ^ var_term
        expn_op = pp.Literal('^')
        sign_op = pp.oneOf('+ -')
        mult_op = pp.oneOf('* /')
        plus_op = pp.oneOf('+ -')
        op_list = [
            (expn_op, 2, pp.opAssoc.RIGHT),
            (sign_op, 1, pp.opAssoc.RIGHT),
            (mult_op, 2, pp.opAssoc.LEFT),
            (plus_op, 2, pp.opAssoc.LEFT),
        ]
        self._plain_grammar = pp.infixNotation(base_expr, op_list)

        # Define evaluation-aware grammar
        base_expr = number ^ constant ^ var_term
        base_expr.setParseAction(_EvalOperand)
        op_list = [
            (expn_op, 2, pp.opAssoc.RIGHT, _MulDivOperator),
            (sign_op, 1, pp.opAssoc.RIGHT, _SignOperator),
            (mult_op, 2, pp.opAssoc.LEFT, _MulDivOperator),
            (plus_op, 2, pp.opAssoc.LEFT, _AddSubOperator),
        ]
        self._eval_grammar = pp.infixNotation(base_expr, op_list)

    def _map_vars_to_cubes(self, cubes):
        """
        Create a dictionary that maps variable names defined in the formula to
        the corresponding input cubes.
        """
        var_dict = {}
        terms = self.formula_vars
        self.logger.debug('Formula terms: %r', terms)

        for term in terms:
            try:
                if term.isupper():
                    value = self._deref_constant(term)
                elif _is_stash_expr(term):
                    value = _find_cube_by_stash_expr(cubes, term,
                        sep=self._pp_constraint_sep,
                        list_sep=self._pp_constraint_list_sep)
                else:
                    value = _find_cube_by_name(cubes, term)
                var_dict[term] = value
            except iris.exceptions.IrisError as exc:
                self.logger.error(str(exc))
                raise

        self.logger.debug("var_dict: %r", var_dict)

        return var_dict

    def _deref_constant(self, name):
        """Dereference a named constant."""
        try:
            return self._constants[name]
        except KeyError:
            self.logger.error("Unable to dereference constant named %s.", name)
            raise


def _find_cube_by_stash_expr(cubes, stash_expr, sep=',', list_sep=':'):
    """
    Find the cube identified by a constrained STASH variable, e.g. one based on
    the syntax 'm01s02i003[keyword=value,...]. We can assume that stash_expr
    is in the correct format otherwise it would not have passed the formula
    validation step.
    """
    cbs = iris.cube.CubeList()
    try:
        stash_code = stash_expr[:10]
        cbs = cubes.extract(iris.AttributeConstraint(STASH=stash_code))
        if len(cbs):
            stash_cons = dict(x.split('=') for x in stash_expr[11:-1].split(sep))
            cbs = _filter_cubes_by_pp_header_words(cbs, stash_cons, list_sep=list_sep)
    except Exception as exc:
        logger.error(str(exc))

    msg = ''
    if not len(cbs):
        msg = "No cubes found corresponding to STASH expression '%s'." % stash_expr
    elif len(cbs) > 1:
        msg = "More than one cube found corresponding to STASH expression '%s'." % stash_expr
    if msg:
        raise iris.exceptions.ConstraintMismatchError(msg)

    return cbs[0]


def _find_cube_by_name(cubes, name):
    """Find the cube identified by name in the passed-in cubelist."""
    if is_msi_stash_code(name):
        cons = iris.AttributeConstraint(STASH=name)
        cbs = cubes.extract(cons)
    else:
        # first try extracting by standard name
        cons = iris.Constraint(name=name)
        cbs = cubes.extract(cons)
        if not len(cbs):
            # otherwise try extracting by var_name
            cons = iris.Constraint(cube_func=lambda cube: cube.var_name == name)
            cbs = cubes.extract(cons)

    msg = ''
    if not len(cbs):
        msg = "No cubes found corresponding to variable '%s'." % name
    elif len(cbs) > 1:
        msg = "More than one cube found corresponding to variable '%s'." % name
    if msg:
        raise iris.exceptions.ConstraintMismatchError(msg)

    return cbs[0]


def _filter_cubes_by_pp_header_words(cubes, constraints, list_sep=':'):
    """
    Subset cubes from a cubelist which match the PP header words and values
    specified in the constraints dictionary.
    """
    ex_cubes = iris.cube.CubeList()

    # Limited set of LBPROC codes supported at present.
    lbproc_codes = {128: 'mean', 4096: 'minimum', 8192: 'maximum'}

    # Get constraint values as strings.
    lbproc = constraints.get('lbproc')
    lbtim = constraints.get('lbtim')
    lblev = constraints.get('lblev')
    lbplev = constraints.get('lbplev')
    blev = constraints.get('blev')

    for cube in cubes:
        include_cube = False

        if lbproc:
            proc = int(lbproc)
            method = lbproc_codes.get(proc, '')
            if not (method and
                cubeutils._check_cell_method(cube, method, coord_name='time')):
                continue
            include_cube = True

        if lbtim:
            tim = int(lbtim)
            interval = '{0:d} hour'.format(tim//100)
            cal = _calendar_from_lbtim(tim)
            try:
                tcoord = cube.coord('time')
            except CoordinateNotFoundError:
                continue
            if tcoord.units.calendar != cal:
                continue   # calendar mismatch
            if not cube.cell_methods:
                continue   # no cell methods present
            has_method = False
            for cm in cube.cell_methods:
                coord_test = 'time' in cm.coord_names
                interval_test = interval in cm.intervals
                if coord_test and interval_test:
                    has_method = True
                    break
            if not has_method:
                continue
            include_cube = True

        # Extract a specified model level.
        # TODO: may need to expand constant such as PLEV19
        if lblev:
            try:
                levels = [int(x) for x in lblev.split(list_sep)]
                zcoord = cube.coord('model_level_number', dim_coords=True)
                cube = cube.extract(iris.Constraint(coord_values={zcoord.name(): levels}))
                include_cube = True
            except CoordinateNotFoundError:
                continue

        # Extract a specified pseudo-level.
        if lbplev:
            try:
                levels = [int(x) for x in lbplev.split(list_sep)]
                zcoord = cube.coord('pseudo_level', dim_coords=True)
                cube = cube.extract(iris.Constraint(coord_values={zcoord.name(): levels}))
                include_cube = True
            except CoordinateNotFoundError:
                continue

        # Extract a specified vertical level.
        # TODO: may need to expand constant such as PLEV3
        if blev:
            try:
                levels = [float(x) for x in blev.split(list_sep)]
                zcoord = _guess_z_axis(cube)
                cube = cube.extract(iris.Constraint(coord_values={zcoord.name(): levels}))
                include_cube = True
            except CoordinateNotFoundError:
                continue

        if include_cube and cube is not None:
            ex_cubes.append(cube)

    return ex_cubes


def _guess_z_axis(cube, dim_coords=None):
    """Search a cube's coordinates for one that has the characteristics of a Z axis."""

    # List of candidate Z axis names. Probably incomplete.
    vert_coord_names = ['pressure', 'height', 'hybrid_height', 'level_height',
        'model_level', 'model_level_number', 'soil_model_level_number']

    try:
        # First see if Iris can detect a Z axis. As of v1.10, Iris only looks for
        # a coordinate whose units are physically equivalent to Pa.
        zcoord = cube.coord(axis='Z', dim_coords=dim_coords)
    except CoordinateNotFoundError:
        zcoord = None
        # Build a list of candidate coordinates for further testing. Remove any
        # X, Y or T axes from this list.
        candidate_coords = cube.coords(dim_coords=dim_coords)
        for axis in 'XYT':
            try:
                coord = cube.coord(axis=axis)
                candidate_coords.remove(coord)
            except CoordinateNotFoundError:
                pass

    # No luck? Check coordinate names.
    if not zcoord:
        for coord in candidate_coords:
            if coord.name() in vert_coord_names:
                zcoord = coord
                break

    # Still no luck? Check for vertical coordinate units.
    if not zcoord:
        for coord in candidate_coords:
            if coord.units.is_vertical():
                zcoord = coord
                break

    if not zcoord:
        raise CoordinateNotFoundError("Unable to identify vertical coordinate axis.")
    else:
        return zcoord


def _is_stash_expr(term):
    """
    Tests whether the specified formula term represents a constrained STASH
    code; that is, one having the form 'm01s01i001[keyword=value,...]'.
    """
    regex = r'm\d{2}s\d{2}i\d{3}\[.+\]$'
    return re.match(regex, term) is not None


# Portions of the following functions are adapted from some of the examples, by
# various authors, made available via the home page of the pyparsing library -
# see http://pyparsing.wikispaces.com. Those contributors are duly and gratefully
# acknowledged.

def _operators_and_operands(tokenlist):
    """Extract operators and operands in pairs."""
    it = iter(tokenlist)
    while 1:
        try:
            op1 = next(it)
            op2 = next(it)
            yield (op1, op2)
        except StopIteration:
            break


class _EvalOperand(object):
    """Evaluate a constant or variable token."""
    def __init__(self, tokens):
        self.tokens = tokens

    def eval(self, var_dict):
        "Evaluate operand."
        value = self.tokens[0]
        if value in var_dict:
            return var_dict[value]
        else:
            try:
                return int(value)
            except ValueError:
                return float(value)


class _SignOperator(object):
    """Evaluate tokens with a leading + or - sign."""
    def __init__(self, tokens):
        self.tokens = tokens

    def eval(self, var_dict):
        "Evaluate expression."
        sign, value = self.tokens[0]
        if sign == '-':
            return -1 * value.eval(var_dict)
        else:
            return value.eval(var_dict)


# TODO: This class could be merged with the _AddSubOperator class below to form
# a general-purpose _BinaryOperator class, for example.
class _MulDivOperator(object):
    """Evaluate multiplication and division expressions."""
    def __init__(self, tokens):
        self.tokens = tokens

    def eval(self, var_dict):
        "Evaluate expression."
        value = self.tokens[0]
        lhs = value[0].eval(var_dict)   # LHS operand

        # Initialise result to None rather than LHS of expression in order to
        # avoid side effects when the latter is an object, such as an Iris cube.
        prod = None

        for op, val in _operators_and_operands(value[1:]):
            oper = MATH_OPERATORS[op]
            if prod is None:
                prod = oper(lhs, val.eval(var_dict))
            else:
                prod = oper(prod, val.eval(var_dict))

        return prod


class _AddSubOperator(object):
    """Evaluate addition and subtraction expressions."""
    def __init__(self, tokens):
        self.tokens = tokens

    def eval(self, var_dict):
        "Evaluate expression."
        value = self.tokens[0]
        lhs = value[0].eval(var_dict)   # LHS operand

        # Initialise result to None rather than LHS of expression in order to
        # avoid side effects when the latter is an object, such as an Iris cube.
        sum = None

        for op, val in _operators_and_operands(value[1:]):
            oper = MATH_OPERATORS[op]
            if sum is None:
                sum = oper(lhs, val.eval(var_dict))
            else:
                sum = oper(sum, val.eval(var_dict))

        return sum


def _flatten(nested):
    """Flattens a (possibly) nested iterable."""
    for item in nested:
        if isinstance(item, Iterable) and not isinstance(item, string_types):
            for subitem in _flatten(item):
                yield subitem
        else:
            yield item


def _calendar_from_lbtim(lbtim):
    """Decode the calendar type from an LBTIM integer."""
    ical = lbtim % 10
    if ical == 1:
        # According to UM doc F3 this ought to be Proleptic Gregorian. However,
        # Iris uses plain Gregorian so we'll use that here to avoid conflicts.
        if version.parse(nct.__version__) >= version.parse("1.5.2"):
            # The 'gregorian' calendar was silently changed to 'standard'
            # internally, since 'gregorian' deprecated in CF v1.9.
            cal = cf_units.CALENDAR_STANDARD
        else:
            cal = cf_units.CALENDAR_GREGORIAN
    elif ical == 2:
        cal = cf_units.CALENDAR_360_DAY
    elif ical == 4:
        cal = cf_units.CALENDAR_365_DAY
    else:
        cal = None
    return cal
