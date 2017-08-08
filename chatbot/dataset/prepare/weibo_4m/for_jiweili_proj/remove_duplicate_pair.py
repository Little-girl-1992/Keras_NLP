#!/usr/bin/python
import sys

print('will remove duplicate pair from: %s' % sys.argv[1])
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
  common = 0
  common_tokens = []
  for token in res_tokens:
   if token in post_tokens and token not in common_tokens:
     common = common + 1
     common_tokens.append(token)
  rate = common * 1.0 / (len(post_tokens) + len(res_tokens) - common)
  if rate >= 0.3:
   removed_count = removed_count + 1
   continue
  output_file.write(line + '\n')

print('removed pair count: %d' % removed_count)
input_file.close()
output_file.close()
