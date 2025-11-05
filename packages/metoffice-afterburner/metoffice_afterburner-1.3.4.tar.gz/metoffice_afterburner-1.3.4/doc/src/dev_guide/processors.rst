Writing Processor Classes
=========================

As mentioned in the :doc:`overview` section, processor classes are designed to
encapsulate self-contained, and typically low-level, data processing functionality.
As such they represent the 'atomic' building blocks from which more complex
scientific applications can be constructed.

An index page summarising the current Afterburner processor classes can be found
:doc:`here </processors>`. 

Naming of Processor Modules and Classes
---------------------------------------

New processor classes should be implemented within dedicated modules under the
``afterburner.processors`` package, or one of its sub-packages. Whenever practicable,
the module name should be a lower-case translation, possibly with recognisable
abbreviations, of the processor class name (which should always be in TitleCase).

Thus, taking the example of the :doc:`ExampleProcessor </apidoc/afterburner.processors.example_proc>`
class in the Afterburner code base, the module containing this class is named
``example_proc.py``, 'proc' being an acceptable short-hand for 'processor'.

It's not mandatory to include the term 'Processor' in the class name. Sometimes
the class name will be sufficiently self-explanatory without it, or sufficiently
long as to warrant dropping it from the name.

In the case of diagnostic-style processor classes, the class name should normally
be just the diagnostic name. For example, a processor class for generating a
net heat flux diagnostic might be called ``NetHeatFlux``, and be implemented in
a module named ``net_heat_flux.py``. (We'll have more to say about diagnostic-type
processors later on.)

.. note:: As per standard object-oriented coding practice, class names should be
   **nouns** rather than verbs. Hence ``PlotGenerator``, not ``GeneratePlots``.

Processor classes should normally be referenced using their **full class path**,
e.g. ``afterburner.processors.example_proc.ExampleProcessor``. If client code --
be that other library code or an end-user application -- expects to find the
class name in the ``afterburner.processors`` namespace, then it will be necessary
to add a suitable import statement to the ``__init__`` module of that package.

In a similar vein, the names of diagnostic processor classes are usually imported
into the ``afterburner.processors.diags`` namespace, as illustrated in the code
snippet below (taken from that package's ``__init__`` module)::

    from .atmos.nao_index import NaoIndex
    from .atmos.toa_radiation_balance import ToaRadiationBalance
    ...

Setting things up this way means that client code/apps that work with diagnostic
processor classes can access them by name alone from a single namespace. A caveat
of course is that the names of diagnostic processor classes must be unique across
all of the modules that occur below the ``afterburner.processors.diags`` package.

Finally, it is quite acceptable -- and often advantageous -- to implement a small
collection of closely-related processor classes within a single module, so long
as the overall line count in the module isn't excessive (1500 lines of code is
the currently recommended maximum).

Class Design Basics
-------------------

All processor classes should inherit from the :doc:`AbstractProcessor </apidoc/afterburner.processors>`
base class. This class, which can be found in the ``afterburner.processors.__init__``
module, defines the standard interface that all concrete subclasses must implement
as a minimum.

The ``__init__()`` method of the ``AbstractProcessor`` base class currently does little
more than define a logger object which can be used by concrete subclasses to send
messages to the user's terminal or, in the case of Rose, to its standard log files.
As the Afterburner framework evolves, however, it is anticipated that the base class
will provide additional capabilities.

Most concrete subclasses will want to invoke the base class initialisation code
early on within the ``__init__()`` method. The ExampleProcessor class does just
that::

    def __init__(self, cubelist):
        super(ExampleProcessor, self).__init__()
        self.cubelist = cubelist
        ...

Thereafter your processor subclass can execute whatever additional initialisation
code it requires.

.. note:: Many Afterburner processor classes follow the convention of taking an
   Iris cubelist as the primary input argument (to the ``run()`` method), and
   returning a new cubelist as a result of the processor being executed. While
   this design paradigm is likely to be valid - and indeed effective - for many
   processor classes, it is **not mandated**. In principle, processor classes may
   be written to take whatever inputs and yield whatever outputs are needed to
   get the task in question done. The next section explores this topic in more
   detail.

Initialisation Arguments vs Runtime Arguments
---------------------------------------------

Most processor classes will require a combination of initialisation arguments
and runtime arguments. As might be expected, the former are used when the processor
object is initialised, the latter when it is executed.

Initialisation arguments must of course be passed to the ``__init__()`` method.
Runtime arguments, on the other hand, can be passed either to the ``__init__()``
method, where they would be stored for later use, or else to the ``run()`` method,
where they would be used more or less immediately.

As we saw in the previous section, the ExampleProcessor class expects a cubelist
argument to be passed to its initialisation method. The cubelist then gets used
when the processor is run. An alternative design would move the cubelist argument
to the ``run()`` method. In this case the same processor object could be run
multiple times with different cubelists, thus::

    >>> proc = ExampleProcessor()
    >>> result1 = proc.run(cubelist1)
    >>> result2 = proc.run(cubelist2)
    >>> ...

The choice of which approach to take will depend on the nature and purpose of the
processor class in question. If a processor is designed for one-time use, then
either approach should suffice. In the case of a processor designed to be invoked
multiple times, the second approach is likely to be advantageous (so long as any
initialisation arguments are applicable to all invocations of the processor).

In the particular case of diagnostic processor classes, the recommended convention
is to employ the second approach, i.e. define the ``__init__()`` method to accept
any arguments that configure the processor, and then define the ``run()`` method to
accept a cubelist to operate on. The skeleton processor class shown below illustrates
this approach::

    class MyDiagnostic(AbstractProcessor):

        def __init__(self, volume=11, result_metadata=None, **kwargs):
            super(MyDiagnostic, self).__init__(**kwargs)
            self.volume = volume
            self.result_metadata = result_metadata
            ...

        def run(self, cubes, **kwargs):
            # apply processing as needed to the input cubelist
            ...

            # return a new cubelist
            return cubelist

Mandatory processor settings should appear in the init method signature either
as positional arguments or as explicit keyword arguments; the latter method is
preferred since it tends to be more robust and more flexible.

Both the init method and the run method should include the ``**kwargs`` argument,
even if a particular processor class doesn't require it (because it serves to
silently scoop up any keyword arguments that the method is not expecting). The
``kwargs`` dictionary object is typically useful, however, for passing in and
handling optional and/or less frequently used processor settings.

The run method should *always* accept an Iris cubelist as the first positional
argument. For some processor classes the cubelist might only be expected to contain
a single cube, although the case of a multi-item cubelist should always be handled.
Generally this means extracting the single cube of interest.

If a processor class always expects to operate on a single cube then an acceptable
implementation variation is to test for a single cube as input to the run method,
and then proceed as though a length-1 cubelist was passed in. In this case the run
method must still work when a cubelist is passed in, and it must still return a
cubelist. If this implementation method is employed then it should be clearly
documented.

The run method will typically need to make use of instance attributes defined at
initialisation time (e.g. the volume attribute in the example above). Depending
on the anticipated use of the class, it may be desirable to support overriding of
one or more of these attributes at runtime. The ``**kwargs`` argument provides a
flexible way to do this. For example, one might override the volume attribute as
follows::

    def run(self, cubes, **kwargs):
        # check to see if the volume attribute has been overridden
        volume = kwargs.get('volume', self.volume)

        # apply processing as needed to the input cubelist
        ...

        # return a new cubelist
        return cubelist

Execution of Processor Objects
------------------------------

Once a processor object has been instantiated, it can be executed (run) in
either of two ways. By invoking it's ``run()`` method, or simply by calling the
object itself.

Explicitly invoking the object's ``run()`` method::

    >>> proc = NaoIndex(mslp_stashcode='m01s16i222')
    >>> result = proc.run(cubes)

Calling the processor object directly::

    >>> proc = NaoIndex(mslp_stashcode='m01s16i222')
    >>> result = proc(cubes)

The second technique is made possible because all processor classes inherit the
``__call__()`` method from the ``AbstractProcessor`` base class. (Behind the scenes
this method simply calls the ``run()`` method.)

The first technique is generally preferred since the explicit method call makes
it more obvious -- especially to subsequent code developers -- what's going on.

Organisation of Processors into Sub-Packages
--------------------------------------------

To avoid a large number of processor classes (or rather their host modules) being
created directly below the ``afterburner.processors`` package, it is recommended
that the modules are organised into suitably-named sub-packages.

In the case of diagnostic-type processors, the following hierarchy of sub-packages
is proposed (and, at the time of writing, partially realised)::

    processors/
      diags/
        atmos/                   # package for atmosphere diagnostics
          ...
        ocean/                   # package for ocean diagnostics
          ...
        land/                    # package for land diagnostics
          ...
        seaice/                  # package for sea-ice diagnostics
          ...
        landice/                 # package for land-ice diagnostics
          ...
        stats/                   # package for statistical-type diagnostics

If a processor class relates to two or more earth system models/realms then it
should be placed under the most appropriate sub-package. In some cases this might
involve a fairly arbitrary choice.

The stats sub-package is intended to be used for general-purpose statistical or
arithmetic/algebraic style diagnostics that are not specific to any particular
earth system realm.

It is hoped that the aforementioned scheme will make it easier to organise and
find diagnostic-type processor classes. New sub-packages should be created on an
as-needs basis.

Development Methodology for Processor Classes
---------------------------------------------

The preferred methodology, or workflow, for developing new Afterburner processor
classes, especially those used to generate model diagnostics, is described below.
Although it is focussed on the development of processor classes, most of the
procedures apply equally well to the development of other parts of the Afterburner
code base.

The steps described below assume that you are familiar with the Linux operating
system, with FCM command-line utilities, and with Python software development.

1. Create a new task ticket on the Afterburner Trac site
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is achieved by selecting the New Ticket option from the menubar of the
Afterburner `Trac site <https://code.metoffice.gov.uk/trac/afterburner>`_. On
the Create New Ticket form set the ticket type to 'task' and the component to
'Core Library (turbofan)'. If a suitable milestone is available (and appropriate)
then it can be selected, but this is not essential.  

2. Create an FCM development branch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using the ``fcm branch-create`` command, create a development branch from the
trunk of the Afterburner code repository. The ``-k`` option to the command should
be used to specify the ticket number created at step 1. Give the branch a suitably
meaningful name.

.. code-block:: console

   % fcm bc -k 1234 heat_stress_diagnostic fcm:turbofan-tr

After the branch has been created, add a comment to the Trac ticket and specify
the repository URL of the new branch. Set the ticket status to 'In Progress'.

3. Create a new module (if required) under the ``afterburner.processors`` package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your new class will be implemented within an existing module then the module's
file name and location obviously will be known. Otherwise you will need to decide,
or seek advice, as regards the name of the module and where best to create it.

As described in the first section of this guide, the module name will usually be
a tokenised, lower-case version of the processor class name, e.g. ``heat_stress.py``
for a processor named ``HeatStress``.

If the module is to be created within an existing sub-package below
``afterburner.processors`` -- the typical scenario -- then creating the module
file can be as easy as follows:

.. code-block:: console

   % cd lib/afterburner/processors/diags/atmos
   % touch heat_stress.py

If the module is to be created within a new sub-package then it will first be
necessary to create the sub-package directory and drop an ``__init__.py`` file
into it. The easiest way to do the latter task is to copy the equivalent file
from an existing sub-package. Don't forget to update the module's docstring if
you do this!

If you will be creating a diagnostic-type processor class then the module file
should be created within one of the sub-packages of the ``afterburner.processors.diags``
package (as listed earlier in this chapter). If none of the existing sub-packages
looks suitable, and you think you need to create a new one, then cross-check your
proposed new sub-package name with the Afterburner development team.

4. Implement the processor class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The quickest way to get started with implementing the actual processor class is
to copy the *skeleton* of an existing class. Usually it's desirable to copy over
the ``class`` declaration, and the statements that define the signature of the
``__init__`` and ``run`` methods. These should, of course, be modified immediately
to reflect the naming and purpose of your new processor class. 

It can also be convenient to copy over selected import statements, e.g. those at
the top of the file relating to Python 3 compatibility, and some of the modules
pertaining to Iris and Afterburner.

The bulk of the class will then need to be implemented so that it generates the
desired result (a cubelist) from the various input arguments. The code should
adhere to all the usual conventions and best practices regarding code construction.

It's not uncommon for processor classes to require private methods and/or functions.
If this is the case for your current development work then any such methods should
be made 'pseudo-private' by prefixing their names with a single underscore
character. That way they won't show up in Afterburner's auto-generated documentation.

.. note:: Don't forget to add user-friendly docstrings to your newly-created
   module(s) and class(es). You can build and review the Afterburner documentation
   set, including the API reference material, by running the build command
   ``python setup.py build_docs`` in the top-level directory of your branch.

If you are developing a diagnostic-type processor class then you should add a
corresponding import statement to the ``afterburner.processors.diags.__init__.py``
file. Continuing with the heat stress example used above::

    from .atmos.heat_stress import HeatStress

5. Implement a test suite
~~~~~~~~~~~~~~~~~~~~~~~~~

Any new processor class will be peer-reviewed (see below) before it can be merged
onto the trunk of the Afterburner repository. Barring exceptional circumstances,
that code review is unlikely to pass unless the branch includes a test module that
contains unit tests -- ideally several of them -- which exercise the new class.

Test files for modules that contain processor classes are organised under the
directory named ``tests/test_afterburner/test_processors``. The hierarchy of test
directories mirrors that used for the actual modules under the ``lib/afterburner/processors``
directory. The directory names use the ``test_`` prefix so that they get recognised
by automatic testing tools, such as pytest.

Designing and implementing unit tests is a large topic in its own right. If you
are unfamiliar with developing test code then please seek advice from colleagues,
study the numerous online resources, and examine (and plagiarise!) the existing
examples of test code in the Afterburner repository.

6. Get your code branch reviewed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before your new processor class(es) can be merged onto the trunk of the Afterburner
repository you will need to ask a suitably-experienced colleague to undertake a
code review of your branch. The reviewer should also examine the test suite and
documentation (you haven't forgotten about documentation, have you?).

If you can't find a friendly team colleague to carry out the code review then
contact the Afterburner development team. Note, however, that while that team can
undertake a code review, it might not necessarily have the expertise to assess
the *scientific validity* of the code.

7. Merge your branch onto the trunk
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once your branch has gone through one or more review-and-update cycles and has
been given the green light, it can be merged onto the Afterburner repository
trunk. In fact, this will normally be carried out by a member of the Afterburner
development team, so please contact that team when your branch is ready to merge.

8. Update and close the Trac ticket
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When your branch has been reviewed and merged onto the trunk, you should update
and mark as complete the Trac ticket created at step 1. The branch can then be
deleted using the ``fcm branch-delete`` command.

Well done! You can now tell your colleagues about your nifty new Afterburner
processor!
