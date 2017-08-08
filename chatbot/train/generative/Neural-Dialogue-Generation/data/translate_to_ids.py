#!/usr/bin/python
#encoding=utf-8

vocab_file = open('./words.txt')
vocab = {}
count = 0
while True:
  line = vocab_file.readline()
  if not line:
    break
  vocab[line.strip()] = count 
  count = count + 1
print count

sentence_file = open('./conv.txt')
result_file = open('t_given_s.txt', 'w')
while True:
  line = sentence_file.readline()
  if not line:
    break
  line = line.strip()
  pairs = line.split('|')
  if len(pairs) != 2:
    print 'invalid conversation'
    print line
  src_words = pairs[0].split(' ') 
  src_tokens = []
  has_unknown = False
  for word in src_words:
    item = word.strip().lower()
    if len(item) == 0:
      continue
    if item not in vocab:
      item = '<unknown>'
      has_unknown = True
    src_tokens.append(str(vocab[item] + 1))
  src_sentence = ' '.join(src_tokens)

  dst_words = pairs[1].split(' ')
  dst_tokens = []
  for word in dst_words:
    item = word.strip().lower()
    if len(item) == 0:
      continue
    if item not in vocab:
      item = '<unknown>'
      has_unknown = True
    dst_tokens.append(str(vocab[item] + 1))
  dst_sentence = ' '.join(dst_tokens)

  if has_unknown:
    #print line
    continue;

  if len(src_sentence) > 0 and len(dst_sentence) > 0:
    result_file.write(src_sentence + '|' + dst_sentence + '\n')

vocab_file.close()
sentence_file.close()
result_file.close()
