# (C) British Crown Copyright 2016-2023, Met Office
#
# See the LICENSE.TXT file included with the Afterburner
# software distribution for full license details.
"""
This is the setup.py file for the Afterburner Python package.

Enter 'python setup.py --help' to view a list of the commands and options
supported by this setup file.
"""
from __future__ import print_function

import os
import sys
import re
import subprocess
import multiprocessing
from setuptools import setup, find_packages, Command
from setuptools.command.install import install


# Stop debug messages being printed to screen when running the tests.
import logging
logging.getLogger('fiona').setLevel(logging.INFO)
logging.getLogger('matplotlib').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)


class CustomInstall(install):
    """Extends the standard install command."""

    description = "install the Afterburner software package"
    user_options = install.user_options + [
        ('no-etc-dir', None, 'do not install the etc directory'),
        ('no-tools-dir', None, 'do not install the tools directory')]
    boolean_options = ['no-etc-dir', 'no-tools-dir']

    def initialize_options(self):
        install.initialize_options(self)
        self.no_etc_dir = False
        self.no_tools_dir = False

    def finalize_options(self):
        install.finalize_options(self)

    def run(self):
        install.run(self)
        if self.no_etc_dir:
            print("Skipping installation of 'etc' directory.")
        else:
            self._install_custom_dir('etc')
        if self.no_tools_dir:
            print("Skipping installation of 'tools' directory.")
        else:
            self._install_custom_dir('tools')

    def _install_custom_dir(self, dirname):
        """
        Install a custom directory to one of the following directories (and in
        the order shown):

        * the directory specified by the --home command-line option
        * the directory specified by the --prefix command-line option
        * the installation base directory
        """

        try:
            if self.home:
                dest_dir = os.path.abspath(self.home)
            elif self.prefix:
                dest_dir = os.path.abspath(self.prefix)
            else:
                dest_dir = os.path.abspath(self.install_base)

            # Could use distutils.dir_util.copy_tree function as an alternative
            # to the rsync command.
            cmd = "rsync -arz {0} {1}".format(dirname, dest_dir)
            if self.dry_run:
                print("dry-run:", cmd)
                return

            print("Copying '{0}' directory to {1}/{0}...".format(dirname, dest_dir))
            if not os.path.exists(dest_dir): os.makedirs(dest_dir)
            subprocess.check_call(cmd, shell=True)
            print("Successfully copied '{0}' directory.".format(dirname))

        except (OSError, subprocess.CalledProcessError):
            print("ERROR: Problem trying to install '{0}' directory using "
                  "command:\n{1}".format(dirname, cmd))
            raise


class BuildDocs(Command):
    """
    Command class for building sphinx documentation. Assumes that the doc tree
    follows the default sphinx directory layout, i.e. with source files under
    the 'src' directory, and built files under the 'src/_build' directory.
    """
    # Specify command usage and options.
    description = "build sphinx documentation"
    user_options = []

    def initialize_options(self):
        self.src_dir = 'doc/src'

    def finalize_options(self):
        self.src_dir = os.path.abspath(self.src_dir)

    def run(self):
        cwd = os.getcwd()
        try:
            os.chdir(self.src_dir)
            build_script = os.path.join(self.src_dir, 'build_docs.sh')
            subprocess.check_call(build_script, shell=True)
            print("Documentation built successfully.")
        except subprocess.CalledProcessError as exc:
            print("ERROR: while trying to build documentation.")
            print(str(exc))
        finally:
            os.chdir(cwd)


class InstallDocs(Command):
    """
    Command class for installing already built sphinx documentation. Assumes
    that the doc tree follows the default sphinx directory layout, i.e.
    with built files under the 'src/_build' directory.
    """
    # Specify command usage and options.
    description = "install sphinx documentation"
    user_options = [
        ('dst-dir=', None, 'pathname of the directory under which to install '
            'built documentation'),
        ('host=', None, 'name of host if installing to a remote machine '
            '(no default)'),]

    def initialize_options(self):
        self.bld_dir = 'doc/src/_build'
        self.dst_dir = ''
        self.host = ''

    def finalize_options(self):
        self.bld_dir = os.path.abspath(self.bld_dir)
        self.dst_dir = os.path.expanduser(os.path.expandvars(self.dst_dir))
        self.dst_dir = os.path.abspath(self.dst_dir)

    def run(self):
        if not self.dst_dir:
            print("ERROR: the --dst-dir option must be specified. Use 'python "
                "setup.py --help install_docs' for more details.")
            sys.exit(1)
        self._install_html_docs()

    def _install_html_docs(self):
        """
        Copy html files over to the destination directory specified via the
        --dst-dir option. The rsync command is used to effect the copy as it
        can handle file transfers to both local and remote destinations.
        """
        html_dir = os.path.join(self.bld_dir, 'html')

        try:
            # If a remote host is specified then we need to use the --rsync-path
            # option to ensure that intermediate directories exist on the host.
            if self.host:
                dest_dir = self.host + ':' + self.dst_dir
                cmd = "rsync -arz --rsync-path='mkdir -p {} && rsync' {} {}".format(
                    self.dst_dir, html_dir, dest_dir)

            # Otherwise for local file copy operations we can use a plain rsync
            # command. Again, we ensure that intermediate directories exist.
            else:
                dest_dir = os.path.abspath(self.dst_dir)
                cmd = "rsync -arz {} {}".format(html_dir, dest_dir)
                if not os.path.exists(dest_dir): os.makedirs(dest_dir)

            print("Copying HTML files to {}/html...".format(dest_dir))
            subprocess.check_call(cmd, shell=True)
            print("HTML files installed successfully.")
        except (OSError, subprocess.CalledProcessError):
            print("ERROR: while trying to install HTML files using command:")
            print(cmd)
            raise


def find_scripts(scriptdir='bin'):
    """
    Return a list of the files in the scripts directory.
    """
    return [os.path.join(scriptdir, fn) for fn in os.listdir(scriptdir)]


def extract_version():
    """
    Retrieve version information from the afterburner __init__.py module.
    """
    version = ''
    ab_dir = os.path.dirname(__file__)
    filename = os.path.join(ab_dir, 'lib', 'afterburner', '__init__.py')

    with open(filename) as fd:
        for line in fd:
            line = line.strip()
            if line.startswith('__version_info__'):
                try:
                    version_info = line.split('=')[1]
                    regex = r'\s*\((\d+),\s*(\d+),\s*(\d+),\s*(.*),.*'
                    m = re.match(regex, version_info)
                    if m:
                        version = '.'.join(m.group(1, 2, 3)) + m.group(4)[1:-1]
                except AttributeError:
                    version = '?.?.?'
                    print("WARNING: Unable to parse version information from "
                        "file: {}".format(filename))

    return version


# Read the project's long description from the README.md file.
with open('README.md', 'r') as fh:
    LONG_DESC = fh.read()

# Define this project's properties.
setup(
    name='metoffice-afterburner',
    version=extract_version(),
    description='Tools and apps for processing numerical climate model data',
    long_description=LONG_DESC,
    long_description_content_type='text/markdown',
    author='UK Met Office',
    author_email='afterburner@metoffice.gov.uk',
    url='https://code.metoffice.gov.uk/trac/afterburner',
    py_modules=['package_logger'],
    packages=find_packages('lib'),
    package_dir={'': 'lib'},
    package_data={},
    scripts=find_scripts(),
    install_requires=['scitools-iris>=2.1', 'pyparsing>=2', 'windspharm'],
    python_requires='>=2.7',
    extras_require={'test': ['pytest']},
    cmdclass={
        'build_docs': BuildDocs,
        'install': CustomInstall,
        'install_docs': InstallDocs,
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
    ],
    zip_safe=False
)
