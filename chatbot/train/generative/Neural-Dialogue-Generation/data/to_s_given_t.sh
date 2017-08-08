cat t_given_s_train.txt | awk -F '|' '{print $2"|"$1}'  > s_given_t_train.txt
cat t_given_s_test.txt | awk -F '|' '{print $2"|"$1}'  > s_given_t_test.txt
cat t_given_s_dev.txt | awk -F '|' '{print $2"|"$1}'  > s_given_t_dev.txt
