Tutorial #1: Accessing the Afterburner Python Package
=====================================================

This short tutorial describes how to configure your Python environment in order
to access the `afterburner` Python package on the Met Office Scientific Desktop
environment, which is currently based upon Red Hat Enterprise Linux v7 (RHEL7).
The instructions should be similar on other UN*X-like platforms on which Afterburner
software is installed.

**METHOD 1:** The first and possibly easiest method is to use the ``module`` command
to load afterburner, as follows. Note that the `scitools` module is a prerequisite.

.. code-block:: sh

    % source /data/users/afterburner/modules/setup
    % module load scitools
    % module load afterburner

The final command above loads the current (stable) release of the afterburner package.
To load the latest (development) release the command should be changed to ``module load
afterburner/latest``.

**METHOD 2:** This method involves setting, or appending to, the PYTHONPATH
environment variable, as shown below. This may be done on a per interactive session
basis, or you could set this variable once within an appropriate shell startup
script (such as ``~/.bashrc``).

For the current stable software release:

.. code-block:: sh

    % export PYTHONPATH=/data/users/afterburner/software/turbofan/current/lib/python

Or for the latest development release:

.. code-block:: sh

    % export PYTHONPATH=/data/users/afterburner/software/turbofan/latest/lib/python

**METHOD 3:** As an alternative to setting the PYTHONPATH environment variable one
could insert or append one of the aforementioned directory paths to the ``sys.path``
list object within a Python session or script. This method is usually only convenient
as a temporary arrangement.

.. code-block:: py

    >>> import sys
    >>> sys.path.append('/data/users/afterburner/software/turbofan/current/lib/python')

**METHOD 4:** Finally, it is also possible to type one or other of the aforementioned
directory paths into a Python .pth file saved under a suitable directory (the
directory ``~/.local/lib/pythonM.N/site-packages`` is a good choice). If you employ
this method then it is recommended that the file is named ``afterburner.pth`` as a
means of highlighting its purpose.

(Note for Met Office HPC users: In the aforementioned directory paths replace
``/data/users`` with ``$UMDIR``)

With one of the above methods applied you should then be able to import the
`afterburner` package (or, rather, its top-level module) as illustrated below.
Typically one also needs to import specific modules, functions and classes from
sub-packages of the `afterburner` package.

.. code-block:: py

    >>> import afterburner
    >>> afterburner.__version__
    '1.3.0'
    >>> from afterburner.metavar import UmMetaVariable

Back to the :doc:`Tutorial Index <index>`
