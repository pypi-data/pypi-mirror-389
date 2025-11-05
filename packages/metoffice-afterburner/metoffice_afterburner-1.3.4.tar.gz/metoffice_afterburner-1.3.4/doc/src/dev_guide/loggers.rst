Message Handling
================

The Afterburner framework uses Python's standard `logging <https://docs.python.org/2/library/logging.html>`_
module to emit log messages.

Afterburner defines three logger objects by default. The names of these loggers,
and their relative position in the logger hierarchy, are as follows::

 root
 |
 + afterburner
   |
   + afterburner.apps
   |
   + afterburner.processors

These loggers are merely created for the convenience of developers of Afterburner
applications. Although it's not obligatory to use them, in most scenarios they
provide a relatively straightforward and flexible way of handling message output.

Developers are free, however, to augment the default logger objects described
below with their own custom loggers if the situation demands it.

The 'afterburner' Logger
------------------------

The 'afterburner' logger is created when the ``afterburner`` package is imported
(which might be implicitly if an Afterburner subpackage/submodule is imported). 
The default log level for this logger is WARNING. At present the log level can be
modified in either - or potentially both - of the following ways:

* by setting the AFTERBURNER_LOG_LEVEL environment variable prior to importing
  the ``afterburner`` package (or any of its subpackages)
* by setting the log level explicitly in client code as and when required

By default, messages at and above ERROR level are sent to the standard error stream.
Messages below ERROR level are sent to standard output. To avoid possible duplication
of messages, the 'afterburner' logger does not propagate messages up to the 'root'
logger.

If required, a handle to the 'afterburner' logger can be obtained as follows::

    >>> import logging
    >>> logger = logging.getLogger('afterburner')

However, most of the modules in the Afterburner library utilise the following
common idiom:

    >>> logger = logging.getLogger(__name__)

Since the resultant logger object, by default, has no handlers defined, any
messages will be passed up to the 'afterburner' logger.

The 'afterburner.apps' Logger
-----------------------------

The 'afterburner.apps' logger gets created in the :class:`afterburner.apps.AbstractApp`
base class and thus is automatically available - via the ``self.logger`` attribute -
to any application objects that are derived from that class.

This logger uses the default log level of NOTSET, and has its propagate attribute
set to true. This means that, in the absence of explicit changes, the logger
passes message up to the 'afterburner' logger object, where they get handled in
the same way as for core library code.

Afterburner applications will often want to set the messaging level according
to a user-specified command-line option, such as ``-q/--quiet``,  ``-v/--verbose``
or ``-D/--debug``. These particular options are automatically supported by all
Afterburner applications.

The :meth:`afterburner.apps.AbstractApp._set_message_level` method can be used
to detect one of the aforementioned options and set the 'afterburner.apps'
log level accordingly. This is often done in the app's ``__init__`` method, e.g.::

    def __init__(self, arglist=None):
        super(MyApp, self).__init__()
        self._parse_args(arglist, ...)
        self._set_message_level()   # detects options like -q, -v, etc.

It should be noted that setting the level of the 'afterburner.apps' logger 
(e.g. to 'INFO') does **not** alter the level of the 'afterburner' logger. This
is usually the desired behaviour: info messages would then be emitted by the
application but not the core Afterburner library.

The 'afterburner.processors' Logger
-----------------------------------

In a similar manner to the 'afterburner.apps' logger, the 'afterburner.processors'
logger gets created in the :class:`afterburner.processors.AbstractProcessor` base
class and thus is automatically available - via the ``self.logger`` attribute -
to any processor objects that are derived from that class.

This logger also uses the default values for log level (NOTSET) and propagation
(true). This means that, in the absence of explicit property updates, the logger
passes message upwards to the 'afterburner' logger where they will be handled in
the same way as for core library code.

As before, setting the level of the 'afterburner.processors' logger does not alter
the level of the 'afterburner' logger. This means that fine-grained control over
message-handling can be achieved, if required, for individual processor objects.

Hints and Tips
--------------

* If you wish to handle all message output in the same way, just set the desired
  log level (and any other properties, such as log format) on the top-level
  'afterburner' logger object. This is the simplest approach.

* If you are writing an Afterburner app, and you want to control message output
  for that app, then you should work with the 'afterburner.apps' logger object
  accessed via ``self.logger``. This will enable you to set, say, info-level or
  debug-level message output for the app whilst avoiding reams of messages from
  the core Afterburner library modules. For example::

    >>> # set log level at app initialisation time
    >>> app = MyApp(log_level='debug')
    >>> ...
    >>> # set log level manually later on
    >>> app.logger.setLevel(logging.INFO)

* Likewise, in the case of processor objects you can set the log level at
  initialisation time, or at any time thereafter. In particular, if you are
  developing an app that creates one or more processor objects, and you want
  the latter to use the same log level as the app, then you can pass the log
  level setting at processor initialisation time. For example::

    >>> # initialise app with verbose command-line option
    >>> app = MyApp(['--verbose'])
    >>> ...
    >>> # initialise processor with same log level as app
    >>> proc = MyProcessor(log_level=app.logger.level)
  