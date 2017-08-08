# encoding=utf8
import os
import json
import logging

from django.http import JsonResponse
from rankingsvm.rankSVM import SVMRanker
from retrieval.oakbay_based.search import SearchClient as RetrievalClient


def log():
  logger = logging.getLogger()
  logger.setLevel(logging.DEBUG)
  log_root = os.getcwd() + '/log/'
  handler = logging.FileHandler(log_root + 'info.log', encoding='UTF-8')
  logging_format = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
  handler.setFormatter(logging_format)
  logger.addHandler(handler)
  return logger

# setting logging
logger = log()

# init ranker
print('path:', os.getcwd())

ranker = SVMRanker(fpath=os.getcwd()+'/data/model/')

# init retrieval clients
retrieval_clients = {
  'douban': RetrievalClient(env='c3', use_cut=False)
}


def to_retrieval(query, doc_type=''):
  if doc_type == 'douban':
    hits = retrieval_clients[doc_type].search(query, limit=30, domain='chatbot',
                                              cluster='chatbot_douban_0.1', only_post=True)
  else:
    hits = {}
    logging.error('doc_type is not exist')
  return hits


def to_rank_request(query, retrieval_results):
  request = dict()
  request['query'] = query.decode('utf-8').split()
  request['p2r'] = []
  request['doc_type'] = []
  for hit in retrieval_results:
    p2r = list()
    p2r.append(hit['source']['post'].decode('utf-8').split())
    p2r.append(hit['source']['resp'].decode('utf-8').split())
    request['p2r'].append(p2r)
    request['doc_type'].append(hit['doc_type'])
  return request


def search_result_to_response(retrieval_results, result_num,
                              query, user, device, reply, status, confidence):
  result = dict()
  result['user'] = user
  result['query'] = query
  result['device'] = device
  result['response_dlchat'] = {}
  for i in range(0, min(result_num, len(retrieval_results))):
    hit = retrieval_results[i]
    res = dict()
    res['score'] = hit['score']
    res['text'] = ' '.join(hit['source']['resp'])
    res['doc_type'] = hit['doc_type']
    result['response_dlchat'][i] = res
  result['response_trio'] = {'status': status, 'text': reply, 'score': confidence}
  logger.info(result)
  print(result)
  return result


def to_response(ranking_request, ranks, result_num,
                query, user, device, reply, status, confidence):
  result = dict()
  result['user'] = user
  result['query'] = query
  result['device'] = device
  result['response_dlchat'] = {}
  for i in range(0, min(result_num, len(ranks))):
    res = {}  # resp result
    rank = ranks[i]
    resp = ranking_request['p2r'][rank][1]
    res['score'] = 1
    res['status'] = 0
    res['text'] = ' '.join(resp)
    res['doc_type'] = ranking_request['doc_type'][rank]
    result['response_dlchat'][i] = res
  result['response_trio'] = {'status': status, 'text': reply, 'score': confidence}
  logger.info(result)
  print(result)
  return result


def query(request):
  # debug code
  if request.method != 'POST':
    error = {}
    mes = "request is error"
    error['OK'] = False
    error['detail'] = mes
    return JsonResponse(error)

  json_request_data = json.loads(request.body)
  user = json_request_data.get('user', 'test_user')
  device = json_request_data.get('device', 'test_device')
  query = json_request_data.get('query', False)
  reply = json_request_data.get('reply', 'test_replay')
  status = json_request_data.get('status', 0)
  confidence = json_request_data.get('confidence', 1)

  retrieval = json_request_data.get('retrieval', True)
  ranking = json_request_data.get('ranking', True)
  doc_type = json_request_data.get('doc_type', 'douban')
  result_num = json_request_data.get('result_num', 1)
  threshold = json_request_data.get('threshold', 0)

  doc_type_list = []
  retrieval_results = []
  if retrieval:
    if doc_type == 'all':
      doc_type_list = retrieval_clients.keys()
    else:
      doc_type_list.append(doc_type)

    for _doc_type in doc_type_list:
      hits = to_retrieval(query, doc_type=_doc_type)
      for hit in hits['top_hits']:
        if threshold < float(hit['score']):
          hit['doc_type'] = _doc_type
          retrieval_results.append(hit)


    if ranking:
      ranking_requests = to_rank_request(query, retrieval_results)
      ranks = ranker.predict(ranking_requests)
      return JsonResponse(to_response(ranking_requests, ranks, result_num,
                                      query, user, device, reply, status, confidence))
    else:
      return JsonResponse(search_result_to_response(retrieval_results, result_num,
                                                    query, user, device, reply, status, confidence))
  else:
    response = {}
    mes = "both retrieval and ranking are False"
    response['OK'] = False
    response['detail'] = mes
    return JsonResponse(response)

