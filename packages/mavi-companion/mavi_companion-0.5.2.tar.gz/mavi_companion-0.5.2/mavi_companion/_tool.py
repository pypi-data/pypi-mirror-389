# Imports
import keyring
from pydantic import BaseModel, ValidationError
from langchain_core.prompts import PromptTemplate
from langchain.agents import create_agent
from langchain_core.runnables import Runnable
from langchain.agents.structured_output import ToolStrategy
from langchain.tools import tool
from langchain_core.runnables import Runnable

# TODO: function to get agent for reasoning and responses.
def get_llm(model:str) -> Runnable | None:
    pass

# TODO: structured output parsing for documentation and github search query.
class LookupOutput(BaseModel):
    documentation_query: str
    github_query: str

combined_lookup_prompt_template = '''
You are an expert programmer and open-source researcher.

Your task:
1. Find the most relevant, authoritative documentation URLs or pages that will help solve the coding problem.
2. Find relevant, high-quality GitHub repos or code examples for the coding problem.

Coding Problem: {question}

Respond ONLY with a JSON object like this:

{{
  "documentation_query": "a concise search query or URLs for documentation",
  "github_query": "a concise search query or URLs for GitHub repos"
}}
'''
lookup_prompt = PromptTemplate(
    input_variables=["question"],
    template=combined_lookup_prompt_template,
)

def get_tavily_api_key() -> str | None:
    tool_name = "tavily"
    key_name = f"MAVI_COMPANION_TOOL_{tool_name}"
    return keyring.get_password(key_name, tool_name)


# @tool("documentation_search")
def search_documentation(search_query: str) -> str:
    tavily_api_key = get_tavily_api_key()
    if not tavily_api_key:
        return "Error: Tavily API key not found."

    query = (
        f"{search_query} (tutorial OR example OR \"how to\" OR \"usage\" OR guide) "
        f"Extract code examples and usage explanations. Exclude marketing, pricing, and FAQ pages."
    )

    tavily_search = TavilySearch(max_results=5, topic="general", tavily_api_key=tavily_api_key)
    tavily_crawl = TavilyCrawl(
        max_depth=1,
        limit=5,
        instructions="Extract code examples and usage explanations. Exclude marketing, pricing, and FAQ pages.",
        tavily_api_key=tavily_api_key
    )

    search_results = tavily_search.invoke({"query": query, "max_results": 5}, output_format="list")
    results_list = search_results.get("results", [])
    if not results_list:
        return "No relevant tutorial or example documentation URLs found."

    filtered_results = [r for r in results_list if all(
        kw not in r.get("url", "").lower() for kw in ["pricing", "plan", "buy"]
    )]

    if not filtered_results:
        return "No suitable tutorial or example documentation URLs found after filtering."

    first_url = filtered_results[0].get("url")
    if not first_url:
        return "No valid documentation URL found."

    crawl_results = tavily_crawl.invoke({"url": first_url, "max_depth": 1, "limit": 5}, output_format="str")
    print(crawl_results)
    # crawl_content_list = crawl_results.get("results", [])
    # if not crawl_content_list:
    #     return f"Could not extract content from {first_url}"

    # raw_content = crawl_content_list[0].get("raw_content")
    # if not raw_content:
    #     return crawl_content_list[0].get("summary", "No content found.")

    return crawl_results

# @tool("github_search")
def search_github(search_query: str) -> str:
    tavily_api_key = get_tavily_api_key()
    if not tavily_api_key:
        return "Error: Tavily API key not found."

    query = (
        f"{search_query} (example OR tutorial OR usage OR \"getting started\") "
        f"site:github.com stars:>100 pushed:>2024-01-01"
    )

    tavily_search = TavilySearch(max_results=10, topic="general", tavily_api_key=tavily_api_key)
    tavily_crawl = TavilyCrawl(
        max_depth=1,
        limit=5,
        instructions="Extract README or relevant code and usage examples from the repository. Focus on well-documented repos with clear usage instructions.",
        tavily_api_key=tavily_api_key
    )

    search_results = tavily_search.invoke({"query": query, "max_results": 10}, output_format="list")
    results_list = search_results.get("results", [])
    if not results_list:
        return "No GitHub repositories found."

    github_urls = [r.get("url") for r in results_list if r.get("url") and 'github.com' in r.get("url").lower()]
    if not github_urls:
        return "No valid GitHub repository URLs found."

    first_url = github_urls[0]

    crawl_results = tavily_crawl.invoke({"url": first_url, "max_depth": 1, "limit": 5}, output_format="str")
    crawl_content_list = crawl_results.get("results", [])
    if not crawl_content_list:
        return f"Could not extract content from {first_url}"

    raw_content = crawl_content_list[0].get("raw_content")
    if not raw_content:
        return crawl_content_list[0].get("summary", "No content found.")

    return raw_content

# Example: Can be plugged into LangChain agent or call standalone for testing
if __name__ == "__main__":
    doc_query = "python langchain agents"
    github_query = "langchain python implementation"

    print("Documentation Search Result:\n", search_documentation(doc_query))
    # print("\nGitHub Search Result:\n", search_github(github_query))
