data_dir="/home/guochengkai/Neural-Dialogue-Generation/big_data/OpenSubData"
th train_atten.lua -train_file $data_dir/t_given_s_dialogue_train.txt -dev_file $data_dir/t_given_s_dialogue_dev.txt -test_file $data_dir/t_given_s_dialogue_test.txt -saveFolder save_t_given_s_dialogue
