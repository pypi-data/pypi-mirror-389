#!/bin/bash
# (C) British Crown Copyright 2019, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
#
# SYNOPSIS
#
#   start_log_server.sh [-h | --help]
#   start_log_server.sh [options]
#
# DESCRIPTION
#
#   Script for launching a TCP server that listens for Python logging requests
#   on a user-defined host and port. The script is a convenience wrapper around
#   the start_log_server.py Python script/module.
#
# ARGUMENTS
#
#   none
#
# OPTIONS
#
#   -H, --host=<hostname>
#       The name of the host on which to start the TCP server.
#
#   -P, --port=<port>
#       The port number on which the TCP serer will listen for Python logging
#       requests.
#
#   --logdir=<path>
#       The pathname of the directory below which to create daily logfiles, the
#       names of which adhere to the format YYYY-MM-DD.log. If undefined then
#       logfiles are created in the current working directory.
#
# ENVIRONMENT VARIABLES
#
#   SCITOOLS_MODULE
#       The name of the SciTools module to load prior to running any Python
#       commands. If undefined then the default module that will be loaded is
#       'scitools/default-current'. Alternatively, this variable can be
#       set to 'none' to skip explicit loading of a SciTools module.

# Potentially useful additional command options:
# --verbose  : turn on verbose mode
# --scitools : specify the scitools module to load
# --force    : kill existing server process if running

set -e
has_module=$(type -t module || echo '')

#-------------------------------------------------------------------------------
# Function definitions
#-------------------------------------------------------------------------------

# Attempt to load the module specified via parameter $1.
load_module () {
   # Test for presence of the module function. Return immediately if not found.
   if [ -z "$has_module" ]; then
      return 0
   fi

   # Determine the target module. If it's set to 'none' then return.
   target_mod=$1
   if [ "$target_mod" == "none" ]; then
      return 0
   fi

   # If a sibling module is already loaded then swap in the target module.
   # Otherwise just load the target module.
   loaded_mod=$((module -t list 2>&1 | grep ${target_mod%%/*}) || echo "none")
   if [ "$loaded_mod" == "none" ]; then
      module load $target_mod || echo "WARNING: Unable to load module $target_mod"
   else
      module swap $target_mod || echo "WARNING: Unable to load module $target_mod"
   fi
}

#-------------------------------------------------------------------------------
# Main script
#-------------------------------------------------------------------------------

# Save input arguments/options for later use.
args=$@

cmdname=$(basename $0)
cmdline_opt=`getopt -o hH:P: --longoptions help,host:,port:,logdir: -n "$cmdname" -- "$@"`

usage="Usage: $cmdname [-h|--help] [-H|--host=host] [-P|--port=port] [--logdir=path]"

# Set default option values.
host=localhost
port=9020
logdir=~/logs/afterburner

eval set -- "$cmdline_opt"

while true ; do
    case "$1" in
        -h|--help) echo -e $usage ; exit 0 ;;
        -H|--host) host=$2 ; shift 2 ;;
        -P|--port) port=$2 ; shift 2 ;;
        --logdir) logdir=$2 ; shift 2 ;;
        --) shift ; break ;;
        *) echo "Error parsing command line" ; exit 1 ;;
    esac
done

# Set the full host address.
if [ -n "$port" ]; then
    address=$host:$port
else
    address=$host
fi

# Check to see if a TCP server is already running on host:port
# Note that the timeout command below is bash-specific. For further info see:
# https://stackoverflow.com/questions/4922943/test-if-remote-tcp-port-is-open-from-a-shell-script
status=$(/bin/timeout 5 /bin/bash -c "</dev/tcp/${host}/${port}" 2>/dev/null; echo $?)
if [ $status -eq 0 ]; then
    echo "A TCP server is already running on host $address"
    exit 1
fi

# Load a scitools module if one has been specified via the SCITOOLS_MODULE variable.
load_module ${SCITOOLS_MODULE:=scitools/default-current}

# Start a TCP server on the specified host and port.
# For now we simply pass over all the input arguments/options. In future we
# might only need to pass a subset of arguments/options.
if (python3 start_log_server.py $args &) ; then
    echo "Started a TCP server on host $address"
else
    echo "Error trying to start a TCP server on host $address" >&2
    exit 2
fi
