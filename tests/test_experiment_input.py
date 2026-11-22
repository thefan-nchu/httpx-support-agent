"""核验实验采集脱敏，不发送model请求。"""
import unittest

from experiment_input import redact_experiment_issue


class ExperimentInputTest(unittest.TestCase):
    """覆盖真实首帖格式及常见请求和响应头布局。"""

    def test_header_dictionaries_preserve_neighbouring_evidence(self):
        """遮蔽字典和 JSON 的值，仍能查证同一行里的协议错误。"""
        example = """{'Set-Cookie': 'synthetic-id=sample-A; Secure', 'Transfer-Encoding': 'chunked, chunked'}
{"cOoKiE": "synthetic-id=sample-B", "Content-Type": "text/plain"}"""
        actual = redact_experiment_issue(example)
        self.assertEqual(actual, """{'Set-Cookie': '[REDACTED]', 'Transfer-Encoding': 'chunked, chunked'}
{"cOoKiE": "[REDACTED]", "Content-Type": "text/plain"}""")

    def test_raw_header_and_continuation_are_redacted(self):
        """截断折叠的全部值，保留后续头、报错，并允许重复处理。"""
        example = "Cookie: abc=sample-A\r\n\tmore=sample-B\r\nSet-Cookie: sid=sample-C\r\nTransfer-Encoding: chunked\r\nRemoteProtocolError"
        actual = redact_experiment_issue(example)
        self.assertEqual(actual, "Cookie: [REDACTED]\r\nSet-Cookie: [REDACTED]\r\nTransfer-Encoding: chunked\r\nRemoteProtocolError")
        self.assertEqual(redact_experiment_issue(actual), actual)
