Overview of Key Software Components
===================================

The sections below provide an overview of the principal collections of Python
classes and functions provided by the Afterburner framework.

MASS Data Access Functions
--------------------------

The ``afterburner.io.moose2`` module provides a number of convenience functions
which act as an interface to the MOOSE command-line interface. These functions
can be used to retrieve or archive data files from or to MASS, the Met Office's
storage solution for weather and climate model data. The ``moose2`` module also
includes a handful of simple data query functions.

It is envisaged that retrieval of data files will be the most common operation.
The Afterburner framework is not really intended to provide a solution for
archiving large volumes of data to MASS.

The ``moose2`` module is not designed to be a complete interface to each and every
MOOSE command. Rather it aims to provide a general-purpose interface to the more
frequently used data retrieval and storage commands and options.

For further details, refer to the :doc:`/apiref`.

Meta-Variable Classes
---------------------

In the same way that meta-data is 'information about data', a meta-variable is
used to record information about model variables (a.k.a. diagnostics). It is
anticipated that most Afterburner applications will apply processing operations
to one or more model variables/diagnostics; hence it is useful to have a way of
representing what those variables are.

The current release of Afterburner provides Python classes for representing
UM diagnostics and NEMO model variables. These classes - ``UmMetaVariable`` and
``NemoMetaVariable`` - are implemented within the ``afterburner.metavar`` module.
Similar classes for other climate models (e.g. CICE, JULES) will be developed as
and when the need arises.

A meta-variable can be thought of simply as a *bundle of properties* which together
describe a variable/diagnostic of interest. As such, meta-variable objects are
similar to Iris cubes, but without a data payload. (For reasons to do with the
design of the ``iris.cube.Cube`` class, the decision was made not to use that class
as the basis for meta-variables.)

The standard meta-variable properties, as provided by the aforementioned classes,
focus on things like the source model, phenomenon identification, processing
methods, time coordinates, and calendar information. However, once a meta-variable
object has been instantiated, additional properties can be created (as instance
attributes) on an as-needs basis.

In the following code snippet, for example, a UM meta-variable is created and
then assigned a couple of custom properties::

    >>> from afterburner.metavar import UmMetaVariable
    >>> var = UmMetaVariable('10.3', 'mi-ab123', stream_id='apm', stash_code='m01s03i326')
    >>> var.short_name = 'tas'
    >>> var.experiment_name = 'historic'

.. _data-caches-and-data-stores:

Data Cache and Data Store Classes
---------------------------------

The majority of Afterburner applications are expected to make use of on-disk
stores - or caches - of model data files. A number of very large, persistent
data stores are already in use, e.g. the one used by the AutoAssess system.

However, with the arrival of new data processing infrastructures such as SPICE
and JASMIN, there is a drive to move away from persistent, high-volume data
stores, to shorter-residency, lower-volume data caches.

Within Afterburner, instances of ``DataCache`` classes are designed to be used
to set up and access on-disk caches of model data files. Various ``DataCache``
classes can be found in the ``afterburner.io.datacaches`` module. Each class
organises data files according to a particular caching scheme. For example, the
``VarSplitDataCache`` class organises model data files into a directory hierarchy
based upon suite id, stream id, and variable name.

Data cache objects must be associated with a data store object, the latter being
an instance of a ``DataStore`` class. A data store object provides the interface
to a specific back-end data store from which files are retrieved and placed in
the correct location within the data cache.

``DataStore`` classes can be found in the ``afterburner.io.datastores`` module.
At the time of writing only the ``MassDataStore`` class is available. Instances
of this class can be used to provide access to the MASS data archive system. This
class makes use of the ``afterburner.io.moose2`` module described above.

The data cache interface is built around the concept of meta-variables, which we
encountered in the previous section. The reason for doing things this way is so
that client applications do not need to have knowledge of how the files are
organised within a data cache, nor how those files are named and persisted within
the back-end data store.

The code fragment below illustrates how data files might be fetched for a series
of meta-variables, and then loaded into an Iris cubelist::

    >>> metavars = [umvar1, umvar2, umvar3]
    >>> dcache.fetch_files(metavars)
    >>> cubes = dcache.load_data(metavars)

.. note:: Afterburner applications do not have to use the existing data cache
   and data store classes. On occasions, it might be necessary for applications
   to interact with an existing, bespoke data store. In other situations, a
   suitable data cache class might not exist for a particular type of data, and
   the format of that data is sufficiently rare or obscure as to not warrant
   developing a general-purpose data cache class.

Additional guidance regarding use of the data cache and data store classes can be
found in the :doc:`datacaches` chapter of this guide.

Filename Provider Classes
-------------------------

The ``afterburner.filename_providers`` module contains model-specific classes
which may be used to generate the names of data files that would be output by
a climate model for a specified list of meta-variables (as described above).

Classes currently exist for generating the names of files produced by the UM
and NEMO models (actually by post-processing scripts in the latter case). Classes
for additional climate models will be written as the need arises.

At present the filename provider classes are mainly used by data caching code to
determine which files need to be retrieved from an underlying data store (such
as MASS) in order to make data available for processing applications.

Processor Classes
-----------------

Processor classes are used to encapsulate self-contained, and typically low-level,
data processing functionality. They represent the 'atomic' building blocks from
which more complex applications can be constructed.

Processor classes are expected to span a broad range of functional areas. Example
classes might implement the following types of tasks and operations:

* Calculation of a bespoke diagnostic from one or more existing model diagnostics.
* Calculation of a statistical measure (mean, min, max, etc.) from a model diagnostic.
* Generation of a plot (or other graphic) from a model diagnostic.
* Calculation and generation of plots to monitor some measure of model performance.
* Convert a series of data files to a new data format.

All processor classes are expected to inherit from the ``afterburner.processors.AbstractProcessor``
base class. That class defines the standard interface that all concrete classes
must implement.

Additional guidance regarding the development of Afterburner processor classes
is provided in the :doc:`processors` section of the Developers' Guide. An index
page summarising the current Afterburner processor classes can be found
:doc:`here </processors>`. 

Application (App) Classes
-------------------------

Afterburner applications - 'apps' for short - represent the principal user-facing
portion of the Afterburner framework. Afterburner apps perform some logically
coherent scientific data processing activity. They might range from the trivially
simple to the fiendishly complicated.

Whichever is the case, the Afterburner framework hopefully provides a selection
of software tools that will make it quicker to develop and test applications
that are based upon common and centrally-maintained code building blocks.

All Afterburner applications should inherit from the ``afterburner.apps.AbstractApp``
base class. As well as defining the standard interface which all concrete app
classes must implement, the base class also provides common functionality that
is likely to be useful for all apps, e.g parsing of command line arguments,
handling of log messages, reading app configuration files, and so on.

In many cases an Afterburner app will be conceptually equivalent to a Rose app.
As such it will usually be desirable, if not essential, to provide a sample
Rose suite which users can refer to (or perhaps copy) in order to configure and
run the application.

Additional guidance regarding the development of Afterburner app classes
is provided in the :doc:`apps` section of the Developers' Guide.

Application Configuration Classes
---------------------------------

The Afterburner framework provides a couple of classes for working with software
configuration information.

The ``afterburner.config.ConfigProvider`` class may be used to query the location
of the main directory and file artifacts comprising the Afterburner software
suite. If your application needed to determine, for example, the default location
of the template directory and the user's configuration file, then the following
code would provide this information::

    >>> from afterburner.config import ConfigProvider
    >>> cfg = ConfigProvider()
    >>> cfg.template_dir
    '/usr/local/afterburner/v1.2.3/etc/templates'
    >>> cfg.user_config_file
    '/home/users/jrluser/.config/afterburner/afterburner.conf'

(Note: The path names shown above are made-up examples. You will obtain different
results specific to your particular runtime environment.)

The ``afterburner.app_config.AppConfig`` class provides a lightweight wrapper
around Rose's ``rose.config.ConfigNode`` class. It provides convenience methods
for retrieving configuration properties of known types (int, float, bool, etc.),
and for iterating over namelist-based configuration sections.

It is envisaged that most Afterburner applications will obtain configuration
information from text files written using Rose's custom INI format. Accordingly,
the ``AppConfig`` class is designed to simplify reading configuration properties
from such files.

Refer to the :doc:`/sys_config` chapter for more information about configuring
Afterburner software.

Utility Classes and Functions
-----------------------------

The Afterburner framework includes a number of handy utility classes and functions,
most of which are to found within the modules collected together under the
``afterburner.utils`` package. The current version of the Afterburner software
includes utility code in connection with the following functional areas:

* manipulating Iris cubes (:doc:`cubeutils </apidoc/afterburner.utils.cubeutils>` module)
* creating and manipulating date and time objects (:doc:`dateutils </apidoc/afterburner.utils.dateutils>` module)
* working with files (:doc:`fileutils </apidoc/afterburner.utils.fileutils>` module)
* manipulating text strings (:doc:`textutils </apidoc/afterburner.utils.textutils>` module)

This list is likely to grow as the Afterburner framework evolves.
