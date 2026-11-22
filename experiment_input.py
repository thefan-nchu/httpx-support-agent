"""实验输入脱敏。只处理首帖文本，保留原始数据集和历史产物。"""
import re

from workflow import redact


# 首帖常以 Python 字典或 JSON 展示请求和响应头。匹配完整引号内的值，
# 避免把同一行的 Transfer-Encoding 等其他头部一并抹掉。
_QUOTED_COOKIE = re.compile(
    r"""(?i)(?P<key>["'](?:set-cookie|cookie)["']\s*:\s*)(?P<quote>["'])(?:\\.|(?!(?P=quote))[^\\\r\n])*(?P=quote)"""
)
# 裸 HTTP 头占一行。允许旧式折叠续行，避免凭据落在下一行。
_HEADER_COOKIE = re.compile(
    r"(?im)^(?P<key>[ \t]*(?:set-cookie|cookie)[ \t]*:[ \t]*)[^\r\n]*(?:\r?\n[ \t]+[^\r\n]+)*"
)


def redact_experiment_issue(text):
    """返回可送给实验模型的首帖副本，保留 Cookie 头名和其他诊断上下文。"""
    text = _QUOTED_COOKIE.sub(
        lambda match: f"{match['key']}{match['quote']}[REDACTED]{match['quote']}", text
    )
    text = redact(_HEADER_COOKIE.sub(r"\g<key>[REDACTED]", text))
    return re.sub(r"(?i)([a-z][a-z0-9+.-]*://)[^\s/@]+:[^\s/@]+@", r"\1[REDACTED]@", text)
