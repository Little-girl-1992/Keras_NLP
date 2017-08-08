#data_dir="/home/guochengkai/Neural-Dialogue-Generation/big_data/OpenSubData_200k"
#data_dir="/home/guochengkai/Neural-Dialogue-Generation/data/cornell"
#data_dir="/home/guochengkai/Neural-Dialogue-Generation/data/kf_32w"
#data_dir="/home/guochengkai/Neural-Dialogue-Generation/data/subtitles_filter"
data_dir="/home/guochengkai/Neural-Dialogue-Generation/data/weibo"
#th train_atten.lua -train_file $data_dir/s_given_t_dialogue_train.txt -dev_file $data_dir/s_given_t_dialogue_dev.txt -test_file $data_dir/s_given_t_dialogue_test.txt -saveFolder save_s_given_t_dialogue_200k_reverse -gpu_index 1 -max_iter 20 -reverse 1>200k_output_s_given_t 2>&1 &
#th train_atten.lua -train_file $data_dir/kf_s_given_t_train.txt -dev_file $data_dir/kf_s_given_t_dev.txt -test_file $data_dir/kf_s_given_t_test.txt -saveFolder save_kf_s_32w_given_t_reverse -max_iter 25 -reverse -dictPath $data_dir/ch_words.txt -gpu_index 3 1>kf_32w_output_s_given_t -vocab_source 25010 -vocab_target 25010 2>&1 &
th train_atten.lua -train_file $data_dir/s_given_t_train.txt -dev_file $data_dir/s_given_t_dev.txt -test_file $data_dir/s_given_t_test.txt -saveFolder weibo_s_given_t_reverse -max_iter 25 -reverse -dictPath $data_dir/words.txt -gpu_index 3 1>weibo_output_s_given_t -vocab_source 25010 -vocab_target 25010 2>&1 &
