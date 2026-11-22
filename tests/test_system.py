import json
from pathlib import Path
import unittest
import uuid
from fastapi.testclient import TestClient
from app import create_app
from retrieval import Corpus
from workflow import Investigator, Store, Conflict, report

ROOT = Path(__file__).resolve().parents[1]

class SystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = Corpus()
        cls.output = ROOT / 'artifacts' / 'test-databases'
        cls.output.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.path = self.output / (str(uuid.uuid4()) + '.sqlite3')
        self.agent = Investigator(self.corpus, Store(self.path))
        self.case = self.agent.store.create()

    def turn(self, message):
        self.case = self.agent.turn(self.case['id'], message, self.case['revision'])
        return self.case

    def test_missing_version_then_resume_conversation(self):
        self.assertEqual(self.turn('连接池超时')['status'], 'needs_info')
        self.assertEqual(self.turn('HTTPX 0.28.1')['status'], 'evidence_ready')
        reopened = Store(self.path).get(self.case['id'])
        self.assertEqual(len(reopened['messages']), 4)
        self.assertIn('连接池', reopened['summary'])

    def test_version_mismatch_does_not_offer_other_docs(self):
        case = self.turn('HTTPX 0.27.0 PoolTimeout')
        self.assertEqual(case['status'], 'version_mismatch')
        self.assertEqual(case['evidence'], [])

    def test_python_version_does_not_replace_httpx(self):
        self.turn('HTTPX 0.28.1 超时')
        self.assertEqual(self.turn('Python 3.13.10 仍然失败')['version'], '0.28.1')

    def test_no_match_abstains(self):
        self.assertEqual(self.turn('HTTPX 0.28.1 zxqv999xyz')['status'], 'insufficient_evidence')

    def test_attempts_and_secret_redaction(self):
        case = self.turn('HTTPX 0.28.1 PoolTimeout 已试过增加连接数，仍然失败 token=FAKE_TEST_TOKEN')
        self.assertEqual(len(case['attempts']), 1)
        self.assertNotIn('FAKE_TEST_TOKEN', json.dumps(case))
        self.assertIn('尚未独立验证', report(case))

    def test_stale_write_conflict(self):
        old = self.agent.store.get(self.case['id'])
        self.turn('HTTPX 0.28.1 timeout')
        with self.assertRaises(Conflict):
            self.agent.store.save(old)

    def test_resume_after_inspection_checkpoint(self):
        case = self.case
        case.update(pending='HTTPX 0.28.1 PoolTimeout', status='running', turns=1)
        case['messages'].append({'role':'user','content':case['pending'],'at':case['created_at']})
        self.agent.store.save(case)
        checkpoint = self.agent.inspect({'case':case})['case']
        restarted = Investigator(self.corpus, Store(self.path))
        result = restarted.resume(case['id'], checkpoint['revision'])
        self.assertEqual(result['status'], 'evidence_ready')
        self.assertEqual(len(result['messages']), 2)
        self.assertEqual([t['node'] for t in result['trace']], ['inspect','retrieve','respond'])

    def test_cannot_submit_new_turn_during_checkpoint(self):
        self.case.update(pending='HTTPX 0.28.1 PoolTimeout', status='running')
        self.agent.store.save(self.case)
        self.case = self.agent.inspect({'case':self.case})['case']
        with self.assertRaises(Conflict):
            self.agent.turn(self.case['id'], 'new', self.case['revision'])

    def test_tool_failure_is_visible(self):
        class Broken:
            def search(self, *args, **kwargs):
                raise TimeoutError('test failure')
        self.agent.corpus = Broken()
        case = self.turn('HTTPX 0.28.1 timeout')
        self.assertEqual(case['status'], 'tool_error')
        self.assertEqual(case['evidence'], [])
        self.assertIn('TimeoutError', case['warnings'][0])

    def test_turn_budget(self):
        self.case['turns'] = 12
        self.agent.store.save(self.case)
        with self.assertRaises(ValueError):
            self.turn('HTTPX 0.28.1 timeout')

    def test_api_and_report(self):
        with TestClient(create_app(self.agent)) as client:
            self.assertEqual(client.get('/').status_code, 200)
            self.assertIn('text/javascript', client.get('/static/app.js').headers['content-type'])
            self.assertEqual(client.get('/api/health').json()['model_calls'], 0)
            case = client.post('/api/sessions').json()
            url = '/api/sessions/' + case['id']
            result = client.post(url+'/messages',json={'revision':0,'message':'HTTPX 0.28.1 SSL 证书错误'})
            self.assertEqual(result.status_code, 200, result.text)
            self.assertGreater(len(result.json()['evidence']), 0)
            self.assertEqual(client.post(url+'/messages',json={'revision':0,'message':'again'}).status_code, 409)
            self.assertEqual(client.get(url+'/report').status_code, 200)
            self.assertIn('调查报告', client.get(url+'/report').text)
            self.assertEqual(client.get('/api/sessions/not-found').status_code, 404)
            self.assertEqual(client.post('/api/sessions',headers={'Origin':'https://evil.example'}).status_code, 403)
            self.assertEqual(client.get('/',headers={'Host':'evil.example'}).status_code, 403)

    def test_real_issue_self_excluded_from_eval(self):
        self.assertFalse(any(c['id'] == 'CHANGELOG.md' for c in self.corpus.chunks))
        for source in self.corpus.manifest['records']:
            if source['kind'] == 'issue':
                results = self.corpus.search(source['title'],kind='doc')
                self.assertTrue(all(r['kind']=='doc' for r in results))

    def test_middle_turn_facts_survive_restart(self):
        self.turn('HTTPX 0.28.1 PoolTimeout')
        self.turn('使用 AsyncClient，经过代理，100 个并发')
        self.agent = Investigator(self.corpus, Store(self.path))
        result = self.turn('已试过增加连接数，仍然失败')
        for token in ['AsyncClient', 'proxy', '100', 'PoolTimeout']:
            self.assertIn(token, result['query'])
        self.assertEqual(result['facts']['concurrency']['turn'], 2)
        self.assertNotIn('请补充', result['answer'])

    def test_explicit_correction_replaces_search_terms(self):
        self.turn('HTTPX 0.28.1 PoolTimeout，经过代理，100 个并发')
        result = self.turn('刚才说错了，没有配置代理；并发数是10；ReadTimeout')
        self.assertFalse(result['facts']['proxy']['value'])
        self.assertEqual(result['facts']['concurrency']['value'], 10)
        self.assertNotIn('proxy', result['query'])
        self.assertNotIn('代理', result['query'])
        self.assertNotIn('100', result['query'])
        self.assertNotIn('PoolTimeout', result['query'])
        self.assertIn('ReadTimeout', result['query'])
        self.assertEqual(len(result['fact_history']), 3)
        self.assertIn('经过代理', result['messages'][0]['content'])

    def test_correction_of_httpx_keeps_python_separate(self):
        self.turn('HTTPX 0.27.0，Python 3.13.10 PoolTimeout')
        result = self.turn('更正 HTTPX 0.28.1')
        self.assertEqual(result['status'], 'evidence_ready')
        self.assertEqual(result['version'], '0.28.1')
        self.assertEqual(result['facts']['python_version']['value'], '3.13.10')

    def test_repeated_attempt_preserves_observations(self):
        self.turn('HTTPX 0.28.1 PoolTimeout，已试过增加 max_connections，仍然失败')
        result = self.turn('尝试过调大连接数，无效')
        self.assertEqual(len(result['attempts']), 1)
        self.assertEqual(len(result['attempts'][0]['observations']), 2)
        self.assertEqual(result['attempts'][0]['outcome'], 'reported_failed')

    def test_asked_fields_not_reasked_as_new_questions(self):
        first = self.turn('连接池超时')
        self.assertIn('请补充 HTTPX', first['answer'])
        result = self.turn('HTTPX 0.28.1 PoolTimeout')
        self.assertNotIn('请补充 HTTPX', result['answer'])
        self.assertNotIn('请补充准确的异常', result['answer'])
        self.assertIn('请补充客户端类型', result['answer'])
        result = self.turn('仍然报错')
        self.assertNotIn('请补充客户端类型', result['answer'])
        self.assertIn('待补充', result['answer'])

    def test_legacy_read_upgrade_does_not_write_database(self):
        legacy = dict(self.case)
        for key in ['schema_version','facts','fact_history','context_notes','asked_fields']:
            legacy.pop(key, None)
        legacy['messages'] = [{'role':'user','content':'HTTPX 0.28.1 PoolTimeout，经过代理', 'at':legacy['created_at']}]
        legacy['turns'] = 1
        legacy['status'] = 'evidence_ready'
        with self.agent.store.connect() as db:
            db.execute('UPDATE sessions SET body=? WHERE id=?',(json.dumps(legacy),legacy['id']))
        upgraded = self.agent.store.get(legacy['id'])
        self.assertEqual(upgraded['schema_version'], 2)
        self.assertTrue(upgraded['facts']['proxy']['value'])
        self.assertEqual(upgraded['revision'], legacy['revision'])
        with self.agent.store.connect() as db:
            body = json.loads(db.execute('SELECT body FROM sessions WHERE id=?',(legacy['id'],)).fetchone()[0])
        self.assertNotIn('schema_version', body)
        result = self.agent.turn(legacy['id'], '没有配置代理', upgraded['revision'])
        self.assertFalse(result['facts']['proxy']['value'])
        reopened = Store(self.path).get(legacy['id'])
        self.assertEqual(reopened['schema_version'], 2)
        self.assertEqual(reopened['messages'][0], legacy['messages'][0])

    def test_future_schema_is_rejected_without_write(self):
        self.case['schema_version'] = 99
        self.agent.store.save(self.case)
        with self.assertRaises(ValueError):
            self.agent.store.get(self.case['id'])

    def test_unrecognized_word_does_not_invent_fact(self):
        result = self.turn('HTTPX 0.28.1 代理可能有问题，但不确定')
        self.assertNotIn('proxy', result['facts'])

    def test_question_or_guess_does_not_replace_known_fact(self):
        self.turn('HTTPX 0.28.1 PoolTimeout，没有配置代理')
        result = self.turn('是不是使用代理会影响？可能是 ReadTimeout')
        self.assertFalse(result['facts']['proxy']['value'])
        self.assertEqual(result['facts']['exception_type']['value'],'PoolTimeout')

    def test_bounded_notes_keep_full_messages(self):
        self.turn('HTTPX 0.28.1 PoolTimeout')
        for i in range(8):
            self.turn(f'观察补充编号 {i}')
        self.assertLessEqual(len(self.case['context_notes']), 6)
        self.assertEqual(len(self.case['messages']),18)
        self.assertEqual(self.case['facts']['exception_type']['value'],'PoolTimeout')

if __name__ == '__main__':
    unittest.main(verbosity=2)
