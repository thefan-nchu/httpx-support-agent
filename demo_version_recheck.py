"""离线演示版本复查。模型和检索选择使用固定夹具，引文来自随包附带的 HTTPX 语料。"""
import json
from pathlib import Path
import uuid

from evidence_workflow import EvidenceInvestigator
from retrieval import Corpus
from workflow import Store, report


CURRENT_QUOTE = 'If using a client instance, then cookies should always be set on the client'
HISTORY_QUOTE = 'When using a client instance, cookies should always be set on the client'


class DemoReplies:
    """模拟对话协议以展示状态转移，无网络调用，也无随机模型输出。"""

    config = {'CHAT_MODEL': 'offline-fixture'}

    def chat(self, messages, first=False):
        """返回空工具计划，让正式工作流走检索回退。"""
        return {'tool_calls': []}

    def request(self, kind, body):
        """按两轮演示返回结构化结论或审查索引。"""
        if body['parameters']['max_tokens'] == 1200:
            value = {'keep_claims': [0], 'keep_limitations': [0], 'keep_follow_up': []}
        else:
            context = body['input']['messages'][1]['content'][0]['text']
            historical = '0.16.1' in context
            quote = HISTORY_QUOTE if historical else CURRENT_QUOTE
            claim = ('0.18.0 发布说明要求将 Cookie 设置在客户端，而非单次请求。' if historical
                     else '0.28.1 兼容性文档建议把 Cookie 设置在客户端。')
            value = {'disposition': 'partial', 'claims': [{'text': claim,
                'evidence': [{'citation': 'E1', 'quote': quote}]}], 'follow_up': [],
                'limitations': ['该资料未单独验证用户报告的故障机制。']}
        return {'choices': [{'message': {'content': json.dumps(value, ensure_ascii=False)}}]}


class DemoEvidence:
    """从真实语料选出两条固定证据，便于观察 E1 在轮次间如何变化。"""

    def __init__(self, corpus):
        self.current = next(c for c in corpus.chunks if CURRENT_QUOTE in c['text'])
        self.history = next(c for c in corpus.chunks if c['version'] == '0.18.0' and HISTORY_QUOTE in c['text'])

    def search(self, query):
        """按用户报告版本返回演示资料，保留原始文本和来源。"""
        return [self.history if '0.16.1' in query else self.current]


def main():
    """以隔离 SQLite 执行两轮 HTTPX 版本更正，并导出可阅读报告。"""
    root = Path(__file__).resolve().parent
    output = root / 'artifacts' / f'version-demo-{uuid.uuid4().hex[:8]}'
    output.mkdir(parents=True)
    corpus = Corpus(root / 'data/corpus-v3')
    agent = EvidenceInvestigator(provider=DemoReplies(), corpus=corpus,
                                 store=Store(output / 'sessions.sqlite3'))
    agent.tool = DemoEvidence(corpus)
    seed = agent.store.create()
    first = agent.turn(seed['id'], 'HTTPX 0.28.1 的逐请求 Cookie 在重定向后丢失。', seed['revision'])
    last = agent.turn(seed['id'], '更正，实际使用 HTTPX 0.16.1。同源跳转也出现问题。', first['revision'])
    assert last['version_recheck']['status'] == 'completed'
    assert len(last['evidence_rounds']) == 2 and all(r['claims'] for r in last['evidence_rounds'])
    assert last['evidence_rounds'][0]['sources'][0]['url'] != last['evidence_rounds'][1]['sources'][0]['url']
    dest = output / 'report.md'
    dest.write_text('> 离线演示：模型输出为固定夹具，原文引文来自随包语料。\n\n'
                    + report(agent.store.get(last['id'])), encoding='utf-8')
    print(dest)


if __name__ == '__main__':
    main()
