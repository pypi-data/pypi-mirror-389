Tutorial #8: Using the DateTimeRange class
==========================================

This tutorial explores the capabilities of Afterburner’s ``DateTimeRange`` class
which, as the name suggests, may be used to represent a time range (or time period,
if you prefer that term). The DateTimeRange class can be found in the
:mod:`afterburner.utils.dateutils` module.

Instances of this class are used fairly widely in the ``afterburner`` package.
The class features a number of useful attributes and methods so you may well find
it handy to incorporate within your own code.

Although the DateTimeRange class includes a mutable calendar attribute, this mainly
comes into play when a method of the class calls a third-party function which is
calendar-aware. In that case the calendar attribute is passed to the third-party
function by whatever means is/are supported by the function. The DateTimeRange
class itself is not therefore calendar-aware, *sensu stricto* (in particular it
does not provide any date-time arithmetic features).

NB: In the rest of this tutorial the term 'date' is used, often loosely, as a
shorthand for 'date-time'. It should usually be evident from context those occasions
when 'date' or 'time' are used in their more restricted senses.

.. tip:: Refer to :doc:`Tutorial #1 </tutorials/accessing_afterburner>` for information
   on how to configure your Python environment to access the afterburner Python
   package.

Creating DateTimeRange Instances
--------------------------------

Instances of the ``DateTimeRange`` class can be created in any of three ways:

1. By calling the class constructor with start-date and end-date strings
2. By calling the ``from_datetime()`` static method
3. By calling the ``from_cube()`` static method

Here's how to create an instance of DateTimeRange using the class constructor
with start and end dates representing the JJA season for the year 1970:

>>> from afterburner.utils.dateutils import DateTimeRange
>>> dtr = DateTimeRange('1970-06-01', '1970-09-01')
>>> str(dtr)
'1970-06-01T00:00:00 1970-09-01T00:00:00'
>>> dtr.calendar
'gregorian'

As we just saw, the default calendar type for a DateTimeRange instance is Gregorian.
To create an instance that uses, say, a 360-day calendar we'd specify it at instance
creation time using the appropriate constant from the ``cf_units`` module:

>>> import cf_units as cfu
>>> from afterburner.utils.dateutils import DateTimeRange
>>> dtr = DateTimeRange('1970-06-01', '1970-09-01', calendar=cfu.CALENDAR_360_DAY)
>>> dtr.calendar
'360_day'

If your code already has two datetime-like objects representing the start and end
of the time range then it’s possible to use the ``from_datetime()`` static method
to create a DateTimeRange object. Here’s how you would do that:

>>> from datetime import datetime
>>> start_dt = datetime(1970, 6, 1, 0, 0)
>>> end_dt = datetime(1970, 9, 1, 0, 0)
>>> dtr = DateTimeRange.from_datetime(start_dt, end_dt)
>>> dtr.start, dtr.end
('1970-06-01T00:00:00', '1970-09-01T00:00:00')
>>> dtr.calendar
'gregorian'

Datetime-like object types that should work with this method include ``datetime.datetime``,
``netcdftime.datetime`` (deprecated), ``cftime.datetime`` and ``iris.time.PartialDateTime``
objects (and potentially any subclasses of these types).

The optional ``calendar`` keyword argument may be used as shown earlier to specify
the calendar type associated with the start and end date-times. However, if this
keyword is undefined then the ``from_datetime()`` method will try to determine the
calendar type by examining the attributes attached to the passed-in datetime objects.

To create a DateTimeRange instance based on the time coordinates attached to an
Iris cube, we can use the ``from_cube()`` static method. By default this method
uses the earliest and latest dates recorded in the array of time coordinates.
However, setting the ``use_bounds`` keyword to True results in the time bounds
being used to determine the earliest and latest dates:

>>> from afterburner.misc import stockcubes
>>> cube = stockcubes.geo_tyx(shape=(60, 19, 36))
>>> tdim = cube.coord('time')
>>> print(tdim[0])
DimCoord([1970-01-16 00:00:00], bounds=[[1970-01-01 00:00:00, 1970-02-01 00:00:00]], standard_name='time', calendar='360_day')
>>> print(tdim[-1])
DimCoord([1974-12-16 00:00:00], bounds=[[1974-12-01 00:00:00, 1975-01-01 00:00:00]], standard_name='time', calendar='360_day')
>>> dtr = DateTimeRange.from_cube(cube)
>>> dtr.start, dtr.end
('1970-01-16T00:00:00', '1974-12-16T00:00:00')

With the ``use_bounds`` keyword enabled we get the *outer bounds* of the time
dimension. Notice also that the ``from_cube()`` method examines the cube's time
dimension metadata in order to set the appropriate calendar attribute on the
returned DateTimeRange object:

>>> dtr = DateTimeRange.from_cube(cube, use_bounds=True)
>>> dtr.start, dtr.end
('1970-01-01T00:00:00', '1975-01-01T00:00:00')
>>> dtr.calendar
'360_day'

DateTimeRange attributes and properties
---------------------------------------

DateTimeRange objects possess a number of handy attributes and properties. As
we've seen above, the original start and end date-times passed to the DateTimeRange
constructor method are stored, unmodified, in the ``start`` and ``end`` attributes:

>>> dtr = DateTimeRange('1970-06-01T09', '1970-09-01T09')
>>> dtr.start, dtr.end
('1970-06-01T09', '1970-09-01T09')

When the start and end dates are auto-generated by the ``from_datetime()`` or
``from_cube()`` methods then those attributes store the *full* ISO 8601-compliant
datetime string:

>>> import cftime as cft
>>> start_dt = cft.datetime(1970, 6, 1, 9, 0)
>>> end_dt = cft.datetime(1970, 9, 1, 9, 0)
>>> dtr = DateTimeRange.from_datetime(start_dt, end_dt)
>>> dtr.start, dtr.end
('1970-06-01T09:00:00', '1970-09-01T09:00:00')

The *read-only* ``start_pdt`` and ``end_pdt`` properties return the date-times as
``iris.time.PartialDateTime`` objects. Any undefined time components are set to 0:

>>> dtr = DateTimeRange('1970-06-01T12', '1970-09-01T12')
>>> dtr.start_pdt, dtr.end_pdt
(PartialDateTime(year=1970, month=6, day=1, hour=12, minute=0, second=0),
 PartialDateTime(year=1970, month=9, day=1, hour=12, minute=0, second=0))

Likewise, the *read-only* ``start_ncdt`` and ``end_ncdt`` properties return the
date-times as either ``netcdftime.datetime`` objects or ``cftime.datetime`` objects,
depending upon which of those two modules is loaded (the former module is now
deprecated, so it should usually now be the latter):

>>> dtr.start_ncdt, dtr.end_ncdt
(cftime._cftime.DatetimeGregorian(1970, 6, 1, 12, 0, 0, 0, -1, 1),
 cftime._cftime.DatetimeGregorian(1970, 9, 1, 12, 0, 0, 0, -1, 1))

If the ``start`` and/or ``end`` attributes are modified then the ``start_pdt/end_pdt``
and  ``start_ncdt/end_ncdt`` properties are adjusted accordingly:

>>> dtr.start = '1970-03-01T12'
>>> dtr.start_pdt, dtr.start_ncdt
>>> (PartialDateTime(year=1970, month=3, day=1, hour=12, minute=0, second=0),
     cftime._cftime.DatetimeGregorian(1970, 3, 1, 12, 0, 0, 0, -1, 1))

The ``interval_type`` attribute stores the type of numeric interval represented
by the time range, one of 'open', 'closed', 'leftclosed', 'leftopen'. The default
is 'leftclosed'. This attribute is mainly used during tests for a date-time value
being contained within the time range:

>>> dtr = DateTimeRange('1970-06-01', '1970-09-01')
>>> dtr.interval_type
'leftclosed'
>>> # With this default setting the end time is *excluded* in a contains test
>>> dtr.contains('1970-09-01')
False
>>> # But the end time is *included* if the interval is 'closed' (or 'leftopen').
>>> dtr.contains('1970-09-01', interval_type='closed')
True

DateTimeRange Methods
---------------------

The DateTimeRange class also contains a handful of useful methods, as demonstrated
below.

A string representation of a DateTimeRange object can be obtained using the usual
mechanisms: ``print()`` and ``str()``:

>>> dtr = DateTimeRange('1970-06-01T06:30', '1970-09-01T18:30')
>>> str(dtr)
'1970-06-01T06:30:00 1970-09-01T18:30:00'

Alternatively, you can get more control over the output string by using the
``as_string(sep='_', ymd_sep='-', hms_sep=':', dt_sep='T')`` method:

>>> dtr.as_string()   # default output
'1970-06-01T06:30:00_1970-09-01T18:30:00'
>>> dtr.as_string(sep='...', ymd_sep='/', hms_sep='.', dt_sep=' ')   # custom output
'1970/06/01 06.30.00...1970/09/01 18.30.00'

The ``as_name_token(dates_only=False, compact=False)`` method may be used to
obtain a string token suitable for use in, say, a filename. By default the token
is identical to the string returned by the ``as_string()`` method:

>>> dtr.as_name_token()                  # default output
'1970-06-01T06:30:00_1970-09-01T18:30:00'
>>> dtr.as_name_token(compact=true)      # compact output
'19700601T063000_19700901T183000'
>>> dtr.as_name_token(dates_only=True)   # drop time components
'1970-06-01_1970-09-01'

Working with 'half-open' time ranges
------------------------------------

On occasions it is desirable to specify just the start date-time, or just the
end date-time, when creating instances of the DateTimeRange class. This can be
achieved by using the value None as the unwanted date-time value. Internally,
the instance replaces the None value with a date-time representation of either
negative infinity (in the case of the start date-time) or positive infinity (in
the case of the end date-time). This behaviour is shown below:

>>> dtr = DateTimeRange(None, '1970-01-01')
>>> str(dtr)
'-9999999-09-09T09:09:09 1970-01-01T00:00:00'
>>> dtr = DateTimeRange('1970-01-01', None)
>>> str(dtr)
'1970-01-01T00:00:00 9999999-09-09T09:09:09'

This mechanism can be useful when you are only interested in determining if time
instants fall before or after a particular date-time and you don't wish to define
the 'missing' half of the date-time range. For example, the final DateTimeRange
object created in the code fragment above essentially encompasses all date-times
at or later than midnight on 1970-01-01 (it's assumed that dates at and above
9999999-09-09T09:09:09 are invalid).

>>> dtr.contains('1900-12-01')
False
>>> dtr.contains('1969-12-31T23:59:59')
False
>>> dtr.contains('1970-01-01')
True
>>> dtr.contains('1999-01-01')
True
>>> dtr.contains('9999-09-09')
True

This tutorial has demonstrated the main areas of functionality provided by the
DateTimeRange class, full details of which can be found in the
:class:`API documentation <afterburner.utils.dateutils.DateTimeRange>`.

Back to the :doc:`Tutorial Index <index>`
