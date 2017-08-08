--require "fbtorch"
require "cunn"
require "cunn"
require "cutorch"
require "nngraph"
local params = require "parse"
local model = require "atten"
print(model)
--local params=torch.reload("./parse")
--local model=torch.reload("./atten");

cutorch.manualSeed(123)
cutorch.setDevice(params.gpu_index)
model:Initial(params)
model:train()
