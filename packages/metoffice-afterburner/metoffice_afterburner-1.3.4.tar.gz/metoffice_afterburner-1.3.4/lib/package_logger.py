# (C) British Crown Copyright 2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
The ``package_logger`` module contains utility classes and functions for logging
package (or module) usage messages to a TCP server using Python's `socket network
interface <https://docs.python.org/3/library/socket.html>`_.
"""
from __future__ import (absolute_import, print_function)

import argparse
import datetime
import getpass
import hashlib
import importlib
import logging
import logging.handlers
import os
import socket
import sys
import time

# Default TCP port.
DEFAULT_PORT = logging.handlers.DEFAULT_TCP_LOGGING_PORT


class UncontactableServerError(OSError):
    """Exception indicating that a server host could not be contacted."""
    pass


class PackageUsageLogger(logging.LoggerAdapter):
    """
    Class for adapting a logger object such that log messages gets augmented
    with, by default, the following runtime information:

    * UTC timestamp
    * username and hostname
    * package name and version
    * Python version
    * scitools version (if loaded)

    The primary purpose of the class is to log invocations (i.e. imports) of a
    specified Python package or module. The package whose usage is to be logged
    must be named at object initialisation time using the ``extra['pkg_name']``
    dictionary item, as shown below for a toy package named 'frobnitz':

    >>> some_logger = logging.getLogger('frobnitz')
    >>> new_logger = PackageUsageLogger(some_logger, extra={'pkg_name': 'frobnitz'})
    >>> new_logger.info('Invoked the frobnitz package')

    The adapted logger is mainly intended to be used for logging INFO messages,
    as exemplified above, although messages at a higher level will also be handled.
    The message text is actually optional; if not supplied then only the runtime
    information will be logged.

    At present an augmented log message looks something like this:

    ``[frobnitz] utc=2019-11-14T12:19:34, user=mary@somehost, pkg=frobnitz-1.2.3, py=3.6.8, sci=default/2019_02_27 | invoked frobnitz package``

    The specific item values will naturally reflect those pertaining in the user's
    environment at runtime.
    """

    _DEFAULT_FMT = ("[{name}] utc={utc}, user={user}@{host}, "
           "pkg={pkg_name}-{pkg_vn}, py={py_vn}, sci={sci_vn} | {msg}")

    def __init__(self, logger, extra):

        if 'pkg_name' not in extra:
            raise KeyError("The 'extra' dictionary must contain a 'pkg_name' key.")
        super(PackageUsageLogger, self).__init__(logger, extra)

        if not hasattr(self, 'name'): self.name = logger.name
        self.pkg_name = extra['pkg_name']
        self.fmt = extra.get('fmt', self._DEFAULT_FMT)

    def process(self, msg, kwargs):
        """
        Process a raw logger message, adding the runtime information as described
        in the class docstring above.
        """

        dt = datetime.datetime.utcnow().replace(microsecond=0)
        timestamp = dt.isoformat()
        user = getpass.getuser()
        host = socket.gethostname()
        pkg_vn = _get_package_version(self.pkg_name) or '?.?.?'
        py_vn = '{v.major}.{v.minor}.{v.micro}'.format(v=sys.version_info)
        sci_vn = _get_scitools_version() or 'n/a'

        new_msg = self.fmt.format(name=self.name, utc=timestamp,
            user=user, host=host, pkg_name=self.pkg_name, pkg_vn=pkg_vn,
            py_vn=py_vn, sci_vn=sci_vn,
            msg=msg or 'no message')

        return new_msg, kwargs


def create_package_logger(log_name, pkg_name, host='localhost', port=None,
        level=None):
    """
    Create a :class:`PackageUsageLogger` object which can be used to log usage of
    the specified package using a socket-based TCP server process.

    :param str log_name: The name to give to the created logger object.
    :param str pkg_name: The name of the package or module whose usage is to be logged.
    :param str host: The hostname of the TCP server listening for log requests.
    :param str port: The port on which the TCP server is listening.
    :param int level: The level to use for the logger (default: logging.INFO).
    :returns: A logger object configured with a ``logging.handlers.SocketHandler``
        object as its sole message handler.
    :raises UncontactableServerError: Raised if a server/service could not be
        detected on the specified host and port.
    """

    if port is None:
        port = DEFAULT_PORT
    if level is None:
        level = logging.INFO

    if not _is_socket_open(host, port):
        raise UncontactableServerError("No server detected at address {0}:{1}".format(
            host, port))

    sock_handler = logging.handlers.SocketHandler(host, port)

    pkg_logger = logging.getLogger(log_name)
    pkg_logger.setLevel(level)
    pkg_logger.addHandler(sock_handler)

    return PackageUsageLogger(pkg_logger, extra={'pkg_name': pkg_name})


def _parse_args():
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        usage="%(prog)s [options]",
        description="Send test messages to a socket-based TCP server listening "
            "for logging requests")

    parser.add_argument("--pkg-name", default='afterburner',
        help="package name (default: afterburner)")
    parser.add_argument("--log-name",
        help="logger name (default: pkg-name+'_logger')")
    parser.add_argument("--host",
        help="hostname on which the TCP server is running (default: localhost)")
    parser.add_argument("--port", type=int,
        help="port configured to listen for logging requests (default: 9020)")
    parser.add_argument("--pingtest", default=False, action='store_true',
        help="include test for a TCP server running on host:port")

    return parser.parse_args()


def _is_socket_open(host, port, retries=3, delay=1, timeout=1, verbose=False):
    """
    Test to see if a TCP stream-type socket is listening on host:port.

    :param str host: The name of the host to scan.
    :param str port: The port number to scan.
    :param int retries: Number of socket connection attempts.
    :param int delay: Time, in seconds, to wait between connection attempts.
    :param int timeout: Timeout, in seconds, for any given socket operation.
    :returns: True if a TCP server process is listening on host:port.
    """

    def _socket_test():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            sock.shutdown(socket.SHUT_RDWR)
            isopen = True
        except:
            isopen = False
        finally:
            sock.close()
        return isopen

    is_open = False
    for i in range(retries):
        if verbose:
            print("socket test #{}".format(i+1))
        if _socket_test():
            is_open = True
            break
        else:
            time.sleep(delay)

    return is_open


def _get_hash_key():
    """
    Get a unique hash key for this package invocation based upon time, process
    ID and hostname. Adapted from the similar technique used by the AVD Team for
    logging Python invocations.

    :returns: A hash key generated from current UTC time, process ID and hpostname.
    """

    dt = datetime.datetime.utcnow().replace(microsecond=0)
    salt_dt = dt.isoformat()
    salt_pid = os.getpid()
    salt_host = socket.gethostname()
    salt = '{0}{1}{2}'.format(salt_dt, salt_pid, salt_host)
    return hashlib.sha256(salt.encode('utf-8')).hexdigest()[:16]


def _get_package_version(pkg_name):
    """
    Obtain the version number of a named package or module by querying its
    '__version__' attribute. Returns an empty string if either the package/module
    could not be imported or the version attribute is not defined in the module.

    :param str pkg_name: The name of the package/module to query.
    :returns: The version number (string) for the requested package.
    """

    try:
        mod = importlib.import_module(pkg_name)
        vn = getattr(mod, '__version__', '')
    except ImportError:
        vn = ''
    return vn


def _get_scitools_version():
    """
    Obtain the name of the currently loaded scitools module, if any. The
    approach used here is to query the value of the SSS_TAG_DIR environment
    variable. An alternative approach would be to parse the output from the
    module -t list command. These are site-specific solutions.

    :returns: The scitools version, if available, else an empty string.
    """

    sss_tag_dir = os.environ.get('SSS_TAG_DIR', '')
    if sss_tag_dir:
        leaf_dirs = sss_tag_dir.split('/')[-2:]
        return os.path.join(*leaf_dirs)
    else:
        return ''


def _send_test_messages(logger):
    """Emit some test messages to the specified logger."""

    logger.debug('debug msg')
    logger.info('info msg')
    logger.warning('warning msg')
    logger.error('error msg')


if __name__ == '__main__':
    args = _parse_args()
    host = args.host or 'localhost'
    port = args.port or DEFAULT_PORT

    # Check that a tcp server is running on host:port
    if args.pingtest and not _is_socket_open(host, port, retries=5, delay=2,
        verbose=True):
        raise RuntimeError("TCP server not detected on host {}:{}".format(host, port))

    print("Creating socket-based package logger to talk to host {0}:{1}...".format(
        host, port))
    log_name = args.log_name or args.pkg_name + '_logger'
    logger = create_package_logger(log_name, args.pkg_name, host, port)

    print("Sending test messages to logger {}...".format(logger.name))
    _send_test_messages(logger)
