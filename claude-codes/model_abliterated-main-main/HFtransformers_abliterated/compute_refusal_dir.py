import jaxtyping
import random
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer, BitsAndBytesConfig
import einops
from tqdm import tqdm

"""计算拒绝方向向量的脚本

此脚本用于计算语言模型中负责拒绝有害请求的神经元方向。
通过对比分析有害指令和无害指令在模型隐藏层的激活模式，
提取出代表"拒绝行为"的方向向量，用于后续的方向消融。
"""

# 启用推理模式，禁用梯度计算以节省内存和加速
torch.inference_mode()

# 模型配置 - 可以选择不同的预训练模型
MODEL_ID = "stabilityai/stablelm-2-zephyr-1_6b"  # 当前使用的模型
#MODEL_ID = "Qwen/Qwen1.5-1.8B-Chat"              # 千问1.5对话模型
#MODEL_ID = "Qwen/Qwen-1_8B-chat"                 # 千问1.8B对话模型
#MODEL_ID = "google/gemma-1.1-2b-it"              # Google Gemma 2B指令调优版
#MODEL_ID = "google/gemma-1.1-7b-it"              # Google Gemma 7B指令调优版
#MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct" # Meta Llama-3 8B指令版

# 加载模型，使用4位量化以节省显存
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, 
    trust_remote_code=True,           # 允许执行自定义代码
    torch_dtype=torch.float16,       # 使用半精度浮点数
    quantization_config=BitsAndBytesConfig(
        load_in_4bit=True,            # 启用4位量化
        bnb_4bit_compute_dtype=torch.float16  # 计算时使用的数据类型
    )
)

# 加载对应的分词器
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)

# ===== 算法参数设置 =====
instructions = 32                                    # 对比分析使用的指令数量（有害/无害各32条）
layer_idx = int(len(model.model.layers) * 0.6)      # 选择模型60%位置的层进行分析
pos = -1                                            # 使用序列最后一个token的位置（-1表示最后位置）

print("Instruction count: " + str(instructions))     # 打印指令数量
print("Layer index: " + str(layer_idx))             # 打印选定的层索引

# ===== 加载数据集 =====
# 读取有害指令集（包含敏感、有害的请求）
with open("harmful.txt", "r") as f:
    harmful = f.readlines()

# 读取无害指令集（包含正常、安全的请求）
with open("harmless.txt", "r") as f:
    harmless = f.readlines()

# 从两个数据集中随机采样指定数量的指令进行对比
harmful_instructions = random.sample(harmful, instructions)    # 随机选择32条有害指令
harmless_instructions = random.sample(harmless, instructions)  # 随机选择32条无害指令

# ===== 准备输入数据 =====
# 将有害指令转换为模型输入格式（添加对话模板和生成提示）
harmful_toks = [
    tokenizer.apply_chat_template(
        conversation=[{"role": "user", "content": insn}], 
        add_generation_prompt=True,      # 添加生成提示符
        return_tensors="pt"              # 返回PyTorch张量格式
    ) for insn in harmful_instructions
]

# 将无害指令转换为模型输入格式
harmless_toks = [
    tokenizer.apply_chat_template(
        conversation=[{"role": "user", "content": insn}], 
        add_generation_prompt=True,      # 添加生成提示符
        return_tensors="pt"              # 返回PyTorch张量格式
    ) for insn in harmless_instructions
]

# ===== 模型推理和隐藏状态提取 =====
max_its = instructions * 2               # 总共需要处理的指令数量（有害+无害）
bar = tqdm(total=max_its)               # 创建进度条

def generate(toks):
    """生成单个token并返回隐藏状态
    
    Args:
        toks: 输入的token张量
    
    Returns:
        包含隐藏状态的生成结果
    """
    bar.update(n=1)                     # 更新进度条
    return model.generate(
        toks.to(model.device), 
        use_cache=False,                 # 禁用缓存以获取完整隐藏状态
        max_new_tokens=1,               # 只生成一个新token
        return_dict_in_generate=True,   # 返回字典格式结果
        output_hidden_states=True       # 输出隐藏状态用于分析
    )

# 对所有有害指令进行推理，获取隐藏状态
harmful_outputs = [generate(toks) for toks in harmful_toks]

# 对所有无害指令进行推理，获取隐藏状态
harmless_outputs = [generate(toks) for toks in harmless_toks]

bar.close()  # 关闭进度条

# ===== 提取指定层的隐藏状态 =====
# 从有害指令的输出中提取指定层、指定位置的隐藏状态向量
harmful_hidden = [output.hidden_states[0][layer_idx][:, pos, :] for output in harmful_outputs]

# 从无害指令的输出中提取指定层、指定位置的隐藏状态向量
harmless_hidden = [output.hidden_states[0][layer_idx][:, pos, :] for output in harmless_outputs]

print(harmful_hidden)  # 打印有害指令的隐藏状态（调试用）

# ===== 计算平均激活向量 =====
# 计算所有有害指令隐藏状态的平均值
harmful_mean = torch.stack(harmful_hidden).mean(dim=0)

# 计算所有无害指令隐藏状态的平均值
harmless_mean = torch.stack(harmless_hidden).mean(dim=0)

print(harmful_mean)  # 打印有害指令的平均激活向量（调试用）

# ===== 计算拒绝方向向量 =====
# 计算有害和无害指令激活的差异向量，这代表了"拒绝方向"
refusal_dir = harmful_mean - harmless_mean

# 对拒绝方向向量进行归一化（单位化），确保只保留方向信息
refusal_dir = refusal_dir / refusal_dir.norm()

print(refusal_dir)  # 打印最终的拒绝方向向量（调试用）

# ===== 保存拒绝方向向量 =====
# 将计算得到的拒绝方向向量保存到文件，供后续推理使用
filename = MODEL_ID.replace("/", "_") + "_refusal_dir.pt"
torch.save(refusal_dir, filename)
print(f"拒绝方向向量已保存到: {filename}")
