"""
LLM Integration Support and Enhanced PII Detection

This module provides:
1. Enhanced PII detection patterns for LLM outputs
2. LLM-specific integration helpers
3. Code injection detection
4. SQL injection detection
5. Model-specific safety patterns
"""

import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import json

# Enhanced PII patterns for LLM outputs
ENHANCED_PII_PATTERNS = {
    "email": [
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        r"[A-Za-z0-9._%+-]+\s*\[at\]\s*[A-Za-z0-9.-]+\s*\[dot\]\s*[A-Za-z]{2,}",  # Obfuscated
        r"[A-Za-z0-9._%+-]+\s*at\s*[A-Za-z0-9.-]+\s*dot\s*[A-Za-z]{2,}",  # Text obfuscated
    ],
    "phone": [
        r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}",  # Standard
        r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # Simple format
        r"(?:phone|tel|mobile|cell)[\s:]*[\+]?[\d\s\-\(\)\.]+",  # With labels
    ],
    "ssn": [
        r"\b\d{3}-\d{2}-\d{4}\b",  # Standard format
        r"\b\d{3}\s\d{2}\s\d{4}\b",  # Space separated
        r"(?:SSN|social\s+security)[\s:]*\d{3}[-.\s]?\d{2}[-.\s]?\d{4}",  # With labels
    ],
    "credit_card": [
        r"\b(?:\d[ -]*?){13,19}\b",  # Standard format
        r"(?:credit\s+card|card\s+number)[\s:]*[\d\s\-]+",  # With labels
        r"\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b",  # 4x4 format
    ],
    "ip_address": [
        r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
        r"(?:IPv4|IP\s+address)[\s:]*[\d\.]+",
    ],
    "mac_address": [
        r"\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b",
        r"(?:MAC|hardware\s+address)[\s:]*[0-9A-Fa-f\-\:]+",
    ],
    "url": [
        r"https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?",
        r"(?:website|url|link)[\s:]*https?://[^\s]+",
    ],
    "file_path": [
        r"(?:/|C:\\)(?:[\w\-\.]+/)*[\w\-\.]+(?:\.\w+)?",  # Unix/Windows paths
        r"(?:file|path)[\s:]*[/\\][^\s]+",
    ],
    "api_key": [
        r"(?:api[_-]?key|access[_-]?token|secret[_-]?key)[\s:]*[A-Za-z0-9\-_]{20,}",
        r"sk-[A-Za-z0-9]{20,}",  # OpenAI-style
        r"pk_[A-Za-z0-9]{20,}",  # Stripe-style
    ],
    "database_connection": [
        r"(?:mysql|postgresql|mongodb)://[^\s]+",
        r"(?:host|database|db)[\s:]*[^\s]+",
    ],
    "code_injection": [
        r"<script[^>]*>.*?</script>",  # HTML script tags
        r"javascript:",  # JavaScript protocol
        r"on\w+\s*=",  # Event handlers
        r"eval\s*\(",  # eval function
        r"document\.",  # DOM manipulation
        r"window\.",  # Window object
        r"localStorage\.",  # Local storage
        r"sessionStorage\.",  # Session storage
    ],
    "sql_injection": [
        r"(?:SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\s+.*?(?:FROM|INTO|WHERE|VALUES)",
        r"UNION\s+SELECT",
        r"OR\s+1\s*=\s*1",
        r"';?\s*--",
        r"';?\s*#",
        r"';?\s*/\*",
    ],
    "prompt_injection": [
        r"ignore\s+(?:previous|above|all)\s+(?:instructions|prompts|rules)",
        r"disregard\s+(?:previous|above|all)\s+(?:instructions|prompts|rules)",
        r"override\s+(?:system|safety|rules)",
        r"act\s+as\s+(?:a\s+)?(?:different|new|other)",
        r"jailbreak",
        r"developer\s+mode",
        r"no\s+restrictions",
        r"bypass\s+(?:safety|rules|filters)",
        r"do\s+anything\s+now",
        r"system\s+prompt",
        r"roleplay\s+as",
    ],
}

# Compile all patterns for efficiency
COMPILED_PII_PATTERNS = {
    category: [re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
               for pattern in patterns]
    for category, patterns in ENHANCED_PII_PATTERNS.items()
}

@dataclass
class PIIDetectionResult:
    """Result of PII detection for a text"""
    text: str
    redacted_text: str
    detected_types: List[str]
    confidence_scores: Dict[str, float]
    redaction_count: int

class EnhancedPIIDetector:
    """Enhanced PII detection with LLM-specific patterns"""
    
    def __init__(self, custom_patterns: Optional[Dict[str, List[str]]] = None):
        self.patterns = COMPILED_PII_PATTERNS.copy()
        if custom_patterns:
            for category, patterns in custom_patterns.items():
                self.patterns[category] = [
                    re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                    for pattern in patterns
                ]
    
    def detect_pii(self, text: str) -> PIIDetectionResult:
        """Detect PII in text and return detailed results"""
        detected_types = []
        confidence_scores = {}
        redacted_text = text
        redaction_count = 0
        
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text)
                if matches:
                    detected_types.append(category)
                    # Calculate confidence based on match quality
                    confidence = min(1.0, len(matches) * 0.3)
                    confidence_scores[category] = confidence
                    
                    # Redact based on category
                    replacement = f"[REDACTED_{category.upper()}]"
                    redacted_text = pattern.sub(replacement, redacted_text)
                    redaction_count += len(matches)
        
        return PIIDetectionResult(
            text=text,
            redacted_text=redacted_text,
            detected_types=detected_types,
            confidence_scores=confidence_scores,
            redaction_count=redaction_count
        )
    
    def detect_pii_batch(self, texts: List[str]) -> List[PIIDetectionResult]:
        """Detect PII in a batch of texts"""
        return [self.detect_pii(text) for text in texts]

# LLMIntegrationHelper: Provider-coupled guardrail configs removed. This toolkit does NOT implement or recommend per-provider defaults.
# Users must provide all policies, blocklists, redaction, and pattern logic themselves, according to their specific provider/model/LLM needs.

# Factory removed: Users must build their own provider- or model-specific config/guardrails, as appropriate for their workflow and risk tolerance.