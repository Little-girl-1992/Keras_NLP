#!/usr/bin/python

import os
import sys

word_freqs = {}
file_name = sys.argv[1] 
word_file_name = sys.argv[2] 
input_file = open(file_name)
word_file = open(word_file_name, 'w')

count = 0
while True:
  line = input_file.readline().strip()
  if not line:
    break
  pairs = line.split('|')
  if len(pairs) != 2:
    print("error: %d %s" % (count + 1, line))
    break
  src_words = pairs[0].split(' ')
  dst_words = pairs[1].split(' ')
  words = src_words + dst_words
  for word in words:
    word = word.strip()
    if len(word) == 0:
      continue
    if word not in word_freqs:
      word_freqs[word] = 1
    else:
      word_freqs[word] = word_freqs[word] + 1
  count = count + 1
  if count % 10000 == 0:
    print("processed %d lines" % count)

input_file.close()
for word in word_freqs.keys():
  word_file.write(str(word_freqs[word]) + ' ' + word + '\n')
word_file.close()
