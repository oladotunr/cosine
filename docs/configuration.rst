Configuration Management
========================

.. contents:: :local:

Configuration Loading
---------------------

Cosine uses YAML-based configuration to configure the setup of the algo framework. This includes things like pricing
feeds to initialise, the strategy to run, available venues to connect to and more. The configuration file must be provided
upfront and you can inform Cosine how to locate it in one of three ways:

* Direct (Cosine will look for a config file path in the ``config`` attribute of the ``cmdline_args`` dict argument passed to the ``CosineAlgo`` constructor)
* Environment (Cosine with otherwise check for the path in the ``COSINE_CFG`` environment variable if it exists)
* Implicit (Cosine will otherwise look for a file called ``config.yaml`` in the current working directory of the executed algo)

Configurable Attributes
-----------------------

Here's the full set of available configurations (complete with group headings per the YAML structure):

.. code-block:: yaml

   # all system-level configurations
   system:
       EventLoop: <val>                         # the event loop configuration mode, "feed" or "timer"
       EventLoopThrottle: <val>                 # event loop rate limit in seconds
       network:                                 # general network level configuration
           ssl:                                 # SSL related configuration
               CertFile: <val>                  # [optional] path to the SSL certificate authority cert file

   # general order worker related configurations
   orders:
       ActiveDepth: <val>                       # active depth on each side of book respectively (bid and ask)

   # set of configured venues (with their contextual configurations) to initialise for use with the order workers
   venues:
       cosine.venues.bem:                       # [optional] the fully qualified module path of the BlockExMarketsVenue (CosineBaseVenue derivative) class to load + configure
           Username: <val>                      # [venue-specific] the username of the trader account to authenticate against
           Password: <val>                      # [venue-specific] the password of the trader account to authenticate against
           APIDomain: <val>                     # [venue-specific] the top-level domain of the BEM venue
           APIID: <val>                         # [venue-specific] the dedicated APIID for the BEM venue
           ConnectSignalR: <val>                # [venue-specific] tells BEM whether to subscribe to the async signalR feed or not, "true" or "false"

   # the set of configured instruments to work markets in. Order workers will be created against each of these on the relevant venue(s)
   instruments:
   - "XTN/EUR"
   - "RCC/EUR"
   - "ETH4/EUR"

   # the set of configured pricing feeds to connect and subscribe to for market data consumption
   feeds:
       cosine.pricing.cryptocompare:            # [optional] the fully qualified module path of the CryptoCompareSocketIOFeed (CosineBaseFeed derivative) class to load + configure
           type: <val>                          # [feed-specific] the type of connection ("stream" only for this feed)
           endpoint: <val>                      # [feed-specific] the websockets/socket.io endpoint hostname to connect to
           port: <val>                          # [feed-specific] the port to connect to
           framework: <val>                     # [feed-specific] the framework for connectivity
           triangulator: <val>                  # [feed-specific] the REST endpoint to use to pull triangulation info for implying pricing for pairs with no direct subscription
           triangulator_throttle: <val>         # [feed-specific] the rate limit for running triangulation queries in seconds
           instruments:                         # the set of instruments to subscribe to
               "XTN/EUR":
                   Ticker: "BTC"                # ticker re-mapping for the base/top-level currency
               "RCC/EUR":
                   BaseCCY: "ETH"               # [optional] forces the feed to subscribe to RCC/ETH and then run triangulation on each price tick to calculate the RCC/EUR price
               "ETH4/EUR":
                   Ticker: "ETH"
   feed:
       Primary: cosine.pricing.cryptocompare

   pricers:
       Default: cosine.pricing.pricers.nullpricer
       settings:
           cosine.pricing.pricers.nullpricer:
               nop: nop

   strategy:
       type: cosine.strategies.noddy_floater
       settings:
           cosine.strategies.noddy_floater:
               Spread: 0.20
               MaxSpread: 0.5
               instrument_settings:
                   "XTN/EUR":
                       MinVol: 5
                       MaxVol: 10
                   "RCC/EUR":
                       MinVol: 5
                       MaxVol: 10
                   "ETH4/EUR":
                       MinVol: 5
                       MaxVol: 10

See above.