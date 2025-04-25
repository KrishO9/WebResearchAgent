import logging
import json
import json_repair
from typing import List
# Change this import to be relative to the agents/ directory
# from utils.llm import call_llm # OLD Absolute
from ..utils.llm import call_llm # NEW Relative (..) goes up to AIAgent/, then down to utils/
from ..utils.config import settings # NEW Relative

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PlanningAgent:
    """
    Analyzes the user query and generates relevant sub-queries for research.
    Addresses: Query Analysis core capability.
    """

    async def generate_sub_queries(self, task: str) -> List[str]:
        """
        Uses an LLM to break down the main task into specific sub-queries,
        considering query intent and information types.

        Args:
            task (str): The main research task/query.

        Returns:
            List[str]: A list of sub-queries.
        """
        logger.info(f"Analyzing task and generating sub-queries for: '{task}'")
        # Enhanced system prompt to guide query analysis
        system_prompt = f"""You are an expert research planner. Your goal is to analyze the user's research task to understand its intent and the types of information likely needed (e.g., facts, opinions, recent developments, historical context).
Based on this analysis, break down the main task into {settings.max_sub_queries} specific, answerable sub-queries. These sub-queries should collectively cover the key aspects needed to fulfill the original task and reflect diverse search strategies if necessary.
Provide the sub-queries as a JSON list of strings.
Example Task: "What are the ethical implications of large language models in education?"
Example Output:
["What are the primary bias concerns associated with LLMs used in educational settings?", "How do LLMs impact student privacy and data security in schools?", "Explore the potential effects of LLM reliance on critical thinking and writing skills.", "What accessibility benefits or drawbacks do LLMs present for students with disabilities?", "Analyze recent policies or guidelines proposed for responsible LLM use in education."]"""

        prompt = f"Main research task: \"{task}\"\n\nPlease analyze this task and generate {settings.max_sub_queries} specific sub-queries, formatted as a JSON list of strings."

        try:
            response = await call_llm(prompt, settings.openrouter_model_planner, system_prompt=system_prompt, temperature=0.4)

            try:
                sub_queries = json.loads(response)
            except json.JSONDecodeError:
                logger.warning("Planner LLM response was not valid JSON, attempting repair...")
                try:
                    sub_queries = json_repair.loads(response)
                except Exception as repair_error:
                     logger.error(f"JSON repair failed: {repair_error}. Falling back to using the original task.")
                     logger.debug(f"Original failing response: {response}")
                     return [task] # Fallback

            if isinstance(sub_queries, list) and all(isinstance(q, str) for q in sub_queries):
                # Filter out empty strings just in case
                valid_queries = [q for q in sub_queries if q.strip()]
                if not valid_queries:
                     logger.error(f"LLM generated an empty list of sub-queries. Falling back.")
                     return [task] # Fallback
                logger.info(f"Generated {len(valid_queries)} valid sub-queries for '{task}'")
                return valid_queries[:settings.max_sub_queries]
            else:
                logger.error(f"Parsed response is not a list of strings: {sub_queries}. Falling back.")
                logger.debug(f"Original response: {response}")
                return [task] # Fallback

        except Exception as e:
            logger.error(f"Error generating sub-queries for task '{task}': {e}")
            return [task] # Fallback