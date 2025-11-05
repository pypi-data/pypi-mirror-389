# (C) British Crown Copyright 2016, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Unit tests for the afterburner logging functionality, as defined within the
afterburner.__init__ module.
"""
from __future__ import (absolute_import, division)
from six.moves import (filter, input, map, range, zip)

import os
import sys
import logging
import tempfile
import unittest
import afterburner

# Some test cases make use of the third-party testfixtures module (MIT licence,
# see https://github.com/Simplistix/testfixtures).
# If this module is not installed locally then those tests are skipped.
try:
    import testfixtures
except ImportError:
    pass


class TestLogging(unittest.TestCase):
    """Unit tests for exercising afterburner logging functionality."""

    def setUp(self):
        self.logger = lgr = logging.getLogger('afterburner')
        self.orig_level = lgr.level

        # For some reason, as yet unexplained, the tests will only work with
        # the propagate option enabled.
        self.orig_propagate = lgr.propagate
        lgr.propagate = True

        # Redirect log messages to a temporary file so that they do not
        # interfere with output from the test suite.
        self.orig_hdlrs = lgr.handlers
        _fh, tmplogfile = tempfile.mkstemp()
        fhdlr = logging.FileHandler(tmplogfile)
        fhdlr.setLevel(logging.DEBUG)
        lgr.handlers = [fhdlr]
        self.tmplogfile = tmplogfile

    def tearDown(self):
        self.logger.level = self.orig_level
        self.logger.propagate = self.orig_propagate
        self.logger.handlers = self.orig_hdlrs
        if os.path.exists(self.tmplogfile): os.remove(self.tmplogfile)

    @unittest.skipUnless('testfixtures' in sys.modules, "testfixtures module not found")
    def test_info_level_cutoff(self):
        from testfixtures import LogCapture
        self.logger.setLevel(logging.INFO)
        with LogCapture() as lc:
            msg = "test message"
            self.logger.debug(msg)   # should not get logged
            self.logger.info(msg)
            self.logger.warning(msg)
            self.logger.error(msg)
            lc.check(('afterburner', 'INFO', msg),
                     ('afterburner', 'WARNING', msg),
                     ('afterburner', 'ERROR', msg))
            lc.uninstall()

    @unittest.skipUnless('testfixtures' in sys.modules, "testfixtures module not found")
    def test_warning_level_cutoff(self):
        from testfixtures import LogCapture
        self.logger.setLevel(logging.WARNING)
        with LogCapture() as lc:
            msg = "test message"
            self.logger.debug(msg)   # should not get logged
            self.logger.info(msg)    # should not get logged
            self.logger.warning(msg)
            self.logger.error(msg)
            lc.check(('afterburner', 'WARNING', msg),
                     ('afterburner', 'ERROR', msg))
            lc.uninstall()

    @unittest.skipUnless('testfixtures' in sys.modules, "testfixtures module not found")
    def test_error_level_cutoff(self):
        from testfixtures import LogCapture
        self.logger.setLevel(logging.ERROR)
        with LogCapture() as lc:
            msg = "test message"
            self.logger.debug(msg)   # should not get logged
            self.logger.info(msg)    # should not get logged
            self.logger.warning(msg) # should not get logged
            self.logger.error(msg)
            lc.check(('afterburner', 'ERROR', msg))
            lc.uninstall()

if __name__ == '__main__':
    unittest.main()
