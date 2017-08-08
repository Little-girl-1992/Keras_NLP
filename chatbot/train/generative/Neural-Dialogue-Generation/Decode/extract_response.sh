id=$1
awk '{if ($1 == "'$id'"){print $0}}' sample_output.txt| awk -F '|' '{print $2" |"$0}' | sort -nr > temp.1 
awk '{if ($1 == "'$id'"){print $0}}' sample_output.txt| awk -F '|' '{print $3" |"$0}' | sort -nr > temp.2 
awk '{if ($1 == "'$id'"){print $0}}' sample_output.txt| awk -F '|' '{print $4" |"$0}' | sort -nr > temp.3 
