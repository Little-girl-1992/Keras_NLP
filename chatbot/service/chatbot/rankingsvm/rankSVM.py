# -*- coding: utf-8 -*-
import os
import math
import codecs
import pickle
import numpy as np
from collections import Counter
from sklearn import preprocessing
from sklearn.feature_extraction.text import TfidfVectorizer


class TransLM(object):
  def __init__(self, token_transition_path, token_frequency_path, alpha, beta, gamma):
    """
    load token transition map, and token frequency from the corpus
    input should two dicts and three float numbers less than 1 but larger than 0
    """
    self.alpha = alpha
    self.beta = beta
    self.gamma = gamma
    self.token_transition_map = token_transition_path  # pickle.load(open(token_transition_path))
    self.token_frequency_map = token_frequency_path  # pickle.load(open(token_frequency_path))

  def compute_sim(self, query, post, response):
    """
    query, post and response given to this function should be a list without punctuations
    """

    ### calculate word frequency of post and response
    post_counter, post_total = Counter(post), sum(Counter(post).values())
    response_counter, response_total = Counter(response), sum(Counter(response).values())

    post_frequency = {k: v / float(post_total) for k, v in post_counter.iteritems()}
    response_frequency = {k: v / float(response_total) for k, v in response_counter.iteritems()}

    sim = 1.0
    for w in query:
      ## question here is what if word in query does not show up in the whole collection?
      if w in self.token_frequency_map:
        sim *= (1 - self.alpha) * self.p_mx(w, post_frequency, response_frequency) \
               + self.alpha * self.token_frequency_map[w]
      else:
        sim *= (1 - self.alpha) * self.p_mx(w, post_frequency, response_frequency) \
               + self.alpha * 0.0
    if sim == 0:
      return math.log(1e-200)
    return math.log(sim)

  def p_mx(self, word, post_frequency, response_frequency):
    ml_post = 0.0
    ml_response = 0.0

    for token in post_frequency:
      transition_prob = 0.0
      if token == word:
        transition_prob = 1.0
      elif token in self.token_transition_map:
        if word in self.token_transition_map[token]:
          transition_prob = self.token_transition_map[token][word]
      ml_post += post_frequency[token] * transition_prob

    if word in post_frequency:
      word_frequency_in_post = post_frequency[word]
    else:
      word_frequency_in_post = 0.0

    a = (1 - self.beta) * ((1 - self.gamma) * word_frequency_in_post + self.gamma * ml_post)

    for token in response_frequency:
      transition_prob = 0.0
      if token == word:
        transition_prob = 1.0
      elif token in self.token_transition_map:
        if word in self.token_transition_map[token]:
          transition_prob = self.token_transition_map[token][word]

      ml_response += response_frequency[token] * transition_prob

    if word in response_frequency:
      word_frequency_in_response = response_frequency[word]
    else:
      word_frequency_in_response = 0.0

    b = self.beta * ((1 - self.gamma) * word_frequency_in_response + self.gamma * ml_response)

    return a + b


class SVMRanker(object):
  """
  Performs pairwise ranking with an underlying LinearSVC model
  Input should be a n-class ranking problem, this object will convert it
  into a two-class classification problem, a setting known as
  `pairwise ranking`.

  Finally the model will rank the post-response pairs
  """

  def __init__(self, fpath):

    self.trained_model = fpath + "coef.pickle"
    self.vectorizer1_path = fpath + "vectorizer1.pickle"
    self.vectorizer2_path = fpath + "vectorizer2.pickle"
    self.token_transition_path = fpath + "transition_map.pickle"
    self.token_frequency_path = fpath + "word_frequency_map.pickle"

    self.vectorizer1 = pickle.load(open(self.vectorizer1_path, 'r'))
    self.vectorizer2 = pickle.load(open(self.vectorizer2_path, 'r'))

    self.coef = pickle.load(open(self.trained_model, 'r'))
    token_transition = pickle.load(open(self.token_transition_path, 'r'))
    word_frequency = pickle.load(open(self.token_frequency_path, 'r'))
    self.transLM = TransLM(token_transition, word_frequency, 0.2, 0.5, 0.8)

  def compute_tfidf_sim_unigram(self, text1, text2):
    """
	Input should two lists of words
	And the output is a unigram tf-idf similarity
    """
    tfidf = self.vectorizer1.transform([" ".join(text1), " ".join(text2)])
    return ((tfidf * tfidf.T).A)[0, 1]

  def compute_tfidf_sim_bigram(self, text1, text2):
    """
    Input should two lists of words
    And the output is a bigram tf-idf similarity
    """
    tfidf = self.vectorizer2.transform([" ".join(text1), " ".join(text2)])
    return ((tfidf * tfidf.T).A)[0, 1]

  def predict(self, data):
    """
    Input should be a dict which contains query and post_to_response pairs
    Predict an ordering on X. For a list of n samples, this method
    returns a list from 0 to n-1 with the relative order of the rows of X.
    Parameters
    """
    if not isinstance(data, dict):
      assert Exception("the input of the function predict should be a dict")
    query = data["query"]
    p2r_list = data["p2r"]
    # q2r, q2p, wv
    X = np.array([[
      self.compute_tfidf_sim_unigram(query, pair[1]),
      self.compute_tfidf_sim_unigram(query, pair[0]),
      self.compute_tfidf_sim_bigram(query, pair[1]),
      self.transLM.compute_sim(query, pair[0], pair[1])
    ]
      for pair in p2r_list])
    X[:, 3] = preprocessing.scale(X[:, 3])

    if hasattr(self, 'coef'):
      return np.argsort(np.dot(X, self.coef.T).ravel())[::-1]
    else:
      raise ValueError("Must call fit() offline prior to predict()")

if __name__ == '__main__':
  ranker = SVMRanker()
  ranker.__doc__()