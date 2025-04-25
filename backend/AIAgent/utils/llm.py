# backend/AIAgent/utils/llm.py
import logging
from openai import AsyncOpenAI
# Use relative import for config within the same package
from .config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
logger = logging.getLogger(__name__)

# Check if settings loaded correctly
if settings and settings.openrouter_api_key:
    aclient = AsyncOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
    )
    logger.info("AsyncOpenAI client initialized for OpenRouter.")
else:
    aclient = None
    logger.error("OpenRouter API key not found in settings. LLM calls will fail.")


async def call_llm(prompt: str, model: str, system_prompt: str | None = None, temperature: float = 0.5) -> str:
    """
    Asynchronously calls the OpenRouter API.
    """
    if not aclient:
        raise RuntimeError("OpenAI client not initialized. Check OpenRouter API key.")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "HTTP-Referer": settings.http_referer if settings else "",
        "X-Title": settings.app_name if settings else "WebAppResearchAgent",
    }

    logger.debug(f"Calling OpenRouter model {model} with prompt: {prompt[:100]}...")
    try:
        response = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=4000,
            extra_headers=headers
        )
        content = response.choices[0].message.content
        logger.debug(f"OpenRouter model {model} response received: {content[:100]}...")
        return content if content else ""
    except Exception as e:
        logger.error(f"Error calling OpenRouter API ({model}): {e}", exc_info=True)
        raise # Re-raise for caller to handle