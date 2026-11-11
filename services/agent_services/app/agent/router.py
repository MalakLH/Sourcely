from app.tools.base import ToolName


def route_request(
    query: str,
    has_code: bool = False,
) -> ToolName:

    # Explicit code takes priority: it needs the sandbox.
    if has_code:
        return ToolName.SANDBOX

    query_lower = query.lower()

    sandbox_keywords = [
        "run this code",
        "run code",
        "execute code",
        "test this code",
        "scan this code",
        "vulnerability",
        "security scan",
    ]

    web_keywords = [
        "find tutorials",
        "search the web",
        "github repository",
        "github repo",
        "latest articles",
        "online resources",
    ]

    if any(keyword in query_lower for keyword in sandbox_keywords):
        return ToolName.SANDBOX

    if any(keyword in query_lower for keyword in web_keywords):
        return ToolName.WEB

    return ToolName.DOCS
