"""离线验证两种模型协议的路由、工具关联字段和返回形状，不发送真实请求。"""
import unittest
from unittest.mock import patch
from pathlib import Path
import uuid
import httpx
from model_agent import DashScope


class ProtocolTests(unittest.TestCase):
    def provider(self):
        """构造无真实凭据的测试客户端，日志写到独立产物文件。"""
        p=object.__new__(DashScope)
        p.config={'DASHSCOPE_BASE_URL':'https://example.org/api/v1','CHAT_BASE_URL':'https://example.org/compatible-mode/v1','DASHSCOPE_API_KEY':'test-fixture'}
        p.audit=Path(__file__).resolve().parents[1]/'artifacts'/('protocol-test-'+uuid.uuid4().hex+'.jsonl')
        return p

    def test_chat_compatible_tool_messages(self):
        """工具调用ID保持不变；原生消息文本数组转成兼容协议文本。"""
        with patch('model_agent.httpx.Client') as client:
            post=client.return_value.__enter__.return_value.post
            post.return_value=httpx.Response(200,json={'choices':[{'message':{'content':'ok'}}],'usage':{'total_tokens':1}})
            out=self.provider().request('chat',{'model':'fixture','input':{'messages':[{'role':'tool','tool_call_id':'call1','content':[{'text':'evidence'}]}]},'parameters':{'max_tokens':8,'response_format':{'type':'json_object'}}})
            self.assertEqual(post.call_args.args[0],'https://example.org/compatible-mode/v1/chat/completions')
            body=post.call_args.kwargs['json']
            self.assertEqual(body['messages'][0]['tool_call_id'],'call1')
            self.assertEqual(body['messages'][0]['content'],'evidence')
            self.assertEqual(body['max_tokens'],8)
            self.assertNotIn('input',body)
            self.assertEqual(out['choices'][0]['message']['content'],'ok')

    def test_embedding_stays_native(self):
        """回答协议变更不会改变向量API地址或原生请求结构。"""
        with patch('model_agent.httpx.Client') as client:
            post=client.return_value.__enter__.return_value.post
            post.return_value=httpx.Response(200,json={'output':{'embeddings':[]}})
            self.provider().request('embedding',{'model':'fixture','input':{'texts':['a']},'parameters':{'dimension':1024}})
            self.assertTrue(post.call_args.args[0].endswith('/api/v1/services/embeddings/text-embedding/text-embedding'))
            self.assertIn('input',post.call_args.kwargs['json'])
