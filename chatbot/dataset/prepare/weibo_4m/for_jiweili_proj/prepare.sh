#python ./generate_conv.py 
#python remove_duplicate_pair.py conv.txt conv_remove_dup_pair.txt
#python remove_duplicate_words.py conv_remove_dup_pair.txt conv_remove_dup_pair_words.txt
#python remove_test_post.py conv_remove_dup_pair_words.txt conv_remove_dup_pair_words_test.txt
#sh remove_special_words.sh conv_remove_dup_pair_words_test.txt conv_prepared.txt
#python generate_freq_words.py conv_prepared.txt words_freq.txt

# generate top words
#cat words_freq.txt | sort -nr | head -n40000 | awk '{print $2}' > words.txt
#echo "<unknown>" >> words.txt

#python translate_to_ids.py conv_prepared.txt t_given_s_train.txt 
python translate_to_ids.py test.txt t_given_s_test.txt
cp t_given_s_test.txt t_given_s_dev.txt
