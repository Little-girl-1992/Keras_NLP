model_path="../Atten/save_kf_32w_t_given_s_reverse"
mmi_model_path="../Atten/save_kf_32w_s_given_t_reverse"
#test_file="../big_data/OpenSubData/t_given_s_dialogue_test_tiny.txt"
test_file="sample_question_ids_kf.txt"
#test_file="../data/kf_32w/kf_t_given_s_test.txt"
model_name="model25"


#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -dictPath ../data/kf/ch_words.txt -OutputFile ./kf/output_raw.txt 
#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -dictPath ../data/kf/ch_words.txt -OutputFile ./kf/output_diverse_5_ep_50.txt -DiverseRate 5

## for mmi
#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -dictPath ../data/kf/ch_words.txt -MMI -MMI_params_file $mmi_model_path/params -MMI_model_file $mmi_model_path/$model_name -OutputFile ./kf/output_mmi.txt

#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -dictPath ../data/kf_32w/ch_words.txt -MMI -MMI_params_file $mmi_model_path/params -MMI_model_file $mmi_model_path/$model_name -OutputFile ./kf_32w/output_mmi_diverse_5_test.txt -DiverseRate 5
th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -dictPath ../data/kf_32w/ch_words.txt -MMI -MMI_params_file $mmi_model_path/params -MMI_model_file $mmi_model_path/$model_name -OutputFile ./output_mmi_diverse_5_test.txt -batch_size 1 -NBest #-DiverseRate 5 
#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -dictPath ../data/kf_32w/ch_words.txt -OutputFile ./output_mmi_diverse_5_test.txt -batch_size 1 -NBest -DiverseRate 5 

#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -batch_size 1 -dictPath ../data/kf/ch_words.txt -MMI -MMI_params_file $mmi_model_path/params -MMI_model_file $mmi_model_path/$model_name -OutputFile ./kf/kf_test_out.txt -DiverseRate 5
