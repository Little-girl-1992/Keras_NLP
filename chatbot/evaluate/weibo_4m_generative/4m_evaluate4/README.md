##实验设置
1. jianweili: Neural-Dialogue-Generation 
2. seq2seq + attention
3. 第9轮迭代，perp: 69
4. beam search size: 15
5. source_vocab = target_vocat = 40000, hidden_size = 512, dropout=0.2, layers=3, batch_size=128, start_halve=6, init_lr=1, init_weight=0.1
6. 3.5 million training pair, 1k testing pair
7. 去掉高频的response

##测试数据选取原则
从测试数据中选取了“不需要额外上线文(图片、链接)就能明确理解含义”的post，一共50条。

##统计结果
From Cuijianwei:
0  0.46 -1.23435
1  0.3 -1.30724
2  0.24 -1.17034
0.78

##实验发现
1. 重复词语太多,约20%
2. 总体看，这组参数效果不错
