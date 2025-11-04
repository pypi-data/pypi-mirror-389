from dash import dcc, html

def get_layout():
    return html.Div([
        dcc.Store(id="theme-store", data="dark"),
        dcc.Store(id="last-alert-id", data=0),
        dcc.Interval(id='interval-component', interval=2 * 1000, n_intervals=0),
        dcc.Download(id="download-data"),
        # Main Header
        html.Header([
            html.H1(" BlazeMetrics", style={"margin": "0", "fontSize": "1.8rem", "fontWeight": "700"}),
            html.P("Unified LLM, GenAI, ML Analytics & Audit Suite", style={"margin": "6px 0 0", "opacity": "0.65"})
        ]),
        html.Br(),
        dcc.Tabs(id="nav-tabs", value="metrics", children=[
            dcc.Tab(label="Metrics Eval", value="metrics"),
            dcc.Tab(label="Analytics/Trends", value="analytics"),
            dcc.Tab(label="Alerts/Guardrails", value="guardrails"),
            dcc.Tab(label="Agent Eval", value="agent_eval"),
            dcc.Tab(label="Code Eval", value="code_eval"),
            dcc.Tab(label="Factuality", value="factuality"),
            dcc.Tab(label="RAG Provenance", value="rag"),
            dcc.Tab(label="Reporting", value="reporting"),
        ]),
        html.Div(id="tab-content"),
        html.Footer([
            html.Hr(),
            html.P("© 2025 BlazeMetrics – Owner: You. Open-source LLM/GenAI analytics suite.", style={"fontSize": "0.95em", "color": "#666", "textAlign": "center", "marginBottom": "5px"})
        ])
    ])
