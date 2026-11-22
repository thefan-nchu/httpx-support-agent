"""对现有候选调用 DashScope 重排，按返回的位置映射回原片段。"""
import math

MODEL = 'qwen3.7-text-rerank'


def rerank(provider,query,candidates):
    """只调整同一批候选的顺序。返回完整排名与分数，拒绝缺失或重复索引。"""
    if not candidates:
        return []
    payload = {'model':MODEL, 'input':{'query':query,
        'documents':[c['title']+'\n'+c['text'] for c in candidates]},
        'parameters':{'top_n':len(candidates),'return_documents':False}}
    results = provider.request('rerank',payload)['results']
    indices = set()
    ranked = []
    for item in results:
        index, score = item['index'],item['relevance_score']
        if (type(index) is not int or not 0<=index<len(candidates) or index in indices
                or type(score) not in (int,float) or not math.isfinite(score)):
            raise ValueError('重排响应的索引或分数无效')
        indices.add(index)
        ranked.append((index,score))
    if len(indices)!=len(candidates):
        raise ValueError('重排响应缺少候选')
    # 同分时维持原有 RRF 顺序，避免任意打散已有候选。
    return [candidates[index] | {'rerank_score':score}
            for index,score in sorted(ranked,key=lambda pair:(-pair[1],pair[0]))]
