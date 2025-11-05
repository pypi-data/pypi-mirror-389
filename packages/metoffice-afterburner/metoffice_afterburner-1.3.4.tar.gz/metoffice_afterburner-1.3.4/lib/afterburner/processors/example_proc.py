# (C) British Crown Copyright 2016, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Defines an example Afterburner processor class, i.e. a concrete subclass of
afterburner.processors.AbstractProcessor.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import logging
from afterburner.processors import AbstractProcessor


class ExampleProcessor(AbstractProcessor):
    """
    Defines an example Afterburner processor class for illustration purposes.
    This processor takes an Iris cubelist as input. When the processor is run
    it sets the history attribute and then prints the name of each cube in turn.
    """

    def __init__(self, cubelist):
        super(ExampleProcessor, self).__init__()
        self.cubelist = cubelist
        self.processor_name = self.__class__.__name__
        self.logger.setLevel(logging.INFO)
        self.logger.info("Initialised %s object.", self.processor_name)

    def run(self):
        """Run the processor."""
        self.logger.info("In %s.run()", self.processor_name)
        self._set_history_attr()
        self.logger.info("Names of cubes:")
        for i, cube in enumerate(self.cubelist):
            self.logger.info("   Cube %s: %s", i, cube.name())

    def _set_history_attr(self):
        """Set the history attribute on each input cube."""
        for cube in self.cubelist:
            cube.attributes['history'] = "Set by " + self.processor_name
