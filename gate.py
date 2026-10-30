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