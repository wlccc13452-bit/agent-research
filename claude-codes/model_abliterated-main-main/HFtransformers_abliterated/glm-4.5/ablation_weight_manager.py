# 权重直接修改的消融管理器
from ast import pattern
import torch
import torch.nn as nn
import functools
import einops
from datasets import load_dataset
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer
from accelerate import infer_auto_device_map
from accelerate import init_empty_weights
from transformers.utils import logging
import os
import glob
from datetime import datetime
import json
import traceback

class RefusalAblationWeightManager:
    def __init__(self, model):
        self.model = model
        self.original_weights = {}  # 存储原始权重
        self.ablated_layers = set()  # 记录已消融的层
        
    def apply_weight_ablation(self, layer_idx: int, refusal_direction: torch.Tensor, ablation_strength: float = 5.0):
        """直接修改权重实现消融 - 基于验证过的实现"""
        print(f"对第{layer_idx}层应用权重消融 (强度: {ablation_strength}x)...")
        
        # 获取目标层
        target_layer = self.model.model.layers[layer_idx]
        
        # 确保refusal_direction在正确的设备和数据类型上
        device = next(target_layer.parameters()).device
        dtype = next(target_layer.parameters()).dtype
        refusal_direction = refusal_direction.to(device=device, dtype=dtype)
        
        # 备份原始权重（如果还没备份过）
        if layer_idx not in self.original_weights:
            self.original_weights[layer_idx] = {}
            
            # 备份注意力层权重
            if hasattr(target_layer, 'self_attn'):
                if hasattr(target_layer.self_attn, 'query_key_value'):
                    # GLM格式：合并的QKV权重
                    self.original_weights[layer_idx]['query_key_value'] = target_layer.self_attn.query_key_value.weight.data.clone()
                else:
                    # 分离的Q, K, V权重
                    if hasattr(target_layer.self_attn, 'q_proj'):
                        self.original_weights[layer_idx]['q_proj'] = target_layer.self_attn.q_proj.weight.data.clone()
                    if hasattr(target_layer.self_attn, 'k_proj'):
                        self.original_weights[layer_idx]['k_proj'] = target_layer.self_attn.k_proj.weight.data.clone()
                    if hasattr(target_layer.self_attn, 'v_proj'):
                        self.original_weights[layer_idx]['v_proj'] = target_layer.self_attn.v_proj.weight.data.clone()
                
                # 输出投影
                if hasattr(target_layer.self_attn, 'dense'):
                    self.original_weights[layer_idx]['attn_output'] = target_layer.self_attn.dense.weight.data.clone()
                elif hasattr(target_layer.self_attn, 'o_proj'):
                    self.original_weights[layer_idx]['attn_output'] = target_layer.self_attn.o_proj.weight.data.clone()
            
            # 备份MLP层权重 - 使用原版本的简化逻辑
            if hasattr(target_layer, 'mlp'):
                # GLM格式的MLP
                if hasattr(target_layer.mlp, 'dense_h_to_4h'):
                    self.original_weights[layer_idx]['mlp_up'] = target_layer.mlp.dense_h_to_4h.weight.data.clone()
                if hasattr(target_layer.mlp, 'dense_4h_to_h'):
                    self.original_weights[layer_idx]['mlp_down'] = target_layer.mlp.dense_4h_to_h.weight.data.clone()
                
                # Llama格式的MLP
                if hasattr(target_layer.mlp, 'up_proj'):
                    self.original_weights[layer_idx]['mlp_up'] = target_layer.mlp.up_proj.weight.data.clone()
                if hasattr(target_layer.mlp, 'down_proj'):
                    self.original_weights[layer_idx]['mlp_down'] = target_layer.mlp.down_proj.weight.data.clone()
                if hasattr(target_layer.mlp, 'gate_proj'):
                    self.original_weights[layer_idx]['mlp_gate'] = target_layer.mlp.gate_proj.weight.data.clone()
        
        # 应用权重消融
        self._apply_ablation_to_weights(layer_idx, refusal_direction, ablation_strength)
        self.ablated_layers.add(layer_idx)
        
        print(f"✅ 第{layer_idx}层权重消融完成")
    
    def _apply_ablation_to_weights(self, layer_idx: int, refusal_direction: torch.Tensor, ablation_strength: float = 5.0):
        """对权重矩阵应用消融 - 基于原版本的逻辑"""
        target_layer = self.model.model.layers[layer_idx]
        
        # 归一化refusal_direction
        refusal_direction = refusal_direction / refusal_direction.norm()
        
        print(f"  拒绝方向向量范数: {refusal_direction.norm().item():.6f}")
        print(f"  拒绝方向前5个元素: {refusal_direction[:5].tolist()}")
        
        # 处理注意力层 - 使用原版本的逻辑
        if hasattr(target_layer, 'self_attn'):
            if hasattr(target_layer.self_attn, 'query_key_value'):
                # GLM格式：合并的QKV权重
                self._ablate_weight_matrix(
                    target_layer.self_attn.query_key_value.weight,
                    refusal_direction,
                    "query_key_value",
                    ablation_strength
                )
            else:
                # 分离的Q, K, V权重
                if hasattr(target_layer.self_attn, 'q_proj'):
                    self._ablate_weight_matrix(
                        target_layer.self_attn.q_proj.weight,
                        refusal_direction,
                        "q_proj",
                        ablation_strength
                    )
                if hasattr(target_layer.self_attn, 'k_proj'):
                    self._ablate_weight_matrix(
                        target_layer.self_attn.k_proj.weight,
                        refusal_direction,
                        "k_proj",
                        ablation_strength
                    )
                if hasattr(target_layer.self_attn, 'v_proj'):
                    self._ablate_weight_matrix(
                        target_layer.self_attn.v_proj.weight,
                        refusal_direction,
                        "v_proj",
                        ablation_strength
                    )
    
            # 注意力输出投影 - 使用原版本的维度适配逻辑
            attn_out_weight = None
            if hasattr(target_layer.self_attn, 'dense'):
                attn_out_weight = target_layer.self_attn.dense.weight
            elif hasattr(target_layer.self_attn, 'o_proj'):
                attn_out_weight = target_layer.self_attn.o_proj.weight

            if attn_out_weight is not None:
                in_features = attn_out_weight.shape[1]
                base = refusal_direction.shape[0]

                if in_features == base:
                    eff_dir = refusal_direction
                elif in_features % base == 0:
                    repeat_times = in_features // base
                    eff_dir = refusal_direction.repeat(repeat_times)
                    print(f"    扩展拒绝方向到 {eff_dir.shape} 以匹配attn_output层")
                else:
                    print(f"⚠️  attn_output: 输入维度 {in_features} 与拒绝方向维度 {base} 不可整除，跳过")
                    eff_dir = None

                if eff_dir is not None:
                    self._ablate_weight_matrix(attn_out_weight, eff_dir, "attn_output", ablation_strength)

        # 处理MLP层 - 修复：将MLP处理代码移到正确位置
        if hasattr(target_layer, 'mlp'):
            # GLM格式
            if hasattr(target_layer.mlp, 'dense_h_to_4h'):
                self._ablate_weight_matrix(
                    target_layer.mlp.dense_h_to_4h.weight,
                    refusal_direction,
                    "mlp_up",
                    ablation_strength
                )
            if hasattr(target_layer.mlp, 'dense_4h_to_h'):
                # MLP输出层通常输入维度是4*hidden_dim
                if target_layer.mlp.dense_4h_to_h.weight.shape[1] > refusal_direction.shape[0]:
                    # 需要扩展拒绝方向
                    expansion_factor = target_layer.mlp.dense_4h_to_h.weight.shape[1] // refusal_direction.shape[0]
                    expanded_refusal_dir = refusal_direction.repeat(expansion_factor)
                    print(f"    扩展拒绝方向到 {expanded_refusal_dir.shape} 以匹配MLP输出层")
                    self._ablate_weight_matrix(
                        target_layer.mlp.dense_4h_to_h.weight,
                        expanded_refusal_dir,
                        "mlp_down",
                        ablation_strength
                    )
                else:
                    self._ablate_weight_matrix(
                        target_layer.mlp.dense_4h_to_h.weight,
                        refusal_direction,
                        "mlp_down",
                        ablation_strength
                    )
            
            # Llama格式类似处理
            if hasattr(target_layer.mlp, 'up_proj'):
                self._ablate_weight_matrix(
                    target_layer.mlp.up_proj.weight,
                    refusal_direction,
                    "mlp_up",
                    ablation_strength
                )
            if hasattr(target_layer.mlp, 'down_proj'):
                if target_layer.mlp.down_proj.weight.shape[1] > refusal_direction.shape[0]:
                    expansion_factor = target_layer.mlp.down_proj.weight.shape[1] // refusal_direction.shape[0]
                    expanded_refusal_dir = refusal_direction.repeat(expansion_factor)
                    print(f"    扩展拒绝方向到 {expanded_refusal_dir.shape} 以匹配down_proj层")
                    self._ablate_weight_matrix(
                        target_layer.mlp.down_proj.weight,
                        expanded_refusal_dir,
                        "mlp_down",
                        ablation_strength
                    )
                else:
                    self._ablate_weight_matrix(
                        target_layer.mlp.down_proj.weight,
                        refusal_direction,
                        "mlp_down",
                        ablation_strength
                    )
            if hasattr(target_layer.mlp, 'gate_proj'):
                self._ablate_weight_matrix(
                    target_layer.mlp.gate_proj.weight,
                    refusal_direction,
                    "mlp_gate",
                    ablation_strength
                )

    def _ablate_weight_matrix_old(self, weight_matrix: torch.Tensor, refusal_direction: torch.Tensor, matrix_name: str, ablation_strength: float = 1.0):
        """对单个权重矩阵应用消融 - 基于原版本，增加量化感知"""
        # 确保设备和数据类型匹配
        refusal_direction = refusal_direction.to(device=weight_matrix.device)
        
        if weight_matrix.shape[1] != refusal_direction.shape[0]:
            print(f"⚠️  {matrix_name}: 权重矩阵输入维度 {weight_matrix.shape[1]} 与拒绝方向维度 {refusal_direction.shape[0]} 不匹配，跳过")
            return
        
        # 检查是否为量化权重
        is_quantized = weight_matrix.dtype == torch.float8_e4m3fn
        
        if is_quantized:
            # 量化权重的处理 - 保守但有效的强度
            print(f"    {matrix_name}: 检测到量化权重，使用保守处理")
            
            # 可以尝试稍微提高量化权重的消融强度
            effective_strength = ablation_strength * 0.2  # 从0.1提高到0.2
            
            try:
                # 简单的量化空间消融
                refusal_direction_compatible = refusal_direction.to(dtype=weight_matrix.dtype)
                projections = torch.matmul(weight_matrix.float(), refusal_direction_compatible.float().unsqueeze(1))
                ablation_component = effective_strength * torch.matmul(projections, refusal_direction_compatible.float().unsqueeze(0))
                
                # 应用消融并转换回量化格式
                weight_fp32 = weight_matrix.float() - ablation_component
                weight_matrix.data = weight_fp32.to(torch.float8_e4m3fn)
                
                print(f"    {matrix_name}: 量化权重消融完成 (强度: {effective_strength:.4f})")
            except Exception as e:
                print(f"    {matrix_name}: 量化权重消融失败，跳过: {e}")
        else:
            # 传统浮点权重的处理（与原版本完全一致）
            refusal_direction = refusal_direction.to(dtype=weight_matrix.dtype)
            
            # 计算投影强度
            projections = torch.matmul(weight_matrix, refusal_direction.unsqueeze(1))
            proj_magnitude = projections.abs().mean().item()
            print(f"    {matrix_name}: 投影强度 {proj_magnitude:.6f}")
            
            # 动态调整消融强度
            if proj_magnitude < 0.001:
                effective_strength = ablation_strength * 10
                print(f"    {matrix_name}: 检测到微弱投影，增强消融强度到 {effective_strength}x")
            else:
                effective_strength = ablation_strength
            
            # 计算并应用消融
            ablation_component = effective_strength * torch.matmul(projections, refusal_direction.unsqueeze(0))
            
            original_norm = weight_matrix.norm().item()
            weight_matrix.data -= ablation_component
            ablated_norm = weight_matrix.norm().item()
            
            change_percent = abs(original_norm - ablated_norm) / original_norm * 100
            print(f"    {matrix_name}: 权重范数变化 {change_percent:.4f}% ({original_norm:.6f} -> {ablated_norm:.6f})")

    def _ablate_weight_matrix(self, weight_matrix: torch.Tensor, refusal_direction: torch.Tensor, matrix_name: str, ablation_strength: float = 1.0):
        """对单个权重矩阵应用消融 - 安全的量化权重处理"""
        # 确保设备匹配
        refusal_direction = refusal_direction.to(device=weight_matrix.device)
        
        if weight_matrix.shape[1] != refusal_direction.shape[0]:
            print(f"⚠️  {matrix_name}: 权重矩阵输入维度 {weight_matrix.shape[1]} 与拒绝方向维度 {refusal_direction.shape[0]} 不匹配，跳过")
            return
        
        # 检查是否为量化权重
        is_quantized = weight_matrix.dtype == torch.float8_e4m3fn
        
        if is_quantized:
            print(f"    {matrix_name}: 检测到量化权重，使用最小化干预方法")
            
            try:
                with torch.no_grad():
                    # 在CPU上以FP32精度进行计算
                    weight_cpu_fp32 = weight_matrix.cpu().to(torch.float32)
                    refusal_cpu_fp32 = refusal_direction.cpu().to(torch.float32)
                    
                    # 记录原始统计信息
                    original_max_abs = weight_cpu_fp32.abs().max().item()
                    original_std = weight_cpu_fp32.std().item()
                    original_mean = weight_cpu_fp32.mean().item()
                    
                    print(f"    {matrix_name}: 原始统计 - max_abs: {original_max_abs:.2f}, std: {original_std:.2f}, mean: {original_mean:.6f}")
                    
                    # 计算投影和消融
                    projections = torch.matmul(weight_cpu_fp32, refusal_cpu_fp32.unsqueeze(1))
                    proj_magnitude = projections.abs().mean().item()
                    
                    # 使用你希望的消融强度（不需要过分保守）
                    effective_strength = ablation_strength * 1  # 可以调整这个系数
                    ablation_component = effective_strength * torch.matmul(projections, refusal_cpu_fp32.unsqueeze(0))
                    
                    # 应用消融
                    ablated_weight_cpu = weight_cpu_fp32 - ablation_component
                    
                    # 关键改进：重新缩放到FP8最大范围
                    ablated_max_abs = ablated_weight_cpu.abs().max().item()
                    
                    if ablated_max_abs > 0:  # 避免除零
                        # 计算缩放因子，将最大值缩放回448（FP8的安全最大值）
                        target_max = 448.0  # 或者使用原始的 original_max_abs
                        scale_factor = target_max / ablated_max_abs
                        
                        # 应用等比缩放
                        rescaled_weight_cpu = ablated_weight_cpu * scale_factor
                        
                        # 验证缩放后的统计信息
                        rescaled_max_abs = rescaled_weight_cpu.abs().max().item()
                        rescaled_std = rescaled_weight_cpu.std().item()
                        rescaled_mean = rescaled_weight_cpu.mean().item()
                        
                        print(f"    {matrix_name}: 消融后max_abs: {ablated_max_abs:.2f} -> 重缩放后: {rescaled_max_abs:.2f}")
                        print(f"    {matrix_name}: 缩放因子: {scale_factor:.4f}, std变化: {original_std:.2f} -> {rescaled_std:.2f}")
                        
                        # 最终安全检查
                        if torch.isnan(rescaled_weight_cpu).any() or torch.isinf(rescaled_weight_cpu).any():
                            print(f"    {matrix_name}: 重缩放产生异常值，使用原始权重")
                            return
                        
                        # 转回设备和FP8格式
                        weight_matrix.data = rescaled_weight_cpu.to(device=weight_matrix.device, dtype=torch.float8_e4m3fn)
                        
                        print(f"    {matrix_name}: FP8消融+重缩放完成")
                        
                    else:
                        print(f"    {matrix_name}: 消融后权重为零，跳过重缩放")
                        
            except Exception as e:
                print(f"    {matrix_name}: FP8消融+重缩放失败: {e}")
        else:
            # 浮点权重的正常处理
            refusal_direction = refusal_direction.to(dtype=weight_matrix.dtype)
            
            projections = torch.matmul(weight_matrix, refusal_direction.unsqueeze(1))
            proj_magnitude = projections.abs().mean().item()
            print(f"    {matrix_name}: 投影强度 {proj_magnitude:.6f}")
            
            if proj_magnitude < 0.001:
                effective_strength = ablation_strength * 10
                print(f"    {matrix_name}: 检测到微弱投影，增强消融强度到 {effective_strength}x")
            else:
                effective_strength = ablation_strength
            
            ablation_component = effective_strength * torch.matmul(projections, refusal_direction.unsqueeze(0))
            
            original_norm = weight_matrix.norm().item()
            weight_matrix.data -= ablation_component
            ablated_norm = weight_matrix.norm().item()
            
            change_percent = abs(original_norm - ablated_norm) / original_norm * 100
            print(f"    {matrix_name}: 权重范数变化 {change_percent:.4f}% ({original_norm:.6f} -> {ablated_norm:.6f})")

    def restore_layer(self, layer_idx: int):
        """恢复指定层的原始权重 - 使用原版本的逻辑"""
        if layer_idx not in self.original_weights:
            print(f"⚠️  第{layer_idx}层没有备份权重，无法恢复")
            return
        
        print(f"恢复第{layer_idx}层的原始权重...")
        
        target_layer = self.model.model.layers[layer_idx]
        original_weights = self.original_weights[layer_idx]
        
        # 恢复注意力层权重
        if hasattr(target_layer, 'self_attn'):
            if 'query_key_value' in original_weights:
                target_layer.self_attn.query_key_value.weight.data.copy_(original_weights['query_key_value'])
            
            if 'q_proj' in original_weights:
                target_layer.self_attn.q_proj.weight.data.copy_(original_weights['q_proj'])
            if 'k_proj' in original_weights:
                target_layer.self_attn.k_proj.weight.data.copy_(original_weights['k_proj'])
            if 'v_proj' in original_weights:
                target_layer.self_attn.v_proj.weight.data.copy_(original_weights['v_proj'])
            
            if 'attn_output' in original_weights:
                if hasattr(target_layer.self_attn, 'dense'):
                    target_layer.self_attn.dense.weight.data.copy_(original_weights['attn_output'])
                elif hasattr(target_layer.self_attn, 'o_proj'):
                    target_layer.self_attn.o_proj.weight.data.copy_(original_weights['attn_output'])
        
        # 恢复MLP层权重 - 使用原版本的逻辑
        if hasattr(target_layer, 'mlp'):
            if 'mlp_up' in original_weights:
                if hasattr(target_layer.mlp, 'dense_h_to_4h'):
                    target_layer.mlp.dense_h_to_4h.weight.data.copy_(original_weights['mlp_up'])
                elif hasattr(target_layer.mlp, 'up_proj'):
                    target_layer.mlp.up_proj.weight.data.copy_(original_weights['mlp_up'])
            
            if 'mlp_down' in original_weights:
                if hasattr(target_layer.mlp, 'dense_4h_to_h'):
                    target_layer.mlp.dense_4h_to_h.weight.data.copy_(original_weights['mlp_down'])
                elif hasattr(target_layer.mlp, 'down_proj'):
                    target_layer.mlp.down_proj.weight.data.copy_(original_weights['mlp_down'])
            
            if 'mlp_gate' in original_weights and hasattr(target_layer.mlp, 'gate_proj'):
                target_layer.mlp.gate_proj.weight.data.copy_(original_weights['mlp_gate'])
        
        self.ablated_layers.discard(layer_idx)
        print(f"✅ 第{layer_idx}层权重已恢复")
    
    def restore_all_layers(self):
        """恢复所有层的原始权重"""
        for layer_idx in list(self.ablated_layers):
            self.restore_layer(layer_idx)
        print("✅ 所有层权重已恢复")
    
    def get_ablated_layers(self):
        """获取当前已消融的层"""
        return list(self.ablated_layers)
    
    def apply_multiple_layers_ablation(self, layer_indices: list, refusal_directions: list, ablation_strength: float = 5.0):
        """对多个层同时应用消融"""
        print(f"对多个层应用权重消融: {layer_indices}")
        
        for layer_idx, refusal_dir in zip(layer_indices, refusal_directions):
            self.apply_weight_ablation(layer_idx, refusal_dir, ablation_strength=ablation_strength)
        
        print(f"✅ 多层权重消融完成，共消融 {len(layer_indices)} 层")