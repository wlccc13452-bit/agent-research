"""
推理脚本 - 使用方向消融技术移除语言模型的拒绝响应机制

这个脚本实现了在推理过程中实时移除语言模型拒绝响应行为的功能。
核心思想是通过方向消融技术，在模型的每一层中移除预先计算好的"拒绝方向"，
使得模型能够回应原本会拒绝的请求。

主要功能：
1. 加载预训练的语言模型和对应的拒绝方向向量
2. 在模型的每一层前插入消融层，实时移除拒绝方向
3. 提供交互式聊天界面与修改后的模型进行对话

注意：此技术仅用于研究目的，使用时需要考虑伦理和安全问题。
"""
from typing import Optional, Tuple

import einops
import jaxtyping
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer, BitsAndBytesConfig

# ==================== 基本配置设置 ====================

# 设置推理模式，禁用梯度计算以提高性能和节省内存
torch.inference_mode()

# 设置默认设备为CPU（虽然后面会指定CUDA设备）
torch.set_default_device("cpu")

# ==================== 模型配置 ====================

# 选择要使用的预训练模型
# 当前使用的是 Stability AI 的 StableLM-2-Zephyr-1.6B 模型
MODEL_ID = "stabilityai/stablelm-2-zephyr-1_6b"

# 其他可选的模型配置（已注释）
#MODEL_ID = "Qwen/Qwen1.5-1.8B-Chat"     # 通义千问1.5系列
#MODEL_ID = "Qwen/Qwen-1_8B-chat"        # 通义千问1.0系列
#MODEL_ID = "google/gemma-1.1-2b-it"     # Google Gemma 2B 指令微调版
#MODEL_ID = "google/gemma-1.1-7b-it"     # Google Gemma 7B 指令微调版
#MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"  # Meta LLaMA 3 8B 指令版

# ==================== 模型和分词器加载 ====================

# 加载预训练的因果语言模型
# 使用4位量化配置以节省显存，并指定使用CUDA设备
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, 
    trust_remote_code=True,  # 信任远程代码（某些模型需要）
    device_map="cuda",       # 指定使用CUDA设备
    quantization_config=BitsAndBytesConfig(
        load_in_4bit=True,                      # 启用4位量化
        bnb_4bit_compute_dtype=torch.float16    # 计算时使用float16精度
    )
)

# 加载对应的分词器
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)

# ==================== 加载拒绝方向向量 ====================

# 加载预先计算好的拒绝方向向量
# 这个向量是通过 compute_refusal_dir.py 脚本生成的
# 文件名格式：模型名（替换"/"为"_"）+ "_refusal_dir.pt"
refusal_dir = torch.load(MODEL_ID.replace("/", "_") + "_refusal_dir.pt")

# ==================== 方向消融核心函数 ====================

def direction_ablation_hook(activation: jaxtyping.Float[torch.Tensor, "... d_act"],
                            direction: jaxtyping.Float[torch.Tensor, "d_act"]):
    """
    方向消融钩子函数
    
    这个函数实现了方向消融的核心算法，用于从激活张量中移除特定方向的分量。
    
    算法原理：
    1. 计算激活在拒绝方向上的投影：proj = (activation · direction) * direction
    2. 从原激活中减去这个投影：result = activation - proj
    3. 这样就移除了激活中沿拒绝方向的分量
    
    参数：
        activation: 输入的激活张量，形状为 [..., d_act]
        direction: 要移除的方向向量，形状为 [d_act]
    
    返回：
        消融后的激活张量，与输入激活具有相同的形状
    """
    # 使用 einops 进行高效的张量乘法计算投影
    # '... d_act, d_act single -> ... single' 表示对最后一维进行点积
    proj = einops.einsum(activation, direction.view(-1, 1), '... d_act, d_act single -> ... single') * direction
    
    # 从原激活中减去投影，实现方向消融
    return activation - proj

# ==================== 自定义消融解码器层 ====================

class AblationDecoderLayer(nn.Module):
    """
    消融解码器层
    
    这是一个自定义的神经网络层，专门用于在模型推理过程中实现方向消融。
    该层会被插入到原始模型的每一层之前，确保在每次前向传播时都移除拒绝方向。
    
    这个层的设计遵循了 Transformers 库中解码器层的接口规范，
    以确保与原始模型架构的兼容性。
    """
    
    def forward(
            self,
            hidden_states: torch.Tensor,                           # 隐藏状态张量
            attention_mask: Optional[torch.Tensor] = None,         # 注意力掩码（可选）
            position_ids: Optional[torch.LongTensor] = None,       # 位置编码（可选）
            past_key_value: Optional[Tuple[torch.Tensor]] = None,  # 缓存的键值对（可选）
            output_attentions: Optional[bool] = False,             # 是否输出注意力权重
            use_cache: Optional[bool] = False,                     # 是否使用缓存
            cache_position: Optional[torch.LongTensor] = None,     # 缓存位置（可选）
            **kwargs,                                              # 其他可选参数
    ) -> Tuple[torch.FloatTensor, Optional[Tuple[torch.FloatTensor, torch.FloatTensor]]]:
        """
        前向传播函数
        
        在这个函数中，我们对输入的隐藏状态应用方向消融，
        然后返回消融后的结果。
        """
        # 确保不输出注意力权重（简化实现）
        assert not output_attentions

        # 应用方向消融：移除隐藏状态中的拒绝方向分量
        # 需要确保拒绝方向向量在正确的设备上
        ablated = direction_ablation_hook(
            hidden_states, 
            refusal_dir.to(hidden_states.device)
        ).to(hidden_states.device)

        # 构建输出元组，第一个元素是消融后的隐藏状态
        outputs = (ablated,)

        # 如果使用缓存，需要传递缓存的键值对
        if use_cache:
            outputs += (past_key_value,)

        # 返回输出（类型检查忽略，因为确定类型正确）
        # noinspection PyTypeChecker
        return outputs

# ==================== 模型架构修改 ====================

# 在原始模型的每一层前插入消融解码器层
# 使用反向遍历确保索引不会因为插入操作而混乱
for idx in reversed(range(len(model.model.layers))):
    # 注意：对于 Qwen 1.0 系列模型，可能需要修改为 model.transformer.h
    model.model.layers.insert(idx, AblationDecoderLayer())

# ==================== 用户交互设置 ====================

# 初始化对话历史列表，用于维护多轮对话上下文
conversation = []

# 创建文本流式输出器，用于实时显示模型生成的文本
streamer = TextStreamer(tokenizer)

# ==================== 交互式聊天循环 ====================

# 显示欢迎信息
print(f"Chat with {MODEL_ID}:")

# 开始无限循环，处理用户输入
while True:
    # 获取用户输入
    prompt = input()
    
    # 将用户输入添加到对话历史中
    conversation.append({"role": "user", "content": prompt})
    
    # 使用分词器将对话转换为模型输入格式
    # apply_chat_template 会自动处理对话格式和特殊令牌
    toks = tokenizer.apply_chat_template(
        conversation=conversation,      # 传入完整对话历史
        add_generation_prompt=True,     # 添加生成提示符
        return_tensors="pt"             # 返回 PyTorch 张量
    )

    # 使用修改后的模型生成回复
    gen = model.generate(
        toks.to(model.device),          # 将输入张量移到模型设备上
        streamer=streamer,              # 启用流式输出
        max_new_tokens=1337             # 最大生成1337个新token
    )

    # 解码生成的新token（排除输入部分）
    decoded = tokenizer.batch_decode(
        gen[0][len(toks[0]):],         # 只解码新生成的部分
        skip_special_tokens=True        # 跳过特殊token
    )
    
    # 将模型回复添加到对话历史中
    conversation.append({"role": "assistant", "content": "".join(decoded)})

