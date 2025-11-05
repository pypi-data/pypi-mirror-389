# (C) British Crown Copyright 2016-2023, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The current module, together with the other modules in the afterburner.utils
package, contains various utility classes and functions.

**Index of Classes and Functions in this Module**

.. autosummary::
   :nosignatures:

   NamespacePlus
   NumericInterval
   OpenInterval
   LeftOpenInterval
   LeftClosedInterval
   ClosedInterval
   get_class_object_from_class_path
   get_cylc_task_work_dir
   get_cylc_variables
   is_numeric
   is_string
   is_iterable
   is_sequence
   is_non_string_iterable
   is_non_string_sequence
   is_true
   lru_cache
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import integer_types, string_types

import os
import copy
import importlib
import argparse
import numbers
import numpy as np
import functools
from collections import namedtuple, OrderedDict
try:
    # Python <= 3.9
    from collections import Iterable, Sequence
except ImportError:
    # Python > 3.9
    from collections.abc import Iterable, Sequence
from afterburner.exceptions import ClassNotFoundError

# Symbolic constants representing the four types of numeric interval implemented
# (as classes) in this module.
INTERVAL_OPEN = 'open'
INTERVAL_LEFTOPEN = 'leftopen'
INTERVAL_LEFTCLOSED = 'leftclosed'
INTERVAL_CLOSED = 'closed'


class NamespacePlus(argparse.Namespace):
    """
    Extends the argparse.Namespace class with a ``__getattr__`` method that
    returns None for non-existent instance attributes. A side-effect of this
    behaviour is that a call to ``hasattr(object, name)``, where object is an
    instance of this class, will return True for *all* names. Accordingly, the
    :meth:`has_name` method should be used to test whether or not an instance
    contains an attribute with a particular name.

    The :meth:`iter_names` method can be used to iterate over all attribute names;
    wrapping this iterator within the ``sorted`` built-in function will yield a
    sorted list of names. It is also possible to iterate over a NamespacePlus
    object, the result being an unordered sequence of (name, value) tuples.
    """
    def __init__(self, *args, **kwargs):
        super(NamespacePlus, self).__init__(*args, **kwargs)

    def __getattr__(self, name):
        return None

    def __copy__(self):
        """Return a shallow copy of self."""
        return NamespacePlus(**self.__dict__)

    def __deepcopy__(self, memo):
        """Return a deep copy of self."""
        new = NamespacePlus()
        for k, v in self.__dict__.items():
            setattr(new, k, copy.deepcopy(v, memo))
        return new

    def copy(self):
        """Return a deep copy of self."""
        return self.__deepcopy__({})

    def __iter__(self):
        """
        Returns an iterator which yields a (name, value) tuple for each attribute
        currently attached to self. The order in which the items are returned is
        not guaranteed. If it is required to obtain the items ordered alphabetically
        by attribute name then the :meth:`iter_names` method should first be used
        to obtain a sorted list of names, e.g. ``sorted(o.iter_names())``.
        """
        return iter(self.__dict__.items())

    def iter_names(self):
        """
        Returns an iterator which yields the names of all attributes currently
        attached to self. The order in which the names are returned is not
        guaranteed.
        """
        return self.__dict__.keys()

    def has_name(self, name):
        """
        Tests to see if ``name`` is an attribute of self. This method should be
        used instead of a call to the ``hasattr()`` built-in function.
        """
        return name in self.__dict__


class NumericInterval(namedtuple('_NumericInterval', ['start', 'stop'])):
    """
    Base class for representing a numeric interval. Client code should use one
    of the subclasses defined below. The interval end-points are defined by
    Python or Numpy numeric values.

    :param start: The start value of the interval. Negative infinity (``float('-inf')``)
        is a valid start value.
    :param stop: The end value of the interval. Positive infinity (``float('inf')``)
        is a valid end value.
    :raises ValueError: Raised if either ``start`` or ``stop`` is non-numeric.
    """
    slots = ()

    def __init__(self, start, stop):
        if not isinstance(start, (numbers.Number, np.number)):
            raise ValueError("NumericInterval: start attribute must be numeric.")
        if not isinstance(stop, (numbers.Number, np.number)):
            raise ValueError("NumericInterval: stop attribute must be numeric.")

    @property
    def ascending(self):
        """
        True if the interval's start value is less than or equal to the end
        value -- the most common case.
        """
        return self.start <= self.stop

    @property
    def descending(self):
        """
        True if the interval's start value is greater than the end value.
        """
        return self.start > self.stop

    def contains(self, value):
        """Returns true if ``value`` lies within the interval, else false."""
        raise NotImplementedError


class OpenInterval(NumericInterval):
    """Class for representing an open numeric interval, i.e. (a,b)."""

    def contains(self, value):
        """Returns true if ``value`` lies within the interval, else false."""
        if self.ascending:
            return self.start < value < self.stop
        else:
            return self.stop < value < self.start


class LeftOpenInterval(NumericInterval):
    """Class for representing a left-open, right-closed numeric interval, i.e. (a,b]."""

    def contains(self, value):
        """Returns true if ``value`` lies within the interval, else false."""
        if self.ascending:
            return self.start < value <= self.stop
        else:
            return self.stop <= value < self.start


class LeftClosedInterval(NumericInterval):
    """Class for representing a left-closed, right-open numeric interval, i.e. [a,b)."""

    def contains(self, value):
        """Returns true if ``value`` lies within the interval, else false."""
        if self.ascending:
            return self.start <= value < self.stop
        else:
            return self.stop < value <= self.start


class ClosedInterval(NumericInterval):
    """Class for representing a closed numeric interval, i.e. [a,b]."""

    def contains(self, value):
        """Returns true if ``value`` lies within the interval, else false."""
        if self.ascending:
            return self.start <= value <= self.stop
        else:
            return self.stop <= value <= self.start


def get_class_object_from_class_path(class_path):
    """
    Get a class object given a class name or dotted path defined in a string.
    In the former case (name only), the class is assumed to be defined within
    the module from which this function was invoked.

    :param str class_path: The class name, e.g. 'RainMaker', or full dotted
        class path, e.g. 'weather.precip.RainMaker'.
    :raises afterburner.exceptions.ClassNotFoundError: Raised if the specified
        could not be found or imported.
    """
    try:
        if '.' in class_path:
            modpath, _sep, classname = class_path.rpartition('.')
            mod = importlib.import_module(modpath)
            cls = getattr(mod, classname)
        else:
            cls = globals()[class_path]
    except (KeyError, AttributeError, ImportError):
        raise ClassNotFoundError("Unable to locate or import class: " + class_path)

    return cls


def get_cylc_task_work_dir(task_name, default=''):
    """
    Return the cylc work directory for the specified task, or the value of the
    ``default`` argument if no task directory could be determined.

    If ``task_name`` is equal to the current cylc task then the returned directory
    path is provided by the CYLC_TASK_WORK_DIR environment variable. Otherwise
    the directory path is constructed by appending the task name to the parent
    directory of CYLC_TASK_WORK_DIR.

    For example, if CYLC_TASK_WORK_DIR is set to '/path/to/suite/work/cycle/foo',
    and ``task_name`` is set to 'bar', then the returned path would be equal to
    '/path/to/suite/work/cycle/bar'.

    :param str task_name: The name of the cylc task whose work directory is to
        be looked up.
    :param str default: The value to return if the cylc task work directory
        cannot be determined (e.g. when no cylc environment is defined).
    :returns: The work directory for the named cylc task.
    """

    task_work_dir = os.environ.get('CYLC_TASK_WORK_DIR')

    if not task_work_dir:
        return default
    elif task_name == os.environ.get('CYLC_TASK_NAME'):
        # task_name refers to the current task so return its work directory
        return task_work_dir
    else:
        # task_name refers to some other task, in which case we assume its
        # work directory is a child of the current task's parent directory
        cycle_dir = os.path.dirname(task_work_dir)
        return os.path.join(cycle_dir, task_name)


def get_cylc_variables():
    """
    Read all cylc variables defined in the current environment and return them as
    attributes of a NamespacePlus object. The attribute names are equivalent to
    lower-case versions of the CYLC environment variables but without the 'CYLC\_'
    prefix. For example the ``task_name`` attribute contains the value of the
    CYLC_TASK_NAME environment variable.

    The returned object also contains an attribute named ``is_active``, which is
    set to True if the cylc environment is active, or False otherwise. The cylc
    environment is deemed to be active if CYLC_SUITE_NAME is defined.

    :returns: A :class:`NamespacePlus` object whose attributes mirror all defined
        CYLC_* environment variables, converted to lower-case and minus the 'CYLC\_'
        prefix.
    """

    if os.environ.get('CYLC_SUITE_NAME'):
        cylc_vars = NamespacePlus(is_active=True)
        for name, value in os.environ.items():
            if name.startswith('CYLC_') and len(name) > 5:
                setattr(cylc_vars, name[5:].lower(), value)
    else:
        cylc_vars = NamespacePlus(is_active=False)

    return cylc_vars


def is_numeric(obj) :
    """
    Returns True if obj is one of Python's numeric types, i.e. int, long (Python
    2 only), float or complex. Otherwise returns False.

    Note: Although the boolean objects True and False are, strictly speaking, of
    numeric type they are not treated as such by this function.
    """
    return isinstance(obj, numbers.Number) and not isinstance(obj, bool)


def is_string(obj) :
    """
    Returns True if obj is a string-type object. Otherwise returns False.
    """
    return isinstance(obj, string_types)


def is_iterable(obj) :
    """
    Returns True if obj is an iterable object, including strings. Otherwise
    returns False.
    """
    return isinstance(obj, Iterable)


def is_sequence(obj) :
    """
    Returns True if obj is a sequence-type object, including strings, whose
    elements can be accessed via integer-based indexing/slicing. Otherwise
    returns False.
    """
    return isinstance(obj, (Sequence, bytearray))


def is_non_string_iterable(obj) :
    """
    Returns True if obj is a non-string iterable object. Otherwise returns False.
    """
    return is_iterable(obj) and not is_string(obj)


def is_non_string_sequence(obj) :
    """
    Returns True if obj is a non-string sequence-type object whose elements can
    be accessed via integer-based indexing/slicing. Otherwise returns False.
    """
    return is_sequence(obj) and not is_string(obj)


def is_true(value):
    """
    Test to see if the function's argument is equivalent to commonly accepted
    representations of 'truthfulness'. The argument value is considered to be
    true if it meets any of the following tests:

    * value == True
    * value == 1
    * value in ['t', 'true', '.true.', 'on', 'y', 'yes', '1'] plus any upper or
      mixed case variants of these text strings

    Conversely, the argument value is considered to be false if it meets any of
    the following tests:

    * value == False
    * value == 0
    * value in ['f', 'false', '.false.', 'off', 'n', 'no', '0'] plus any upper or
      mixed case variants of these text strings

    For all other argument values the function returns None.

    Note that the aforementioned tests are, by design, more restrictive than
    those used by Python's standard ``bool()`` builtin function. The principal
    use of the current function is to test the truth-nature of a user-supplied
    value, which will often be a text string.

    :param any value: The value to test.
    :returns: True if ``value`` is true-valued, False if it is false-valued,
        otherwise None.
    """
    if isinstance(value, bool):
        return value

    elif isinstance(value, string_types):
        true_values = ['t', 'true', '.true.', 'on', 'y', 'yes', '1']
        false_values = ['f', 'false', '.false.', 'off', 'n', 'no', '0']
        if value.lower() in true_values:
            return True
        elif value.lower() in false_values:
            return False

    elif isinstance(value, integer_types):
        if value == 0:
            return False
        elif value == 1:
            return True

    return None


def lru_cache(maxsize=32):
    """
    Least-recently-used cache decorator function. For more information see:
    http://code.activestate.com/recipes/498245-lru-and-lfu-cache-decorators/.
    As of Python 3.2 this function is included in the functools module.

    Arguments to the cached function must be hashable. Cache performance
    statistics are stored in f.hits and f.misses.

    :param int maxsize: Maximum size (number of items) of the cache. Use the
        f.hits and f.misses instrumentation to tune the best setting for maxsize
        that yields the optimum trade-off between hit-rate and space consumed.
    """
    def decorating_function(user_function):
        cache = OrderedDict()    # order: least recent to most recent

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            key = args
            if kwds:
                key += tuple(sorted(kwds.items()))
            try:
                result = cache.pop(key)
                wrapper.hits += 1
            except KeyError:
                result = user_function(*args, **kwds)
                wrapper.misses += 1
                if len(cache) >= maxsize:
                    cache.popitem(0)    # purge least recently used cache entry
            cache[key] = result         # record recent use of this key
            return result
        wrapper.hits = wrapper.misses = 0
        return wrapper

    return decorating_function
