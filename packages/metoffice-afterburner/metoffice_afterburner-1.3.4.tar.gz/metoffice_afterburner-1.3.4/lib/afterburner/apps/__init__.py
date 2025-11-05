# (C) British Crown Copyright 2016-2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
This is the initialisation module for the afterburner.apps package, which acts
as a logical container for all Afterburner processing applications (or 'apps'
for short).

Each Afterburner app should be implemented as a dedicated class within its own
module below the afterburner.apps package. All application classes should
inherit from the :class:`AbstractApp` base class, which is defined below. This
class provides some basic attributes and methods that are likely to be needed
by all application classes. Refer to the class documentation for further details.

By way of example, a statistics generator application might be implemented via
a class named ``StatsGenerator`` within a module called ``afterburner.apps.stats_generator``.

If client code expects a particular application class to be visible from within
the afterburner.apps namespace then it should be imported at the foot of this
module (or at least *after* the definition of the AbstractApp class).
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six import add_metaclass

import abc
import importlib
import logging
import argparse

try:
    # The abstractproperty decorator was deprecated at Python 3.3
    from abc import abstractproperty
except ImportError:
    abstractproperty = lambda f: property(abc.abstractmethod(f))

from afterburner import __version__ as abvn
from afterburner import set_log_level, PACKAGE_LOGGER
from afterburner.app_config import AppConfig


def initialise_app(class_path, arglist=None):
    """
    Instantiate a processing application object defined either by the full path
    to the app class or by the class name alone. In the latter case it is assumed
    that the class name has been imported into the afterburner.apps namespace.

    This function is primarily intended to act as a convenient mechanism by which
    external Python scripts can invoke Afterburner application functionality in
    a generic way, one that does not require knowledge of class internals.

    :param str class_path: Either the full path specification of the app class,
        e.g. 'afterburner.apps.test_app.TestApp', or the unadorned class name,
        e.g. 'TestApp'.
    :param list arglist: List of raw options and/or arguments passed from the
        calling environment. Typically these will be unprocessed command-line
        arguments, e.g. ``['-f', 'foo', '--foe=fum', 'infile']``.
    :raises ImportError: Raised if the module defined in ``class_path``
        could not be found.
    :raises AttributeError: Raised if the class name defined in ``class_path``
        does not exist.
    """
    try:
        if '.' in class_path:
            # A dotted class path was passed in.
            module_path, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            klass = getattr(module, class_name)
        else:
            # A plain class name was passed in.
            module_path = __name__
            class_name = class_path
            klass = globals()[class_name]

        # Return an instance of the requested class.
        return klass(arglist)

    except ImportError:
        raise ImportError("Problem importing module '{0}'".format(module_path))

    except (AttributeError, KeyError):
        raise AttributeError("Class '{0}' is not defined in module '{1}'".format(
            class_name, module_path))


@add_metaclass(abc.ABCMeta)
class AbstractApp(object):
    """
    Defines the abstract base class which all Afterburner apps should inherit.
    Subclasses should define the application's command-line interface by over-
    riding the :attr:`cli_spec` property. The application's functionality should
    be specified by overriding the :meth:`run` method. The latter may of course
    call any number of private methods in order to implement that functionality.
    """

    def __init__(self, *args, **kwargs):
        """
        Extra Keyword Arguments (`**kwargs`):

        :param str_or_int log_level: The logging level to assign to app objects.
            The log level may be defined as one of the level names recognised by
            the logging module (e.g. 'WARN' or 'warn') or an equivalent integer
            (e.g. 30). Note, however, that this setting will be overridden if
            the calling code passes in an equivalent command-line option such as
            ``-q`` (quiet) or ``-v`` (verbose).
        :param str version: The version number to assign to app objects. If
            undefined, a default version number of '1.0' is used.
        """

        #: The application's string-valued version identifier (default is '1.0').
        self.version = kwargs.get('version', '1.0')

        #: A logger object for use by the application. See the :mod:`afterburner`
        #: module documentation for information about the default logger configuration.
        self.logger = logging.getLogger(__name__)

        # Set log level if passed in via a keyword argument of that name. This
        # feature is primarily intended for developer use. End-user control of
        # message output should normally be via the customary --quiet/--verbose
        # command-line options.
        if 'log_level' in kwargs:
            set_log_level(self.logger, kwargs['log_level'])

        #: A namespace object holding values parsed from any command-line options
        #: and arguments declared via the :attr:`cli_spec` property.
        self.cli_args = argparse.Namespace()

        #: An :class:`afterburner.app_config.AppConfig` object which can be used
        #: to store application configuration information read from a Rose
        #: configuration file. See the :meth:`_parse_app_config` method for
        #: further details.
        self.app_config = None

        #: Application return code. Typically this attribute should be updated
        #: by the run() method to indicate an application's completion status.
        #: The default return code is 0, signifying successful completion.
        self.returncode = 0

        # Log this app invocation unless the log_usage keyword evaluates false.
        if kwargs.get('log_usage', True):
            self.log_app_usage()

    @abstractproperty
    def cli_spec(self):
        """
        Defines the command-line interface specification for the application.
        This should be a list of dictionaries, each of which specifies a series
        of parameters to pass through to the :meth:`argparse.ArgumentParser.add_argument`
        method. The artificial example below illustrates how to specify various
        textual and numeric options::

            return [
                {'names': ['-v', '--verbose'], 'help': 'enable verbose mode'},
                {'names': ['-n', '--num'], 'type': int, 'default': 1},
                {'names': ['--deltax'], 'type': float},
                {'names': ['-o'], 'dest': 'opfile', 'help': 'output file'},
                {'names': ['arg1'], 'help': 'positional argument 1'},
            ]

        If no CLI arguments are required (over and above any globally-defined
        defaults) then an empty list should be returned.

        .. note:: The ArgumentParser class handles option and argument names differently
            if they contain a '-' character. An option name such as ``--log-level`` gets
            translated, as expected, to an attribute named ``log_level`` on the namespace
            object returned by the ArgumentParser.parse_args method. However, an argument
            named ``in-file`` does not get translated in the same way; it keeps the same
            name. This means that it is not possible to query the attribute value using
            standard dotted access notation, i.e. ``x = args.in-file`` will raise an
            exception.

            The recommended practice is to avoid using '-' in argument names. The metavar
            keyword argument may be used if you wish to change the name of the argument
            as displayed in the usage and help text, e.g.::

            {'names': ['infile'], 'metavar': 'in-file', 'help': 'input filename'},
        """
        raise NotImplementedError

    @abc.abstractmethod
    def run(self, *args, **kwargs):
        """Run the application."""
        raise NotImplementedError

    def log_app_usage(self, message=None):
        """
        Log the invocation of an application using the package logger created
        during initialisation of the afterburner package. If the package logger
        is undefined (e.g. because no TCP log server was contactable) then this
        method returns silently.

        :param str message: Optional text string to append to the auto-generated
            invocation message. If undefined then the text 'Invoked the <AppName> app'
            is used. Pass an empty string to prevent any extra text being appended.
        """
        if PACKAGE_LOGGER:
            if message is None:
                message = "Invoked the {} app".format(self.__class__.__name__)
            PACKAGE_LOGGER.info(message)

    def _parse_args(self, arglist, desc=None, epilog=None):
        """
        Parse command-line arguments according to the app's :attr:`cli_spec`
        property. Parsed options and/or arguments can subsequently be accessed
        via the application object's :attr:`cli_args` attribute.

        Attributes values should normally be accessed using standard dot notation,
        e.g, ``self.cli_args.verbose`` to obtain the value of a ``--verbose``
        command-line option, assuming that option is supported by the application.

        If there is a possibility that the target attribute has not been defined
        on the ``self.cli_args`` object then the ``getattr`` built-in function
        should be used. This, however, should not normally be necessary since an
        application should only be querying those options or arguments that it
        has formally declared as such (via the :attr:`cli_spec` property).

        :param list arglist: A list of command-line options and/or arguments
            passed to the application, either directly by the user or else via
            a Rose suite.
        :param str desc: The name of the program to display in the usage text.
        :param str epilog: A longer description of the program to append to the
            usage text.
        """
        prog = self.__class__.__name__
        parser = argparse.ArgumentParser(prog=prog, description=desc, epilog=epilog,
            conflict_handler='resolve')
        self._add_common_cli_args(parser)

        for adict in self.cli_spec or []:
            try:
                tmp_dict = adict.copy()
                names = tmp_dict.pop('names')
                parser.add_argument(*names, **tmp_dict)
            except:
                self.logger.error("Error in CLI argument specification:\n%s", adict)
                raise

        parser.parse_args(arglist or [], namespace=self.cli_args)

    def _parse_app_config(self, config_file=None):
        """
        Parse configuration options from a file in Rose's extended INI format
        and wrap it in an :class:`afterburner.app_config.AppConfig` object. Upon
        successful parsing of the file, configuration properties can be accessed
        via the instance attribute named ``app_config``.

        If an Afterburner application supports configuration via Rose - and it
        is envisaged that most will - then the current method should normally
        be invoked at an appropriate place within the ``__init__`` method of the
        application class.

        :param str config_file: Optional pathname of the configuration file to
            parse. If not specified then the command-line argument list is
            checked for a --config-file option.
        :raises AttributeError: If a configuration file was not specified via
            one of the aforementioned mechanisms.
        :raises IOError: If the configuration file does not exist.
        :raises rose.config.ConfigSyntaxError: If the configuration file contains
            syntax errors.
        """

        # If the config_file argument was not specified, check the --config-file
        # command-line argument
        if not config_file:
            config_file = getattr(self.cli_args, 'config_file', None)

        # Still no luck? Raise an exception.
        if not config_file:
            raise AttributeError("No configuration file specified.")

        try:
            self.app_config = AppConfig.from_file(config_file)
        except:
            self.logger.error("Error parsing configuration file %s", config_file)
            raise

    def _add_common_cli_args(self, parser):
        """Add command-line arguments common to all Afterburner apps."""
        parser.add_argument('-V', '--version', action='version', version=abvn,
            help='Show Afterburner version number and exit')
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-D', '--debug', action='store_true',
            help='Enable debug message mode')
        group.add_argument('-q', '--quiet', action='store_true',
            help='Enable quiet message mode')
        group.add_argument('-v', '--verbose', action='store_true',
            help='Enable verbose message mode')

    def _set_message_level(self):
        """
        Set logger message level based on the quiet/verbose/debug command-line
        arguments. The message level settings for the various arguments are as
        follows:

        * `--quiet` => error messages only
        * `--verbose` => informational messages and above
        * `--debug` => debug messages and above

        The default behaviour, i.e. in the absence of one of the aforementioned
        command-line arguments, is to display warning and error messages.
        """
        try:
            if self.cli_args.quiet:
                self.logger.setLevel(logging.ERROR)
            elif self.cli_args.verbose:
                self.logger.setLevel(logging.INFO)
            elif self.cli_args.debug:
                self.logger.setLevel(logging.DEBUG)
        except AttributeError:
            pass


# If client code expects a particular app class to be visible from within the
# afterburner.apps namespace then it should be imported below using the
# following syntax:
#
# from afterburner.apps.<module_name> import <app_class_name>

from afterburner.apps.asov_calculator import AsovCalculator
from afterburner.apps.diagnostic_generator import DiagnosticGenerator
from afterburner.apps.inline_regridder import InlineRegridder
from afterburner.apps.jet_speed_calc import JetSpeedCalculator
from afterburner.apps.model_emulators import UmEmulator, NemoEmulator, CiceEmulator
from afterburner.apps.model_monitor import ModelMonitor
from afterburner.apps.model_monitor2 import ModelMonitor2
from afterburner.apps.mass_data_robot import MassDataRobot
