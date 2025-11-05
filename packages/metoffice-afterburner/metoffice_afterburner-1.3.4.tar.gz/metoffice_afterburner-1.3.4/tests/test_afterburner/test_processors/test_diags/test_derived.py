# (C) British Crown Copyright 2017-2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.processors.diags.derived module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import logging
import unittest
import numpy as np
import numpy.testing as npt
import cf_units
import iris
from iris.fileformats.pp import STASH

from afterburner.exceptions import InvalidDiagnosticFormulaError
from afterburner.processors.diags.derived import (SimpleDerivedDiagnostic,
    create_simple_derived_diagnostic)
from afterburner.processors.diags.derived import (MipDerivedDiagnostic,
    create_mip_derived_diagnostic)


class TestFormulaParser(unittest.TestCase):
    """Test the parsing of formula expressions."""

    def setUp(self):
        # disable logging
        lgr = logging.getLogger('afterburner')
        self.log_level = lgr.level
        lgr.level = 100
        self.test_cubes = _create_test_cubes()

    def tearDown(self):
        # re-enable logging
        lgr = logging.getLogger('afterburner')
        lgr.level = self.log_level

    def test_using_raw_parser(self):
        test_cube = self.test_cubes.extract('air_temperature')[0]
        orig_cube = test_cube.copy()

        formula = 'm01s00i024 + 10'
        proc = SimpleDerivedDiagnostic(formula)

        var_dict = {'m01s00i024': test_cube}
        result_cube = proc.evaled_formula.eval(var_dict)

        # The result should be an Iris cube.
        self.assertEqual(type(result_cube), iris.cube.Cube)
        # The result cube and the input cube should not refer to the same object.
        self.assertFalse(result_cube is test_cube)
        # The original cube should not have been modified.
        self.assertEqual(orig_cube, test_cube)

    def test_using_run_method(self):
        test_cube = self.test_cubes.extract('air_temperature')[0]
        orig_cube = test_cube.copy()

        formula = 'm01s00i024 + 10'
        proc = SimpleDerivedDiagnostic(formula)
        result_cubes = proc.run(self.test_cubes)

        # The result should be a length-1 cubelist.
        self.assertEqual(type(result_cubes), iris.cube.CubeList)
        self.assertEqual(len(result_cubes), 1)
        # The result cube and the input cube should not refer to the same object.
        self.assertFalse(result_cubes[0] is test_cube)
        # The original cube should not have been modified.
        self.assertEqual(orig_cube, test_cube)


class TestSimpleDerivedDiagnostic(unittest.TestCase):
    """Test the SimpleDerivedDiagnostic processor class."""

    def setUp(self):
        # disable logging
        lgr = logging.getLogger('afterburner')
        self.log_level = lgr.level
        lgr.level = 100

        self.test_cubes = _create_test_cubes()
        self.result_metadata = {
            'standard_name': 'toa_net_downward_radiative_flux',
            'var_name': 'toa_rad_bal',
            'units': 'W m-2',
        }

    def tearDown(self):
        # re-enable logging
        lgr = logging.getLogger('afterburner')
        lgr.level = self.log_level

    def test_scalar_operations(self):
        result, = SimpleDerivedDiagnostic('m01s01i207 + 10').run(self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = 20.0
        npt.assert_allclose(result.data, testdata)

        result, = SimpleDerivedDiagnostic('m01s01i207 - 2.5').run(self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = 7.5
        npt.assert_allclose(result.data, testdata)

        result, = SimpleDerivedDiagnostic('m01s01i207 * -5').run(self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = -50.0
        npt.assert_allclose(result.data, testdata)

        result, = SimpleDerivedDiagnostic('m01s01i207 / 2.0').run(self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = 5.0
        npt.assert_allclose(result.data, testdata)

        result, = SimpleDerivedDiagnostic('m01s01i207^3').run(self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = 1000.0
        npt.assert_allclose(result.data, testdata)

    def test_unrecognised_scalar_operations(self):
        self.assertRaises(InvalidDiagnosticFormulaError, SimpleDerivedDiagnostic,
            'm01s01i207 // 2')
        self.assertRaises(InvalidDiagnosticFormulaError, SimpleDerivedDiagnostic,
            'm01s01i207 % 2')
        self.assertRaises(InvalidDiagnosticFormulaError, SimpleDerivedDiagnostic,
            'm01s01i207**2')

    def test_return_single_cube(self):
        result = SimpleDerivedDiagnostic('m01s01i207 + 10').run(self.test_cubes,
            return_single_cube=True)
        testdata = result.data.copy()
        testdata[:] = 20.0
        npt.assert_allclose(result.data, testdata)

    def test_formulas_with_stash_codes(self):
        formula = 'm01s01i207 - m01s01i208 - m01s03i332'
        result, = SimpleDerivedDiagnostic(formula).run(self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = 2.5
        npt.assert_allclose(result.data, testdata)

        formula = 'm01s01i207 + m01s01i208'
        result, = SimpleDerivedDiagnostic(formula).run(self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = 15.0
        npt.assert_allclose(result.data, testdata)

        formula = 'm01s01i207 / m01s03i332'
        result, = SimpleDerivedDiagnostic(formula).run(self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = 4.0
        npt.assert_allclose(result.data, testdata)

        formula = 'm01s01i207^2 + m01s01i208^2'
        result, = SimpleDerivedDiagnostic(formula).run(self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = 125.0
        npt.assert_allclose(result.data, testdata)

    def test_formulas_with_std_names(self):
        formula = 'toa_incoming_shortwave_flux - toa_outgoing_shortwave_flux - ' \
                  'toa_outgoing_longwave_flux'
        result, = SimpleDerivedDiagnostic(formula).run(self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = 2.5
        npt.assert_allclose(result.data, testdata)

    def test_formulas_with_var_names(self):
        formula = 'sw_in - sw_out - lw_out'
        result, = SimpleDerivedDiagnostic(formula).run(self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = 2.5
        npt.assert_allclose(result.data, testdata)

    def test_dict_metadata(self):
        formula = 'm01s01i207 + 10'
        diag = SimpleDerivedDiagnostic(formula, result_metadata=self.result_metadata)
        result, = diag.run(self.test_cubes)
        self.assertEqual(result.standard_name, self.result_metadata['standard_name'])
        self.assertEqual(result.var_name, self.result_metadata['var_name'])
        self.assertEqual(result.units, self.result_metadata['units'])
        self.assertTrue(formula in result.attributes['history'])

        new_metadata = {'var_name': 'foo', 'units': 'W ft-2'}
        result, = diag.run(self.test_cubes, result_metadata=new_metadata)
        self.assertEqual(result.standard_name, None)
        self.assertEqual(result.var_name, 'foo')
        self.assertEqual(result.units, 'W ft-2')

    def test_cube_metadata(self):
        formula = 'm01s01i207 + 10'
        md = iris.cube.CubeMetadata(standard_name='toa_net_downward_radiative_flux',
            long_name=None, var_name='toa_rad_bal', units='W m-2', cell_methods=None,
            attributes={'project': 'afterburner'})
        diag = SimpleDerivedDiagnostic(formula, result_metadata=md)
        result, = diag.run(self.test_cubes)
        self.assertEqual(result.standard_name, md.standard_name)
        self.assertEqual(result.var_name, md.var_name)
        self.assertEqual(result.units, md.units)

    def test_missing_cube(self):
        # incorrect stash code
        formula = 'm02s01i207 * 10'
        diag = SimpleDerivedDiagnostic(formula)
        self.assertRaises(iris.exceptions.ConstraintMismatchError, diag.run, self.test_cubes)

        # incorrect std name
        formula = 'toa_incoming_shortwave_flux - toa_outgoing_shortwave_flux - ' \
                  'outgoing_longwave_flux'
        diag = SimpleDerivedDiagnostic(formula)
        self.assertRaises(iris.exceptions.ConstraintMismatchError, diag.run, self.test_cubes)

        # incorrect var name
        formula = 'sw_in - sw_out - lw_in'
        diag = SimpleDerivedDiagnostic(formula)
        self.assertRaises(iris.exceptions.ConstraintMismatchError, diag.run, self.test_cubes)

    def test_invalid_formula(self):
        formula = '01s01i207 * 10'
        self.assertRaises(InvalidDiagnosticFormulaError, SimpleDerivedDiagnostic, formula)

    def test_history_att(self):
        md = dict(attributes={'project': 'afterburner'})
        diag = SimpleDerivedDiagnostic('m01s01i207 + 10', result_metadata=md)
        result, = diag.run(self.test_cubes)
        self.assertTrue(result.attributes.get('history'))
        self.assertEqual(result.attributes.get('project'), 'afterburner')


class TestSimpleDerivedUtilFunc(unittest.TestCase):
    """Test the create_simple_derived_diagnostic() utility function."""

    def setUp(self):
        self.test_cubes = _create_test_cubes()
        self.result_metadata = {
            'standard_name': 'toa_net_downward_radiative_flux',
            'var_name': 'toa_rad_bal',
            'units': 'W m-2',
        }

    def test_with_stash_codes(self):
        formula = 'm01s01i207 - m01s01i208 - m01s03i332'
        result, = create_simple_derived_diagnostic(formula, self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = 2.5
        npt.assert_allclose(result.data, testdata)

    def test_with_metadata(self):
        md = dict(attributes={'project': 'afterburner'})
        formula = 'm01s01i207 + 10'
        result, = create_simple_derived_diagnostic(formula, self.test_cubes, result_metadata=md)
        self.assertTrue(result.attributes.get('history'))
        self.assertEqual(result.attributes.get('project'), 'afterburner')


class TestMipDerivedDiagnostic(unittest.TestCase):
    """Test the MipDerivedDiagnostic processor class."""

    def setUp(self):
        # disable logging
        lgr = logging.getLogger('afterburner')
        self.log_level = lgr.level
        lgr.level = 100

        self.test_cubes = _create_test_cubes()
        self.result_metadata = {
            'standard_name': 'toa_net_downward_radiative_flux',
            'var_name': 'toa_rad_bal',
            'units': 'W m-2',
        }

    def tearDown(self):
        # re-enable logging
        lgr = logging.getLogger('afterburner')
        lgr.level = self.log_level

    def test_valid_formulas(self):
        diag = MipDerivedDiagnostic('m01s01i207')
        self.assertEqual(diag.formula_terms, ['m01s01i207'])

        diag = MipDerivedDiagnostic('var1')
        self.assertEqual(diag.formula_terms, ['var1'])

        diag = MipDerivedDiagnostic('m01s01i207 + 10')
        self.assertEqual(diag.formula_terms, ['m01s01i207', '10'])
        self.assertEqual(diag.formula_vars, ['m01s01i207'])

        diag = MipDerivedDiagnostic('m01s01i207[lbproc=128] - 10')
        self.assertEqual(diag.formula_terms, ['m01s01i207[lbproc=128]', '10'])
        self.assertEqual(diag.formula_vars, ['m01s01i207[lbproc=128]'])

        diag = MipDerivedDiagnostic('m01s01i207 + m01s01i208 * 2')
        self.assertEqual(diag.formula_terms, ['m01s01i207', 'm01s01i208', '2'])
        self.assertEqual(diag.formula_vars, ['m01s01i207', 'm01s01i208'])

        diag = MipDerivedDiagnostic('m01s01i207 - m01s01i208 / PI')
        self.assertEqual(diag.formula_terms, ['m01s01i207', 'm01s01i208', 'PI'])
        self.assertEqual(diag.formula_vars, ['m01s01i207', 'm01s01i208', 'PI'])

        diag = MipDerivedDiagnostic('var1 + var2^2')
        self.assertEqual(diag.formula_terms, ['var1', 'var2', '2'])
        self.assertEqual(diag.formula_vars, ['var1', 'var2'])

    def test_scalar_operations(self):
        result, = MipDerivedDiagnostic('m01s01i207 + 10').run(self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = 20.0
        npt.assert_allclose(result.data, testdata)

    def test_with_stash_codes(self):
        formula = 'm01s01i207 - m01s01i208 - m01s03i332'
        result, = MipDerivedDiagnostic(formula).run(self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = 2.5
        npt.assert_allclose(result.data, testdata)

    def test_with_lbproc_constraints(self):
        formula = 'm01s01i207[lbproc=128] * 10'
        tmp_cubes = self.test_cubes[:]
        result, = MipDerivedDiagnostic(formula).run(tmp_cubes)
        testdata = result.data.copy()
        testdata[:] = 100.0
        npt.assert_allclose(result.data, testdata)

        formula = 'm01s01i207[lbproc=4096] * 10'
        cm = iris.coords.CellMethod('minimum', coords=('time',))
        cube0 = tmp_cubes[0]
        cube0.cell_methods = (cm,)
        result, = MipDerivedDiagnostic(formula).run(tmp_cubes)
        testdata = result.data.copy()
        testdata[:] = 100.0
        npt.assert_allclose(result.data, testdata)

        formula = 'm01s01i207[lbproc=8192] * 10'
        cm = iris.coords.CellMethod('maximum', coords=('time',))
        cube0.cell_methods = (cm,)
        result, = MipDerivedDiagnostic(formula).run(tmp_cubes)
        testdata = result.data.copy()
        testdata[:] = 100.0
        npt.assert_allclose(result.data, testdata)

    def test_with_lbtim_constraints(self):
        formula = 'm01s01i207[lbtim=122] * 10'
        tmp_cubes = self.test_cubes[:]
        result, = MipDerivedDiagnostic(formula).run(tmp_cubes)
        testdata = result.data.copy()
        testdata[:] = 100.0
        npt.assert_allclose(result.data, testdata)

        formula = 'm01s01i207[lbtim=621] * 10'
        cm = iris.coords.CellMethod('mean', coords=('time',), intervals=('6 hour'))
        cube0 = tmp_cubes[0]
        cube0.cell_methods = (cm,)
        tcoord = cube0.coord('time')
        tcoord.units = cf_units.Unit(tcoord.units, calendar=cf_units.CALENDAR_GREGORIAN)
        result, = MipDerivedDiagnostic(formula).run(tmp_cubes)
        testdata = result.data.copy()
        testdata[:] = 100.0
        npt.assert_allclose(result.data, testdata)

    def test_with_lbtim_and_lbproc_constraints(self):
        formula = 'm01s01i207[lbtim=2422,lbproc=4096] * 10'
        tmp_cubes = self.test_cubes[:]
        cm = iris.coords.CellMethod('minimum', coords=('time',), intervals=('24 hour'))
        cube0 = tmp_cubes[0]
        cube0.cell_methods = (cm,)
        result, = MipDerivedDiagnostic(formula).run(tmp_cubes)
        testdata = result.data.copy()
        testdata[:] = 100.0
        npt.assert_allclose(result.data, testdata)

    def test_with_lblev_constraints(self):
        formula = 'm01s00i024[lblev=1] * 10'
        tmp_cubes = self.test_cubes[:]
        result, = MipDerivedDiagnostic(formula).run(tmp_cubes)
        self.assertEqual(result.ndim, 1)
        testdata = result.data.copy()
        testdata[:] = 100.0
        npt.assert_allclose(result.data, testdata)

        formula = 'm01s00i024[lblev=1:2] * 5'
        result, = MipDerivedDiagnostic(formula).run(tmp_cubes)
        self.assertEqual(result.ndim, 2)
        self.assertEqual(result.shape[1], 2)
        testdata = result.data.copy()
        testdata[:] = 50.0
        npt.assert_allclose(result.data, testdata)

    def test_invalid_lblev_constraints(self):
        tmp_cubes = self.test_cubes[:]
        formula = 'm01s00i024[lblev=-1] * 10'
        diag = MipDerivedDiagnostic(formula)
        self.assertRaises(iris.exceptions.ConstraintMismatchError,
            diag.run, tmp_cubes)

        formula = 'm01s00i024[lblev=99] * 10'
        diag = MipDerivedDiagnostic(formula)
        self.assertRaises(iris.exceptions.ConstraintMismatchError,
            diag.run, tmp_cubes)

    def test_with_blev_constraints(self):
        formula = 'm01s30i201[blev=250] * 10'   # specify levels as ints
        tmp_cubes = self.test_cubes[:]
        result, = MipDerivedDiagnostic(formula).run(tmp_cubes)
        self.assertEqual(result.ndim, 1)
        testdata = result.data.copy()
        testdata[:] = 100.0
        npt.assert_allclose(result.data, testdata)

        formula = 'm01s30i201[blev=250.0:500.0] * 5'   # specify levels as floats
        result, = MipDerivedDiagnostic(formula).run(tmp_cubes)
        self.assertEqual(result.ndim, 2)
        self.assertEqual(result.shape[1], 2)
        testdata = result[0].data.copy()
        testdata[:] = 50.0
        npt.assert_allclose(result[0].data, testdata)

        formula = 'm01s30i201[blev=250:500:850] * 2'
        result, = MipDerivedDiagnostic(formula).run(tmp_cubes)
        self.assertEqual(result.ndim, 2)
        self.assertEqual(result.shape[1], 3)
        testdata = result[0].data.copy()
        testdata[:] = 20.0
        npt.assert_allclose(result[0].data, testdata)

        formula = 'm01s01i208[blev=30] * 10'
        result, = MipDerivedDiagnostic(formula).run(tmp_cubes)
        self.assertEqual(result.ndim, 1)
        testdata = result.data.copy()
        testdata[:] = 50.0
        npt.assert_allclose(result.data, testdata)

        formula = 'm01s00i024[blev=1] * 10'
        result, = MipDerivedDiagnostic(formula).run(tmp_cubes)
        self.assertEqual(result.ndim, 1)
        testdata = result.data.copy()
        testdata[:] = 100.0
        npt.assert_allclose(result.data, testdata)

        formula = 'm01s05i216[blev=20] * 10'
        result, = MipDerivedDiagnostic(formula).run(tmp_cubes)
        self.assertEqual(result.ndim, 1)
        testdata = result.data.copy()
        testdata[:] = 100.0
        npt.assert_allclose(result.data, testdata)

    def test_invalid_blev_constraints(self):
        tmp_cubes = self.test_cubes[:]
        formula = 'm01s01i208[blev=-1] * 10'
        diag = MipDerivedDiagnostic(formula)
        self.assertRaises(iris.exceptions.ConstraintMismatchError,
            diag.run, tmp_cubes)

        formula = 'm01s01i208[blev=99] * 10'
        diag = MipDerivedDiagnostic(formula)
        self.assertRaises(iris.exceptions.ConstraintMismatchError,
            diag.run, tmp_cubes)

    def test_with_named_constant(self):
        formula = 'm01s01i207 + DAYS_IN_YEAR'
        result, = MipDerivedDiagnostic(formula).run(self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = 370.0
        npt.assert_allclose(result.data, testdata)

    def test_history_att(self):
        md = dict(attributes={'project': 'afterburner'})
        diag = MipDerivedDiagnostic('m01s01i207 + 10')
        result, = diag.run(self.test_cubes, result_metadata=md)
        self.assertTrue(result.attributes.get('history'))
        self.assertEqual(result.attributes.get('project'), 'afterburner')


class TestMipDerivedUtilFunc(unittest.TestCase):
    """Test the create_mip_derived_diagnostic() utility function."""

    def setUp(self):
        self.test_cubes = _create_test_cubes()
        self.result_metadata = {
            'standard_name': 'toa_net_downward_radiative_flux',
            'var_name': 'toa_rad_bal',
            'units': 'W m-2',
        }

    def test_with_stash_codes(self):
        formula = 'm01s01i207 - m01s01i208 - m01s03i332'
        result, = create_mip_derived_diagnostic(formula, self.test_cubes)
        testdata = result.data.copy()
        testdata[:] = 2.5
        npt.assert_allclose(result.data, testdata)

    def test_with_metadata(self):
        md = dict(attributes={'project': 'afterburner'})
        formula = 'm01s01i207 + 10'
        result, = create_mip_derived_diagnostic(formula, self.test_cubes, result_metadata=md)
        self.assertTrue(result.attributes.get('history'))
        self.assertEqual(result.attributes.get('project'), 'afterburner')


def _create_test_cubes():
    sw_in = _create_raw_tz_cube(standard_name='toa_incoming_shortwave_flux',
        var_name='sw_in', units='W m-2', z_std_name='height', z_units='m',
        stash_code='m01s01i207')
    sw_in.data[:] = 10.0

    sw_out = _create_raw_tz_cube(standard_name='toa_outgoing_shortwave_flux',
        var_name='sw_out', units='W m-2', z_std_name='height', z_units='m',
        stash_code='m01s01i208')
    sw_out.data[:] = 5.0

    lw_out = _create_raw_tz_cube(standard_name='toa_outgoing_longwave_flux',
        var_name='lw_out', units='W m-2', z_std_name='height', z_units='m',
        stash_code='m01s03i332')
    lw_out.data[:] = 2.5

    uwind = _create_raw_tz_cube(standard_name='x_wind',
        var_name='uwind', units='m s-1', z_long_name='pressure', z_units='hPa',
        stash_code='m01s30i201')
    uwind.data[:] = 10.0

    tas = _create_raw_tz_cube(standard_name='air_temperature',
        var_name='tas', units='K', z_std_name='model_level_number', z_units='1',
        stash_code='m01s00i024')
    tas.data[:] = 10.0

    pr = _create_raw_tz_cube(long_name='precipitation', var_name='precip',
        units='mm', z_long_name='altitude', z_units='m', stash_code='m01s05i216')
    pr.data[:] = 10.0

    return iris.cube.CubeList([sw_in, sw_out, lw_out, uwind, tas, pr])


def _create_raw_tz_cube(**kwargs):
    times = np.arange(0., 360., 30.)
    tunits = cf_units.Unit('days since 1970-01-01', calendar='360_day')
    tcoord = iris.coords.DimCoord(times, standard_name='time', units=tunits)

    if kwargs.get('z_long_name') == 'pressure':
        levels = [1000., 850., 500., 250.]
    elif kwargs.get('z_std_name') == 'height' or kwargs.get('z_long_name') == 'altitude':
        levels = [0., 10., 20., 30.]
    else:
        levels = np.arange(4)
    zcoord = iris.coords.DimCoord(levels, standard_name=kwargs.get('z_std_name'),
        long_name=kwargs.get('z_long_name'), units=kwargs.get('z_units'))

    data = np.zeros([len(times), len(levels)]).astype('float32')
    cube = iris.cube.Cube(data, standard_name=kwargs.get('standard_name'),
        long_name=kwargs.get('long_name'), var_name=kwargs.get('var_name'),
        units=kwargs.get('units', '1'))

    cube.attributes['STASH'] = STASH.from_msi(kwargs.get('stash_code'))
    cube.add_dim_coord(tcoord, 0)
    cube.add_dim_coord(zcoord, 1)

    cm = iris.coords.CellMethod('mean', coords=('time',), intervals=('1 hour'))
    cube.cell_methods = (cm,)

    return cube


if __name__ == '__main__':
    unittest.main()
