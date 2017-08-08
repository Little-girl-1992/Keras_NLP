#!/usr/bin/python

post_file = open('stc_weibo_train_post')
response_file = open('stc_weibo_train_response')
conv_file = open('conv.txt', 'w')

count = 0
while True:
  post = post_file.readline().strip()
  if not post:
    break
  response = response_file.readline().strip()
  if post.find('|') != -1 or response.find('|') != -1:
    continue
  conv_file.write(post + " | " + response + "\n")
  count = count + 1
  if count % 10000 == 0:
    print("processed %d lines" % count)

conv_file.close()
response_file.close()
post_file.close()

  
