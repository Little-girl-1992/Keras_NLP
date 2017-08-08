import time
import pprint
from perfcounter import PerfCounter
from threading import Thread

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

pc = PerfCounter()


def test_id():
    print id(PerfCounter())
    time.sleep(0.5)


def test():
    ts = [Thread(target=test_id) for _ in range(3)]
    for t in ts:
        t.start()

    for t in ts:
        t.join()

    pc.count('c', 1)
    pc.count('c', 2)

    with pc.duration('test_py_perfcounter_d'):
        time.sleep(0.5)
    with pc.duration('test_py_perfcounter_d'):
        time.sleep(0.4)

    pc.inc_counter('test_py_perfcounter_c', 3)
    pc.mark_meter('test_py_perfcounter_m', 1)

    pc.set_gauge('test_py_perfcounter_g', 100)

    for i in range(10):
        pc.add_hist('test_py_perfcounter_h', i)

    pprint.pprint(pc.dump_metrics())
    pprint.pprint(pc.reporter_collect())


def main():
    pc.add_tags('test_py_perfcounter_duration', dict(t='test', r='random'))
    pc.add_tags('test_py_perfcounter_count', dict(t='test', r='random'))
    while True:
        time.sleep(1)
        logger.info('new falcon record')
        with pc.duration('test_py_perfcounter_duration'):
            time.sleep(0.3)
        pc.count('test_py_perfcounter_count', 2)


if __name__ == '__main__':
    main()


