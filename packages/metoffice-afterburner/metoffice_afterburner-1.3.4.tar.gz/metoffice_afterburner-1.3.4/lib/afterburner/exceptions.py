# (C) British Crown Copyright 2016-2017, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
Definitions of custom exception classes - and related error-handling objects -
required by the afterburner package.

For each class, the ``error_code`` attribute should be assigned a unique positive
integer. Conceptually-related exception classes should be assigned codes from
the appropriate range. The following error code ranges are currently defined.
Additional ranges should be specified as the need arises. The maximum permissible
code number is 9999.
::

    General purpose exceptions:            10-99
    Directory/file related exceptions:     100-149
    Data format related exceptions:        150-199
    Climate model related exceptions:      200-249

**Index of Exception Classes**

.. autosummary::
   :nosignatures:

   AfterburnerError
   ConfigurationError
   AppConfigError
   AppRuntimeError
   DataProcessingError
   DataCacheError
   DataStoreError
   MooseCommandError
   MooseUnavailableError
   MooseLimitExceededError
   MooseUnsupportedError
   ClassNotFoundError
   CoordinateError
   TempFileError
   MissingDataFilesError
   UnknownModelNameError
   InvalidDiagnosticFormulaError
"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)

UNDEFINED_ERROR_CODE = -1


class AfterburnerError(Exception):
    """
    Base class for the Afterburner exception class hierarchy. All user-defined
    exception classes should inherit from this class.
    """
    error_code = UNDEFINED_ERROR_CODE

    def __init__(self, message=''):
        """
        :param str message: The error message text.
        """
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        """
        Return a string representation of the exception in the format:
            ERROR CODE nnnn: error message
        """
        return "ERROR CODE {0:04d}: {1}".format(self.error_code, self.message or
            'unspecified')


# GENERAL PURPOSE EXCEPTIONS

class ConfigurationError(AfterburnerError):
    """
    For use when an error is reported in connection with the run-time setup or
    configuration of the Afterburner software (e.g. missing python modules)

    The :class:`AppConfigError` exception class should be used for handling
    configuration errors associated with specific Afterburner applications.
    """
    error_code = 10


class AppConfigError(AfterburnerError):
    """
    For use when an error is detected in the configuration of an Afterburner
    application. Typically this will relate to an error in a command-line
    option or Rose configuration file setting.
    """
    error_code = 11


class AppRuntimeError(AfterburnerError):
    """
    For use when an error is encountered while running an Afterburner
    application.
    """
    error_code = 12


class DataProcessingError(AfterburnerError):
    """
    For use when a data processing error occurs. Typically this will relate to
    an error detected within one of Afterburner's data processor classes.
    """
    error_code = 13


class DataCacheError(AfterburnerError):
    """
    For use when an error is encountered during a data cache setup or access
    operation.
    """
    error_code = 14


class DataStoreError(AfterburnerError):
    """
    For use when an error is encountered during a data store access operation,
    e.g. attempting to querying or retrieve data from MASS. Note that the more
    specific MOOSE-related exceptions below inherit from this class.
    """
    error_code = 15


class MooseCommandError(DataStoreError):
    """
    For use when a MOOSE command does not complete successfully because there
    was an error in the MOOSE command sent, e.g. the data requested may not
    exist.
    """
    error_code = 20


class MooseUnavailableError(DataStoreError):
    """
    For use when a MOOSE command does not complete successfully because the
    MOOSE or MASS systems are currently unavailable.
    """
    error_code = 21


class MooseLimitExceededError(DataStoreError):
    """
    For use when a MOOSE command exceeds one of its built-in limits (as defined
    by the 'moo si -v' command).
    """
    error_code = 22


class MooseUnsupportedError(DataStoreError):
    """
    For use when the MOOSE command-line interface is not supported by the
    current runtime environment.
    """
    error_code = 23


class ClassNotFoundError(AfterburnerError):
    """
    For use when a requested class, identified by name or path, could not be
    found.
    """
    error_code = 30


class CoordinateError(AfterburnerError):
    """
    For use with errors relating to coordinate definitions.
    """
    error_code = 35


# DIRECTORY/FILE RELATED EXCEPTIONS

class TempFileError(AfterburnerError):
    """
    For use when there is a problem creating, writing to, or deleting a
    temporary file.
    """
    error_code = 100


class MissingDataFilesError(AfterburnerError):
    """
    For use when one or more data files required for an operation are missing.
    """
    error_code = 101


# DATA FORMAT RELATED EXCEPTIONS


# MODEL RELATED EXCEPTIONS

class UnknownModelNameError(AfterburnerError):
    """
    For use when an unknown model name is encountered.
    """
    error_code = 200


class InvalidDiagnosticFormulaError(AfterburnerError):
    """
    For use when an invalid diagnostic formula (a.k.a. expression) is specified.
    """
    error_code = 201

    def __init__(self, message='', formula=''):
        AfterburnerError.__init__(self, message)
        self.formula = formula
