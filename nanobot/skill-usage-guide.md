# NanoBot Skill 使用指南

## Skill 概述

Skill 是 NanoBot 的扩展机制，通过 Markdown 文件教授 Agent 使用特定工具或执行特定任务。

## Skill 文件结构

```
nanobot/skills/
├── github/
│   └── SKILL.md          # Skill 定义文件
├── weather/
│   └── SKILL.md
└── README.md
```

每个 Skill 目录包含一个 `SKILL.md` 文件，格式如下：

```markdown
---
name: github
description: "Interact with GitHub using the `gh` CLI..."
metadata:
  nanobot:
    emoji: 🐙
    requires:
      bins: [gh]
    install:
      - id: brew
        kind: brew
        formula: gh
---

# Skill 使用说明
...实际内容...
```

## Skill 加载流程

### 1. 注册阶段 (SkillsLoader)

```python
# nanobot/agent/skills.py

class SkillsLoader:
    def __init__(self, workspace: Path, builtin_skills_dir: Path | None = None):
        self.workspace = workspace
        self.workspace_skills = workspace / "skills"      # 用户自定义 skill
        self.builtin_skills = builtin_skills_dir          # 内置 skill
    
    def list_skills(self, filter_unavailable: bool = True):
        """列出所有可用 skill，按优先级排序"""
        # 1. workspace_skills 优先级最高
        # 2. builtin_skills 其次
        # 3. 过滤不满足依赖的 skill
```

### 2. 上下文构建阶段 (ContextBuilder)

```python
# nanobot/agent/context.py

class ContextBuilder:
    def build_system_prompt(self, skill_names: list[str] | None = None):
        # 1. 加载 always=true 的 skill（完整内容）
        always_skills = self.skills.get_always_skills()
        if always_skills:
            always_content = self.skills.load_skills_for_context(always_skills)
        
        # 2. 其他 skill 只显示摘要（渐进式加载）
        skills_summary = self.skills.build_skills_summary()
        # Agent 需要时用 read_file 加载完整内容
```

### 3. 渐进式加载

```
系统提示中显示:
<skills>
  <skill available="true">
    <name>github</name>
    <description>Interact with GitHub...</description>
    <location>/path/to/SKILL.md</location>
  </skill>
</skills>

Agent 按需读取:
read_file("/path/to/SKILL.md")
```

## Skill 元数据字段

| 字段 | 说明 |
|------|------|
| `name` | Skill 名称 |
| `description` | 简短描述 |
| `nanobot.requires.bins` | 需要的 CLI 工具 |
| `nanobot.requires.env` | 需要的环境变量 |
| `nanobot.always` | 是否总是加载完整内容 |
| `nanobot.install` | 安装指引 |

## Python 案例：创建自定义 Skill

### 场景：创建一个 Python 项目管理 Skill

**步骤 1：创建目录结构**

```bash
mkdir -p workspace/skills/python-project
```

**步骤 2：编写 SKILL.md**

```markdown
---
name: python-project
description: "Manage Python projects with venv, pip, and pytest. Create, test, and run Python applications."
metadata:
  nanobot:
    emoji: 🐍
    requires:
      bins: [python3, pip]
    always: true
---

# Python Project Skill

## 创建新项目

```bash
# 创建项目目录
mkdir my-project && cd my-project

# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 安装依赖
pip install pytest black mypy
```

## 项目结构

```
my-project/
├── .venv/
├── src/
│   └── my_module.py
├── tests/
│   └── test_my_module.py
├── requirements.txt
└── pyproject.toml
```

## 测试

```bash
# 运行测试
pytest tests/

# 带覆盖率
pytest --cov=src tests/
```

## 代码质量

```bash
# 格式化
black src/ tests/

# 类型检查
mypy src/
```
```

**步骤 3：使用**

```python
# 用户发送消息
"帮我创建一个 Python 项目，包含 pytest 测试框架"

# Agent 自动：
# 1. 检测到 python-project skill 可用
# 2. 读取完整 SKILL.md（因为 always=true）
# 3. 执行命令创建项目
# 4. 设置虚拟环境和依赖
```

## Skill 与 Tool 的区别

| 维度 | Skill | Tool |
|------|-------|------|
| 形式 | Markdown 文档 | Python 类 |
| 内容 | 使用指南、最佳实践 | 可执行代码 |
| 加载 | 按需加载到上下文 | 注册到工具注册表 |
| 扩展性 | 用户可轻松添加 | 需要编写代码 |

## 依赖检查机制

```python
def _check_requirements(self, skill_meta: dict) -> bool:
    """检查 skill 依赖是否满足"""
    requires = skill_meta.get("requires", {})
    
    # 检查 CLI 工具
    for b in requires.get("bins", []):
        if not shutil.which(b):
            return False  # 工具未安装
    
    # 检查环境变量
    for env in requires.get("env", []):
        if not os.environ.get(env):
            return False  # 环境变量未设置
    
    return True
```

## 最佳实践

1. **渐进式加载**：只有 `always=true` 的 skill 才加载完整内容，避免上下文膨胀
2. **明确依赖**：在 `requires` 中声明所需工具和环境变量
3. **提供安装指引**：帮助用户安装缺失的依赖
4. **简洁描述**：description 用于技能发现，应简明扼要
