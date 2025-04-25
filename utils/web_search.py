import logging
from tavily import TavilyClient
from .config import settings
import asyncio # Import asyncio if using asyncio.to_thread

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

tavily = TavilyClient(api_key=settings.tavily_api_key)

async def search_tavily(query: str, max_results: int = 5) -> list[dict]:
    """
    Performs a web search using Tavily API. Handles filtering and ranking implicitly via Tavily.

    Args:
        query (str): The search query. Handles different types (factual, exploratory, news).
        max_results (int): The maximum number of results to return.

    Returns:
        list[dict]: A list of search result dictionaries ('url', 'content', 'score', etc.).
                    Returns empty list on error.
    """
    logger.info(f"Performing Tavily search for query: '{query}' (max_results={max_results})")
    try:
        # Using asyncio.to_thread to run the synchronous Tavily client in an async context
        response = await asyncio.to_thread(
            tavily.search,
            query=query,
            search_depth="basic", # Tavily handles depth/page navigation implicitly
            max_results=max_results,
            include_answer=False # We typically want sources, not a direct answer here
        )
        # Tavily results are generally relevance-ranked
        results = response.get("results", [])
        logger.info(f"Tavily search returned {len(results)} results for '{query}'")
        return results
    except Exception as e:
        logger.error(f"Error during Tavily search for '{query}': {e}", exc_info=True)
        return []