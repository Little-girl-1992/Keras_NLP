#data_dir="/home/guochengkai/Neural-Dialogue-Generation/data/cornell"
#data_dir="/home/guochengkai/Neural-Dialogue-Generation/data/kf_32w"
#data_dir="/home/guochengkai/Neural-Dialogue-Generation/data/subtitles_filter"
data_dir="/home/guochengkai/Neural-Dialogue-Generation/data/weibo"
#th train_atten.lua -train_file $data_dir/t_given_s_dialogue_train.txt -dev_file $data_dir/t_given_s_dialogue_dev.txt -test_file $data_dir/t_given_s_dialogue_test.txt -saveFolder save_t_given_s_dialogue_200k_reverse -gpu_index 3 -max_iter 20 -reverse 1>200k_output 2>&1 &
#th train_atten.lua -train_file $data_dir/cornell_t_given_s_train.txt -dev_file $data_dir/cornell_t_given_s_dev.txt -test_file $data_dir/cornell_t_given_s_test.txt -saveFolder save_cornell_t_given_s_reverse -max_iter 50 -reverse -dictPath $data_dir/cornell_25000 1>cornell_output 2>&1 &
#th train_atten.lua -train_file $data_dir/kf_t_given_s_train.txt -dev_file $data_dir/kf_t_given_s_dev.txt -test_file $data_dir/kf_t_given_s_test.txt -saveFolder save_kf_32w_t_given_s_reverse -max_iter 25 -reverse -dictPath $data_dir/ch_words.txt -vocab_source 25010 -vocab_target 25010 1>kf_32w_output 2>&1 &

th train_atten.lua -train_file $data_dir/t_given_s_train.txt -dev_file $data_dir/t_given_s_dev.txt -test_file $data_dir/t_given_s_test.txt -saveFolder weibo_t_given_s_reverse -max_iter 25 -reverse -dictPath $data_dir/words.txt -vocab_source 25010 -vocab_target 25010 1>weibo_output 2>&1 &
