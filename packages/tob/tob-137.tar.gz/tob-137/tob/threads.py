# This file is placed in the Public Domain.


"non-blocking"


import queue
import threading
import time


from .methods import name


class Thread(threading.Thread):

    def __init__(self, func, *args, daemon=True, **kwargs):
        super().__init__(None, self.run, None, (), daemon=daemon)
        self.name = kwargs.get("name", name(func))
        self.queue = queue.Queue()
        self.result = None
        self.starttime = time.time()
        self.stopped = threading.Event()
        self.queue.put((func, args))

    def __iter__(self):
        return self

    def __next__(self):
        yield from dir(self)

    def join(self, timeout=None):
        super().join(timeout)
        return  self.result

    def run(self):
        func, args = self.queue.get()
        self.result = func(*args)


def launch(func, *args, **kwargs):
    thread = Thread(func, *args, **kwargs)
    thread.start()
    return thread


def __dir__():
    return (
        'Repeater',
        'Thread',
        'launch'
   )
