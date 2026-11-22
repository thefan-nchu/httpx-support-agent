"""将长首帖压缩成检索查询，优先保留首尾和中段技术线索。"""
import re

CHECKLIST = re.compile(r'^\s*-\s*\[[ xX]\]')
TRACE_FRAME = re.compile(r'^\s*File ["\'].*?, line \d+')
SIGNALS = re.compile(
    r'\b(?:[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+|\w+(?:Error|Timeout|Exception)|'
    r'\d+\.\d+\.\d+|[a-z][a-z0-9]*(?:_[a-z0-9]+)+)\b|`[^`\n]{1,80}`')


def focused_query(title, body, limit=1800):
    """返回预算内的查询。短帖保持原文，长帖保留结尾并从中段抽取技术行。"""
    full = title + '\n' + body
    if len(full) <= limit:
        return full
    heading = title.strip()[:limit//4]
    lines = []
    seen = set()
    # 跳过模板勾选、重复行及重复栈帧，保留实际异常行和代码中的参数。
    for raw in body.splitlines():
        line = raw.strip()
        if (not line or line in seen or CHECKLIST.match(line) or TRACE_FRAME.match(line)
                or line in ('```', '---') or line.startswith('<!--')):
            continue
        seen.add(line)
        lines.append(line)
    cleaned = '\n'.join(lines)
    budget = limit - len(heading) - 1
    if len(cleaned) <= budget:
        return heading+'\n'+cleaned
    head_len = budget*65//100
    tail_len = budget*25//100
    head, tail = cleaned[:head_len], cleaned[-tail_len:]
    middle = cleaned[head_len:-tail_len]
    available = budget - len(head) - len(tail) - 2
    hints = []
    covered = {x.group().lower() for x in SIGNALS.finditer(head+'\n'+tail)}
    ranked = []
    for index, line in enumerate(middle.splitlines()):
        matches = list(SIGNALS.finditer(line))
        unique = {match.group().lower() for match in matches}
        if unique - covered:
            ranked.append((-len(unique-covered), index, line, matches))
    for _, _, line, matches in sorted(ranked):
        match = next((m for m in matches if m.group().lower() not in covered), None)
        if match is None or available < 50:
            continue
        start = max(0,match.start()-35)
        hint = line[start:start+min(170,available)].strip()
        hints.append(hint)
        available -= len(hint)+1
        covered.update(m.group().lower() for m in SIGNALS.finditer(hint))
    return '\n'.join([heading, head, *hints, tail])
