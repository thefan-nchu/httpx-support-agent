# HTTPX Support Agent Lab

面向 HTTPX 的技术支持调查工作台。用户补充或更正版本后，应用会结合原问题重新检索和审查答复。每轮引文保留自己的来源，便于复盘版本变化和证据不足的原因。

A local technical support agent for HTTPX with version-aware evidence, persistent investigation state, and per-turn citations.

- **调查链路**：LangGraph 编排问题检查、检索和回复。SQLite 保存会话、事实更正、轮次证据和失败轨迹。
- **证据答复**：BM25 与向量召回、RRF 融合和模型重排。先逐字核对引用，再审查是否支持结论与版本范围。
- **可复查结果**：版本变化后重查证据，历史引文仍指向各自来源。可在网页查看并导出 Markdown 报告。

## 本地运行

需要 Python 3.13（发布包在 Python 3.13 下验证）及 pip。先在项目根目录建立环境。

```bash
python -m venv .venv
```

Windows PowerShell 使用：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8767
```

macOS / Linux 使用：

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8767
```

打开 [本地调查工作台](http://127.0.0.1:8767)。默认是无需密钥的确定性检索模式。可输入「HTTPX 0.28.1 出现 PoolTimeout，如何排查？」查看资料与报告。

### 演示多轮版本复查

用已安装依赖的 Python 运行 `python -X utf8 -B demo_version_recheck.py`。这是不联网的演示，使用固定模型答复和真实官方引文，输出报告到本地 `artifacts/`。用 `python -X utf8 -B -m unittest discover -s tests -v` 运行发布版离线测试。

### 使用真实模型

1. 将 `.env.example` 复制为本地 `.env`，填写自己的 DashScope API Key。根据控制台设置同一工作区的向量、对话地址和可用模型。配置示例使用 [Alibaba Cloud Model Studio 官方端点](https://docs.modelstudio.console.alibabacloud.com/en/model-studio/base-url)。
2. Windows PowerShell 在启动前设置 `$env:SUPPORT_MODEL_MODE = '2'`。macOS / Linux 在同一个 shell 执行 `export SUPPORT_MODEL_MODE=2`，再用上面的命令启动。
3. 示例中先报告「HTTPX 0.28.1 用 AsyncClient 的 GET 参数传 Cookie，重定向后丢失」，再回复「更正，实际使用 HTTPX 0.16.1。同源跳转也出现问题」。展开「各轮证据与版本复查」，查看和导出两轮引文。

真实模型模式会发送问题和证据给配置服务，并产生调用费用。首次索引可能调用多次向量服务。应用面向本地演示，避免输入密钥或个人数据。

## 评测说明

历史固定候选池中，模型重排把完整证据 Hit@5 从 **16/25** 提升到 **21/25**。独立端到端基线以模型辅助评分，参考组答复联合达标 **14/25**。三组多轮开发诊断全部保留前后引文，两组完整保留孤立第二轮遗漏的场景信息，一组部分保留。仍观察到跨版本推断，未通过答复质量门槛。

发布包含运行所需官方语料和独立测试。上述历史指标是项目实测摘要，发布包不含真实 Issue 原帖、冻结评测集和内部原始答复，不能仅靠本包复算历史结果。更多细节见 [设计与评测说明](docs/DESIGN.md)。

随包附带的 HTTPX 文档、发布说明和源码摘录以语料清单固定上游提交。许可与版权见 [HTTPX-LICENSE.md](HTTPX-LICENSE.md)。
