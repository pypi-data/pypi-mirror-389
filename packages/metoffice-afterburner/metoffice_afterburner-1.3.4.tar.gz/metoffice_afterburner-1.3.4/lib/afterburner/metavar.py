# (C) British Crown Copyright 2016-2025, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The metavar module contains classes used to identify variables (or diagnostics)
produced by numerical climate models. Currently, the principal use-case for
these classes is to identify file-sets associated with a model diagnostic, or a
subset of a diagnostic as identified by spatio-temporal and/or attribute metadata.
Typically such metadata is specified via the Rose configuration files used to
control Afterburner applications.

Instances of concrete subclasses of :class:`MetaVariable` contain a number of
default attributes, as described in the documentation for the init method of
each subclass. As such, a meta-variable object can be thought of simply as a
bundle of properties which uniquely identifies some model variable/diagnostic of
interest.

Over and above the default set of attributes, any additional attributes may be
attached to meta-variable objects in order to support the functional requirements
of client applications. It is up to these client applications to decide when and
how to use such attributes.

For most practical applications it will usually be necessary to specify some
minimum set of attributes that enables the desired target variable to be both
distinguished from other variables and potentially instantiated using data from
an appropriate data source.

**Index of Classes in this Module**

.. autosummary::
   :nosignatures:

   MetaVariable
   UmMetaVariable
   NemoMetaVariable
   CiceMetaVariable
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import add_metaclass
from packaging.version import Version 

import abc
import copy
import cf_units
import iris
import warnings

try:
    # The abstractproperty decorator was deprecated at Python 3.3
    from abc import abstractproperty
except ImportError:
    abstractproperty = lambda f: property(abc.abstractmethod(f))

from afterburner.utils import dateutils
from afterburner.modelmeta import MODEL_UM, MODEL_NEMO, MODEL_CICE, is_msi_stash_code
from afterburner.exceptions import UnknownModelNameError
from afterburner.coords import CoordRange

__all__ = ('MetaVariable', 'UmMetaVariable', 'NemoMetaVariable', 'CiceMetaVariable')


@add_metaclass(abc.ABCMeta)
class MetaVariable(object):
    """
    Abstract base class used to define a requested/virtual variable, one without
    associated data. The concrete subclasses defined within this module should be
    used to represent model-specific phenomena, e.g. a UM diagnostic or a NEMO
    model variable.
    """

    def __init__(self, model_vn, suite_id, **kwargs):
        """
        :param str model_vn: Model version number in familiar dot-separated
            major.minor.micro notation. If either or both of the minor and
            micro components are omitted then a value of 0 is assumed.
            Examples: '8.1.2', '9.2', '10.0.0', '10'.
        :param str suite_id: Suite identifier. This should be a Rose suite name,
            e.g. 'mi-abcde', or a UM runid, e.g. 'abcde'.
        """
        self._xaxis_range = self._yaxis_range = self._zaxis_range = None
        self._time_range = None

        #: Name of the model with which the meta-variable is associated. Set
        #: automatically by concrete subclasses.
        self.model_name = None

        #: Model version number. Defaults to '0.0.0' if not defined by caller.
        self.model_vn = _normalize_version_string(model_vn)

        #: Rose suite id or UMUI run/expt id.
        self.suite_id = suite_id

        #: UMUI-style run id. Derived automatically from ``suite_id`` unless
        #: defined explicitly via the ``kwargs['run_id']`` key-value pair.
        self.run_id = kwargs.get('run_id') or suite_id.split('-')[-1]

        #: An alias for the :attr:`run_id` attribute.
        self.runid = self.run_id

        #: Start date-time as an `iris.time.PartialDateTime` object. This read-only
        #: attribute is derived from :attr:`time_range`.
        self.start_time = None

        #: End date-time as an `iris.time.PartialDateTime object`. This read-only
        #: attribute is derived from :attr:`time_range`.
        self.end_time = None

        # Assign X-Y-Z-T coordinate range objects, if specified.
        self.xaxis_range = kwargs.get('xaxis_range')
        self.yaxis_range = kwargs.get('yaxis_range')
        self.zaxis_range = kwargs.get('zaxis_range')
        self.time_range = kwargs.get('time_range')

        # Postproc version number string, if specified.
        self.postproc_vn = str(kwargs.get('postproc_vn', ''))

    def __getattr__(self, name):
        """
        If attribute with name ``name`` is not defined on a meta-variable object
        then return None.
        """
        return None

    def __copy__(self):
        """Shallow copying not supported."""
        raise copy.Error("Shallow copying not supported. Use copy.deepcopy() "
            "or MetaVariable.copy()")

    def __deepcopy__(self, memo):
        """Return a deep copy of self."""
        raise NotImplementedError()

    @abstractproperty
    def name(self):
        """
        A representative human-readable name for the variable. Read-only attribute.
        """
        raise NotImplementedError()

    @abstractproperty
    def slug(self):
        """
        A tokenised name for the variable. Typical use is to form a directory
        or file name. Accordingly, slug names comprise characters from the set
        [_a-zA-Z0-9]. Read-only attribute.
        """
        raise NotImplementedError()

    @property
    def xaxis_range(self):
        """
        Coordinate range, if any, associated with the meta-variable's X
        axis/dimension -- longitude in many cases.
        """
        return self._xaxis_range

    @xaxis_range.setter
    def xaxis_range(self, value):
        """
        Set the the meta-variable's X-axis coordinate range.
        :param afterburner.coords.CoordRange value: A CoordRange object or None.
        """
        if isinstance(value, (type(None), CoordRange)):
            self._xaxis_range = copy.deepcopy(value)
        else:
            msg = "xaxis_range attribute must be of type CoordRange or None."
            raise ValueError(msg)

    @property
    def yaxis_range(self):
        """
        Coordinate range, if any, associated with the meta-variable's Y
        axis/dimension -- latitude in many cases.
        """
        return self._yaxis_range

    @yaxis_range.setter
    def yaxis_range(self, value):
        """
        Set the the meta-variable's Y-axis coordinate range.
        :param afterburner.coords.CoordRange value: A CoordRange object or None.
        """
        if isinstance(value, (type(None), CoordRange)):
            self._yaxis_range = copy.deepcopy(value)
        else:
            msg = "yaxis_range attribute must be of type CoordRange or None."
            raise ValueError(msg)

    @property
    def zaxis_range(self):
        """
        Coordinate range, if any, associated with the meta-variable's Z
        axis/dimension -- e.g. model level number, pressure level.
        """
        return self._zaxis_range

    @zaxis_range.setter
    def zaxis_range(self, value):
        """
        Set the the meta-variable's Z-axis coordinate range.
        :param afterburner.coords.CoordRange value: A CoordRange object or None.
        """
        if isinstance(value, (type(None), CoordRange)):
            self._zaxis_range = copy.deepcopy(value)
        else:
            msg = "zaxis_range attribute must be of type CoordRange or None."
            raise ValueError(msg)

    @property
    def time_range(self):
        """
        The date-time range, if any, associated with the meta-variable's time
        axis/dimension. Typically the range represents a *left-closed* interval
        i.e. start time included, end time excluded. Ultimately, however, the
        interpretation of the time range is the responsibility of calling code.

        Internally, the time range is stored as a 2-tuple of date-time strings
        in ISO 8601 format. See also the :attr:`start_time` and :attr:`end_time`
        attributes.
        """
        return self._time_range

    @time_range.setter
    def time_range(self, value):
        """
        Set the meta-variable's date-time range.
        :param list/tuple value: A 2-tuple of date-time strings in ISO 8601 format,
            i.e. 'YYYY-MM-DDThh:mm:ss'. Alternatively, an instance of class
            :class:`afterburner.utils.dateutils.DateTimeRange` may be supplied.
        """
        if value is None:
            self._time_range = self.start_time = self.end_time = None
        elif isinstance(value, (list, tuple)) and len(value) == 2:
            self._time_range = tuple(value)
            self.decode_time_range()
        elif isinstance(value, dateutils.DateTimeRange):
            self._time_range = tuple(value[:])
            self.decode_time_range()
        else:
            msg = ("time_range attribute must be either a 2-tuple of date-time "
                "strings or an afterburner.utils.datetuils.DateTimeRange object.")
            raise ValueError(msg)

    @staticmethod
    def create_variable(model_name, model_vn, suite_id, **kwargs):
        """
        Create a meta-variable object specific to ``model_name``. Model-specific
        attributes should be specified via keyword arguments. The list of
        supported arguments is described in the documentation below for each
        concrete subclass.

        :param str model_name: The model short name or acronym. Currently
            supported model names are 'UM', 'NEMO' and 'CICE'.
        :param str model_vn: Model version number in familiar dot-separated
            major.minor.micro notation. If either or both of the minor and
            micro components are omitted then a value of 0 is assumed.
            Examples: '8.1.2', '9.2', '10.0.0', '10'.
        :param str suite_id: Suite identifier. This should be a Rose suite name,
            e.g. 'mi-ab123', or a UM runid, e.g. 'abcde'.
        """
        if model_name.upper() == MODEL_UM:
            metavar = UmMetaVariable(model_vn, suite_id, **kwargs)
        elif model_name.upper() == MODEL_NEMO:
            metavar = NemoMetaVariable(model_vn, suite_id, **kwargs)
        elif model_name.upper() == MODEL_CICE:
            metavar = CiceMetaVariable(model_vn, suite_id, **kwargs)
        else:
            raise UnknownModelNameError("Unrecognised model name: " + model_name)
        return metavar

    def copy(self):
        """Return a deep copy of self."""
        return self.__deepcopy__({})

    def decode_time_range(self):
        """
        Decode the start and end date-time strings defined in the :attr:`time_range`
        attribute. The decoded values are stored as `iris.time.PartialDateTime`
        objects in the :attr:`start_time` and :attr:`end_time` attributes.
        """
        if self.time_range:
            self.start_time = dateutils.pdt_from_date_string(self.time_range[0], default=0)
            self.end_time = dateutils.pdt_from_date_string(self.time_range[1], default=0)
        else:
            msg = "A time-range attribute is not defined on meta-variable '%s'" % self
            raise ValueError(msg)

    def make_load_callback(self, **kwargs):
        """
        Construct a callback function which can be passed to an iris.load*()
        function so as to yield the *smallest* cubelist that satisfies the
        properties defined on a meta-variable object.

        Concrete subclasses will typically want to override this method in order
        to return a callback function which acts upon a meta-variable's specific
        attributes.
        """
        return None

    def make_id_constraint(self):
        """
        Construct an Iris load constraint which compares the identity of the
        current meta-variable with a cube, returning True if they are equal.

        Concrete subclasses will typically want to override this method in order
        to return a constraint object which acts upon a meta-variable's specific
        attributes.
        """
        def _id_constraint(cube):
            if self.var_name != cube.var_name:
                return False
            if self.standard_name:
                return self.standard_name == cube.standard_name
            return True

        return iris.Constraint(cube_func=_id_constraint)

    def _iris_calendar_compatibility_check(self, loaded_calendar):
        """
        A workaround for iris silently changing the gregorian calendar attribute to
        standard.

        This will be called within a callback if the iris version contains the change
        that must be worked around.
        """
        if self.calendar == "gregorian" and loaded_calendar == "standard":
            warnings.warn(UserWarning("Calendars gregorian and standard assumed to be"
                                      " the same."))
        else:
            raise iris.exceptions.IgnoreCubeException()

class UmMetaVariable(MetaVariable):
    """
    Class used to define a requested/virtual variable produced by the Unified
    Model.

    For applications working with UM diagnostics it will typically be necessary
    to define, as minimum, the relevant ``stream_id`` and ``stash_code`` values,
    plus, for temporal subsets, the ``time_range`` attribute. Which other
    attributes are required will necessarily depend upon the application context.
    """

    def __init__(self, model_vn, suite_id, realization_id='', stream_id='',
            stash_code='', lbproc=None, lbtim=None, time_range=None, calendar=None,
            **kwargs):
        """
        All of the constructor argument values, be they user-specified or defaults,
        are stored in like-named attributes on the instance object. They can of
        course be updated post-creation, should that be desired.

        :param str model_vn: Model version number in familiar dot-separated
            major.minor.micro notation. If either or both of the minor and
            micro components are omitted then a value of 0 is assumed.
            Examples: '8.1.2', '9.2', '10.0.0', '10'.
        :param str suite_id: Suite identifier. This should be a Rose suite name,
            e.g. 'mi-abcde', or a UM runid, e.g. 'abcde'.
        :param str realization_id: Realization identifier, e.g. 'r1i3p2'.
        :param str stream_id: Stream identifier, e.g. 'apy', 'apm'.
        :param str stash_code: UM STASH code in MSI format (but see also the
            ``var_name`` keyword argument below).
        :param int lbproc: Value of the LBPROC PP header field, as defined in
            UM documentation paper F03.
        :param int lbtim: Value of the LBTIM PP header field, as defined in
            UM documentation paper F03.
        :param list/tuple time_range: A 2-tuple of date-time strings, or an
            instance of :class:`DateTimeRange <afterburner.utils.dateutils.DateTimeRange>`,
            specifying the start and end date-times of the variable. Date-times
            strings should be specified in the format 'YYYY-MM-DDThh:mm:ss'.
        :param str calendar: Calendar type specified using one of the CALENDAR_xxx
            constants defined in the cf_units module. If this argument is not
            specified, but ``lbtim`` is, then the calendar type is determined
            from the latter. If both arguments are defined then they must be
            mutually consistent.

        Extra Keyword Arguments:

        :param str var_name: Alternative way to specify the UM STASH code, thus
            achieving a measure of API consistency with other metavariable classes.
        :param afterburner.coords.CoordRange xaxis_range: X axis coordinate range.
        :param afterburner.coords.CoordRange yaxis_range: Y axis coordinate range.
        :param afterburner.coords.CoordRange zaxis_range: Z axis coordinate range.
        :param str postproc_vn: postproc version number.

        The following arguments may be used to override the equivalent options
        recognised by the :mod:`afterburner.contrib.umfilelist` module. For
        most typical scenarios these arguments should not need to be defined.

        :param str cmrdate: Climate meaning reference date in format YYYYMMDDhhmm.
            (default = '185912010000').
        :param bool newmode: Use new UM file-naming convention (default = True)
        :param int reinit: Reinitialisation interval in days (default = 0)
        :param str time_format: Absolute time format specifier. Recognised values
            are 'standard' (the default), 'short', or 'long'. Refer to the
            :mod:`afterburner.contrib.umfilelist` module for further details.
        :param bool zeropad_dates: Left-pad date strings with zeros (default = True)
        """
        super(UmMetaVariable, self).__init__(model_vn, suite_id, **kwargs)

        # Model metadata.
        self.model_name = MODEL_UM
        self.realization_id = realization_id
        self.stream_id = stream_id

        # Phenomenon metadata.
        if not stash_code:
            if is_msi_stash_code(kwargs.get('var_name', '')):
                stash_code = kwargs['var_name']
            else:
                raise ValueError("A STASH code must be specified for UM meta-variables.")
        if not is_msi_stash_code(stash_code):
            raise ValueError("Invalid MSI-style STASH code: %s" % stash_code)
        self.stash_code = stash_code
        self.var_name = stash_code

        # Time and calendar metadata.
        self.lbproc = lbproc
        self.lbtim = lbtim
        self.time_range = time_range
        self.calendar = calendar
        if lbtim or calendar: self._check_calendar()

        # Options to pass through to the umfilelist module.
        # Climate meaning reference date in format 'YYYYMMDDhhmm'.
        self.cmrdate = kwargs.get('cmrdate', '')
        # Reinitialisation interval in days.
        self.reinit = kwargs.get('reinit', 0)
        # Absolute time format specifier. One of 'standard', 'short', or 'long'.
        self.time_format = kwargs.get('time_format', '')
        # Use the new (post vn9.2) UM file-naming convention.
        self.newmode = kwargs.get('newmode', True)
        # Whether or not to left-pad date tokens in filenames with zeros.
        self.zeropad_dates = kwargs.get('zeropad_dates', True)

    def __str__(self):
        """Return a string containing selected properties of the variable."""
        if self.realization_id:
            suite_real = self.suite_id + '/' + self.realization_id
        else:
            suite_real = self.suite_id
        text = "{0} v{1}, {2}/{3}, {4}:lbproc={5}:lbtim={6}".format(
            self.model_name, self.model_vn, suite_real, self.stream_id,
            self.stash_code, self.lbproc, self.lbtim)
        if self.time_range:
            start, end = self.time_range
            text += ", from {0} to {1}".format(start, end)
        return text

    def __deepcopy__(self, memo):
        """Return a deep copy of self."""
        # Create a new instance from mandatory arguments.
        mandatory_keys = ['model_vn', 'suite_id', 'stash_code']
        mandatory_args = {k:self.__dict__[k] for k in mandatory_keys}
        new = UmMetaVariable(**mandatory_args)

        # Deep-copy the remaining attributes from self.__dict__.
        for k, v in self.__dict__.items():
            if k in mandatory_keys: continue
            setattr(new, k, copy.deepcopy(v, memo))

        return new

    @property
    def name(self):
        """Returns the variable's STASH code string."""
        return self.stash_code

    @property
    def slug(self):
        """Returns the variable's STASH code string."""
        return self.stash_code

    def make_load_callback(self, id_only=False, do_time_check=False):
        """
        Construct a callback function which can be passed to an iris.load*()
        function so as to yield the *smallest* cubelist that satisfies the
        properties defined on a meta-variable object.

        :param bool id_only: If this option is enabled then the returned callback
            function only performs identity tests, i.e. against stash_code.
        :param bool do_time_check: If this option is enabled then the returned
            callback function includes a test for the PP field's start time (T1)
            lying within the meta-variable's time range, i.e. start <= T1 < end.
            This option is disabled by default because it is hard to anticipate
            the kinds of time-based filtering that client code might wish to
            perform.
        """
        def _um_var_load_callback(cube, field, filename):
            if id_only is not None:
                if self.stash_code:
                    stash = cube.attributes.get('STASH')
                    if stash and str(stash) != self.stash_code:
                        raise iris.exceptions.IgnoreCubeException()
                if id_only: return

            if self.lbproc is not None:
                if field.lbproc != self.lbproc:
                    raise iris.exceptions.IgnoreCubeException()

            if self.lbtim is not None:
                if field.lbtim != self.lbtim:
                    raise iris.exceptions.IgnoreCubeException()

            if self.calendar:
                # NB: for convenience this test is done against the units of the
                # cube's time coord. An alternative would be to test against the
                # field.lbtim.ic value, though with a little more effort.
                if 'time' in [crd.name() for crd in cube.coords()]:
                    time = cube.coord('time')
                    if time.units.calendar != self.calendar:
                        if Version(iris.__version__) >= Version("3.3"):
                            #Work around for changes in iris 3.3 changing calendar
                            # attributes silently from gregorian to standard
                            self._iris_calendar_compatibility_check(time.units.calendar)
                        else:
                            raise iris.exceptions.IgnoreCubeException()


            if self.time_range and do_time_check:
                # Since field.t1 is a datetime object we can compare it directly
                # against the meta-variable's start and end date-time values.
                start_ncdt = dateutils.pdt_to_nc_datetime(self.start_time,
                    calendar=self.calendar)
                end_ncdt = dateutils.pdt_to_nc_datetime(self.end_time,
                    calendar=self.calendar)
                if not (dateutils.pdt_compare(field.t1, 'ge', start_ncdt) and
                        dateutils.pdt_compare(field.t1, 'lt', end_ncdt)):
                    raise iris.exceptions.IgnoreCubeException()

        return _um_var_load_callback

    def make_id_constraint(self):
        """
        Construct an Iris load constraint which compares the identity of the
        current meta-variable with a cube, returning True if they are equal.
        """
        return iris.AttributeConstraint(STASH=self.stash_code)

    def _check_calendar(self):
        """Check that calendar information, if defined, is valid and consistent."""
        lbtim_cal = self.lbtim and _calendar_from_lbtim(self.lbtim) or ''
        if lbtim_cal:
            if self.calendar:
                if self.calendar != lbtim_cal:
                    raise ValueError("Specified calendar ({0}) does not match\n"
                        "calendar ({1}) encoded in the lbtim argument.".format(
                        self.calendar, lbtim_cal))
            else:
                self.calendar = lbtim_cal

        if self.calendar and self.calendar not in cf_units.CALENDARS:
            raise ValueError("Invalid calendar type: %s" % self.calendar)


class NemoMetaVariable(MetaVariable):
    """
    Class used to define a requested/virtual variable produced by the NEMO ocean
    model.

    For applications working with NEMO variables it will typically be necessary
    to define, as minimum, the relevant ``stream_id`` and ``var_name`` values,
    plus, for temporal subsets, the ``time_range`` attribute. Which other
    attributes are required will necessarily depend upon the application context.
    """

    #: List of recognised NEMO grid types.
    GRID_TYPES = ('T', 'U', 'V', 'W', 'diaptr', 'scalar')

    #: Named profiles for selecting pre-defined sets of auxiliary variables.
    AUX_VAR_PROFILES = {
        'default': (
            'nav_lon', 'nav_lat', 'lont_bounds', 'latt_bounds',
            'ocndept', 'deptht', 'deptht_bounds',
            'time_counter', 'time_counter_bnds',
            'areat', 'ang1t', 'e1t', 'e2t', 'e3t'),
        'xyt_coords': (
            'nav_lon', 'nav_lat', 'lont_bounds', 'latt_bounds',
            'time_counter', 'time_counter_bnds'),
        'xyzt_coords': (
            'nav_lon', 'nav_lat', 'lont_bounds', 'latt_bounds',
            'ocndept', 'deptht', 'deptht_bounds',
            'time_counter', 'time_counter_bnds')
    }

    def __init__(self, model_vn, suite_id, realization_id='', stream_id='',
            var_name='', long_name='', standard_name='',
            aux_var_names=None, aux_var_profile='',
            time_range=None, calendar=None, grid_type='T', **kwargs):
        """
        All of the constructor argument values, be they user-specified or defaults,
        are stored in like-named attributes on the instance object. They can of
        course be updated post-creation, should that be desired.

        :param str model_vn: Model version number in familiar dot-separated
            major.minor.micro notation. If either or both of the minor and
            micro components are omitted then a value of 0 is assumed.
            Examples: '8.1.2', '9.2', '10.0.0', '10'.
        :param str suite_id: Suite identifier. This should be a Rose suite name,
            e.g. 'mi-abcde', or a UM runid, e.g. 'abcde'.
        :param str realization_id: Realization identifier, e.g. 'r1i3p2'.
        :param str stream_id: Stream identifier, e.g. 'ony', 'onm'.
        :param str var_name: NetCDF variable name.
        :param str long_name: Long name of variable.
        :param str standard_name: CF standard name of variable.
        :param list aux_var_names: List of auxiliary netCDF variables associated
            with the primary variable. Takes precedence over ``aux_var_profile``,
            if that attribute is also defined.
        :param str aux_var_profile: The name of a pre-defined list of auxiliary
            variables. The keys of the :attr:`AUX_VAR_PROFILES` dictionary define
            the list of permissible profile names.
        :param list/tuple time_range: A 2-tuple of date-time strings, or an
            instance of :class:`DateTimeRange <afterburner.utils.dateutils.DateTimeRange>`,
            specifying the start and end date-times of the variable. Date-times
            strings should be specified in the format 'YYYY-MM-DDThh:mm:ss'.
        :param str calendar: Calendar type specified using one of the CALENDAR_xxx
            constants defined in the cf_units module.
        :param str grid_type: Grid type indicator - one of the values defined in
            the :attr:`GRID_TYPES` attribute.

        Extra Keyword Arguments:

        :param afterburner.coords.CoordRange xaxis_range: X axis coordinate range.
        :param afterburner.coords.CoordRange yaxis_range: Y axis coordinate range.
        :param afterburner.coords.CoordRange zaxis_range: Z axis coordinate range.
        :param str postproc_vn: postproc version number.
        """
        super(NemoMetaVariable, self).__init__(model_vn, suite_id, **kwargs)

        # Model metadata.
        self.model_name = MODEL_NEMO
        self.realization_id = realization_id
        self.stream_id = stream_id

        # Phenomenon metadata.
        if not var_name:
            raise ValueError("The var_name argument must be specified for NEMO meta-variables.")
        self.var_name = var_name
        self.long_name = long_name
        self.standard_name = standard_name

        # Auxiliary variable name metadata.
        self.aux_var_names = aux_var_names
        if not aux_var_names and aux_var_profile:
            self.aux_var_names = self.AUX_VAR_PROFILES.get(aux_var_profile)

        # Time and calendar metadata.
        self.time_range = time_range
        if calendar and calendar not in cf_units.CALENDARS:
            raise ValueError("Invalid calendar type: %s" % calendar)
        self.calendar = calendar

        # Grid metadata.
        if grid_type not in self.GRID_TYPES:
            raise ValueError("Invalid grid type: %s" % grid_type)
        self.grid_type = grid_type

    def __str__(self):
        """Return a string containing selected properties of the variable."""
        if self.realization_id:
            suite_real = self.suite_id + '/' + self.realization_id
        else:
            suite_real = self.suite_id
        text = "{0} v{1}, {2}/{3}, {4} on {5}-grid".format(self.model_name,
            self.model_vn, suite_real, self.stream_id, self.name, self.grid_type)
        if self.time_range:
            start, end = self.time_range
            text += ", from {0} to {1}".format(start, end)
        return text

    def __deepcopy__(self, memo):
        """Return a deep copy of self."""
        # Create a new instance from mandatory arguments.
        mandatory_keys = ['model_vn', 'suite_id', 'var_name']
        mandatory_args = {k:self.__dict__[k] for k in mandatory_keys}
        new = NemoMetaVariable(**mandatory_args)

        # Deep-copy the remaining attributes from self.__dict__.
        for k, v in self.__dict__.items():
            if k in mandatory_keys: continue
            setattr(new, k, copy.deepcopy(v, memo))

        return new

    @property
    def name(self):
        """
        Returns the first non-null value taken from the following instance
        attributes: ``standard_name``, ``long_name``, ``var_name``.
        """
        return self.standard_name or self.long_name or self.var_name

    @property
    def slug(self):
        """
        Returns the value of the ``var_name`` attribute, i.e. the netCDF
        variable name.
        """
        return self.var_name

    def make_load_callback(self, id_only=False, do_time_check=False):
        """
        Construct a callback function which can be passed to an iris.load*()
        function so as to yield the *smallest* cubelist that satisfies the
        properties defined on a meta-variable object.

        :param bool id_only: If this option is enabled then the returned callback
            function only performs identity tests, i.e. against standard_name
            and var_name.
        :param bool do_time_check: If this option is enabled then the returned
            callback function includes a test for the source cube's start and
            end times lying within the meta-variable's time range, i.e.
            start <= T1 and T2 < end. This option is disabled by default because
            it is hard to anticipate the kinds of time-based filtering that
            client code might wish to perform.
        """
        def _nemo_var_load_callback(cube, field, filename):

            if id_only is not None:
                if self.var_name:
                    if cube.var_name != self.var_name:
                        raise iris.exceptions.IgnoreCubeException()
                if self.standard_name:
                    if cube.standard_name != self.standard_name:
                        raise iris.exceptions.IgnoreCubeException()
                if id_only: return

            if self.calendar:
                if 'time' in [crd.name() for crd in cube.coords()]:
                    time = cube.coord('time')
                    if time.units.calendar != self.calendar:
                        if Version(iris.__version__) >= Version("3.3"):
                            #Work around for changes in iris 3.3 changing calendar
                            # attributes silently from gregorian to standard
                            self._iris_calendar_compatibility_check(time.units.calendar)
                        else:
                            raise iris.exceptions.IgnoreCubeException()

            if self.time_range and do_time_check:
                # Check that cube's time extent falls within time range.
                if 'time' in [crd.name() for crd in cube.coords()]:
                    time = cube.coord('time')
                    # Cubes derived from netcdf files may contain 2 or more
                    # time coordinates. The test below reflects this possibility.
                    if time.has_bounds():
                        # Analogous treatment as per T1 dates in UM PP data.
                        t1, t2 = time.bounds[0,0], time.bounds[-1,0]
                    else:
                        t1, t2 = time.points[0], time.points[-1]
                    t1, t2 = time.units.num2date((t1, t2))
                    if not (dateutils.pdt_compare(t1, 'ge', self.start_time) and
                            dateutils.pdt_compare(t2, 'lt', self.end_time)):
                        raise iris.exceptions.IgnoreCubeException()

        return _nemo_var_load_callback


class CiceMetaVariable(MetaVariable):
    """
    Class used to define a requested/virtual variable produced by the CICE model.

    For applications working with CICE variables it will typically be necessary
    to define, as minimum, the relevant ``stream_id`` and ``var_name`` values,
    plus, for temporal subsets, the ``time_range`` attribute. Which other
    attributes are required will necessarily depend upon the application context.
    """

    #: List of recognised CICE grid types.
    GRID_TYPES = ('T', 'U')

    #: Named profiles for selecting pre-defined sets of auxiliary variables.
    AUX_VAR_PROFILES = {
        'default': (
            'TLON', 'TLAT', 'lont_bounds', 'latt_bounds',
            'ULON', 'ULAT', 'lonu_bounds', 'latu_bounds',
            'NCAT', 'time', 'time_bounds',
            'tmask', 'tarea', 'uarea', 'ANGLE', 'ANGLET'),
        'xyt_coords': (
            'TLON', 'TLAT', 'lont_bounds', 'latt_bounds',
            'ULON', 'ULAT', 'lonu_bounds', 'latu_bounds',
            'time', 'time_bounds'),
        'xyzt_coords': (
            'TLON', 'TLAT', 'lont_bounds', 'latt_bounds',
            'ULON', 'ULAT', 'lonu_bounds', 'latu_bounds',
            'NCAT', 'time', 'time_bounds')
    }

    def __init__(self, model_vn, suite_id, realization_id='', stream_id='',
            var_name='', long_name='', standard_name='',
            aux_var_names=None, aux_var_profile='',
            time_range=None, calendar=None, grid_type='T', **kwargs):
        """
        All of the constructor argument values, be they user-specified or defaults,
        are stored in like-named attributes on the instance object. They can of
        course be updated post-creation, should that be desired.

        :param str model_vn: Model version number in familiar dot-separated
            major.minor.micro notation. If either or both of the minor and
            micro components are omitted then a value of 0 is assumed.
            Examples: '8.1.2', '9.2', '10.0.0', '10'.
        :param str suite_id: Suite identifier. This should be a Rose suite name,
            e.g. 'mi-abcde', or a UM runid, e.g. 'abcde'.
        :param str realization_id: Realization identifier, e.g. 'r1i3p2'.
        :param str stream_id: Stream identifier, e.g. 'ony', 'onm'.
        :param str var_name: NetCDF variable name.
        :param str long_name: Long name of variable.
        :param str standard_name: CF standard name of variable.
        :param list aux_var_names: List of auxiliary netCDF variables associated
            with the primary variable. Takes precedence over ``aux_var_profile``,
            if that attribute is also defined.
        :param str aux_var_profile: The name of a pre-defined list of auxiliary
            variables. The keys of the :attr:`AUX_VAR_PROFILES` dictionary define
            the list of permissible profile names.
        :param list/tuple time_range: A 2-tuple of date-time strings, or an
            instance of :class:`DateTimeRange <afterburner.utils.dateutils.DateTimeRange>`,
            specifying the start and end date-times of the variable. Date-times
            strings should be specified in the format 'YYYY-MM-DDThh:mm:ss'.
        :param str calendar: Calendar type specified using one of the CALENDAR_xxx
            constants defined in the cf_units module.
        :param str grid_type: Grid type indicator - one of the values defined in
            the :attr:`GRID_TYPES` attribute.

        Extra Keyword Arguments:

        :param afterburner.coords.CoordRange xaxis_range: X axis coordinate range.
        :param afterburner.coords.CoordRange yaxis_range: Y axis coordinate range.
        :param afterburner.coords.CoordRange zaxis_range: Z axis coordinate range.
        :param str postproc_vn: postproc version number.
        """
        super(CiceMetaVariable, self).__init__(model_vn, suite_id, **kwargs)

        # Model metadata.
        self.model_name = MODEL_CICE
        self.realization_id = realization_id
        self.stream_id = stream_id

        # Phenomenon metadata.
        if not var_name:
            raise ValueError("The var_name argument must be specified for CICE meta-variables.")
        self.var_name = var_name
        self.long_name = long_name
        self.standard_name = standard_name

        # Auxiliary variable name metadata.
        self.aux_var_names = aux_var_names
        if not aux_var_names and aux_var_profile:
            self.aux_var_names = self.AUX_VAR_PROFILES.get(aux_var_profile)

        # Time and calendar metadata.
        self.time_range = time_range
        if calendar and calendar not in cf_units.CALENDARS:
            raise ValueError("Invalid calendar type: %s" % calendar)
        self.calendar = calendar

        # Grid metadata.
        if grid_type not in self.GRID_TYPES:
            raise ValueError("Invalid grid type: %s" % grid_type)
        self.grid_type = grid_type

    def __str__(self):
        """Return a string containing selected properties of the variable."""
        if self.realization_id:
            suite_real = self.suite_id + '/' + self.realization_id
        else:
            suite_real = self.suite_id
        text = "{0} v{1}, {2}/{3}, {4} on {5}-grid".format(self.model_name,
            self.model_vn, suite_real, self.stream_id, self.name, self.grid_type)
        if self.time_range:
            start, end = self.time_range
            text += ", from {0} to {1}".format(start, end)
        return text

    def __deepcopy__(self, memo):
        """Return a deep copy of self."""
        # Create a new instance from mandatory arguments.
        mandatory_keys = ['model_vn', 'suite_id', 'var_name']
        mandatory_args = {k:self.__dict__[k] for k in mandatory_keys}
        new = CiceMetaVariable(**mandatory_args)

        # Deep-copy the remaining attributes from self.__dict__.
        for k, v in self.__dict__.items():
            if k in mandatory_keys: continue
            setattr(new, k, copy.deepcopy(v, memo))

        return new

    @property
    def name(self):
        """
        Returns the first non-null value taken from the following instance
        attributes: ``standard_name``, ``long_name``, ``var_name``.
        """
        return self.standard_name or self.long_name or self.var_name

    @property
    def slug(self):
        """
        Returns the value of the ``var_name`` attribute, i.e. the netCDF
        variable name.
        """
        return self.var_name

    def make_load_callback(self, id_only=False, do_time_check=False):
        """
        Construct a callback function which can be passed to an iris.load*()
        function so as to yield the *smallest* cubelist that satisfies the
        properties defined on a meta-variable object.

        :param bool id_only: If this option is enabled then the returned callback
            function only performs identity tests, i.e. against standard_name
            and var_name.
        :param bool do_time_check: If this option is enabled then the returned
            callback function includes a test for the source cube's start and
            end times lying within the meta-variable's time range, i.e.
            start <= T1 and T2 < end. This option is disabled by default because
            it is hard to anticipate the kinds of time-based filtering that
            client code might wish to perform.
        """
        def _cice_var_load_callback(cube, field, filename):

            if id_only is not None:
                if self.var_name:
                    if cube.var_name != self.var_name:
                        raise iris.exceptions.IgnoreCubeException()
                if self.standard_name:
                    if cube.standard_name != self.standard_name:
                        raise iris.exceptions.IgnoreCubeException()
                if id_only: return

            if self.calendar:
                if 'time' in [crd.name() for crd in cube.coords()]:
                    time = cube.coord('time')
                    if time.units.calendar != self.calendar:
                        if Version(iris.__version__) >= Version("3.3"):
                            #Work around for changes in iris 3.3 changing calendar
                            # attributes silently from gregorian to standard
                            self._iris_calendar_compatibility_check(time.units.calendar)
                        else:
                            raise iris.exceptions.IgnoreCubeException()

            if self.time_range and do_time_check:
                # Check that cube's time extent falls within time range.
                if 'time' in [crd.name() for crd in cube.coords()]:
                    time = cube.coord('time')
                    # Cubes derived from netcdf files may contain 2 or more
                    # time coordinates. The test below reflects this possibility.
                    if time.has_bounds():
                        # Analogous treatment as per T1 dates in UM PP data.
                        t1, t2 = time.bounds[0,0], time.bounds[-1,0]
                    else:
                        t1, t2 = time.points[0], time.points[-1]
                    t1, t2 = time.units.num2date((t1, t2))
                    if not (dateutils.pdt_compare(t1, 'ge', self.start_time) and
                            dateutils.pdt_compare(t2, 'lt', self.end_time)):
                        raise iris.exceptions.IgnoreCubeException()

        return _cice_var_load_callback


def _normalize_version_string(vn_str):
    """
    Normalize a version string into the form major.minor.micro replacing missing
    components with 0 where necessary.
    """
    if vn_str:
        parts = vn_str.strip().split('.') + ['0']*3
        vn_str = '.'.join(parts[:3])
    else:
        vn_str = '0.0.0'
    return vn_str


def _calendar_from_lbtim(lbtim):
    """Decode the calendar type from an LBTIM integer."""
    ical = lbtim % 10
    if ical == 1:
        # According to UM doc F3 this ought to be Proleptic Gregorian. However,
        # Iris uses plain Gregorian so we'll use that here to avoid conflicts.
        cal = cf_units.CALENDAR_GREGORIAN
    elif ical == 2:
        cal = cf_units.CALENDAR_360_DAY
    elif ical == 4:
        cal = cf_units.CALENDAR_365_DAY
    else:
        cal = None
    return cal
