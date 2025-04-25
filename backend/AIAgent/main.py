# backend/AIAgent/main.py

# --- Add sys.path modification at the VERY TOP ---
import sys
import os
# Get the absolute path of the current file (AIAgent/main.py)
current_file_dir = os.path.dirname(os.path.abspath(__file__))
# Get the absolute path of the parent directory (backend/)
backend_dir = os.path.dirname(current_file_dir)
# Add the 'backend' directory to sys.path
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
# --- End Path Modification ---

import asyncio
import logging
import time
import argparse
from typing import Callable, Coroutine # For type hinting the callback

# --- Import Agent Components using Relative Paths ---
from .agents.planner import PlanningAgent
from .agents.researcher import ResearchAgent
from .agents.reporter import ReportAgent
from .utils.config import settings # Assuming settings is initialized correctly in config.py

# --- DEFINE MESSAGE TYPE CONSTANTS ---
# These should match the types expected by the frontend via agent_runner.py
MSG_TYPE_LOG = "log"
MSG_TYPE_STATUS = "status"
MSG_TYPE_REPORT_CHUNK = "report_chunk" # If implementing streaming
MSG_TYPE_FINAL_REPORT = "final_report" # Sending full report at once
MSG_TYPE_SOURCES = "sources"
MSG_TYPE_ERROR = "error"
# --- END CONSTANTS ---


# Configure logging for this specific module
logger = logging.getLogger(__name__)
# Set default logging level if no handlers are configured elsewhere (e.g., by Uvicorn)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')


# --- DEFINE THE IMPORTABLE FUNCTION ---
async def run_research(task: str, send_update_callback: Callable[[str, str, dict], Coroutine] | None = None):
    """
    Core logic to run the research process for a given task and send updates via callback.

    Args:
        task (str): The research query.
        send_update_callback (callable, optional): An async function to send updates.
                                                   Expected signature: async def callback(level: str, msg_type: str, data: dict)
    Returns:
        str: The final generated research report or an error message.
    """
    start_time = time.time()
    final_report = "Error: Research process did not complete successfully." # Default error report

    # --- Internal Helper for Sending Updates ---
    async def _send_update(level: str, msg_type: str, data: dict):
        """Safely sends updates using the provided callback or logs fallback."""
        if send_update_callback:
            try:
                # Ensure data is a dict for consistency
                if not isinstance(data, dict):
                    log_msg = f"Callback received non-dict data for type {msg_type}: {data}. Wrapping."
                    logger.warning(log_msg)
                    # Also send this warning as a log via callback if possible
                    await send_update_callback("warning", MSG_TYPE_LOG, {"message": log_msg})
                    data = {"content": str(data)} # Wrap non-dict data

                # Add log level info if it's a log message
                if msg_type == MSG_TYPE_LOG:
                     data['level'] = level # Frontend might use this for styling

                # Send the actual message
                await send_update_callback(level, msg_type, data)

            except Exception as cb_err:
                logger.error(f"Error executing send_update_callback for type {msg_type}: {cb_err}", exc_info=True)
                # Don't crash the whole process if callback fails, just log it.
        else:
            # Fallback logging if no callback is provided (e.g., direct run)
            logger.log(logging.getLevelName(level.upper()), f"[{msg_type}] {data}")
    # --- End Helper Function ---

    try:
        # Ensure settings were loaded correctly
        if not settings:
             critical_error_msg = "Configuration settings failed to load. Cannot proceed."
             logger.critical(critical_error_msg)
             await _send_update("critical", MSG_TYPE_ERROR, {"message": critical_error_msg})
             await _send_update("critical", MSG_TYPE_STATUS, {"status": "error", "message": "Configuration Error"})
             return critical_error_msg # Return error immediately

        # --- Start Research Process ---
        await _send_update("info", MSG_TYPE_STATUS, {"status": "starting", "message": f"Initializing research for task: '{task}'..."})
        logger.info(f"--- Starting Research Task ---")
        logger.info(f"Task: '{task}'")
        logger.info(f"Using Models (OpenRouter): Planner={settings.openrouter_model_planner}, Researcher={settings.openrouter_model_researcher}, Reporter={settings.openrouter_model_reporter}")
        logger.info(f"Using Search: Tavily")
        logger.info(f"Using Scraper: Firecrawl")

        # 1. Initialize Agents
        planner = PlanningAgent()
        researcher = ResearchAgent()
        reporter = ReportAgent()

        # 2. Planning Stage
        await _send_update("info", MSG_TYPE_STATUS, {"status": "planning", "message": "Generating sub-queries..."})
        logger.info(">>> Stage 1: Planning Research (Query Analysis) <<<")
        sub_queries = await planner.generate_sub_queries(task)

        if not sub_queries or (len(sub_queries) == 1 and sub_queries[0] == task) :
             warning_msg = f"Planning might have defaulted or failed. Using queries: {sub_queries}"
             logger.warning(warning_msg)
             await _send_update("warning", MSG_TYPE_LOG, {"message": warning_msg})
             if not sub_queries:
                 raise ValueError("Planning failed: No sub-queries generated.") # Raise to trigger except block

        logger.info(f"Planned {len(sub_queries)} sub-queries: {sub_queries}")
        await _send_update("info", MSG_TYPE_LOG, {"message": f"Planned Sub-queries: {sub_queries}"})


        # 3. Research Stage
        await _send_update("info", MSG_TYPE_STATUS, {"status": "researching", "message": f"Researching {len(sub_queries)} sub-queries..."})
        logger.info(">>> Stage 2: Conducting Research via Web Search & Firecrawl Content Extraction <<<")
        # Pass the original 'task' to research_sub_query for context
        research_tasks = [researcher.research_sub_query(sq, task) for sq in sub_queries]
        # Gather results, including exceptions
        research_results_with_errors = await asyncio.gather(*research_tasks, return_exceptions=True)

        successful_findings = []
        error_count = 0
        source_urls = set()

        for i, result in enumerate(research_results_with_errors):
            query = sub_queries[i]
            await _send_update("info", MSG_TYPE_LOG, {"message": f"Processing result for query: '{query}'"})
            if isinstance(result, Exception):
                error_note = f"Query: '{query}'\nError: Research task failed - {type(result).__name__}: {result}"
                logger.error(f"Research task for sub-query '{query}' failed with exception: {result}", exc_info=result)
                successful_findings.append(error_note)
                await _send_update("error", MSG_TYPE_LOG, {"message": error_note})
                error_count += 1
            elif isinstance(result, str):
                successful_findings.append(result)
                # Basic source URL extraction (assuming "Source: URL\n...") format from scraper
                try:
                    lines = result.split('\n')
                    if lines and lines[0].startswith("Source: http"):
                         source_urls.add(lines[0].replace("Source: ", "").strip())
                except Exception as parse_err:
                     logger.warning(f"Could not parse source URL from finding for '{query}': {parse_err}")
            else:
                error_note = f"Query: '{query}'\nError: Unexpected result type ({type(result)}) during research."
                logger.error(error_note)
                successful_findings.append(error_note)
                await _send_update("error", MSG_TYPE_LOG, {"message": error_note})
                error_count += 1

        # Send accumulated source URLs update
        if source_urls:
             await _send_update("info", MSG_TYPE_SOURCES, {"urls": sorted(list(source_urls))})


        # Check if research stage failed critically
        if not successful_findings or error_count == len(sub_queries):
            error_msg = f"Research stage failed: {error_count}/{len(sub_queries)} tasks resulted in errors."
            logger.error(error_msg)
            raise ValueError(error_msg) # Raise to trigger except block

        logger.info(f"Gathered {len(successful_findings)} findings/notes from research stage ({error_count} errors).")


        # 4. Reporting Stage
        await _send_update("info", MSG_TYPE_STATUS, {"status": "reporting", "message": "Synthesizing final report..."})
        logger.info(">>> Stage 3: Generating Final Report (Information Synthesis) <<<")
        final_report = await reporter.write_report(task, successful_findings)
        # Send the final report content
        await _send_update("info", MSG_TYPE_FINAL_REPORT, {"report": final_report})


        # --- Research Successfully Completed ---
        end_time = time.time()
        elapsed_time = end_time - start_time
        completion_msg = f"Research complete ({elapsed_time:.2f}s)."
        logger.info(f"--- Research Task Completed ---")
        logger.info(f"Total Time Elapsed: {elapsed_time:.2f} seconds")
        await _send_update("info", MSG_TYPE_STATUS, {"status": "done", "message": completion_msg })


    except Exception as e:
        # Catch errors from any stage above
        critical_error_msg = f"Research failed critically: {type(e).__name__} - {e}"
        logger.critical(critical_error_msg, exc_info=True)
        try: # Try to notify client
             await _send_update("error", MSG_TYPE_ERROR, {"message": critical_error_msg})
             await _send_update("error", MSG_TYPE_STATUS, {"status": "error", "message": "Research process failed."})
        except Exception as cb_err:
             logger.error(f"Failed to send critical error via callback: {cb_err}")
        final_report = f"FATAL ERROR: Research failed.\nDetails: {critical_error_msg}" # Update report on critical failure

    return final_report # Return the final report string or error message


# --- Keep this block for direct execution/testing ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the multi-agent web researcher (Direct Execution Test).")
    parser.add_argument("task", type=str, help="The research task or query to perform.")
    args = parser.parse_args()

    # Basic check for API keys before starting asyncio loop
    if not settings or not settings.openrouter_api_key or not settings.tavily_api_key or not settings.firecrawl_api_key:
         print("ERROR: Configuration or API keys (OPENROUTER_API_KEY, TAVILY_API_KEY, FIRECRAWL_API_KEY) not found or loaded correctly.")
         print("Please check .env file in project root and utils/config.py.")
         exit(1)

    async def direct_main():
        print("--- Running Research Agent Directly (No WebSocket Updates) ---")
        report = await run_research(args.task, send_update_callback=None) # Pass None for callback
        print("\n" + "="*70)
        print(" F I N A L   R E S E A R C H   R E P O R T (Direct Run)")
        print("="*70 + "\n")
        print(f"Original Task: {args.task}\n")
        print("-"*70 + "\n")
        print(report)
        print("\n" + "="*70)

    try:
        asyncio.run(direct_main())
    except KeyboardInterrupt:
        print("\nResearch process interrupted by user.")
        logger.info("Research process interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred during direct execution: {e}")
        logger.error(f"Error during direct execution: {e}", exc_info=True)