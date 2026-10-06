"""配置：从环境变量读取模型接入信息。

为什么这样设计：
- API Key 绝不能写进代码，要走环境变量（配合 .gitignore）。
- 用 OpenAI 兼容接口：换模型厂商只改 BASE_URL 和 MODEL，
  代码不用动。这是 2026 年国内开发的标准做法。
"""
import os


def load_config():
    return {
        "api_key": os.environ.get("LLM_API_KEY", ""),
        "base_url": os.environ.get("LLM_BASE_URL", "https://api.deepseek.com"),
        "model": os.environ.get("LLM_MODEL", "deepseek-chat"),
    }


def check_config(cfg):
    if not cfg["api_key"]:
        raise RuntimeError(
            "没有找到 LLM_API_KEY。请先去 DeepSeek 开放平台申请 API Key（有免费额度），"
            "然后执行: export LLM_API_KEY=你的key"
        )
