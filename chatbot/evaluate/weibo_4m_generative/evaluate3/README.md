##实验设置
1. jianweili: Neural-Dialogue-Generation 
2. seq2seq + attention
3. 第8轮迭代，perp: 78 
4. beam search size: 15
5. source_vocab = target_vocat = 25010, hidden_size = 1024, dropout=0.2, layers=3, batch_size=128, start_halve=6, init_lr=1, init_weight=0.1
6. 1.4 million training pair, 1.4w testing pair

##测试数据选取原则
从测试数据中选取了“不需要额外上线文(图片、链接)就能明确理解含义”的post，一共64条。

##统计结果
1  0.488372 -1.15321
2  0.116279 -1.02862
0  0.395349 -1.14216
AvgScore 0.72093

##实验发现
1. 如果继续增加beam search size，一些先验概率高的response就会以排在前面
2. mmi model的分数与model的分数scale不一样，简单加权有问题
3. 目前的结果又一些语法错误，以及相当比例的“安全回答”
