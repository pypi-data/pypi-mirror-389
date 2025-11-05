# (C) British Crown Copyright 2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.

# This module contains functions for comparing pairs of Iris cubes and their
# internal objects, e.g. coordinates, cell_methods, and cell measures. These
# functions are imported into the afterburner.utils.cubeutils module and should
# normally be accessed from that location.

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import sys
from contextlib import contextmanager
from iris.exceptions import CoordinateNotFoundError

__all__ = ('compare_cubes',)


@contextmanager
def stdout_redirector(stream):
    "Context manager for redirecting stdout."
    old_stdout = sys.stdout
    if stream != sys.stdout: sys.stdout = stream
    try:
        yield
    finally:
        sys.stdout = old_stdout


def compare_cubes(cube1, cube2, stream=None, **kwargs):
    """
    Compare two Iris cubes and report differences on the stream pointed to by
    the stream argument. Note that the numerical arrays making up the cube data
    payloads are *not* currently compared.

    As well as comparing metadata attributes attached directly to both cubes
    (e.g. the various `*_name` attributes), this function also recursively examines
    the main composite cube objects: coordinates, cell_methods and cell_measures.

    :param iris.cube.Cube cube1: The first cube to compare.
    :param iris.cube.Cube cube2: The second cube to compare.
    :param file stream: The output stream (a file-like object) on which to print
        messages. The default stream is sys.stdout.

    The following boolean keyword arguments may be used to enable/disable any of
    the cube elements being compared. By default all elements are examined.

    :param bool shapes_and_types: Compare the shape and type of the data arrays.
    :param bool metadata: Compare the metadata properties of the cubes.
    :param bool cell_methods: Compare the cell methods of the cubes.
    :param bool cell_measures: Compare the cell measures of the cubes.
    :param bool coordinates: Compare the coordinates of the cubes.

    :returns: True if the cubes are equal (ignoring data arrays), otherwise false.
    """
    cubes_are_equal = True

    if not stream: stream = sys.stdout

    with stdout_redirector(stream):
        print("Comparing the following cubes:")
        print("  1: {0}".format(cube1.summary(shorten=True)))
        print("  2: {0}".format(cube2.summary(shorten=True)))

        # compare data shapes and types
        if kwargs.get('shapes_and_types', True):
            if not _compare_shapes_and_types(cube1, cube2): cubes_are_equal = False

        # compare cube metadata
        if kwargs.get('metadata', True):
            if not _compare_metadata(cube1, cube2): cubes_are_equal = False

        # compare cell methods
        if kwargs.get('cell_methods', True):
            if not _compare_cell_methods(cube1, cube2): cubes_are_equal = False

        # compare cell measures
        if kwargs.get('cell_measures', True):
            if not _compare_cell_measures(cube1, cube2): cubes_are_equal = False

        # compare coordinate lists
        if kwargs.get('coordinates', True):
            if not _compare_coordinates(cube1, cube2): cubes_are_equal = False

    if cubes_are_equal:
        print("\nCubes are equal")
    else:
        print("\nCubes differ")

    return cubes_are_equal


def _compare_shapes_and_types(cube1, cube2):
    "Compare data shapes and types on two cubes."

    print("\nComparing cube shapes and data types:")

    items_are_equal = True

    if cube1.shape != cube2.shape:
        print("  cube shapes differ: {0} != {1}".format(cube1.shape, cube2.shape))
        items_are_equal = False
    else:
        print("  cube shapes are equal {0}".format(cube1.shape))

    # compare cube datatypes
    if cube1.dtype != cube2.dtype:
        print("  cube datatypes differ: {0} != {1}".format(cube1.dtype, cube2.dtype))
        items_are_equal = False
    else:
        print("  cube datatypes are equal ({0})".format(cube1.dtype))

    return items_are_equal


def _compare_metadata(cube1, cube2):
    "Compare metadata items on two cubes."

    items_are_equal = True

    # compare cube metadata attributes
    print("\nComparing cube metadata attributes:")
    for att in ['standard_name', 'long_name', 'var_name', 'units']:
        att_val1 = getattr(cube1, att, '<null>')
        att_val2 = getattr(cube2, att, '<null>')
        if att_val1 != att_val2:
            print("  attribute '{0}': {1} != {2}".format(att, att_val1, att_val2))
            items_are_equal = False
    if items_are_equal:
        print("  metadata attributes are equal")

    # compare cube.attributes dictionaries
    print("\nComparing cube.attributes dictionaries:")
    if cube1.attributes != cube2.attributes:
        print("  attribute dictionaries differ")
        _compare_dicts(cube1.attributes, cube2.attributes)
        items_are_equal = False
    else:
        print("  attribute dictionaries are equal")

    return items_are_equal


def _compare_cell_methods(cube1, cube2):
    "Compare cell methods on two cubes."

    print("\nComparing cell methods:")

    cms_are_equal = True

    cube1_cms = set(cube1.cell_methods) if cube1.cell_methods else set()
    cube2_cms = set(cube2.cell_methods) if cube2.cell_methods else set()

    if cube1_cms != cube2_cms:
        cube1_not_2 = cube1_cms.difference(cube2_cms)
        if cube1_not_2:
            cm_text = ["    '{0}'".format(cm) for cm in cube1_not_2]
            print("  cell methods in cube1 but not cube2:\n" + '\n'.join(cm_text))
        cube2_not_1 = cube2_cms.difference(cube1_cms)
        if cube2_not_1:
            cm_text = ["    '{0}'".format(cm) for cm in cube2_not_1]
            print("  cell methods in cube2 but not cube1:\n" + '\n'.join(cm_text))
        cms_are_equal = False
    else:
        print("  cell methods are equal (or null)")

    return cms_are_equal


def _compare_cell_measures(cube1, cube2):
    "Compare cell measures on two cubes."

    print("\nComparing cell measure lists:")

    cms_are_equal = True

    try:
        cube1_cms = set([cm.measure for cm in cube1.cell_measures()])
        cube2_cms = set([cm.measure for cm in cube2.cell_measures()])
        if cube1_cms != cube2_cms:
            diffs = list(cube1_cms.difference(cube2_cms))
            print("  cell measures in cube1 but not cube2:", diffs or '<null>')
            diffs = list(cube2_cms.difference(cube1_cms))
            print("  cell measures in cube2 but not cube1:", diffs or '<null>')
            cms_are_equal = False
        else:
            print("  cell measure lists are equal (or null)")

        # compare individual cell measures common to both cubes
        for measure in cube1_cms & cube2_cms:
            if not _compare_cell_measure(cube1, cube2, measure):
                cms_are_equal = False

    except AttributeError:
        print("  none found (old version of Iris?)")

    return cms_are_equal


def _compare_cell_measure(cube1, cube2, measure):
    "Compare a given cell measure on two cubes."

    print("\nComparing {0} cell measures:".format(measure))

    cm1 = cm2 = None
    for cm in cube1.cell_measures():
        if cm.measure == measure:
            cm1 = cm
            break
    for cm in cube2.cell_measures():
        if cm.measure == measure:
            cm2 = cm
            break

    if not any([cm1, cm2]):
        print("  cell measure '{0}' not present on either cube.".format(measure))
        return False
    elif cm1 and not cm2:
        print("  cell measure '{0}' not present on cube2".format(measure))
        return False
    elif cm2 and not cm1:
        print("  cell measure '{0}' not present on cube1".format(measure))
        return False

    cms_are_equal = True

    # compare cell measure shapes
    if cm1.data.shape != cm2.data.shape:
        print("  cell measure shapes differ: {0} != {1}".format(cm1.data.shape,
            cm2.data.shape))
        cms_are_equal = False

    # compare cell measure datatypes
    if cm1.data.dtype != cm2.data.dtype:
        print("  cell measure datatypes differ: {0} != {1}".format(cm1.data.dtype,
            cm2.data.dtype))
        cms_are_equal = False

    # compare name attributes and units
    for att in ['standard_name', 'long_name', 'var_name', 'units']:
        att_val1 = getattr(cm1, att, '<null>')
        att_val2 = getattr(cm2, att, '<null>')
        if att_val1 != att_val2:
            print("  attribute '{0}': {1} != {2}".format(att, att_val1, att_val2))
            cms_are_equal = False

    # compare attributes dictionaries
    if cm1.attributes != cm2.attributes:
        print("  attribute dictionaries differ")
        _compare_dicts(cm1.attributes, cm2.attributes)
        cms_are_equal = False
    else:
        print("  attribute dictionaries are equal")

    if cms_are_equal:
        print("  cell measures are equal")

    return cms_are_equal


def _compare_coordinates(cube1, cube2):
    "Compare coordinates on two cubes."

    print("\nComparing coordinate lists:")

    coords_are_equal = True
    cube1_coords = {c.name() for c in cube1.coords()}
    cube2_coords = {c.name() for c in cube2.coords()}

    if cube1_coords != cube2_coords:
        diffs = list(cube1_coords.difference(cube2_coords))
        print("  coordinates in cube1 but not cube2:", diffs or '<null>')
        diffs = list(cube2_coords.difference(cube1_coords))
        print("  coordinates in cube2 but not cube1:", diffs or '<null>')
        coords_are_equal = False
    else:
        print("  coordinate lists are equal (or null)")

    # compare individual coordinates common to both cubes
    for coord_name in cube1_coords & cube2_coords:
        if not _compare_coordinate(cube1, cube2, coord_name):
            coords_are_equal = False

    return coords_are_equal


def _compare_coordinate(cube1, cube2, coord_name):
    "Compare a given coordinate on two cubes."

    print("\nComparing {0} coordinates:".format(coord_name))

    try:
        coord1 = cube1.coord(coord_name)
    except CoordinateNotFoundError:
        coord1 = None
    try:
        coord2 = cube2.coord(coord_name)
    except CoordinateNotFoundError:
        coord2 = None

    if not any([coord1, coord2]):
        print("  coordinate '{0}' not present on either cube.".format(coord_name))
        return False
    elif coord1 and not coord2:
        print("  coordinate '{0}' not present on cube2".format(coord_name))
        return False
    elif coord2 and not coord1:
        print("  coordinate '{0}' not present on cube1".format(coord_name))
        return False

    coords_are_equal = True

    # compare coordinate shapes
    if coord1.shape != coord2.shape:
        print("  coordinate shapes differ: {0} != {1}".format(coord1.shape, coord2.shape))
        coords_are_equal = False

    # compare coordinate datatypes
    if coord1.dtype != coord2.dtype:
        print("  coordinate datatypes differ: {0} != {1}".format(coord1.dtype, coord2.dtype))
        coords_are_equal = False

    # compare coordinate systems
    if coord1.coord_system != coord2.coord_system:
        print("  coordinate systems differ: {0} != {1}".format(
            coord1.coord_system or '<null>',
            coord2.coord_system or '<null>'))
        coords_are_equal = False

    # compare name attributes and units
    for att in ['standard_name', 'long_name', 'var_name', 'units']:
        att_val1 = getattr(coord1, att, '<null>')
        att_val2 = getattr(coord2, att, '<null>')
        if att_val1 != att_val2:
            print("  attribute '{0}': {1} != {2}".format(att, att_val1, att_val2))
            coords_are_equal = False

    # compare circular attributes
    circ1 = getattr(coord1, 'circular', '<null>')
    circ2 = getattr(coord2, 'circular', '<null>')
    if circ1 != circ2:
        print("  circular attribute: {0} != {1}".format(circ1, circ2))
        coords_are_equal = False

    if coords_are_equal:
        print("  coordinates are equal")

    return coords_are_equal


def _compare_dicts(dict1, dict2):
    "Compare the key-value pairs of two dictionaries."

    dicts_are_equal = True

    for key in list(dict1) + list(dict2):
        val1 = dict1.get(key, '<null>')
        val2 = dict2.get(key, '<null>')
        if val1 != val2:
            print("  attribute '{0}': {1} != {2}".format(key, val1, val2))
            dicts_are_equal = False

    return dicts_are_equal
