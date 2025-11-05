# (C) British Crown Copyright 2016-2017, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The textutils module contains various utility functions for working with
text strings.

**Index of Functions in this Module**

.. autosummary::
   :nosignatures:

   camel_to_snake_case
   decode_string_value
   int_list_from_string
   ripf_matcher
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import re
import ast

from afterburner.modelmeta import RIPF_REGEX


def decode_string_value(instr):
    """
    Decode the value stored in a string (typically derived from an application
    configuration file) to a value of the appropriate type, e.g. int, float,
    bool, etc. If no type conversion is possible then the original string is
    returned.

    The following special cases are handled:

    * If the input string is equal to 'true' or '.true.' (case-insensitive) then
      the return value is True.
    * If the input string is equal to 'false' or '.false.' (case-insensitive)
      then the return value is False.
    * If the input string contains a comma-separated sequence of numbers (of any
      numeric type) then a tuple containing those numbers is returned. This can
      be disabled by enclosing the number sequence in single or double quotes.

    Here are some examples of invoking this function:

    >>> decode_string_value('true')
    True
    >>> decode_string_value('.false.')
    False
    >>> decode_string_value('0, 1.1, 2.2')
    (0, 1.1, 2.2)
    >>> decode_string_value("'0, 1.1, 2.2'")
    '0, 1.1, 2.2'
    >>> decode_string_value('[1, 1, 2, 3, 5]')
    [1, 1, 2, 3, 5]
    >>> decode_string_value('(1, 1, 2, 3, 5)')
    (1, 1, 2, 3, 5)
    >>> decode_string_value("{'foo': 1, 'bar': 2}")
    {'foo': 1, 'bar': 2}

    :param str instr: The text string to decode.
    :returns: The input value converted to its natural Python type.
    """

    # Return null values as-is.
    if not instr:
        return instr

    # Check for recognised values of true.
    if instr.lower() in ('true', '.true.'):
        value = True

    # Check for recognised values of false.
    elif instr.lower() in ('false', '.false.'):
        value = False

    # Otherwise attempt to evaluate the string as a Python literal.
    else:
        try:
            value = ast.literal_eval(instr)
        except (SyntaxError, ValueError):
            value = instr

    return value


def int_list_from_string(instr, sep=',', unique=False):
    """
    Parse a sequence of integers and/or integer ranges (m-n) from a text string.
    Return the result as a list of integers, with any ranges expanded, and with
    duplicate values removed if ``unique`` is set true. Negative numbers may be
    specified **individually** but not in a range specifier (since -m-n is
    ambiguous).

    Below are some examples of the way in which this function can be invoked:

    >>> int_list_from_string('1,2,3,4,5,6')
    [1, 2, 3, 4, 5, 6]
    >>> int_list_from_string('6,4,2,0,-2,-4')
    [6, 4, 2, 0, -2, -4]
    >>> int_list_from_string('1-5, 8, 10-15, 20')
    [1, 2, 3, 4, 5, 8, 10, 11, 12, 13, 14, 15, 20]
    >>> int_list_from_string('1 2 3 4 5 6', sep=' ')
    [1, 2, 3, 4, 5, 6]

    :param str instr: A text string containing a comma-separated sequence of
        numbers and/or number ranges (m-n).
    :param str sep: The text character (default ',') used to separate successive
        numbers. Setting ``sep`` to None means that integers can be separated by
        any number of whitespace characters.
    :param bool unique: If set to True, duplicate values are removed from the
        returned list. In this case the order of the returned numbers may not
        match their order in the input string.
    :returns: A list containing the integer values decoded from ``instr``.
    :raises ValueError: Raised if the input string is invalid (i.e. does not
        contain a sequence of integers), or the separator character is invalid.
    """
    if sep == '-':
        raise ValueError("Cannot use '-' as the separator character because it\n"
            "is reserved for range definitions, e.g. m-n.")

    instr = instr.strip()
    if not instr:
        raise ValueError("Unable to parse an empty string.")

    ivals = []
    for token in [t.strip() for t in instr.split(sep)]:
        if not token: continue
        try:
            # positive integer range, m-n
            if token.find('-') > 0:
                mn = [int(x) for x in token.split('-')]
                ivals.extend(range(mn[0], mn[1]+1))
            # positive or negative integer
            else:
                ivals.append(int(token))
        except:
            msg = "Cannot parse integer values from string: '{0}'".format(token)
            raise ValueError(msg)

    if unique:
        return list(set(ivals))
    else:
        return ivals


def camel_to_snake_case(text):
    """
    Convert text, typically a tokenised name, from CamelCase to snake_case.

    >>> camel_to_snake_case('OneHumpedDromedary')
    'one_humped_dromedary'
    >>> camel_to_snake_case('twoHumpedDromedary')
    'two_humped_dromedary'

    :param str text: The text string to convert.
    :returns: The case-converted text string.
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def ripf_matcher(ripf_id, rnum=None, inum=None, pnum=None, fnum=None):
    """
    Test to see if the numeric values encoded in a CMIPn-style RIPF ensemble
    identifier match the value(s) specified via the keyword arguments. If any of
    the latter retain the default value of None then they are not used during
    the match. At least one of the arguments must be defined.

    A CMIPn-style ensemble identifier must conform to one of the following
    case-insensitive text formats:

    * 'r<rnum>i<inum>p<pnum>'
    * 'r<rnum>i<inum>p<pnum>f<fnum>'

    A regular expression capable of matching either text format is defined by
    the constant :attr:`afterburner.modelmeta.RIPF_REGEX`. This regex is used
    by the current function.

    Here are some example calls:

    >>> ripf_matcher('r1i2p3', rnum=1)
    True
    >>> ripf_matcher('r1i2p3f4', rnum=1, fnum=4)
    True
    >>> # test values can also be passed as decimal strings
    >>> ripf_matcher('r1i2p3', rnum='1', inum='2', pnum='3')
    True
    >>> # leading zeros in an ensemble id are ignored
    >>> ripf_matcher('r02i01p01f0', rnum=2, pnum=1)
    True
    >>> # ensemble identifiers are not case sensitive
    >>> ripf_matcher('R002I1P00001', rnum=2, inum=1, pnum=1)
    True

    :param str ripf_id: A CMIPn-style RIPF ensemble identifier.
    :param int/str rnum: The realization number, if any, to match.
    :param int/str inum: The initialization number, if any, to match.
    :param int/str pnum: The physics perturbation number, if any, to match.
    :param int/str fnum: The forcings number, if any, to match.
    :returns: True if all of the specified RIPF numbers match the corresponding
        parts of the ``ripf_id`` ensemble identifier. Otherwise false.
    """
    # Check that at least one component number was defined.
    ndefined = len(list(filter(lambda x: x is not None, [rnum, inum, pnum, fnum])))
    if not ndefined:
        return False

    # Check that a valid RIPF identifier was specified.
    match = re.match(RIPF_REGEX, ripf_id)
    if not match:
        return False

    if rnum is not None and int(match.group('rnum')) != int(rnum):
        return False

    if inum is not None and int(match.group('inum')) != int(inum):
        return False

    if pnum is not None and int(match.group('pnum')) != int(pnum):
        return False

    # The F component (forcing) is optional and therefore needs slightly
    # different treatment.
    if fnum is not None:
        if match.group('fnum') is None or int(match.group('fnum')) != int(fnum):
            return False

    return True
