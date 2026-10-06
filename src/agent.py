"""Agent 主循环：ReAct 风格的 tool-calling loop。

流程（这就是 Agent 和普通 chatbot 的区别）：
  用户输入
    -> 把 system prompt + 孩子档案 + 历史组装成 messages
    -> 调模型
    -> 如果模型返回 tool_calls：执行本地工具，把结果 append 回 messages，再调模型
    -> 直到模型直接返回文本回答（或达到最大轮数，防止死循环烧钱）

核心就两件事：system prompt 定义"它是谁、怎么说话、红线在哪"，
主循环定义"它怎么行动"。
"""
import json

from openai import OpenAI

from . import tools
from .config import check_config, load_config

SYSTEM_PROMPT = """你是"小芽参谋"——一位 0-3 岁婴儿期育儿参谋，服务对象是新手父母。

你的底层理念（来自 PET 父母效能训练）：
- 父母不是上帝，也是人：疲惫、焦虑、自我怀疑都是正常的。先接住父母的情绪，再谈方法。
- 示范"我信息"：教父母把"你怎么又哭"换成"妈妈现在很累，我们一起想办法"。
- 行为窗口：先判断这是谁的问题——孩子发展阶段的正常表现，就帮父母调整期待；
  确实需要引导的，再给方法。没有"坏孩子"，只有没被理解的需求。

回答结构（必须遵守）：
1. 【先听你说】一句话共情，具体、不说空话。
2. 【原因分析】基于检索到的知识，解释行为背后的发展原因。先调用 search_parenting_knowledge。
3. 【可以试试】2-4 条具体可执行的行动，不说空话。
4. 【观察什么】告诉父母接下来观察哪些信号。
5. 【给父母的话】一句话，关怀父母本身（他们也需要被照看）。

硬性 guardrails：
- 涉及发育问题，必须先调用 get_developmental_milestones。
- 出现红灯信号时，必须明确建议去看儿科医生或做专业评估，不许说"再等等看"。
- 不确定的就承认不确定，不许编造数据和研究。
- 不开药、不做诊断，只给养育建议。
"""


class ParentingAgent:
    """参谋本体：持有模型客户端 + 对话历史，对外只暴露 chat()。"""

    def __init__(self):
        cfg = load_config()
        check_config(cfg)
        self.client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
        self.model = cfg["model"]
        self.history = []

    def _build_messages(self, user_input):
        """组装 messages：系统设定 + 孩子档案（长期记忆）+ 历史 + 本轮输入。"""
        profile = tools.get_child_profile()
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": "孩子档案（长期记忆）：\n" + profile},
            *self.history,
            {"role": "user", "content": user_input},
        ]

    def chat(self, user_input, max_rounds=5):
        """一轮对话：循环调模型、执行工具，直到模型直接回答。"""
        messages = self._build_messages(user_input)
        for _ in range(max_rounds):
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools.TOOLS_SCHEMA,
                tool_choice="auto",
            )
            msg = resp.choices[0].message
            if not msg.tool_calls:
                # 模型直接回答：本轮结束，记入历史
                self.history += [
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": msg.content},
                ]
                return msg.content
            # 模型想调工具：先把"模型想调工具"这条消息记下来，
            # 再把每个工具的执行结果 append 回去，下一轮模型能看到
            messages.append(msg)
            for call in msg.tool_calls:
                fn = tools.TOOL_FUNCS[call.function.name]
                args = json.loads(call.function.arguments or "{}")
                result = fn(**args)
                messages.append(
                    {"role": "tool", "tool_call_id": call.id, "content": result}
                )
        return "（达到最大工具调用轮数，请换个问法再试一次）"
