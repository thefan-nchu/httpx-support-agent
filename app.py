from pathlib import Path
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field
from workflow import Investigator, Conflict, report

ROOT = Path(__file__).resolve().parent

def create_app(investigator=None):
    @asynccontextmanager
    async def lifespan(app):
        # 显式开关才启用收费模型；原run.ps1和注入测试仍使用离线模式。
        if investigator is None and os.getenv('SUPPORT_MODEL_MODE') == '2':
            # 新版参考库和逐条结论检查；保留模式1便于旧方案对照。
            from evidence_workflow import EvidenceInvestigator
            app.state.agent = EvidenceInvestigator()
        elif investigator is None and os.getenv('SUPPORT_MODEL_MODE') == '1':
            from model_workflow import ModelInvestigator
            app.state.agent = ModelInvestigator()
        else:
            app.state.agent = investigator or Investigator()
        yield

    app = FastAPI(title='Support Agent Lab', version='0.1.0', lifespan=lifespan)

    @app.middleware('http')
    async def local_only(request: Request, call_next):
        host = request.headers.get('host', '').split(':')[0]
        if host not in ['127.0.0.1', 'localhost', 'testserver']:
            return JSONResponse({'detail': 'Local access only'}, status_code=403)
        origin = request.headers.get('origin')
        if origin and origin not in [f'http://{request.headers.get("host")}', f'https://{request.headers.get("host")}']:
            return JSONResponse({'detail': 'Cross-origin access denied'}, status_code=403)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        return response

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        return JSONResponse({'detail': str(exc)}, status_code=409)

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        return JSONResponse({'detail': '调查不存在'}, status_code=404)

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({'detail': str(exc)}, status_code=400)

    @app.get('/')
    def index():
        return FileResponse(ROOT / 'static' / 'index.html')

    @app.get('/static/{name}')
    def static(name: str):
        if name not in ['app.js', 'style.css']:
            raise HTTPException(404)
        return FileResponse(ROOT / 'static' / name, media_type='text/javascript' if name.endswith('.js') else 'text/css')

    @app.get('/api/health')
    def health():
        corpus = app.state.agent.corpus
        return {'status': 'ok', 'mode': 'dashscope-versioned-evidence' if getattr(app.state.agent,'reference_mode',False) else 'dashscope-hybrid' if hasattr(app.state.agent,'provider') else 'deterministic-no-model', 'version': '0.28.1',
            'max_input_characters': 20000 if getattr(app.state.agent,'reference_mode',False) else 6000,
            'reference_sources':sum(r['kind'] in ['release_note','code_reference'] for r in corpus.manifest['records']),
            'documents': len({r['id'] for r in corpus.chunks if r['kind'] == 'doc'}),
            'issues': sum(r['kind'] == 'issue' for r in corpus.manifest['records']),
            'chunks': len(corpus.chunks), 'model_calls': None if hasattr(app.state.agent,'provider') else 0}

    @app.get('/api/sources')
    def sources():
        return app.state.agent.corpus.manifest

    @app.get('/api/sessions')
    def sessions():
        return app.state.agent.store.list()

    @app.post('/api/sessions')
    def create():
        return app.state.agent.store.create()

    @app.get('/api/sessions/{sid}')
    def get(sid: str):
        return app.state.agent.store.get(sid)

    @app.post('/api/sessions/{sid}/messages')
    def turn(sid: str, body: Turn):
        return app.state.agent.turn(sid, body.message, body.revision)

    @app.post('/api/sessions/{sid}/resume')
    def resume(sid: str, body: Resume):
        return app.state.agent.resume(sid, body.revision)

    @app.get('/api/sessions/{sid}/report', response_class=PlainTextResponse)
    def export(sid: str):
        case = app.state.agent.store.get(sid)
        return PlainTextResponse(report(case), headers={'Content-Disposition': f'attachment; filename="investigation-{case["id"]}.md"'})

    return app

class Resume(BaseModel):
    revision: int = Field(ge=0)

class Turn(Resume):
    # API容纳长报告；各工作流仍按自己的额度校验，旧模式保持6000字符限制。
    message: str = Field(min_length=1, max_length=20000)

app = create_app()
