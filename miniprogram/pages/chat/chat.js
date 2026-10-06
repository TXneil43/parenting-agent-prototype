// 聊天页：调后端 /api/chat，session_id 带回保持多轮上下文
const app = getApp();

Page({
  data: {
    messages: [
      { role: "assistant", text: "你好呀，我是小芽参谋。跟我说说宝宝最近的情况吧，比如：8个月宝宝夜醒很频繁怎么办。" }
    ],
    input: "",
    sessionId: "",
    loading: false,
    scrollTop: 99999
  },

  onInput(e) { this.setData({ input: e.detail.value }); },

  sendMsg() {
    const text = this.data.input.trim();
    if (!text || this.data.loading) return;
    const msgs = this.data.messages.concat([{ role: "user", text }]);
    this.setData({ messages: msgs, input: "", loading: true, scrollTop: 99999 });

    wx.request({
      url: app.globalData.baseUrl + "/api/chat",
      method: "POST",
      data: { message: text, session_id: this.data.sessionId },
      success: (res) => {
        const reply = (res.data && res.data.reply) || "（后端没有返回内容）";
        this.setData({
          messages: this.data.messages.concat([{ role: "assistant", text: reply }]),
          sessionId: (res.data && res.data.session_id) || this.data.sessionId,
          loading: false,
          scrollTop: 99999
        });
      },
      fail: () => {
        this.setData({
          messages: this.data.messages.concat([{ role: "assistant", text: "连不上后端，检查 baseUrl 和后端是否启动。" }]),
          loading: false
        });
      }
    });
  }
});
