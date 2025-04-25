import asyncio
import logging
import time
import re
from firecrawl import FirecrawlApp
from .llm import call_llm
from .config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Firecrawl App globally
try:
    firecrawl_app = FirecrawlApp(api_key=settings.firecrawl_api_key)
except Exception as e:
    logger.critical(f"Failed to initialize FirecrawlApp. Check API Key. Error: {e}")
    firecrawl_app = None

# Define a semaphore based on config
scrape_semaphore = asyncio.Semaphore(settings.max_scrape_concurrency)

# Rate limiter class for Firecrawl requests
class RateLimiter:
    def __init__(self, max_calls_per_minute=20):
        self.max_calls = max_calls_per_minute
        self.calls = 0
        self.reset_time = time.time() + 60
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            current_time = time.time()
            
            if current_time > self.reset_time:
                self.calls = 0
                self.reset_time = current_time + 60
            
            if self.calls >= self.max_calls:
                sleep_time = max(1, self.reset_time - current_time)
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
                self.calls = 0
                self.reset_time = time.time() + 60
            
            self.calls += 1

# Initialize rate limiter - set to be conservative to avoid rate limits
rate_limiter = RateLimiter(max_calls_per_minute=15)

async def scrape_with_firecrawl(url: str) -> str | None:
    """Scrapes the URL using Firecrawl and returns Markdown content."""
    if not firecrawl_app:
        logger.error("FirecrawlApp not initialized. Skipping scrape.")
        return None

    logger.debug(f"Attempting to scrape URL with Firecrawl: {url}")
    try:
        # Acquire rate limit before making the request
        await rate_limiter.acquire()
        
        # Using synchronous method in an async function
        # We'll run it in a thread pool to not block the event loop
        loop = asyncio.get_event_loop()
        scrape_response = await loop.run_in_executor(
            None,
            lambda: firecrawl_app.scrape_url(
                url,
                formats=["markdown"],
                only_main_content=True,
                timeout=30000
            )
        )

        # Handle ScrapeResponse object
        if hasattr(scrape_response, 'markdown') and scrape_response.markdown:
            markdown_content = scrape_response.markdown
            logger.debug(f"Firecrawl extracted ~{len(markdown_content)} chars (Markdown) from {url}")
            MAX_EXTRACT_CHARS = 30000
            return markdown_content[:MAX_EXTRACT_CHARS].strip()
        else:
            # Also check for data attribute in case the response structure is different
            if hasattr(scrape_response, 'data') and scrape_response.data:
                if isinstance(scrape_response.data, list) and len(scrape_response.data) > 0:
                    first_result = scrape_response.data[0]
                    if hasattr(first_result, 'markdown') and first_result.markdown:
                        markdown_content = first_result.markdown
                        logger.debug(f"Firecrawl extracted ~{len(markdown_content)} chars (Markdown) from {url}")
                        MAX_EXTRACT_CHARS = 30000
                        return markdown_content[:MAX_EXTRACT_CHARS].strip()
            
            logger.warning(f"Firecrawl returned no valid markdown for {url}")
            return None

    except Exception as e:
        # Check if it's a rate limit error (429)
        if any(x in str(e) for x in ["429", "Rate limit"]):
            # Extract retry time from error message if possible
            retry_seconds = 60  # Default fallback
            try:
                # Try to extract retry time from error message using regex
                msg = str(e)
                match = re.search(r"retry after (\d+)s", msg)
                if match:
                    retry_seconds = int(match.group(1)) + 5  # Add buffer
                else:
                    match = re.search(r"retry after (\d+\.\d+)s", msg)
                    if match:
                        retry_seconds = int(float(match.group(1))) + 5
            except:
                logger.debug(f"Couldn't extract retry time from: {str(e)}")
                
            logger.warning(f"Rate limit hit for {url}, backing off for {retry_seconds}s")
            await asyncio.sleep(retry_seconds)
            
            # Try once more after waiting
            try:
                logger.info(f"Retrying {url} after rate limit backoff")
                await rate_limiter.acquire()
                
                # Use the same approach for retry
                loop = asyncio.get_event_loop()
                scrape_response = await loop.run_in_executor(
                    None,
                    lambda: firecrawl_app.scrape_url(
                        url,
                        formats=["markdown"],
                        only_main_content=True,
                        timeout=30000
                    )
                )
                
                # Handle ScrapeResponse object in retry as well
                if hasattr(scrape_response, 'markdown') and scrape_response.markdown:
                    markdown_content = scrape_response.markdown
                    logger.debug(f"Retry successful! Extracted ~{len(markdown_content)} chars from {url}")
                    MAX_EXTRACT_CHARS = 30000
                    return markdown_content[:MAX_EXTRACT_CHARS].strip()
                else:
                    # Also check for data attribute in case the response structure is different
                    if hasattr(scrape_response, 'data') and scrape_response.data:
                        if isinstance(scrape_response.data, list) and len(scrape_response.data) > 0:
                            first_result = scrape_response.data[0]
                            if hasattr(first_result, 'markdown') and first_result.markdown:
                                markdown_content = first_result.markdown
                                logger.debug(f"Retry successful! Extracted ~{len(markdown_content)} chars from {url}")
                                MAX_EXTRACT_CHARS = 30000
                                return markdown_content[:MAX_EXTRACT_CHARS].strip()
                    
                    logger.warning(f"Firecrawl retry returned no valid markdown for {url}")
                    return None
            except Exception as retry_e:
                logger.error(f"Retry also failed for {url}: {retry_e}", exc_info=False)
        else:
            logger.error(f"Firecrawl scrape failed for {url}: {e}", exc_info=False)
        
        return None


async def summarize_with_llm(markdown_content: str, query: str, url: str, task: str) -> str | None:
    """Summarizes extracted Markdown content using an LLM."""
    if not markdown_content or len(markdown_content.split()) < 30:
         logger.warning(f"Skipping summarization for short/empty content from {url}")
         return f"Source: {url}\nInfo: Content was too short or empty to summarize."

    MAX_SUMMARY_WORDS = 300
    truncated_markdown = markdown_content

    system_prompt = f"""You are a highly focused research assistant. Your goal is to extract and summarize information from the provided **Markdown content** that is **directly relevant to the *original research task***. Ignore information not pertinent to the original task. The summary should be concise (around {MAX_SUMMARY_WORDS} words). Mention the source URL."""

    prompt = f"Original Research Task: {task}\nSource URL: {url}\nSub-Query Context: {query}\n\n**Markdown Content** to Summarize:\n```markdown\n{truncated_markdown}\n```\n\nBased **only** on the text above, provide a concise summary (around {MAX_SUMMARY_WORDS} words) containing information **strictly relevant to the Original Research Task: '{task}'**."

    try:
        summary = await call_llm(prompt, settings.openrouter_model_researcher, system_prompt=system_prompt, temperature=0.1)
        logger.info(f"Successfully summarized content from {url}")
        return f"Source: {url}\nSummary:\n{summary}"
    except Exception as e:
        logger.error(f"Failed to summarize content from {url}: {e}")
        return f"Source: {url}\nError: Could not summarize content due to an LLM error."


async def process_url(url: str, query: str, task: str) -> str:
    """Scrapes URL with Firecrawl, then summarizes the Markdown content."""
    async with scrape_semaphore:
        logger.info(f"Processing URL: {url} for query: '{query}' / task: '{task}'")
        markdown_content = await scrape_with_firecrawl(url)
        if markdown_content:
            summary_or_error = await summarize_with_llm(markdown_content, query, url, task)
            return summary_or_error if summary_or_error else f"Source: {url}\nError: Summarization failed unexpectedly."
        else:
            return f"Source: {url}\nError: Could not scrape or extract content using Firecrawl."


async def scrape_and_summarize_urls(urls: list[str], query: str, task: str) -> list[str]:
    """
    Uses Firecrawl to scrape and then summarizes content from URLs concurrently.

    Args:
        urls (list[str]): A list of URLs to process.
        query (str): The sub-query for context.
        task (str): The original main task for relevance filtering during summarization.

    Returns:
        list[str]: A list of summaries or error notes.
    """
    if not firecrawl_app:
        logger.critical("FirecrawlApp not initialized. Cannot scrape URLs.")
        return [f"Error: Firecrawl service not available for URLs: {urls}"]

    logger.info(f"Starting Firecrawl scraping & summarization for {len(urls)} URLs. Query: '{query}' / Task: '{task}'")
    summaries = []

    tasks = [process_url(url, query, task) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        url = urls[i]
        if isinstance(result, Exception):
            logger.error(f"Task for URL {url} failed with exception: {result}", exc_info=result)
            summaries.append(f"Source: {url}\nError: Failed to process URL due to system error: {result}")
        elif isinstance(result, str):
            summaries.append(result)
        else:
            logger.error(f"Unexpected result type for URL {url}: {type(result)}")
            summaries.append(f"Source: {url}\nError: Processing returned unexpected result type.")

    logger.info(f"Finished Firecrawl scraping/summarization. Got {len(summaries)} results/notes for query: '{query}'")
    return summaries