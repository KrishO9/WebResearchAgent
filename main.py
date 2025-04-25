import asyncio
import logging
import time
import argparse

from agents.planner import PlanningAgent        # Changed from relative to absolute import
from agents.researcher import ResearchAgent     # Changed from relative to absolute import
from agents.reporter import ReportAgent         # Changed from relative to absolute import
from utils.config import settings           # Changed from relative to absolute import

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
logger = logging.getLogger(__name__) # Use __name__ for logger name

async def run_research(task: str):
    """
    Orchestrates the multi-agent research process using OpenRouter and Tavily.
    """
    start_time = time.time()
    logger.info(f"--- Starting Research Task ---")
    logger.info(f"Task: '{task}'")
    logger.info(f"Using Models (OpenRouter): Planner={settings.openrouter_model_planner}, Researcher={settings.openrouter_model_researcher}, Reporter={settings.openrouter_model_reporter}")
    logger.info(f"Using Search: Tavily")
    logger.info(f"Using Scraper: Firecrawl") # Added scraper info

    # 1. Initialize Agents
    planner = PlanningAgent()
    researcher = ResearchAgent()
    reporter = ReportAgent()

    try:
        # 2. Planning Stage: Generate Sub-Queries (Query Analysis)
        logger.info(">>> Stage 1: Planning Research (Query Analysis) <<<")
        sub_queries = await planner.generate_sub_queries(task)
        if not sub_queries or (len(sub_queries) == 1 and sub_queries[0] == task) : # Check if fallback occurred
             logger.warning(f"Planning might have defaulted to the original task or failed. Proceeding with: {sub_queries}")
             if not sub_queries: # Handle empty list case
                 print("\nERROR: Failed to generate a research plan. Aborting.")
                 return
        logger.info(f"Planned {len(sub_queries)} sub-queries: {sub_queries}")

        # 3. Research Stage: Execute Sub-Queries Concurrently (Web Search, Content Extraction)
        logger.info(">>> Stage 2: Conducting Research via Web Search & Content Extraction <<<")
        research_tasks = [researcher.research_sub_query(sq, task) for sq in sub_queries]
        # gather will run the research_sub_query tasks concurrently
        research_results_with_errors = await asyncio.gather(*research_tasks, return_exceptions=True)

        # Process results, separating successful findings from errors
        successful_findings = []
        error_count = 0
        for i, result in enumerate(research_results_with_errors):
            query = sub_queries[i]
            if isinstance(result, Exception):
                logger.error(f"Research task for sub-query '{query}' failed with exception: {result}", exc_info=result)
                # Optionally include a note about the failure in findings passed to reporter
                successful_findings.append(f"Query: '{query}'\nError: Research failed due to system error: {result}")
                error_count += 1
            elif isinstance(result, str):
                successful_findings.append(result) # This string might contain error notes from scraping stage
            else:
                logger.error(f"Unexpected result type for sub-query '{query}': {type(result)}")
                successful_findings.append(f"Query: '{query}'\nError: Unexpected result type during research.")
                error_count += 1


        if not successful_findings: # Check if we have anything to report
            logger.error("Research stage failed: No successful results or error notes gathered.")
            print("\nERROR: Failed to gather any information during research. Aborting.")
            return
        elif error_count == len(sub_queries):
             logger.error("Research stage failed: All sub-query tasks resulted in errors.")
             print("\nERROR: All research attempts failed. Aborting.")
             return


        logger.info(f"Gathered {len(successful_findings)} findings/notes from research stage ({error_count} errors).")

        # 4. Reporting Stage: Synthesize Findings (Information Synthesis)
        logger.info(">>> Stage 3: Generating Final Report (Information Synthesis) <<<")
        final_report = await reporter.write_report(task, successful_findings)

        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"--- Research Task Completed ---")
        logger.info(f"Total Time Elapsed: {elapsed_time:.2f} seconds")

        # 5. Output Final Report
        print("\n" + "="*70)
        print(" F I N A L   R E S E A R C H   R E P O R T")
        print("="*70 + "\n")
        print(f"Original Task: {task}\n")
        print("-"*70 + "\n")
        print(final_report)
        print("\n" + "="*70)

    except Exception as e:
        logger.critical(f"An critical error occurred in the main research loop: {e}", exc_info=True)
        print(f"\nFATAL ERROR: The research process failed unexpectedly. Check logs for details. Error: {e}")


if __name__ == "__main__":
    # Add the sys.path modification back if running directly
    import sys
    import os
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    parser = argparse.ArgumentParser(description="Run the multi-agent web researcher using OpenRouter, Tavily, and Firecrawl.")
    parser.add_argument("task", type=str, help="The research task or query to perform.")
    args = parser.parse_args()

    # Check for all required API keys
    if not settings.openrouter_api_key or not settings.tavily_api_key or not settings.firecrawl_api_key:
         print("ERROR: API keys (OPENROUTER_API_KEY, TAVILY_API_KEY, FIRECRAWL_API_KEY) not found.")
         print("Please create a .env file in the root directory or set the environment variables.")
         exit(1)

    try:
        asyncio.run(run_research(args.task))
    except KeyboardInterrupt:
        print("\nResearch process interrupted by user.")
        logger.info("Research process interrupted by user.")