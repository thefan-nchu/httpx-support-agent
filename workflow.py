"""Persisted, deterministic investigation graph; no LLM claims or code execution."""
from pathlib import Path
from typing import TypedDict
from datetime import datetime, timezone
import json
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from langgraph.graph import StateGraph, START, END
from retrieval import Corpus
from investigation_state import CaseState, upgrade_case, update_memory, build_query, fact_summary, follow_up

ROOT = Path(__file__).resolve().parent

def now():
    return datetime.now(timezone.utc).isoformat()

def redact(text):
    text = re.sub(r'(?i)(authorization\s*[:=]\s*(?:bearer\s+)?)[^\s]+', r'\1[REDACTED]', text)
    text = re.sub(r'(?i)((?:api[_-]?key|password|token|secret)\s*[:=]\s*)[^\s,;]+', r'\1[REDACTED]', text)
    return text

class Conflict(Exception):
    pass

class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, revision INTEGER NOT NULL, updated TEXT NOT NULL, body TEXT NOT NULL)')

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def create(self):
        state = {'id': str(uuid.uuid4()), 'revision': 0, 'created_at': now(), 'updated_at': now(),
            'messages': [], 'trace': [], 'evidence': [], 'attempts': [], 'version': '',
            'status': 'new', 'next': 'inspect', 'turns': 0, 'summary': '', 'query': '',
            'pending': '', 'answer': '', 'warnings': [], 'mode': 'deterministic-no-model'}
        state = upgrade_case(state)
        with self.connect() as db:
            db.execute('INSERT INTO sessions VALUES (?,?,?,?)',
                       (state['id'], 0, state['updated_at'], json.dumps(state, ensure_ascii=False)))
        return state

    def get(self, sid):
        with self.connect() as db:
            row = db.execute('SELECT body FROM sessions WHERE id=?', (sid,)).fetchone()
        if row is None:
            raise KeyError(sid)
        return upgrade_case(json.loads(row[0]))

    def list(self):
        with self.connect() as db:
            rows = db.execute('SELECT body FROM sessions ORDER BY updated DESC LIMIT 50').fetchall()
        return [{'id': s['id'], 'summary': s['summary'], 'status': s['status'], 'updated_at': s['updated_at']}
                for (body,) in rows for s in [json.loads(body)]]

    def save(self, state):
        prior = state['revision']
        new = {**state, 'revision': prior + 1, 'updated_at': now()}
        with self.connect() as db:
            cursor = db.execute('UPDATE sessions SET revision=?,updated=?,body=? WHERE id=? AND revision=?',
                (new['revision'], new['updated_at'], json.dumps(new, ensure_ascii=False), state['id'], prior))
            if cursor.rowcount != 1:
                raise Conflict('会话已被另一个请求更新，请刷新后重试。')
        state.update(new)
        return state

class GraphState(TypedDict):
    case: CaseState

class Investigator:
    def __init__(self, corpus=None, store=None):
        self.corpus = corpus or Corpus()
        self.store = store or Store(ROOT / 'data' / 'sessions.sqlite3')
        graph = StateGraph(GraphState)
        graph.add_node('inspect', self.inspect)
        graph.add_node('retrieve', self.retrieve)
        graph.add_node('respond', self.respond)
        graph.add_conditional_edges(START, lambda s: s['case']['next'],
                                    {'inspect': 'inspect', 'retrieve': 'retrieve', 'respond': 'respond'})
        graph.add_conditional_edges('inspect', lambda s: s['case']['next'],
                                    {'retrieve': 'retrieve', 'respond': 'respond'})
        graph.add_edge('retrieve', 'respond')
        graph.add_edge('respond', END)
        self.graph = graph.compile()

    def checkpoint(self, case, node, detail, started):
        case['trace'].append({'node': node, 'at': now(), 'detail': detail,
                              'elapsed_ms': round((time.perf_counter()-started)*1000, 2)})
        self.store.save(case)
        return {'case': case}

    def inspect(self, state):
        start = time.perf_counter()
        case = state['case']
        text = case['pending']
        if not case['summary']:
            case['summary'] = text[:160]
        update_memory(case, text, case['turns'], case['messages'][-1]['at'] if case['messages'] else now())
        case['query'] = build_query(case)
        case['warnings'] = []
        if not case['version']:
            case['status'] = 'needs_info'
            case['answer'] = '版本尚未明确，暂不检索。' + follow_up(case)
            case['next'] = 'respond'
        elif case['version'] != '0.28.1':
            case['status'] = 'version_mismatch'
            case['evidence'] = []
            case['answer'] = f"当前版本为 {case['version']}，本地文档仅覆盖 0.28.1。已停止版本相关建议；请导入匹配版本资料。不要为了匹配演示而升级实际环境。"
            case['next'] = 'respond'
        else:
            case['next'] = 'retrieve'
        return self.checkpoint(case, 'inspect', {'version': case['version'], 'next': case['next']}, start)

    def retrieve(self, state):
        start = time.perf_counter()
        case = state['case']
        try:
            docs = self.corpus.search(case['query'], version=case['version'], kind='doc', limit=4)
            issues = self.corpus.search(case['query'], version=case['version'], kind='issue', limit=1)
            case['evidence'] = docs + issues if docs else []
            case['status'] = 'evidence_ready' if docs else 'insufficient_evidence'
            if issues and docs:
                case['warnings'].append('历史 Issue 未验证与当前版本相同，仅供线索参考；未导入解决评论。')
        except Exception as exc:
            case['status'] = 'tool_error'
            case['evidence'] = []
            case['warnings'].append('检索工具失败：' + type(exc).__name__ + '；没有生成诊断。')
        case['next'] = 'respond'
        return self.checkpoint(case, 'retrieve', {'tool': 'search_local_corpus',
            'query': case['query'], 'results': [e['chunk_id'] for e in case['evidence']],
            'status': case['status']}, start)

    def respond(self, state):
        start = time.perf_counter()
        case = state['case']
        if case['status'] == 'evidence_ready':
            case['answer'] = ('已检索到候选资料，相关性分数不代表根因置信度。\n'
                '已记录（用户提供，未独立验证）：' + fact_summary(case) + '\n' + follow_up(case))
            if case['attempts']:
                case['answer'] += f"\n已记录 {len(case['attempts'])} 项尝试及反馈，尚未独立验证。"
        elif case['status'] == 'insufficient_evidence':
            case['answer'] = '没有检索到足够的词汇匹配证据。' + follow_up(case)
        elif case['status'] == 'tool_error':
            case['answer'] = '本轮检索失败，会话已保留。修复工具问题后可继续提交问题；当前没有可支持的结论。'
        case['messages'].append({'role': 'assistant', 'content': case['answer'], 'at': now()})
        case['next'] = 'inspect'
        return self.checkpoint(case, 'respond', {'status': case['status'], 'model_calls': 0}, start)

    def turn(self, sid, message, revision):
        case = self.store.get(sid)
        if revision != case['revision'] or case['status'] == 'running' or case['next'] != 'inspect':
            raise Conflict('会话版本过期或仍在运行，请刷新；中断任务请使用恢复。')
        if case['turns'] >= 12:
            raise ValueError('已达到每次调查 12 轮预算，请导出报告或开始新调查。')
        text = redact(message.strip())
        if not text or len(text) > 6000:
            raise ValueError('请输入 1-6000 字符。')
        case['messages'].append({'role': 'user', 'content': text, 'at': now()})
        case.update(pending=text, status='running', next='inspect', turns=case['turns']+1)
        self.store.save(case)
        return self.graph.invoke({'case': case})['case']

    def resume(self, sid, revision):
        case = self.store.get(sid)
        if revision != case['revision']:
            raise Conflict('会话版本过期，请刷新。')
        # next node survives a process exit, including after inspect/retrieve.
        if case['status'] == 'running' or (case['next'] in ['retrieve', 'respond']):
            self.store.save(case)
            return self.graph.invoke({'case': case})['case']
        return case

def report(case):
    """导出当前调查及各轮审查快照，按本轮编号查找历史引文。"""
    lines = ['# HTTPX 调查报告', '', f"调查编号：{case['id']}",
        f"模式：{case.get('mode', '无模型确定性检索')} / 状态：{case['status']}", f"HTTPX 版本：{case['version'] or '未知'}",
        '', '## 问题', case['summary'], '', '## 当前结果', case['answer'],
        '', '## 用户报告的尝试（未独立验证）']
    lines.extend('- ' + a['text'] for a in case['attempts'])
    if not case['attempts']:
        lines.append('尚未提供。')
    lines.extend(['', '## 当前调查事实（用户提供，未独立验证）', fact_summary(upgrade_case(case)),
                  '', '## 事实更正记录', json.dumps(case['fact_history'], ensure_ascii=False, indent=2),
                  '', '## 当前引用证据'])
    for evidence in case['evidence']:
        lines.extend([f"- [{evidence['title']}]({evidence['url']})", f"  版本：{evidence['version']}；SHA256：{evidence['sha256']}",
                      '  摘录：' + evidence['text'].replace('\n', '\n  > ')])
    rounds=case.get('evidence_rounds',[])
    if rounds:
        lines.extend(['','## 各轮证据与版本复查'])
    for item in rounds:
        lines.extend(['',f"### 第 {item['turn']} 轮 · HTTPX {item['reported_version'] or '未知'}"])
        change=item.get('version_recheck')
        if change:
            result='复查完成' if change['status']=='completed' else '复查失败，尚无新结果'
            previous=f"第 {change['previous_turn']} 轮结论需按新版本复查。 " if change['previous_turn'] is not None else ''
            lines.append(f"报告版本：{change['from'] or '未知'} → {change['to']}。{previous}{result}。")
        if not item['claims']:
            lines.append('本轮没有保存已审查的证据结论。')
        sources={s['citation']:s for s in item['sources']}
        for claim in item['claims']:
            lines.append('- '+claim['text'])
            for ref in claim['evidence']:
                source=sources[ref['citation']]
                lines.append(f"  - [{ref['citation']} · {source.get('title', '来源')}]({source.get('url', '')})"
                             f"（资料版本 {source.get('version', '未知')}）：{ref['quote']}")
    lines.extend(['', '## 不确定性', '未执行复现；未判定根因；检索分数不代表可信度；历史 Issue 版本可能不匹配。',
                  '', '## 对话记录'])
    for message in case['messages']:
        lines.extend([f"### {message['role']} / {message['at']}", message['content'], ''])
    lines.extend(['## 下一步', '补充环境、最小复现和已尝试步骤；由维护者审核证据与结论。'])
    return '\n'.join(lines)
