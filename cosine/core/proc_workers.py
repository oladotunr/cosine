"""
# 
# 15/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
import os
import multiprocessing as mp

from queue import Empty as EmptyException
from multiprocessing import Queue
from cosine.core.config import FieldSet
from cosine.core.utils import CosineEventSlot


# MODULE CLASSES
class CosineProcWorker(mp.Process):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super().__init__(group, target, name, args, kwargs)

        # proc worker attrs
        self.args = args
        self.kwargs = kwargs

    """Worker process config prop"""
    @property
    def proc_cfg(self):
        return self.args[0]

    """Worker process context prop"""
    @property
    def proc_cxt(self):
        return self.args[1]


class CosineProcEventMgr(object):

    EventSlot = CosineEventSlot

    def init_queue(self):
        self._events = Queue()
        self._slots = FieldSet()

    def process_events(self):
        # consume all the available events...
        evts = []
        try:
            while not self._events.empty():
                evts.append( self._events.get_nowait() )
        except EmptyException:
            pass

        # process any event handlers registered for these events...
        for evt in evts:
            (name, data) = evt
            if name in self.events:
                self.events[name].fire(data)

    @property
    def events(self):
        return self._slots


class CosineProcEventWorker(CosineProcWorker, CosineProcEventMgr):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super().__init__(group, target, name, args, kwargs)
        self.init_queue()

    def run_via(self, pool, **kwargs):
        pool.start(workers=[self], context=(self._events,), kwargs=kwargs)

    """Worker process enqueue event"""
    def enqueue_event(self, name, data):
        self.proc_queue.put((name, data))

    """Worker process context prop"""
    @property
    def proc_queue(self):
        return self.args[1][0]


class CosineProcWorkers(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self._procs = {}


    def start(self, workers, context=None, kwargs=None):
        pids = []
        for worker in workers:
            if isinstance(worker, mp.Process):
                worker.args = (self.cfg, context)
                worker.kwargs = kwargs
                p = worker
            else:
                p = mp.Process(target=worker, args=(self.cfg, context), kwargs=kwargs)
            self._procs[p.pid] = p
            self._procs[p.pid].start()
            pids.append(p.pid)
        return pids


    def join(self, pid=None, timeout=None):
        for pd in self._procs if pid is None else {pid: self._procs[pid]}:
            p = self._procs[pd]
            p.join(timeout)

        if pid:
            del self._procs[pid]
        else:
            self._procs.clear()


    @property
    def procs(self):
        return self._procs
