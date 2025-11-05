# (C) British Crown Copyright 2016-2018, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Contains the :class:`AppConfig` class to read Rose configuration files. This
class wraps the ``rose_config.ConfigNode`` class to provide additional
functionality.
"""
from __future__ import (absolute_import, division)
from six.moves import (filter, input, map, range, zip)
from six import string_types

import re
import sys
from functools import cmp_to_key

if sys.version_info.major == 3:
    # Python 3 compatible implementation of the rose.config module.
    from afterburner.contrib import rose_config
    from afterburner.contrib.rose_config import ConfigNode
else:
    import rose.config as rose_config
    from rose.config import ConfigNode


class AppConfig(ConfigNode):
    """
    Read Rose configuration files. This extends ``rose_config.ConfigNode`` to
    provide additional functionality. A tree of AppConfig objects is formed.
    Values from the configuration file can then be obtained from the root node
    of the tree.
    """
    def __init__(self, value=None, state=ConfigNode.STATE_NORMAL, comments=None):
        """
        :param value: The value of the AppConfig object, typically a dict or
            str.
        :param str state: The ignore state of the object. Either '', '!' or '!!'.
        :param str comments: Any comments about the object.
        :raises ValueError: If ``state`` is not an allowed value.
        """
        allowed_states = [ConfigNode.STATE_NORMAL,
            ConfigNode.STATE_USER_IGNORED, ConfigNode.STATE_SYST_IGNORED]
        if state not in allowed_states:
            msg = "State '{}' is not an allowed value.".format(state)
            raise ValueError(msg)
        ConfigNode.__init__(self, value, state, comments)

    @staticmethod
    def from_file(filename):
        """
        Create an instance from a Rose configuration file.

        :param str filename: The path of the Rose configuration file to load.
        :returns: An AppConfig object containing the loaded Rose configuration
            file.
        :rtype: afterburner.app_config.AppConfig
        """
        rose_cfg = rose_config.load(filename)
        return AppConfig(rose_cfg.value, rose_cfg.state, rose_cfg.comments)

    def get_property(self, section, prop_name, default=None):
        """
        Get a string from the specified ``section`` and ``prop_name`` of the
        object.

        :param str section: The name of the section. An empty string indicates
            the root level of the configuration file.
        :param str prop_name: The name of the property.
        :param str default: The default value to return if the specified
            property does not exist.
        :returns: The string property value specified or default if it doesn't
            exist.
        """
        return self.get_value([section, prop_name], default)

    def get_int_property(self, section, prop_name, default=None):
        """
        Get an integer from the specified ``section`` and ``prop_name`` of the
        object.

        :param str section: The name of the section. An empty string indicates
            the root level of the configuration file.
        :param str prop_name: The name of the property.
        :param int default: The default value to return if the specified
            property does not exist.
        :returns: The integer property value specified or default if it doesn't
            exist.
        :rtype: int
        :raises ValueError: If the property value cannot be converted to an
            integer.
        """
        int_str = self.get_value([section, prop_name], default)
        if int_str is None:
            return default
        try:
            return int(int_str)
        except ValueError:
            raise ValueError("Could not convert section '{}' and property "
                "name '{}' to an integer: '{}'".format(section, prop_name,
                int_str))

    def get_float_property(self, section, prop_name, default=None):
        """
        Get a float from the specified ``section`` and ``prop_name`` of the
        object.

        :param str section: The name of the section. An empty string indicates
            the root level of the configuration file.
        :param str prop_name: The name of the property.
        :param float default: The default value to return if the specified
            property does not exist.
        :returns: The floating point property value specified or default if it
            doesn't exist.
        :rtype: float
        :raises ValueError: If the property value cannot be converted to a
            float.
        """
        float_value = self.get_value([section, prop_name], default)
        if float_value is None:
            return default
        try:
            return float(float_value)
        except ValueError:
            raise ValueError("Could not convert section '{}' and property "
                "name '{}' to a float: '{}'".format(section, prop_name,
                float_value))

    def get_bool_property(self, section, prop_name, default=None):
        """
        Get a boolean from the specified ``section`` and ``prop_name`` of the
        object. The case of the value in the file is ignored.

        :param str section: The name of the section. An empty string indicates
            the root level of the configuration file.
        :param str prop_name: The name of the property.
        :param bool default: The default value to return if the specified
            property does not exist.
        :returns: The boolean property value specified or default if it doesn't
            exist.
        :rtype: bool
        :raises ValueError: If the property value cannot be converted to a
            boolean.
        """
        bl = self.get_value([section, prop_name], default)
        if isinstance(bl, string_types):
            if 'TRUE' in bl.upper():
                return True
            elif 'FALSE' in bl.upper():
                return False
            else:
                raise ValueError("Could not convert section '{}' and property "
                    "name '{}' to a boolean: '{}'".format(section, prop_name, bl))
        else:
            return bool(bl)

    def get_nl_property(self, namelist, index, prop_name, default=None):
        """
        Get a property from a specific namelist. e.g.::

            [namelist:fruits(0)]
            colour=yellow

            >> cfg.get_nl_property('fruits', '0', 'colour')
            'yellow'

        :param str namelist: The namelist's name.
        :param str index: The index of the namelist item.
        :param str prop_name: The name of the property.
        :param str default: The default value to return if the specified
            property does not exist.
        :returns: The string property value specified or default if it doesn't
            exist.
        :rtype: str
        """
        index_name = 'namelist:{}({})'.format(namelist, index)
        return self.get_value([index_name, prop_name], default)

    def iter_nl(self, namelist, callback=None):
        """
        A generator function to loop through the items in the specified
        namelist, which is first sorted into alphanumeric order, and return
        dictionaries containing each item's data. e.g.::

            [namelist:fruits(0)]
            colour=yellow
            [namelist:fruits(1)]
            colour=orange

            >> for item in cfg.iter_nl('fruits'):
            ...     print(item)
            {'_index': '0', 'colour': 'yellow'}
            {'_index': '1', 'colour': 'orange'}

        The index of each item is included in the returned dictionary with the
        key '_index'.

        :param str namelist: The namelist's name.
        :param function callback: An optional user-supplied function. It should
            accept a dictionary containing the namelist item's properties and
            return a boolean indicating if this namelist item should be output.
        :returns: A dictionary containing the data for this namelist item. The
            dictionary's keys are the namelist item's property names and the
            dictionary values are the property values. The index of this item is
            included with a key of '_index'.
        :rtype: dict
        """
        section_keys = list(self.value.keys())
        sorter = rose_config.sort_settings
        section_keys.sort(key=cmp_to_key(sorter))
        section_name = r'namelist:{}\((.+)\)'.format(namelist)

        for sect_key in section_keys:
            node = self.get([sect_key])
            if node.is_ignored():
                continue
            index_match = re.findall(section_name, sect_key)
            if isinstance(node.value, dict) and index_match:
                sub_keys = list(node.value.keys())
                index_str = index_match[0]
                output = {'_index': index_str}
                for key in sub_keys:
                    output[key] = node.get_value([key])
                if callback:
                    if callback(output):
                        yield output
                else:
                    yield output

    def section_to_dict(self, section, use_ignored=False):
        """
        Convert a top-level configuration section to a plain dict object. The
        ``use_ignored`` argument can be used to control whether or not ignored
        values are included in the dictionary.

        :param str section: The name of the section to convert to a dictionary.
        :param bool used_ignored: Indicates whether or not to use the *actual*
            values of configuration items that are marked as ignored. The default
            behaviour is to include such items in the dictionary but with a None
            value. This mirrors the behaviour of the ``get_value()`` method.
        :returns: A dictionary containing the key-value pairs defined in the
            requested configuration section.
        """
        if section not in self.get_value().keys():
            raise ValueError("Section '{}' does not occur in AppConfig "
                "object.".format(section))

        dct = {}
        sect_node = self.get([section])

        for item_keys, item_node in sect_node.walk():
            if item_node.is_ignored() and not use_ignored:
                dct[item_keys[-1]] = None
            else:
                dct[item_keys[-1]] = item_node.get_value()

        return dct
