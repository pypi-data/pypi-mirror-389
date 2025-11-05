# (C) British Crown Copyright 2016-2021, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Assorted date-time utility functions and classes.

**Index of Classes and Functions in this Module**

.. autosummary::
   :nosignatures:

   DateTimeRange
   ImmutableDateTime
   pdt_from_date_string
   pdt_to_date_string
   pdt_to_nc_datetime
   pdt_compare
   parse_ymd_string
   parse_hms_string
   round_date_to_stream_boundary
   round_date_down
   round_date_up
   is_valid_datetime_format
   ordinal_day_of_year
   ordinal_datetime
   moose_date_to_iso_date
   iso_date_to_moose_date
   iter_date_chunks
   iter_dates
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import string_types

import re
import copy
import operator
import cf_units
import datetime
import numpy as np

try:
    import cftime as cft
except ImportError:
    import netcdftime as cft

import iris
from iris.time import PartialDateTime as PDT

from afterburner.exceptions import CoordinateError
from afterburner.modelmeta import meaning_period_from_stream
from afterburner.utils import (INTERVAL_OPEN, INTERVAL_LEFTOPEN,
    INTERVAL_LEFTCLOSED, INTERVAL_CLOSED)

# Associate calendar identifiers with possible netcdftime package class names.
# Depending on the version of the netcdftime package being used, these classes
# may or may not be present.
CALENDAR_CLASS_MAP = {
    cf_units.CALENDAR_STANDARD: 'DatetimeGregorian',
    cf_units.CALENDAR_GREGORIAN: 'DatetimeGregorian',
    cf_units.CALENDAR_PROLEPTIC_GREGORIAN: 'DatetimeProlepticGregorian',
    cf_units.CALENDAR_360_DAY: 'Datetime360Day',
    cf_units.CALENDAR_365_DAY: 'DatetimeNoLeap',
    cf_units.CALENDAR_366_DAY: 'DatetimeAllLeap',
    cf_units.CALENDAR_ALL_LEAP: 'DatetimeAllLeap',
    cf_units.CALENDAR_NO_LEAP: 'DatetimeNoLeap',
}

# Regular expressions for broadly defined date and time strings, including an
# optional +/- sign, and year > 9999 in the case of dates. Afterburner mostly
# works with these date-time forms, which are broadly CF & ISO-8601 compliant.
BROAD_DATE_REGEX = r'[-+]?\d{4,}-\d{2}-\d{2}'
BROAD_TIME_REGEX = r'\d{2}:\d{2}(:\d{2})?'
BROAD_DATETIME_REGEX = BROAD_DATE_REGEX + '[ T]' + BROAD_TIME_REGEX

# Regular expressions for ISO-8601-like date and time strings. Dates with
# negative years are not matched.
ISO_DATE_REGEX = r'\d{4,}-\d{2}-\d{2}'
ISO_TIME_REGEX = r'\d{2}:\d{2}:\d{2}'
ISO_DATETIME_REGEX = ISO_DATE_REGEX + 'T' + ISO_TIME_REGEX
ISO_STRICT_DATE_REGEX = r'\d{4}-\d{2}-\d{2}'

# Regular expressions for MOOSE-supported date and time strings.
MOOSE_DATE_REGEX = r'\d{1,}/\d{2}/\d{2}'
MOOSE_TIME_REGEX = r'\d{2}:\d{2}(:\d{2})?'
MOOSE_DATETIME_REGEX = MOOSE_DATE_REGEX + ' ' + MOOSE_TIME_REGEX

# Largest value of year able to be used in an ImmutableDateTime object.
MAX_YEAR_VALUE = 999999


class ImmutableDateTime(object):
    """
    Class for representing an immutable date-time value. Instance objects possess
    the following read-only attributes: year, month, day, hour, minute, second,
    and microsecond. The last of these attributes is always set to zero and is
    included primarily to support comparisons with other date-time objects which
    possess this attribute.

    .. tip:: Within recent versions of the netcdftime package (v1.4 or later?),
       instances of the various datetime classes have changed from being mutable
       to being immutable. As such, those classes represent a potential alternative
       solution - albeit one with different behaviours - to that provided by the
       current class.

    The year attribute can be any positive or negative integer, or zero. The
    remaining date and time attributes take on their usual range-limited integer
    values. Note that ImmutableDateTime objects are neither timezone nor calendar
    aware.

    Instances of ImmutableDateTime can be compared with other objects that
    possess the aforementioned date and time attributes, including instances of
    iris.time.PartialDateTime, netcdftime.datetime and datetime.datetime, as
    illustrated below:

    >>> idt = ImmutableDateTime(1970, 1, 1)
    >>> pdt = iris.time.PartialDateTime(1960, 1, 1)
    >>> idt == pdt
    False
    >>> idt > pdt
    True

    >>> ndt = cft.datetime(1970, 1, 1, 12, 0, 0)
    >>> idt == ndt
    False
    >>> idt < ndt
    True

    .. note:: These and similar comparison operations are believed to be reliable
       when the ImmutableDateTime object is the *left-most* operand. If a date-time
       object of a different type is the left-most operand then certain comparison
       operations (e.g. > or <) may raise an exception. This is known to be the
       case with datetime.datetime objects.

    The ``str()`` method and, in its default form, the ``strftime()`` method return
    date-time strings in the same format as that used by netcdftime.datetime and
    datetime.datetime instance objects:

    >>> str(idt)
    '1970-01-01 00:00:00'
    >>> idt.strftime()
    '1970-01-01 00:00:00'

    The ``isoformat()`` method may be used to return a date-time string in ISO 8601
    format:

    >>> idt.isoformat()
    '1970-01-01T00:00:00'

    A couple of examples of the use of the ImmutableDateTime class can be found
    in the symbolic constants :data:`DATETIME_POS_INF` and :data:`DATETIME_NEG_INF`.
    """
    __hash__ = None

    def __init__(self, year, month=1, day=1, hour=0, minute=0, second=0):
        """
        :param int year: The year. Can be zero or negative in addition to the
            customary positive values.
        :param int month: The month of the year from 1..12.
        :param int day: The day of the month from 1..31.
        :param int hour: The hour of the day from 0..23.
        :param int minute: The minute from 0..59.
        :param int second: The second from 0..59.
        :raises ValueError: Raised if an invalid value is supplied for any of
            the input arguments.
        """
        assert 1 <= month <= 12, "ImmutableDateTime: month argument must be " \
            "between 1 and 12."
        assert 1 <= day <= 31, "ImmutableDateTime: day argument must be " \
            "between 1 and 31."
        assert 0 <= hour <= 23, "ImmutableDateTime: hour argument must be " \
            "between 0 and 23."
        assert 0 <= minute <= 59, "ImmutableDateTime: minute argument must be " \
            "between 0 and 59."
        assert 0 <= second <= 59, "ImmutableDateTime: second argument must be " \
            "between 0 and 59."

        # Store the date-time values in a netcdftime.datetime object so that we
        # can invoke useful methods such as strftime().
        _proxy_dt = cft.datetime(year, month, day, hour, minute, second)
        if not hasattr(_proxy_dt, 'microsecond'): _proxy_dt.microsecond = 0
        object.__setattr__(self, '_proxy_dt', _proxy_dt)

    def __setattr__(self, *args):
        raise AttributeError("Attributes of class %s cannot be set or modified" \
            % type(self).__name__)

    def __delattr__(self, *args):
        raise AttributeError("Attributes of class %s cannot be deleted" \
            % type(self).__name__)

    def __repr__(self):
        attr_pieces = ['{}={}'.format(name, getattr(self, name)) for name in
            ['year', 'month', 'day', 'hour', 'minute', 'second']]
        result = '{}({})'.format(type(self).__name__, ', '.join(attr_pieces))
        return result

    def __str__(self):
        result = "{0.year:04d}-{0.month:02d}-{0.day:02d} {0.hour:02d}:" \
            "{0.minute:02d}:{0.second:02d}".format(self._proxy_dt)
        return result

    def __eq__(self, other):
        return pdt_compare(self, 'eq', other)

    def __ne__(self, other):
        return pdt_compare(self, 'ne', other)

    def __le__(self, other):
        return pdt_compare(self, 'le', other)

    def __lt__(self, other):
        return pdt_compare(self, 'lt', other)

    def __ge__(self, other):
        return pdt_compare(self, 'ge', other)

    def __gt__(self, other):
        return pdt_compare(self, 'gt', other)

    def __format__(self, format='%Y-%m-%d %H:%M:%S'):
        return self.strftime(format=format)

    def strftime(self, format='%Y-%m-%d %H:%M:%S'):
        """
        Return a string representation of the date-time value formatted according
        to the specified format argument. Refer to Python's description of the
        `strftime function <https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior>`_
        for details regarding recognised formatting directives.
        """
        return self._proxy_dt.strftime(format=format)

    def isoformat(self):
        """
        Return a string representation of the date-time value in ISO 8601 format.
        """
        result = "{0.year:04d}-{0.month:02d}-{0.day:02d}T{0.hour:02d}:" \
            "{0.minute:02d}:{0.second:02d}".format(self._proxy_dt)
        return result

    @property
    def year(self):
        """The year component of the date-time value (read-only)."""
        return self._proxy_dt.year

    @property
    def month(self):
        """The month component of the date-time value (read-only)."""
        return self._proxy_dt.month

    @property
    def day(self):
        """The day component of the date-time value (read-only)."""
        return self._proxy_dt.day

    @property
    def hour(self):
        """The hour component of the date-time value (read-only)."""
        return self._proxy_dt.hour

    @property
    def minute(self):
        """The minute component of the date-time value (read-only)."""
        return self._proxy_dt.minute

    @property
    def second(self):
        """The second component of the date-time value (read-only)."""
        return self._proxy_dt.second

    @property
    def microsecond(self):
        """The microsecond component of the date-time value. Always set to zero."""
        return self._proxy_dt.microsecond


#: Symbolic constant representing positive infinity for date-time objects.
DATETIME_POS_INF = ImmutableDateTime(MAX_YEAR_VALUE, 9, 9, 9, 9, 9)

#: Symbolic constant representing negative infinity for date-time objects.
DATETIME_NEG_INF = ImmutableDateTime(-MAX_YEAR_VALUE, 9, 9, 9, 9, 9)

#: Symbolic constant representing a standard climate meaning reference date.
CMR_DATE = ImmutableDateTime(1859, 12, 1, 0, 0, 0)


class DateTimeRange(object):
    """
    The DateTimeRange class represents a date-time range as start and end
    date-time instants.

    Instance objects are initialised using either ISO 8601 or CF style date-time
    strings. Some examples include '1970-01-01T12:00:00', '1970-01-01 00:00',
    and '1970-01-01'. Any missing time components are set to zero.

    The start date-time must be less than or equal to the end date-time. If the
    two values are set equal then the behaviour is client-dependent.

    Instances of this class also store the start and end date-times as Iris
    PartialDateTime objects: see :attr:`start_pdt` and :attr:`end_pdt`. These
    attributes get updated automatically if the :attr:`start` or :attr:`end`
    attributes are modified (it is envisaged, however, that instances will often
    be used in a read-only capacity once they have been created).

    A calendar type (default: Gregorian) is associated with each instance object.
    And while this class does not currently provide calendar-aware date arithmetic,
    recording the calendar type does allow clients to do so should the need
    arise.

    As a convenience, the start and end attributes can be accessed using slice
    notation (in addition, that is, to the familiar ``obj.attr`` dot notation).
    The following code fragment below illustrates these two access methods using
    simple date-only initial input values::

        >>> dtr = DateTimeRange('1970-01-01', '1971-01-01')
        >>> dtr.start
        '1970-01-01'
        >>> dtr.end
        '1971-01-01'
        >>> dtr[0]
        '1970-01-01'
        >>> dtr[1]
        '1971-01-01'
        >>> dtr[:]
        ['1970-01-01', '1971-01-01']
        >>> dtr.start_pdt.year
        1970
        >>> dtr.start_pdt.hour
        0
        >>> dtr.end_pdt.year
        1971
        >>> dtr.end_pdt.minute
        0

    If the start date or the end date is passed a value of None then it is reset
    to the date-time equivalent of negative or positive infinity, respectively::

        >>> dtr = DateTimeRange(None, '1970-01-01')
        >>> str(dtr)
        '-999999-09-09T09:09:09 1970-01-01T00:00:00'
        >>> dtr = DateTimeRange('1970-01-01', None)
        >>> str(dtr)
        '1970-01-01T00:00:00 999999-09-09T09:09:09'

    Finally, the start and/or end date-times may be converted to CF-style numeric
    values by passing the relevant datetime attribute, i.e. :attr:`start_ncdt`
    or :attr:`end_ncdt`, together with the desired units and calendar type, to the
    ``cf_units.date2num()`` function. For example::

        >>> dtr = DateTimeRange('1970-01-01', '1971-01-01')
        >>> ndays = cf_units.date2num(dtr.start_ncdt, 'days since 1959-12-01', '360_day')
        >>> ndays
        3630.0
    """

    def __init__(self, start, end, calendar=None, interval_type=None):
        """
        :param str start: A CF or ISO 8601-like date-time string representing
            the start date-time. Date-time strings should adhere to the format
            'YYYY-MM-DD[Thh[:mm[:ss]]]'. A single space character may be used
            in place of the 'T' separator character. If ``start`` is set equal
            to None then it is reset to the date-time equivalent of negative
            infinity as defined by the constant :data:`DATETIME_NEG_INF`.
        :param str end: A CF or ISO 8601-like date-time string representing
            the end date-time. Recognised date-time formats are as described
            under the ``start`` argument. If ``end`` is set equal to None then
            it is reset to the date-time equivalent of positive infinity as
            defined by the constant :data:`DATETIME_POS_INF`.
        :param str calendar: Defines the calendar associated with the start and
            end dates. Permissible values are those defined by constants having
            the prefix ``CALENDAR_`` in the cf_units module. If unspecified
            then the Gregorian calendar is assumed.
        :param str interval_type: The type of mathematical interval represented
            by the date-time range. One of 'open', 'leftopen', 'leftclosed' (the
            default), or 'closed'.
        """
        # Check that at least one of start date or end date is defined.
        if not (start or end):
            raise ValueError("Neither the start date nor the end date is specified.")

        # Replace a null-valued start or end date with negative or positive infinity.
        if start is None: start = DATETIME_NEG_INF.isoformat()
        if end is None: end = DATETIME_POS_INF.isoformat()

        # Check that input date-times are valid.
        if not is_valid_datetime_format(start):
            raise ValueError("Invalid start date-time string: '%s'" % start)
        if not is_valid_datetime_format(end):
            raise ValueError("Invalid end date-time string: '%s'" % end)

        # Convert date-time strings to Iris PartialDateTime (PDT) objects.
        self._start_pdt = pdt_from_date_string(start, default=0)
        self._end_pdt = pdt_from_date_string(end, default=0)

        # Check that start date is not later than end date.
        if pdt_compare(self._start_pdt, 'gt', self._end_pdt):
            raise ValueError("Start date ({0}) is later than "
                "end date ({1}).".format(start, end))

        # Check that a user-defined calendar is valid.
        if calendar and calendar not in cf_units.CALENDARS:
            raise ValueError("Invalid calendar type: %s" % calendar)

        self._start = start
        self._end = end
        self._start_ncdt = self._end_ncdt = None

        #: The calendar type associated with this date-time range.
        self.calendar = calendar or cf_units.CALENDAR_GREGORIAN

        #: The interval type represented by this date-time range. The default
        #: setting is 'leftclosed'.
        self.interval_type = interval_type or INTERVAL_LEFTCLOSED

    @staticmethod
    def from_datetime(start_dt, end_dt, calendar=None, interval_type=None):
        """
        Create a DateTimeRange object from start and end datetime-like objects,
        e.g. instances of datetime.datetime, netcdftime.datetime, or
        iris.time.PartialDateTime.

        :param datetime start_dt: The start date-time.
        :param datetime end_dt: The end date-time.
        :param str calendar: Defines the calendar associated with the start and
            end dates. Permissible values are those defined by constants having
            the prefix ``CALENDAR_`` in the cf_units module. If unspecified then
            an attempt is made to determine the calendar type from the input
            datetime objects. If that search draws a blank then the Gregorian
            calendar is assumed as the default.
        :param str interval_type: The type of mathematical interval represented
            by the date-time range. One of 'open', 'leftopen', 'leftclosed' (the
            default), or 'closed'.
        :raises ValueError: Raised if either of the start or end date-time
            objects is invalid.
        """
        start = pdt_to_date_string(start_dt)
        end = pdt_to_date_string(end_dt)

        # If the calendar is not specified by the caller, try and determine it
        # from the input datetime objects.
        if not calendar:
            start_cal = getattr(start_dt, 'calendar', None)
            end_cal = getattr(end_dt, 'calendar', None)
            if start_cal and end_cal and start_cal == end_cal:
                calendar = start_cal

        return DateTimeRange(start, end, calendar=calendar,
            interval_type=interval_type)

    @staticmethod
    def from_cube(cube, time_coord_name='time', use_bounds=False, interval_type=None):
        """
        Create a DateTimeRange object from the time coordinates associated with
        the specified cube. By default the date-time range is determined from the
        cube's regular time coordinates. If the ``use_bounds`` argument is set
        to true then the coordinate bounds are used instead. If necessary the
        bounds will be guessed - assuming there are least 2 time coordinates.
        If not, then the date-time range will be equivalent to the single time
        coordinate.

        If a particular calendar type (e.g. 360-day) is associated with the cube's
        time dimension then it is copied over to the returned DateTimeRange object.

        :param iris.cube.Cube: The cube from which to obtain the date-time range.
        :param str time_coord_name: The name of the cube's time coordinate.
        :param bool use_bounds: If set to true then the coordinate cell bounds,
            rather than the coordinate points, will be used to determine the
            date-time range.
        :param str interval_type: The type of mathematical interval represented
            by the date-time range. One of 'open', 'leftopen', 'leftclosed' (the
            default), or 'closed'.
        :raises CoordinateError: Raised if the named coordinate is not 1d, or is
            not based on time-since-x style units.
        """
        tcoord = cube.coord(time_coord_name)
        if tcoord.ndim != 1:
            msg = "Coordinate named '{}' is not 1-dimensional.".format(time_coord_name)
            raise CoordinateError(msg)

        tunits = tcoord.units
        if not tunits.is_time_reference():
            msg = "Coordinate named '{}' is not based on a reference time.".format(
                time_coord_name)
            raise CoordinateError(msg)

        if use_bounds:
            if not tcoord.has_bounds() and len(tcoord.points) > 1:
                tcoord.guess_bounds()
            if tcoord.has_bounds():
                start_dt = tunits.num2date(tcoord.bounds[0,0])
                end_dt = tunits.num2date(tcoord.bounds[-1,1])
            else:
                start_dt = tunits.num2date(tcoord.points[0])
                end_dt = tunits.num2date(tcoord.points[-1])
        else:
            start_dt = tunits.num2date(tcoord.points[0])
            end_dt = tunits.num2date(tcoord.points[-1])

        start = pdt_to_date_string(start_dt)
        end = pdt_to_date_string(end_dt)

        return DateTimeRange(start, end, calendar=tunits.calendar,
            interval_type=interval_type)

    @property
    def start(self):
        """The start date-time string."""
        return self._start

    @start.setter
    def start(self, dt_str):
        """Set the start date-time to ``dt_str``."""
        if not is_valid_datetime_format(dt_str):
            raise ValueError("Invalid start date-time string: '%s'" % dt_str)

        # Check that start date is not later than end date.
        pdt = pdt_from_date_string(dt_str, default=0)
        if pdt_compare(pdt, 'gt', self._end_pdt):
            raise ValueError("Start date would be later than end date.")

        self._start = dt_str
        self._start_pdt = pdt
        self._start_ncdt = None

    @property
    def end(self):
        """The end date-time string."""
        return self._end

    @end.setter
    def end(self, dt_str):
        """Set the end date-time to ``dt_str``."""
        if not is_valid_datetime_format(dt_str):
            raise ValueError("Invalid end date-time string: '%s'" % dt_str)

        # Check that end date is not earlier than start date.
        pdt = pdt_from_date_string(dt_str, default=0)
        if pdt_compare(pdt, 'lt', self._start_pdt):
            raise ValueError("End date would be earlier than start date.")

        self._end = dt_str
        self._end_pdt = pdt
        self._end_ncdt = None

    @property
    def start_pdt(self):
        """The start date-time as an Iris PartialDateTime object."""
        return self._start_pdt

    @property
    def end_pdt(self):
        """The end date-time as an Iris PartialDateTime object."""
        return self._end_pdt

    @property
    def start_ncdt(self):
        """The start date-time as a netcdftime.datetime object."""
        if not self._start_ncdt:
            self._start_ncdt = pdt_to_nc_datetime(self.start_pdt, self.calendar)
        return self._start_ncdt

    @property
    def end_ncdt(self):
        """The end date-time as a netcdftime.datetime object."""
        if not self._end_ncdt:
            self._end_ncdt = pdt_to_nc_datetime(self.end_pdt, self.calendar)
        return self._end_ncdt

    def __getitem__(self, key):
        # Assumes the object is the length-2 list [self.start, self.end].
        values = [self.start, self.end]
        if isinstance(key, int):
            if key not in range(-2, 2):
                raise IndexError("DateTimeRange: Index is outside range -2..1")
            return values[key]
        elif isinstance(key, slice):
            return values[key]
        else:
            raise TypeError("DateTimeRange: Invalid key type: " + type(key))

    def __str__(self):
        return self.as_string(sep=' ')

    def __repr__(self):
        if self.calendar == cf_units.CALENDAR_GREGORIAN:
            return "DateTimeRange('{0}', '{1}')".format(self.start, self.end)
        else:
            return "DateTimeRange('{0}', '{1}', calendar='{2}')".format(
                self.start, self.end, self.calendar)

    def as_name_token(self, dates_only=False, compact=False):
        """
        Return the date-time range as a string suitable for use as a token in
        a filename. By default the token is returned in ISO-like format, e.g.
        'YYYY-MM-DDThh:mm:ss_YYYY-MM-DDThh:mm:ss'. If the ``compact`` option
        is enabled then the token is built without any separator characters
        in the date and time portions, e.g. 'YYYYMMDDThhmmss_YYYYMMDDThhmmss'.
        The ``dates_only`` option can be used to drop the time elements, e.g.
        'YYYY-MM-DD_YYYY-MM-DD'. These two options may of course be combined.

        If finer-grained control of the output token is required then either
        make use of the :meth:`as_string` method, or apply custom formatting
        directly to the :attr:`start_pdt` and :attr:`end_pdt` attributes.

        :param bool dates_only: If enabled then only the date components are
            encoded in the returned string token.
        :param bool compact: If enabled then no separator characters are used
            within the date and time portions of the returned token.
        """
        if compact:
            ymd_sep, hms_sep = '', ''
        else:
            ymd_sep, hms_sep = '-', ':'

        if dates_only:
            sdt = self._date_as_string(self.start_pdt, ymd_sep=ymd_sep)
            edt = self._date_as_string(self.end_pdt, ymd_sep=ymd_sep)
            return sdt + '_' + edt
        else:
            return self.as_string(ymd_sep=ymd_sep, hms_sep=hms_sep)

    def as_string(self, sep='_', ymd_sep='-', hms_sep=':', dt_sep='T'):
        """
        Return the date-time range as a string in which the start and end dates
        are output, by default, in ISO 8601 format, i.e. YYYY-MM-DDThh:mm:ss.
        The keyword arguments may be used to define the single characters or,
        if desired, longer text strings separating the various elements.

        :param str sep: String used to separate the start and end date-times.
        :param str ymd_sep: String used to separate individual date components.
        :param str hms_sep: String used to separate individual time components.
        :param str dt_sep: String used to separate date and time components.
        """
        sdt = self._date_as_string(self.start_pdt, ymd_sep=ymd_sep) + dt_sep + \
              self._time_as_string(self.start_pdt, hms_sep=hms_sep)
        edt = self._date_as_string(self.end_pdt, ymd_sep=ymd_sep) + dt_sep + \
              self._time_as_string(self.end_pdt, hms_sep=hms_sep)
        return sdt + sep + edt

    def _date_as_string(self, pdt, ymd_sep='-'):
        return "{0:04d}{1}{2:02d}{3}{4:02d}".format(pdt.year, ymd_sep,
            pdt.month, ymd_sep, pdt.day)

    def _time_as_string(self, pdt, hms_sep=':'):
        return "{0:02d}{1}{2:02d}{3}{4:02d}".format(pdt.hour, hms_sep,
            pdt.minute, hms_sep, pdt.second)

    def contains(self, str_or_dt, check_calendar=False, interval_type=None):
        """
        Tests whether or not the date-time instant specified by the ``str_or_dt``
        argument falls within the current date-time range. The containment test
        assumes that the type of interval represented by the date-time range is
        defined by the :attr:`interval_type` attribute (default = 'leftclosed',
        i.e. lower <= x < upper). This may be temporarily overridden, however,
        by setting the ``interval_type`` keyword argument.

        Note that the outcome of the test is determined in a naive manner simply
        by comparing the specified date-time with the end-points of the range.
        In particular, no check is performed to determine whether or not the
        specified date-time is valid for the calendar type associated with the
        current date-time range.

        The ``check_calendar`` keyword may be used, however, to request an extra
        equality check between the calendars associated with ``self`` and
        ``str_or_dt``. If the latter object does not possess a calendar attribute
        (always the case with string-valued dates) then the request is ignored.

        :param str_or_dt: The date-time string or datetime-like object to test
            for containment in the date-time range encoded in ``self``. If a string
            is supplied then it must contain a date-time value in ISO 8601 or CF
            format (refer to :func:`pdt_from_date_string` for examples).
        :param bool check_calendar: If set to true then also check that the
            calendar attributes, if any, associated with ``self`` and ``str_or_dt``
            are equal.
        :param str interval_type: The type of interval represented by the time
            range. One of 'open', 'leftopen', 'leftclosed' (default), or 'closed'.
            If set then the value temporarily overrides the equivalent instance
            attribute of the same name.
        """
        result = False

        if isinstance(str_or_dt, PDT):
            pdt = str_or_dt
        elif isinstance(str_or_dt, (datetime.datetime, cft.datetime)):
            pdt = PDT(str_or_dt.year, str_or_dt.month, str_or_dt.day,
                str_or_dt.hour, str_or_dt.minute, str_or_dt.second)
        elif isinstance(str_or_dt, string_types):
            pdt = pdt_from_date_string(str_or_dt, default=0)
            check_calendar = False
        else:
            raise ValueError("The str_or_dt argument must be a string or a "
                "datetime-like object.")

        if check_calendar:
            other_cal = getattr(str_or_dt, 'calendar', None)
            if other_cal and self.calendar != other_cal:
                return False

        if not interval_type: interval_type = self.interval_type

        if interval_type == INTERVAL_OPEN:
            if pdt_compare(pdt, 'gt', self.start_pdt) and \
               pdt_compare(pdt, 'lt', self.end_pdt):
                result = True
        elif interval_type == INTERVAL_LEFTOPEN:
            if pdt_compare(pdt, 'gt', self.start_pdt) and \
               pdt_compare(pdt, 'le', self.end_pdt):
                result = True
        elif interval_type == INTERVAL_CLOSED:
            if pdt_compare(pdt, 'ge', self.start_pdt) and \
               pdt_compare(pdt, 'le', self.end_pdt):
                result = True
        else:
            if pdt_compare(pdt, 'ge', self.start_pdt) and \
               pdt_compare(pdt, 'lt', self.end_pdt):
                result = True

        return result


def pdt_from_date_string(datestr, default=None):
    """
    Create an iris.time.PartialDateTime object from the date and time values
    encoded in ``datestr``, a CF or ISO 8601-like date-time string that adheres
    to one of the following formats:

    * 'YYYY-MM-DDThh:mm:ss'
    * 'YYYY-MM-DD hh:mm:ss'
    * 'YYYY-MM-DD'
    * 'hh:mm:ss'
    * 'hh:mm'

    If the YYYY-MM-DD part is omitted from ``datestr`` then the year, month
    and day attributes are each assigned the value of ``default``. Similarly
    for the hh:mm:ss part.

    If the minutes and/or seconds specifiers are omitted from the hh:mm:ss part
    then they are assigned the value 0.

    If necessary, individual attributes may be modified on the returned object.

    This function, like the PartialDateTime class itself, is neither timezone-aware
    nor sensitive to calendar type.

    :param str datestr: A date-time string in one of the formats listed above.
    :param default: The default value to assign to date or time elements if they
        are absent from the passed in string.
    :returns: An iris.time.PartialDateTime object whose attributes are set from
        the corresponding elements in ``datestr``.
    :raises ValueError: Raised if an incorrectly formatted date-time string is
        passed in.
    """
    datestr = datestr.strip()
    yy, mm, dd = [default]*3
    hh, mi, ss = [default]*3

    if 'T' in datestr:
        date, time = datestr.split('T')
        yy, mm, dd = parse_ymd_string(date)
        hh, mi, ss = parse_hms_string(time)
    elif ' ' in datestr:
        date, time = datestr.split()
        yy, mm, dd = parse_ymd_string(date)
        hh, mi, ss = parse_hms_string(time)
    elif '-' in datestr[1:]:
        yy, mm, dd = parse_ymd_string(datestr)
    elif ':' in datestr:
        hh, mi, ss = parse_hms_string(datestr)
    else:
        raise ValueError("Invalid date-time string: %s" % datestr)

    datedict = dict(year=yy, month=mm, day=dd, hour=hh, minute=mi, second=ss)

    return iris.time.PartialDateTime(**datedict)


def pdt_to_date_string(pdt):
    """
    Convert an Iris PartialDateTime object, or a plain datetime.datetime object,
    to an ISO 8601 date-time string in the format 'YYYY-MM-DD[Thh[:mm[:ss]]]'.

    :param iris.time.PartialDateTime pdt: The date-time object to convert to
        a string. All date elements must be defined. Time elements are optional;
        any undefined elements will be omitted from the returned string.
    :returns: A date-time string in ISO 8601 format.
    :raises ValueError: Raised if the input date-time object is invalid.
    """
    # Check that the input date-time object has at least a full date definition.
    if None in (pdt.year, pdt.month, pdt.day):
        raise ValueError("Invalid date-time object: '%r'" % pdt)

    # Initialise date-time string using date elements.
    datestr = "{0.year:04d}-{0.month:02d}-{0.day:02d}".format(pdt)

    # Append any time elements that are defined.
    if pdt.hour is not None:
        datestr += 'T'
        time_vals = (pdt.hour, pdt.minute, pdt.second)
        time_vals = filter(lambda x: x is not None, time_vals)
        datestr += ':'.join(['%02d'%x for x in time_vals])

    return datestr


def pdt_to_nc_datetime(pdt, calendar=None):
    """
    Convert an Iris PartialDateTime object to a netcdftime.datetime object.
    Depending on the version of the netcdftime package, the returned object
    may or may not possess a calendar attribute with the appropriate value.

    Note that newer versions of the netcdftime package create datetime objects
    with a calendar setting of 'proleptic_gregorian' by default.

    :param iris.time.PartialDateTime pdt: The date-time object to convert.
        Date elements (YMD) are mandatory. Any null-valued time elements (hms)
        will get set to 0 in the returned datetime object.
    :param str calendar: A cf_units-compatible calendar identifier, such as
        'gregorian' or '360_day'. If set then an attempt is made to return a
        datetime object whose type matches the specified calendar.
    :returns: A netcdftime.datetime object.
    :raises ValueError: Raised if the input date-time object is invalid.
    """
    # Check that the input date-time object has at least a full date definition.
    if None in (pdt.year, pdt.month, pdt.day):
        raise ValueError("Invalid date-time object: '%r'" % pdt)

    # Check that a user-defined calendar is valid.
    if calendar and calendar not in cf_units.CALENDARS:
        raise ValueError("Invalid calendar type: %s" % calendar)

    # Determine which netcdftime class to instantiate.
    klass = cft.datetime
    if calendar in CALENDAR_CLASS_MAP:
        klass = getattr(cft, CALENDAR_CLASS_MAP[calendar], klass)

    # NB: netcdftime objects won't accept None for hour, minute or second.
    ndt = klass(pdt.year, pdt.month, pdt.day,
        hour=pdt.hour or 0, minute=pdt.minute or 0, second=pdt.second or 0)

    return ndt


def pdt_compare(pdt1, op, pdt2):
    """
    Compare two iris.time.PartialDateTime objects. Any None-valued attributes
    on either of the PDT objects are treated as 0. In the case of equality tests
    this means that expressions such as the one shown below return True.

    >>> pdt_compare(PDT(1970, 1, 1), operator.eq, PDT(1970, 1, 1, 0, 0, 0))
    True

    If you need to perform a strict equality test then use Python's standard ==
    operator, e.g. ``pdt1 == pdt2``. (Note that PartialDateTime objects do not
    support greater/less than tests.)

    :param iris.time.PartialDateTime pdt1: The PDT instance object to use as the
        left-hand operand.
    :param func or str op: The comparison operator. Typically this will be one
        of the object comparison functions defined in Python's standard operator
        module. Alternatively it can be the string name of the operator, e.g.
        'lt', 'le', 'gt', 'eq', and so on.
    :param iris.time.PartialDateTime pdt2: The PDT instance object to use as the
        right-hand operand.
    """
    if isinstance(op, string_types):
        op = getattr(operator, op)

    odate1 = ordinal_datetime(pdt1)
    odate2 = ordinal_datetime(pdt2)

    return op(odate1, odate2)


def parse_ymd_string(datestr):
    """
    Parse the year, month and day values from a date string in '[+-]YYYY-MM-DD'
    format. The year component may comprise more than 4 digits and may optionally
    be preceded by a plus or minus sign.

    :param str datestr: A date string in the format '[+-]YYYY-MM-DD'.
    :returns: The list of integers [year, month, day].
    :raises ValueError: Raised if an incorrectly formatted date string is passed in.
    """
    if not re.match(BROAD_DATE_REGEX + '$', datestr):
        raise ValueError("Invalid date string: %s" % datestr)

    if datestr.startswith('-'):
        yy, mm, dd = map(int, datestr[1:].split('-'))
        yy *= -1
    else:
        yy, mm, dd = map(int, datestr.split('-'))

    return [yy, mm, dd]


def parse_hms_string(timestr, default=0):
    """
    Parse the hour, minute and second values from a time string in 'hh[:mm[:ss]]'
    format. Missing elements are assigned the specified default value.

    :param str timestr: A time specification in the format 'hh[:mm[:ss]]'.
    :param int default: The default value to use for missing minute and/or
        second components.
    :returns: The list of integers [hour, minute, second].
    :raises ValueError: Raised if an incorrectly formatted time string is passed in.
    """
    if ':' in timestr:
        hms = list(map(int, timestr.split(':')))
    else:
        # Assumes only the hour value is defined.
        hms = [int(timestr)]

    # If fewer than 3 values decoded, pad out with the default value.
    if len(hms) < 3:
        hms += [default]*2

    return hms[:3]


def round_date_to_stream_boundary(date, stream_id, ref_date=None, end=False):
    """
    Round the specified date to the start or end of the time period within which
    it falls. The time period to use (year, season, month, etc) is determined
    from the specified stream identifer.

    By default the input date is rounded down to the start of the enclosing time
    period. If ``end`` is set to true then the date is rounded up to the end of
    the time period, this being equivalent to the start of the succeeding time
    period.

    By default this function assumes that a model year runs from midnight Dec 1
    to midnight Dec 1 of the following year. If required, this can be changed
    via the ``ref_date`` argument.

    :param iris.time.PartialDateTime pdt: The date to round to the start or end
        of the time meaning/accumulation period associated with ``stream_id``.
        Times of day, if set, are ignored.
    :param str stream_id: The model stream identifier, e.g. 'apy', 'ony'.
    :param iris.time.PartialDateTime ref_date: The reference date to use for
        rounding calculations. The default date is 1859-12-01.
    :param bool end: If set to True then the date is rounded up to the start of
        the succeeding time period.
    :returns: An iris.time.PartialDateTime object rounded to the desired date.
    :raises ValueError: Raised if a valid time period indicator could not be
        deduced from the stream identifier.
    """
    _count, _units, time_period = meaning_period_from_stream(stream_id)

    if end:
        return round_date_up(date, time_period, ref_date=ref_date)
    else:
        return round_date_down(date, time_period, ref_date=ref_date)


def round_date_down(date, time_period, ref_date=None):
    """
    Round the specified date down to the start of the enclosing time meaning
    (or accumulation) period.

    By default this function assumes that a model year runs from midnight Dec 1
    to midnight Dec 1 of the following year. If required, this can be changed
    via the ``ref_date`` argument.

    :param iris.time.PartialDateTime date: The date to round down to the start
        of the enclosing time period. Times of day, if set, are ignored.
    :param str time_period: The time period indicator. Supported values are
        as follows:

        * 'm' or '1m' for monthly-mean periods
        * 's' or '3m' for climatological seasonal-mean periods
        * 'y' or '1y' for annual-mean periods
        * 'Ny' for multi-year meaning periods, where N is the number of years
    :param iris.time.PartialDateTime ref_date: The reference date to use for
        rounding calculations. The default date is 1859-12-01.
    :returns: An iris.time.PartialDateTime object rounded to the desired date.
    :raises ValueError: Raised if the time period indicator is not recognised.
    """
    pdt = copy.copy(date)
    if not ref_date: ref_date = CMR_DATE

    # Convert input date and reference date to day-of-year values.
    doy = ordinal_day_of_year(pdt)
    ref_doy = ordinal_day_of_year(ref_date)

    # 1-year time periods.
    if time_period in ['y', '1y']:
        if doy < ref_doy:
            pdt.year -= 1
        pdt.month = ref_date.month
        pdt.day = ref_date.day

    # Multi-year time periods.
    elif re.match(r'\d+y$', time_period):
        ny = int(time_period[:-1])
        year_offset = (pdt.year-ref_date.year) % ny
        if year_offset:
            pdt.year -= year_offset
        elif doy < ref_doy:
            pdt.year -= ny
        pdt.month = ref_date.month
        pdt.day = ref_date.day

    # Seasonal/3-month time periods.
    elif time_period in ['s', '3m']:
        month_offset = (pdt.month-ref_date.month) % 3
        if month_offset:
            pdt.month -= month_offset
        elif pdt.day < ref_date.day:
            pdt.month -= 3
        if pdt.month < 1:
            pdt.year -= 1        # Decrement if year boundary crossed.
            pdt.month += 12
        pdt.day = ref_date.day

    # 1-month time periods.
    elif time_period in ['m', '1m']:
        if pdt.day < ref_date.day:
            pdt.month -= 1
            if pdt.month < 1:
                pdt.year -= 1    # Decrement if year boundary crossed.
                pdt.month += 12
        pdt.day = ref_date.day

    else:
        raise ValueError("Unrecognised time period indicator: '%s'" % time_period)

    return pdt


def round_date_up(date, time_period, ref_date=None):
    """
    Round the specified date up to the end of the enclosing time meaning
    (or accumulation) period, this being equivalent to the start date of the
    succeeding time period.

    By default this function assumes that a model year runs from midnight Dec 1
    to midnight Dec 1 of the following year. If required, this can be changed
    via the ``ref_date`` argument.

    :param iris.time.PartialDateTime date: The date to round up to the end
        of the specified time period. Times of day, if set, are ignored.
    :param str time_period: The time period indicator. Supported values are:
        as follows:

        * 'm' or '1m' for monthly-mean periods
        * 's' or '3m' for climatological seasonal-mean periods
        * 'y' or '1y' for annual-mean periods
        * 'Ny' for multi-year meaning periods, where N is the number of years
    :param iris.time.PartialDateTime ref_date: The reference date to use for
        rounding calculations. The default date is 1859-12-01.
    :returns: An iris.time.PartialDateTime object rounded to the desired date.
    :raises ValueError: Raised if the time period indicator is not recognised.
    """
    pdt = copy.copy(date)
    if not ref_date: ref_date = CMR_DATE

    # Convert input date and reference date to day-of-year values.
    doy = ordinal_day_of_year(pdt)
    ref_doy = ordinal_day_of_year(ref_date)

    # 1-year time periods.
    if time_period in ['y', '1y']:
        if doy >= ref_doy:
            pdt.year += 1
        pdt.month = ref_date.month
        pdt.day = ref_date.day

    # Multi-year time periods.
    elif re.match(r'\d+y$', time_period):
        ny = int(time_period[:-1])
        year_offset = (pdt.year-ref_date.year) % ny
        if year_offset:
            pdt.year += ny - year_offset
        elif doy >= ref_doy:
            pdt.year += ny
        pdt.month = ref_date.month
        pdt.day = ref_date.day

    # Seasonal/3-month time periods.
    elif time_period in ['s', '3m']:
        pdt.month -= (pdt.month-ref_date.month) % 3
        pdt.month += 3
        if pdt.month > 12:
            pdt.year += 1        # Increment if year boundary crossed.
            pdt.month %= 12
        pdt.day = ref_date.day

    # 1-month time periods.
    elif time_period in ['m', '1m']:
        if pdt.day >= ref_date.day:
            pdt.month += 1
            if pdt.month > 12:
                pdt.year += 1    # Increment if year boundary crossed.
                pdt.month %= 12
        pdt.day = ref_date.day

    else:
        raise ValueError("Unrecognised time period indicator: '%s'" % time_period)

    return pdt


def is_valid_datetime_format(dtstr):
    """
    Test to see if the date-time value defined in ``dtstr`` is in one of the
    formats supported by the Afterburner package. Recognised formats essentially
    follow those prescribed by the `ISO 8601 <https://en.wikipedia.org/wiki/ISO_8601>`_
    standard (specifically the *extended* format 'YYYY-MM-DDThh:mm:ss'), and the
    Climate & Forecast (`CF <http://cfconventions.org/>`_) metadata conventions
    (in which a space character is used in place of the 'T' separator).

    Note that this function does *not* test the validity of any specific date or
    time values, merely the *format* in which they are encoded.

    Note also that none of the currently recognised formats include time zone
    information.

    :param str dtstr: The date, time, or date-time string to test.
    :returns: True if the specified date-time string is in a recognised format,
        else false.

    Some examples of valid date-time formats::

        >>> is_valid_datetime_format('1970-01-01T09:15:30')
        True
        >>> is_valid_datetime_format('1970-01-01 09:15:30')
        True
        >>> is_valid_datetime_format('1970-01-01T09:15')
        True
        >>> is_valid_datetime_format('1970-01-01T09')
        True
        >>> is_valid_datetime_format('1970-02-30')
        True
        >>> is_valid_datetime_format('09:15:30')
        True
        >>> is_valid_datetime_format('09:15')
        True
    """
    if not isinstance(dtstr, string_types): return False

    # Define regular expressions for valid date, time, and date-time strings.
    sep_regex = r'[ T]'
    date_regex = BROAD_DATE_REGEX
    time_regex = BROAD_TIME_REGEX
    datetime_regex = BROAD_DATETIME_REGEX
    datehour_regex = date_regex + sep_regex + r'\d{2}'
    full_regex = datetime_regex + '$|' + datehour_regex + '$|' + \
                 date_regex + '$|' + time_regex + '$'

    match = re.match(full_regex, dtstr)
    return match is not None


def ordinal_day_of_year(pdt):
    """
    Returns an integer-valued ordinal date which can be used as a proxy for
    day-of-year, one that is suitable for simple numeric comparisons.

    :param iris.time.PartialDateTime pdt: The date object from which to compute
        an ordinal date. The month and day elements must be set. All other
        elements are ignored.
    :returns: The computed ordinal date.
    :rtype: int
    """
    return pdt.month * 100 + pdt.day


def ordinal_datetime(pdt):
    """
    Returns an integer-valued ordinal date based on all of the date and time
    attributes (year, month, day, hour, minute, second) defined on the specified
    PDT object.

    :param iris.time.PartialDateTime pdt: The date object from which to compute
        an ordinal date. If a date or time attribute is not defined on the input
        PDT object then a value of 0 is used in its place.
    :returns: The computed ordinal date.
    :rtype: int
    """
    istr = "{0:04d}{1:02d}{2:02d}{3:02d}{4:02d}{5:02d}".format(
        pdt.year or 0, pdt.month or 0, pdt.day or 0,
        pdt.hour or 0, pdt.minute or 0, pdt.second or 0)
    return int(istr)


def moose_date_to_iso_date(moose_date):
    """
    Convert a date-time string from MOOSE format (YYYY/MM/DD [hh:mm[:ss]]) to
    ISO 8601 format (YYYY-MM-DD[Thh:mm:ss]). If the input string only contains
    a date (no time), then the returned string likewise only contains a date.

    Note: In the case of PP-type datasets the year component of a MOOSE date can
    be greater than 9999, but dates less than 1 are prohibited.

    :param str moose_date: The MOOSE date-time string to convert.
    :returns: A date-time string in ISO 8601 format.
    :raises ValueError: Raised if ``moose_date`` does not contain a valid
        MOOSE date-time string.
    """
    if re.match(MOOSE_DATE_REGEX + '$', moose_date):
        iso_date = moose_date.replace('/', '-')
        npad = 10-len(iso_date)
        if npad > 0: iso_date = "{0}{1}".format('0'*npad, iso_date)
    elif re.match(MOOSE_DATETIME_REGEX + '$', moose_date):
        iso_date = moose_date.replace('/', '-')
        iso_date = iso_date.replace(' ', 'T')
        if len(iso_date.split('T')[1]) == 5:
            # append seconds if not present in MOOSE date string
            iso_date += ':00'
        npad = 19-len(iso_date)
        if npad > 0: iso_date = "{0}{1}".format('0'*npad, iso_date)
    else:
        raise ValueError("Invalid MOOSE date-time string: " + moose_date)

    return iso_date


def iso_date_to_moose_date(iso_date, include_secs=False):
    """
    Convert a date-time string from ISO 8601 format (YYYY-MM-DD[Thh:mm:ss]) to
    MOOSE format (YYYY/MM/DD [hh:mm[:ss]]). If the input string only contains
    a date (no time), then the returned string likewise only contains a date.

    :param str iso_date: The ISO date-time string to convert.
    :param include_secs: If set to true then the returned date-time string
        includes the seconds component.
    :returns: A date-time string in MOOSE format.
    :raises ValueError: Raised if ``iso_date`` does not contain a valid
        ISO date-time string.
    """
    if re.match(ISO_DATE_REGEX + '$', iso_date):
        moose_date = iso_date.replace('-', '/')
    elif re.match(ISO_DATETIME_REGEX + '$', iso_date):
        pdt = pdt_from_date_string(iso_date, default=0)
        moose_date = "{0:04d}/{1:02d}/{2:02d} {3:02d}:{4:02d}".format(
            pdt.year, pdt.month, pdt.day, pdt.hour, pdt.minute)
        if include_secs:
            moose_date += ":%02d" % pdt.second
    else:
        raise ValueError("Invalid ISO date-time string: " + iso_date)

    return moose_date


def iter_date_chunks(start_date, end_date, stream_id, calendar=None, padding=True,
        ref_date=None, end_offset=0):
    """
    Generates a sequence of contiguous time meaning/accumulation periods spanning
    a specified time interval.

    Iterates over the time meaning (or accumulation) periods occurring within, or
    overlapping, the time interval spanned by start_date and end_date, yielding
    a :class:`DateTimeRange` object for each such meaning period.

    The length of the meaning periods is determined from the stream_id argument,
    e.g. 3 months for seasonal means. At present only streams based upon monthly,
    seasonal or annual meaning periods can be handled.

    The padding argument may be used to control whether meaning periods that
    overlap the start and/or end dates are included (the default) or excluded.

    :param start_date: Either a CF or ISO 8601-like date-time string, or an
        iris.time.PartialDateTime object, representing the start of the time
        period over which to iterate.
    :param end_date: Either a CF or ISO 8601-like date-time string, or an
        iris.time.PartialDateTime object representing the end of the time period
        over which to iterate.
    :param str stream_id: The model stream identifier, e.g. 'apy', 'ony', 'inm'.
    :param str calendar: Defines the calendar associated with the start and end
        dates. Permissible values are those defined by constants having the
        prefix ``CALENDAR_`` in the cf_units module. If unspecified then the
        Gregorian calendar is assumed.
    :param bool padding: Indicates whether or not to pad out the time chunks to
        cover the full time range. This is enabled by default since it is the
        desired behaviour in most scenarios.
    :param iris.time.PartialDateTime ref_date: The reference date to use for
        rounding calculations. The default date is 1859-12-01.
    :param int end_offset: The offset, in whole hours, to apply to the end
        dates. For example, an offset of -24 might be specified in order to
        facilitate the construction of date strings for use in NEMO filenames
        prior to postproc-2.0. By default no offset is applied.
    :returns: Yields a DateTimeRange object for each meaning period contained
        within, or overlapping, the time interval.
    """
    iso_fmt = '%Y-%m-%dT%H:%M:%S'

    # Convert input dates from strings to PDT objects, if necessary.
    if isinstance(start_date, string_types):
        start_date = pdt_from_date_string(start_date)
    if isinstance(end_date, string_types):
        end_date = pdt_from_date_string(end_date)

    # Check that a user-defined calendar is valid.
    if calendar and calendar not in cf_units.CALENDARS:
        raise ValueError("Invalid calendar type: %s" % calendar)

    # Define reference units to use for date conversions.
    if not calendar: calendar = cf_units.CALENDAR_GREGORIAN
    tunits = cf_units.Unit('hours since {:04d}-01-01 00:00:00'.format(start_date.year-1),
        calendar=calendar)

    # Convert the end date to a numeric coordinate.
    end_coord = tunits.date2num(pdt_to_nc_datetime(end_date))

    # Calculate the date at the beginning or, if padding is disabled, the end of
    # the first meaning period.
    epdt = round_date_to_stream_boundary(start_date, stream_id, ref_date=ref_date)
    if not (epdt == start_date or padding):
        epdt = round_date_to_stream_boundary(start_date, stream_id, ref_date=ref_date,
            end=True)
    ecoord = tunits.date2num(pdt_to_nc_datetime(epdt))

    # Loop over successive time chunks until the end date is reached.
    max_iter = 1000000
    niter = 0
    while ecoord < end_coord and niter < max_iter:
        niter += 1
        spdt = epdt
        epdt = round_date_to_stream_boundary(spdt, stream_id, ref_date=ref_date,
            end=True)

        scoord = tunits.date2num(pdt_to_nc_datetime(spdt))
        ecoord = tunits.date2num(pdt_to_nc_datetime(epdt))

        if ecoord > end_coord and not padding:
            # break out if the current time chunk extends beyond the end date
            # and padding is disabled.
            break

        # Convert start and end of current chunk to datetime objects.
        sdate = tunits.num2date(scoord)
        edate = tunits.num2date(ecoord + end_offset)   # apply offset to end date

        yield DateTimeRange(sdate.strftime(iso_fmt), edate.strftime(iso_fmt),
            calendar=calendar)


def iter_dates(start_date, end_date, step=1, endpoint=False, time_units=None,
        return_nums=False, num_dtype=np.float64):
    """
    Generates a sequence of datetime objects or numeric time-since-refdate values
    spanning a time interval at a given time step.

    This generator function yields a sequence of datetime objects or, if
    ``return_nums`` is True, numeric timeunits-since-refdate values, covering the
    *left-closed time interval* defined by ``start_date`` and ``end_date``.

    If the ``endpoint`` argument is enabled, however, then the time interval is
    treated as as a *closed interval*, meaning that the end date is included *if*
    it falls on a step boundary.

    Internally, the function calculates date-time instants as whole seconds since
    an 1800-01-01 reference date. The ``time_units`` argument may be used, in
    combination with the ``return_nums`` argument, to yield ordinal time values
    in some other user-defined time units.

    Example usage yielding datetime objects at daily intervals:

    >>> it = iter_dates('1970-03-01', '1970-06-01')
    >>> next(it)
    datetime.datetime(1970, 3, 1, 0, 0)
    >>> next(it)
    datetime.datetime(1970, 3, 2, 0, 0)
    >>> for x in it: pass   # iterate to final value
    >>> x
    datetime.datetime(1970, 5, 31, 0, 0)

    Example usage yielding 360-day calendar datetime objects at 10-day intervals:

    >>> units = cf_units.Unit('days since 1970-01-01', calendar='360_day')
    >>> it = iter_dates('1970-03-01', '1970-06-01', step=10, time_units=units,
    ...     endpoint=True)
    >>> next(it)
    cftime._cftime.Datetime360Day(1970, 3, 1, 0, 0, 0, 0, -1, 61)
    >>> next(it)
    cftime._cftime.Datetime360Day(1970, 3, 11, 0, 0, 0, 0, -1, 71)
    >>> for x in it: pass   # iterate to final value
    >>> x
    cftime._cftime.Datetime360Day(1970, 6, 1, 0, 0, 0, 0, -1, 151)

    Example usage yielding 'days since 1970-01-01' numeric values:

    >>> units = cf_units.Unit('days since 1970-01-01', calendar='360_day')
    >>> it = iter_dates('1970-03-01', '1970-06-01', time_units=units, return_nums=True)
    >>> next(it)
    60.0
    >>> next(it)
    61.0

    Example usage yielding *integer* 'hours since 1970-01-01' numeric values:

    >>> units = cf_units.Unit('hours since 1970-01-01', calendar='360_day')
    >>> it = iter_dates('1970-02-01', '1970-03-01', step=3600/86400.,
    ...     time_units=units, return_nums=True, num_dtype=np.int32)
    >>> next(it)
    720
    >>> next(it)
    721

    :param str start_date: The start date-time in ISO 8601 or CF format.
    :param str end_date: The end date-time in ISO 8601 or CF format.
    :param float step: The time step in days (or fractional days) between
        successive date-times in the generated sequence. The value may be
        specified as an integer, a float, or a ``datetime.timedelta`` object.
        The latter is convenient when you want to specify the time step in units
        other than (or in addition to) days. For internal time calculation
        purposes the time step is converted to a whole number of seconds.
    :param bool endpoint: If True then the end date is included *if* it aligns
        with the step interval.
    :param time_units: A CF-style time unit specifier, which can either be a
        ``cf_units.Unit`` object, or a string of the form 'timeunits-since-refdate',
        in which case the Gregorian calendar is assumed. If undefined then the
        default units are 'seconds since 1800-01-01' based on the Gregorian calendar.
    :param bool return_nums: If True then the function yields time-since-refdate
        values based upon either ``time_units``, if these are defined, or else
        the default units as noted above. If false (the default) then the function
        yields datetime objects, the type of which is determined by the calendar
        associated with the time units.
    :param num_dtype: The numpy datatype to use for returned numeric times. The
        default type is ``np.float64``. If an integer datatype is supplied then
        the returned values are first rounded to the nearest integer (using
        ``numpy.rint()``).
    """

    # Define the reference time units to use for calculating the date sequence.
    ref_calendar = cf_units.CALENDAR_GREGORIAN
    ref_datum = 'seconds since 1800-01-01'
    ref_units = cf_units.Unit(ref_datum, calendar=ref_calendar)

    # If step is a datetime.timedelta object, convert it to seconds.
    if isinstance(step, datetime.timedelta):
        step = step.total_seconds()
    else:
        step = step * 86400

    # Round the time step to the nearest whole number of seconds.
    step = int(np.rint(step))

    # Check the validity of the time_units argument.
    if isinstance(time_units, string_types):
        time_units = cf_units.Unit(time_units, calendar=ref_calendar)
    elif isinstance(time_units, cf_units.Unit):
        if time_units.is_time_reference():
            if ref_units.calendar != time_units.calendar:
                ref_units = cf_units.Unit(ref_datum, calendar=time_units.calendar)
        else:
            raise ValueError("time_units argument does not define a CF-style "
                "'timeunits-since-refdate' unit.")

    # Convert start and end date-strings to cftime.datetime objects.
    start_pdt = pdt_from_date_string(start_date)
    end_pdt = pdt_from_date_string(end_date)
    start_dt = pdt_to_nc_datetime(start_pdt, calendar=ref_units.calendar)
    end_dt = pdt_to_nc_datetime(end_pdt, calendar=ref_units.calendar)

    # Check that start date < end date
    if step > 0 and start_dt >= end_dt:
        raise ValueError("Start date ({0}) must be less than end date ({1}).".format(
            start_date, end_date))
    # Check that start date < end date
    elif step < 0 and start_dt <= end_dt:
        raise ValueError("Start date ({0}) must be greater than end date ({1}).".format(
            start_date, end_date))

    # Convert start and end datetimes to seconds-since units
    start_time = int(np.rint(ref_units.date2num(start_dt)))
    end_time = int(np.rint(ref_units.date2num(end_dt)))

    if step > 0:
        oper = operator.le if endpoint else operator.lt
    else:
        oper = operator.ge if endpoint else operator.gt

    i = 0
    point = start_time

    while oper(point, end_time):
        num = ref_units.convert(point, time_units) if time_units else point

        # Generate numeric timeunits-since-refdate values if requested.
        if return_nums:
            if np.issubdtype(num_dtype, np.integer):
                num = np.rint(num)
            yield num_dtype(num)

        # Generate datetime-type objects.
        else:
            yield time_units.num2date(num) if time_units else ref_units.num2date(num)

        i += 1
        point = start_time + step * i
