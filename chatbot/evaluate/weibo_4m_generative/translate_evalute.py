#encoding=utf-8
import sys

dict_file = open('../../data/weibo/words.txt')
word_dict = [] 
while True:
  line = dict_file.readline()
  if not line:
    break
  word_dict.append(line.strip())

raw_file = open(sys.argv[1])
answer_file = open('../../data/weibo/evaluate_ids.txt')

def read_answer(input_file, to_word = False):
  line = input_file.readline().strip()
  tokens = line.split('|')
  if to_word:
    answer_words = []
    for token in tokens[1].split(' '):
      answer_words.append(word_dict[int(token.strip()) - 1])
    return ' '.join(answer_words)
  else:
    return tokens[1]

count = 0
while True:
  line = raw_file.readline().strip()
  if not line:
    break 
  tokens = line.split('|')
  question_tokens = tokens[0].split(' ')
  question_tokens.reverse()
  question = ' '.join(question_tokens)
  model_answer = question + '|' + tokens[1]
  model_answer = model_answer + '  |  ' + read_answer(answer_file, True) + '|' + tokens[2] 
  print model_answer
  count = count + 1
  #if count == 850:
  #  break

raw_file.close()
answer_file.close()
dict_file.close()
