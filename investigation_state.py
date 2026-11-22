"""Explicit, bounded conversation memory. No inference, network, or DB writes."""
import re
from typing import TypedDict, Literal

SCHEMA_VERSION = 2

class Fact(TypedDict):
    value: str | int | bool
    turn: int
    source_text: str

class CaseState(TypedDict, total=False):
    # Partial annotations describe the persisted extension; runtime validation is explicit.
    schema_version: int
    facts: dict[str, Fact]
    fact_history: list[dict]
    context_notes: list[dict]
    asked_fields: list[str]
    messages: list[dict]
    attempts: list[dict]
    version: str
    next: Literal['inspect', 'retrieve', 'respond']
    status: Literal['new', 'running', 'needs_info', 'version_mismatch', 'evidence_ready', 'insufficient_evidence', 'tool_error']

LABELS = {'httpx_version':'HTTPX 版本', 'python_version':'Python 版本',
          'exception_type':'异常类名', 'client_type':'客户端类型',
          'proxy':'代理配置', 'concurrency':'并发数'}
PATTERNS = {
    'httpx_version': r'(?i)httpx\s*(?:版本|version|==|v|:|：)?\s*(\d+\.\d+\.\d+)',
    'python_version': r'(?i)python\s*(?:版本|version|==|v|:|：)?\s*(\d+\.\d+(?:\.\d+)?)',
    'exception_type': r'\b(PoolTimeout|ReadTimeout|ConnectTimeout|WriteTimeout|ConnectError|ReadError|ProxyError|HTTPStatusError|RemoteProtocolError)\b',
    'client_type': r'\b(AsyncClient|Client)\b',
    'concurrency': r'(\d+)\s*(?:个\s*)?并发|并发(?:数|量)?\s*(?:为|是|=|：|:)?\s*(\d+)',
}
PROXY = re.compile(r'没有(?:配置|使用)?代理|未(?:配置|使用)代理|不(?:使用|走)代理|无代理|(?:使用|配置|经过|通过|走)(?:了)?代理', re.I)

def initialize(case):
    case.setdefault('facts', {})
    case.setdefault('fact_history', [])
    case.setdefault('context_notes', [])
    case.setdefault('asked_fields', [])
    return case

def record_fact(case, key, value, turn, text):
    old = case['facts'].get(key)
    if old and old['value'] == value:
        return
    fact = {'value': value, 'turn': turn, 'source_text': text[:500]}
    if old:
        case['fact_history'].append({'field': key, 'previous': old, 'replacement': fact})
    case['facts'][key] = fact

def update_memory(case, text, turn, at):
    initialize(case)
    residual = text
    # Do not promote questions, examples or explicit uncertainty into facts.
    clauses = re.split(r'[，,。；;\n]', text)
    assertions = '\n'.join(c for c in clauses if not re.search(
        r'可能|不确定|是否|是不是|例如|比如|或者|还是|[?？]|\bor\b', c, re.I))
    for key, pattern in PATTERNS.items():
        matches = list(re.finditer(pattern, assertions))
        if matches:
            match = matches[-1]  # Most recent explicit mention wins, no semantic guessing.
            value = next(g for g in match.groups() if g is not None)
            record_fact(case, key, int(value) if key == 'concurrency' else value, turn, match.group(0))
            residual = re.sub(pattern, '', residual)
    if not case['facts'].get('httpx_version') and re.fullmatch(r'\s*\d+\.\d+\.\d+\s*', text):
        record_fact(case, 'httpx_version', text.strip(), turn, text)
        residual = ''
    proxy_matches = list(PROXY.finditer(assertions))
    if proxy_matches:
        phrase = proxy_matches[-1].group(0)
        value = not phrase.startswith(('没有','未','不','无'))
        record_fact(case, 'proxy', value, turn, phrase)
        residual = PROXY.sub('', residual)
    case['version'] = str(case['facts'].get('httpx_version', {}).get('value', case.get('version','')))
    # Only explicit tried-actions become attempts. 'still' alone is not an action.
    attempt = re.search(r'(?:已(?:经)?试过|尝试过|试过|tried)\s*(.+?)(?=[，,。；;\n]|$)', text, re.I)
    if attempt:
        action = attempt.group(1).strip()
        key = re.sub(r'\s+', '', action).lower().replace('max_connections','连接数').replace('调大','增加')
        outcome = 'reported_failed' if re.search(r'仍然|无效|失败|still|did not work', text, re.I) else 'reported_unknown'
        existing = next((a for a in case['attempts'] if a.get('action_key') == key), None)
        observation = {'turn':turn, 'at':at, 'text':text[:1200], 'outcome':outcome}
        if existing:
            if not any(o['turn'] == turn for o in existing.get('observations', [])):
                existing.setdefault('observations', []).append(observation)
            existing['outcome'] = outcome
        else:
            case['attempts'].append({'text':text[:1200], 'at':at, 'source':'user_report_unverified',
                'action':action, 'action_key':key, 'outcome':outcome, 'observations':[observation]})
    residual = re.sub(r'(刚才说错了|更正|改为|其实|不是|而是)', '', residual).strip(' ，,。；;:\n')
    if residual and not any(n['turn'] == turn for n in case['context_notes']):
        case['context_notes'].append({'turn':turn,'text':residual[:500]})
        case['context_notes'] = case['context_notes'][-6:]

def upgrade_case(case):
    version = case.get('schema_version', 1)
    if version not in (1, 2):
        raise ValueError('不支持此会话结构版本，请使用匹配的程序。')
    if case.get('next') not in ('inspect','retrieve','respond'):
        raise ValueError('会话的下一节点无效。')
    initialize(case)
    if version == 1:
        # Reconstruct only completed user input. The pending inspect node consumes its input itself.
        users = [m for m in case['messages'] if m['role'] == 'user']
        if case['status'] == 'running' and case['next'] == 'inspect':
            users = users[:-1]
        old_attempts = case['attempts']
        case['attempts'] = []
        for turn, message in enumerate(users, 1):
            update_memory(case, message['content'], turn, message['at'])
        # Keep legacy records that cannot be reconstructed by the narrower new rules.
        texts = {o['text'] for a in case['attempts'] for o in a.get('observations', [])}
        case['attempts'].extend(a for a in old_attempts if a['text'] not in texts)
        if case.get('version') and 'httpx_version' not in case['facts']:
            record_fact(case, 'httpx_version', case['version'], 0, 'legacy version field')
    case['schema_version'] = SCHEMA_VERSION
    return case

def build_query(case):
    parts = [n['text'] for n in case['context_notes']]
    for key, fact in case['facts'].items():
        value = fact['value']
        # Negative proxy state is not a positive keyword; BM25 cannot understand negation.
        if key == 'proxy':
            if value:
                parts.append('proxy')
        elif key in ('exception_type','client_type'):
            parts.append(str(value))
        elif key == 'concurrency':
            parts.append(f'并发数 {value}')
    return '\n'.join(parts)

def fact_summary(case):
    return '；'.join(f"{LABELS[key]}：{('使用' if f['value'] else '未使用') if key == 'proxy' else f['value']}（第{f['turn']}轮）"
                    for key, f in case['facts'].items())

def follow_up(case):
    questions = {'httpx_version':'请补充 HTTPX 的准确版本，例如 HTTPX 0.28.1。',
                 'exception_type':'请补充准确的异常类名，例如 PoolTimeout；若没有异常，请描述具体表现。',
                 'client_type':'请补充客户端类型：Client 还是 AsyncClient？'}
    for key, question in questions.items():
        if key not in case['facts'] and key not in case['asked_fields']:
            case['asked_fields'].append(key)
            return question
    missing = [LABELS[k] for k in questions if k not in case['facts']]
    if missing:
        return '待补充：' + '、'.join(missing) + '。上述信息仍未明确，可以继续补充或导出报告。'
    return '关键类型信息已记录。请对照引用资料验证，并反馈具体结果；当前尚未独立复现或确认根因。'
