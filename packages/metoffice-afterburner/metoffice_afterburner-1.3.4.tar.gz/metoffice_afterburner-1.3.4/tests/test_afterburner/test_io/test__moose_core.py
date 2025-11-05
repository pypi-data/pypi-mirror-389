# (C) British Crown Copyright 2022, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Unit tests for the afterburner.io._moose_core module.
"""
import unittest

from afterburner.io._moose_core import convert_msi_to_numeric


class TestConvert(unittest.TestCase):

    def test_convert_msi_to_numeric(self):
        msi = "m12s34i567"
        output = convert_msi_to_numeric(msi)
        expected = "34567"
        self.assertEqual(output, expected)
