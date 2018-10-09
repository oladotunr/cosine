Venues
======

.. contents:: :local:

Structure
---------

Cosine's venues all inherit from the ``CosineBaseVenue`` class and are responsible for providing all market exchange
connectivity, on-venue portfolio management and trade execution functionality for the algo framework. Venues are designed
to be modular, where an algo can be configured to connect to multiple venues simultaneously, and can work different sets
of instruments across different venues as part of a comprehensive, complex trading strategy. Venues are setup via the
configuration file (See the :doc:`configuration` section for more details) with all of their custom venue-specific
attributes defined. These config attributes will be automatically set as member attributes on the class instance on
construction via the ``CosineAlgo``. Once a venue instance has been created, the ``CosineAlgo`` calls the venue's ``setup()``
method, which is expected to initialise any connectivity to the remote exchange as well as retrieve and cache any
supported (or at least required) tradable assets/instruments at the destination exchange. The ``CosineBaseVenue`` base
class provides access to the ``CosineProcWorkers`` worker pool instance, that can be using during setup to instantiate
a worker for any asynchronous exchange connectivity required (if at all).

The ``BlockExMarketsVenue`` has been provided as an initial exchange venue integration, which supports trade execution
via REST (with asynchronous response updates), on-venue portfolio management & symbology retrieval. Feel free to check out
the code for this venue implementation to familiarise yourself with the structure.

Developing A Custom Venue
-------------------------

Custom venue implementations can be integrated easily, by inheriting from ``CosineBaseVenue`` and overriding the following methods:

* ``setup()``
* ``teardown()``
* ``update()`` (optional)
* ``on()`` (optional)
* ``get_instrument_defs``
* ``get_open_orders``
* ``get_inventory``
* ``new_order``
* ``cancel_order``
* ``cancel_all_orders``

Custom venues can implement support for these methods either synchronously or asynchronously depending on the anatomy of the remote
exchange connectivity API the venue implementation aims to abstract. The venue must inform the cosine framework of which configuration
it implements via overriding the ``is_async()`` property of the ``CosineBaseVenue`` class.

To implement asynchronous connectivity, the venue should define a process worker, which it initialises internally and runs as part of
``setup()`` workflow. The ``CosineProcEventWorker`` class provides a convenient worker implementation to inherit from, which handles
IPC via a shared event queue. The main process initiates requests directly on the main process and ``CosineProcEventWorker.EventSlot``
listeners are used to capture and handle responses asynchronously. The worker should connect to the exchange via some asynchronous
connectivity protocol and subscribe for the request responses. When the responses arrive they are pushed onto shared queue.
The main process will then leverage the ``update()`` method to drive event processing, which pulls queued events and handles them
via the handlers registered with each relevant ``CosineProcEventWorker.EventSlot``.

If an exchange connectivity implementation requires full asynchronous processing, i.e. requests need to be sent asynchronously, then
it maybe best to implement your own ``CosineProcWorker`` derivative, with your own ``CosineProcEventMgr`` equivalent implementation
to better facilitate the specific workflow required.

The ``BlockExMarketsVenue`` provides an example implementation of how to implement a ``CosineBaseVenue``, complete with asynchronous
workflow, via the ``BlockExMarketsSignalRWorker`` implementation.

Once your custom venue has been written and tested, you can leverage it in one of two ways:

* Submit your venue implementation to the `main open source repository <https://github.com/oladotunr/cosine>`_ as a pull request (recommended if applicable)
* Or leverage it locally as part of your algo implementation.

To achieve the latter is fairly simple. Assuming you have an algo project setup to use cosine (an example project has been provided
`here <https://github.com/oladotunr/cosine-algo>`_), you can simply configure the module path in the configuration file to
allow the native import mechanics to load your custom module locally at run-time.

For example, let's assume we have a custom venue called ``MyCustomVenue`` in the local project (at the path ``/myproject/venues/mycustomvenue.py``).
We can setup the following in the configuration file (at ``/myproject/config.yaml``):

.. code-block:: yaml

   ...

   venues:
       venues.mycustomvenue:
           Username: trader101324
           Password: !example123456!
           APIDomain: https://api.exchange-venue.io
           ... <venue specific configs> ...
   ...

Which should inform ``CosineAlgo`` to load the module, instantiate the venue and initialise it for use.
