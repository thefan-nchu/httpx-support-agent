"""Small transparent BM25 index. No embeddings, inference, or network calls."""
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPANSIONS = {
    '超时': 'timeout timeouts ReadTimeout ConnectTimeout PoolTimeout',
    '连接池': 'pool connection limits PoolTimeout max_connections',
    '代理': 'proxy proxies HTTP_PROXY HTTPS_PROXY',
    '证书': 'SSL certificate verify certifi',
    '异步': 'async AsyncClient asyncio',
    '重定向': 'redirect follow_redirects TooManyRedirects',
    '连接复用': 'Client connection pooling',
    '环境变量': 'environment variables trust_env',
    '流式': 'stream streaming aiter_bytes',
    '编码': 'encoding charset unicode',
    '重试': 'retries HTTPTransport',
    '上传': 'upload multipart files',
    '报错': 'exception',
}
STOP = set(
    'the a an is are was were to of and or for in on with i it this that httpx python please how can do does not using use'.split())


def tokens(text):
    words = re.findall(r'[a-zA-Z_][a-zA-Z_0-9]*', text.lower())
    for phrase in re.findall(r'[\u4e00-\u9fff]+', text):
        words.extend(phrase[i:i + 2] for i in range(max(1, len(phrase) - 1)))
    return [word for word in words if word not in STOP]


def expand(query):
    return query + ' ' + ' '.join(value for key, value in EXPANSIONS.items() if key in query)


def paragraph_chunks(text):
    """保持原切分规则，按空行累积，超过1600字符的段再按字符拆。"""
    pieces, current = [], ''
    for paragraph in text.split('\n\n'):
        if len(current) + len(paragraph) > 1600 and current:
            pieces.append(current)
            current = ''
        for offset in range(0, len(paragraph), 1600):
            part = paragraph[offset:offset + 1600]
            if current and len(current) + len(part) > 1600:
                pieces.append(current)
                current = ''
            current += part + '\n\n'
    if current:
        pieces.append(current)
    return pieces


def heading_boundaries(text):
    """返回围栏外 Markdown 标题的字符位置，围栏内的标题保留在同一章节。"""
    offset = 0
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if marker:
            run, suffix = marker.groups()
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence) and not suffix.strip():
                fence = None
        elif fence is None and offset and re.match(r'^ {0,3}#{1,6}\s+\S', line):
            yield offset
        offset += len(line)


def heading_chunks(text):
    """按围栏外标题分节，章节内继续用原长度规则。"""
    boundaries = [0, *heading_boundaries(text), len(text)]
    sections = [text[a:b].rstrip('\r\n') for a,b in zip(boundaries, boundaries[1:])]
    return [piece for section in sections for piece in paragraph_chunks(section) if piece.strip()]


def packed_heading_chunks(text):
    """仅对长文档用标题优先的1600字符窗口，合并过短小节。"""
    if len(text) <= 3200:
        return paragraph_chunks(text)
    headings = list(heading_boundaries(text))
    paragraphs = [m.end() for m in re.finditer(r'\r?\n[ \t]*\r?\n', text)]
    start, parts = 0, []
    while len(text) - start > 1600:
        # 优先保留至少900字符的上下文，临近末尾给末段留下至少500字符。
        maximum = min(start + 1600, len(text) - 500)
        preferred = [end for end in headings if start + 900 <= end <= maximum]
        fallback = [end for end in paragraphs if start + 900 <= end <= maximum]
        end = max(preferred or fallback or [maximum])
        parts.append(text[start:end])
        start = end
    parts.append(text[start:])
    return parts


class Corpus:
    def __init__(self, data_dir=None, *, chunker=paragraph_chunks, doc_chunker=None):
        """加载语料。可注入全局切分器，也可仅让官方用法文档使用替代切分。"""
        self.data_dir = Path(data_dir or ROOT / 'data')
        self.manifest = json.loads((self.data_dir / 'manifest.json').read_text(encoding='utf-8'))
        self.chunks = []
        for source in self.manifest['records']:
            # A changelog snapshot contains historical APIs; do not label its old
            # release sections as current-version guidance.
            if source['kind'] == 'license' or source['id'] == 'CHANGELOG.md':
                continue
            content = (self.data_dir / source['path']).read_bytes()
            if hashlib.sha256(content).hexdigest() != source['sha256']:
                raise ValueError('Corpus checksum mismatch: ' + source['id'])
            text = content.decode('utf-8')
            if source['kind'] == 'issue':
                issue = json.loads(text)
                text = issue['title'] + '\n\n' + (issue['body'] or '')
            split = doc_chunker if doc_chunker is not None and source['kind']=='doc' else chunker
            for index, part in enumerate(split(text)):
                self.chunks.append({**source, 'chunk_id': source['id'] + ':' + str(index),
                                    'text': part.strip(), 'tf': Counter(tokens(source['title'] + '\n' + part))})
        self.df = Counter()
        for chunk in self.chunks:
            self.df.update(chunk['tf'].keys())
        self.average = sum(sum(c['tf'].values()) for c in self.chunks) / max(1, len(self.chunks))

    def search(self, query, version='0.28.1', kind='all', enhanced=True, limit=5, exclude=(), per_source=1):
        """用 BM25 排序。per_source 控制每份文档的片段上限，None 表示不限。"""
        query_tokens = set(tokens(expand(query) if enhanced else query))
        results = []
        for chunk in self.chunks:
            if chunk['id'] in exclude or (kind != 'all' and chunk['kind'] != kind):
                continue
            # Do not silently serve docs for another version. Issue versions are unknown.
            if chunk['kind'] == 'doc' and chunk['version'] != version:
                continue
            tf = chunk['tf']
            length = sum(tf.values())
            score = 0.0
            for term in query_tokens:
                count = tf.get(term, 0)
                if count:
                    idf = math.log(1 + (len(self.chunks) - self.df[term] + 0.5) / (self.df[term] + 0.5))
                    score += idf * count * 2.5 / (count + 1.5 * (0.25 + 0.75 * length / max(1, self.average)))
            if score > 0:
                results.append({k: v for k, v in chunk.items() if k != 'tf'} | {'score': round(score, 4)})
        results.sort(key=lambda r: (-r['score'], r['chunk_id']))
        # 先按片段得分排序，再限制每份文档的配额，总候选数仍由 limit 控制。
        selected, seen = [], Counter()
        for result in results:
            if per_source is None or seen[result['id']] < per_source:
                selected.append(result)
                seen[result['id']] += 1
            if len(selected) >= limit:
                break
        return selected
