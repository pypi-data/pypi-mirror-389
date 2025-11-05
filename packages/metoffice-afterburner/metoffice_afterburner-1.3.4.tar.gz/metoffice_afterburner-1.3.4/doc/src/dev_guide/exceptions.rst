Exception Handling
==================

Custom exception classes may be defined within the :doc:`/apidoc/afterburner.exceptions`.
All such classes should inherit from the ``AfterburnerError`` base class and
should have a name ending in 'Error'.

As a rule, new exception class should *only* be created for those situations where
one of Python's standard exceptions is not applicable. Standard exceptions such
as ValueError, TypeError, KeyError and IndexError (to name just a few) can be used
to cover a surprisingly wide variety of common application exceptions.

In particular, it is rarely necessary to write exception classes to handle invalid
values for particular application objects/attributes. Just use ValueError with
a suitable message string.

In certain cases it can make sense to create a shallow hierarchy of exception
classes. This allows client code to catch a single generic exception, rather than
multiple specific exceptions, if the occasion calls. The various ``Moose*Error``
exception classes follow this pattern, for example.

The majority of existing Afterburner exception classes make do with the standard
``message`` attribute (as inherited from Python's
`Exception <https://docs.python.org/2/library/exceptions.html#exceptions.Exception>`_
base class). If your class needs to store additional attributes, that's fine,
but be sure to document them.

When it comes to raising exceptions, invariably it's useful - if not essential -
to pass a suitably instructive message string to the constructor. This should make
it quicker and easier to chase down user-reported error messages.

Afterburner exception classes are assigned a unique error code, the ranges of
which are defined in the :doc:`/apidoc/afterburner.exceptions` docstring.
Be sure to pick an unused code when defining a new exception class. This can
follow the existing sequence of codes used in related exceptions. If, however,
it seems likely that extra classes will need to be slotted into the sequence later
on, then it may be prudent to pick an error code that leaves a small gap in the
sequence (again, the ``Moose*Error`` exception classes provide an example of this).

.. note:: The error code mechanism has, as yet, proven to be of little value. But
   it's been started so let's run with it for the time being!
