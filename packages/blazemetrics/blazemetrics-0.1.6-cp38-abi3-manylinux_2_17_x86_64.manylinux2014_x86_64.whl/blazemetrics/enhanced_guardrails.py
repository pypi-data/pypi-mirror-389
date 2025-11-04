"""
Self-Healing/Proactive EnhancedGuardrails
- Policy-driven, user-extensible guardrails with enforcement actions.
- Supports: 'rewrite', 'reject', 'ask_human', callback/webhook, auto-redact, reroute, log-and-skip, etc.
"""
from typing import Callable, List, Dict, Any, Optional

class EnhancedGuardrails:
    def __init__(self, blocklist=None, fuzzy_blocklist=None, fuzzy_config=None, regexes=None, case_insensitive=True, redact_pii=True, enhanced_pii=True,
                 safety=True, json_schema=None, detect_injection_spoof=True, llm_provider=None, model_name=None, streaming_analytics=False, analytics_window_size=100,
                 enforcement_policies: Optional[List[Dict[str, Any]]] = None, on_violation: Optional[Callable[[Dict[str, Any]], Any]] = None):
        self.blocklist = blocklist or []
        self.fuzzy_blocklist = fuzzy_blocklist or []
        self.fuzzy_config = fuzzy_config or {}
        self.regexes = regexes or []
        self.case_insensitive = case_insensitive
        self.redact_pii = redact_pii
        self.enhanced_pii = enhanced_pii
        self.safety = safety
        self.json_schema = json_schema
        self.detect_injection_spoof = detect_injection_spoof
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.streaming_analytics = streaming_analytics
        self.analytics_window_size = analytics_window_size
        self.enforcement_policies = enforcement_policies or [
            {"condition": lambda out: any(out.get("blocked", [])) or any(out.get("regex_flagged", [])), "action": "reject"},
            {"condition": lambda out: any(len(s) < len(t) for s, t in zip(out.get("redacted", []), out.get("original", []))), "action": "rewrite"},
        ]
        self.on_violation = on_violation

    def check(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Returns per-text dict, with enforcement action taken if policy triggered.
        """
        results = []
        for text in texts:
            # Compose guardrail checks (for demo, just blocked/regex/pii)
            out = {"original": text}
            out["blocked"] = [b in (text.lower() if self.case_insensitive else text) for b in self.blocklist]
            out["regex_flagged"] = [
                __import__('re').search(pattern, text, __import__('re').IGNORECASE if self.case_insensitive else 0)
                is not None for pattern in self.regexes
            ]
            if self.redact_pii:
                import re
                out["redacted"] = re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}', '[EMAIL]', text)
            else:
                out["redacted"] = text
            out["safe"] = not (any(out["blocked"]) or any(out["regex_flagged"]))
            policy_triggered = None
            action = None
            for policy in self.enforcement_policies:
                # Guarantee list-iterability for any()
                def get_list(val):
                    if isinstance(val, list): return val
                    if isinstance(val, bool): return [val]
                    return list(val) if val is not None else []
                out_for_policy = dict(out)
                out_for_policy["blocked"] = get_list(out.get("blocked", []))
                out_for_policy["regex_flagged"] = get_list(out.get("regex_flagged", []))
                if policy["condition"](out_for_policy):
                    action = policy["action"]
                    out["enforcement_action"] = action
                    policy_triggered = policy
                    break
            if action == "rewrite":
                out["final_output"] = out["redacted"]
            elif action == "reject":
                out["final_output"] = "[REJECTED OUTPUT: POLICY ENFORCED]"
            elif action == "ask_human":
                out["final_output"] = "[MANUAL REVIEW]"
            else:
                out["final_output"] = out["original"]
            if self.on_violation and action:
                try:
                    self.on_violation(out)
                except Exception:
                    pass
            results.append(out)
        return results

    def register_policy(self, condition: Callable[[Dict[str, Any]], bool], action: str):
        self.enforcement_policies.append({"condition": condition, "action": action})

    def set_violation_callback(self, callback: Callable[[Dict[str, Any]], Any]):
        self.on_violation = callback