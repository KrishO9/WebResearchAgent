import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Loads configuration settings from environment variables for OpenRouter."""
    openrouter_api_key: str = ""
    tavily_api_key: str = ""
    firecrawl_api_key: str = ""

    # Optional OpenRouter identification headers
    http_referer: str = os.getenv("YOUR_SITE_URL", "") # Header: HTTP-Referer
    app_name: str = os.getenv("YOUR_APP_NAME", "WebResearchAgent") # Header: X-Title

    # LLM Model Identifiers for OpenRouter
    openrouter_model_planner: str = os.getenv("OPENROUTER_MODEL_PLANNER", "openai/gpt-4o")
    openrouter_model_researcher: str = os.getenv("OPENROUTER_MODEL_RESEARCHER", "openai/gpt-3.5-turbo")
    openrouter_model_reporter: str = os.getenv("OPENROUTER_MODEL_REPORTER", "openai/gpt-4o")

    # Base URL for OpenRouter API
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Research process settings
    max_sub_queries: int = int(os.getenv("MAX_SUB_QUERIES", 5))
    max_search_results_per_query: int = int(os.getenv("MAX_SEARCH_RESULTS_PER_QUERY", 5))
    max_scrape_concurrency: int = int(os.getenv("MAX_SCRAPE_CONCURRENCY", 5))

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'

    # Pydantic automatically loads from environment variables now,
    # but we add explicit validation for required keys.
    def __init__(self, **values):
        super().__init__(**values)
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set.")
        if not self.tavily_api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set.")
        if not self.http_referer:
            print("Warning: YOUR_SITE_URL environment variable not set. OpenRouter requests might be less identifiable.")
        if not self.firecrawl_api_key: # <-- ADD THIS VALIDATION
            raise ValueError("FIRECRAWL_API_KEY environment variable not set.")


# Create a single instance to be imported
settings = Settings()

# Example usage (optional, for testing):
if __name__ == "__main__":
    print("Settings loaded for OpenRouter:")
    print(f"Planner Model: {settings.openrouter_model_planner}")
    print(f"Researcher Model: {settings.openrouter_model_researcher}")
    print(f"Reporter Model: {settings.openrouter_model_reporter}")
    print(f"Max Sub-Queries: {settings.max_sub_queries}")
    print(f"Max Search Results: {settings.max_search_results_per_query}")
    print(f"Max Scrape Concurrency: {settings.max_scrape_concurrency}")
    print(f"HTTP Referer: {settings.http_referer}")
    print(f"App Name (X-Title): {settings.app_name}")
    print(f"Firecrawl Key Loaded: {'Yes' if settings.firecrawl_api_key else 'No'}")
    # print(f"OpenRouter Key Loaded: {'Yes' if settings.openrouter_api_key else 'No'}")
    # print(f"Tavily Key Loaded: {'Yes' if settings.tavily_api_key else 'No'}")