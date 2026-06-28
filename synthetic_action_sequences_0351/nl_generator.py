"""
Natural Language Input Generator — produces varied NL phrasings for automation tasks.
Supports 6 syntactic patterns: imperative, polite request, conditional, time-constrained,
multi-conditional, question-form. Includes rollback-aware phrasings.

Usage:
    result = generate_nl("Deploy {service} to {env}", {"service":"api-gateway","env":"staging"}, rng=my_random_instance)
    # Or without rng — uses random module directly.
"""

import random
import re

# Vocabulary substitutions for diverse phrasings — used to add variety to base descriptions
SYNONYM_MAP = {
    "provision": ["provision", "spin up", "launch", "set up", "create", "deploy", "initialize", "stand up"],
    "delete": ["delete", "remove", "terminate", "destroy", "tear down", "deprovision", "clean up"],
    "create": ["create", "make", "generate", "build", "establish", "set up", "configure", "form"],
    "upload": ["upload", "push", "publish", "submit", "send", "transfer", "copy"],
    "deploy": ["deploy", "release", "roll out", "push", "ship", "publish", "distribute"],
    "capture": ["capture", "charge", "process", "collect", "settle", "accept"],
    "generate": ["generate", "produce", "create", "compile", "build", "run", "compute"],
    "process": ["process", "run", "execute", "handle", "compute", "calculate"],
    "authorize": ["authorize", "approve", "validate", "pre-auth", "hold"],
    "refund": ["refund", "reverse", "credit back", "reimburse", "repay"],
    "stop": ["stop", "halt", "pause", "suspend", "shut down"],
    "start": ["start", "begin", "boot", "launch", "initiate"],
    "attach": ["attach", "assign", "link", "bind", "connect"],
    "detach": ["detach", "remove", "unlink", "unbind", "disconnect"],
}

ROLLBACK_PHRASES = [
    "with automatic rollback",
    "with cleanup on failure",
    "and undo if it fails",
    "with rollback safeguards",
    "and revert on error",
    "with compensation on failure",
    "with automatic cleanup",
    "make sure to undo if something goes wrong",
    "with rollback coverage",
    "with failure compensation",
    "and revert if issues arise",
]

ROLLBACK_WARNINGS = [
    "if anything fails, roll back",
    "undo everything if there is an error",
    "clean up resources if something breaks",
    "revert changes on failure",
    "compensate if any step fails",
]

CONDITIONS = [
    "the system is ready",
    "approval is granted",
    "the prerequisites are met",
    "the dependency check passes",
    "the environment is available",
    "the queue is not full",
    "validation succeeds",
    "the resource is free",
]

DEADLINES = ["end of day", "Friday", "next Monday", "tomorrow", "the end of the week", "Thursday"]
TIMEFRAMES = ["the next hour", "the next 30 minutes", "today", "a day", "two hours"]

IMPERATIVE_ADVERBS = ["quickly", "automatically", "immediately", "now", "promptly", "right away"]
POLITE_STARTERS = ["Please", "Could you please", "Kindly", "Would you please"]
CONDITIONAL_TEMPLATES = [
    "If {cond}, {base}",
    "When {cond}, {base}",
    "In case {cond}, {base}",
    "Should {cond}, {base}",
]
TIME_TEMPLATES = [
    "{base} by {deadline}",
    "Need to {base} before {deadline}",
    "{base} within {timeframe}",
    "Urgent: {base} as soon as possible",
    "{base} no later than {deadline}",
]
MULTI_TEMPLATES = [
    "First {a}, then {b}",
    "{a} and subsequently {b}",
]
QUESTION_TEMPLATES = [
    "Can you {base}?",
    "Is it possible to {base}?",
    "Would it be feasible to {base}?",
    "Could we {base}?",
    "How do I {base}?",
]


def _get_rng(rng):
    """Return the provided rng or the global random module."""
    return rng if rng is not None else random


def _fill_placeholders(template_str, params):
    """Replace {placeholders} with actual values from params dict."""
    def replace_one(match):
        content = match.group(1)
        # Support {param/divisor} patterns for money values
        if "/" in content:
            parts = content.split("/")
            param_name = parts[0].strip()
            divisor = parts[1].strip()
            if param_name in params:
                try:
                    val = int(params[param_name]) / int(divisor)
                    return f"${val:.0f}"
                except (ValueError, TypeError):
                    return str(params.get(param_name, match.group(0)))
        return str(params.get(content, match.group(0)))

    return re.sub(r'\{([^}]+)\}', replace_one, template_str)


def _apply_synonyms(text, rng):
    """Replace the first known verb word with a synonym for variety."""
    words = text.split()
    if not words:
        return text
    first_word = words[0].lower().rstrip(".,!?;")
    for key, synonyms in SYNONYM_MAP.items():
        if key == first_word or first_word.startswith(key):
            repl = rng.choice(synonyms)
            if words[0][0].isupper():
                repl = repl[0].upper() + repl[1:]
            words[0] = repl
            break
    return " ".join(words)


def _add_rollback_phrasing(text, rng):
    """Append or prepend rollback-aware phrasing to text."""
    coin = rng.random()
    if coin < 0.4:
        return f"{text.rstrip('.?!')}, {rng.choice(ROLLBACK_PHRASES)}"
    elif coin < 0.7:
        return f"{rng.choice(ROLLBACK_WARNINGS)}: {text}"
    else:
        parts = text.split(",", 1)
        if len(parts) > 1:
            return f"{parts[0]} with automatic cleanup,{parts[1]}"
        return text


def generate_nl(template_str, params, rng=None):
    """
    Generate varied natural language input from a template string and parameter dict.

    Supports 6 syntactic patterns: imperative, polite request, conditional,
    time-constrained, multi-conditional, question-form. Includes rollback-aware phrasings.

    Args:
        template_str: String with {placeholders} like "Deploy {service} to {env}"
        params: Dict of parameter values like {"service": "api-gateway", "env": "staging"}
        rng: Optional random.Random instance for seeded reproducibility. If None,
             uses the global random module.

    Returns:
        String with varied natural language phrasing (20-250 chars)
    """
    rng = _get_rng(rng)

    # Step 1: Fill placeholders to get the base description
    base = _fill_placeholders(template_str, params)
    if not base.strip():
        return template_str

    # Step 2: Detect if template has rollback intent
    is_rollback_aware = any(
        phrase in template_str.lower()
        for phrase in ["rollback", "roll back", "cleanup", "clean up", "revert", "undo", "failure", "error"]
    )

    # Step 3: Apply synonym substitution for variety (~40% chance)
    if rng.random() < 0.4:
        base = _apply_synonyms(base, rng)

    # Step 4: Choose a syntactic pattern and build output
    base_lc = base[0].lower() + base[1:] if base else base

    pattern_choice = rng.random()

    if pattern_choice < 0.25:
        # IMPERATIVE: use description directly
        if rng.random() < 0.3:
            result = f"{rng.choice(IMPERATIVE_ADVERBS).capitalize()}, {base_lc}"
        else:
            result = base

    elif pattern_choice < 0.40:
        # POLITE REQUEST
        result = f"{rng.choice(POLITE_STARTERS)} {base_lc}"

    elif pattern_choice < 0.55:
        # CONDITIONAL
        result = rng.choice(CONDITIONAL_TEMPLATES).format(
            cond=rng.choice(CONDITIONS), base=base_lc
        )

    elif pattern_choice < 0.70:
        # TIME-CONSTRAINED
        result = rng.choice(TIME_TEMPLATES).format(
            base=base_lc, deadline=rng.choice(DEADLINES), timeframe=rng.choice(TIMEFRAMES)
        )

    elif pattern_choice < 0.85:
        # MULTI-CONDITIONAL
        words = base.split()
        mid = max(1, len(words) // 2)
        part_a = " ".join(words[:mid])
        part_b = " ".join(words[mid:])
        result = rng.choice(MULTI_TEMPLATES).format(a=part_a, b=part_b)

    else:
        # QUESTION FORM
        result = rng.choice(QUESTION_TEMPLATES).format(base=base_lc)

    # Step 5: Add rollback phrasing
    if is_rollback_aware and rng.random() < 0.6:
        result = _add_rollback_phrasing(result, rng)
    elif rng.random() < 0.10:
        result = _add_rollback_phrasing(result, rng)

    # Step 6: Clean up
    result = result.strip()
    if result and result[-1] not in ".!?":
        result += "."
    if result:
        result = result[0].upper() + result[1:]

    return result


def generate_nl_variants(template_str, params, count=1, rng=None):
    """Generate multiple varied NL phrasings for the same template."""
    rng = _get_rng(rng)
    results = []
    seen = set()
    attempts = 0
    while len(results) < count and attempts < count * 5:
        text = generate_nl(template_str, params, rng)
        if text not in seen:
            seen.add(text)
            results.append(text)
        attempts += 1
    return results