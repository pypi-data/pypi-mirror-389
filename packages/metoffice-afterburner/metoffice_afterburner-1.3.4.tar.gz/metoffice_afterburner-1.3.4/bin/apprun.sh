#!/bin/bash -l
# (C) British Crown Copyright 2020, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
#
# SYNOPSIS
#
#   apprun.sh [-h | --help]
#   apprun.sh <app_name> [app-options] [app-arguments]
#   apprun.sh [script-options] -- <app_name> [app-options] [app-arguments]
#
# DESCRIPTION
#
#   The apprun.sh script is a thin shell wrapper around the abrun.py Python script.
#   Its main purpose is to provide a simple and uniform mechanism for invoking an
#   Afterburner processing application (a.k.a. Afterburner app), either from the
#   command-line or from within a Rose suite or cron job.
#
#   This script is a replacement for the abrun.sh script. It is designed to invoke
#   an Afterburner app within a Python3-based SciTools environment. In theory the
#   script could be invoked in such a way as to execute within a Python2.7-based
#   environment; this, however, is discouraged.
#
#   By default the app is invoked within the 'scitools/default' environment.
#   This can be changed using either the SCITOOLS_MODULE environment variable
#   or the --sci-module command-line option. The latter takes precedence.
#
#   The directory location of the Afterburner software suite is obtained either
#   directly from the AFTERBURNER_HOME_DIR environment variable, or else it is
#   derived from the directory path of the current script. If the --ab-module
#   command-line option is used to specify the name of an Afterburner module to
#   load then the AFTERBURNER_HOME_DIR environment variable automatically gets
#   set to the correct location.
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
# SCRIPT OPTIONS
#
#   NOTE: If any of the options and switches described below are included in the
#   command invocation then, as per the SYNOPSIS, the -- token must be used to
#   signal the end of script options/switches, and the start of the Afterburner
#   app name and its options (if any are required).
#
#   --ab-module=<afterburner-module>
#       The name of the Afterburner module to load prior to running any Python
#       commands. This option overrides the AFTERBURNER_MODULE environment variable
#       if that is defined (see the ENVIRONMENT VARIABLES section below).
#
#   --debug
#       Turn on diagnostic messages. Useful for troubleshooting runtime issues,
#       typically in combination with the --dry-run switch.
#
#   -n, --dry-run
#       Execute in dry-run mode. This just prints out any diagnostic messages (if
#       --debug is enabled) and prints the final command that would get executed
#       in order to invoke the specified Afterburner app (which, in this particular
#       instance, could be entirely fabricated since it won't get run).
#
#   --py=<python-version>
#       This option may be used to specify a particular version of Python within
#       which to invoke the requested Afterburner application. You can specify
#       just the major version, e.g. --py=3, or the major and minor version, e.g.
#       --py=3.6. Note that this command-line option overrides the PYTHON_EXEC
#       variable, if that is defined. If the requested Python version cannot be
#       found in the runtime environment then the plain 'python' command is used.
#
#   --reset-pypath
#       If this switch is included in the command invocation then the PYTHONPATH
#       environment variable is reset (to the empty string) before being built
#       up with the required locations of, e.g., the Rose and Afterburner Python
#       packages.
#
#   --sci-module=<sci-module>
#       The name of the SciTools module to load prior to running any Python
#       commands. This option overrides the SCITOOLS_MODULE environment variable
#       if that is defined (see the ENVIRONMENT VARIABLES section below).
#
#   Any additional options or arguments are passed through as-is to the specified
#   Afterburner application.
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
#       (e.g. within an appropriate shell start-up script).
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
#       one might set this to 'python3.6' if that is the version of Python 3 you
#       with to use. See also the --py command-line option.
#
#   SCITOOLS_MODULE
#       The name of the SciTools module to load prior to running any Python
#       commands. If undefined then the default module that will be loaded is
#       'scitools/default'. Alternatively, this variable can be set to 'none' to
#       skip explicit loading of a SciTools module, in which case the default
#       version of Python provided by the user's runtime environment will be used.
#
# EXIT STATUS
#
#   0: Succesful completion.
#   1: Invalid command invocation (e.g. missing argument).
#   N: An Afterburner error code.

set -e
has_module=$(type -t module || echo '')

cmdname=$(basename $0)
usage="SYNOPSIS
    $cmdname -h|--help
    $cmdname <app_name> [app-options] [app-arguments]
    $cmdname [script-options] -- <app-name> [app-options] [app-arguments]

ARGUMENTS
    app-name - The name of the Afterburner app to run. This should either be the
               leaf name or the full dotted pathname of the app's Python class.

SCRIPT-OPTIONS
    --ab-module=<afterburner-module> - Load the named afterburner module
    --debug                          - Print diagnostic/debug information
    --dry-run,-n                     - Enable dry-run mode (doesn't run the app)
    --py=<python-version>            - Run app using the specified Python version
    --reset_pypath                   - Set PYTHONPATH variable from clean state
    --sci-module=<sci-module>        - Load the named scitools module
"

#-------------------------------------------------------------------------------
# Function definitions
#-------------------------------------------------------------------------------

# Augment PYTHONPATH using the colon-delimited directory paths passed in via
# parameter $1. Paths are added to the front of PYTHONPATH.
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
   export PYTHONPATH
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

   # Try to unload the target module using just its base name. This will complete
   # silently if the module is not loaded. Then load the target module using its
   # full name. This approach should be more robust than trying to determine if
   # the target module is loaded and then calling module swap or module load.
   target_base=${target_mod%%/*}
   module unload $target_base || true
   module load $target_mod
   if ! module -t list 2>&1 | grep -q $target_base ; then
      echo "WARNING: Unable to load module $target_mod"
      return 1
  fi
}

# Print script usage.
print_usage () {
    echo "$usage" | while IFS= read -r line ; do echo "$line"; done
}

#-------------------------------------------------------------------------------
# Main script
#-------------------------------------------------------------------------------

if [ $# -eq 0 ]; then
   echo "WARNING: No command-line arguments specified."
   print_usage
   exit 1
fi

if [ "$*" == "-h" -o "$*" == "--help" ]; then
   print_usage
   exit 0
fi

# Set option defaults.
abargs=()
ab_module=${AFTERBURNER_MODULE:-none}
debug=0
dryrun=0
python_cmd=${PYTHON_EXEC:-python}
reset_pypath=0
sci_module=${SCITOOLS_MODULE:-scitools/default}

# Configure command-line options.
shortopts="hn"
longopts="debug,dry-run,help,py:,reset-pypath,ab-module:,sci-module:"
if [[ "$*" != *--\ * ]]; then
   cmdargs=("--" "$@")
else
   cmdargs=("$@")
fi

# Process command-line options.
#echo "i/p cmd args: ${cmdargs[@]}"
cmdargs=$(getopt -o "$shortopts" --long "$longopts" -n "$cmdname" -- "${cmdargs[@]}")
eval set -- "$cmdargs"
#echo "o/p cmd args: ${cmdargs}"

while true; do
   case "$1" in
      -h|--help)
         print_usage
         exit 0 ;;
      -n|--dry-run)
         dryrun=1
         shift ;;
      --ab-module)
         ab_module=$2
         shift 2 ;;
      --debug)
         debug=1
         shift ;;
      --py)
         python_cmd="python$2"
         shift 2 ;;
      --reset-pypath)
         reset_pypath=1
         shift ;;
      --sci-module)
         sci_module=$2
         shift 2 ;;
      --)
         shift
         abargs=("$@")
         break ;;
   esac
done

# Reset the PYTHONPATH variable if required.
if [ $reset_pypath -eq 1 ]; then
   export PYTHONPATH=""
fi

# Add location of Rose package to PYTHONPATH.
rose_cmd=$(which rose 2>/dev/null || echo '')
if [[ -n $rose_cmd ]]; then
   rose_pkg_dir=$(rose --version | sed 's/^.*(\(.*\))$/\1/')/lib/python
   if [[ -d $rose_pkg_dir ]]; then
      augment_pythonpath $rose_pkg_dir
   fi
else
   echo "WARNING: Unable to determine location of Rose python package."
fi

# Add a "scitools/" prefix to the scitools module name if required.
if [[ "$sci_module" != "none" ]] && [[ ! "$sci_module" =~ ^scitools/.* ]]; then
   sci_module="scitools/$sci_module"
fi

# Add an "afterburner/" prefix to the afterburner module name if required.
if [[ "$ab_module" != "none" ]] && [[ ! "$ab_module" =~ ^afterburner/.* ]]; then
   ab_module="afterburner/$ab_module"
fi

# Load a scitools module if one has been specified via the sci-module option or
# the SCITOOLS_MODULE variable.
load_module $sci_module || exit 1

# Load an afterburner module if one has been specified via the --ab-module option
# or the AFTERBURNER_MODULE variable.
# NB: a scitools module is a prerequisite for loading an afterburner module.
load_module $ab_module || exit 1

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

# Add location of Afterburner package to PYTHONPATH if an afterburner module
# has NOT been loaded, either by this script or by the calling environment.
loaded_mod=$(module -t list 2>&1 | grep afterburner || echo '')
if [[ -z $loaded_mod ]]; then
   augment_pythonpath $($python_cmd ${bindir}/abconfig --pythonpath)
fi

# Removing any trailing ':' character from PYTHONPATH.
export PYTHONPATH=${PYTHONPATH/%:/}

# Extract the Afterburner application class name.
app_name=${abargs[0]}

# If debug mode is on then print some useful diagnostic information.
if [ $debug -eq 1 ]; then
   hdr=$(printf '=%.0s' {1..30})
   echo
   echo "$hdr DEBUG INFO $hdr"
   echo "AFTERBURNER_HOME_DIR: $AFTERBURNER_HOME_DIR"
   echo "PYTHONPATH: ${PYTHONPATH:-not defined}"
   echo "Python command: $(which $python_cmd)"
   echo "SciTools module: $sci_module"
   echo "Rose package location: ${rose_pkg_dir:-not defined}"
   echo "Afterburner module: $ab_module"
   echo "Afterburner app: $app_name"
   echo "App arguments: ${abargs[*]:1}"
   echo "$hdr============$hdr"
   echo
fi

# Invoke the abrun.py script, passing through any options and arguments
if [ $dryrun -eq 1 ]; then
   echo "App invocation: $python_cmd ${bindir}/abrun.py ${app_name} ${abargs[*]:1}"
else
    $python_cmd ${bindir}/abrun.py ${app_name} ${abargs[*]:1}
fi
