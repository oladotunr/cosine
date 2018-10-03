Overview
========

.. contents:: :local:

Architecture
------------

Cosine was designed with both scalability and modularity in mind. At The top level is the ``CosineAlgo`` a class
which represents top level application construct. Within this are several constructs providing varying layers of
functionality, of which all of that are provided to the core strategy (a derivative of ``CosineBaseStrategy``) for
orchestration of all trading activities. Here's the list of constructs provided:

* ``CosineBaseFeed`` - The base class representing an interface for subscribing to market pricing information, typically from an external data source. Current the ``CryptoCompareSocketIOFeed`` has been provided to support pricing feeds across a range of instruments.
* ``CosinePairInstrument`` - The class representing a single tradable instrument, representing an asset pair. Or more specifically, a tradable asset, denominated in a secondary quote currency asset type. Both assets derive from ``CosineTradableAsset`` base type.
* ``CosineBaseVenue`` - The base class representing an interface for connectivity to a market execution venue. It's expected that such venues would provide a range of markets for trading a set of instruments, as well as providing on-exchange account management of trader balances of inventory. This interface should expose all required access to this functionality and the interface is designed to support either synchronous (blocking) exchange interaction or asynchronous (non-blocking).
* ``CosineBasePricer`` - The base class representing an interface to an internal or external source of pricing. Cosine is designed to support sophisticated pricing engines that may consume a wide variety of pricing sources and leverage statistical pricing models to determine theoretical pricing for a given market, or provide pricing leans as a means of integrated risk management within execution of the algo.
* ``CosineOrderWorker`` - The class which provides order-working management (e.g. place resting orders, amend orders based on pricing changes and cancel orders) for a specified instrument, against a specified venue.

Event Loop
----------

Cosine is designed to run via an internal event loop. The main process which runs the ``CosineAlgo`` instance, kicks off
the set of configured venues and feeds (which may individually create separate processes) as well as creating the
strategy. At which point the algo can run in one of two configurations: ``system.EventLoop: feed`` which uses the
``feed.Primary:`` configuration to determine which configured and initialised ``CosineBaseFeed`` to use to drive the
event loop. Alternatively the ``system.EventLoop: timer`` configurations sets up a periodic timer which kicks the event
loop on a regular interval.

.. code-block:: python

   # in CosineAlgo
   def run(self):

       # setup the algo...
       self.setup()

       # initiate the update loop...
       if self._cfg.system.EventLoop == "feed":

           # here we tick the strategy every time the primary pricing feed ticks...
           self._run_on_primary_feed()
       else:
           # here we tick the strategy every time the timer ticks...
           self._run_on_timer()

       # clean up the algo and exit...
       return self.teardown()


If the ``system.EventLoop: feed`` is selected, whenever a pricing update comes in from the pricing feed, the pricing
cache is updated (see the :doc:`pricingfeeds` section for more details) and the ``CosineAlgo`` instance's ``_tick_main()``
method is called. This call is rate limited by the ``debounce`` utility decorator, based on the ``system.EventLoopThrottle:``
configuration value, which represents a minimal inter-arrival rate in seconds.

The ``_tick_main()`` represents the main workhouse of the algo, which processing the following business logic in-order:

* Update any configured auxiliary (i.e. non-primary) pricing feeds to build an up-to-date set of pricing caches (feeds subscribe to message updates which are queued and processed on the main process)
* Update all the configured venues (if any have asynchronous components, they will queue inbound events and these update calls will consume the queued events and update order worker states accordingly)
* Update the strategy (this will process any strategy level business logic, see the :doc:`strategies` section for more details)

Multiprocessing
---------------

Cosine is designed to operate within a multi-process setup. The core ``CosineAlgo`` provides a framework class called
``CosineProcWorkers``, which manages and orchestrates all processes for running the various services required by the
algo framework, such as pricing, feeds, exchange connectivity and strategy logic. For example, the ``BlockExMarketsVenue``
(a derived class of ``CosineBaseVenue``) provides two main connectivity protocols: a set of synchronous requests to
control order execution and to query order, market, instrument and pricing information. As well as an asynchronous event
feed for subscribing to pricing changes order state updates and executions, to publish events that are queued and picked
up by the main process for reactive processing (i.e. order-working). In-order to achieve this, the ``BlockExMarketsVenue``
implements a ``CosineProcWorker`` derived class (``BlockExMarketsSignalRWorker``), which handles the blocking
subscription for async updates in a separate process, and events that come in are republished into an event queue for
processing on the main process by the initiating ``CosineOrderWorker``.

The ``CosineProcWorkers`` instance can be leveraged by any custom strategy, feed or connectivity layer module, that
requires processing to be done in a separate process, so as to not block the main process event loop. This provides
streamlined execution of the algo, and was designed this way to lay the foundations for maximising performance (e.g.
for HFT algo development), alleviating the costs around frequent context switching as well as the risks of thread/process
starvation inherent with a cooperative multi-threading (aka green threads or co-routines - i.e. `Asyncio <https://docs.python.org/3/library/asyncio.html>`_
concurrency) approach. This also alleviates the performance problems inherent in python multithreading due to the
`Global Interpreter Lock (or GIL) <https://wiki.python.org/moin/GlobalInterpreterLock>`_.

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

