import itertools
from audit import write_audit
from gate import load_policy, check_identity

_ids = itertools.count(1)
pending: dict[int, dict] = {}


def request_approval(role: str, request: str, tool_name: str, tool_arg: str, user: str = "anon") -> int:
    ticket = next(_ids)
    pending[ticket] = {"role": role, "request": request, "tool_name": tool_name,
                       "tool_arg": tool_arg, "user": user}
    write_audit({"event": "pending", "ticket": ticket, **pending[ticket]})
    return ticket


def reject(ticket: int) -> str:
    item = pending.pop(ticket)
    write_audit({"event": "rejected", "ticket": ticket, "tool": item["tool_name"]})
    return "REJECTED"


def approve(ticket: int, run) -> str:
    item = pending.pop(ticket)
    # approval never grants permissions: identity is checked again
    if not check_identity(load_policy(), item["role"], item["tool_name"]):
        write_audit({"event": "approval_refused", "ticket": ticket, "tool": item["tool_name"]})
        return "DENIED: this role may not use the tool, even with approval"
    write_audit({"event": "approved", "ticket": ticket, "tool": item["tool_name"]})
    return run(item["tool_name"], item["tool_arg"])