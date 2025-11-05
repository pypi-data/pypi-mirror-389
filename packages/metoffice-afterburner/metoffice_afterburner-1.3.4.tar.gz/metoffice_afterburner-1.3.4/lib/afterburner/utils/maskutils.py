# (C) British Crown Copyright 2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The maskutils module contains various utility functions for applying masks to
NumPy arrays. Currently supported masking operations include:

* Mask an array A where array M is [masked | not masked]
* Mask an array A where array M is [eq | ne | gt | ge | lt | le] a user-defined value
* Mask an array A where array M is [eq | ne | gt | ge | lt | le] a user-defined value,
  and then apply a NumPy binary function to arrays A and M, e.g ``np.add(A, M)``.

Some of the functions act as fairly lightweight wrappers around NumPy's masking
functions, such as ``np.ma.masked_where()``. However, the functions provided here
do offer the advantage of being able to replace chunks of commonly repeated NumPy
array masking code with a single function call.

In the case of masking a data array of higher rank (i.e. more dimensions) than
the mask array, the functions here take care of correctly broadcasting the mask
array to match the data array.

A number of functions provide the added convenience of being able to operate
directly on the data arrays attached to Iris cubes.

**Index of Functions in this Module**

.. autosummary::
   :nosignatures:

   apply_mask_to_array
   apply_masked_op_to_array
   apply_mask_to_cube
   apply_masked_op_to_cube

.. note:: This module depends upon NumPy v1.10.0 or later.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import string_types

import operator
import numpy as np
import numpy.ma as ma
import iris


def apply_mask_to_array(data_array, mask_array, mask_only=True, invert_mask=False,
        compare_value=0, compare_op=None, np_func=None, fill_value=None):
    """
    Apply a mask or mask-plus-function operation to a NumPy array.

    Mask elements in ``data_array`` based upon either the masked elements in
    ``mask_array`` (if mask_only is True) or a comparison of the values in
    ``mask_array`` with ``compare_value`` (if mask_only is False). In the latter
    case, the default settings will result in elements in ``data_array`` being
    masked where elements in ``mask_array`` are equal to zero.

    The shape of ``mask_array`` must be the same as, or broadcastable to, that
    of ``data_array``. In the particular case where ``mask_array`` is a 2D
    MaskedArray object (representing, for example, a land-sea mask) which is to
    be applied to a ``data_array`` of higher rank (e.g. 3D or 4D), then ``mask_array``
    is first broadcast (locally: the passed-in array is unaffected) to the shape
    of ``data_array``.

    If ``np_func`` defines the name of a NumPy binary function, and ``mask_only``
    is False, then the  *unmasked* elements of ``data_array`` and ``mask_array``
    are combined in the manner ``np_func(data_array, mask_array)``. For example,
    if ``np_func`` is set to ``np.multiply`` then the effect will be to perform
    an element-wise product of the two arrays. This can be handy for both masking
    out sea points and applying a land-area fraction correction -- or the inverse
    -- to a data array in a single operation, as shown below:

    >>> newdata = apply_mask_to_array(data, land_area_frac, mask_only=False,
    ...     compare_value=0.5, compare_op='lt', np_func=np.multiply)

    Note that the type of the ``newdata`` array will reflect NumPy's standard
    type promotion rules when operating on multiple operands.

    :param data_array: The NumPy array to be masked (or further masked if it is
        already a MaskedArray object).
    :param mask_array: The NumPy array or MaskedArray that is used to determine
        which elements in data_array to mask.
    :param bool mask_only: If true (the default) then only the mask portion of
        mask_array is consulted. In this case mask_array must be a NumPy
        MaskedArray object. If mask_only is False then the elements to mask are
        determined by comparing mask_array values with compare_value (default: 0)
        using compare_op (default: eq)
    :param bool invert_mask: If set to true then the complement of the mask
        attached to mask_array is used for pure masking operations (mask_only is True).
    :param int/float compare_value: The value to use in comparison tests
        against elements of mask_array. Elements that meet the comparison test
        define the array indices which then get used to mask data_array.
    :param str compare_op: The comparison operator to use in comparison tests
        against elements of mask_array. This can either be a string such as 'eq',
        'lt', 'ge', etc, or the name of one of the equivalent functions defined
        in the operator module, e.g. operator.eq (the default), operator.lt, etc.
    :param function np_func: Optionally, the name of a NumPy binary function
        (e.g. np.add) which will be used to operate on *unmasked* elements of
        data_array and mask_array. For example, if compare_value and compare_op
        are set so as to mask out sea (or land) elements in mask_array, then
        setting np_func to np.multiply will result in the corresponding elements
        in data_array being masked and the remaining unmasked elements being
        multiplied by the land (or sea) area fraction. In the default case
        where np_func is undefined, unmasked elements in data_array are left
        unmodified.
    :param int/float fill_value: The fill value to assign to the returned array.
        If undefined then a NumPy default fill value will be used, the value of
        which will depend upon the array's data type.
    :returns: A masked data array.
    :raises ValueError: Raised if the shapes of the input arrays are incompatible,
        or if mask_array is not a MaskedArray (but one was expected).
    """

    # Assign the comparison operator (equality being the default).
    if isinstance(compare_op, string_types):
        op = getattr(operator, compare_op)
    else:
        op = compare_op or operator.eq

    # Check that shape of mask_array matches trailing dimensions of data_array.
    if mask_array.shape != data_array.shape[-2:]:
        raise ValueError("Shape of mask_array does not match data_array")

    # Simple case: just mask data_array using mask_array.mask
    if mask_only:
        # check that mask_array is a numpy MaskedArray
        if not ma.isMA(mask_array):
            raise ValueError("Type of mask_array argument must be numpy.MaskedArray")

        tmp_mask = ~mask_array.mask if invert_mask else mask_array.mask

        if data_array.shape != mask_array.shape:
            tmp_mask = np.broadcast_to(tmp_mask, data_array.shape)

        new_array = ma.masked_where(tmp_mask, data_array)

    # Determine the mask from mask_array then apply the np_func operator.
    elif np_func:
        # broadcasting should happen automatically
        new_array = np_func(data_array, ma.masked_where(op(mask_array, compare_value),
            mask_array))

    # Determine the mask from mask_array and use it to mask data_array.
    else:
        if data_array.shape == mask_array.shape:
            new_array = ma.masked_where(op(mask_array, compare_value), data_array)
        else:
            # broadcast mask_array
            tmp_mask = np.broadcast_to(mask_array, data_array.shape)
            new_array = ma.masked_where(op(tmp_mask, compare_value), data_array)

    # Set fill value if one was specified.
    if fill_value is not None and ma.isMA(new_array):
        new_array.set_fill_value(fill_value)

    return new_array


def apply_masked_op_to_array(data_array, mask_array, compare_value, compare_op,
        np_func, fill_value=None):
    """
    Apply a mask-plus-function operation to a NumPy array.

    Mask elements in ``data_array`` based upon a comparison of the values in
    ``mask_array`` with ``compare_value``. The operation defined by ``np_func``
    is then applied to any *unmasked* elements.

    This function is a convenience wrapper around the :func:`apply_mask_to_array`
    function for the case where one wishes to derive a mask from ``mask_array``
    based upon that array's values (rather than any mask that might be attached
    to it). ``mask_array`` can be a plain NumPy array or a MaskedArray object.

    Here's how this function may be used, in a more succinct manner, to apply the
    land-area fraction masking task shown earlier:

    >>> newdata = apply_masked_op_to_array(data, land_area_frac, 0.5, 'lt', np.multiply)

    Refer to the :func:`apply_mask_to_array` function for a description of the
    arguments.

    :returns: A masked data array.
    """
    return apply_mask_to_array(data_array, mask_array, mask_only=False,
        compare_value=compare_value, compare_op=compare_op, np_func=np_func,
        fill_value=fill_value)


def apply_mask_to_cube(cube, mask_array_or_cube, mask_only=True, invert_mask=False,
        compare_value=0, compare_op=None, np_func=None, fill_value=None,
        update_history=False):
    """
    Apply a mask or mask-plus-function operation to an Iris cube's data payload.

    This is basically a convenience wrapper around the :func:`apply_mask_to_array`
    function to enable client code to work with cubes as input arguments.

    :param iris.cube.Cube cube: The cube whose data payload is to be masked (and
        potentially operated on with np_func, if that argument is defined).
    :param mask_array_or_cube: The NumPy array, MaskedArray or Iris cube that is
        used to determine which elements to mask in the cube.data array.
    :param bool update_history: If set to true then the cube's history attribute
        is updated with text stating that the cube's data array has been masked.

    Refer to the :func:`apply_mask_to_array` function for a description of the
    remaining arguments.

    .. note:: The cube's data payload is modified in situ.
    """

    if isinstance(mask_array_or_cube, iris.cube.Cube):
        mask_array = mask_array_or_cube.data
    else:
        mask_array = mask_array_or_cube

    masked_data = apply_mask_to_array(cube.data, mask_array,
        mask_only=mask_only, invert_mask=invert_mask,
        compare_value=compare_value, compare_op=compare_op,
        np_func=np_func, fill_value=fill_value)

    nmasked = ma.count_masked(cube.data)
    cube.data = masked_data
    nmasked = ma.count_masked(cube.data) - nmasked

    if update_history:
        hist = ("Masked the data array - number of elements masked: {}".format(
            nmasked))
        if 'history' in cube.attributes:
            cube.attributes['history'] += ';\n' + hist
        else:
            cube.attributes['history'] = hist


def apply_masked_op_to_cube(cube, mask_array_or_cube, compare_value, compare_op,
        np_func, fill_value=None, update_history=False):
    """
    Apply a mask-plus-function operation to an Iris cube's data payload.

    Mask elements in the ``cube.data array`` based upon a comparison of the values
    in ``mask_array_or_cube`` with ``compare_value``. The operation defined by
    ``np_func`` is then applied to any unmasked elements.

    This function is a convenience wrapper around the :func:`apply_mask_to_cube`
    function for the case where one wishes to apply a masked operation to the
    cube's data payload based upon the array values associated with :attr:`mask_array_or_cube`,
    rather than any mask that might be attached to it. The array associated with
    ``mask_array_or_cube`` can be a plain NumPy array or a MaskedArray object.

    :param iris.cube.Cube cube: The cube whose data payload is to be masked.
    :param mask_array_or_cube: THe NumPy array, MaskedArray or Iris cube that is
        used to determine which elements to mask in the cube.data array.
    :param bool update_history: If set to true then the cube's history attribute
        is updated with text stating that the cube's data array has been masked.

    Refer to the :func:`apply_mask_to_array` function for a description of the
    remaining arguments.

    .. note:: The cube's data payload is modified in situ.
    """
    apply_mask_to_cube(cube, mask_array_or_cube, mask_only=False,
        compare_value=compare_value, compare_op=compare_op, np_func=np_func,
        fill_value=fill_value, update_history=update_history)
