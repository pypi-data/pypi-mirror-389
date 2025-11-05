#!/bin/bash
# Build the documentation set for the current Afterburner project.
#
# Assumes that the doc tree follows the default sphinx directory layout, i.e.
# with source files under the 'src' directory, and built files created under
# the 'src/_build' directory. The alternative scheme (separate 'source' and
# 'build' directories) could be accommodated with minor modification to this
# script.

# Exit on error.
set -e

# Build API documentation.
libdir="../../lib"
if [ -d $libdir ]; then
   echo "Creating API documentation sources..."
   sphinx-apidoc -e -f -T -o apidoc $libdir >/dev/null
else
   echo "WARNING: unable to find Python source files."
fi

# Build html documentation.
echo "Creating HTML documentation..."
make html >/dev/null
