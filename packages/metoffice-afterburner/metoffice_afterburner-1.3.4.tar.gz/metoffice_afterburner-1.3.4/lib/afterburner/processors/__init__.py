# (C) British Crown Copyright 2016-2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The afterburner.processors package acts as a logical container for Afterburner
processors. These processors are expected to form the basic building blocks of
most Afterburner end-user applications.

All processor classes should subclass the :class:`AbstractProcessor` class, which is
defined in this module. In normal circumstances each processor class should be
implemented within a dedicated module below the afterburner.processors package.
In some situations, however, it may be practical to implement a small number of
closely related processor classes within the same module.

The :class:`ExampleProcessor <afterburner.processors.example_proc.ExampleProcessor>` class
provides a rudimentary example of a concrete processor class.

If client code expects a particular processor class to be visible from within
the afterburner.processors namespace then it should be imported at the foot of
this module (or at least *after* the definition of the AbstractProcessor class).
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import add_metaclass

import logging
from abc import ABCMeta, abstractmethod
from afterburner import set_log_level


@add_metaclass(ABCMeta)
class AbstractProcessor(object):
    """
    Defines the abstract base class for Afterburner processing operations.
    All concrete subclasses should implement the :meth:`run` method. Typically
    they will also need to override the :meth:`__init__` method in order to
    execute any processor-specific initialisation code.
    """

    def __init__(self, *args, **kwargs):
        """
        Extra Keyword Arguments (`**kwargs`):

        :param int/str log_level: The log level to assign to the logger object
            named `afterburner.processors`. The specified level will apply until
            it is reset by a subsequent call. The level may be defined either as
            an integer, e.g. 40, or a string, e.g. 'error'.
        """

        #: A logger object for use by the processor. See the :mod:`afterburner`
        #: module documentation for information about the default logger configuration.
        self.logger = logging.getLogger(__name__)

        # Set log level if passed in via a keyword argument of that name. This
        # feature is primarily intended for developer use.
        if 'log_level' in kwargs:
            set_log_level(self.logger, kwargs['log_level'])

        self.logger.debug("Initialising %s processor object...",
            self.__class__.__name__)

    def __call__(self, *args, **kwargs):
        """
        Invokes the :meth:`run` method, thus enabling instance objects to be
        called directly if desired. For example::

            >>> processor = CustomProcessor(init_args)
            >>> cubes = processor(arg1, arg2, ...)
        """
        return self.run(*args, **kwargs)

    @abstractmethod
    def run(self, *args, **kwargs):
        """Run the processor."""
        raise NotImplementedError


class NullProcessor(AbstractProcessor):
    """
    Defines a null processor class which, in normal mode, does nothing. If the
    logging level is set to DEBUG then it emits a debug message comprising the
    name of the called method. The primary intended use is in code testing and
    debugging.
    """

    def __init__(self, *args, **kwargs):
        super(NullProcessor, self).__init__(*args, **kwargs)
        self.logger.debug("In NullProcessor.__init__() method.")

    def run(self, *args, **kwargs):
        """Run the processor."""
        self.logger.debug("In NullProcessor.run() method.")


# If client code expects a particular processor class to be visible from within
# the afterburner.processors namespace then it should be imported below using
# the following syntax:
#
# from afterburner.processors.<module_name> import <processor_class_name>
