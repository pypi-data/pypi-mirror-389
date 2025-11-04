# Minimal working FastAPI API for BlazeMetrics dashboard
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_api(analytics=None, metrics_iter=None):
    app = FastAPI(title="BlazeMetrics Dashboard API")

    # Enable CORS for all origins (dev only; adjust for production!)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health_check():
        return {"status": "ok"}

    # Metrics evaluation endpoint
    @app.post("/api/metrics")
    async def compute_metrics(payload: dict):
        # Expect: {candidates: [...], references: [[...]], (optional) include,...}
        from blazemetrics.client import BlazeMetricsClient
        candidates = payload.get("candidates", [])
        references = payload.get("references", [])
        include = payload.get("include")
        lowercase = payload.get("lowercase")
        stemming = payload.get("stemming")
        client = BlazeMetricsClient()
        result = client.compute_metrics(candidates, references, include, lowercase, stemming)
        return {"metrics": result}

    # Streaming Analytics summary
    @app.get("/api/analytics")
    async def analytics_summary():
        # Must be supplied in constructor
        if analytics:
            return analytics.get_metric_summary()
        return {"error": "Analytics not instantiated on server."}
    
    # Model card reporting endpoint
    @app.post("/api/model_card")
    async def generate_model_card(payload: dict):
        from blazemetrics.client import BlazeMetricsClient
        client = BlazeMetricsClient()
        model_name = payload.get("model_name", "Unknown")
        metrics = payload.get("metrics", {})
        analytics_data = payload.get("analytics", {})
        config = payload.get("config", {})
        violations = payload.get("violations")
        factuality = payload.get("factuality")
        provenance = payload.get("provenance")
        format = payload.get("format", "markdown")
        return {"card": client.generate_model_card(model_name, metrics, analytics_data, config, violations, factuality, provenance, format)}
    
    # Data card reporting endpoint
    @app.post("/api/data_card")
    async def generate_data_card(payload: dict):
        from blazemetrics.client import BlazeMetricsClient
        client = BlazeMetricsClient()
        dataset_name = payload.get("dataset_name", "Unknown")
        evaluation = payload.get("evaluation", {})
        analytics_data = payload.get("analytics", {})
        config = payload.get("config")
        format = payload.get("format", "markdown")
        return {"card": client.generate_data_card(dataset_name, evaluation, analytics_data, config, format)}

    # Alert history endpoint
    @app.get("/api/alerts")
    async def alert_history():
        if analytics and hasattr(analytics, 'alert_history'):
            return {"alerts": list(analytics.alert_history)}
        return {"alerts": []}

    # Guardrails text check endpoint
    @app.post("/api/guardrails")
    async def check_guardrails(payload: dict):
        from blazemetrics.client import BlazeMetricsClient
        client = BlazeMetricsClient()
        texts = payload.get("texts", [])
        config = payload.get("config", {})
        # Instantiate guardrails with custom config if requested
        guardrails = client.get_guardrails() if not config else BlazeMetricsClient(config).get_guardrails()
        result = guardrails.check(texts)
        return {"guardrails": result}

    # Agent evaluation endpoint
    @app.post("/api/agent_eval")
    async def agent_eval(payload: dict):
        from blazemetrics.client import BlazeMetricsClient
        client = BlazeMetricsClient()
        tasks = payload.get("tasks", [])
        agent_traces = payload.get("agent_traces", [])
        metrics = payload.get("metrics")
        available_tools = payload.get("available_tools")
        safety_policies = payload.get("safety_policies")
        goal_tracking = payload.get("goal_tracking", True)
        result = client.evaluate_agent(tasks, agent_traces, metrics, available_tools, safety_policies, goal_tracking)
        return {"agent_eval": result}

    # Code evaluation endpoint
    @app.post("/api/code_eval")
    async def code_eval(payload: dict):
        from blazemetrics.client import BlazeMetricsClient
        client = BlazeMetricsClient()
        prompts = payload.get("prompts", [])
        generated_code = payload.get("generated_code", [])
        reference_solutions = payload.get("reference_solutions", [])
        metrics = payload.get("metrics")
        languages = payload.get("languages")
        security_checks = payload.get("security_checks", True)
        performance_analysis = payload.get("performance_analysis", True)
        result = client.evaluate_code(prompts, generated_code, reference_solutions, metrics, languages, security_checks, performance_analysis)
        return {"code_eval": result}

    # Factuality scoring endpoint (requires user to POST a callable reference, here mocked for demo)
    @app.post("/api/factuality")
    async def factuality_eval(payload: dict):
        from blazemetrics.client import BlazeMetricsClient
        client = BlazeMetricsClient()
        # Factuality scoring requires a custom callable—a simple mock logic for demo
        def dummy_scorer(output, reference):
            return {"factuality": 1.0 if reference and reference in output else 0.0}
        client.set_factuality_scorer(dummy_scorer)
        outputs = payload.get("outputs", [])
        references = payload.get("references")
        metadata = payload.get("metadata")
        result = client.evaluate_factuality(outputs, references, metadata)
        return {"factuality": result}

    # RAG provenance endpoint
    @app.post("/api/rag_provenance")
    async def rag_provenance(payload: dict):
        from blazemetrics.client import BlazeMetricsClient
        client = BlazeMetricsClient()
        outputs = payload.get("outputs", [])
        rag_chunks = payload.get("rag_chunks", [])
        output_citations = payload.get("output_citations")
        result = client.trace_provenance(outputs, rag_chunks, output_citations)
        return {"provenance": result}

    return app
