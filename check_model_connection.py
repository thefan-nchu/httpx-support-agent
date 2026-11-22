"""读取本地配置，显式运行时执行两个小请求；不打印密钥、请求头或响应正文。

这是接入前连通性检查，不是检索评测。只发送固定教学文本，不上传项目资料。
使用已有httpx访问DashScope原生HTTP协议，无需安装额外SDK。
"""
import argparse
import json
import os
import re
from urllib.parse import urlsplit
from pathlib import Path
from datetime import datetime, timezone
import math
import httpx

ROOT = Path(__file__).resolve().parent


_SHARED_HOSTS = {
    'dashscope.aliyuncs.com', 'dashscope-intl.aliyuncs.com',
    'dashscope-us.aliyuncs.com', 'cn-hongkong.dashscope.aliyuncs.com',
}
_WORKSPACE_HOST = re.compile(
    r"[a-z0-9][a-z0-9-]*[.](?:cn-beijing|cn-hongkong|ap-southeast-1|"
    r"ap-northeast-1|eu-central-1|us-east-1)[.]maas[.]aliyuncs[.]com"
)


def _approved_endpoint(value, paths):
    """校验并规范化 HTTPS 模型地址，拒绝账号信息、非官方地址和多余 URL 部分。"""
    url = urlsplit(value)
    host = url.hostname or ''
    path = url.path.rstrip('/')
    if (url.scheme != 'https' or url.netloc.lower() != host or url.query or url.fragment
            or path not in paths or (host not in _SHARED_HOSTS and not _WORKSPACE_HOST.fullmatch(host))):
        raise ValueError('请配置同一工作区的 HTTPS DashScope 服务地址')
    return f'https://{host}{path}'


def configuration():
    """读取项目.env的简单KEY=VALUE配置，环境变量优先；不执行配置内容。"""
    values = {}
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                values[key.strip()] = value.strip().strip('\"\'')
    for key in ['DASHSCOPE_API_KEY', 'DASHSCOPE_BASE_URL', 'EMBEDDING_MODEL', 'CHAT_MODEL']:
        if key in os.environ:
            values[key] = os.environ[key]
        if not values.get(key):
            raise ValueError('缺少配置字段：' + key)
    native = _approved_endpoint(values['DASHSCOPE_BASE_URL'], {'/api/v1'})
    chat = _approved_endpoint(os.getenv('CHAT_BASE_URL') or values.get('CHAT_BASE_URL') or native,
                              {'/api/v1', '/compatible-mode/v1'})
    # 防止把同一密钥误发给另一个工作区。两种协议可以使用同一主机上的不同路径。
    if urlsplit(native).hostname != urlsplit(chat).hostname:
        raise ValueError('对话与向量接口必须使用同一个 DashScope 主机')
    values.update(DASHSCOPE_BASE_URL=native, CHAT_BASE_URL=chat)
    return values


def check_response(kind, data):
    """只提取必要结构和usage；异常响应不输出可能携带输入或敏感内容的正文。"""
    if data.get('code'):
        raise ValueError('服务返回业务错误，请在服务控制台检查模型权限和配置')
    if kind == 'embedding':
        items = data['output']['embeddings']
        if len(items) != 1:
            raise ValueError('向量数量不符合预期')
        vector = items[0]['embedding']
        if not vector or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in vector):
            raise ValueError('向量不是有效的有限数值数组')
        return {'dimension': len(vector), 'usage': data.get('usage')}
    content = data['output']['choices'][0]['message']['content']
    if not content:
        raise ValueError('回答为空')
    return {'has_content': True, 'usage': data.get('usage')}


def main():
    """默认仅验证配置；--live才产生最多2个API请求，各自保留成功或失败记录。"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true', help='发送两个小请求，会消耗少量额度')
    args = parser.parse_args()
    try:
        config = configuration()
    except ValueError as exc:
        print(str(exc))
        return 1
    if not args.live:
        print('配置字段完整；未联网，未验证Key有效性。')
        return 0
    folder = ROOT / 'artifacts' / 'EXP-006' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder.mkdir(parents=True)
    requests = [
        ('embedding', '/services/embeddings/text-embedding/text-embedding', {
            'model': config['EMBEDDING_MODEL'], 'input': {'texts': ['HTTPX read timeout']},
            'parameters': {'dimension': 1024, 'output_type': 'dense'}}),
        ('chat', '/services/aigc/multimodal-generation/generation', {
            'model': config['CHAT_MODEL'],
            'input': {'messages': [{'role': 'user', 'content': [{'text': '请只回答：连接成功'}]}]},
            'parameters': {'max_tokens': 32, 'enable_thinking': False}}),
    ]
    rows = []
    # 不重试、不跟随重定向，避免无意扩大计费或转发凭据；TLS校验保持开启。
    # 复用正式适配器，检查脚本与产品必须使用相同的回答协议和地址。
    from model_agent import DashScope
    provider = DashScope()
    for kind, route, body in requests:
        row = {'kind': kind, 'model': body['model'], 'status': 'failed'}
        try:
            output = provider.request(kind, body)
            row.update(check_response(kind, {'output': output}), status='success')
        except Exception as exc:
            row['error_type'] = type(exc).__name__
        rows.append(row)
        (folder / 'results.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(folder), 'results': rows}, ensure_ascii=False, indent=2))
    return 0 if all(x['status'] == 'success' for x in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
