from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SearchResult(BaseModel):
    """Normalized web search result returned by a search provider."""

    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1)
    url: HttpUrl
    snippet: str = ""
    source: str
    score: float | None = None
    published_date: datetime | None = None