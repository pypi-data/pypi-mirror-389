"""
06_code_generation_evaluation.py

Use Case: Code Generation Model Evaluation — Correctness, Security & Style
---------------------------------------------------------------------------
Assess code generation models using classical metrics, security, and advanced criteria.
 - Supports multiple languages (Python, C++, etc.) and real-world scoring
 - Results reflect correctness, code quality, and optionally security vulnerabilities (if supported by the backend)

Adapt to integrate with your own code output pipeline and real prompt/solution pairs.
"""
from blazemetrics import CodeEvaluator

prompts = [
    "Write a function to sum two numbers in Python.",
    "Print hello world in C++.",
]
generated_code = [
    "def add(a, b):\n    return a + b",
    "#include <iostream>\nint main() { std::cout << 'Hello world'; }",
]
reference_solutions = [
    "def add(a, b):\n    return a + b",
    "#include <iostream>\nint main() { std::cout << \"Hello world\"; }",
]
languages = ["python", "cpp"]

code_eval = CodeEvaluator(languages=languages, security_checks=True)
results = code_eval.evaluate(prompts, generated_code, reference_solutions)
print("--- Code Generation Evaluation ---")
for k, v in results.items():
    print(f"  {k}: {v:.3f}")
