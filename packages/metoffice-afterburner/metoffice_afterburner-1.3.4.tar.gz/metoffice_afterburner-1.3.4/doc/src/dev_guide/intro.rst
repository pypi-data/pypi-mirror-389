Introduction
============

The Afterburner framework provides Python software components which can be used
to build met-ocean science applications based upon Iris, Cartopy, NumPy, SciPy,
and many other popular scientific software packages.

Development of the Afterburner software stack has been informed by, among other
objectives, two key design goals:

* To provide a high level application programming interface (API) to the lower-level
  functionality available via the Iris package (plus its close associates: Biggus
  and Cartopy).

* To provide software components that can be used to facilitate the integration of
  Afterburner-based applications with the Rose/cylc suite execution environment.

Software Organisation
---------------------

The Afterburner software framework consists of a collection of Python modules
organised into a series of packages and sub-packages. The top-level (root) package
is called, unsurprisingly, ``afterburner``. The principal sub-packages are
shown below in alphabetical order::

    afterburner/
        apps/
        contrib/
        io/
        misc/
        processors/
        stats/
        utils/

It is expected that further sub-packages will be added as the framework evolves.

Depending on the nature of your application it will usually be necessary to
access Afterburner software components using a combination of the familiar Python
import idioms illustrated below::

    >>> import afterburner
    >>> import afterburner.io.moose
    >>> from afterburner.app_config import AppConfig

Naturally your own applications will import modules and classes different, or in
addition, to those shown above.
