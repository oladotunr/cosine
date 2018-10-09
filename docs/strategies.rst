Strategies
==========

.. contents:: :local:

Structure
---------

Cosine's strategies represent the core business logic drivers for each algo and leverage the rest of the framework components
(venues, orderworkers, feeds, pricers) to achieve their goals. Inheriting from the ``CosineBaseStrategy`` class, strategies
are designed to run the main business logic on an event loop. This can be configured to run on every tick (or throttled) of
a specific pricing feed or on a simple timer. Strategies are setup via the configuration file (See the :doc:`configuration`
section for more details) with all of their custom strategy-specific attributes defined. These config attributes will be
automatically set as member attributes on the class instance on construction via the ``CosineAlgo``. Once a strategy instance
has been created, the ``CosineAlgo`` calls the strategy's ``setup()`` method, which is expected to initialise any logical
setup required for operation. The ``CosineBaseStrategy`` base class provides access to all configured feeds, orderworkers
and pricers to use as part of the strategy logical flow, mostly via the ``CosineCoreContext`` passed to it on construction.

The ``NoddyFloaterStrategy`` has been provided as an initial strategy implementation (limited), which supports simple price
consumption, pricer pipelining as well as quote updating based on the generated target prices. See the :doc:`noddyfloater`
section for more details.

Running Multiple Strategies
---------------------------

The ``CosineAlgo`` is designed to run a single strategy instance within the main algo process. It's possible to run multiple
strategies within a single algo process, however care must be taken to measure and assess the performance considerations of
this, specifically where a lot of heavy lifting is done. Since all strategies would run their ``update()`` methods serially
on each tick of the main event loop, significant latency in update processing may cause undesirable behaviour in the algo.
For simple strategies, a ``CosineMultiStrategy`` class has been provided to allow multiple strategies to be run under it.

To configure the ``CosineMultiStrategy`` you can setup the ``config.yaml`` as follows:

.. code-block:: yaml

   ...
   strategy:
       type: cosine.strategies.multi_strategy
       settings:
           cosine.strategies.multi_strategy:
               strategies:
               - strategies.localstrategya
               - strategies.localstrategyb
           strategies.localstrategya:
               ... <strategy specific configs> ...
           strategies.localstrategyb:
               ... <strategy specific configs> ...
   ...


Developing A Custom Strategy
----------------------------

Custom strategy implementations can be integrated easily, by inheriting from ``CosineBaseStrategy`` and overriding the following methods:

* ``setup()`` (optional)
* ``teardown()`` (optional)
* ``update()``

A suite of convenience methods have also been provided in the ``CosineBaseStrategy`` class to streamline strategy logic as
needed. Strategies have direct access to all orderworkers, which in-turn are configured and grouped by connected venue. In this
way a single strategy can generate quotes ansd work orders across either a single market or across multiple markets simultaneously
as required by the business logic implemented within it. In a similar vein, strategies have full access to all configured
feeds and can source instrument pricing from one or more feeds as desired.

Once your custom strategy has been written and tested, you can leverage it in one of two ways:

* Submit your strategy implementation to the `main open source repository <https://github.com/oladotunr/cosine>`_ as a pull request (not recommended unless widely useful)
* Or leverage it locally as part of your algo implementation. (recommended)

To achieve the latter is fairly simple. Assuming you have an algo project setup to use cosine (an example project has been provided
`here <https://github.com/oladotunr/cosine-algo>`_), you can simply configure the module path in the configuration file to
allow the native import mechanics to load your custom module locally at run-time.

For example, let's assume we have a custom strategy called ``MyCustomStrategy`` in the local project (at the path ``/myproject/strategies/mycustomstrategy.py``).
We can setup the following in the configuration file (at ``/myproject/config.yaml``):

.. code-block:: yaml

   ...
   strategy:
       type: strategies.mycustomstrategy
       settings:
           strategies.mycustomstrategy:
               ... <strategy specific configs> ...
   ...

Which should inform ``CosineAlgo`` to load the module, instantiate the strategy and initialise it for use.
