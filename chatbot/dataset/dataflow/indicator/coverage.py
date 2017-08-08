#!/usr/bin/env python
# encoding: utf-8

import time
import ujson as json
from config import logger
import multiprocessing

from comm.tmtool import parallel
from retrieval import ConvClient

class Retrieval(object):
    def __init__(self, env, domain, cluster):
        self.env = env
        self.domain = domain
        self.cluster = cluster
        self.conv_client = ConvClient(env, self.domain)

    def search(self, query, limit=30, only_post=False):
        return self.conv_client.search(query, limit, self.cluster, only_post)

    def delete(self, id):
        return self.conv_client.delete(self.cluster, id)

    def index(self, contents):
        return self.conv_client.make_index(self.cluster, contents)

    def scores(self, query, limit=30, only_post=True):
        try:
            res = self.search(query, limit, only_post)
        except Exception as e:
            logger.exception(e)
            hits = []
        else:
            hits = res['top_hits']

        if len(hits) == 0:
            scores = [0]
        else:
            scores = [x['score'] for x in hits]
        max_score = max(scores)
        avg_score = float(sum(scores)) / limit
        logger.debug('%s\t%s\t%s' % (max_score, avg_score, query))
        return scores


class Coverage(object):
    """
    没有对query做escape，需要传递clean之后的
    """
    ID_PREFIX = 'COVERAGE_TEMP_ID_PREFIX'
    INTERVAL = 10

    def __init__(self, queries, env, domain, cluster):
        self.queries = queries or []
        self.query_ids = []
        self.env = env
        self.domain = domain
        self.cluster = cluster
        self.assign_query_id()
        self.retrieval = Retrieval(env, domain, cluster)

    def init_queries_from_file(self, fpath):
        with open(fpath) as f:
            lines = f.readlines()
        self.queries = map(lambda x: x.strip(), lines)
        self.assign_query_id()

    def assign_query_id(self):
        total = len(self.queries)
        self.query_ids = ['%s_%s' % (self.ID_PREFIX, i) for i in range(total)]

    def delete_temp_queries(self):

        def worker(task_queue, result_queue):
            retrieval = Retrieval(self.env, self.domain, self.cluster)
            while not task_queue.empty():
                cid = task_queue.get()
                retrieval.delete(cid)

        start = time.time()
        parallel(self.query_ids, worker)
        end = time.time()

        logger.info('Has delete all %s temp queries in %ss' % (len(self.query_ids), (end - start)))

    def insert_temp_queries(self):
        contents = []
        for cid, post in zip(self.query_ids, self.queries):
            content = dict(id=cid, post=post, resp='NULLRESP')
            contents.append(json.dumps(content))
        chunks = [contents[x: x + 100] for x in xrange(0, len(contents), 100)]
        for i, chunk in enumerate(chunks):
            self.retrieval.index(chunk)
            logger.debug('Has indexed %s temp queries' % ((i + 1) * 100))
        logger.info('Indexed done for %s temp queries' % len(self.queries))

    def all_query_scores(self, limit=30, only_post=True):
        start = time.time()

        def worker(task_queue, result_queue):
            retrieval = Retrieval(self.env, self.domain, self.cluster)
            while not task_queue.empty():
                q = task_queue.get()
                scores = retrieval.scores(q, limit, only_post)
                result_queue.put(scores)

        all_scores = parallel(self.queries, worker)
        # all_scores = map(lambda x: self.retrieval.scores(x, limit, only_post), self.queries)

        end = time.time()
        logger.info('All query complete in %ss' % (end - start))
        return all_scores

    def compute_avg_score(self, all_scores, limit):
        total = len(all_scores)
        max_scores = map(lambda x: max(x), all_scores)
        avg_scores = map(lambda x: float(sum(x)) / limit, all_scores)
        avg_max = float(sum(max_scores)) / total
        avg_avg = float(sum(avg_scores)) / total
        logger.info('Total Avg:\t%s\t%s\t%s' % (total, avg_max, avg_avg))
        return avg_max, avg_avg

    def get_avg_score(self, limit, only_post):
        all_scores = self.all_query_scores(limit, only_post)
        avg_max, avg_avg = self.compute_avg_score(all_scores, limit)
        return avg_max, avg_avg

    def compute(self, limit=30, only_post=True):
        self.insert_temp_queries()
        # 等待oakbay处理完毕
        time.sleep(self.INTERVAL)
        max_contain, avg_contain = self.get_avg_score(limit=1, only_post=only_post)
        self.delete_temp_queries()
        # 等待oakbay处理完毕
        time.sleep(self.INTERVAL)
        max_pure, avg_pure = self.get_avg_score(limit=limit, only_post=only_post)
        max_coverage = max_pure / max_contain
        avg_coverage = avg_pure / avg_contain

        score = dict(
            max_coverage=max_coverage,
            avg_coverage=avg_coverage,
            max_pure=max_pure,
            avg_pure=avg_pure,
            max_contain=max_contain,
            avg_contain=avg_contain
        )

        logger.info('Coverage indicator: %s' % score)
        return score


if __name__ == '__main__':
    import sys
    c = Coverage(None, sys.argv[2], sys.argv[3], sys.argv[4])
    c.init_queries_from_file(sys.argv[1])
    score = c.compute(only_post=False)
