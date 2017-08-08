model_path="../Atten/save_cornell_s_given_t_reverse"
mmi_model_path="../Atten/save_cornell_t_given_s_reverse"
#test_file="../big_data/OpenSubData/t_given_s_dialogue_test_tiny.txt"
test_file="sample_question_ids.txt"
#test_file="../data/cornell/cornell_t_given_s_test.txt"
model_name="model16"

th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -batch_size 1 -dictPath ../data/cornell/cornell_25000 -MMI -MMI_params_file $mmi_model_path/params -MMI_model_file $mmi_model_path/$model_name -OutputFile ./cornell/output_test.txt -DiverseRate 5 -NBest

# for raw
#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -batch_size 23 -dictPath ../data/cornell/cornell_25000 -OutputFile ./cornell/output_raw.txt 
#
## for diverse 1
#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -batch_size 23 -dictPath ../data/cornell/cornell_25000 -OutputFile ./cornell/output_diverse_1.txt -DiverseRate 1 
#
## for diverse 5 
#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -batch_size 23 -dictPath ../data/cornell/cornell_25000 -OutputFile ./cornell/output_diverse_5.txt -DiverseRate 5 
#
## for diverse 10
#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -batch_size 23 -dictPath ../data/cornell/cornell_25000 -OutputFile ./cornell/output_diverse_10.txt -DiverseRate 10 
#
## for mmi
#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -batch_size 23 -dictPath ../data/cornell/cornell_25000 -MMI -MMI_params_file $mmi_model_path/params -MMI_model_file $mmi_model_path/$model_name -OutputFile ./cornell/output_mmi.txt
#
## for mmi with diverse 5
#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -batch_size 23 -dictPath ../data/cornell/cornell_25000 -MMI -MMI_params_file $mmi_model_path/params -MMI_model_file $mmi_model_path/$model_name -OutputFile ./cornell/output_mmi_diverse_5.txt -DiverseRate 5
#
## with beam size = 50
#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -batch_size 23 -dictPath ../data/cornell/cornell_25000 -OutputFile ./cornell/output_beam_50.txt -beam_size 50 
#
## with beam size = 200
#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -batch_size 23 -dictPath ../data/cornell/cornell_25000 -OutputFile ./cornell/output_beam_200.txt -beam_size 200 
#
## mmi with beam size 100 
#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -batch_size 23 -dictPath ../data/cornell/cornell_25000 -MMI -MMI_params_file $mmi_model_path/params -MMI_model_file $mmi_model_path/$model_name -OutputFile ./cornell/output_mmi_beam_100.txt -beam_size 100
#
## for mmi with diverse 5
#th decode.lua -model_file $model_path/$model_name -params_file $model_path/params -InputFile $test_file -gpu_index 3 -batch_size 23 -dictPath ../data/cornell/cornell_25000 -MMI -MMI_params_file $mmi_model_path/params -MMI_model_file $mmi_model_path/$model_name -OutputFile ./cornell/output_mmi_diverse_5_beam_100.txt -DiverseRate 5 -beam_size 100
