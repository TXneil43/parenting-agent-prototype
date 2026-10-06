"""CLI 入口：和育儿参谋对话。"""
from . import tools
from .agent import ParentingAgent


def main():
    print("=== 小芽参谋 · 0-3岁育儿顾问（原型）===")
    print("直接描述你的困扰，比如：8个月宝宝最近夜醒很频繁怎么办")
    print("命令：/profile 查看孩子档案，/quit 退出\n")
    agent = ParentingAgent()
    while True:
        try:
            text = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text == "/quit":
            break
        if text == "/profile":
            print(tools.get_child_profile())
            continue
        if not text:
            continue
        print("\n小芽参谋：", agent.chat(text), "\n")


if __name__ == "__main__":
    main()
