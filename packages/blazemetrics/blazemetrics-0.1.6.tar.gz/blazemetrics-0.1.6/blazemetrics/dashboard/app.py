# New dashboard/app.py
import argparse
import os
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware

from .api import create_api
from .layout import get_layout
from .callbacks import register_callbacks

import dash
import uvicorn


def run_dashboard(host="127.0.0.1", port=8000, analytics=None, metrics_iter=None):
    parser = argparse.ArgumentParser(description="BlazeMetrics Dashboard Server")
    parser.add_argument("--host", default=host, type=str, help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", default=port, type=int, help="Bind port (default: 8000)")
    args, _ = parser.parse_known_args()
    host = os.environ.get("BLAZEMETRICS_DASHBOARD_HOST", args.host)
    port = int(os.environ.get("BLAZEMETRICS_DASHBOARD_PORT", args.port))

    # Backing FastAPI + all API endpoints
    app = create_api(analytics=analytics, metrics_iter=metrics_iter)

    # Dash
    dash_app = dash.Dash(__name__, requests_pathname_prefix="/dashboard/")
    dash_app.layout = get_layout()
    register_callbacks(dash_app, host, port)

    # Mount Dash UI onto FastAPI
    app.mount("/dashboard", WSGIMiddleware(dash_app.server))

    print(f"\n Running BlazeMetrics Dashboard: http://{host}:{port}/dashboard")
    uvicorn.run(app, host=host, port=port, log_level="warning")

if __name__ == "__main__":
    run_dashboard()
