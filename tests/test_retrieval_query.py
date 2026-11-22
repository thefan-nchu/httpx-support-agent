"""覆盖全文查询的长度、后文条件和短帖兼容。"""
import unittest

from retrieval_query import focused_query


class FocusedQueryTests(unittest.TestCase):
    def test_short_question_keeps_original_layout(self):
        """短帖保留原文和内部换行。"""
        self.assertEqual(focused_query('读取超时', '第一行\n\n第二行'), '读取超时\n第一行\n\n第二行')

    def test_long_report_keeps_late_condition_inside_budget(self):
        """后文条件与异常可参加检索，重复栈帧和勾选模板被移除。"""
        body = '- [x] 模板\n'+'\n'.join(f'普通日志 {i} 内容内容' for i in range(250))
        body += '\n  File "fixture.py", line 2\n使用 NO_PROXY 时出现 ProxyError。'
        query = focused_query('代理连接异常', body)
        self.assertTrue(query.startswith('代理连接异常\n'))
        self.assertLessEqual(len(query), 1800)
        self.assertIn('NO_PROXY', query)
        self.assertIn('ProxyError', query)
        self.assertNotIn('fixture.py', query)
        self.assertNotIn('模板', query)
