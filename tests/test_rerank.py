"""验证重排响应只能重组已有候选，使用模拟服务，无网络调用。"""
import unittest
from unittest.mock import Mock, patch
from grounded_agent import RerankedReferenceTool

from rerank import rerank


class RerankTests(unittest.TestCase):
    def test_production_search_uses_quota_three_and_falls_back(self):
        """付费重排不可用时返回以前的RRF顺序，并标注实际方法。"""
        tool = object.__new__(RerankedReferenceTool)
        tool.provider = Mock()
        tool.candidates = Mock(return_value=([{'chunk_id':'a','title':'A','text':'first'}],[]))
        with patch('grounded_agent.rerank',side_effect=RuntimeError('fixture')):
            rows = tool.search('question')
        tool.candidates.assert_called_once_with('question',per_source=3)
        self.assertEqual(rows[0]['ranking_method'],'rrf_fallback')

    def test_indices_map_to_original_passages(self):
        """服务索引对应原输入位置，分数随该片段返回。"""
        items = [{'title':'A','text':'first','chunk_id':'a'}, {'title':'B','text':'second','chunk_id':'b'}]
        provider = Mock()
        provider.request.return_value = {'results':[{'index':1,'relevance_score':.8},{'index':0,'relevance_score':.1}]}
        self.assertEqual([r['chunk_id'] for r in rerank(provider,'question',items)],['b','a'])
        args = provider.request.call_args.args
        self.assertEqual(args[0],'rerank')
        self.assertEqual(args[1]['input']['documents'],['A\nfirst','B\nsecond'])

    def test_duplicate_or_missing_indices_fail(self):
        """重复索引和截断响应不能冒充完整候选排序。"""
        items = [{'title':'A','text':'first'}] * 2
        provider = Mock()
        row = {'index':0,'relevance_score':.9}
        for response in [[row,row],[row]]:
            provider.request.return_value = {'results':response}
            with self.assertRaises(ValueError):
                rerank(provider,'question',items)
