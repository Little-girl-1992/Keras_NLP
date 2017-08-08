awk -F '|' '{print $1}' conv_prepared.txt > t_given_s_train_post
awk -F '|' '{print $2}' conv_prepared.txt > t_given_s_train_response
awk -F '|' '{print $1}' test.txt > t_given_s_test_post
awk -F '|' '{print $2}' test.txt > t_given_s_test_response
