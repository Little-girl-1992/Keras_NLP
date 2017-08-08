echo $1
awk -F '|' '{count[$1]++;total++;score+=$1;perp[$1]+=$NF}END{for (item in count){print item" "count[item]/total" "perp[item]/count[item]}{print score/total}}' $1
