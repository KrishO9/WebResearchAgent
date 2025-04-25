# backend/AIAgent/utils/config.py
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import logging

# Configure logging early if needed by settings loading itself
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
logger = logging.getLogger(__name__)


# Determine the root directory of the project (web-research-agent-app)
# Assumes this config.py is at backend/AIAgent/utils/config.py
UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
AIAGENT_DIR = os.path.dirname(UTILS_DIR)
BACKEND_DIR = os.path.dirname(AIAGENT_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

# Load .env file from the project root
dotenv_path = os.path.join(PROJECT_ROOT, '.env')
logger.info(f"Attempting to load .env file from: {dotenv_path}")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logger.info(".env file loaded successfully.")
else:
    logger.warning(f".env file not found at {dotenv_path}. Relying on environment variables.")


class Settings(BaseSettings):
    """Loads configuration settings from environment variables for OpenRouter."""
    openrouter_api_key: str = ""
    tavily_api_key: str = ""
    firecrawl_api_key: str = ""

    http_referer: str = os.getenv("YOUR_SITE_URL", "")
    app_name: str = os.getenv("YOUR_APP_NAME", "WebResearchAgent")

    openrouter_model_planner: str = os.getenv("OPENROUTER_MODEL_PLANNER", "openai/gpt-4o")
    openrouter_model_researcher: str = os.getenv("OPENROUTER_MODEL_RESEARCHER", "openai/gpt-3.5-turbo")
    openrouter_model_reporter: str = os.getenv("OPENROUTER_MODEL_REPORTER", "openai/gpt-4o")

    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    max_sub_queries: int = int(os.getenv("MAX_SUB_QUERIES", 5))
    max_search_results_per_query: int = int(os.getenv("MAX_SEARCH_RESULTS_PER_QUERY", 5))
    max_scrape_concurrency: int = int(os.getenv("MAX_SCRAPE_CONCURRENCY", 2)) # Keep low initially

    class Config:
        # No need for env_file here if loading manually above
        extra = 'ignore'

    def __init__(self, **values):
        super().__init__(**values)
        # Re-check after loading from environment potentially overridden by Pydantic's own loading
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", self.openrouter_api_key)
        self.tavily_api_key = os.getenv("TAVILY_API_KEY", self.tavily_api_key)
        self.firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY", self.firecrawl_api_key)

        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set or loaded.")
        if not self.tavily_api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set or loaded.")
        if not self.firecrawl_api_key:
            raise ValueError("FIRECRAWL_API_KEY environment variable not set or loaded.")
        if not self.http_referer:
            logger.warning("Warning: YOUR_SITE_URL environment variable not set. OpenRouter requests might be less identifiable.")


try:
    settings = Settings()
    logger.info("Configuration settings loaded successfully.")
except ValueError as e:
     logger.critical(f"Configuration Error: {e}")
     # Depending on the setup, you might want to exit here if config fails critically
     # sys.exit(1)
     settings = None # Indicate failure


# Example usage (optional, for testing within this module)
if __name__ == "__main__":
    if settings:
        print("Settings loaded for OpenRouter:")
        print(f"Planner Model: {settings.openrouter_model_planner}")
        print(f"HTTP Referer: {settings.http_referer}")
        print(f"Firecrawl Key Loaded: {'Yes' if settings.firecrawl_api_key else 'No'}")
    else:
        print("Settings failed to load.")