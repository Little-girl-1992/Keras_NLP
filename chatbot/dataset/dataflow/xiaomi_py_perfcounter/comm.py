import time
import threading
import functools


class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


def func_threading(daemon=True):
    def args_func(func):
        @functools.wraps(func)
        def action_func(*args, **kwargs):
            t = StoppableThread(target=func, args=args, kwargs=kwargs)
            t.setName('threading_%s' % func.func_name)
            t.setDaemon(daemon)
            t.start()
            return t
        return action_func
    return args_func


def periodic_threading(interval, daemon=True):
    def args_func(func):

        @func_threading(daemon)
        def _loop(*args, **kwargs):
            t = threading.currentThread()
            while not t.stopped():
                func(*args, **kwargs)
                time.sleep(interval)

        @functools.wraps(func)
        def action_func(*args, **kwargs):
            t = _loop(*args, **kwargs)
            return t
        return action_func

    return args_func
