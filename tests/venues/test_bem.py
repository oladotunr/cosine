"""
# 
# 10/09/2018
# BlockEx - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from unittest import TestCase
from cosine.core.config import Config, Section
from cosine.core.context import CosineCoreContext
from cosine.core.proc_workers import CosineProcWorkers
from cosine.venues.bem import BlockExMarketsVenue


# MODULE CLASSES
class BlockExMarketsVenueTest(TestCase):

    def _new_venue(self):
        self.cfg = Config(
            venues=Section(
                bem=Section(
                    Username="polkadot",
                    Password="raptor",
                    APIDomain="https://api-tst.blockex.com/",
                    APIID="7c11fb8e-f744-47ee-aec2-9da5eb83ad84",
                    ConnectSignalR=True
                )
            ),
            system=Section(
                network=Section(
                    ssl=Section(
                        CertFile="/usr/local/etc/openssl/cert.pem"
                    )
                )
            )
        )
        self.pool = CosineProcWorkers(cfg=self.cfg)
        self.venue = BlockExMarketsVenue(
            worker_pool=self.pool,
            cxt=CosineCoreContext(),
            **self.cfg.venues.bem.asdict()
        )
        self.assertIsInstance(self.venue, BlockExMarketsVenue)


    def test_setup(self):
        self._new_venue()
        self.venue.setup()
        self.venue.teardown()


    def test_update(self):
        self._new_venue()
        self.venue.setup()
        self.venue.update()
        self.venue.teardown()


