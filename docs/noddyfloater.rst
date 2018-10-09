Strategy: Noddy Floater
=======================

.. contents:: :local:

Structure
---------

Cosine's ``NoddyFloaterStrategy`` strategy provides a simple limited-functionality example use-case for how to structure and write
your own custom strategies in the cosine algo framework. See the :doc:`strategies` section for more details in general
around strategies, how they work, how they're shaped and how then can be developed and integrated.

You can also checkout the example algo project `here <https://github.com/oladotunr/cosine-algo>`_ to see how to configure
and run the ``NoddyFloaterStrategy``.

Core Logic
----------

Noddy floater's core logic is fairly simple and follows the following algorithmic flow on every price tick:

* Retrieve the set of orderworkers for the target venue (BEM)
* Extract the set of instruments associated with each order worker
* Capture the set of cached pricing snapshots for each instrument
* Run the pricer pipeline across all pricing snapshots (to embellish them)
* Generate a set of quotes from the final pricing data
* Push the quotes to the orderworkers to update all order quotes on the markets

Quoting is basically constructed as a butterfly spread around the mid-price for each market, roughly 20% (configurable)
away from the mid-price on either side. Quotes are configured to linearly scale up to a maximum spread price with some
marginal stochastic variance on each price step. Volume is similarly calculated out based on a linear interpolation
between minimum & maximum quote sizes per price level.

This is a very simple implementation that does nothing fancy but proves the basic building blocks for developers to build
more sophisticated trading strategies on the cosine framework.
