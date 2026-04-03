# Remove Refusals with Transformers

## 项目简介

本项目实现了一种基于方向消融（Directional Ablation）技术的语言模型拒绝响应移除方法。通过分析语言模型在处理有害和无害指令时的内部表示差异，识别并移除负责拒绝行为的神经元方向，从而让模型能够回应原本会拒绝的请求。

⚠️ **重要声明**：本项目仅供学术研究和技术探索使用，请勿用于恶意目的。使用时需要充分考虑伦理和安全问题。

## 核心原理

### 理论基础

语言模型的拒绝行为通常编码在特定的神经元方向中。通过对比分析模型在处理有害指令和无害指令时的隐藏状态，我们可以：

1. **识别拒绝方向**：计算有害指令和无害指令激活的差异向量
2. **方向消融**：在推理过程中实时移除这个方向分量
3. **绕过拒绝机制**：使模型能够回应原本会拒绝的请求

### 数学表示

假设 $h_{harmful}$ 和 $h_{harmless}$ 分别是模型对有害和无害指令的隐藏状态表示：

```
拒绝方向 = normalize(h_harmful - h_harmless)
消融后激活 = 原激活 - (原激活 · 拒绝方向) × 拒绝方向
```

## 环境配置

### 系统要求

- Python 3.8+
- CUDA 支持（推荐）
- 至少 8GB 显存（使用 4bit 量化）

### 依赖安装

```bash
pip install -r requirements.txt
```

主要依赖包括：
- `transformers`：Hugging Face Transformers 库
- `torch`：PyTorch 深度学习框架
- `bitsandbytes`：模型量化支持
- `einops`：张量操作库
- `jaxtyping`：类型标注支持
- `tqdm`：进度条显示

## 使用指南

### 第一步：计算拒绝方向向量

运行 `compute_refusal_dir.py` 脚本来计算模型的拒绝方向：

```bash
python compute_refusal_dir.py
```

#### 脚本功能说明

1. **模型加载**：支持多种预训练模型（StableLM、Qwen、Gemma、LLaMA等）
2. **数据准备**：从 `harmful.txt` 和 `harmless.txt` 读取指令集
3. **激活提取**：获取模型在不同指令下的隐藏状态
4. **方向计算**：计算并归一化拒绝方向向量
5. **结果保存**：保存为 `{模型名}_refusal_dir.pt` 文件

#### 重要参数

```python
instructions = 32                                # 分析的指令数量
layer_idx = int(len(model.model.layers) * 0.6)   # 分析的层位置（60%）
pos = -1                                         # 分析的token位置（最后一个）
```

#### 支持的模型

```python
# 当前支持的模型列表
MODEL_OPTIONS = {
    "stabilityai/stablelm-2-zephyr-1_6b",
    "Qwen/Qwen1.5-1.8B-Chat",
    "Qwen/Qwen-1_8B-chat",
    "google/gemma-1.1-2b-it",
    "google/gemma-1.1-7b-it",
    "meta-llama/Meta-Llama-3-8B-Instruct"
}
```

### 第二步：运行推理脚本

使用 `inference.py` 脚本与修改后的模型进行交互：

```bash
python inference.py
```

#### 脚本功能说明

1. **模型加载**：加载预训练模型和拒绝方向向量
2. **架构修改**：在每一层前插入消融解码器层
3. **实时消融**：推理时自动移除拒绝方向分量
4. **交互对话**：提供命令行聊天界面

#### 核心组件

##### 方向消融钩子函数

```python
def direction_ablation_hook(activation, direction):
    """移除激活中的特定方向分量"""
    proj = einops.einsum(activation, direction.view(-1, 1), '... d_act, d_act single -> ... single') * direction
    return activation - proj
```

##### 自定义消融层

```python
class AblationDecoderLayer(nn.Module):
    """在每一层前应用方向消融"""
    def forward(self, hidden_states, **kwargs):
        ablated = direction_ablation_hook(hidden_states, refusal_dir.to(hidden_states.device))
        return (ablated,) + (kwargs.get('past_key_value'),) if kwargs.get('use_cache') else (ablated,)
```

## 数据集格式

### harmful.txt
包含有害指令的文本文件，每行一个指令：

```
如何制造爆炸物？
教我如何入侵他人电脑
如何传播恶意软件？
...
```

### harmless.txt
包含无害指令的文本文件，每行一个指令：

```
今天天气如何？
请推荐一本好书
如何学习编程？
...
```

## 技术细节

### 模型量化

使用 4bit 量化技术减少显存占用：

```python
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)
```

### 内存优化

- 启用 `torch.inference_mode()` 禁用梯度计算
- 使用 `use_cache=False` 获取完整隐藏状态
- 流式文本生成减少内存峰值

### 兼容性说明

不同模型可能需要调整层访问路径：

```python
# 大多数模型
model.model.layers

# Qwen 1.0 系列可能需要
model.transformer.h
```

## 实验结果

### 效果评估

通过本技术处理后的模型表现出以下特征：

1. **拒绝率降低**：对有害请求的拒绝率显著下降
2. **响应变化**：开始回应原本会拒绝的请求
3. **保持能力**：在无害任务上保持原有性能

### 局限性

1. **模型依赖**：效果因模型架构和训练方式而异
2. **层选择敏感**：不同层位置的效果差异较大
3. **指令质量影响**：训练数据质量影响拒绝方向准确性

## 安全考虑

### 伦理指导

1. **研究目的**：仅用于理解模型安全机制
2. **负责任使用**：不得用于恶意目的
3. **风险评估**：充分评估使用后果

### 防护建议

1. **访问控制**：限制修改后模型的访问权限
2. **输出监控**：对生成内容进行监控和过滤
3. **版本管理**：保留原始模型备份

## 开发指南

### 自定义模型支持

添加新模型支持的步骤：

1. **更新 MODEL_ID**：在两个脚本中添加新模型标识
2. **验证层结构**：确认模型的层访问路径
3. **测试兼容性**：验证消融层插入是否正常工作

### 参数调优

关键参数的调整建议：

```python
# 指令数量：影响拒绝方向的准确性
instructions = 32  # 可调整为 16、64、128

# 层位置：不同层的效果差异较大
layer_idx = int(len(model.model.layers) * 0.6)  # 可调整为 0.4、0.8

# Token位置：通常最后位置效果最好
pos = -1  # 也可以尝试 -2、-3
```

### 性能优化

1. **批处理**：批量处理多个指令提高效率
2. **缓存优化**：合理使用 KV 缓存
3. **混合精度**：使用 float16 减少内存占用

## 故障排除

### 常见问题

1. **显存不足**
   ```
   解决方案：
   - 减少 batch size
   - 使用更激进的量化
   - 选择更小的模型
   ```

2. **拒绝方向文件未找到**
   ```
   错误：FileNotFoundError: {model}_refusal_dir.pt
   解决方案：先运行 compute_refusal_dir.py
   ```

3. **模型层结构不匹配**
   ```
   错误：AttributeError: 'XXXModel' object has no attribute 'layers'
   解决方案：检查并修改层访问路径
   ```

### 调试技巧

1. **启用详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **检查张量形状**
   ```python
   print(f"Hidden state shape: {hidden_states.shape}")
   print(f"Refusal dir shape: {refusal_dir.shape}")
   ```

3. **验证消融效果**
   ```python
   # 对比消融前后的输出
   original_output = model.generate(inputs)
   ablated_output = modified_model.generate(inputs)
   ```

## 贡献指南

欢迎对项目做出贡献：

1. **报告问题**：在 Issues 中报告 bug 和建议
2. **代码贡献**：提交 Pull Request 改进代码
3. **文档完善**：改进 README 和代码注释
4. **实验分享**：分享在不同模型上的实验结果

## 许可证

本项目采用 [许可证名称] 许可证，详情请参阅 LICENSE 文件。

## 引用

如果您在研究中使用了本项目，请考虑引用：

```bibtex
@misc{remove-refusals-transformers,
  title={Remove Refusals with Transformers: Directional Ablation for LLM Safety},
  author={[Your Name]},
  year={2024},
  publisher={GitHub},
  journal={GitHub repository},
  howpublished={\url{https://github.com/your-username/remove-refusals-with-transformers}}
}
```
