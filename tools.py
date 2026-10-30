def read_file(path: str) -> str:
    return f"contents of {path}"


def query_db(query: str) -> str:
    return f"results for query: {query}"


def send_email(to: str, body: str) -> str:
    return f"email sent to {to}"


def delete_file(path: str) -> str:
    return f"deleted {path}"