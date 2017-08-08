#!/usr/bin/python
import sys

vocab_file = open('words.txt')
vacab = []
while True:
  line = vocab_file.readline()
  if not line:
    break
  vacab.append(line.strip())
print len(vacab)

sentence_file = open(sys.argv[1])
result_file = open(sys.argv[2], 'w')
while True:
  line = sentence_file.readline()
  if not line:
    break
  pairs = line.split('|')
  if len(pairs) != 2:
    print 'invalid conversation'
    print line
    break
  src_tokens = pairs[0].split(' ') 
  src_words = []
  for token in src_tokens:
    src_words.append(vacab[int(token) - 1])
  src_sentence = ' '.join(src_words)

  dst_tokens = pairs[1].split(' ')
  dst_words = []
  for token in dst_tokens:
    dst_words.append(vacab[int(token) - 1])
  dst_sentence = ' '.join(dst_words)

  result_file.write(src_sentence + '|' + dst_sentence + '\n')

vocab_file.close()
sentence_file.close()
result_file.close()
