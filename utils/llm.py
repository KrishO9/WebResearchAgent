import logging
from openai import AsyncOpenAI # Still use the openai library, but configured for OpenRouter
from .config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure the AsyncOpenAI client to use OpenRouter
aclient = AsyncOpenAI(
    base_url=settings.openrouter_base_url,
    api_key=settings.openrouter_api_key,
)

async def call_llm(prompt: str, model: str, system_prompt: str | None = None, temperature: float = 0.5) -> str:
    """
    Asynchronously calls the OpenRouter API (mimicking OpenAI structure).

    Args:
        prompt (str): The user prompt.
        model (str): The OpenRouter model identifier (e.g., "openai/gpt-4o").
        system_prompt (str, optional): An optional system message. Defaults to None.
        temperature (float): Sampling temperature. Defaults to 0.5.

    Returns:
        str: The content of the LLM's response.

    Raises:
        Exception: If the API call fails.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    # Prepare OpenRouter specific headers
    headers = {
        "HTTP-Referer": settings.http_referer,
        "X-Title": settings.app_name,
    }

    logger.debug(f"Calling OpenRouter model {model} with prompt: {prompt[:100]}...")
    try:
        response = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=4000, # Adjust based on model/needs
            extra_headers=headers # Pass the required headers
        )
        content = response.choices[0].message.content
        logger.debug(f"OpenRouter model {model} response received: {content[:100]}...")
        return content if content else ""
    except Exception as e:
        logger.error(f"Error calling OpenRouter API ({model}): {e}", exc_info=True)
        raise