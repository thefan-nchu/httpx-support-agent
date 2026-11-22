"""离线工具边界测试：模拟模型响应，不把模拟输出作为真实模型质量。"""
import unittest
from model_agent import answer, HybridTool


class ModelTests(unittest.TestCase):
    def test_query_bounds(self):
        """非法参数在联网和索引构建之前被拒绝。"""
        tool=object.__new__(HybridTool)
        for query in ['',None,'x'*2001]:
            with self.assertRaises(ValueError): tool.search(query)

    def test_tool_roundtrip_and_citation(self):
        """两轮消息保留tool_call_id；不存在的引用不会作为答案展示。"""
        class Provider:
            def chat(self,messages,first=False):
                if first: return {'role':'assistant','content':[], 'tool_calls':[{'id':'test','function':{'name':'search_knowledge','arguments':'{"query":"timeout"}'}}]}
                assert messages[-1]['tool_call_id']=='test'
                return {'content':[{'text':'说明[E1]'}]}
        class Tool:
            def search(self,q): return [{'text':'test evidence','url':'https://example.org','version':'0.28.1'}]
        self.assertEqual(answer('test',Tool(),Provider())['model_calls'],2)

    def test_unknown_tool_rejected(self):
        """模型不能通过自造工具名执行其他操作。"""
        class Provider:
            def chat(self,*args,**kwargs): return {'tool_calls':[{'function':{'name':'execute_shell'}}]}
        with self.assertRaises(ValueError): answer('test',None,Provider())
