import os
import re
from dataclasses import dataclass


DEFAULT_MAX_CHARS = int(os.environ.get("MAX_PROMPT_CHARS", "2000"))
DEFAULT_POLICY_MODE = os.environ.get("POLICY_MODE", "strict")

INJECTION_PATTERNS = [
    r"ignore\s+previous",
    r"system\s+prompt",
    r"developer\s+message",
    r"reveal\s+secrets",
    r"bypass\s+policy",
    r"jailbreak",
    r"do\s+anything\s+now",
]

SENSITIVE_KEYWORDS = {
    "password",
    "secret",
    "api key",
    "token",
    "private key",
    "ssn",
    "social security",
    "credit card",
    "confidential",
}

OUTPUT_SENSITIVE_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b\d{13,16}\b"),
]


@dataclass
class GuardrailResult:
    allowed: bool
    policy_mode: str
    violations: list[str]
    injection_detected: bool
    sensitive_detected: bool
    risk_score: int
    prompt_length: int


@dataclass
class OutputFilterResult:
    sanitized_text: str
    redactions: int
    blocked: bool


def _keyword_hit(prompt: str, keywords: set[str]) -> bool:
    text = prompt.lower()
    return any(keyword in text for keyword in keywords)

def detect_sensitive(prompt: str) -> bool:
    return _keyword_hit(prompt, SENSITIVE_KEYWORDS)


def validate_input(prompt: str, max_chars: int) -> tuple[bool, list[str]]:
    errors = []
    if not prompt or not prompt.strip():
        errors.append("prompt is required")
    if max_chars and len(prompt) > max_chars:
        errors.append(f"prompt exceeds {max_chars} characters")
    return len(errors) == 0, errors


def detect_injection(prompt: str) -> bool:
    lowered = prompt.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return True
    return False


def evaluate_policy(
    prompt: str,
    policy_mode: str | None,
    allow_override: bool,
    max_chars: int | None = None,
) -> GuardrailResult:
    mode = (policy_mode or DEFAULT_POLICY_MODE).strip().lower()
    mode = mode if mode in {"strict", "monitor"} else "strict"

    max_len = max_chars if max_chars is not None else DEFAULT_MAX_CHARS
    ok, errors = validate_input(prompt, max_len)

    injection = detect_injection(prompt)
    sensitive = detect_sensitive(prompt)

    risk_score = 0
    violations: list[str] = []

    if not ok:
        violations.extend(errors)
        risk_score += 3
    if injection:
        violations.append("prompt_injection_detected")
        risk_score += 5
    if sensitive:
        violations.append("sensitive_keyword_detected")
        risk_score += 3

    allowed = True
    if mode == "strict" and (not ok or injection or sensitive):
        allowed = False
    if allow_override and not ok:
        allowed = False

    return GuardrailResult(
        allowed=allowed,
        policy_mode=mode,
        violations=violations,
        injection_detected=injection,
        sensitive_detected=sensitive,
        risk_score=risk_score,
        prompt_length=len(prompt),
    )


def sanitize_output(text: str) -> OutputFilterResult:
    sanitized = text
    redactions = 0
    for pattern in OUTPUT_SENSITIVE_PATTERNS:
        matches = pattern.findall(sanitized)
        if matches:
            redactions += len(matches)
            sanitized = pattern.sub("[REDACTED]", sanitized)

    blocked = False
    if "[REDACTED]" in sanitized:
        blocked = False

    return OutputFilterResult(
        sanitized_text=sanitized,
        redactions=redactions,
        blocked=blocked,
    )
