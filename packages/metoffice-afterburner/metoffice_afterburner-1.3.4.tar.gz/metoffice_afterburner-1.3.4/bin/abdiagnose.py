#!/usr/bin/env python
# (C) British Crown Copyright 2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
SYNOPSIS

    abdiagnose.py

DESCRIPTION

    Utility script for displaying selected Afterburner runtime diagnostics. This
    script is likely to be useful in diagnosing issues or failures encountered
    within non-interactive runtime environments, e.g. batch jobs executed from
    Rose/cylc suites.

    The following information, if defined, is currently displayed to sys.stdout:

    - Host name

    - PYTHONPATH environment variable
    - SSS_ENV_DIR environment variable
    - SSS_TAG_DIR environment variable
    - SCITOOLS_MODULE environment variable
    - AFTERBURNER_HOME_DIR environment variable

    - SciTools module name
    - Python version
    - Python path
    - Rose version
    - Cylc version
    - Iris version
    - Afterburner version
    - Afterburner package path

ARGUMENTS

    None

OPTIONS

    None
"""

from __future__ import print_function

import os
import sys
import socket
import subprocess

os.environ['AFTERBURNER_PKG_LOG_LEVEL'] = '0'  # disable package usage logging


class AbDiagnoser(object):
    """
    Gathers and displays diagnostic information regarding the current runtime
    environment. The public API of the AbDiagnoser class mirrors that of the
    afterburner.apps.AbstractApp class. However, it intentionally does not
    inherit from the latter class since the afterburner package might not be
    available within the runtime environment.
    """

    def __init__(self, *args, **kwargs):
        self.returncode = 0   # reqd if this class is initialised by abrun.py

    def run(self, *args, **kwargs):
        """Run the diagnostics."""

        hdr = "AFTERBURNER RUNTIME DIAGNOSTICS"
        print("\n" + hdr)
        print('=' * len(hdr))

        try:
            print("Host name:", socket.gethostname())
            print()
            print("PYTHONPATH=" + os.environ.get('PYTHONPATH', '<undefined>'))
            print("SSS_ENV_DIR=" + os.environ.get('SSS_ENV_DIR', '<undefined>'))
            print("SSS_TAG_DIR=" + os.environ.get('SSS_TAG_DIR', '<undefined>'))
            print("SCITOOLS_MODULE=" + os.environ.get('SCITOOLS_MODULE', '<undefined>'))
            print("AFTERBURNER_HOME_DIR=" + os.environ.get('AFTERBURNER_HOME_DIR', '<undefined>'))
            print()
            print("SciTools module:", self._query_scitools_module())
            print("Python version:", repr(sys.version))
            print("Rose version:", self._query_rose_version())
            print("Cylc version:", self._query_cylc_version())
            print("Iris version:", self._query_iris_version())
            abvn, abpath = self._query_afterburner_pkg_info()
            print("Afterburner version:", abvn)
            print("Afterburner package path:", abpath)
        except:
            self.returncode = -1

        print()

    @property
    def cli_spec(self):
        """Return an empty CLI specification."""
        return []

    def _query_scitools_module(self):
        """Query the name of the currently loaded scitools module, if any."""

        scimod = 'indeterminate'

        try:
            result = subprocess.check_output('module -t list', shell=True,
                stderr=subprocess.STDOUT)
            if result:
                result = result.decode('utf8')
                for modname in result.split():
                    if modname.startswith('scitools'):
                        scimod = modname
        except subprocess.CalledProcessError:
            pass

        return scimod

    def _query_rose_version(self):
        """Query the version of the rose package."""

        rose_vn = 'not available'

        try:
            result = subprocess.check_output('rose --version', shell=True)
            if result:
                rose_vn = result.decode('utf8').strip()
        except subprocess.CalledProcessError:
            pass

        return rose_vn

    def _query_cylc_version(self):
        """Query the version of the cylc package."""

        cylc_vn = 'not available'

        try:
            result = subprocess.check_output('cylc --version', shell=True)
            if result:
                cylc_vn = result.decode('utf8').strip()
        except subprocess.CalledProcessError:
            pass

        return cylc_vn

    def _query_iris_version(self):
        """Query the version of the iris package."""

        try:
            import iris
            return iris.__version__
        except ImportError:
            return 'not available'

    def _query_afterburner_pkg_info(self):
        """Query the version and path of the afterburner package."""

        try:
            import afterburner
            return afterburner.__version__, afterburner.__file__.rpartition('/')[0]
        except ImportError:
            return 'not available', 'not available'


def main():
    "main entry point."

    # Check that a SciTools module has been loaded. We do this by checking to see
    # if the iris module is importable. Alternatively, it might be feasible to
    # check if the SSS_ENV_DIR environment variable has been defined.
    try:
        import iris
    except ImportError:
        print("\n"
            "*** Unable to import the Iris package. It looks like a SciTools\n"
            "*** module has not been loaded into the runtime environment.\n"
            "*** This may limit the amount of diagnostic information provided."
        )

    try:
        diagnoser = AbDiagnoser()
        diagnoser.run()
    except Exception as exc:
        msg = ("*** A problem was encountered gathering diagnostic information.\n"
               "*** Here's the error message:\n{}".format(str(exc)))
        print(msg)


if __name__ == '__main__':
    main()
