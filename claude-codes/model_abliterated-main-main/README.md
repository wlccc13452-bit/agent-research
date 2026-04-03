# Qwen2.5-1.5B-Instruct 模型去安全限制工具

这是一个用于对 Qwen2.5-1.5B-Instruct 模型进行"abliteration"（去安全限制）的 Python 脚本。该工具通过分析模型在有害和无害指令上的激活模式，识别并移除模型中的安全拒绝机制。

## 🚀 功能特点
- 🔍 激活分析 : 分析模型在有害和无害指令上的不同激活模式
- 🎯 拒绝方向识别 : 自动识别模型中负责拒绝有害请求的神经元方向
- ⚡ 实时干预 : 支持推理时干预和永久权重修改两种模式
- 💾 本地保存 : 将去安全限制后的模型保存到本地
- 📊 效果评估 : 提供多种候选层的效果对比和人工评估

## 📋  环境要求

```bash
pip install torch transformers datasets transformer-lens einops jaxtyping tqdm
```

## 📁  项目结构

```
abliterated/
├── main.py                           # 主脚本文件
├── data/                              # 数据集目录
│   ├── harmful_behaviors/             # 有害指令数据集
│   │   ├── train-00000-of-00001.parquet
│   │   └── test-00000-of-00001.parquet
│   └── harmless_alpaca/               # 无害指令数据集
│       ├── train-00000-of-00001.parquet
│       └── test-00000-of-00001.parquet
├── Qwen
│   └── qwen2.5-1.5B-Instruct/            # 原始模型目录│（需要下载）
└── qwen2.5-1.5B-Instruct-abliterated/ # 输出的修改后模型（脚本生成）
```

## 🛠️  使用方法

### 1. 数据准备

确保在`data/`目录下有以下数据集：
- `harmful_behaviors/`: 包含有害指令的数据集
- `harmless_alpaca/`: 包含无害指令的数据集

### 2. 模型准备

将Qwen2.5-1.5B-Instruct模型放置在本地，或确保能够访问Hugging Face Hub。

### 3. 运行脚本

```bash
python main.py
```
### 4. 脚本执行流程
1. 📥 数据加载 : 加载有害和无害指令数据集
2. 🤖 模型加载 : 加载本地 Qwen2.5-1.5B-Instruct 模型
3. ⚙️ 激活提取 : 批量处理256个指令样本，提取模型各层激活
4. 📐 方向分析 : 计算有害和无害激活的差异方向
5. 🧪 效果评估 : 测试20个候选方向的干预效果
6. ✂️ 权重修改 : 选择第10个候选方向并永久修改模型权重
7. 💾 模型保存 : 将修改后的模型保存到本地


## 🧪核心算法

### 激活差异分析

1. **数据收集**: 分别收集模型在处理有害和无害指令时的内部激活
2. **差异计算**: 计算有害和无害激活的平均差异
3. **方向识别**: 将差异向量标准化作为"拒绝方向"
4. **方向排序**: 根据激活强度对所有候选方向进行排序

### 正交化权重修改

使用数学正交化方法永久性地修改模型权重：

```python
def get_orthogonalized_matrix(matrix, vec):
    proj = einops.einsum(matrix, vec.view(-1, 1), "... d_model, d_model single -> ... single") * vec
    return matrix - proj
```

修改的权重矩阵包括：
- `model.W_E`: 词嵌入权重
- `block.attn.W_O`: 注意力输出权重
- `block.mlp.W_out`: MLP输出权重

## 🔧参数配置

### 关键参数

- `n_inst_train = 256`: 训练样本数量
- `batch_size = 32`: 批处理大小
- `N_INST_TEST = 4`: 测试样本数量
- `EVAL_N = 20`: 评估的候选方向数量
- `LAYER_CANDIDATE = 10`: 选择的最优候选方向索引

### 内存优化参数

- 激活缓存到CPU以节省GPU内存
- 定期调用垃圾回收和CUDA缓存清理
- 批处理大小可根据硬件配置调整

## 输出文件

- `qwen2.5-1.5B-Instruct-abliterated/`: 修改后的模型目录
  - 包含模型权重、配置文件和分词器
  - 可直接用于推理或进一步分析

## 📊结果分析

程序会输出三种类型的生成结果：

1. **BASELINE COMPLETION**: 原始模型的回复（通常包含拒绝语句）
2. **INTERVENTION COMPLETION**: 临时干预后的回复
3. **ORTHOGONALIZED COMPLETION**: 权重修改后的回复

## ⚠️注意事项

### 安全考虑

- 本工具会移除模型的安全防护机制
- 修改后的模型可能生成有害、不当或危险的内容
- 请确保在安全的环境中使用，并不要将修改后的模型用于生产环境

### 技术限制

- 权重修改是不可逆的，建议在修改前备份原始模型
- 效果可能因数据集质量和模型版本而异
- 需要大量GPU内存进行激活收集和模型推理
- 模型支撑清单：

## 技术细节

### 内存管理

- 使用`torch.set_grad_enabled(False)`关闭自动微分以节省内存
- 激活缓存到CPU设备以避免GPU内存溢出
- 定期清理缓存和垃圾回收

### 设备兼容性

- 自动检测和处理不同设备间的张量转换
- 支持CPU-only和GPU加速环境
- 针对不同硬件配置优化批处理大小

## 📚引用

如果您在研究中使用了此工具，请引用相关的表示工程和模型安全研究论文。

### 🔬  核心技术博客文章
- **[Uncensor any LLM with abliteration](https://huggingface.co/blog/mlabonne/abliteration)** - 本项目的主要技术依据，详细介绍了Abliteration技术的原理和实现方法


### 🤖 支持的模型清单

本Abliteration技术支持以下模型的去安全限制操作：

| 模型系列 | 支持的模型 | 备注 |
|---------|-----------|------|
| **GPT系列** | gpt2, gpt2-medium, gpt2-large, gpt2-xl, distilgpt2 | OpenAI经典模型 |
| **Meta OPT** | facebook/opt-125m, facebook/opt-1.3b, facebook/opt-2.7b, facebook/opt-6.7b, facebook/opt-13b, facebook/opt-30b, facebook/opt-66b | Meta开源模型 |
| **EleutherAI GPT-Neo** | EleutherAI/gpt-neo-125M, EleutherAI/gpt-neo-1.3B, EleutherAI/gpt-neo-2.7B | 社区训练模型 |
| **EleutherAI GPT-J** | EleutherAI/gpt-j-6B | 6B参数模型 |
| **EleutherAI GPT-NeoX** | EleutherAI/gpt-neox-20b | 20B参数大模型 |
| **EleutherAI Pythia** | EleutherAI/pythia-14m ~ EleutherAI/pythia-12b | 完整Pythia系列(含去重版本) |
| **Stanford CRFM** | stanford-crfm/alias-gpt2-small-x21 等 | 研究用GPT2变体 |
| **Meta Llama 1** | llama-7b-hf, llama-13b-hf, llama-30b-hf, llama-65b-hf | 原版Llama模型 |
| **Meta Llama 2** | meta-llama/Llama-2-7b-hf, meta-llama/Llama-2-13b-hf, meta-llama/Llama-2-70b-chat-hf | Llama 2系列 |
| **Meta Llama 3/3.1/3.2/3.3** | meta-llama/Meta-Llama-3-8B, meta-llama/Llama-3.1-8B-Instruct 等 | 最新Llama系列 |
| **CodeLlama** | codellama/CodeLlama-7b-hf, codellama/CodeLlama-7b-Python-hf, codellama/CodeLlama-7b-Instruct-hf | 代码专用模型 |
| **Qwen 1.0** ⭐ | Qwen/Qwen-1_8B, Qwen/Qwen-7B, Qwen/Qwen-14B 等 | 阿里云通义千问 |
| **Qwen 1.5** ⭐ | Qwen/Qwen1.5-0.5B ~ Qwen/Qwen1.5-14B | Qwen 1.5系列 |
| **Qwen 2.0** ⭐ | Qwen/Qwen2-0.5B ~ Qwen/Qwen2-7B | Qwen 2.0系列 |
| **Qwen 2.5** ⭐ | Qwen/Qwen2.5-0.5B ~ Qwen/Qwen2.5-72B | 本项目重点支持 |
| **QwQ** | Qwen/QwQ-32B-Preview | 思维链推理模型 |
| **Microsoft Phi** | microsoft/phi-1, microsoft/phi-1_5, microsoft/phi-2, microsoft/Phi-3-mini-4k-instruct, microsoft/phi-4 | 微软小型模型 |
| **Google Gemma** | google/gemma-2b, google/gemma-7b, google/gemma-2-9b, google/gemma-2-27b 等 | Google开源模型 |
| **Google T5** | google-t5/t5-small, google-t5/t5-base, google-t5/t5-large | 文本转换模型 |
| **Google BERT** | google-bert/bert-base-cased 等 | 预训练语言模型 |
| **Mistral** | mistralai/Mistral-7B-v0.1, mistralai/Mixtral-8x7B-v0.1 等 | Mistral AI模型 |
| **BigScience BLOOM** | bigscience/bloom-560m ~ bigscience/bloom-7b1 | 多语言大模型 |
| **01.AI Yi** | 01-ai/Yi-6B, 01-ai/Yi-34B | 零一万物模型 |
| **StabilityAI** | stabilityai/stablelm-base-alpha-3b 等 | Stability AI模型 |
| **TinyStories** | roneneldan/TinyStories-1M ~ roneneldan/TinyStories-33M | 小型故事模型 |
| **NeelNanda研究** | NeelNanda/SoLU_1L_v9_old 等 | 机制解释性研究模型 |
| **其他特殊** | bigcode/santacoder, ai-forever/mGPT, Baidicoot/Othello-GPT-Transformer-Lens | 代码/多语言/游戏AI |

---
