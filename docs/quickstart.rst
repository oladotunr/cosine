Quickstart
==========

.. contents:: :local:

.. NOTE:: All code starting with a ``$`` is meant to run on your terminal.
    All code starting with a ``>>>`` is meant to run in a python interpreter,
    like `ipython <https://pypi.org/project/ipython/>`_.

Installation
------------

Cosine can be installed (preferably in a :ref:`virtualenv <setup_environment>`)
using ``pip`` as follows:

.. code-block:: shell

   $ pip install cosine-crypto


.. NOTE:: If you run into problems during installation, you might have a
    broken environment. See the troubleshooting guide to :ref:`setup_environment`.


Installation from source can be done from the root of the project with the
following command.

.. code-block:: shell

   $ pip install .

Using Cosine
------------

Once cosine has been installed, it's relatively easy to get setup to run it. Before that however, it's best to get
familiar with the architecture and more information can be found via the :doc:`overview` section of this documentation.

Once you're ready you can begin by implementing code similar to the following.

.. code-block:: python

   import argparse
   from cosine.core.algo import CosineAlgo


   def main():
       parser = argparse.ArgumentParser(description='Cosine Algo')
       parser.add_argument("-c", "--config",
                        help="Config YAML file required to setup the algo.")
       parser.add_argument("-e", "--env", choices=['DEV', 'TST', 'PRD'],
                        help="The execution environment.")
       parser.add_argument("-a", "--appname", default='Cosine Algo',
                        help="The name of the application.")
       parser.add_argument("-lf", "--logfile",
                        help="The name of the log file. Do not change this unless you know what you're doing.")
       parser.add_argument("-lv", "--loglevel",
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL', 'CRITICAL'],
                        help="Log level.")

       parser.print_help()
       args = parser.parse_args()

       app = CosineAlgo(cmdline_args=args)
       app.run()


   if __name__ == "__main__":
       main()

In the above code we perform the following actions:

#. First we import the `argparse <https://docs.python.org/3/library/argparse.html>`_ module to capture the required command line arguments Cosine cares about.
#. Then we import the ``CosineAlgo`` class, the main application class we need to instantiate to launch the algo.
#. In our main function we construct the argument list for consumption and parse it.
#. We then instantiate the ``CosineAlgo`` class into an object, which we then proceed to run to start the algo execution.

Command Line Arguments
----------------------

Here's the set of command line arguments that cosine looks for.

.. NOTE:: Cosine will by default check the provided ``cmdline_args`` keyword parameter of the ``CosineAlgo``
   constructor, for the required parameters and if not provided, fall back to the environment variable equivalent
   and then a default if none has been provided.

+------------------------+-----------------------+---------------------------------------------+-------+
| Command Line Argument  | Environment Variable  | Description                                 | Type  |
+========================+=======================+=============================================+=======+
| --config               | COSINE_CFG            | The path to the configuration file required | str   |
+------------------------+-----------------------+---------------------------------------------+-------+
| --appname              | COSINE_APP            | The name of the application                 | str   |
+------------------------+-----------------------+---------------------------------------------+-------+
| --env                  | COSINE_ENV            | The execution environment                   | str   |
+------------------------+-----------------------+---------------------------------------------+-------+
| --logfile              | COSINE_LOGFILE        | The path to the file to provide logging into| str   |
+------------------------+-----------------------+---------------------------------------------+-------+
| --loglevel             | COSINE_LOGLVL         | The filtered log level                      | str   |
+------------------------+-----------------------+---------------------------------------------+-------+

Configuring The Algo
--------------------

Cosine provides a comprehensive set of configurations for setting up and customising the algo. See the
:doc:`configuration` section for more details.

Custom Strategies
-----------------

Cosine supports the implementation and configuration of custom strategies for use with the algo framework. See the
:doc:`strategies` section for more details.

Custom Connectivity
-------------------

Cosine supports the implementation and configuration of connectivity to a multiple custom venues for execution, as well
as to multiple pricing feeds concurrently. See the :doc:`venues` section to learn more about building and using custom
exchange connectivity. Also check out the :doc:`pricingfeeds` section to learn more about building consuming custom
feeds to new pricing sources.

