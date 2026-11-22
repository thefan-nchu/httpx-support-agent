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

评测以 **138 条真实 GitHub Issue** 构建，开发 41 道、验证 41 道、留出 56 道。Issue 用作评测问题，检索索引只收录官方文档、分版本发布说明和源码摘录。下表使用 audited-v4 验证集中有参考证据的 **25 道题**，固定语料、切分和查询。BM25 和向量各召回 20 个候选，RRF 按两路名次融合，重排在同一融合池上调整顺序。

| 检索方式 | 候选池凑齐全部证据 | 前 5 凑齐全部证据（Hit@5） | 前 5 至少命中一个要点 | 完整证据 MRR@5 |
| --- | ---: | ---: | ---: | ---: |
| BM25 单路 | 16/25 | 9/25（36%） | 10/25 | 0.2293 |
| 向量单路 | 23/25 | 18/25（72%） | 19/25 | 0.4947 |
| 双路召回 + RRF | 23/25 | 16/25（64%） | 19/25 | 0.4267 |
| 双路召回 + RRF + 模型重排 | 23/25 | **21/25（84%）** | **23/25** | **0.5447** |

**候选覆盖**统计整个候选池能否找齐全部参考要点。**完整 Hit@5** 只看前五个片段。**完整 MRR@5** 反映前五中首次凑齐全部证据的位置，越靠前越高。

- **双路召回**：相对 BM25 单路，加入向量把完整候选覆盖从 **16/25 提到 23/25**，补齐了 7 道题的证据。这一组里，向量单路也覆盖了这 23 道题。
- **RRF 融合**：相对 BM25 单路，完整 Hit@5 从 **9/25 提到 16/25**。相对向量单路，RRF 把 3 道题推入前五，也让 5 道题掉出前五。例如 #2182 首次凑齐证据的位置从向量第 11 位升到融合第 1 位。单独调整 BM25 每文档片段配额，融合完整 Hit@5 从 **12/25 提到 16/25**。
- **模型重排**：固定 RRF 候选池，完整 Hit@5 从 **16/25 提到 21/25**，验证集中 5 道改善、0 道退步。整个候选池的完整覆盖保持 23/25，收益来自排序。


### Ragas 多指标评测

使用 Ragas 0.4.3 对同一批已存端到端结果做复评，保留原答复和原检索前五证据。下表为按题均值。参考文本来自 audited-v4 的冻结答案要点。模型裁判为 qwen3.8-flash，向量模型为 qwen3.7-text-embedding-flash。

| 指标 | 衡量内容 | 均值 |
| --- | --- | ---: | ---: |
| Context Precision | 相关证据是否排在前面 | 0.725 |
| Context Recall | 前五证据是否覆盖参考要点 | 0.729 |
| Context Relevance | 证据整体是否与问题相关 | 0.763 |
| Faithfulness | 最终技术结论能否由检索上下文支持 | 0.815 |
| Answer Relevancy | 完整答复与用户问题有多相关 | 0.547 |
| Answer Correctness | 技术结论与参考要点有多一致 | 0.342 |
| Semantic Similarity | 技术结论与参考要点的向量相似程度 | 0.661 |

41 道登记题中有 1 道预先排除、1 道原运行失败。答复相关性纳入 4 道无技术结论的回复；技术结论指标只评有结论的题，需要参考的指标还要求冻结参考要点。Context Precision 的 2 道结构失败和 Answer Correctness 的 1 道请求失败单列。正确性包含事实匹配和语义相似，分数会受到冻结参考要点的范围与质量影响。各项独立报告。

逐题复核发现，#2653 的 Context Recall 是 1.00，Answer Correctness 约 0.190。证据有 SOCKS 可选依赖的安装说明，最终答复却只讨论了代理配置。#1610 的 Faithfulness 是 1.00，通用代理说明虽然有出处，仍没有解释用户的 EOF 报错。这两题分别提示了**漏答关键条件**和**引用有据但回答不适用**的问题。[Ragas 0.4.3 指标定义](https://docs.ragas.io/en/v0.4.3/concepts/metrics/available_metrics/)

发布包含运行所需官方语料和独立测试。上述历史指标是项目实测摘要，发布包不含真实 Issue 原帖、冻结评测集和内部原始答复，不能仅靠本包复算历史结果。更多细节见 [设计与评测说明](docs/DESIGN.md)。
