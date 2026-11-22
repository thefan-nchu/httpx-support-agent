"""在现有状态图中注入模型检索节点，保留版本门控、SQLite与恢复机制。"""
import time
from workflow import Investigator, Store, ROOT, now, fact_summary
from retrieval import Corpus
from model_agent import DashScope, HybridTool, answer


class ModelInvestigator(Investigator):
    """模型模式使用独立会话库，避免把旧离线会话误标为模型生成。"""
    def __init__(self, provider=None, corpus=None, store=None):
        corpus = corpus or Corpus(ROOT/'data/corpus-v2')
        self.provider = provider or DashScope()
        self.tool = HybridTool(corpus,self.provider)
        super().__init__(corpus,store or Store(ROOT/'data/model-sessions.sqlite3'))

    def retrieve(self,state):
        """模型生成检索参数并根据证据回答；失败保存状态，不返回无证据诊断。"""
        started=time.perf_counter(); case=state['case']
        case['mode']='dashscope-hybrid'; case['model_calls']=0
        try:
            result=answer(case['query']+'\n用户报告：'+fact_summary(case),self.tool,self.provider)
            case.update(answer=result['answer'],evidence=result['evidence'],status='evidence_ready',model_calls=2)
            detail={'tool':'search_knowledge','query':result['tool_query'],'model_calls':2}
        except Exception as exc:
            case.update(answer='模型或检索调用失败，未生成诊断。请查看本地调用日志后重试。',evidence=[],status='tool_error')
            case['warnings'].append('调用未完成：'+type(exc).__name__)
            detail={'error_type':type(exc).__name__,'model_calls':'见model-usage.jsonl；失败前可能已计费'}
        case['next']='respond'
        return self.checkpoint(case,'retrieve',detail,started)

    def respond(self,state):
        """保存模型回答或版本补问，不覆盖检索节点的模型生成内容。"""
        started=time.perf_counter(); case=state['case']
        case['messages'].append({'role':'assistant','content':case['answer'],'at':now()})
        case['next']='inspect'
        return self.checkpoint(case,'respond',{'status':case['status'],'mode':'dashscope-hybrid'},started)
