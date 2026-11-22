"""证据回答边界测试；测试文本为人工夹具，不计入真实验证集。"""
import unittest
import uuid
from unittest.mock import patch
from pathlib import Path
from grounded_agent import validate_draft,apply_review,ReferenceTool,answer_grounded
from evidence_workflow import EvidenceInvestigator
from retrieval import Corpus
from workflow import Store
from app import create_app
from fastapi.testclient import TestClient
import json


class GroundedTests(unittest.TestCase):
    def test_missing_tool_call_falls_back_without_fabricating_id(self):
        """工具调用缺失时仍执行同一个只读检索，模型草稿消息没有虚构的调用ID。"""
        class Provider:
            def chat(self, messages, first=False):
                return {'role':'assistant','tool_calls':None}

        class Tool:
            def search(self, query):
                self.query=query
                return []

        tool=Tool()
        draft={'disposition':'insufficient_evidence','claims':[],'limitations':[],'follow_up':[]}
        review={'keep_claims':[],'keep_limitations':[],'keep_follow_up':[]}
        with patch('grounded_agent.json_call',side_effect=[draft,review]) as call:
            result=answer_grounded('本轮原文：示例问题',tool,Provider())
        self.assertEqual(tool.query,'示例问题')
        self.assertEqual(result['audit']['query_origin'],'fallback_original_question')
        self.assertFalse(any(m['role']=='tool' for m in call.call_args_list[0].args[1]))

    def test_grounded_roundtrip_filters_unsupported_claim(self):
        """三轮协议模拟：草稿结论被审查否决时，不应残留在最终用户回答里。"""
        class Provider:
            config={'CHAT_MODEL':'fixture'}
            def __init__(self):self.calls=0
            def chat(self,messages,first=False):return {'role':'assistant','content':[], 'tool_calls':[{'id':'test','function':{'name':'search_knowledge','arguments':'{"query":"q"}'}}]}
            def request(self,*args,**kwargs):
                self.calls+=1
                value={'disposition':'supported','claims':[{'text':'没有证据的根因断言','evidence':[{'citation':'E1','quote':'actual words'}]}],'limitations':[],'follow_up':['请提供最小复现。']} if self.calls==1 else {'keep_claims':[],'keep_limitations':[],'keep_follow_up':[0]}
                return {'choices':[{'message':{'content':[{'text':json.dumps(value,ensure_ascii=False)}]}}]}
        class Tool:
            def search(self,q):return [{'text':'actual words in fixture','url':'https://example.org','kind':'doc','version':'0.28.1'}]
        result=answer_grounded('fixture',Tool(),Provider())
        self.assertNotIn('没有证据的根因断言',result['answer'])
        self.assertIn('请提供最小复现',result['answer'])
        self.assertEqual(result['model_calls'],3)

    def test_fabricated_quote_removed(self):
        """引用编号存在但引文不存在时不能保留技术结论。"""
        draft={'disposition':'partial','claims':[{'text':'bad','evidence':[{'citation':'E1','quote':'invented'}]}],'limitations':[],'follow_up':[]}
        clean,rejected=validate_draft(draft,[{'citation':'E1','text':'real source'}])
        self.assertEqual(clean['claims'],[]);self.assertEqual(len(rejected),1)

    def test_review_cannot_inject_claim(self):
        """审查只能按下标保留已有文本，越界或布尔下标不接受。"""
        draft={'claims':[],'limitations':[],'follow_up':['version?']}
        for index in [1,True,-1]:
            with self.assertRaises(ValueError):apply_review(draft,{'keep_claims':[],'keep_limitations':[],'keep_follow_up':[index]})

    def test_no_claims_means_not_supported(self):
        """模型自报supported不能覆盖程序的证据不足判断。"""
        result=apply_review({'disposition':'supported','claims':[],'limitations':[],'follow_up':[]},
                            {'keep_claims':[],'keep_limitations':[],'keep_follow_up':[]})
        self.assertEqual(result['disposition'],'insufficient_evidence')

    def test_failure_stages_are_saved_without_raw_model_text(self):
        """真实会话图注入四种故障，确认阶段、清理和对外提示一致。"""
        class Provider:
            config = {'CHAT_MODEL':'fixture'}

            def __init__(self, replies):
                self.replies = iter(replies)

            def chat(self, messages, first=False):
                return {'role':'assistant','tool_calls':None}

            def request(self, *args, **kwargs):
                item = next(self.replies)
                if isinstance(item,Exception):
                    raise item
                return item

        def wrap(text):
            """构造与兼容接口相同的消息封装。"""
            return {'choices':[{'message':{'content':text}}]}

        draft = wrap(json.dumps({'disposition':'partial','claims':[{'text':'fixture private draft',
            'evidence':[{'citation':'E1','quote':'supporting phrase'}]}],
            'limitations':[],'follow_up':[]}))
        failures = [
            ('model_request_error',RuntimeError('fixture private failure'),RuntimeError),
            ('response_envelope_error',{'private':'fixture private response'},None),
            ('json_parse_error',wrap('fixture private response is not JSON'),json.JSONDecodeError),
            ('schema_error',wrap('[]'),None),
            ('schema_error',wrap('{"private":"fixture private invalid fields"}'),ValueError),
        ]
        root=Path(__file__).resolve().parents[1]
        store=Store(root/'artifacts/test-databases'/f'{uuid.uuid4()}.sqlite3')
        for stage in ('draft','review'):
            for kind,response,cause in failures:
                with self.subTest(stage=stage,kind=kind,cause=cause):
                    replies=[response] if stage=='draft' else [draft,response]
                    agent=EvidenceInvestigator(provider=Provider(replies),store=store)
                    state=agent.store.create()
                    state.update(answer_disposition='partial',evidence=[{'text':'old evidence'}],
                                 answer_audit={'old':'old audit'})
                    agent.store.save(state)
                    docs=[{'text':'supporting phrase in official fixture','url':'https://example.org',
                           'kind':'doc','version':'0.28.1','ranking_method':'rerank'}]
                    with patch.object(agent.tool,'search',return_value=docs):
                        result=agent.turn(state['id'],'fixture question',state['revision'])
                    saved=agent.store.get(state['id'])
                    detail=next(x['detail'] for x in saved['trace'] if x['node']=='retrieve')
                    self.assertEqual((detail['failure_stage'],detail['failure_kind']),(stage,kind))
                    if cause:
                        self.assertEqual(detail['error_type'],cause.__name__)
                    self.assertNotIn('fixture private',json.dumps(saved,ensure_ascii=False))
                    self.assertEqual(result['status'],'tool_error')
                    self.assertIn('请稍后重试',result['messages'][-1]['content'])
                    self.assertEqual(saved['evidence'],[])
                    self.assertEqual(saved['answer_audit'],{})
                    self.assertIsNone(saved['answer_disposition'])
                    self.assertEqual(saved['next'],'inspect')


    def test_reference_versions_preserved(self):
        """历史版本与开发版本标记保留，不伪装成当前版本说明。"""
        corpus=Corpus(Path(__file__).resolve().parents[1]/'data/corpus-v3')
        tool=ReferenceTool(corpus,object())
        self.assertTrue(any(c['kind']=='release_note' and c['version']=='0.24.1' for c in tool.docs))
        self.assertTrue(any('.dev' in c['version'] for c in tool.docs))
        self.assertFalse(any(c['kind']=='issue' for c in tool.docs))

    def test_long_issue_and_unknown_version_can_retrieve(self):
        """原文超过旧6000限制仍保存，未知版本进入受限参考检索而非被直接拒绝。"""
        root=Path(__file__).resolve().parents[1];path=root/'artifacts/test-databases'/f'{uuid.uuid4()}.sqlite3'
        agent=EvidenceInvestigator(provider=object(),store=Store(path));case=agent.store.create()
        fake={'answer':'资料不足，请补版本。','evidence':[],'audit':{'final':{'claims':[]}},'disposition':'needs_info','tool_query':'q'}
        with patch('evidence_workflow.answer_grounded',return_value=fake) as fn:
            text='actual user report '+('x'*7000)
            result=agent.turn(case['id'],text,case['revision'])
            self.assertEqual(result['messages'][0]['content'],text)
            self.assertEqual(result['status'],'insufficient_evidence');self.assertTrue(fn.called)
            self.assertEqual(agent.store.get(case['id'])['answer'],fake['answer'])

    def test_api_accepts_long_report_in_new_mode(self):
        """不仅Python方法，HTTP入口也接受长报告，并明确返回新版模式。"""
        root=Path(__file__).resolve().parents[1];path=root/'artifacts/test-databases'/f'{uuid.uuid4()}.sqlite3'
        agent=EvidenceInvestigator(provider=object(),store=Store(path))
        fake={'answer':'待补信息','evidence':[],'audit':{'final':{'claims':[]}},'disposition':'needs_info','tool_query':'q'}
        with TestClient(create_app(agent)) as client,patch('evidence_workflow.answer_grounded',return_value=fake):
            health=client.get('/api/health').json()
            self.assertEqual(health['mode'],'dashscope-versioned-evidence')
            self.assertEqual(health['max_input_characters'],20000)
            case=client.post('/api/sessions').json()
            response=client.post('/api/sessions/'+case['id']+'/messages',json={'revision':case['revision'],'message':'x'*7000})
            self.assertEqual(response.status_code,200)
