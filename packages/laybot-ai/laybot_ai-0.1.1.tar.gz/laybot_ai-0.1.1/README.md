# LayBot 灵语智教 · Python SDK  
> 教育智能中枢引擎 · 为教学场景深度优化  
> Powered by **LayBot LingTeach AI**   |   官网 <https://ai.laybot.cn>

[![PyPI](https://img.shields.io/pypi/v/laybot-ai?label=sdk&logo=pypi&color=3776AB)](https://pypi.org/project/laybot-ai/)
[![License](https://img.shields.io/badge/License-Apache_2.0-3DA639?logo=apache&logoColor=white)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/laybot-ai.svg?logo=python&color=3776AB)](https://python.org)
[![GDPR](https://img.shields.io/badge/GDPR-Compliant-0C77B8?logo=privacytools)](https://ai.laybot.cn/compliance)
[![K12](https://img.shields.io/badge/K12%E6%95%99%E8%82%B2%E5%AE%89%E5%85%A8-认证通过-2E7D32?logo=openaccess)](https://edu.laybot.cn/safety)

**LayBot 灵语智教** 为 **课堂教学 / 分层辅导 / 作业批改 / 教研创作 / 动态 Q&A** 打磨的 AI 引擎。  
本 Python-SDK 以 **OpenAI 完全兼容** 的请求体，一键接入 LayBot 教育核心模型矩阵，自动完成计费与合规审计，让 Python 开发者专注教学业务本身。

---

## ✨ 选择 LayBot Python-SDK 的理由

| 功能                           | 价值 |
|--------------------------------|------|
| 🛰️ **流式 SSE**                | `stream=True` 即获毫秒级增量反馈 |
| 🛡️ **企业级安全**               | API-Key / IP 白名单、余额预扣、敏感词脱敏 |
| ♻️ **自动指数退避 3 次**         | 429 / 5xx ⇒ 200 ms → 400 ms → 800 ms |
| 🛰️ **Idle-Guard™**             | 只检测“连续空闲 N 秒”不限制总时长，超长输出不卡壳 |
| 💰 **成本透明**                 | 请求级计费，Credit 实时可查 |
| 📦 **零依赖**                   | 仅 `requests`，极简集成 |
| 🤝 **多厂商切换**               | 一行切换 OpenAI / DeepSeek / Groq / Azure-OpenAI |
| 🧠 **教学深度适配**             | 预置 K12 / 高教 / 国际课程推理参数 |
| 🚀 **智能分层教学**             | 动态生成梯度化习题（基础→拓展→竞赛） |
| 📝 **教研创作加速**             | 3 秒生成考点明确的试卷（支持 LaTeX） |

---

## 📦 安装

```bash
pip install laybot-ai          # 官方 PyPI
# 或国内镜像：
pip install laybot-ai -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 🏃‍♂️ 快速上手

### 1. Chat（非流式）

```python
from laybot_ai import Chat

chat = Chat("sk-teach-xxxx")      # 默认直连 LayBot
rsp = chat.completions({
    "model": "LB-Cosmos",
    "messages": [{"role": "user", "content": "解释牛顿第二定律"}]
})
print(rsp["choices"][0]["message"]["content"])
```

### 2. Chat（流式推送）

```python
def on_delta(chunk: dict, done: bool):
    if done:
        print("\n[DONE]")
    else:
        print(chunk["choices"][0]["delta"].get("content", ""), end="", flush=True)

Chat("sk-teach-xxxx").completions(
    {
        "model": "LB-Cosmos",
        "stream": True,
        "messages": [{"role": "user", "content": "莎士比亚风格的告白"}]
    },
    on_stream=on_delta
)
```

### 3. 文档解析

```python
from laybot_ai import Doc
doc = Doc("sk-teach-xxxx")
ret = doc.extract("https://example.com/paper.pdf", mode="auto")
print(ret["response"]["usage"])
```

### 4. 一行切换 OpenAI / DeepSeek / Groq…

```python
chat = Chat("sk-openai-xxxx", vendor="openai",
            base="https://api.openai.com")   # base 可省略 ⇒ 默认值
rsp  = chat.completions({
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}]
})
```

---

## 🧩 教育专属能力

| 能力            | 典型场景 | 对应端点 |
|-----------------|----------|----------|
| **Smart Chat**  | 课堂 Q&A / 知识点讲解 | `/v1/chat` |
| **Doc Parser**  | 课件\|试卷 → 结构化文本 | `/v1/doc` |
| **Essay Grader**| 作文批改 / 润色 | `/v1/chat` + rubric 模板 |
| **Batch Items** | 习题 / 试卷批量生成 | `/v1/chat` batch |
| **Vision QA**   | 图片实验报告解析 | `/v1/chat` + image-in |

---

## ⛑️ 常见错误码

| code  | http | 描述 |
|-------|------|------|
| 40101 | 401  | API_KEY_INVALID — Key 不存在或禁用 |
| 40200 | 402  | INSUFFICIENT_CREDIT — 余额不足 |
| 42900 | 429  | RATE_LIMITED — 触发限流 |

完整表见文档 <https://ai.laybot.cn/docs/errors>

---

## 🔧 高级用法

```python
from laybot_ai import Chat, Client

cli = Client(
    "sk-teach-xxxx",
    base="https://my.corp.gateway",           # 自定义域名
    vendor="laybot",
    timeout={"connect": 5, "idle": 300},      # 超时分离
    on_req=lambda m,u,o: print("REQ:", m, u), # 调试钩子
)
chat = Chat(cli)

chat.completions({
    "model": "LB-Cosmos",
    "messages": [{"role": "user", "content": "Hi"}],
    "endpoint": "/v1/chat/completions"        # 单次覆盖端点
})
```

---

## 🚀 路线图
- Embed / Audio / Vision 端点  
- Async / httpx 版本  
- WebSocket 多轮上下文  
- `pip install laybot-ai[web]` → FastAPI 中间件

---

## 🤝 贡献
欢迎 PR / Issue！  
代码规范：PEP-8 + Ruff + PyTest。

```bash
pip install -e ".[dev]"          # 本地开发模式
pytest                            # 运行全部单测
```

---

## 📜 许可证
Apache-2.0 © 2025 LayBot Inc. – LayBot LingTeach AI
```
