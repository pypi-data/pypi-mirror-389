# (C) British Crown Copyright 2016, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The afterburner.contrib package acts as a container for external, contributed
code (as opposed to code developed expressly as part of the Afterburner project).
The typical use-case is to handle those Python packages or modules which are
not distributed independently and therefore cannot readily be obtained and
installed by users of Afterburner software.

Normally any contributed code should be incorporated into this package 'as-is'.
However, it may sometimes be necessary to apply minor modifications in order to
make a package usable by the main Afterburner code. Any such modifications should
be suitably commented.

If a contributed package requires significant modifications to make it usable
within Afterburner, then it should probably be incorporated into the main code
directory structure rather than within the afterburner.contrib package. It may
be necessary to obtain permission to do this from the original code owner.
"""
