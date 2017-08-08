# -*- coding: utf-8 -*-
from keras.preprocessing import sequence
import cPickle as pickle
import random
import numpy as np
import itertools
import tensorflow as tf

import os
os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"]="0,1"

print 'loading token map'
word_to_index = pickle.load(open('word_to_index.pkl'))
index_to_vector = pickle.load(open('index_to_vector.pkl'))

print 'loading data'
train_cut = pickle.load(open('train.pkl'))
dev_cut = pickle.load(open('dev.pkl'))
print 'number of queries(plus 4 negative samples) for training: ', len(train_cut)

## parameters for fine-tuning
sequence_length = 25
vocab_size = len(word_to_index)
embedding_size = 50
filter_size = 4
num_filters = 100
hidden_dim1 = 50
#hidden_dim2  = 20
learning_rate = 0.001
dropout_rate = 0.7
std = 0.05
margin = 1.5



def load_data(data, sequence_length, word_to_index):
    post = map(lambda lll: [word_to_index[x] if x in word_to_index else 1 for x in lll], [x[0] for x in data])
    reply = map(lambda lll: [word_to_index[x] if x in word_to_index else 1 for x in lll], [x[1] for x in data])
    
    x_post = sequence.pad_sequences(post, maxlen=sequence_length, padding='post', truncating='post', value=0)
    x_reply = sequence.pad_sequences(reply, maxlen=sequence_length, padding='post', truncating='post', value=0)
    y = np.array([x[-1] for x in data])
    shuffle_indices = np.random.permutation(np.arange(len(data)))
    x_post, x_reply, y = x_post[shuffle_indices], x_reply[shuffle_indices], y[shuffle_indices]
    return np.array(zip(x_post, x_reply, y))

def dump_into_batches(data, batch_size):
    shuffle_indices = np.random.permutation(np.arange(len(data)))
    batches = []
    data = data[shuffle_indices]
    for batch_indices in xrange(0, len(data), batch_size):
        batches.append(data[batch_indices:batch_indices+batch_size])
#         print batch_indices, batch_indices + batch_size
    return batches





def tf_count(t, val):
    elements_equal_to_value = tf.equal(t, val)
    as_ints = tf.cast(elements_equal_to_value, tf.int32)
    count = tf.reduce_sum(as_ints, axis=1)
    return count

input_x1 = tf.placeholder(tf.int32, [None, sequence_length], name='input_x_post')
input_x2 = tf.placeholder(tf.int32, [None, sequence_length], name='input_x_reply')
input_y = tf.placeholder(tf.float32, [None, 1], name='input_y')



with tf.name_scope("embedding"):
#     W = tf.Variable(
#         tf.random_uniform([vocab_size, embedding_size], -1.0, 1.0),
#         name="Weight_emb")
    W = tf.Variable(tf.constant(0.0, shape=[vocab_size, embedding_size]), trainable=False, name='Weight_emb')
    embedding_placeholder = tf.placeholder(tf.float32, [vocab_size, embedding_size])
    embedding_init = W.assign(embedding_placeholder)
    
    embedded_words1 = tf.nn.embedding_lookup(W, input_x1)
    embedded_words_expanded1 = tf.expand_dims(embedded_words1, -1)
    
    embedded_words2 = tf.nn.embedding_lookup(W, input_x2)
    embedded_words_expanded2 = tf.expand_dims(embedded_words2, -1)
    
    
    
pool_outputs = []

with tf.device('/gpu:0'), tf.name_scope('conv-maxpool1'):
    filter_shape = (filter_size, embedding_size, 1, num_filters)
    W = tf.Variable(np.float32(np.random.normal(0, std, filter_shape)), name="W_conv1")
    conv1 = tf.nn.conv2d(
        embedded_words_expanded1,
        W,
        strides=[1, 1, 1, 1],
        padding="VALID",
        name="conv1")

    b = tf.Variable(np.float32(np.random.normal(0, std, [num_filters])), name="b_conv1")
    # Apply nonlinearity
    h1 = tf.nn.relu(tf.nn.bias_add(conv1, b), name="sigmoid_conv1")
    
    num_zero_pad1 = tf_count(input_x1, 0)

    big_mask1 = []
    for _ in range(num_filters):
        mask = tf.sequence_mask(sequence_length - filter_size + 1 -num_zero_pad1 +2, \
                                sequence_length - filter_size + 1)
        mask = tf.expand_dims(mask, -1)
        mask = tf.expand_dims(mask, -1)
        mask = tf.cast(mask, tf.float32)
        big_mask1.append(mask)
    big_mask1 = tf.concat(big_mask1, 3)
    h_new1 = tf.multiply(h1, big_mask1)



    max_pooled1 = tf.reduce_max(h_new1, axis=[1], keep_dims=True)

    pool_outputs.append(max_pooled1)
    

with tf.device('/gpu:1'), tf.name_scope('conv-maxpool2'):
    filter_shape = (filter_size, embedding_size, 1, num_filters)
    W = tf.Variable(np.float32(np.random.normal(0, std, filter_shape)), name="W_conv2")
    conv2 = tf.nn.conv2d(
        embedded_words_expanded2,
        W,
        strides=[1, 1, 1, 1],
        padding="VALID",
        name="conv2")

    b = tf.Variable(np.float32(np.random.normal(0, std, [num_filters])), name="b_conv2")
    # Apply nonlinearity
    h2 = tf.nn.relu(tf.nn.bias_add(conv2, b), name="sigmoid_conv2")


    num_zero_pad2 = tf_count(input_x2, 0)

    big_mask2 = []
    for _ in range(num_filters):
        mask = tf.sequence_mask(sequence_length - filter_size + 1 -num_zero_pad2 +2, \
                                sequence_length - filter_size + 1)
        mask = tf.expand_dims(mask, -1)
        mask = tf.expand_dims(mask, -1)
        mask = tf.cast(mask, tf.float32)
        big_mask2.append(mask)
    big_mask2 = tf.concat(big_mask2, 3)

    h_new2 = tf.multiply(h2, big_mask2)
    max_pooled2 = tf.reduce_max(h_new2, axis=[1], keep_dims=True)

    pool_outputs.append(max_pooled2)
    
with tf.name_scope('maxPooling-concat'):
    num_filters_total = num_filters * len(pool_outputs)
    h_pool = tf.concat(pool_outputs, 3)   
    h_pool_flat = tf.reshape(h_pool, [-1, num_filters_total])
    


###
### after pooling, and then just feed to the output
###

with tf.name_scope('dropout1'):
    dropout1 = tf.layers.dropout(h_pool_flat, rate=dropout_rate)

with tf.name_scope('dense'):
    W = tf.Variable(np.float32(np.random.normal(0, std, [num_filters_total, hidden_dim1])), name="W_dense1")
    b = tf.Variable(np.float32(np.random.normal(0, std, [hidden_dim1])), name="b_dense1")
    dense = tf.nn.relu(tf.nn.xw_plus_b(dropout1, W, b), name='dense1_relu')

with tf.name_scope('dropout2'):
    dropout2 = tf.layers.dropout(dense, rate=dropout_rate)


with tf.name_scope('output'):
    W = tf.Variable(np.float32(np.random.normal(0, std, [hidden_dim1, 1])), name="W_output")
    b = tf.Variable(np.float32(np.random.normal(0, std, [1])), name="b_output")
    scores = tf.nn.xw_plus_b(dropout2, W, b, name='scores')


with tf.name_scope('loss'):
    losses = tf.reduce_mean(tf.nn.relu(margin - input_y * scores))

    
with tf.name_scope('optimizer'):
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(losses)

    
init = tf.global_variables_initializer()




# Launch the graph
with tf.Session(config=tf.ConfigProto(log_device_placement=True, allow_soft_placement=True)) as sess:
    train_data = load_data(np.array(list(itertools.chain(*train_cut))), sequence_length, word_to_index)
    print 'initializing weights ...'
    sess.run(init)
    print 'loading embedding ...'
    sess.run(embedding_init, feed_dict={embedding_placeholder:index_to_vector.values()})
    num_epoch = 1000
    batch_size = 96
    iter_epoch = 0
    print "training ..."
    while iter_epoch <= num_epoch:
        
#         print ">----------", iter_epoch, "------------<"
        if iter_epoch % 10 == 0:
            print 'evaluating...', iter_epoch, '.....'
            for item in random.sample(dev_cut, 10):
                combo = load_data(item, sequence_length, word_to_index)
                x_post = np.array([x[0] for x in combo])
                x_reply = np.array([x[1] for x in combo])
                y = np.reshape(np.array([x[2] for x in combo]), (-1, 1))
                y_pred = sess.run(scores, feed_dict={input_x1: x_post, input_x2: x_reply,input_y: y})
                print sorted(zip(y.reshape(-1), y_pred.reshape(-1)), key=lambda x:x[1], reverse=True)
                
        if iter_epoch % 50 == 0:
            print 'evaluating...', iter_epoch, '.....'
            p_at_1 = 0
            for item in random.sample(train_cut, 10000):
                combo = load_data(item, sequence_length, word_to_index)
                x_post = np.array([x[0] for x in combo])
                x_reply = np.array([x[1] for x in combo])
                y = np.reshape(np.array([x[2] for x in combo]), (-1, 1))
                y_pred = sess.run(scores, feed_dict={input_x1: x_post, input_x2: x_reply, input_y: y})
                top1 = sorted(zip(y.reshape(-1), y_pred.reshape(-1)), key=lambda x: x[1], reverse=True)[0]
                if top1[0] == 1:
                    p_at_1 += 1
            print "train p@1: ", p_at_1 / 10000.0

            p_at_1 = 0
            for item in random.sample(dev_cut,10000):
                combo = load_data(item, sequence_length, word_to_index)
                x_post = np.array([x[0] for x in combo])
                x_reply = np.array([x[1] for x in combo])
                y = np.reshape(np.array([x[2] for x in combo]), (-1, 1))
                y_pred = sess.run(scores, feed_dict={input_x1: x_post, input_x2: x_reply,input_y: y})
                top1 = sorted(zip(y.reshape(-1), y_pred.reshape(-1)), key=lambda x:x[1], reverse=True)[0]
                if top1[0] == 1:
                    p_at_1 += 1
            print "dev p@1: ", p_at_1 / 10000.0
#             train_data = load_data(random.sample(train_cut, len(dev_cut)*5), sequence_length, word_to_index)
#             loss_train = sess.run(losses, feed_dict={input_x1: np.array([x[0] for x in train_data]), \
#                                             input_x2: np.array([x[1] for x in train_data]) ,\
#                                            input_y: np.reshape(np.array([x[2] for x in train_data]), (-1,1))})
            
            
#             dev_data = load_data(np.array(list(itertools.chain(*dev_cut))), sequence_length, word_to_index)
#             loss_dev = sess.run(losses, feed_dict={input_x1: np.array([x[0] for x in dev_data]), \
#                                            input_x2: np.array([x[1] for x in dev_data]) ,\
#                                            input_y: np.reshape(np.array([x[2] for x in dev_data]), (-1, 1))})
#             print 'hinge loss, train and dev: ', loss_train, loss_dev


        batches = dump_into_batches(train_data, batch_size)
        for batch in batches:
            batch_x_post = np.array([x[0] for x in batch])
            batch_x_reply = np.array([x[1] for x in batch])
            batch_y = np.reshape(np.array([x[2] for x in batch]), (-1, 1))
            sess.run(optimizer, feed_dict={input_x1: batch_x_post, \
                                           input_x2: batch_x_reply,\
                                           input_y: batch_y})    
        iter_epoch += 1
