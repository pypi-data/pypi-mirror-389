# (C) British Crown Copyright 2016, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Units tests for the afterburner.processors.example_proc module.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import unittest
import iris
from iris.tests.stock import simple_1d, simple_2d, simple_3d
from afterburner.processors.example_proc import ExampleProcessor


class TestExampleProcessor(unittest.TestCase):
    """Test the ExampleProcessor class."""

    def setUp(self):
        cubelist = iris.cube.CubeList([simple_1d(), simple_2d(), simple_3d()])
        self.proc = ExampleProcessor(cubelist)

    def test_init(self):
        self.assertEqual(self.proc.processor_name, 'ExampleProcessor')

    def test_run(self):
        self.proc.run()
        for cube in self.proc.cubelist:
            self.assertEqual(cube.attributes['history'], 'Set by ExampleProcessor')


if __name__ == '__main__':
    unittest.main()
