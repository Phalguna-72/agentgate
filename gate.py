import yaml
import os
import time

def load_policy(path: str = "policy.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def check_identity(policy: dict, role: str, tool_name: str) -> bool:
    allowed = policy["roles"].get(role, {}).get("allowed_tools", [])
    return tool_name in allowed


DESTRUCTIVE_TOOLS = ["delete_file", "send_email"]


def check_intent(user_request: str, tool_name: str) -> bool:
    rules = {
        "read_file": ["read", "open", "show", "summarize", "look at"],
        "query_db": ["query", "database", "look up", "find", "count"],
        "send_email": ["email", "send", "message"],
        "delete_file": ["delete", "remove", "erase"],
    }
    request = user_request.lower()

    # If the request mentions a destructive action, it must belong to the tool being called
    for other_tool in DESTRUCTIVE_TOOLS:
        if other_tool != tool_name and any(word in request for word in rules[other_tool]):
            return False

    keywords = rules.get(tool_name, [])
    return any(word in request for word in keywords)



call_history: dict[str, list[float]] = {}


def check_behavior(policy: dict, tool_name: str, now: float | None = None, user: str = "anon") -> bool:
    limit = policy["rate_limit"]
    if tool_name != limit["tool"]:
        return True
    now = time.time() if now is None else now
    key = f"{user}:{tool_name}"
    history = call_history.setdefault(key, [])
    history[:] = [t for t in history if now - t < limit["window_seconds"]]
    if len(history) >= limit["max_calls"]:
        return False
    history.append(now)
    return True

def decide(policy: dict, role: str, user_request: str, tool_name: str,
           arg: str = "", now: float | None = None, user: str = "anon") -> dict:
    if not check_identity(policy, role, tool_name):
        return {"decision": "DENY", "reason": f"role '{role}' may not use {tool_name}"}
    if not check_arguments(policy, tool_name, arg):
        return {"decision": "DENY", "reason": f"argument '{arg}' is not allowed for {tool_name}"}
    if not check_intent(user_request, tool_name):
        return {"decision": "NEEDS_APPROVAL", "reason": "tool does not match the user's request"}
    if not check_behavior(policy, tool_name, now, user):
        return {"decision": "DENY", "reason": "too many calls in a short time"}
    return {"decision": "ALLOW", "reason": "passed identity, intent and behavior checks"}



def check_arguments(policy: dict, tool_name: str, tool_arg: str) -> bool:
    if tool_name == "send_email":
        # the address is the argument; only allowed domains pass
        if "@" not in tool_arg:
            return False
        domain = tool_arg.rsplit("@", 1)[-1].lower()
        return domain in policy.get("allowed_email_domains", [])
    # file tools: the path must stay inside the allowed folder
    if tool_name not in ("read_file", "delete_file"):
        return True
    prefix = policy.get("allowed_path_prefix", "data/")
    cleaned = os.path.normpath(tool_arg).replace("\\", "/")
    
    return cleaned.startswith(prefix)