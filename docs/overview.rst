Overview
========

.. contents:: :local:

Architecture
------------

Cosine was designed with both scalability and modularity in mind. At The top level is the ``CosineAlgo`` a class
which represents top level application construct. Within this are several constructs providing varying layers of
functionality, of which all of that are provided to the core strategy (a derivative of ``CosineBaseStrategy``) for
orchestration of all trading activities. Here's the list of constructs provided:

* ``CosineBaseFeed`` - The base class representing an interface for subscribing to market pricing information, typically from an external data source.
* ``CosinePairInstrument`` - The class representing a single tradable instrument, representing an asset pair. Or more specifically, a tradeable asset, denominated in a secondary quote currency asset type. Both assets derive from ``CosineTradableAsset`` base type.
* ``CosineBaseVenue`` - The base class representing an interface for connectivity to a market execution venue. It's expected that such venues would provide a range of markets for trading a set of instruments, as well as providing on-exchange account management of trader balances of inventory. This interface should expose all required access to this functionality and the interface is designed to support either synchronous (blocking) exchange interaction or asynchronous (non-blocking).
* ``CosineBasePricer`` - The base class representing an interface to an internal or external source of pricing. Cosine is designed to support sophisticated pricing engines that may consume a wide variety of pricing sources and leverage statistical pricing models to determine theoretical pricing for a given market, or provide pricing leans as a means of integrated risk management within execution of the algo.

