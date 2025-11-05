Introduction
============

This documentation set describes the **Afterburner** software suite, a collection
of Python-based software tools for incorporating 'on-the-fly' and post-processing
tasks into climate model suites. While the primary focus is currently on the climate
modelling domain, it is envisaged that Afterburner software will also be of utility
within NWP and related met-ocean applications.

Additional chapters in this documentation set describe how to install, configure
and run the various Afterburner software tools. These chapters can be accessed
via the table of contents displayed on this page.

**Software Components**

The Afterburner software suite consists of three main elements:

* An extensive library of Python packages and modules focussed on the building-block
  functionality needed for processing multi-dimensional earth science datasets.
  (This software library is often referred to as the *Afterburner framework* since
  it provides the low-level scaffolding code - the framework - upon which to build
  richer, more powerful end-user applications.)

* A collection of Python-based reference applications ('Afterburner apps'), based
  upon the aforementioned library, which climate scientists and modellers can use to
  perform common data processing tasks.

* A corresponding collection of sample Rose suites which demonstrate how to configure
  and run Afterburner apps using the `Rose <http://metomi.github.io/rose/doc/rose.html>`_ 
  and `cylc <http://cylc.github.io/cylc/>`_ task scheduling toolkits.

As hinted at above, Afterburner software has been designed to be integrated into,
and executed using, the Rose/cylc framework for configuring and running complex
suites of scientific software. If desired, however, Afterburner software may also
be invoked manually at the command line within a terminal window.

**Using and Contributing to the Afterburner Project**

Afterburner software is owned and maintained by the UK `Met Office <http://www.metoffice.gov.uk>`_.
It is made available under a BSD 3-Clause license and can be accessed via the dedicated
`afterburner <https://code.metoffice.gov.uk/trac/afterburner/>`_ code repository
within the Met Office's Science Repository Service facility.

At present, external contributions to the Afterburner code base are not supported.
We hope to have a mechanism in place to enable such contributions once the necessary
protocols and procedures have been drawn up. Please check the project home page
from time to time for further announcements.

**Development Roadmap**

The Afterburner software suite is continually being extended and improved. While
the existing Python library code contains many useful building blocks, it is envisaged
that many more such blocks will be designed, developed and tested during the
lifetime of the project.

Similarly, new Afterburner apps targeted at specific areas of end-user functionality
will continue to be developed, documented and supported.

It is envisaged that major releases of the Afterburner software suite will be
issued roughly every 3-4 months. Smaller maintenance and bug-fix releases will
likely be made available on a more frequent basis.

**Contact Us**

If you have any feedback or questions, feel free to contact the development team
at afterburner@metoffice.gov.uk

-- The Afterburner Project Team
