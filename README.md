# 小芽参谋 · 0-3岁育儿顾问（原型 v0.1）

给新手父母的 AI 育儿参谋。核心理念：**父母不是上帝，也是人** —— 先接住父母的情绪，再谈方法。

## 它能做什么（最小闭环）

家长用自然语言描述困扰 → Agent 自动做三件事：
1. **查知识库**：检索 0-3 岁发展心理学知识（RAG），不凭空编
2. **看孩子档案**：读取长期记忆里的孩子特点（每个孩子独一无二）
3. **结构化回答**：共情 → 原因分析 → 可执行的行动 → 观察什么 → 给父母的话

## 快速运行

```bash
cd parenting-agent-prototype
pip install -r requirements.txt

# 1. 去 DeepSeek 开放平台申请 API Key（有免费额度）
# 2. 设置环境变量（Key 绝不写进代码）
export LLM_API_KEY=你的key
# 可选：换模型厂商只改这两个，不用改代码
# export LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# export LLM_MODEL=qwen-flash

python -m src.main
```

对话示例：
- 「8个月宝宝最近夜醒很频繁怎么办」
- 「1岁半宝宝只会叫爸爸妈妈，正常吗」
- 命令：`/profile` 查看孩子档案，`/quit` 退出

## 架构（一眼看懂）

```
家长输入
   │
   ▼
┌─────────────┐
│  agent.py   │  主循环：调模型 → 有 tool_calls 就执行 → 把结果喂回去 → 直到模型直接回答
│ (ReAct loop)│  上限 5 轮，防止死循环烧钱
└──────┬──────┘
       │  按需调用
       ▼
┌─────────────────────────────────────────────────┐
│ tools.py                                        │
│ ① search_parenting_knowledge  检索本地知识库     │
│ ② get_developmental_milestones 按月龄查里程碑   │
│ ③ get/update_child_profile   孩子档案读写（记忆）│
└─────────────────────────────────────────────────┘
```

## 每个文件学什么（建议按这个顺序读）

1. `src/config.py` —— 最小：配置与密钥管理。为什么 Key 走环境变量。
2. `src/knowledge_base.py` —— RAG 的最小形态：文档切分 + 关键词检索。生产升级就是把 `score_section` 换成向量检索，接口不变。
3. `src/tools.py` —— Agent 的"手脚"：OpenAI function calling 的 schema 定义，工具就是带 JSON 描述的 Python 函数。
4. `src/agent.py` —— 核心：system prompt（PET 理念 + guardrails）+ tool-calling 主循环。**这是最值得吃透的文件。**
5. `src/main.py` —— CLI 对话入口，没技术含量，负责交互。

## 刻意留下的"坑"（学习用）

- `knowledge_base.py` 用的是关键词检索，中文长句检索效果一般 —— 下一步亲手换成 embedding 向量检索，体会差距。
- 孩子档案是 JSON 文件 —— 下一步换成 SQLite，体会持久化。
- 没有对话轮数外的成本控制 —— 下一步加 max_tokens 和按任务计费。

## 安全红线（写进 system prompt 的）

- 红灯信号 → 必须建议就医/专业评估，不许说"再等等"
- 不确定的承认不确定，不编数据
- 不开药、不做诊断

## 微信小程序版（中国优先）

```
小程序前端 (miniprogram/)          你的后端 (backend/)              大模型
┌──────────────────┐   POST   ┌──────────────────┐  OpenAI兼容  ┌──────────┐
│ 聊天页            │ ──────► │ FastAPI /api/chat │ ──────────► │ DeepSeek │
│ (wxml/wxss/js)    │ ◄────── │ 跑 Agent 循环     │ ◄────────── │ /Qwen    │
└──────────────────┘   JSON   └──────────────────┘              └──────────┘
```

- 小程序只负责 UI，API Key 只在后端，Agent 核心（src/）一行不用改
- 后端运行：`pip install -r backend/requirements.txt && uvicorn backend.app:app --port 8000`
- 小程序用微信开发者工具打开 `miniprogram/` 目录，`app.js` 里改 `baseUrl`
- 上线前要办：HTTPS 域名 + 微信 request 合法域名配置；AI 聊天类目过审；算法备案（远期门）
