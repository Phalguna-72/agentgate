from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from gate import load_policy, decide
from tools import read_file, query_db, send_email, delete_file
from audit import write_audit

policy = load_policy()

TOOLS = {
    "read_file": read_file,
    "query_db": query_db,
    "send_email": send_email,
    "delete_file": delete_file,
}


class AgentState(TypedDict):
    role: str
    request: str
    tool_name: str
    tool_arg: str
    decision: str
    reason: str
    result: str


def gate_node(state: AgentState) -> dict:
    verdict = decide(policy, state["role"], state["request"], state["tool_name"])
    write_audit({
        "role": state["role"],
        "request": state["request"],
        "tool": state["tool_name"],
        "decision": verdict["decision"],
        "reason": verdict["reason"],
    })
    return {"decision": verdict["decision"], "reason": verdict["reason"]}


def run_tool(state: AgentState) -> dict:
    name = state["tool_name"]
    if name == "send_email":
        result = send_email(state["tool_arg"], "hello")
    else:
        result = TOOLS[name](state["tool_arg"])
    return {"result": result}


def route(state: AgentState) -> str:
    return "run_tool" if state["decision"] == "ALLOW" else END


graph = StateGraph(AgentState)
graph.add_node("gate", gate_node)
graph.add_node("run_tool", run_tool)
graph.add_edge(START, "gate")
graph.add_conditional_edges("gate", route)
graph.add_edge("run_tool", END)
app = graph.compile()


if __name__ == "__main__":
    cases = [
        {"role": "analyst", "request": "summarize this file", "tool_name": "read_file", "tool_arg": "notes.txt"},
        {"role": "analyst", "request": "delete the old file", "tool_name": "delete_file", "tool_arg": "old.txt"},
        {"role": "analyst", "request": "read this file and then delete it", "tool_name": "read_file", "tool_arg": "secret.txt"},
    ]
    for case in cases:
        state = {**case, "decision": "", "reason": "", "result": ""}
        out = app.invoke(state)
        print(out["decision"], "|", out["reason"], "|", out["result"] or "-")