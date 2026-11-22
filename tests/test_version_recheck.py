"""通过会话 API 检查多轮版本复查，模型和候选使用离线夹具。"""
import uuid
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import create_app
from evidence_workflow import EvidenceInvestigator
from grounded_agent import EvidenceStageError
from workflow import Store


def reply(version):
    """返回一轮已审查的答案和有独立来源的 E1。"""
    citation = {'citation': 'E1', 'quote': f'quoted words for {version}'}
    source = {'chunk_id': version, 'title': f'Document {version}',
              'url': f'https://github.com/encode/httpx/{version}', 'version': version,
              'kind': 'doc', 'sha256': 'fixture', 'text': citation['quote']}
    return {'answer': f'范围为 {version}。', 'evidence': [source],
            'audit': {'final': {'claims': [{'text': f'范围为 {version}。', 'evidence': [citation]}],
                                'follow_up': []}},
            'disposition': 'partial', 'tool_query': 'fixture'}


class VersionRecheckTests(unittest.TestCase):
    """同时验收发布结果、历史引用和故障路径。"""

    def setUp(self):
        """每项测试使用项目产物目录的独立会话库。"""
        root = Path(__file__).resolve().parents[1]
        self.store = Store(root / 'artifacts/test-databases' / f'{uuid.uuid4()}.sqlite3')
        self.agent = EvidenceInvestigator(provider=object(), store=self.store)

    def test_correction_rechecks_without_overwriting_prior_citation(self):
        """新旧 E1 分别可追溯；第二轮使用原故障背景和更正后的版本。"""
        with TestClient(create_app(self.agent)) as client, patch(
            'evidence_workflow.answer_grounded', side_effect=[reply('0.28.1'), reply('0.22.0')]
        ) as model:
            state = client.post('/api/sessions').json()
            url = f"/api/sessions/{state['id']}"
            first = client.post(url+'/messages', json={'message':'HTTPX 0.28.1 的 ASGI SSE 挂起',
                                                       'revision':state['revision']}).json()
            second = client.post(url+'/messages', json={'message':'更正，HTTPX 0.22.0',
                                                        'revision':first['revision']}).json()
            saved = client.get(url).json()
            exported = client.get(url+'/report').text

        recheck = second['evidence_rounds'][1]['version_recheck']
        self.assertEqual(recheck, {'from':'0.28.1', 'to':'0.22.0', 'previous_turn':1, 'status':'completed'})
        self.assertEqual(first['evidence_rounds'][0], saved['evidence_rounds'][0])
        self.assertEqual([r['sources'][0]['chunk_id'] for r in saved['evidence_rounds']], ['0.28.1','0.22.0'])
        self.assertIn('quoted words for 0.28.1', exported)
        self.assertIn('quoted words for 0.22.0', exported)
        self.assertIn('第 1 轮结论需按新版本复查', exported)
        self.assertIn('ASGI SSE', model.call_args.kwargs['fallback_query'])
        self.assertIn('0.22.0', model.call_args.args[0])
        self.assertNotIn('0.28.1', model.call_args.args[0])

    def test_failed_recheck_does_not_republish_old_claims(self):
        """复查失败只展示失败状态，旧引文仍有历史可查。"""
        failure = EvidenceStageError('review', 'model_request_error', 'RuntimeError')
        with patch('evidence_workflow.answer_grounded', side_effect=[reply('0.22.0'), failure]):
            seed = self.store.create()
            first = self.agent.turn(seed['id'], 'ASGI SSE 挂起', seed['revision'])
            second = self.agent.turn(seed['id'], 'HTTPX 0.22.0', first['revision'])
        self.assertEqual(second['evidence'], [])
        self.assertEqual(second['evidence_rounds'][1]['claims'], [])
        self.assertEqual(second['version_recheck']['status'], 'failed')
        self.assertEqual(second['evidence_rounds'][0], first['evidence_rounds'][0])
        self.assertIn('尚无新的审查结果', second['answer'])

    def test_old_session_without_snapshots_can_continue(self):
        """数据库尚无历史快照时仍可更正版本，界面不宣称拥有旧轮证据。"""
        seed = self.store.create()
        seed.update(turns=1, version='0.28.1')
        self.store.save(seed)
        with patch('evidence_workflow.answer_grounded', return_value=reply('0.22.0')):
            second = self.agent.turn(seed['id'], '更正 HTTPX 0.22.0', seed['revision'])
        self.assertEqual(len(second['evidence_rounds']), 1)
        self.assertIsNone(second['version_recheck']['previous_turn'])
