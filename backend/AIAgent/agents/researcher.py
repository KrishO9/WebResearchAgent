import logging
from typing import List, Dict
# Change these imports to be relative
# from utils.web_search import search_tavily # OLD
# from utils.web_scraper import scrape_and_summarize_urls # OLD
# from utils.config import settings # OLD
from ..utils.web_search import search_tavily # NEW Relative
from ..utils.web_scraper import scrape_and_summarize_urls # NEW Relative
from ..utils.config import settings # NEW Relative

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResearchAgent:
    """Conducts research for a specific sub-query using web search and Firecrawl scraping."""

    # Modify method signature to accept the original task
    async def research_sub_query(self, sub_query: str, task: str) -> str:
        """
        Performs web search, scrapes URLs using Firecrawl, and summarizes content.

        Args:
            sub_query (str): The specific sub-query to research.
            task (str): The original main research task for context/relevance.

        Returns:
            str: A consolidated string of summaries and error notes for the sub-query.
        """
        logger.info(f"Starting research for sub-query: '{sub_query}' (Original Task: '{task}')")

        # 1. Web Search
        search_term = sub_query # Using sub-query directly is often fine with Tavily
        # Optional: Augment search_term with task constraints if needed here
        search_results = await search_tavily(search_term, max_results=settings.max_search_results_per_query)
        urls = [result['url'] for result in search_results if 'url' in result]

        if not urls:
            logger.warning(f"No URLs found via Tavily for sub-query: '{sub_query}'")
            return f"Query: '{sub_query}'\nError: No relevant web search results found."

        logger.info(f"Found {len(urls)} URLs for sub-query: '{sub_query}'. Attempting scrape with Firecrawl.")

        # 2. Content Extraction & Summarization using Firecrawl
        # Pass the original 'task' for better summarization relevance
        summaries_or_errors = await scrape_and_summarize_urls(urls, sub_query, task)

        # 3. Consolidate Results
        if not summaries_or_errors:
            logger.warning(f"No summaries or error notes generated for sub-query: '{sub_query}'")
            return f"Query: '{sub_query}'\nError: Failed to retrieve or process content from search results using Firecrawl."

        consolidated_results = f"Research Findings for Query: \"{sub_query}\"\n" + "="*20 + "\n\n" + "\n\n".join(summaries_or_errors)
        logger.info(f"Finished research stage for sub-query: '{sub_query}'")
        return consolidated_results