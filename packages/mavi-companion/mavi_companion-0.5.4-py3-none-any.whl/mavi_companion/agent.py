from typing import List
import re
import keyring

from langchain.tools import tool
from langchain.chat_models import BaseChatModel
from langchain.agents import create_agent
from langchain.messages import SystemMessage
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.document_loaders import GithubFileLoader
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents.middleware import LLMToolSelectorMiddleware


KEYRING_PREFIX = "MAVI_COMPANION_MODEL_"

@tool("github-repo-docs", description="Search GitHub for repositories and fetch code/markdown files from the top repo.")
def get_github_repo_docs(query: str) -> List[dict]:
    """Search GitHub repos via DuckDuckGo and fetch coding files from the top repository."""
    try:
        pattern = re.compile(r"https?://github\.com/([^/]+)/([^/]+)(?:/|$)")
        search = DuckDuckGoSearchResults(output_format="list", max_results=15)
        results = search.invoke(f"{query} site:github.com")

        def is_github_repo_url(url: str) -> bool:
            if "github.com" not in url:
                return False
            url = url.split('?', 1)[0].split('#', 1)[0]
            parts = url.replace("https://github.com/", "").strip("/").split("/")
            return len(parts) == 2 and all(parts)

        repo_urls = [item['link'] for item in results if is_github_repo_url(item['link'])]
        if not repo_urls:
            return [{"error": "No GitHub repositories found."}]

        url = repo_urls[0]
        match = pattern.match(url)
        if not match:
            return [{"error": "Invalid GitHub URL."}]

        owner, repo = match.group(1), match.group(2)
        loader = GithubFileLoader(
            repo=f"{owner}/{repo}",
            branch="main",
            access_token="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",
            file_filter=lambda file_path: file_path.endswith((
                ".md", ".py", ".js", ".ts", ".java", ".c", ".cpp", ".cs", ".go", ".rb",
                ".php", ".swift", ".rs", ".sh", ".html", ".css", ".json", ".yml", ".yaml"
            ))
        )
        documents = loader.load()
        output = [{"source": doc.metadata.get("source", ""), "content": doc.page_content} for doc in documents]

        print(f"Fetched {len(output)} documents from {owner}/{repo}")
        return output
    except Exception as e:
        print(f"Fetched 0 documents.")
        return "No Docs found."

def get_api_key(model: str) -> str | None:
    """Retrieve API key for cloud models from keyring."""
    if model == "gemini-2.5-flash":
        return keyring.get_password(f"{KEYRING_PREFIX}{model}", model)
    return None

def get_llm(model: str) -> BaseChatModel | None:
    """Return a LangChain-compatible chat model based on the model name."""
    if model == "qwen2::0.5b":
        llm = HuggingFacePipeline.from_model_id(
            model_id="Qwen/Qwen2-0.5B",
            task="text-generation",
            pipeline_kwargs=dict(
                max_new_tokens=512,
                do_sample=False,
                repetition_penalty=1.03,
                return_full_text=False,
            ),
        )
        return ChatHuggingFace(llm=llm)

    elif model == "gemini-2.5-flash":
        api_key = get_api_key(model)
        if not api_key:
            print("Missing API key for Gemini. Please set it using your CLI.")
            return None
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)

    else:
        print(f"Unsupported model: {model}")
        return None

def get_agent(model: str):
    """Create and return a LangChain agent with tools and system prompt."""
    chat_model = get_llm(model)
    if not chat_model:
        return None

    system_prompt = """
    You are a CLI-based coding assistant.
    Your job is to help users with programming, debugging, and explaining code clearly.
    Rules:
    - Keep responses concise (100–200 words).
    - Avoid unnecessary formatting or markdown.
    - Provide short, practical code snippets when needed.
    - Do not repeat explanations.
    - Write in a clean, readable terminal style.
    - Focus on clarity, not decoration.
    """

    agent = create_agent(
        model=chat_model,
        system_prompt=system_prompt,
        tools=[get_github_repo_docs],
        middleware=[
        LLMToolSelectorMiddleware(
            model=chat_model,
            max_tools=3,
            always_include=["github-repo-docs"]
        )]
    )
    return agent
