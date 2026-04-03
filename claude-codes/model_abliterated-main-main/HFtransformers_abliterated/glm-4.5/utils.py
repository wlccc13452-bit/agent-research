import torch
from contextlib import contextmanager

@contextmanager
def preserve_model_dtypes(model):
    """保护模型参数类型不被推理过程改变"""
    # 记录原始参数类型
    original_dtypes = {}
    for name, param in model.named_parameters():
        original_dtypes[name] = param.dtype
    
    try:
        # 设置为推理模式，禁用梯度计算
        model.eval()
        with torch.no_grad(), torch.inference_mode():
            yield model
    finally:
        # 恢复原始参数类型
        print("🔧 检查并恢复参数类型...")
        restored_count = 0
        for name, param in model.named_parameters():
            original_dtype = original_dtypes[name]
            if param.dtype != original_dtype:
                #print(f"  恢复 {name}: {param.dtype} → {original_dtype}")
                # 将参数转换回原始类型
                param.data = param.data.to(dtype=original_dtype)
                restored_count += 1
        
        if restored_count > 0:
            print(f"✅ 已恢复 {restored_count} 个参数的类型")
        else:
            print("✅ 所有参数类型保持不变")

# 使用方法
def safe_generate(model, tokenizer, input_text):
    """安全的生成函数，保护参数类型"""
    with preserve_model_dtypes(model):
        # 准备输入
        conversation = [{"role": "user", "content": input_text}]
        tokenized_input = tokenizer.apply_chat_template(
            conversation,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True
        )
        
        # 确保输入在正确设备上
        model_device = get_model_device(model)
        input_ids = tokenized_input['input_ids'].to(model_device)
        attention_mask = tokenized_input.get('attention_mask', torch.ones_like(input_ids)).to(model_device)
        
        # 执行生成
        outputs = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=1,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
            use_cache=True
        )
        
        # 解码输出
        response = tokenizer.decode(outputs[0][len(input_ids[0]):], skip_special_tokens=True)
        return response

# 替换原来的生成代码
# response = model.generate(...)  # 旧方式
response = safe_generate(model, tokenizer, "你好")  # 新方式

# 在你的 interactive_test_ablation_weight_modification 函数中
def interactive_test_ablation_weight_modification(ablation_strength=5.0):
    """交互式测试权重消融效果 - 类型安全版本"""
    print(f"\n=== 交互式权重消融测试 (类型保护模式) ===")
    
    while True:
        try:
            user_input = input("\n请输入测试问题: ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                break
                
            # 使用类型保护的生成
            with preserve_model_dtypes(model):
                conversation = [{"role": "user", "content": user_input + "/nothink"}]
                tokenized_input = tokenizer.apply_chat_template(
                    conversation,
                    add_generation_prompt=True,
                    return_tensors="pt",
                    return_dict=True
                )
                
                model_device = get_model_device(model)
                input_ids = tokenized_input['input_ids'].to(model_device)
                attention_mask = tokenized_input.get('attention_mask', torch.ones_like(input_ids)).to(model_device)
                
                outputs = model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=64,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=tokenizer.eos_token_id
                )
                
                response = tokenizer.decode(outputs[0][len(input_ids[0]):], skip_special_tokens=True)
                print(f"模型回复: {response}")
                
        except Exception as e:
            print(f"发生错误: {e}")
            continue
    
    print("已安全退出，所有参数类型已保护")

    ########################

    def diagnose_ablation_impact():
    """诊断消融操作对模型的具体影响"""
    
    print("🔍 开始消融影响诊断...")
    
    # 1. 记录消融前的完整状态
    print("\n=== 第1步: 记录消融前状态 ===")
    pre_ablation_state = {}
    
    # 记录所有参数的详细信息
    for name, param in model.named_parameters():
        pre_ablation_state[name] = {
            'dtype': param.dtype,
            'shape': param.shape,
            'device': param.device,
            'requires_grad': param.requires_grad,
            'data_ptr': param.data_ptr(),  # 内存地址
            'is_contiguous': param.is_contiguous(),
            'checksum': param.data.sum().item() if param.numel() < 1000000 else param.data.flatten()[:1000].sum().item()
        }
    
    print(f"记录了 {len(pre_ablation_state)} 个参数的状态")
    
    # 2. 测试消融前推理
    print("\n=== 第2步: 消融前推理测试 ===")
    test_prompt = "你好"
    
    try:
        pre_response = simple_generate(test_prompt)
        print(f"✅ 消融前推理成功: {pre_response[:50]}...")
        pre_inference_success = True
    except Exception as e:
        print(f"❌ 消融前推理已有问题: {e}")
        pre_inference_success = False
        
    if not pre_inference_success:
        print("⚠️ 消融前推理就有问题，停止诊断")
        return
    
    # 3. 执行消融操作（逐步）
    print("\n=== 第3步: 逐步执行消融操作 ===")
    
    # 选择一个测试层
    test_layer_idx = selected_layers[0]
    test_refusal_dir = selected_refusal_directions[0]
    
    print(f"测试层: {test_layer_idx}")
    print(f"消融前推理状态: 正常")
    
    # 逐步执行消融的各个子操作
    target_layer = model.model.layers[test_layer_idx]
    
    # 子步骤1: 设备和类型转换
    print("\n--- 子步骤1: 拒绝方向设备和类型适配 ---")
    try:
        device = next(target_layer.parameters()).device
        dtype = next(target_layer.parameters()).dtype
        print(f"目标设备: {device}, 目标类型: {dtype}")
        
        original_refusal_dir = test_refusal_dir.clone()
        adapted_refusal_dir = test_refusal_dir.to(device=device, dtype=dtype)
        print(f"✅ 设备类型适配完成")
        
        # 测试推理
        test_response = simple_generate("你好")
        print(f"✅ 设备适配后推理正常")
        
    except Exception as e:
        print(f"❌ 设备类型适配导致问题: {e}")
        return
    
    # 子步骤2: 权重备份
    print("\n--- 子步骤2: 权重备份过程 ---")
    try:
        backup_weights = {}
        
        if hasattr(target_layer, 'self_attn'):
            if hasattr(target_layer.self_attn, 'q_proj'):
                backup_weights['q_proj'] = target_layer.self_attn.q_proj.weight.data.clone()
                print(f"✅ 备份q_proj权重: {backup_weights['q_proj'].dtype}")
            
        print(f"✅ 权重备份完成")
        
        # 测试推理
        test_response = simple_generate("你好")
        print(f"✅ 权重备份后推理正常")
        
    except Exception as e:
        print(f"❌ 权重备份导致问题: {e}")
        return
    
    # 子步骤3: 权重消融计算（不修改权重）
    print("\n--- 子步骤3: 消融计算（不修改权重） ---")
    try:
        if hasattr(target_layer.self_attn, 'q_proj'):
            weight_matrix = target_layer.self_attn.q_proj.weight
            print(f"权重类型: {weight_matrix.dtype}")
            
            if weight_matrix.dtype == torch.float8_e4m3fn:
                print("检测到FP8权重，跳过计算")
            else:
                # 只计算，不修改
                refusal_direction_adapted = adapted_refusal_dir.to(dtype=weight_matrix.dtype)
                projections = torch.matmul(weight_matrix, refusal_direction_adapted.unsqueeze(1))
                print(f"✅ 投影计算完成: {projections.shape}")
        
        # 测试推理
        test_response = simple_generate("你好")
        print(f"✅ 消融计算后推理正常")
        
    except Exception as e:
        print(f"❌ 消融计算导致问题: {e}")
        return
    
    # 子步骤4: 实际权重修改
    print("\n--- 子步骤4: 实际权重修改 ---")
    try:
        if hasattr(target_layer.self_attn, 'q_proj'):
            weight_matrix = target_layer.self_attn.q_proj.weight
            
            if weight_matrix.dtype == torch.float8_e4m3fn:
                print("跳过FP8权重修改")
            else:
                # 执行实际修改
                refusal_direction_adapted = adapted_refusal_dir.to(dtype=weight_matrix.dtype)
                projections = torch.matmul(weight_matrix, refusal_direction_adapted.unsqueeze(1))
                ablation_component = 4.2 * torch.matmul(projections, refusal_direction_adapted.unsqueeze(0))
                
                print(f"修改前权重范数: {weight_matrix.norm().item():.6f}")
                weight_matrix.data -= ablation_component
                print(f"修改后权重范数: {weight_matrix.norm().item():.6f}")
                print(f"✅ 权重修改完成")
        
        # 关键测试：权重修改后立即推理
        test_response = simple_generate("你好")
        print(f"✅ 权重修改后推理正常: {test_response[:30]}...")
        
    except Exception as e:
        print(f"❌ 权重修改导致推理问题: {e}")
        print(f"具体错误: {type(e).__name__}: {str(e)}")
        
        # 恢复权重再测试
        if 'q_proj' in backup_weights:
            target_layer.self_attn.q_proj.weight.data = backup_weights['q_proj']
            print("已恢复权重")
            
            try:
                recovery_response = simple_generate("你好")
                print(f"✅ 恢复权重后推理恢复正常")
            except Exception as recovery_error:
                print(f"❌ 即使恢复权重，推理仍有问题: {recovery_error}")
        
        return
    
    # 4. 对比消融后状态
    print("\n=== 第4步: 对比消融后状态 ===")
    changed_params = []
    
    for name, param in model.named_parameters():
        if name in pre_ablation_state:
            pre_info = pre_ablation_state[name]
            current_info = {
                'dtype': param.dtype,
                'device': param.device,
                'data_ptr': param.data_ptr(),
                'is_contiguous': param.is_contiguous()
            }
            
            # 检查变化
            changes = []
            if pre_info['dtype'] != current_info['dtype']:
                changes.append(f"dtype: {pre_info['dtype']} -> {current_info['dtype']}")
            if pre_info['device'] != current_info['device']:
                changes.append(f"device: {pre_info['device']} -> {current_info['device']}")
            if pre_info['data_ptr'] != current_info['data_ptr']:
                changes.append(f"data_ptr changed")
            if pre_info['is_contiguous'] != current_info['is_contiguous']:
                changes.append(f"contiguous: {pre_info['is_contiguous']} -> {current_info['is_contiguous']}")
            
            if changes:
                changed_params.append((name, changes))
    
    if changed_params:
        print(f"发现 {len(changed_params)} 个参数发生变化:")
        for name, changes in changed_params[:10]:  # 只显示前10个
            print(f"  {name}: {', '.join(changes)}")
        if len(changed_params) > 10:
            print(f"  ... 还有 {len(changed_params) - 10} 个参数")
    else:
        print("✅ 没有检测到参数状态变化")

def simple_generate(prompt):
    """简化的生成函数用于测试"""
    conversation = [{"role": "user", "content": prompt}]
    tokenized_input = tokenizer.apply_chat_template(
        conversation,
        add_generation_prompt=True,
        return_tensors="pt",
        return_dict=True
    )
    
    model_device = get_model_device(model)
    input_ids = tokenized_input['input_ids'].to(model_device)
    attention_mask = tokenized_input.get('attention_mask', torch.ones_like(input_ids)).to(model_device)
    
    with torch.no_grad():
        outputs = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=5,
            temperature=0.1,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0][len(input_ids[0]):], skip_special_tokens=True)
    return response

# 运行诊断
diagnose_ablation_impact()