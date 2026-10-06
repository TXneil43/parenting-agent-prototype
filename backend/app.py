"""FastAPI 后端：给微信小程序提供 HTTP 接口。

架构：小程序 --POST /api/chat--> 后端跑 Agent 循环 --OpenAI兼容接口--> 大模型
为什么必须有后端：
- 小程序前端不能存 API Key（会被反编译拿走），也不能直调大模型
- 会话、孩子档案、未来的用户鉴权都在后端做
- Agent 核心代码（src/agent.py）原样复用，一行不用改

运行：uvicorn backend.app:app --host 0.0.0.0 --port 8000
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from pydantic import BaseModel

from src import tools
from src.agent import ParentingAgent

app = FastAPI(title="小芽参谋 API")

# 会话：session_id -> ParentingAgent（带对话历史）。
# 原型用内存字典，生产换 Redis（多实例/重启不丢）。
sessions = {}


class ChatIn(BaseModel):
    message: str
    session_id: str = ""


@app.post("/api/chat")
def chat(inp: ChatIn):
    """小程序调这个接口对话。返回回答 + session_id（下轮带回来保持上下文）。"""
    sid = inp.session_id or uuid.uuid4().hex[:12]
    agent = sessions.get(sid)
    if agent is None:
        agent = ParentingAgent()  # 需要环境变量 LLM_API_KEY
        sessions[sid] = agent
    reply = agent.chat(inp.message)
    return {"reply": reply, "session_id": sid}


@app.get("/api/profile")
def profile():
    """查看孩子档案。"""
    return {"profile": tools.get_child_profile()}


@app.get("/health")
def health():
    return {"ok": True}
