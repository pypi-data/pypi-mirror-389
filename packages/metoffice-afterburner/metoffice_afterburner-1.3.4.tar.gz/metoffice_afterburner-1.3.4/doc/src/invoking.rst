Running Afterburner Software
============================

As a hierarchically packaged collection of Python modules, the Afterburner software
framework  supports a number of invocation methods designed to suit the needs of
different end users and software clients.

Broadly speaking, two main invocation scenarios are envisaged:

* Running bespoke Afterburner apps that target specific climate model data
  processing tasks,

* Incorporating Afterburner code components into other Python-based software
  applications and libraries.

These scenarios are described in more detail below.


Running Afterburner Applications
--------------------------------

Bespoke Afterburner applications - or *apps* for short - are designed to be run
in either of two ways: automatically as part of Rose suites, or manually from
the command-line.

Each Afterburner app is implemented as a Python class which encapsulates the
logic of the processing task, or tasks, which the app is designed to execute.
Thus, running an Afterburner app involves creating an instance of the associated
class and invoking its ``run`` method.

Happily, since this procedure is essentially the same for all Afterburner apps,
a utility script is provided to make it easy. The script is called ``apprun.sh``
and it can be found in the ``bin`` subdirectory below the location where the
Afterburner software is installed at your site.

.. note:: The ``apprun.sh`` is designed to work with Python 3 by default. It supercedes
   the earlier ``abrun.sh`` script, which was designed to work with Python 2.7

So, assuming you have defined the AFTERBURNER_HOME_DIR environment variable to point
to the *root* directory of the Afterburner software suite, then the full path to
the aforementioned launch script is ``$AFTERBURNER_HOME_DIR/bin/apprun.sh``.

Armed with this background information, let's look first at how to run Afterburner
apps manually. This will then give us a good idea as to how apps can be invoked
automatically by Rose suites.

.. hint:: If you're not sure where the Afterburner software is installed at your
   site, please check with your local site administrator.

Command-line Invocation
~~~~~~~~~~~~~~~~~~~~~~~

Firstly, being able to running Afterburner apps manually within a terminal window
environment is a useful feature. As well as allowing you to do quick tests to
check that an app works as expected (or not!), it also means that you can access
Afterburner functionality outside of the Rose environment, should that be an
unwanted overhead in the context of your preferred workflow.

As mentioned above, you'll typically need to define the AFTERBURNER_HOME_DIR
environment variable before you can run Afterburner apps. Here's how::

    % export AFTERBURNER_HOME_DIR=<path-to-afterburner-software-directory>

If you do this on a regular basis then you'll probably want to define it once in the
appropriate shell start-up file (e.g. ``~/.bashrc`` in the case of the Bash shell).
Otherwise you can define the variable on an as-needs basis.

If your computing environment supports the Met Office's Scientific Software Stack
(SciTools, for short) as a loadable module, then you can request a specific module
be loaded by assigning its name to the SCITOOLS_MODULE environment variable, e.g.::

    % export SCITOOLS_MODULE=scitools/experiment-current

If left undefined then an attempt is made to load the default **Python3-compatible** version of
SciTools. If you prefer to use the particular SciTools module loaded into the current
runtime environment then you should set SCITOOLS_MODULE=none.

With that done, you should now be able to run a particular Afterburner app using
the ``apprun.sh`` script. The basic command syntax is as follows::

    % $AFTERBURNER_HOME_DIR/bin/apprun.sh <app-class> -c <config-file> [options] [args]

Here, ``<app-class>`` refers to the name of the Python class that implements the app.
The class name should be a dotted class path of the form ``afterburner.apps.my_app.MyApp``.
The class path to use for a particular app is displayed near the top of the
documentation page for that app.

As a convenience, in some cases it may be possible to specify just the final
class name, e.g. ``MyApp``, rather than the full class path. The app documentation
will state if that's the case.

The ``-c <config-file>`` part of the above command specifies the location of the
ini-style file that is used to configure the application (assuming one is needed
at all: if not then this part can be omitted). As before, the app documentation
page will describe the format and contents of any required configuration file, or
files. Most apps require at least one configuration file.

Finally, the ``[options]`` and ``[args]`` parts of the run command may be used
to specify additional options and/or arguments to be passed to the app. Once again,
the app documentation page provides the details (also, most apps recognise the
``--help`` option, which displays basic command-line usage information).

By way of an artificial example, the following command might be used to invoke a
jet speed calculator app with a config file named js_app.conf, and with verbose
logging mode enabled::

    % apprun.sh afterburner.apps.jet_speed.JetSpeedCalculator -c js_app.conf --verbose

This last command assumes that the ``$AFTERBURNER_HOME_DIR/bin`` directory has
been added to your command search path (i.e. via the PATH environment variable).
If you frequently run Afterburner apps then you might want to modify the PATH
setting in your shell start-up script to do this. But this is not obligatory:
you can always use the longer, explicit command form.

Integration into Rose suites
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each Afterburner app (at least those developed by the core project team) is
associated with a reference Rose suite which contains a sample Rose app configuration
directory that users can copy, either to run the app in stand-alone mode or
integrate into their existing suites.

The location of the reference suite is linked from the main documentation page
for each Afterburner app (see :doc:`rose_apps/index`). Most of the reference
Rose suites are expected to reside within the `roses-u <https://code.metoffice.gov.uk/trac/roses-u>`_
repository of the Met Office Science Repository Service.

A typical Rose suite will contain a Rose application configuration directory
whose name mirrors the name of the Afterburner app's associated Python class.
Thus, taking the earlier example of the jet speed calculator application, the
Rose app directory is likely to be named something like ``jet_speed_calculator``.

Within the Rose app directory there should be a ``rose-app.conf`` file which
provides default or sample settings for the associated Afterburner app.

The ``[command]`` section will normally look something like this::

    [command]
    default=$AFTERBURNER_HOME_DIR/bin/apprun.sh afterburner.apps.my_app.MyApp -c $ROSE_SUITE_DIR/app/my_app/rose-app.conf

Having read the previous section regarding manual invocation of Afterburner apps,
the purpose of this command should now be fairly clear. The command syntax may of
course be modified to reflect the particular application behaviour you desire.
The app's documentation page should describe which options and/or arguments are
supported.

If the AFTERBURNER_HOME_DIR variable is not defined within your default login
environment, then you'll probably need to specify it under the ``[env]`` section
of the configuration file. For example::

    [env]
    AFTERBURNER_HOME_DIR=/path/to/afterburner/home/dir

Most Afterburner app config files include this section, though you might need to
verify that the path is correct for your site. If you're wanting to use a non-
standard release of the Afterburner software - a new beta release, for example -
then you'll need to specify the path to the release directory using the above mechanism.

.. note:: If you are planning to run an Afterburner app on the SPICE platform
   then you should check that the Afterburner software location is visible to
   processes running on that platform (and likewise for data locations, of course).

The advice in the previous section regarding the use of the SCITOOLS_MODULE
environment variable applies here too. Depending on your needs, you may wish to
specify this variable in the ``[env]`` section of your app config file.

Depending on the intended use of the app, you can either run it in stand-alone
mode, i.e. as the sole app (i.e. cylc task) within a Rose suite, or as one component
of a larger, potentially more complex, climate suite. And whether the app is executed
once, or multiple times at selected time points, will likewise depend upon the
design and functionality of the app.

Most Afterburner apps support a ``--verbose`` option (``-v`` for short). If enabled,
this option results in additional messages being emitted to Rose's log files (or
the terminal window when executing the app manually). This can be useful for
progress tracking or debugging purposes.


Using the Afterburner Python Package
------------------------------------

As mentioned earlier, the Afterburner software suite is primarily a collection of
standard Python packages and modules. As such it can be called from within your
own Python software, or else invoked directly from an interactive Python session,
just like any other package.

The top-level Python package is called, unsurprisingly, ``afterburner``. It acts
as the entry point to the full range of Afterburner sub-packages and modules.
Accordingly, it will usually be necessary to issue import statements along the
following lines::

    >>> import afterburner
    >>> import afterburner.io.moose
    >>> from afterburner.config import AppConfig

The Afterburner :doc:`apiref` provides comprehensive documentation for the various
sub-packages and modules. A familiarity with the main functional areas of the
afterburner package will likely prove beneficial.

Unless the Afterburner software has been installed into one of Python's standard
locations, then you will need to specify its location.

The simplest, though not necessarily best, way to do this is to append the pathname
of the directory containing the ``afterburner`` Python package to the PYTHONPATH
environment variable, either on a per-session basis or else in the appropriate
shell start-up file.

The pathname of the directory containing the ``afterburner`` package can be
obtained using the following utility command::

    %  $AFTERBURNER_HOME_DIR/bin/abconfig --python

For standard installations the displayed path should look something like
``$AFTERBURNER_HOME_DIR/lib/python`` (with the AFTERBURNER_HOME_DIR part
expanded to its actual value).

If you're having trouble accessing the ``afterburner`` package then our advice
is to contact your site administrator, or a nearby Python guru!

.. note:: Although Afterburner software is now compliant with both Python 2.7
   and Python 3.x, at the time of writing (Feb 2020) this is not the case for
   a small number of its prerequisite packages. Depending therefore on the Python
   setup at your site, you may need to run Afterburner against Python 2.7.

Utility Scripts
---------------

The utilities described below can be found in the ``$AFTERBURNER_HOME_DIR/bin``
directory.

.. _apprun.sh:

apprun.sh shell script
~~~~~~~~~~~~~~~~~~~~~~

.. program:: apprun.sh

SYNOPSIS

.. code-block:: console

   apprun.sh [-h | --help]
   apprun.sh <app_name> [app-options] [app-arguments]
   apprun.sh [script-options] -- <app_name> [app-options] [app-arguments]

DESCRIPTION

   The ``apprun.sh`` script is a thin shell wrapper around the ``abrun.py`` Python script.
   Its main purpose is to provide a simple and uniform mechanism for invoking an
   Afterburner processing application (a.k.a. Afterburner app), either from the
   command-line or from within a Rose suite or cron job.

   This script is a replacement for the ``abrun.sh`` script. It is designed to invoke
   an Afterburner app within a **Python3-based** SciTools environment. In theory the
   script could be invoked in such a way as to execute within a Python2.7-based
   environment; this, however, is discouraged.

   By default the app is invoked within the 'scitools/default' environment.
   This can be changed using either the SCITOOLS_MODULE environment variable
   or the ``--sci-module`` command-line option. The latter takes precedence.

   The directory location of the Afterburner software suite is obtained either
   directly from the AFTERBURNER_HOME_DIR environment variable, or else it is
   derived from the directory path of the current script. If the ``--ab-module``
   command-line option is used to specify the name of an Afterburner module to
   load then the AFTERBURNER_HOME_DIR environment variable automatically gets
   set to the correct location.

ARGUMENTS

.. option:: app_name

   Specifies the name of the Python class in the Afterburner software suite
   which implements the application. The class name should either be the
   full dotted class path, e.g. ``afterburner.apps.pp_to_nc.PpToNc``, or the
   bare class name if the class has been imported into the namespace of the
   ``afterburner.apps`` package.

SCRIPT OPTIONS

.. note:: If any of the options and switches described below are included in the
   command invocation then, as per the SYNOPSIS, the ``--`` token must be used to
   signal the end of script options/switches, and the start of the Afterburner
   app name and its options (if any are required).

.. option:: --ab-module=<afterburner-module>

   The name of the Afterburner module to load prior to running any Python
   commands. This option overrides the AFTERBURNER_MODULE environment variable
   if that is defined (see the ENVIRONMENT VARIABLES section below).

.. option:: --debug

   Turn on diagnostic messages. Useful for troubleshooting runtime issues,
   typically in combination with the ``--dry-run`` switch.

.. option:: -n, --dry-run

   Execute in dry-run mode. This just prints out any diagnostic messages (if
   ``--debug`` is enabled) and prints the final command that would get executed
   in order to invoke the specified Afterburner app (which, in this particular
   instance, could be entirely fabricated since it won't get run).

.. option:: --py=<python-version>

   This option may be used to specify a particular version of Python within
   which to invoke the requested Afterburner application. You can specify
   just the major version, e.g. ``--py=3``, or the major and minor version, e.g.
   ``--py=3.6``. Note that this command-line option overrides the PYTHON_EXEC
   variable, if that is defined. If the requested Python version cannot be
   found in the runtime environment then the plain 'python' command is used.

.. option:: --reset-pypath

   If this switch is included in the command invocation then the PYTHONPATH
   environment variable is reset (to the empty string) before being built
   up with the required locations of, e.g., the Rose and Afterburner Python
   packages.

.. option:: --sci-module=<sci-module>

   The name of the SciTools module to load prior to running any Python
   commands. This option overrides the SCITOOLS_MODULE environment variable
   if that is defined (see the ENVIRONMENT VARIABLES section below).

   Any additional options or arguments are passed through as-is to the specified
   Afterburner application.

ENVIRONMENT VARIABLES

.. envvar:: AFTERBURNER_HOME_DIR

   This environment variable may be used to specify the home directory of
   the Afterburner software suite. If unspecified then the default directory
   path is determined from the location of the current script. Depending on
   how this script is invoked, however, this method cannot always be relied
   upon to yield the correct path. Consequently it is recommended that, in
   normal use, the AFTERBURNER_HOME_DIR variable should be defined explicitly
   (e.g. within an appropriate shell start-up script).

.. envvar:: AFTERBURNER_MODULE

   The name of the Afterburner module to load prior to running any Python
   commands. If this variable is undefined or set to 'none' then no attempt
   is made to load an Afterburner module. In that case the location of the
   Afterburner python package is determined by the ``abconfig`` script (which
   can be found alongside the current script). The returned location is then
   prepended to the PYTHONPATH variable.

.. envvar:: PYTHON_EXEC

   This environment variable may be used to specify the name (or full path)
   of the Python command used to run the Afterburner software. For example,
   one might set this to 'python3.6' if that is the version of Python 3 you
   with to use. See also the ``--py`` command-line option.

.. envvar:: SCITOOLS_MODULE

   The name of the SciTools module to load prior to running any Python
   commands. If undefined then the default module that will be loaded is
   'scitools/default'. Alternatively, this variable can be set to 'none' to
   skip explicit loading of a SciTools module, in which case the default
   version of Python provided by the user's runtime environment will be used.

.. _abrun.sh:

abrun.sh shell script
~~~~~~~~~~~~~~~~~~~~~

.. program:: abrun.sh

SYNOPSIS

.. code-block:: console

   abrun.sh [-h | --help]
   abrun.sh <app_name> [options] [arguments]

DESCRIPTION

   The ``abrun.sh`` script is a thin shell wrapper around the ``abrun.py`` Python script.
   Its main purpose is to provide a simple and uniform mechanism for invoking an
   Afterburner processing application (a.k.a. Afterburner app), either from the
   command-line or from within a Rose suite or cron job.

ARGUMENTS

.. option:: app_name

   Specifies the name of the Python class in the Afterburner software suite
   which implements the application. The class name should either be the
   full dotted class path, e.g. ``afterburner.apps.pp_to_nc.PpToNc``, or the
   bare class name if the class has been imported into the namespace of the
   ``afterburner.apps`` package.

OPTIONS

.. option:: --pyM[.N]

   This option may be used to specify a particular version of Python within
   which to invoke the requested Afterburner application. You can specify
   just the major version, e.g. ``--py3``, or the major and minor version, e.g.
   ``--py3.6``. Note that this command-line option overrides the PYTHON_EXEC
   variable (see below) if that is defined. If the requested Python version cannot
   be found in the runtime environment then the plain 'python' command is used.

Any additional options or arguments are passed through as-is to the specified
processing application.

ENVIRONMENT VARIABLES

   **AFTERBURNER_HOME_DIR**

   This environment variable may be used to specify the home directory of
   the Afterburner software suite. If unspecified then the default directory
   path is determined from the location of the current script. Depending on
   how this script is invoked, however, this method cannot always be relied
   upon to yield the correct path. Consequently it is recommended that, in
   normal use, the AFTERBURNER_HOME_DIR variable should be defined explicitly
   (typically within an appropriate shell start-up script).

   **AFTERBURNER_MODULE**

   The name of the Afterburner module to load prior to running any Python
   commands. If this variable is undefined or set to 'none' then no attempt
   is made to load an Afterburner module. In that case the location of the
   Afterburner python package is determined by the ``abconfig`` script (which
   can be found alongside the current script). The returned location is then
   prepended to the PYTHONPATH variable.

   **PYTHON_EXEC**

   This environment variable may be used to specify the name (or full path)
   of the Python command used to run the Afterburner software. For example,
   one might set this to 'python3.6' if that is the version of Python 3 on
   your operating system.

   **SCITOOLS_MODULE**

   The name of the SciTools module to load prior to running any Python
   commands. If undefined then the default module that will be loaded is
   'scitools/production_legacy-os43-2'. Alternatively, this variable can be set to
   'none' to skip explicit loading of a SciTools module, in which case the
   default version of Python provided by the user's runtime environment will
   be used.

   NOTE: Use of the SCITOOLS_MODULE variable to load a specific SciTools module
   is preferred over the old SCITOOLS_PATH method, which is now deprecated.

   **SCITOOLS_PATH**

   This environment variable may be used to specify a colon-delimited list
   of SciTools directory paths to prepend to the PYTHONPATH variable prior
   to invoking the requested Afterburner app. Directories already present
   in PYTHONPATH are silently ignored.

   NOTE: Use of the SCITOOLS_PATH variable is deprecated in favour of the
   SCITOOLS_MODULE variable, as described above. Setting both variables is
   likely to lead to conflicts and is therefore strongly discouraged.

.. _abconfig:

abconfig python script
~~~~~~~~~~~~~~~~~~~~~~

.. program:: abconfig

SYNOPSIS

.. code-block:: console

   abconfig [-h | --help]
   abconfig [options]

DESCRIPTION

   Script for querying the location of various Afterburner software artifacts.
   Assumes that the software is laid out in the familiar distutils/setuptools
   pattern of top-level directories: bin, etc, lib, and so on.

   The script is designed to process a single option. This is to facilitate its
   use in setting shell variables, e.g.

   .. code-block:: console

      % export PYTHONPATH=$PYTHONPATH:$(abconfig --pythonpath)

   If multiple options are specified then the behaviour is currently undefined.

ARGUMENTS

    None

OPTIONS

.. option:: -h, --help

   Show the command-line usage for this script.

.. option:: --bin

   Display the pathname of the Afterburner software suite's ``bin`` directory.

.. option:: --env

   Print all configuration properties in a format suitable for setting as
   environment variables, i.e. one VARNAME=value pair per line. The output
   may then be eval'd by the calling shell.

.. option:: --etc

   Display the pathname of the Afterburner software suite's ``etc`` directory.

.. option:: --home

   Display the pathname of the Afterburner software suite's home directory.

.. option:: --pythonpath

   Display the pathname of the Afterburner python package directory.
   Useful for setting the PYTHONPATH environment variable.

.. option:: --site-config

   Display the pathname of the Afterburner site configuration file.

.. option:: --user-config

   Display the pathname of the Afterburner user configuration file.

.. option:: --version

   Display the version number of the current Afterburner software suite.
