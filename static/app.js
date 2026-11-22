let current = null;
let busy = false;
const $ = id => document.getElementById(id);
const statuses = {new:'尚未开始', running:'调查中', needs_info:'需要补充信息', version_mismatch:'版本不匹配', evidence_ready:'已找到候选证据', insufficient_evidence:'证据不足', tool_error:'工具失败'};
async function api(path, method='GET', body) {
  const response = await fetch(path, {method, headers:{'Content-Type':'application/json'}, body:body?JSON.stringify(body):undefined});
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail==='string'?data.detail:'请求未通过校验');
  return data;
}
function el(tag, text, cls) { const node=document.createElement(tag); if(text!==undefined) node.textContent=text; if(cls)node.className=cls; return node; }
// 用每轮自己的引用表解析 E1 等编号，恢复调查时也不会把旧引文指向新证据。
function renderEvidenceRounds(rounds) {
  if (!rounds.length) return;
  const history=el('details',undefined,'evidence');
  history.append(el('summary','各轮证据与版本复查'));
  for (const round of [...rounds].reverse()) {
    const card=el('section',undefined,'trace-item');
    card.append(el('b',`第 ${round.turn} 轮 · HTTPX ${round.reported_version || '未知'}`));
    const change=round.version_recheck;
    if (change) {
      const status=change.status==='completed'?'复查完成':'复查失败，尚无新结果';
      const previous=change.previous_turn!=null?` · 第 ${change.previous_turn} 轮结论需复查`:'';
      card.append(el('p',`${change.from || '未知'} → ${change.to} · ${status}${previous}`,'meta'));
    }
    if (!round.claims.length) card.append(el('p','本轮没有已审查的证据结论。','meta'));
    for (const claim of round.claims) {
      card.append(el('p',claim.text));
      for (const ref of claim.evidence) {
        const source=round.sources.find(source=>source.citation===ref.citation);
        if (!source) continue;
        const link=el('a',`[${ref.citation}] ${source.title || '来源'} · ${source.version || '版本未知'}`);
        if (source.url?.startsWith('https://github.com/encode/httpx/')) link.href=source.url;
        link.target='_blank'; link.rel='noopener noreferrer';
        card.append(link, el('div',ref.quote,'excerpt'));
      }
    }
    history.append(card);
  }
  $('evidence').append(history);
}
function setBusy(value) { busy=value; $('send').disabled=value; $('new').disabled=value; $('resume').disabled=value; $('send').textContent=value?'检索中…':'继续调查 →'; }
async function list() {
  const sessions = await api('/api/sessions'); $('sessions').replaceChildren();
  for (const session of sessions) { const b=el('button',session.summary||'新调查','session'+(current?.id===session.id?' selected':'')); b.title=session.summary; b.onclick=async()=>{if(busy)return;try{current=await api('/api/sessions/'+session.id);render();await list();}catch(e){$('error').textContent=e.message;}}; $('sessions').append(b); }
}
function render() {
  $('messages').replaceChildren();
  for (const message of current.messages) {const node=el('div',undefined,'message '+message.role);node.append(el('strong',message.role==='user'?'你':'SUPPORT LAB'),el('div',message.content));$('messages').append(node);}
  if(!current.messages.length){$('messages').append(el('p','请输入 HTTPX 版本、异常类名和触发条件。系统仅检索资料，不自动确认根因。','empty'));}
  $('messages').scrollTop=$('messages').scrollHeight;
  $('status').textContent=statuses[current.status]||current.status;
  $('evidence').replaceChildren();
  renderEvidenceRounds(current.evidence_rounds || []);
  if(!current.evidence.length)$('evidence').append(el('div','尚无可引用证据。','empty'));
  current.evidence.forEach((source,i)=>{const card=el('article',undefined,'evidence');const link=el('a',`${i+1}. ${source.title}`); if(source.url.startsWith('https://github.com/encode/httpx/'))link.href=source.url;link.target='_blank';link.rel='noopener noreferrer';card.append(link,el('div',`${source.kind==='doc'?'官方文档':'历史 Issue'} · 版本 ${source.version} · BM25 ${source.score}`,'meta'),el('div',source.text,'excerpt'));const details=el('details');details.append(el('summary','来源校验值'),el('div',source.sha256,'excerpt'));card.append(details);$('evidence').append(card);});
  $('trace').replaceChildren(); current.trace.forEach(step=>{const node=el('div',undefined,'trace-item');node.append(el('b',`${step.node} · ${step.elapsed_ms} ms`),el('pre',step.at+'\n'+JSON.stringify(step.detail,null,2)));$('trace').append(node);});
  $('attempts').replaceChildren(); if(!current.attempts.length)$('attempts').append(el('div','尚未记录已尝试步骤。反馈中说明“已试过”或“仍然失败”即可记录。','empty'));current.attempts.forEach(attempt=>{const node=el('div',undefined,'evidence');node.append(el('div',attempt.text),el('p','用户报告 · 尚未独立验证','meta'));$('attempts').append(node);});
  $('warnings').textContent=current.warnings.join('\n');$('export').disabled=false;$('resume').hidden=!(current.status==='running'||['retrieve','respond'].includes(current.next));
}
async function newCase(){current=await api('/api/sessions','POST');render();await list();$('message').focus();}
$('new').onclick=()=>newCase().catch(e=>$('error').textContent=e.message);
$('composer').onsubmit=async event=>{event.preventDefault();if(busy)return;const message=$('message').value.trim();if(!message)return;setBusy(true);$('error').textContent='';try{if(!current)current=await api('/api/sessions','POST');current=await api(`/api/sessions/${current.id}/messages`,'POST',{message,revision:current.revision});$('message').value='';render();await list();}catch(e){$('error').textContent=e.message;if(current){try{current=await api('/api/sessions/'+current.id);render();}catch{}}}finally{setBusy(false);}};
$('resume').onclick=async()=>{setBusy(true);try{current=await api(`/api/sessions/${current.id}/resume`,'POST',{revision:current.revision});render();}catch(e){$('error').textContent=e.message;}finally{setBusy(false);}};
$('export').onclick=()=>{if(current)window.location.href=`/api/sessions/${current.id}/report`;};
for(const name of ['evidence','trace','attempts'])$('tab-'+name).onclick=()=>{for(const other of ['evidence','trace','attempts']){const active=other===name;$(other).hidden=!active;$('tab-'+other).classList.toggle('active',active);$('tab-'+other).setAttribute('aria-selected',String(active));}};
document.querySelectorAll('.example').forEach(button=>button.onclick=()=>{$('message').value=button.dataset.query;$('message').focus();});
Promise.all([api('/api/health'),list()]).then(([health])=>{$('doc-count').textContent=health.documents;$('issue-count').textContent=health.issues;}).catch(e=>$('error').textContent='服务不可用：'+e.message);

// 根据服务状态显示模式，不把收费模型模式标为离线。
api('/api/health').then(h=>{$('mode-label').textContent=h.mode==='dashscope-versioned-evidence'?'DashScope · 版本化证据问答':h.mode==='dashscope-hybrid'?'DashScope · 混合检索问答':'无模型 · 确定性检索';$('message').maxLength=h.max_input_characters||6000;}).catch(()=>{});
