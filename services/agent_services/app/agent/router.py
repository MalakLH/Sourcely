from app.tools.base import ToolName


# Initially, use a deterministic router to test whether the architecture works.

def route_request(query: str) -> ToolName:

    query_lower = query.lower()

    sandbox_keywords = [
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