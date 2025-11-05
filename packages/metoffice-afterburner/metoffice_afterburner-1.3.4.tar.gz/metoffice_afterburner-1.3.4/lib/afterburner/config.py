# (C) British Crown Copyright 2016, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Contains the ConfigProvider class, which may be used to obtain information
relating to the configuration of Afterburner software artifacts, e.g. the
location of key directories and configuration files.

For information regarding the configuration of individual Afterburner end-user
applications, refer to the :mod:`afterburner.app_config` module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)
from six.moves.configparser import ConfigParser

import os
from afterburner.exceptions import ConfigurationError
from afterburner.utils.fileutils import truncate_path


class ConfigProvider(object):
    """
    Encapsulates the logic for providing Afterburner configuration information.
    This configuration information falls roughly into two categories:

    1. Information relating to the location of key directories and files
    comprising the installed Afterburner software (of which this module is
    a part).

    2. Configuration properties defined within either or both of a site
    configuration file and a user configuration file. The pathnames of these
    files can be obtained via the :attr:`site_config_file` and
    :attr:`user_config_file` attributes of this class. Specific configuration
    options may be queried via the :meth:`get_config_option` method.
    """

    def __init__(self):
        self._home_dir = ''
        self._bin_dir = ''
        self._etc_dir = ''
        self._template_dir = ''
        self._site_config_file = ''
        self._user_config_file = ''
        self._config_parser = None
        self._lib_dir = truncate_path(os.path.abspath(__file__), 'lib', right=True)
        if not self._lib_dir:
            raise ConfigurationError("Unable to find 'lib' directory among "
                "ancestors of {0} module.".format(__name__))

    @property
    def home_dir(self):
        """The home directory of the Afterburner software suite."""
        if not self._home_dir:
            self._home_dir = os.path.dirname(self._lib_dir)
        return self._home_dir

    @property
    def bin_dir(self):
        """The bin directory of the Afterburner software suite."""
        if not self._bin_dir:
            self._bin_dir = os.path.join(self.home_dir, 'bin')
        return self._bin_dir

    @property
    def etc_dir(self):
        """The etc directory of the Afterburner software suite."""
        if not self._etc_dir:
            self._etc_dir = os.path.join(self.home_dir, 'etc')
        return self._etc_dir

    @property
    def template_dir(self):
        """The etc/template directory of the Afterburner software suite."""
        if not self._template_dir:
            self._template_dir = os.path.join(self.etc_dir, 'templates')
        return self._template_dir

    @property
    def site_config_file(self):
        """The pathname of the Afterburner site configuration file."""
        if not self._site_config_file:
            self._site_config_file = os.path.join(self.etc_dir, 'afterburner.conf')
        return self._site_config_file

    @property
    def user_config_file(self):
        """The pathname of the Afterburner user configuration file."""
        if not self._user_config_file:
            home_dir = os.path.expandvars(os.environ['HOME'])
            self._user_config_file = os.path.join(home_dir, '.config',
                'afterburner', 'afterburner.conf')
        return self._user_config_file

    def get_config_option(self, section, option, default=''):
        """
        Return the value of the ``option`` property from the specified ``section``
        of the user or site configuration file. The files are searched in that
        order, although neither file need necessarily exist.

        If the option is not defined, return the value assigned to ``default``.

        :param str section: The section name in which to search for ``option``.
        :param str option: The name of the configuration option to search for.
        :param default: Default value to use if ``option`` is not defined.
        :returns: The text value of the requested configuration option.
        :rtype: str
        """
        if not self._config_parser:
            self._config_parser = ConfigParser()
            self._config_parser.read([self.site_config_file, self.user_config_file])

        if section.lower() == 'default': section = 'DEFAULT'

        if self._config_parser.has_option(section, option):
            return self._config_parser.get(section, option)
        else:
            return default
