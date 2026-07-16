from abc import ABC, abstractmethod
from config import settings


class SearchResult:
    def __init__(self, title: str, url: str, content: str):
        self.title = title
        self.url = url
        self.content = content

    def to_dict(self):
        return {"title": self.title, "url": self.url, "content": self.content}


class SearchProvider(ABC):
    @abstractmethod
    def search(self, term: str, max_results: int = 5) -> list[SearchResult]:
        ...


class TavilyProvider(SearchProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, term: str, max_results: int = 5) -> list[SearchResult]:
        from tavily import TavilyClient

        client = TavilyClient(api_key=self.api_key)
        response = client.search(
            query=f"{term} 定义 解释 是什么",
            max_results=max_results,
            search_depth="basic",
        )

        results = []
        for item in response.get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                )
            )
        return results


def search_term(term: str, max_results: int = 5) -> list[SearchResult]:
    api_key = settings.TAVILY_API_KEY
    if not api_key:
        raise ValueError("请在 .env 中设置 TAVILY_API_KEY")
    return TavilyProvider(api_key).search(term, max_results)
