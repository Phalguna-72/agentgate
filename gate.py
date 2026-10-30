import yaml


def load_policy(path: str = "policy.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def check_identity(policy: dict, role: str, tool_name: str) -> bool:
    allowed = policy["roles"].get(role, {}).get("allowed_tools", [])
    return tool_name in allowed


def check_intent(user_request: str, tool_name: str) -> bool:
    # Keyword rules: each tool must be mentioned in a way that fits the request
    rules = {
        "read_file": ["read", "open", "show", "summarize", "look at"],
        "query_db": ["query", "database", "look up", "find", "count"],
        "send_email": ["email", "send", "message"],
        "delete_file": ["delete", "remove", "erase"],
    }
    keywords = rules.get(tool_name, [])
    request = user_request.lower()
    return any(word in request for word in keywords)


import time

call_history: dict[str, list[float]] = {}


def check_behavior(policy: dict, tool_name: str, now: float | None = None) -> bool:
    limit = policy["rate_limit"]
    if tool_name != limit["tool"]:
        return True
    now = time.time() if now is None else now
    history = call_history.setdefault(tool_name, [])
    # keep only the calls made inside the time window
    history[:] = [t for t in history if now - t < limit["window_seconds"]]
    if len(history) >= limit["max_calls"]:
        return False
    history.append(now)
    return True


def decide(policy: dict, role: str, user_request: str, tool_name: str, now: float | None = None) -> dict:
    if not check_identity(policy, role, tool_name):
        return {"decision": "DENY", "reason": f"role '{role}' may not use {tool_name}"}
    if not check_intent(user_request, tool_name):
        return {"decision": "NEEDS_APPROVAL", "reason": "tool does not match the user's request"}
    if not check_behavior(policy, tool_name, now):
        return {"decision": "DENY", "reason": "too many calls in a short time"}
    return {"decision": "ALLOW", "reason": "passed identity, intent and behavior checks"}