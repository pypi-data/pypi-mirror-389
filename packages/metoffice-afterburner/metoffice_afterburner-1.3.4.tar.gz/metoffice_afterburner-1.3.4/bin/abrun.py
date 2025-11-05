#!/usr/bin/env python
# (C) British Crown Copyright 2016-2021, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
SYNOPSIS

    abrun.py <app_name> [options] [arguments]

DESCRIPTION

    Creates and runs an instance of the Afterburner application specified via the
    app_name argument.

ARGUMENTS

    app_name
        Specifies the name of the Afterburner application class to instantiate
        and run. The class name should either be the full dotted class path, e.g.
        afterburner.apps.pp_to_nc.PpToNc, or the bare class name if the class
        has been imported into the namespace of the afterburner.apps package.

OPTIONS

    Any additional options or arguments are passed through as-is to the
    application object.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

import sys
import traceback

USAGE = "Usage: abrun.py <app_name> [options] [arguments]"


def main():
    """Main control function."""

    try:
        from afterburner.apps import initialise_app
        from afterburner.exceptions import AfterburnerError
    except ImportError as exc:
        print("ERROR: Unable to initialise the afterburner package owing to the "
              "following import error:\n\t{}.".format(exc), file=sys.stderr)
        sys.exit(1)

    try:
        # Initialise an instance of the specified application class.
        app_name = sys.argv[1]
        app = initialise_app(app_name, sys.argv[2:] or None)

        # Run the application.
        app.run()

        # If the application return code is non-zero then call sys.exit so that
        # it gets handed back to the calling program. For error-free application
        # completion the standard return code of 0 will be passed back.
        if app.returncode: sys.exit(app.returncode)

    except SystemExit:
        # Hand on SystemExit exceptions since in most if not all cases these
        # will have been raised by modules (e.g. argparse) that have detected
        # an error, printed an appropriate message, and called sys.exit(n)
        raise

    except:
        # Print a full traceback for all other exceptions. For Afterburner
        # exceptions, use the error_code attribute as the exit code.
        exc_type, exc_value = sys.exc_info()[:2]
        exit_code = 1
        if issubclass(exc_type, AfterburnerError):
            exit_code = getattr(exc_value, 'error_code', 1)
        traceback.print_exc()
        sys.exit(exit_code)


if __name__ == "__main__":

    # Check command-line syntax.
    if len(sys.argv) < 2:
        msg = "ERROR: Missing argument(s).\n" + USAGE
        print(msg, file=sys.stderr)
        sys.exit(1)
    elif sys.argv[1] in ('-h', '--help'):
        print(USAGE)
        sys.exit(1)

    main()
