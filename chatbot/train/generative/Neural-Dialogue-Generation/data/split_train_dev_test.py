#!/usr/bin/python

total_file = open('t_given_s.txt')
train_file = open('t_given_s_train.txt', 'w')
dev_file = open('t_given_s_dev.txt', 'w')
test_file = open('t_given_s_test.txt', 'w')

count = 1
while True:
  line = total_file.readline()
  if not line:
    break
  count = count + 1
  if count % 10 == 0:
    test_file.write(line)
  else:
    train_file.write(line)
test_file.close()
dev_file.close()
train_file.close()
total_file.close()
