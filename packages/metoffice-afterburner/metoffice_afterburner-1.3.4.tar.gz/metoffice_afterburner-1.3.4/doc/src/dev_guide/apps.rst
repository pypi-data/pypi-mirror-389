Writing Application Classes
===========================

As mentioned in the :doc:`overview` section, Afterburner applications - or 'apps'
for short - represent the principal user-facing elements of the Afterburner
framework. Afterburner apps should perform some logically coherent scientific data
processing activity, such as computing a custom model diagnostic, generating a
series of bespoke plots or images, or monitoring some indicator of model performance.

Naming of Application Modules and Classes
-----------------------------------------

New application classes should be implemented within a dedicated module below the
``afterburner.apps`` package. Whenever practicable, the module name should
be a lower-case translation, possibly with recognisable abbreviations, of the
application class name (which should always be in TitleCase).

For example, in the case of an application designed to create Hovmoller plots
from a user-specified model diagnostic, we might implement an app class called
``HovmollerPlotMaker`` in a module called ``hovmoller_plot_maker.py``. The full
path to the class would then be ``afterburner.apps.hovmoller_plot_maker.HovmollerPlotMaker``.

It's not mandatory to append the suffix 'App' to the class name, though doing so
serves to emphasise the purpose and provenance of the class. Often the class name
will be sufficiently long as to warrant dropping the 'App' part from the name.
Use your best judgement.

.. note:: As per standard object-oriented coding practice, class names should be
   **nouns** rather than verbs. Hence ``PlotGenerator``, not ``GeneratePlots``.

Class Design Basics
-------------------

All application classes should inherit from the :doc:`AbstractApp </apidoc/afterburner.apps>`
base class. This abstract class, which can be found in the ``afterburner.apps.__init__``
module, defines the standard interface that all concrete classes must implement.

The ``__init__()`` method of the ``AbstractApp`` base class currently performs the
following set-up tasks:

* defines a logger object which can be used by concrete subclasses to send messages
  to the user's terminal or, in the case of Rose-driven apps, to its standard log files.
* initialises an instance attribute, ``cli_args``, to hold command-line arguments and options.
* initialises an instance attribute, ``app_config``, to hold app configuration information.

Most concrete subclasses will want to execute the base class initialisation code
early on within the ``__init__()`` method. Continuing with our ``HovmollerPlotMaker``
example class from earlier, the top of this method might appears thus::

    def __init__(self, arglist=None):
        super(HovmollerPlotMaker, self).__init__()
        ...

Thereafter your app subclass can execute whatever additional initialisation
code it requires. Usually it will be desirable both to parse any command-line
arguments or options, and to read an app configuration file, if one has been
specified.

Typically these actions will be performed during app initialisation, as shown
below::

    def __init__(self, arglist=None):
        super(HovmollerPlotMaker, self).__init__()

        # Parse command-line arguments and, if one was specified, a Rose
        # configuration file.
        self._parse_args(arglist)
        self._parse_app_config()
        ...

As the name suggests, the ``_parse_args()`` method is used to parse command-line
arguments and/or options. This process is described in the next section.

The ``_parse_app_config()`` method takes an optional ``config_file`` argument,
but if that is omitted, as here, then the method scans the list of command-line
options for a ``--config-file`` option. If a file is specified then all configuration
options are read in and made accessible via the ``self.app_config`` instance attribute.

It is envisaged that many Afterburner apps will want to follow the pattern of
initialisation described above.

Handling Command-Line Arguments and Options
-------------------------------------------

Application classes should be capable of reading 'raw' command-line arguments and/or
options that have been passed in from the calling environment. In most cases
command-line arguments will be passed over from some manner of shell wrapper script
(indeed the Afterburner framework provides a general-purpose script - ``bin/abrun.sh``
- for just this purpose).

In the example code fragment shown in the previous section, the ``_parse_args()``
method (which is defined in the AbstractApp base class) takes a list of command-line
arguments, parses them, and stores the decoded argument-value pairs as attributes
on the ``self.cli_args`` instance attribute.

The arguments and options which an application supports are defined using the
``cli_spec`` property. All application classes should define this property, even
if only to set it to None or an empty list. Refer to the property's docstring
for guidance on how to specify the arguments/options that the application will
recognise.

Assuming that our HovmollerPlotMaker app supported options called ``--verbose`` and
``--format``, plus a single output filename argument, then it might be invoked thus::

    % abrun.sh HovmollerPlotMaker --verbose --format=png outfile.png

This would result in the application being invoked with the raw argument list:
``['--verbose', '--format=png', 'outfile.png']``.

After app initialisation, these command-line arguments/options would then be
available as follows (assuming ``self`` refers to the app object)::

    >>> self.cli_args.verbose
    True
    >>> self.cli_args.format
    'png'
    >>> self.cli_args.outfile
    'outfile.png'

TODO: Document standard command-line options (e.g. --verbose, --config-file)

Application Configuration
-------------------------

Afterburner apps are expected to be passed several, and possibly many, configuration
options. Since it is clearly impractical to pass large numbers of application
options and/or arguments via the command line, they need to be specified in one
or more configuration files, the number of files depending on the nature of the
application.

Adopting Rose terminology, these files are usually referred to as 'app config'
files. In order to standardise on a single convention for defining configuration
options, the format of app config files is also the same as Rose's modified INI
file format.

In effect this means that if an Afterburner app is set up to work with config files
that are laid out, and named, as per standard Rose app conventions, then the
Afterburner app is conceptually equivalent to a Rose app, even if some of the
unerlying implementation details may differ.

That said, it's not obligatory to lay out an application's configuration file(s)
in Rose-compliant fashion. It's entirely feasible, for instance, to use a single
app config file called, say, ``app_config.ini``. So long as the file contents
adhere to Rose's extended INI format, then the app should be able to work with it.

Since it is envisaged, however, that many Afterburner apps will need to be executed
from within climate model Rose suites it is expected that these apps will configurable
using familiar Rose file-naming and layout conventions.

For our artificial Hovmoller plot generation application, we might create a basic
sample Rose suite containing the following directories and files::

    suite.info
    suite.rc
    app/
        hovmoller_plot_maker/
            rose-app.conf
            meta/
                rose-meta.conf

In this example the Rose app corresponding to our Afterburner app is called
``hovmoller_plot_maker``, i.e. it's a tokenised, lower-case version of the app
class name (in much the same way as the name of the module containing the class
is derived).

With the above setup, users could potentially invoke the app in any of three
ways, assuming that the main ``rose-app.conf`` config file has been suitably
specified:

#. By running the Rose suite in stand-alone mode.
#. By incorporating the ``hovmoller_plot_maker`` app into an existing, larger
   Rose suite.
#. By instantiating and running the ``HovmollerPlotMaker`` app class, making sure
   to pass in the path to the ``rose-app.conf`` config file during initialisation.

These methods of invoking Afterburner apps are described in more detail in
:doc:`/invoking`.
