#!/bin/bash -l
# (C) British Crown Copyright 2016-2021, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
#
# SYNOPSIS
#
#   abrun.sh [-h | --help]
#   abrun.sh <app_name> [options] [arguments]
#
# DESCRIPTION
#
#   This script is a thin shell wrapper around the abrun.py Python script. Its
#   main purpose is to provide a simple and uniform mechanism for invoking an
#   Afterburner processing application (a.k.a. Afterburner app), either from the
#   command-line or from within a Rose suite or cron job.
#
# ARGUMENTS
#
#   app_name
#       Specifies the name of the Python class in the Afterburner software suite
#       which implements the application. The class name should either be the
#       full dotted class path, e.g. afterburner.apps.pp_to_nc.PpToNc, or the
#       bare class name if the class has been imported into the namespace of the
#       afterburner.apps package.
#
# OPTIONS
#
#   --pyM[.N]
#       This option may be used to specify a particular version of Python within
#       which to invoke the requested Afterburner application. You can specify
#       just the major version, e.g. --py3, or the major and minor version, e.g.
#       --py3.6. Note that this command-line option overrides the PYTHON_EXEC
#       variable, if that is defined. If the requested Python version cannot be
#       found in the runtime environment then the plain 'python' command is used.
#
#   Any additional options or arguments are passed through as-is to the specified
#   processing application.
#
# ENVIRONMENT VARIABLES
#
#   AFTERBURNER_HOME_DIR
#       This environment variable may be used to specify the home directory of
#       the Afterburner software suite. If unspecified then the default directory
#       path is determined from the location of the current script. Depending on
#       how this script is invoked, however, this method cannot always be relied
#       upon to yield the correct path. Consequently it is recommended that, in
#       normal use, the AFTERBURNER_HOME_DIR variable should be defined explicitly
#       (typically within an appropriate shell start-up script).
#
#   AFTERBURNER_MODULE
#       The name of the Afterburner module to load prior to running any Python
#       commands. If this variable is undefined or set to 'none' then no attempt
#       is made to load an Afterburner module. In that case the location of the
#       Afterburner python package is determined by the abconfig script (which
#       can be found alongside the current script). The returned location is then
#       prepended to the PYTHONPATH variable.
#
#   PYTHON_EXEC
#       This environment variable may be used to specify the name (or full path)
#       of the Python command used to run the Afterburner software. For example,
#       one might set this to 'python3.6' if that is the version of Python 3 on
#       your operating system.
#
#   SCITOOLS_MODULE
#       The name of the SciTools module to load prior to running any Python
#       commands. If undefined then the default module that will be loaded is
#       'scitools/production_legacy-os43-2'. Alternatively, this variable can be set to
#       'none' to skip explicit loading of a SciTools module, in which case the
#       default version of Python provided by the user's runtime environment will
#       be used.
#
#       NOTE: Use of the SCITOOLS_MODULE variable to load a particular SciTools
#       module is preferred over the SCITOOLS_PATH method, which is now deprecated.
#
#   SCITOOLS_PATH
#       This environment variable may be used to specify a colon-delimited list
#       of SciTools directory paths to prepend to the PYTHONPATH variable prior
#       to invoking the requested Afterburner app. Directories already present
#       in PYTHONPATH are silently ignored.
#
#       NOTE: Use of the SCITOOLS_PATH variable is deprecated in favour of the
#       SCITOOLS_MODULE variable, as described above. Setting both variables is
#       likely to lead to conflicts and is therefore strongly discouraged.
#
# EXIT STATUS
#
#   0: Succesful completion.
#   1: Invalid command invocation (e.g. missing argument).
#   N: An Afterburner error code.

set -e
has_module=$(type -t module || echo '')

#-------------------------------------------------------------------------------
# Function definitions
#-------------------------------------------------------------------------------

# Augment PYTHONPATH using the colon-delimited directory paths passed in via
# parameter $1. Paths are prepended to the front of PYTHONPATH.
augment_pythonpath () {
   # Read directory paths from $1 into array variable PATHLIST.
   IFS=':' read -ra PATHLIST <<< "$1"

   # Loop over the paths specified in parameter $1 in reverse order.
   for (( idx=${#PATHLIST[@]}-1 ; idx>=0 ; idx-- )); do
      path=${PATHLIST[idx]}
      if [[ -z "$PYTHONPATH" ]]; then
         PYTHONPATH=$path
      elif [[ ! $PYTHONPATH =~ (^|.+:)$path(:.+|$) ]]; then
         PYTHONPATH=$path:$PYTHONPATH
      fi
   done
}

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

echo
echo "WARNING: The Afterburner abrun.sh script is now deprecated. It is recommended"
echo "#######: that you upgrade to using the newer Python3-based apprun.sh script."
echo

# Check command-line syntax.
usage="abrun.sh <app_name> [options] [arguments]"
if [ $# -eq 0 ]; then
   echo "ERROR: Missing argument(s)."
   echo "Usage: $usage"
   exit 1
elif [ ${1//-/} = "h" -o ${1//-/} = "help" ]; then
   echo "Usage: $usage"
   exit 0
fi

# Load a scitools module if one has been specified via SCITOOLS_MODULE.
load_module ${SCITOOLS_MODULE:=scitools/production_legacy-os43-2}

# Load an afterburner module if one has been specified via AFTERBURNER_MODULE.
load_module ${AFTERBURNER_MODULE:=none}

# Select the python executable to use as follows:
# 1. the version, if any, specified via the --py command-line option
# 2. the value of $PYTHON_EXEC if it's defined
# 3. otherwise plain 'python'
python_cmd=python
if [[ -n $PYTHON_EXEC ]]; then
   python_cmd=$PYTHON_EXEC
fi

# Scan the argument list for a --pyM[.N] option which can be used to override
# the default python command as set above.
arglist=()
for var in "$@"; do
   if [[ "$var" == --py* ]]; then
      python_cmd=python${var#--py}
   else
      arglist+=($var)
   fi
done

# Check to see if the required python command is on the command search path.
has_py=$(which $python_cmd 2>/dev/null || echo '')
if [[ -z $has_py ]]; then
   echo "WARNING: $python_cmd command not found; reverting to plain 'python' command."
   python_cmd=python
fi

# Obtain the path of the Afterburner bin directory. If the AFTERBURNER_HOME_DIR
# environment variable has been set, then use that. Otherwise set it to the
# directory containing this script.
if [[ -n $AFTERBURNER_HOME_DIR ]]; then
   bindir=${AFTERBURNER_HOME_DIR}/bin
else
   bindir=$(dirname $($python_cmd -c 'import sys, os; print(os.path.realpath(sys.argv[1]))' $0))
   export AFTERBURNER_HOME_DIR=$(dirname $bindir)
fi

# Prepend location(s) of SciTools packages to PYTHONPATH.
if [[ -n $SCITOOLS_PATH ]]; then
   echo
   echo "*** NOTE: The use of SCITOOLS_PATH is now deprecated. Please use the"
   echo "*** SCITOOLS_MODULE variable instead to specify a SciTools module name."
   echo
   augment_pythonpath $SCITOOLS_PATH
fi

# Prepend location of Rose package to PYTHONPATH.
rose_cmd=$(which rose 2>/dev/null || echo '')
if [[ -n $rose_cmd ]]; then
   rose_pkg_dir=$(rose --version | sed 's/^.*(\(.*\))$/\1/')/lib/python
   if [[ -d $rose_pkg_dir ]]; then
      augment_pythonpath $rose_pkg_dir
   fi
else
   echo "WARNING: Unable to determine location of rose python package."
fi

# Prepend location of Afterburner package to PYTHONPATH if an afterburner module
# has not been loaded, either by this script or by the calling environment.
loaded_mod=$((module -t list 2>&1 | grep afterburner) || echo '')
if [[ -z $loaded_mod ]]; then
   PYTHONPATH=$($python_cmd ${bindir}/abconfig --pythonpath):${PYTHONPATH}
   export PYTHONPATH=${PYTHONPATH/%:/}
fi

# Extract the Afterburner application class name.
app_name=${arglist[0]}

# Invoke the abrun.py script, passing through any options and arguments
$python_cmd ${bindir}/abrun.py ${app_name} ${arglist[*]:1}
