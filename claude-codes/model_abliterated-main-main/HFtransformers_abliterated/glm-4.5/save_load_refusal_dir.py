import torch
import os
import json
from datetime import datetime

"""
# 1. 保存当前数据
save_ablation_data(selected_layers, selected_refusal_directions, MODEL_ID, save_dir="./ablation_cache")

# 2. 稍后加载数据
selected_layers, selected_refusal_directions, metadata = quick_load_latest_ablation_data(MODEL_ID, search_dir="./ablation_cache")


# 3. 直接应用消融
apply_saved_ablation(weight_manager, MODEL_ID, ablation_strength=4.2)
"""

def save_ablation_data(selected_layers, selected_refusal_directions, model_id, save_dir=None):
    """
    保存消融数据到磁盘
    
    Args:
        selected_layers: list of int, 选中的层索引
        selected_refusal_directions: list of torch.Tensor, 对应的拒绝方向向量
        model_id: str, 模型标识符
        save_dir: str, 保存目录，默认为None
    
    Returns:
        str: 保存的文件路径
    """
    if save_dir is None:
        save_dir = os.path.dirname(os.path.abspath(__file__))
    
    os.makedirs(save_dir, exist_ok=True)
    
    # 生成文件名
    model_name = model_id.replace("/", "_").replace("-", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"{model_name}_ablation_data_{timestamp}"
    
    # 构造保存数据
    ablation_data = {
        'selected_layers': selected_layers,
        'selected_refusal_directions': selected_refusal_directions,
        'model_id': model_id,
        'timestamp': timestamp,
        'num_layers': len(selected_layers),
        'tensor_shapes': [tensor.shape for tensor in selected_refusal_directions],
        'tensor_dtypes': [str(tensor.dtype) for tensor in selected_refusal_directions],
        'tensor_devices': [str(tensor.device) for tensor in selected_refusal_directions],
        'version': '1.0'
    }
    
    # 保存到.pt文件
    pt_filepath = os.path.join(save_dir, f"{base_filename}.pt")
    torch.save(ablation_data, pt_filepath)
    
    # 同时保存元数据到JSON文件（便于快速查看信息）
    metadata = {
        'model_id': model_id,
        'timestamp': timestamp,
        'num_layers': len(selected_layers),
        'selected_layers': selected_layers,
        'tensor_info': [
            {
                'layer_idx': layer_idx,
                'shape': list(tensor.shape),
                'dtype': str(tensor.dtype),
                'device': str(tensor.device),
                'norm': float(tensor.norm().item())
            }
            for layer_idx, tensor in zip(selected_layers, selected_refusal_directions)
        ],
        'version': '1.0',
        'pt_file': f"{base_filename}.pt"
    }
    
    json_filepath = os.path.join(save_dir, f"{base_filename}_metadata.json")
    with open(json_filepath, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 消融数据已保存:")
    print(f"   数据文件: {pt_filepath}")
    print(f"   元数据文件: {json_filepath}")
    print(f"   层数量: {len(selected_layers)}")
    print(f"   选中层: {selected_layers}")
    
    return pt_filepath, json_filepath

def load_ablation_data(filepath, device='auto'):
    """
    从磁盘加载消融数据
    
    Args:
        filepath: str, .pt文件路径
        device: str or torch.device, 目标设备，'auto'表示自动选择
    
    Returns:
        tuple: (selected_layers, selected_refusal_directions, metadata)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"消融数据文件不存在: {filepath}")
    
    print(f"🔄 加载消融数据: {filepath}")
    
    # 自动选择设备
    if device == 'auto':
        if torch.cuda.is_available():
            device = torch.device('cuda:0')
        else:
            device = torch.device('cpu')
    elif isinstance(device, str):
        device = torch.device(device)
    
    # 加载数据
    ablation_data = torch.load(filepath, map_location=device)
    
    # 验证数据完整性
    required_keys = ['selected_layers', 'selected_refusal_directions', 'model_id', 'version']
    for key in required_keys:
        if key not in ablation_data:
            raise ValueError(f"消融数据文件缺少必要字段: {key}")
    
    selected_layers = ablation_data['selected_layers']
    selected_refusal_directions = ablation_data['selected_refusal_directions']
    
    # 将张量移动到指定设备
    selected_refusal_directions = [tensor.to(device) for tensor in selected_refusal_directions]
    
    print(f"✅ 消融数据加载成功:")
    print(f"   模型ID: {ablation_data['model_id']}")
    print(f"   时间戳: {ablation_data.get('timestamp', 'N/A')}")
    print(f"   版本: {ablation_data.get('version', 'N/A')}")
    print(f"   层数量: {len(selected_layers)}")
    print(f"   选中层: {selected_layers}")
    print(f"   张量设备: {device}")
    
    # 返回元数据
    metadata = {
        'model_id': ablation_data['model_id'],
        'timestamp': ablation_data.get('timestamp'),
        'version': ablation_data.get('version'),
        'num_layers': len(selected_layers),
        'tensor_shapes': ablation_data.get('tensor_shapes'),
        'tensor_dtypes': ablation_data.get('tensor_dtypes')
    }
    
    return selected_layers, selected_refusal_directions, metadata

def list_ablation_files(search_dir=None, model_filter=None):
    """
    列出可用的消融数据文件
    
    Args:
        search_dir: str, 搜索目录，默认为当前目录
        model_filter: str, 模型过滤器，只显示包含此字符串的文件
    
    Returns:
        list: 找到的文件信息列表
    """
    if search_dir is None:
        search_dir = os.path.dirname(os.path.abspath(__file__))
    
    pattern = "*_ablation_data_*.pt"
    import glob
    
    pt_files = glob.glob(os.path.join(search_dir, pattern))
    
    file_info_list = []
    
    for pt_file in pt_files:
        if model_filter and model_filter not in pt_file:
            continue
        
        try:
            # 尝试加载文件获取元数据
            data = torch.load(pt_file, map_location='cpu')
            
            file_info = {
                'filepath': pt_file,
                'filename': os.path.basename(pt_file),
                'model_id': data.get('model_id', 'Unknown'),
                'timestamp': data.get('timestamp', 'Unknown'),
                'num_layers': len(data.get('selected_layers', [])),
                'selected_layers': data.get('selected_layers', []),
                'file_size_mb': os.path.getsize(pt_file) / (1024*1024)
            }
            
            file_info_list.append(file_info)
            
        except Exception as e:
            print(f"⚠️  无法读取文件 {pt_file}: {e}")
    
    # 按时间戳排序
    file_info_list.sort(key=lambda x: x['timestamp'], reverse=True)
    
    print(f"\n📁 找到 {len(file_info_list)} 个消融数据文件:")
    for i, info in enumerate(file_info_list):
        print(f"  {i+1}. {info['filename']}")
        print(f"     模型: {info['model_id']}")
        print(f"     时间: {info['timestamp']}")
        print(f"     层数: {info['num_layers']}")
        print(f"     大小: {info['file_size_mb']:.2f} MB")
        print(f"     选中层: {info['selected_layers'][:10]}{'...' if len(info['selected_layers']) > 10 else ''}")
        print()
    
    return file_info_list

def quick_load_latest_ablation_data(model_id, search_dir=None, device='auto'):
    """
    快速加载指定模型的最新消融数据
    
    Args:
        model_id: str, 模型ID
        search_dir: str, 搜索目录
        device: str, 设备
    
    Returns:
        tuple: (selected_layers, selected_refusal_directions, metadata) 或 None
    """
    model_filter = model_id.replace("/", "_").replace("-", "_")
    files = list_ablation_files(search_dir, model_filter)
    
    if not files:
        print(f"❌ 未找到模型 {model_id} 的消融数据文件")
        return None
    
    latest_file = files[0]['filepath']  # 已按时间排序
    return load_ablation_data(latest_file, device)

"""
# ===== 在你的主代码中使用 =====

# 保存当前的消融数据
print(f"\n💾 保存消融数据...")
pt_filepath, json_filepath = save_ablation_data(
    selected_layers, 
    selected_refusal_directions, 
    MODEL_ID,
    save_dir="./ablation_cache"  # 可以指定保存目录
)

# 示例：稍后加载数据
print(f"\n🔄 演示加载数据...")
try:
    # 方法1：直接加载指定文件
    loaded_layers, loaded_directions, metadata = load_ablation_data(pt_filepath, device='cuda:0')
    
    # 验证加载的数据
    print(f"验证数据完整性:")
    print(f"  原始层数: {len(selected_layers)}, 加载层数: {len(loaded_layers)}")
    print(f"  原始方向数: {len(selected_refusal_directions)}, 加载方向数: {len(loaded_directions)}")
    print(f"  层列表匹配: {selected_layers == loaded_layers}")
    
    # 验证张量数据
    tensors_match = all(
        torch.allclose(orig.cpu(), loaded.cpu(), rtol=1e-5, atol=1e-8) 
        for orig, loaded in zip(selected_refusal_directions, loaded_directions)
    )
    print(f"  张量数据匹配: {tensors_match}")
    
    print("✅ 数据加载验证成功!")
    
except Exception as e:
    print(f"❌ 数据加载失败: {e}")
"""

# 添加便捷函数到你的代码中
def apply_saved_ablation(weight_manager, model_id, ablation_strength=4.2, search_dir=None):
    """
    应用保存的消融数据
    
    Args:
        weight_manager: RefusalAblationWeightManager实例
        model_id: str, 模型ID
        ablation_strength: float, 消融强度
        search_dir: str, 搜索目录
    
    Returns:
        bool: 是否成功应用
    """
    try:
        # 加载最新的消融数据
        result = quick_load_latest_ablation_data(model_id, search_dir)
        if result is None:
            return False
        
        loaded_layers, loaded_directions, metadata = result
        
        # 应用消融
        weight_manager.apply_multiple_layers_ablation(
            loaded_layers, 
            loaded_directions, 
            ablation_strength=ablation_strength
        )
        
        print(f"✅ 已应用保存的消融数据:")
        print(f"   消融层数: {len(loaded_layers)}")
        print(f"   消融强度: {ablation_strength}")
        print(f"   数据时间: {metadata.get('timestamp', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 应用消融数据失败: {e}")
        return False

"""
# 使用示例
print(f"\n🔧 使用保存的数据进行消融测试...")

# # 方法1：直接应用保存的消融
# if apply_saved_ablation(weight_manager, MODEL_ID, ablation_strength=4.2):
#     # 进行交互测试
#     interactive_test_ablation_weight_modification(ablation_strength=4.2)

# 方法2：手动加载并应用
try:
    # 列出可用文件
    available_files = list_ablation_files(search_dir="./ablation_cache", model_filter="GLM")
    
    if available_files:
        # 加载最新文件
        latest_file = available_files[0]['filepath']
        loaded_layers, loaded_directions, metadata = load_ablation_data(latest_file)
        
        # 更新全局变量（如果需要）
        selected_layers = loaded_layers
        selected_refusal_directions = loaded_directions
        
        print(f"✅ 已更新消融配置")
        
except Exception as e:
    print(f"⚠️  加载失败，使用原始计算的数据: {e}")

print(f"\n🎯 当前消融配置:")
print(f"   选中层: {selected_layers}")
print(f"   方向向量数: {len(selected_refusal_directions)}")

"""