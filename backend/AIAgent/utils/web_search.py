# backend/AIAgent/utils/web_search.py
import logging
from tavily import TavilyClient
import asyncio
# Use relative import for config
from .config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
logger = logging.getLogger(__name__)

# Check if settings loaded correctly
if settings and settings.tavily_api_key:
    tavily = TavilyClient(api_key=settings.tavily_api_key)
    logger.info("Tavily client initialized.")
else:
    tavily = None
    logger.error("Tavily API key not found in settings. Web search will fail.")

async def search_tavily(query: str, max_results: int = 5) -> list[dict]:
    """
    Performs a web search using Tavily API.
    """
    if not tavily:
         raise RuntimeError("Tavily client not initialized. Check Tavily API key.")

    logger.info(f"Performing Tavily search for query: '{query}' (max_results={max_results})")
    try:
        response = await asyncio.to_thread(
            tavily.search,
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=False
        )
        results = response.get("results", [])
        logger.info(f"Tavily search returned {len(results)} results for '{query}'")
        return results
    except Exception as e:
        logger.error(f"Error during Tavily search for '{query}': {e}", exc_info=True)
        return [] # Return empty list on error, don't raise to allow process to continue