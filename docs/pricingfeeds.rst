Pricing Feeds
=============

.. contents:: :local:

Structure
---------

Cosine's pricing feeds all inherit from the ``CosineBaseFeed`` class and are responsible for providing all market data
consumption connectivty for the algo framework. Feeds are designed to be modular, where an algo can be configured to
connect to multiple feed sources simultaneously to obtain pricing for different instruments, or even for the same ones
but providing different data sets perhaps. Feeds are setup via the configuration file (See the :doc:`configuration` section
for more details) with all of their custom feed-specific attributes defined. These config attributes will be automatically set as
member attributes on the class instance on construction via the ``CosineAlgo``. Once a feed instance has been created, the
``CosineAlgo`` calls the feed's ``setup()`` method, which first initialises the pricing cache based on the set of configured
instruments, and then it will attempt to initialise the feed connection. If the ``system.EventLoop: feed`` configuration
is set and the specific feed instance is the primary feed, then the feed will run inline in the current process.
If not then the feed will run in a separate worker process managed by the ``CosineProcWorkers`` worker pool.

The ``CryptoCompareSocketIOFeed`` has been provided as an initial pricing feed implementation, which supports websockets based
pricing updates, with REST based pricing triangulation on pricing ticks, for price triangulation of instrument pairs where required
(i.e. if there is no direct pricing feed provided for this pair by `cryptocompare.com <https://www.cryptocompare.com>`_).
Feel free to check out the code for this feed implementation to familiarise yourself with the structure.

Developing A Custom Feed
------------------------

Custom feeds can be implemented easily, by inheriting from ``CosineBaseFeed`` and overriding the ``run()`` method.
The ``CryptoCompareSocketIOFeed`` provides an example implementation of how to achieve this.

Once your custom feed has been written and tested, you can leverage it in one of two ways:

* Submit your feed implementation to the `main open source repository <https://github.com/oladotunr/cosine>`_ as a pull request (recommended if applicable)
* Or leverage it locally as part of your algo implementation.

To achieve the latter is fairly simple. Assuming you have an algo project setup to use cosine (an example project has been provided
`here <https://github.com/oladotunr/cosine-algo>`_), you can simply configure the module path in the configuration file to
allow the native import mechanics to load your custom module locally at run-time.

For example, let's assume we have a custom feed called ``MyCustomFeed`` in the local project (at the path ``/myproject/pricing/mycustomfeed.py``).
We can setup the following in the configuration file (at ``/myproject/config.yaml``):

.. code-block:: yaml

   ...

   feeds:
       pricing.mycustomfeed:
           type: stream
           endpoint: wss://mycustomfeed.io
           port: 443
           framework: websockets
           triangulator: https://api.mycustomfeed.io/priceinfo
           triangulator_throttle: 0.5
           instruments:
               "XTN/EUR":
                   Ticker: "BTC"
               "RCC/EUR":
                   BaseCCY: "ETH"
               "ETH4/EUR":
                   Ticker: "ETH"
   ...

Which should inform ``CosineAlgo`` to load the module, instantiate the feed and initialise it for use.
