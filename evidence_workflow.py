"""在原状态流上接入有范围说明的证据回答；未知版本不再一律挡在检索前。"""
import time
from copy import deepcopy
from workflow import Investigator, Store, ROOT, now, redact
from investigation_state import update_memory, fact_summary
from retrieval import Corpus
from model_agent import DashScope
from grounded_agent import EvidenceStageError, ReferenceTool, RerankedReferenceTool, answer_grounded


class EvidenceInvestigator(Investigator):
    """使用单独会话库；始终保留原文，有限支持历史资料而不假装全版本诊断。"""
    def __init__(self,provider=None,corpus=None,store=None,*,rerank_enabled=True):
        """正式工作流默认重排，旧实验可显式复用调整前的配置。"""
        self.reference_mode=True
        corpus=corpus or Corpus(ROOT/'data/corpus-v3')
        self.provider=provider or DashScope()
        tool_class = RerankedReferenceTool if rerank_enabled else ReferenceTool
        self.tool=tool_class(corpus,self.provider)
        super().__init__(corpus,store or Store(ROOT/'data/evidence-sessions.sqlite3'))

    def inspect(self,state):
        """提取已有会话事实，保留完整问题用于检索规划；缺版本作为限制而非阻断。"""
        started=time.perf_counter();case=state['case'];text=case['pending']
        if not case['summary']:case['summary']=text[:160]
        before=case['version']
        update_memory(case,text,case['turns'],now())
        history=case.get('evidence_rounds', [])
        prior=history[-1] if history else None
        # 只用已提交的上一轮建立关联。旧会话可以继续，不推断缺失的历史引文。
        case['version_recheck']=None
        if case['turns']>1 and before!=case['version'] and case['version']:
            case['version_recheck']={'from':before,'to':case['version'],
                'previous_turn':prior['turn'] if prior else None,'status':'pending'}
        background='\n'.join(n['text'] for n in case['context_notes'] if n['turn']!=case['turns'])
        prefix='用户报告的会话事实（未独立验证）：'+fact_summary(case)+'\n先前问题背景：'+background
        if case['version_recheck']:
            prefix+='\n以当前报告版本重新检索和判断适用范围；上轮判断不能沿用为本轮依据。'
        if case['turns']>1:
            prefix+='\n结合先前问题理解本轮反馈，补问只索取尚缺的信息。'
        case['query']=prefix+'\n本轮原文：'+text
        case['warnings']=[]
        case['next']='retrieve';case['mode']='dashscope-versioned-evidence'
        detail={'reported_version':case['version'],'scope':'限定资料范围，不保证历史故障可诊断'}
        if case['version_recheck']:
            detail['version_change']={k:v for k,v in case['version_recheck'].items() if k!='status'}
        return self.checkpoint(case,'inspect',detail,started)

    def retrieve(self,state):
        """保存逐条引文检查和审查轨迹；失败时不保留旧轮证据或未经审查的草稿。"""
        started=time.perf_counter();case=state['case']
        try:
            if case['turns']>1:
                # 只在工具规划回退时用有界的会话上下文，避免“版本更正”成为唯一检索词。
                fallback='\n'.join([case['pending'][:900],fact_summary(case),
                    *(n['text'] for n in case['context_notes'] if n['turn']!=case['turns'])])[:1800]
                result=answer_grounded(case['query'],self.tool,self.provider,fallback_query=fallback)
            else:
                result=answer_grounded(case['query'],self.tool,self.provider)
            case.update(answer=result['answer'],evidence=result['evidence'],answer_audit=result['audit'],
                answer_disposition=result['disposition'],status='evidence_ready' if result['audit']['final']['claims'] else 'insufficient_evidence')
            detail={'tool':'search_knowledge','query':result['tool_query'],'model_calls':3,'disposition':result['disposition']}
            detail['ranking_method']=next((e.get('ranking_method') for e in result['evidence']),None)
            if detail['ranking_method']=='rrf_fallback':
                case['warnings'].append('重排服务本轮不可用，已按基础检索排序提供证据。')
        except Exception as exc:
            case.update(answer='证据处理未完成，本轮没有可支持的诊断。请稍后重试。',
                evidence=[],answer_audit={},answer_disposition=None,status='tool_error')
            # 历史会话没有新字段也能读；这里只落盘分类，不持久化出错的模型正文。
            detail={'error_type':type(exc).__name__,'failure_stage':'unknown',
                    'failure_kind':'unexpected_error','billing':'失败前可能已计费，参见调用日志'}
            if isinstance(exc,EvidenceStageError):
                detail.update(error_type=exc.cause_type,failure_stage=exc.stage,failure_kind=exc.kind)
        case['next']='respond'
        return self.checkpoint(case,'retrieve',detail,started)

    def respond(self,state):
        """提交本轮结论快照和版本复查状态，供页面和导出恢复各轮引用。"""
        started=time.perf_counter();case=state['case']
        recheck=case.get('version_recheck')
        if recheck:
            failed=case['status']=='tool_error'
            recheck['status']='failed' if failed else 'completed'
            previous=f"第 {recheck['previous_turn']} 轮结论需按新版本复查。" if recheck['previous_turn'] is not None else ''
            outcome='本轮复查失败，尚无新的审查结果。' if failed else '下方是按新信息重新检索并审查后的本轮结果。'
            case['answer']=f"你报告的 HTTPX 版本由 {recheck['from'] or '未知'} 更新为 {recheck['to']}。{previous}{outcome}\n\n"+case['answer']
        # E1 等编号每轮重用。把对应来源和已通过审查的原句一起保存，旧轮不被覆盖。
        sources=[{'citation':f'E{i}',**{k:e[k] for k in ('title','url','version','chunk_id') if k in e}}
                 for i,e in enumerate(case['evidence'],1)]
        final=case.get('answer_audit',{}).get('final',{})
        case.setdefault('evidence_rounds',[]).append({
            'turn':case['turns'],'reported_version':case['version'],'status':case['status'],
            'version_recheck':deepcopy(recheck),'sources':sources,
            'claims':deepcopy(final.get('claims',[])),'follow_up':list(final.get('follow_up',[])),
        })
        case['messages'].append({'role':'assistant','content':case['answer'],'at':now()});case['next']='inspect'
        return self.checkpoint(case,'respond',{'status':case['status']},started)

    def turn(self,sid,message,revision):
        """扩展模型模式输入至20000字符，保留原文，不截掉历史Issue末尾版本信息。"""
        from workflow import Conflict
        case=self.store.get(sid)
        if revision!=case['revision'] or case['status']=='running' or case['next']!='inspect':raise Conflict('会话版本过期或正在处理')
        if case['turns']>=12:raise ValueError('每次调查最多12轮')
        text=redact(message.strip())
        if not text or len(text)>20000:raise ValueError('请输入1至20000字符')
        case['messages'].append({'role':'user','content':text,'at':now()})
        case.update(pending=text,status='running',next='inspect',turns=case['turns']+1)
        self.store.save(case)
        return self.graph.invoke({'case':case})['case']
