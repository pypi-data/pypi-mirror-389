# (C) British Crown Copyright 2016-2020, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The modelmeta module defines a variety of metadata properties and utility
functions pertinent to climate models recognised by the Afterburner framework.

**Index of Functions in this Module**

.. autosummary::
   :nosignatures:

   cf_cell_method_from_lbproc
   decode_dates_from_cice_filename
   decode_dates_from_nemo_filename
   is_msi_stash_code
   mass_collection_from_stream
   meaning_period_from_stream
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import re
from afterburner.exceptions import UnknownModelNameError

#: Symbolic constant for identifying the UM atmosphere model.
MODEL_UM = "UM"

#: Symbolic constant for identifying the NEMO ocean model.
MODEL_NEMO = "NEMO"

#: Symbolic constant for identifying the CICE sea-ice model.
MODEL_CICE = "CICE"

#: List of climate models currently known to Afterburner software.
KNOWN_MODELS = (MODEL_UM, MODEL_NEMO, MODEL_CICE)

#: Regular expression used to identify CMIPn-compliant ensemble members.
#: Numeric components may be accessed using ``match.group('rnum')``,
#: ``match.group('pnum')``, and so on, assuming ``match`` is a match object
#: returned by ``re.match(RIPF_REGEX, 'ripf_string')``.
RIPF_REGEX = r'[rR](?P<rnum>\d+)[iI](?P<inum>\d+)[pP](?P<pnum>\d+)(?:[fF](?P<fnum>\d+))?$'

#: Regular expression for matching an MSI-style STASH code.
MSI_REGEX = r'm(\d{2})s(\d{2})i(\d{3})$'

# Dictionary of mappings from selected LBPROC codes to CF cell method names.
_LBPROC_TO_CELL_METHOD_NAME = {0: 'point', 128: 'mean', 4096: 'minimum', 8192: 'maximum',
    65536: 'variance'}


def cf_cell_method_from_lbproc(lbproc):
    """
    Return the name of the CF cell method corresponding to the specified LBPROC
    header value as used, for example, in UM fieldsfiles and PP files.

    Currently, the following LBPROC values (and their corresponding methods) are
    recognised:

    * 0 (point)
    * 128 (mean)
    * 4096 (minimum)
    * 8192 (maximum)
    * 65536 (variance)

    :param int lbproc: The LBPROC header value, e.g. 128 for a time-mean.
    :returns: The name of the CF cell method corresponding to LBPROC, or an
        empty string if there is no corresponding method.
    """
    return _LBPROC_TO_CELL_METHOD_NAME.get(lbproc, '')


def is_msi_stash_code(stash_code):
    """
    Tests whether the string ``stash_code`` contains a MSI-formatted STASH code.
    Leading or trailing whitespace is significant: if required, the ``string.strip()``
    method may be used to strip off extraneous whitespace from the passed-in
    string.

    >>> is_msi_stash_code('m01s03i236')
    True
    >>> is_msi_stash_code(' m01s03i236 ')
    False
    >>> is_msi_stash_code(' m01s03i236 '.strip())
    True
    >>> is_msi_stash_code('m1s03i236')
    False

    :param str stash_code: The string to test.
    :returns: True if ``stash_code`` is a MSI-style STASH code, else False.
    """
    return re.match(MSI_REGEX, stash_code) is not None


def mass_collection_from_stream(model_name, stream_id):
    """
    Return the name of the MASS collection corresponding to the specified model
    and stream.

    :param str model_name: Name of the parent climate model. Client code should
        specify the model using one of the MODEL_xxx constants defined at the
        top of this module.
    :param str stream_id: Stream identifier, e.g. 'apy', 'ons', 'inm'.
    :returns: The name of the MASS collection.
    """
    if model_name not in KNOWN_MODELS:
        raise UnknownModelNameError("Unrecognised model name: " + model_name)

    if model_name == MODEL_UM:
        return stream_id + '.pp'
    elif model_name in (MODEL_NEMO, MODEL_CICE):
        return stream_id + '.nc.file'


def meaning_period_from_stream(stream_id, as_num_days=False):
    """
    Return information about the meaning/aggregation period corresponding to the
    specified stream. Some example calls are shown below:

    >>> meaning_period_from_stream('apy')
    (1, 'years', '1y')
    >>> meaning_period_from_stream('apy', as_num_days=True)
    (360, 'days', '1y')
    >>> meaning_period_from_stream('ons')
    (3, 'months', '3m')
    >>> meaning_period_from_stream('ons', as_num_days=True)
    (90, 'days', '3m')
    >>> meaning_period_from_stream('inm')
    (1, 'months', '1m')
    >>> meaning_period_from_stream('inm', as_num_days=True)
    (30, 'days', '1m')

    :param str stream_id: Stream identifier, e.g. 'apy', 'ons', 'inm'.
    :param bool as_num_days: If true then the duration of the meaning period is
        returned in units of days (assumes a 360-day calendar). Otherwise the
        canonical units for the meaning period are returned, e.g. months or years.
    :returns tuple: The 3-tuple (count, time_units, abbrev), where `count` is the
        number of time units, `time_units` is currently one of 'days', 'months' or
        'years', and `abbrev` is a handy text abbreviation for the duration of the
        meaning period, e.g. '3m' for a seasonal mean.
    """
    time_units = {'d': 'days', 'm': 'months', 'y': 'years'}

    # Meaning period abbreviations and day-lengths (assuming a 360-day calendar)
    # for various streams.
    meaning_periods = {
        'a': ('1d', 1), 'b': ('1d', 1), 'c': ('1d', 1), 'd': ('1d', 1),
        'e': ('1d', 1), 'f': ('1d', 1), 'g': ('1d', 1), 'h': ('1d', 1),
        'i': ('1d', 1), 'j': ('1d', 1), 'k': ('1d', 1),
        'p': ('5d', 5), 'w': ('7d', 7), 't': ('10d', 10), 'r': ('14d', 14),
        'm': ('1m', 30), 's': ('3m', 90),
        'y': ('1y', 360), 'v': ('5y', 1800), 'x': ('10y', 3600),
        'l': ('50y', 18000), 'u': ('100y', 36000), 'z': ('1000y', 360000),
        '1': ('1d', 1), '2': ('1d', 1), '3': ('1d', 1), '4': ('1d', 1)
    }

    mp_letter = stream_id[-1]
    if mp_letter not in meaning_periods:
        raise ValueError("Unrecognised stream identifier: %s" % stream_id)

    if as_num_days:
        abbrev, count = meaning_periods[mp_letter]
        units = 'days'
    else:
        abbrev, ndays = meaning_periods[mp_letter]
        count = int(abbrev[:-1])
        units = time_units[abbrev[-1]]

    return (count, units, abbrev)


def decode_dates_from_nemo_filename(filename):
    """
    Decode date-time information from a filename generated by the NEMO ocean
    model (or, more often, by an associated post-processing script). The returned
    date-time values are as encoded in the filename: no attempt is currently made
    to round dates to, say, meaning period boundaries.

    Note that the dates in some NEMO files do not always accurately reflect the
    actual time period spanned by the data contained within the file. For example,
    end dates may be encoded as midnight Nov 30 when midnight Dec 1 would in fact
    be the correct date if CF-compliance was being observed.

    :param str filename: The name of the file from which to decode date-time
        information.
    :returns: The tuple (start_datetime, end_datetime), where each item is either
        a string in ISO 8601 format, or else None if the corresponding date-time
        values could not be decoded from the passed in filename.
    """
    stt_dts = end_dts = None

    # Define regular expressions for postproc v1 & v2 NEMO filenames
    regexes = [
        r'.+_(\d{8})_(\d{8})_(.+)\.nc$',   # postproc_vn1 pattern
        r'.+_(\d{8})-(\d{8})_(.+)\.nc$',   # postproc_vn2 pattern
    ]

    for regex in regexes:
        mtch = re.match(regex, filename)
        if mtch:
            stt_date = mtch.group(1)
            stt_dts = "{0}-{1}-{2}T00:00:00".format(stt_date[:4],
                stt_date[4:6], stt_date[6:8])
            end_date = mtch.group(2)
            end_dts = "{0}-{1}-{2}T00:00:00".format(end_date[:4],
                end_date[4:6], end_date[6:8])

    return (stt_dts, end_dts)


def decode_dates_from_cice_filename(filename):
    """
    Decode date-time information from a filename generated by the CICE ocean
    model (or, more often, by an associated post-processing script). The returned
    date-time values are as encoded in the filename: no attempt is currently made
    to round dates to, say, meaning period boundaries.

    Note that the dates in some CICE files do not always accurately reflect the
    actual time period spanned by the data contained within the file. For example,
    end dates may be encoded as midnight Nov 30 when midnight Dec 1 would in fact
    be the correct date if CF-compliance was being observed.

    :param str filename: The name of the file from which to decode date-time
        information.
    :returns: The tuple (start_datetime, end_datetime), where each item is either
        a string in ISO 8601 format, or else None if the corresponding date-time
        values could not be decoded from the passed in filename.
    """
    stt_dts = end_dts = None

    # Define regular expressions for postproc v1 & v2 CICE filenames
    re1 = r'.+(\d{4})-(\d{2})\.nc$'    # postproc_vn1 pattern
    re2 = r'.+_(\d{8})-(\d{8})\.nc$'   # postproc_vn2 pattern

    mtch = re.match(re1, filename)
    if mtch:
        # postproc_vn1 filenames only encode the (approximate) end date
        end_yy = mtch.group(1)
        end_mm = mtch.group(2)
        end_dd = '30'   # assumes a 360-day calendar
        end_dts = "{0}-{1}-{2}T00:00:00".format(end_yy, end_mm, end_dd)
        return (stt_dts, end_dts)

    mtch = re.match(re2, filename)
    if mtch:
        stt_date = mtch.group(1)
        stt_dts = "{0}-{1}-{2}T00:00:00".format(stt_date[:4], stt_date[4:6],
            stt_date[6:8])
        end_date = mtch.group(2)
        end_dts = "{0}-{1}-{2}T00:00:00".format(end_date[:4], end_date[4:6],
            end_date[6:8])

    return (stt_dts, end_dts)
