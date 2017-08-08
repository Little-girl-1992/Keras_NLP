#!/usr/bin/python
import sys

print('will remove duplicate pair from: %s' % sys.argv[1])
test_post = open('test.txt')
from_file = open(sys.argv[1])
output_file = open(sys.argv[2], 'w')

test_post_dict = {}
while True:
  line = test_post.readline()
  if not line:
    break
  post = line.strip().split('|')[0].strip()
  test_post_dict[post] = True 

removed_count = 0
while True:
  line = from_file.readline()
  if not line:
    break
  post = line.strip().split('|')[0].strip()
  if post not in test_post_dict:
    output_file.write(line.strip() + '\n')
  else:
    removed_count = removed_count + 1

print('removed test pair count: %d' % removed_count)
test_post.close()
from_file.close()
output_file.close()
