from dash import Output, Input, State, callback_context, no_update, dcc, html
import requests
import json

def register_callbacks(app, host, port):
    # Central tab switcher
    @app.callback(
        Output('tab-content', 'children'),
        Input('nav-tabs', 'value')
    )
    def render_tab(tab):
        if tab == 'metrics':
            return html.Div([
                html.H3('Metrics Evaluation'),
                dcc.Markdown("""Upload or paste candidate and reference texts and compute BLEU/ROUGE/CHRF and more."""),
                dcc.Textarea(id='metrics-candidates', placeholder='Candidate predictions, one per line', style={'width': '100%', 'minHeight': '60px'}),
                dcc.Textarea(id='metrics-references', placeholder='References (use | to separate multiple per line)', style={'width': '100%', 'minHeight': '60px'}),
                html.Button('Compute Metrics', id='metrics-btn'),
                html.Pre(id='metrics-result', style={'marginTop': '12px', 'whiteSpace': 'pre-wrap'})
            ], style={'maxWidth': 720, 'margin': 'auto'})
        elif tab == 'analytics':
            return html.Div([
                html.H3('Analytics & Trends'),
                dcc.Markdown("View real-time trends, performance, alert history, and sliding-window stats."),
                html.Button('Refresh', id='analytics-refresh-btn'),
                html.Pre(id='analytics-summary', style={'marginTop': '12px', 'whiteSpace': 'pre-wrap'})
            ], style={'maxWidth': 720, 'margin': 'auto'})
        elif tab == 'guardrails':
            return html.Div([
                html.H3('Guardrails / Moderation'),
                dcc.Markdown("Check text(s) for policy/blocklist, PII, abuse, and more."),
                dcc.Textarea(id='guardrails-input', placeholder='Text(s), one per line', style={'width': '100%', 'minHeight': '60px'}),
                html.Button('Check Guardrails', id='guardrails-btn'),
                html.Pre(id='guardrails-result', style={'marginTop': '12px', 'whiteSpace': 'pre-wrap'})
            ], style={'maxWidth': 720, 'margin': 'auto'})
        elif tab == 'agent_eval':
            return html.Div([
                html.H3('Agent Evaluation'),
                dcc.Markdown("""Evaluate LLM agentic workflows: tool use, reasoning, safety, and goal completion."""),
                dcc.Textarea(id='agent-tasks', placeholder='Tasks (JSON list)', style={'width': '100%', 'minHeight': '50px'}),
                dcc.Textarea(id='agent-traces', placeholder='Agent traces (JSON list/dict)', style={'width': '100%', 'minHeight': '50px'}),
                html.Button('Evaluate Agent', id='agent-btn'),
                html.Pre(id='agent-result', style={'marginTop': '12px', 'whiteSpace': 'pre-wrap'})
            ], style={'maxWidth': 720, 'margin': 'auto'})
        elif tab == 'code_eval':
            return html.Div([
                html.H3('Code Evaluation'),
                dcc.Markdown("Rate code generation accuracy, style, security, and performance."),
                dcc.Textarea(id='code-prompts', placeholder='Prompts (JSON list)', style={'width': '100%', 'minHeight': '40px'}),
                dcc.Textarea(id='code-gen', placeholder='Generated code (JSON list)', style={'width': '100%', 'minHeight': '40px'}),
                dcc.Textarea(id='code-refs', placeholder='Reference solutions (JSON list)', style={'width': '100%', 'minHeight': '40px'}),
                html.Button('Evaluate Code', id='code-btn'),
                html.Pre(id='code-result', style={'marginTop': '12px', 'whiteSpace': 'pre-wrap'})
            ], style={'maxWidth': 720, 'margin': 'auto'})
        elif tab == 'factuality':
            return html.Div([
                html.H3('Factuality / Hallucination'),
                dcc.Markdown("Rate output factuality given user-provided scoring logic."),
                dcc.Textarea(id='factual-outputs', placeholder='Outputs (JSON list)', style={'width': '100%', 'minHeight': '40px'}),
                dcc.Textarea(id='factual-refs', placeholder='References (JSON list)', style={'width': '100%', 'minHeight': '40px'}),
                html.Button('Evaluate Factuality', id='factual-btn'),
                html.Pre(id='factual-result', style={'marginTop': '12px', 'whiteSpace': 'pre-wrap'})
            ], style={'maxWidth': 720, 'margin': 'auto'})
        elif tab == 'rag':
            return html.Div([
                html.H3('RAG Provenance / Citation Trace'),
                dcc.Markdown("Show document chunks cited in model outputs for audit."),
                dcc.Textarea(id='rag-outputs', placeholder='Outputs (JSON list)', style={'width': '100%', 'minHeight': '40px'}),
                dcc.Textarea(id='rag-chunks', placeholder='RAG Chunks (JSON list[list])', style={'width': '100%', 'minHeight': '40px'}),
                dcc.Textarea(id='rag-cites', placeholder='Citation indices (JSON list[list[int]])', style={'width': '100%', 'minHeight': '40px'}),
                html.Button('Trace Provenance', id='rag-btn'),
                html.Pre(id='rag-result', style={'marginTop': '12px', 'whiteSpace': 'pre-wrap'})
            ], style={'maxWidth': 720, 'margin': 'auto'})
        elif tab == 'reporting':
            return html.Div([
                html.H3('Model/Data Card Reporting'),
                dcc.Markdown("Export a full evaluation card (Markdown, HTML, or JSON)."),
                dcc.Input(id='report-model', placeholder='Model/Dataset name', type='text', style={'width': '80%'}),
                dcc.Textarea(id='report-metrics', placeholder='Metrics JSON', style={'width': '100%', 'minHeight': '40px'}),
                dcc.Textarea(id='report-analytics', placeholder='Analytics JSON', style={'width': '100%', 'minHeight': '40px'}),
                dcc.Textarea(id='report-config', placeholder='Config JSON', style={'width': '100%', 'minHeight': '40px'}),
                dcc.Dropdown(options=[{'label': f, 'value': f} for f in ['markdown', 'json', 'html']], value='markdown', id='report-format', style={'width': '40%'}),
                html.Button('Generate Card', id='report-btn'),
                html.Pre(id='report-result', style={'marginTop': '12px', 'whiteSpace': 'pre-wrap'})
            ], style={'maxWidth': 720, 'margin': 'auto'})
        return html.Div([
            html.P('Select a workflow tab above.'),
        ])

    # API callback for Metrics Evaluation
    @app.callback(
        Output('metrics-result', 'children'),
        Input('metrics-btn', 'n_clicks'),
        State('metrics-candidates', 'value'),
        State('metrics-references', 'value'),
        prevent_initial_call=True
    )
    def compute_metrics(n, candidates, references):
        import json as _json
        if not candidates or not references:
            return "Enter candidates and reference texts to evaluate."
        try:
            cands = [l.strip() for l in candidates.strip().splitlines() if l.strip()]
            refs = [[s.strip() for s in l.split('|')] for l in references.strip().splitlines() if l.strip()]
            r = requests.post(f"http://{host}:{port}/api/metrics", json={"candidates": cands, "references": refs}, timeout=12)
            return _json.dumps(r.json(), indent=2)
        except Exception as ex:
            return f"Error: {type(ex).__name__}: {ex}"

    # API callback for Analytics Summary
    @app.callback(
        Output('analytics-summary', 'children'),
        Input('analytics-refresh-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def get_analytics(n):
        import json as _json
        try:
            r = requests.get(f"http://{host}:{port}/api/analytics", timeout=7)
            return _json.dumps(r.json(), indent=2)
        except Exception as ex:
            return f"Error: {type(ex).__name__}: {ex}"

    # API callback for Guardrails Check
    @app.callback(
        Output('guardrails-result', 'children'),
        Input('guardrails-btn', 'n_clicks'),
        State('guardrails-input', 'value'),
        prevent_initial_call=True
    )
    def guardrails_check(n, texts):
        import json as _json
        if not texts:
            return "Enter text(s) to moderate."
        lines = [l.strip() for l in texts.strip().splitlines() if l.strip()]
        try:
            r = requests.post(f"http://{host}:{port}/api/guardrails", json={"texts": lines}, timeout=12)
            return _json.dumps(r.json(), indent=2)
        except Exception as ex:
            return f"Error: {type(ex).__name__}: {ex}"

    # API callback for Agent Eval
    @app.callback(
        Output('agent-result', 'children'),
        Input('agent-btn', 'n_clicks'),
        State('agent-tasks', 'value'),
        State('agent-traces', 'value'),
        prevent_initial_call=True
    )
    def agent_eval_cb(n, tasks, traces):
        import json as _json
        try:
            data = {
                "tasks": json.loads(tasks or "[]"),
                "agent_traces": json.loads(traces or "[]"),
            }
            r = requests.post(f"http://{host}:{port}/api/agent_eval", json=data, timeout=20)
            return _json.dumps(r.json(), indent=2)
        except Exception as ex:
            return f"Error: {type(ex).__name__}: {ex}"

    # API callback for Code Eval
    @app.callback(
        Output('code-result', 'children'),
        Input('code-btn', 'n_clicks'),
        State('code-prompts', 'value'),
        State('code-gen', 'value'),
        State('code-refs', 'value'),
        prevent_initial_call=True
    )
    def code_eval_cb(n, prompts, gen, refs):
        import json as _json
        try:
            data = {
                "prompts": json.loads(prompts or "[]"),
                "generated_code": json.loads(gen or "[]"),
                "reference_solutions": json.loads(refs or "[]"),
            }
            r = requests.post(f"http://{host}:{port}/api/code_eval", json=data, timeout=20)
            return _json.dumps(r.json(), indent=2)
        except Exception as ex:
            return f"Error: {type(ex).__name__}: {ex}"

    # API callback for Factuality
    @app.callback(
        Output('factual-result', 'children'),
        Input('factual-btn', 'n_clicks'),
        State('factual-outputs', 'value'),
        State('factual-refs', 'value'),
        prevent_initial_call=True
    )
    def factuality_cb(n, outs, refs):
        import json as _json
        try:
            data = {
                "outputs": json.loads(outs or "[]"),
                "references": json.loads(refs or "[]"),
            }
            r = requests.post(f"http://{host}:{port}/api/factuality", json=data, timeout=20)
            return _json.dumps(r.json(), indent=2)
        except Exception as ex:
            return f"Error: {type(ex).__name__}: {ex}"

    # API callback for RAG Provenance
    @app.callback(
        Output('rag-result', 'children'),
        Input('rag-btn', 'n_clicks'),
        State('rag-outputs', 'value'),
        State('rag-chunks', 'value'),
        State('rag-cites', 'value'),
        prevent_initial_call=True
    )
    def rag_cb(n, outs, chunks, cites):
        import json as _json
        try:
            data = {
                "outputs": json.loads(outs or "[]"),
                "rag_chunks": json.loads(chunks or "[]"),
                "output_citations": json.loads(cites or "[]"),
            }
            r = requests.post(f"http://{host}:{port}/api/rag_provenance", json=data, timeout=20)
            return _json.dumps(r.json(), indent=2)
        except Exception as ex:
            return f"Error: {type(ex).__name__}: {ex}"

    # API callback for Model/Data Card Reporting
    @app.callback(
        Output('report-result', 'children'),
        Input('report-btn', 'n_clicks'),
        State('report-model', 'value'),
        State('report-metrics', 'value'),
        State('report-analytics', 'value'),
        State('report-config', 'value'),
        State('report-format', 'value'),
        prevent_initial_call=True
    )
    def report_cb(n, name, metrics, analytics, config, fmt):
        import json as _json
        try:
            data = {
                "model_name": name or "Model",
                "metrics": json.loads(metrics or "{}"),
                "analytics": json.loads(analytics or "{}"),
                "config": json.loads(config or "{}"),
                "format": fmt or "markdown"
            }
            r = requests.post(f"http://{host}:{port}/api/model_card", json=data, timeout=12)
            return _json.dumps(r.json(), indent=2)
        except Exception as ex:
            return f"Error: {type(ex).__name__}: {ex}"

    # (Old guardrail/test not used in multi-tab)