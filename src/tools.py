"""工具定义：agent 能调用的"手脚"。

三个工具，对应原型的三个能力：
1. search_parenting_knowledge —— RAG 检索 0-3 岁育儿知识（不凭空编）
2. get_developmental_milestones —— 按月龄查发展里程碑（含红灯信号）
3. get_child_profile / update_child_profile —— 孩子档案读写（长期记忆，
   每个孩子独一无二，agent 要记住这个孩子的特点）

OpenAI function calling 的本质：给模型一份"工具说明书"(TOOLS_SCHEMA)，
模型决定调哪个、传什么参数；真正执行的是本地 Python 函数(TOOL_FUNCS)。
"""
import json
import os

from . import knowledge_base

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PROFILE_PATH = os.path.join(DATA_DIR, "child_profile.json")

# 月龄 -> 发展里程碑（含红灯信号）。原型用内置表，生产可搬进知识库。
MILESTONES = {
    "0-3个月": {
        "milestones": "俯卧抬头45度；对声音有反应、被逗会笑；社会性微笑（6-8周出现）",
        "red_flags": "3个月还不会抬头、对声音无反应、很少笑 → 建议儿科评估",
    },
    "4-6个月": {
        "milestones": "翻身；抓握摇晃玩具；咿呀学语；认出熟悉面孔",
        "red_flags": "6个月不会翻身、几乎不发声、对人脸没兴趣 → 建议儿科评估",
    },
    "7-9个月": {
        "milestones": "独坐；爬行/匍匐；牙牙学语（ba-ba、ma-ma无意义）；分离焦虑出现；开始理解客体永久性",
        "red_flags": "9个月不会独坐、不认生也不认熟、发声很少 → 建议儿科评估",
    },
    "10-12个月": {
        "milestones": "扶站、扶走；拇指食指对捏；第一批有意义的词（爸爸/妈妈）；会挥手再见",
        "red_flags": "12个月不会扶站、无有意义发音、眼神交流差 → 建议儿科评估",
    },
    "13-18个月": {
        "milestones": "独立行走；扶着上下楼梯；词汇10-50个；指认身体部位；热衷模仿家务",
        "red_flags": "18个月不会走、一个词都不会说 → 建议儿科评估",
    },
    "19-24个月": {
        "milestones": "跑、踢球；词汇爆发到200+、说双词句；爱说不；出现如厕训练 readiness 信号",
        "red_flags": "2岁不会双词短语、语言明显倒退 → 建议儿科评估",
    },
    "25-36个月": {
        "milestones": "双脚跳、单脚站片刻；说完整简单句、会讲小故事；数到10；自己穿脱简单衣物",
        "red_flags": "3岁说不出短句、眼神交流持续差、已会技能明显倒退 → 建议儿科评估",
    },
}


def _month_in_range(range_name, age_months):
    lo, hi = range_name.replace("个月", "").split("-")
    return int(lo) <= age_months <= int(hi)


def search_parenting_knowledge(query, age_stage=""):
    """检索 0-3 岁育儿知识库。age_stage 可选：0-1岁 / 1-2岁 / 2-3岁。"""
    results = knowledge_base.search(query, top_k=3, stage=age_stage or None)
    if not results:
        return "知识库中没有找到相关内容，请基于通用育儿原则回答，并说明依据有限。"
    out = []
    for r in results:
        out.append("【" + r["stage"] + "·" + r["title"] + "】\n" + r["text"][:600])
    return "\n\n".join(out)


def get_developmental_milestones(age_months):
    """按月龄（0-36）查询发展里程碑和红灯信号。"""
    for range_name, info in MILESTONES.items():
        if _month_in_range(range_name, age_months):
            return (
                "月龄 " + str(age_months) + " 个月（" + range_name + "）：\n"
                + "里程碑：" + info["milestones"] + "\n"
                + "红灯信号：" + info["red_flags"]
            )
    return "月龄超出 0-36 个月范围，原型暂不支持。"


def get_child_profile():
    """读取孩子档案（长期记忆）。"""
    if not os.path.exists(PROFILE_PATH):
        return "（档案为空：还没有记录孩子信息）"
    with open(PROFILE_PATH, encoding="utf-8") as f:
        return f.read()


def update_child_profile(name="", age_months=-1, notes=""):
    """更新孩子档案。notes 用一句话记录新观察到的特点。"""
    profile = {"name": "", "age_months": None, "notes": []}
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, encoding="utf-8") as f:
            profile = json.load(f)
    if name:
        profile["name"] = name
    if age_months >= 0:
        profile["age_months"] = age_months
    if notes:
        profile.setdefault("notes", []).append(notes)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    return "档案已更新：" + json.dumps(profile, ensure_ascii=False)


# ---- 工具说明书：模型靠这个决定调哪个工具 ----
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_parenting_knowledge",
            "description": "检索 0-3 岁育儿知识库。回答养育问题前优先调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索关键词，如：夜醒 分离焦虑"},
                    "age_stage": {"type": "string", "description": "0-1岁 / 1-2岁 / 2-3岁，可空"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_developmental_milestones",
            "description": "按月龄查询发展里程碑和红灯信号。涉及发育问题时必须调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "age_months": {"type": "integer", "description": "月龄 0-36"},
                },
                "required": ["age_months"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_child_profile",
            "description": "读取孩子档案，了解这个孩子的特点和历史。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_child_profile",
            "description": "家长提到孩子的新情况时，记录到档案。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age_months": {"type": "integer"},
                    "notes": {"type": "string", "description": "一句话记录新观察"},
                },
            },
        },
    },
]

TOOL_FUNCS = {
    "search_parenting_knowledge": search_parenting_knowledge,
    "get_developmental_milestones": get_developmental_milestones,
    "get_child_profile": get_child_profile,
    "update_child_profile": update_child_profile,
}
