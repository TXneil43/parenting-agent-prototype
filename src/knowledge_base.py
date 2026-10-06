"""知识库：加载 knowledge/ 下的 markdown，按小节切分 + 关键词检索。

这是 RAG 的最小形态，目的是先跑通闭环：
  用户问题 -> 检索相关知识 -> 把知识塞进 prompt -> 模型基于知识回答。

生产升级路径：把 score_section 换成 embedding 向量检索
（chroma / qdrant / DashScope 文本向量），函数签名不变。
"""
import os
import re

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")


def load_sections():
    """把每个 md 文件按 ## 标题切成小节，返回 [{stage, title, text}]。"""
    sections = []
    for fname in sorted(os.listdir(KNOWLEDGE_DIR)):
        if not fname.endswith(".md"):
            continue
        stage = fname.replace(".md", "")
        path = os.path.join(KNOWLEDGE_DIR, fname)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        parts = re.split(r"^## ", content, flags=re.M)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            title, _, text = part.partition("\n")
            sections.append({"stage": stage, "title": title.strip(), "text": text.strip()})
    return sections


def _grams(query):
    """把查询切成 2-gram，用于中文关键词匹配（原型级实现）。"""
    q = re.sub(r"\s+", "", query)
    return {q[i:i + 2] for i in range(len(q) - 1)} or {q}


def score_section(query, section):
    grams = _grams(query)
    text = section["title"] + section["text"]
    return sum(1 for g in grams if g in text)


def search(query, top_k=3, stage=None):
    """检索知识库，返回最相关的 top_k 个小节。"""
    sections = load_sections()
    if stage:
        sections = [s for s in sections if stage in s["stage"]]
    ranked = sorted(sections, key=lambda s: score_section(query, s), reverse=True)
    return [s for s in ranked[:top_k] if score_section(query, s) > 0]
