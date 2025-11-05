# (C) British Crown Copyright 2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
This module provides an implementation of the DiagnosticGenerator app, which
provides the capability to generate custom diagnostics, where each such target
(a.k.a. derived) diagnostic is calculated from one or more source diagnostics
produced by a climate or weather model.
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

from afterburner.apps.derived_diag_template import DerivedDiagTemplateApp


class DiagnosticGenerator(DerivedDiagTemplateApp):
    """
    The DiagnosticGenerator class implements an Afterburner app which can be used
    to generate arbitrary custom (or derived) model diagnostics. The app may, if
    desired, be run in off-line mode, i.e. as a post-processing task. However,
    it is primarily designed to be run 'in-line', i.e. as a climate simulation
    is running.

    The DiagnosticGenerator app assumes that the climate simulation is configured
    to write out source model diagnostics on a stream-by-stream basis, i.e. sets
    of diagnostics for each data stream are saved to a single large file. The
    source diagnostics required to generate each of the target diagnostics must
    all be present in the respective stream file. The app permits the same target
    diagnostic to be generated for multiple input streams if required.

    The documentation attached to the :class:`DerivedDiagTemplateApp` class
    provides further information regarding the overall application logic and the
    expected layout of the source model data. 

    The app is designed to be configured and run under the control of a Rose suite.
    A Rose app config file (usually named ``rose-app.conf``) is used to specify
    options such as the location of the source data, the location of the output
    directory, the list of source and target diagnostics, and the names of any
    Afterburner processor classes needed to generate the target diagnostics.
    Full details of the various app config options, and the ways to invoke the
    DiagnosticGenerator app, are provided in the
    :doc:`user guide </rose_apps/diagnostic_generator/guide>`.
    """

    def __init__(self, arglist=None, **kwargs):
        super(DiagnosticGenerator, self).__init__(arglist=arglist, version='1.0.0b1',
            description='generates derived model diagnostics', **kwargs)

    def process_diagnostic(self, stream_data, diag_defn):
        return DerivedDiagTemplateApp.process_diagnostic(self, stream_data, diag_defn)
