"""发布版端点校验测试。所有输入均为构造值，不连接外部服务。"""
import unittest

from check_model_connection import _approved_endpoint


class PublicEndpointTests(unittest.TestCase):
    """模型密钥仅用于受支持的官方地址。"""

    def test_official_endpoints(self):
        """接受共享域名和合法工作区域名并规范化末尾斜杠。"""
        for url in ('https://dashscope.aliyuncs.com/api/v1',
                    'https://llm-example.cn-beijing.maas.aliyuncs.com/api/v1'):
            with self.subTest(url=url):
                self.assertEqual(_approved_endpoint(url + '/', {'/api/v1'}), url)

    def test_distinct_host_or_unsafe_url(self):
        """拒绝伪装域名、用户信息、非 HTTPS 和额外查询部分。"""
        for url in ('https://dashscope.aliyuncs.com.example.org/api/v1',
                    'https://someone@dashscope.aliyuncs.com/api/v1',
                    'http://dashscope.aliyuncs.com/api/v1',
                    'https://dashscope.aliyuncs.com/api/v1?other=value'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                _approved_endpoint(url, {'/api/v1'})
