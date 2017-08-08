#!/usr/bin/python
import sys

print('will remove duplicate words from: %s' % sys.argv[1])
input_file = open(sys.argv[1])
output_file = open(sys.argv[2], 'w')
uniq_map = {}

removed_count = 0
while True:
  line = input_file.readline()
  if not line:
    break
  line = line.strip()
  if line not in uniq_map:
    uniq_map[line] = True
  else:
    continue
  post_and_res = line.split('|')
  post_tokens = post_and_res[0].strip().split(' ')
  res_tokens = post_and_res[1].strip().split(' ')
  distinct_tokens = 0
  exist_tokens = []
  for token in res_tokens:
   if token not in exist_tokens:
     distinct_tokens = distinct_tokens + 1
     exist_tokens.append(token)
  rate = distinct_tokens * 1.0 / len(res_tokens)
  if rate <= 0.6:
    removed_count = removed_count + 1
    continue 
  else:
    output_file.write(line + '\n')

print('removed dup words: %d' % removed_count)
input_file.close()
output_file.close()
