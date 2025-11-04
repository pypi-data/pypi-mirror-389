import keyring
from langchain.chat_models import BaseChatModel
from langchain.agents import create_agent
from langchain.messages import SystemMessage
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langchain_google_genai import ChatGoogleGenerativeAI

KEYRING_PREFIX = "MAVI_COMPANION_MODEL_"

def get_api_key(model: str) -> str | None:
    """Retrieve API key for cloud models from keyring."""
    # Only cloud models require an API key
    if model == "gemini-2.5-flash":
        return keyring.get_password(f"{KEYRING_PREFIX}{model}", model)
    return None


def get_llm(model: str) -> BaseChatModel | None:
    """Return a LangChain-compatible chat model based on model name."""
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
    
    agent = create_agent(model=chat_model, system_prompt=system_prompt)
    return agent
