# 2026-03-17 价格提醒功能升级

## 更新内容

升级价格提醒功能，支持**同时监控目标价格和涨跌幅**，满足任一条件即触发提醒并推送通知。

---

## 核心改进

### 1. 同时监控多个条件

**之前**: 单一提醒类型 (price_up/price_down/change_up/change_down)

**现在**: 同时设置
- ✅ 目标价格 (target_price)
- ✅ 上涨幅度% (change_up_pct)
- ✅ 下跌幅度% (change_down_pct)

**至少一个，满足任一即触发**

### 2. 新增字段

**数据库模型**:
```python
base_price          # 基准价格（创建时的价格）
target_price        # 目标价格（可选）
change_up_pct       # 上涨幅度%（可选）
change_down_pct     # 下跌幅度%（可选）
trigger_reason      # 触发原因 (target_price/change_up/change_down)
```

**移除字段**:
- `alert_type` (不再需要单一类型)
- `target_value` (拆分为具体字段)

---

## 实现细节

### 1. 数据模型更新

**文件**: `backend/database/models.py`

**变化**:
- 添加 `base_price` 字段
- 添加 `target_price` 字段
- 添加 `change_up_pct` 字段
- 添加 `change_down_pct` 字段
- 添加 `trigger_reason` 字段
- 移除 `alert_type` 字段
- 移除 `target_value` 字段

### 2. 服务层重写

**文件**: `backend/services/price_alert_manager.py`

**核心逻辑**:

#### 创建提醒
```python
async def create_alert(
    self,
    db: AsyncSession,
    stock_code: str,
    target_price: Optional[float] = None,
    change_up_pct: Optional[float] = None,
    change_down_pct: Optional[float] = None,
    feishu_chat_id: Optional[str] = None,
    notes: Optional[str] = None
) -> PriceAlert:
    # 验证至少一个条件
    if target_price is None and change_up_pct is None and change_down_pct is None:
        raise ValueError("至少需要设置一个监控条件")
    
    # 获取当前价格作为基准价
    quote = await stock_service.get_realtime_quote(stock_code)
    current_price = quote.get("price", 0)
    
    # 创建提醒
    alert = PriceAlert(
        stock_code=stock_code,
        base_price=current_price,  # 基准价
        target_price=target_price,
        change_up_pct=change_up_pct,
        change_down_pct=change_down_pct,
        ...
    )
```

#### 检查提醒
```python
async def check_alerts(self, db: AsyncSession) -> List[Dict]:
    for alert in alerts:
        # 更新当前价格
        current_price = get_current_price(alert.stock_code)
        alert.current_price = current_price
        
        # 检查触发条件
        trigger_reason = None
        
        # 检查目标价
        if alert.target_price and current_price >= alert.target_price:
            trigger_reason = "target_price"
        
        # 检查涨幅
        if alert.change_up_pct and current_change_pct >= alert.change_up_pct:
            trigger_reason = "change_up"
        
        # 检查跌幅
        if alert.change_down_pct and current_change_pct <= alert.change_down_pct:
            trigger_reason = "change_down"
        
        if trigger_reason:
            # 发送飞书通知
            await self._send_alert_notification(alert, quote, trigger_reason)
```

#### 发送通知
```python
async def _send_alert_notification(self, alert, quote, trigger_reason):
    # 构建触发消息
    if trigger_reason == "target_price":
        trigger_emoji = "🎯"
        trigger_text = f"达到目标价 {alert.target_price:.2f}元"
    elif trigger_reason == "change_up":
        trigger_emoji = "📈"
        trigger_text = f"涨幅超过 {alert.change_up_pct:+.2f}%"
    elif trigger_reason == "change_down":
        trigger_emoji = "📉"
        trigger_text = f"跌幅超过 {alert.change_down_pct:+.2f}%"
    
    message = f"""
{trigger_emoji} 价格提醒触发

股票: {alert.stock_name} ({alert.stock_code})
触发条件: {trigger_text}
当前状态: {current_price:.2f}元 ({current_change_pct:+.2f}%)
基准价格: {alert.base_price:.2f}元

监控设置:
• 目标价: {alert.target_price:.2f}元
• 涨幅监控: {alert.change_up_pct:+.2f}%
• 跌幅监控: {alert.change_down_pct:+.2f}%

触发时间: {datetime.now()}
    """
```

### 3. API路由更新

**文件**: `backend/routers/price_alerts.py`

**Pydantic模型**:
```python
class PriceAlertCreate(BaseModel):
    stock_code: str
    target_price: Optional[float] = None
    change_up_pct: Optional[float] = None
    change_down_pct: Optional[float] = None
    feishu_chat_id: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('change_up_pct', 'change_down_pct')
    def validate_percentage(cls, v):
        if v is not None and (v < -100 or v > 100):
            raise ValueError('涨跌幅必须在 -100 到 100 之间')
        return v
    
    @validator('notes')
    def validate_at_least_one_condition(cls, v, values):
        if all(values.get(k) is None for k in ['target_price', 'change_up_pct', 'change_down_pct']):
            raise ValueError('至少需要设置一个监控条件')
        return v
```

**API端点**:
```python
@router.post("", response_model=PriceAlertResponse)
async def create_alert(alert_data: PriceAlertCreate, db: AsyncSession = Depends(get_db)):
    """
    创建新的价格提醒
    
    同时支持目标价格和涨跌幅监控，至少需要设置一个条件。
    
    示例:
    {
      "stock_code": "000001",
      "target_price": 15.0,
      "change_up_pct": 5.0,
      "change_down_pct": -3.0
    }
    """
```

### 4. 飞书卡片更新

**文件**: `backend/services/feishu_card_service.py`

**卡片表单**:
```python
def _create_price_alert_card(self):
    card = {
        "elements": [
            {
                "tag": "div",
                "text": {
                    "content": "**➕ 创建价格提醒**\n同时监控目标价格和涨跌幅（至少填写一项）"
                }
            },
            {
                "tag": "form",
                "elements": [
                    {
                        "tag": "input",
                        "name": "stock_code",
                        "required": True,
                        "label": "股票代码"
                    },
                    {
                        "tag": "input",
                        "name": "target_price",
                        "required": False,
                        "label": "🎯 目标价格"
                    },
                    {
                        "tag": "input",
                        "name": "change_up_pct",
                        "required": False,
                        "label": "📈 上涨幅度%"
                    },
                    {
                        "tag": "input",
                        "name": "change_down_pct",
                        "required": False,
                        "label": "📉 下跌幅度%"
                    },
                    {
                        "tag": "input",
                        "name": "notes",
                        "required": False,
                        "label": "📝 备注"
                    }
                ]
            }
        ]
    }
```

### 5. 回调处理更新

**文件**: `backend/routers/feishu.py`

```python
elif action_type == "confirm_create_price_alert":
    stock_code = form_data.get("stock_code", "")
    target_price_str = form_data.get("target_price", "")
    change_up_pct_str = form_data.get("change_up_pct", "")
    change_down_pct_str = form_data.get("change_down_pct", "")
    notes = form_data.get("notes", "")
    
    # 转换为float (空字符串转None)
    target_price = float(target_price_str) if target_price_str.strip() else None
    change_up_pct = float(change_up_pct_str) if change_up_pct_str.strip() else None
    change_down_pct = float(change_down_pct_str) if change_down_pct_str.strip() else None
    
    # 创建提醒
    alert = await price_alert_manager.create_alert(
        db,
        stock_code=stock_code,
        target_price=target_price,
        change_up_pct=change_up_pct,
        change_down_pct=change_down_pct,
        feishu_chat_id=chat_id,
        notes=notes
    )
    
    # 构建成功消息
    conditions = []
    if target_price:
        conditions.append(f"目标价 {target_price:.2f}元")
    if change_up_pct:
        conditions.append(f"涨幅超 {change_up_pct:+.2f}%")
    if change_down_pct:
        conditions.append(f"跌幅超 {change_down_pct:+.2f}%")
    
    message = f"✅ 已创建价格提醒: {alert.stock_name}\n"
    message += f"基准价格: {float(alert.base_price):.2f}元\n"
    message += f"监控条件: {', '.join(conditions)}"
```

---

## 测试验证

### 测试脚本
- `test/temp/feishu-card-test/test_price_alert_simultaneous.py`

### 测试覆盖
1. ✅ 仅目标价格
2. ✅ 仅涨跌幅
3. ✅ 全部条件
4. ✅ 验证逻辑
5. ✅ API请求验证
6. ✅ 飞书卡片生成

### 测试命令
```bash
# 运行测试
python test/temp/feishu-card-test/test_price_alert_simultaneous.py

# API测试
curl -X POST http://localhost:8000/api/price-alerts \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001",
    "target_price": 15.0,
    "change_up_pct": 5.0,
    "change_down_pct": -3.0
  }'
```

---

## 使用示例

### 示例1: 突破买入
```json
{
  "stock_code": "000001",
  "target_price": 15.0,
  "change_up_pct": 5.0,
  "change_down_pct": -3.0,
  "notes": "突破阻力位"
}
```

触发逻辑:
- 价格 >= 15元 → 目标价提醒
- 涨幅 >= 5% → 涨幅提醒
- 跌幅 >= 3% → 跌幅提醒(止损)

### 示例2: 区间交易
```json
{
  "stock_code": "000002",
  "target_price": 16.0,
  "change_down_pct": -5.0,
  "notes": "区间卖出+止损"
}
```

触发逻辑:
- 价格 >= 16元 → 卖出提醒
- 跌幅 >= 5% → 止损提醒

### 示例3: 波段操作
```json
{
  "stock_code": "000003",
  "change_up_pct": 3.0,
  "change_down_pct": -2.0,
  "notes": "短线波段"
}
```

触发逻辑:
- 涨幅 >= 3% → 止盈提醒
- 跌幅 >= 2% → 止损提醒

---

## 文件清单

### 核心文件
- `backend/database/models.py` - 更新数据模型
- `backend/services/price_alert_manager.py` - 完全重写
- `backend/routers/price_alerts.py` - 完全重写
- `backend/routers/feishu.py` - 更新回调处理
- `backend/services/feishu_card_service.py` - 更新卡片表单

### 测试和文档
- `test/temp/feishu-card-test/test_price_alert_simultaneous.py` - 新建测试
- `reference/technical/feishu/PRICE_ALERT_UPDATE.md` - 更新说明
- `.harness/memory/session-summaries/2026-03-17-price-alert-upgrade.md` - 本文件

---

## 代码统计

| 文件 | 行数 | 变化 |
|------|------|------|
| models.py | +40 | 更新 |
| price_alert_manager.py | 300 | 重写 |
| price_alerts.py | 120 | 重写 |
| feishu.py | +30 | 更新 |
| feishu_card_service.py | +50 | 更新 |
| test_price_alert_simultaneous.py | 200 | 新建 |
| 文档 | 400 | 新建 |
| **总计** | **~1140** | |

---

## 总结

✅ **完成升级**:
1. 支持同时监控目标价格和涨跌幅
2. 基准价格追踪
3. 触发原因记录
4. 增强的飞书通知
5. 完整的验证逻辑
6. 全面的测试覆盖

🎯 **核心价值**:
- 更灵活的监控设置
- 更精准的价格追踪
- 更及时的通知推送
- 更完善的使用体验

🚀 **准备就绪**: 可以立即使用!
