#!/usr/bin/env python
"""
Initialises a socketserver.ThreadingTCPServer instance on a named host and port
(default: 9020) for the purpose of listening to Python logging requests sent
via a socket handler.

Adapted from the recipe included in Python's Logging Cookbook. See:
https://docs.python.org/dev/howto/logging-cookbook.html#sending-and-receiving-logging-events-across-a-network

Outline of methodology and component parts:

1. A TCP server is started on host:port and configured to utilise a handler of
   type ``socketserver.StreamRequestHandler`` to process LogRecord requests.
2. A python application creates a logger object with a handler of type
   ``logging.handlers.SocketHandler``. The handler is configured to send LogRecords
   to the TCP server at host:port.
3. The python application emits messages to the logger, which sends a request
   (as a pickled LogRecord object) to the TCP server.
4. The TCP server picks up the request and hands it off to the ``handle()``
   method of the ``socketserver.StreamRequestHandler``.
5. The ``handle()`` method unpickles the LogRecord object and gathers various bits
   of runtime information (timestamp, user, package version, python version, etc).
6. The ``handle()`` method creates a formatted text string combining the runtime
   information and the original text message, if any, attached to the LogRecord.
7. The final text string is then appended to the appropriate logfile, the name of
   which is derived from the current date (e.g. ../1970/jan/1970-01-16.log for a
   logfile created on 16 Jan 1970).

"""
from __future__ import (absolute_import, print_function)

import argparse
import datetime
import logging
import logging.handlers
import os
import pickle
import select
import socketserver
import struct
import sys

DEFAULT_PORT = logging.handlers.DEFAULT_TCP_LOGGING_PORT


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """
    Handler class for handling LogRecord objects streamed to a TCP server process.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length, followed
        by the LogRecord in pickle format. Logs the record according to whatever
        policy is configured locally.
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = pickle.loads(chunk)
            record = logging.makeLogRecord(obj)
            self.handle_record(record)

    def handle_record(self, record):
        """Handle a LogRecord object."""

        # Note: EVERY record gets logged. This is because Logger.handle is
        # normally called AFTER logger-level filtering. If you want to do
        # filtering, do it at the client end to save wasting cycles and network
        # bandwidth!

        logfile = get_logfile_path(base_dir=self.server.logdir)
        if not os.path.exists(os.path.dirname(logfile)):
            # parent directory does not exist so try to create it
            try:
                os.makedirs(os.path.dirname(logfile))
            except OSError as exc:
                print(str(exc), file=sys.stderr)
                return

        # Open logfile in append mode and write log message to it.
        with open(logfile, 'a') as fh:
            text = "{0}\n".format(record.getMessage())
            fh.write(text)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
    Class for implementing a TCP server capable of receiving and processing
    client requests containing LogRecord objects.
    """

    # TODO: what's the best setting for this attribute?
    allow_reuse_address = True

    def __init__(self, host='localhost', port=DEFAULT_PORT, logdir=None,
            timeout=1, handler=LogRecordStreamHandler):
        """
        Create a non-blocking threaded TCP server that listens for logging
        requests.

        :param str host: The host on which to launch the TCP server.
        :param int port: The port number on which to listen for requests.
        :param logdir: The pathname of the directory under which to create
            logfiles.
        :param timeout: The timeout period in seconds when checking for incoming
            socket events. The timeout value is passed to the ``select.select()``
            method.
        :param object handler: The handler instance object that will handle
            logging requests.
        """

        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)

        # set to True to abort the server
        self.abort = False

        # max time (in seconds) for handle_request() to wait for a request
        self.timeout = timeout

        # base directory under which to create logfiles; default is $PWD
        self.logdir = logdir

    def serve_until_stopped(self):
        """Serve client requests until the server is stopped."""

        # TODO: consider using selectors.SelectSelector here (Py 3.4+)

        abort = False
        while not abort:
            rd, _wr, _ex = select.select([self.socket.fileno()], [], [], self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort


def main():
    """Main control function."""

    args = parse_args()
    host = args.host or 'localhost'
    port = args.port or DEFAULT_PORT

    logdir = args.logdir
    if logdir:
        logdir = os.path.expanduser(os.path.expandvars(logdir))
        if os.path.isdir(logdir):
            os.chdir(logdir)

    if args.verbose:
        print("Starting TCP log server on host {0}:{1}...".format(host, port))

    try:
        tcpserver = LogRecordSocketReceiver(host=host, port=port, logdir=logdir)
        if args.verbose:
            print("reuse address =", tcpserver.allow_reuse_address)
            print("queue size =", tcpserver.request_queue_size)
            print("timeout =", tcpserver.timeout)
            # can we get pid of server process? (try using lsof or ss commands)
            print("Listening...")
        tcpserver.serve_until_stopped()

    except KeyboardInterrupt:
        tcpserver.server_close()
        if args.verbose:
            print("\nStopped TCP log server via keyboard interrupt.")


def parse_args():
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        usage="%(prog)s [options]",
        description="Start a socket-based TCP server to listen for logging requests")

    parser.add_argument("-H", "--host",
        help="hostname on which to start the server (default: localhost)")
    parser.add_argument("-P", "--port", type=int,
        help="port on which to listen for logging requests (default: 9020)")
    parser.add_argument("--logdir",
        help="pathname of base directory under which to store logfiles")
    parser.add_argument("-v", "--verbose", default=False, action='store_true',
        help="enable verbose mode")

    return parser.parse_args()


def get_logfile_path(base_dir=None):
    """
    Return the full path of the logfile to use for the current date and time.
    """
    dt = datetime.datetime.now()

    if not base_dir:
        base_dir = os.getcwd()
    else:
        base_dir = os.path.abspath(base_dir)

    logdir = os.path.join(base_dir, dt.strftime('%Y'), dt.strftime('%b').lower())
    logfile = "{}.log".format(dt.strftime('%Y-%m-%d'))

    return os.path.join(logdir, logfile)


if __name__ == '__main__':
    main()
