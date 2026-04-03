from typing import Optional, Tuple

import einops
import jaxtyping
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer, BitsAndBytesConfig

torch.inference_mode()

# torch.set_default_device("cpu")  # 建议注释掉这行避免设备冲突

MODEL_ID = "../Qwen/Qwen2.5-1.5B-Instruct"

# 修改量化配置，统一使用 bfloat16
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, 
    trust_remote_code=True, 
    device_map="cuda", 
    quantization_config=BitsAndBytesConfig(
        load_in_4bit=True, 
        bnb_4bit_compute_dtype=torch.bfloat16  # 改为 bfloat16
    ),
    torch_dtype=torch.bfloat16  # 添加明确的数据类型指定
)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)

# 加载拒绝方向并确保数据类型正确
refusal_dir = torch.load(MODEL_ID.replace("/", "_") + "_refusal_dir.pt")
refusal_dir = refusal_dir.to(torch.bfloat16)  # 确保数据类型匹配


def direction_ablation_hook(activation: jaxtyping.Float[torch.Tensor, "... d_act"],
                            direction: jaxtyping.Float[torch.Tensor, "d_act"]):
    # 确保数据类型匹配
    if direction.dtype != activation.dtype:
        direction = direction.to(activation.dtype)
    
    proj = einops.einsum(activation, direction.view(-1, 1), '... d_act, d_act single -> ... single') * direction
    return activation - proj


class AblationDecoderLayer(nn.Module):
    def __init__(self, refusal_direction=None):
        super().__init__()
        if refusal_direction is not None:
            self.register_buffer('refusal_direction', refusal_direction.to(torch.bfloat16))
        else:
            self.refusal_direction = None
    
    def forward(
            self,
            hidden_states: torch.Tensor,
            attention_mask: Optional[torch.Tensor] = None,
            position_ids: Optional[torch.LongTensor] = None,
            past_key_value: Optional[Tuple[torch.Tensor]] = None,
            output_attentions: Optional[bool] = False,
            use_cache: Optional[bool] = False,
            cache_position: Optional[torch.LongTensor] = None,
            **kwargs,
    ) -> Tuple[torch.FloatTensor, Optional[Tuple[torch.FloatTensor, torch.FloatTensor]]]:
        assert not output_attentions

        # 使用实例方向或全局方向，并确保数据类型正确
        direction = self.refusal_direction if self.refusal_direction is not None else refusal_dir
        direction = direction.to(hidden_states.dtype).to(hidden_states.device)
        
        ablated = direction_ablation_hook(hidden_states, direction)

        outputs = (ablated,)

        if use_cache:
            outputs += (past_key_value,)

        return outputs

print(f"模型总层数: {len(model.model.layers)}")

# 加载层分析结果以选择第3个最有效的层
try:
    # 尝试加载完整分析结果
    analysis_results = torch.load(MODEL_ID.replace("/", "_") + "_layer_analysis.pt")
    # 使用综合评分排序的第3个层（索引2，即第18层）
    best_layer = analysis_results['sorted_by_combined'][2]['layer']
    # 同时使用对应的拒绝方向向量
    best_refusal_dir = analysis_results['sorted_by_combined'][2]['refusal_dir']
    print(f"使用分析结果中排名第3的层: {best_layer}")
except FileNotFoundError:
    best_layer = 18  # 默认使用第18层
    best_refusal_dir = refusal_dir  # 使用默认拒绝方向
    print(f"未找到分析结果文件，使用默认层: {best_layer}")

# 创建消融层时传入对应的拒绝方向
# model.model.layers.insert(best_layer, AblationDecoderLayer(refusal_dir))
model.model.layers[best_layer] = AblationDecoderLayer(best_refusal_dir)

conversation = []

streamer = TextStreamer(tokenizer)

print(f"Chat with {MODEL_ID}:")
print("输入 'quit' 或 'exit' 退出聊天")

while True:
    try:
        prompt = input("用户: ")
        if prompt.lower() in ['quit', 'exit', '退出', 'q']:
            print("再见！")
            break
        
        conversation.append({"role": "user", "content": prompt})
        toks = tokenizer.apply_chat_template(
            conversation=conversation,
            add_generation_prompt=True, 
            return_tensors="pt"
        )

        print("助手: ", end="")
        gen = model.generate(
            toks.to(model.device), 
            streamer=streamer, 
            max_new_tokens=512,  # 减少生成长度
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

        decoded = tokenizer.batch_decode(
            gen[0][len(toks[0]):], 
            skip_special_tokens=True
        )
        conversation.append({"role": "assistant", "content": "".join(decoded)})
        
    except KeyboardInterrupt:
        print("\n用户中断，退出聊天")
        break
    except Exception as e:
        print(f"发生错误: {e}")
        continue
