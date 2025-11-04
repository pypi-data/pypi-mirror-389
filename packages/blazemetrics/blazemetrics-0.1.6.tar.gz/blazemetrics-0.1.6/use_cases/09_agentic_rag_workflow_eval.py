"""
09_agentic_rag_workflow_eval.py

Use Case: Agentic RAG Workflow (Multi-step Agents, Tool Use, Task Decomposition)
-------------------------------------------------------------------------------
Evaluation for advanced agentic pipelines: multi-step decisionmaking, tool orchestration, and RAG provenance.
- Works with real traces from frameworks like LangChain, crewAI, or custom logs
- Computes granular agent performance metrics (task, coordination, retrieval, etc)
- Solid base for production AI workflow/agent benchmarking

Replace simulated traces/outputs with logs from your actual LLM agent execution system.
"""
from blazemetrics import AgenticRAGEvaluator

# Example user queries
queries = [
    "Find the official biography of Ada Lovelace and cite the primary sources.",
    "Plan a day trip in Kyoto, including transport and restaurant recommendations."
]
# Example traces from agent runs (replace with your real logs)
agent_traces = [
    {
        "steps": [
            {"tool": "WebSearch", "input": "Ada Lovelace biography", "output": "Wikipedia/encyclopedia links..."},
            {"tool": "CitationExtractor", "input": "...", "output": "Primary source: Letters of Ada Lovelace"},
            {"tool": "LLM", "input": "Summarize and cite", "output": "Ada Lovelace was ... (Letter 1842)"}
        ],
        "decisions": ["Used fact sources", "Cited correctly"],
        "coordination": True
    },
    {
        "steps": [
            {"tool": "TravelAPI", "input": "Kyoto day trip", "output": "Train schedule, sights list."},
            {"tool": "RestaurantAPI", "input": "Kyoto restaurants", "output": "Sushi Dai, % ratings"},
            {"tool": "LLM", "input": "Weave plan", "output": "You can start at Fushimi Inari..."}
        ],
        "decisions": ["Diversified options", "Used up-to-date info"],
        "coordination": True
    }
]
expected_outputs = [
    "Biography is in her letters, cite 1842, also cite Wikipedia.",
    "Visit Fushimi Inari, use JR Line, lunch at Sushi Dai or Gion area."
]
metrics = ["agent_efficiency", "retrieval_precision", "coordination_score", "task_completion_rate"]

evaluator = AgenticRAGEvaluator(
    track_agent_decisions=True, measure_tool_usage=True, evaluate_coordination=True
)
results = evaluator.evaluate(queries, agent_traces, expected_outputs, metrics)
print("--- Agentic RAG Evaluation ---")
for k, v in results.items():
    print(f"  {k}: {v:.3f}")
