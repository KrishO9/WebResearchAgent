import logging
from typing import List
# Change these imports to be relative
# from utils.llm import call_llm # OLD
# from utils.config import settings # OLD
from ..utils.llm import call_llm # NEW Relative
from ..utils.config import settings # NEW Relative

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReportAgent:
    """
    Generates the final research report by synthesizing findings from multiple sources.
    Addresses: Information Synthesis core capability.
    """

    async def write_report(self, task: str, research_results: List[str]) -> str:
        """
        Uses an LLM to synthesize research findings into a coherent report.

        Args:
            task (str): The original research task/query.
            research_results (List[str]): A list of consolidated summaries and error notes,
                                          one block for each sub-query researched.

        Returns:
            str: The final generated report.
        """
        logger.info(f"Starting report generation for task: '{task}'")
        if not research_results:
             logger.warning("No research results provided to ReportAgent.")
             return "Error: No research findings were available to generate the report."

        # Combine the results from all sub-queries
        findings_text = "\n\n---\nEnd of Findings for one Sub-Query\n---\n\n".join(research_results)

        # Enhanced system prompt for synthesis
        system_prompt = """You are an expert research analyst and writer. Your primary task is to synthesize the provided research findings (which include summaries and potential error notes from web scraping) into a single, comprehensive, well-structured, and objective report that directly addresses the original user task.

Key Instructions:
1.  **Synthesize, Don't List:** Combine information logically from the different sources and sub-queries. Do not simply list the summaries provided.
2.  **Address the Core Task:** Ensure the final report directly answers or addresses the original user task.
3.  **Structure:** Organize the report with clear headings (e.g., using Markdown like ## Heading) and paragraphs for readability. Start with a brief introduction summarizing the task and scope, followed by the main findings, and conclude with a concise summary.
4.  **Objectivity:** Maintain a neutral and informative tone. Avoid personal opinions or speculation beyond the provided findings.
5.  **Handle Contradictions/Errors:** If you encounter contradictory information between sources, acknowledge it neutrally (e.g., "Some sources suggest X, while others indicate Y."). If the findings include error notes (e.g., "Could not summarize content"), mention that information for that source was unavailable or problematic, but focus the report on the successfully retrieved information.
6.  **Source Attribution (Implicit):** The findings provided may contain source URLs. While you don't need to create a separate bibliography, ensure the synthesized text flows naturally and implicitly reflects the information gathered from those sources.
7.  **Base Only on Provided Text:** Generate the report **solely** based on the "Combined Research Findings" provided below. Do not add external knowledge."""

        prompt = f"""Original User Task: "{task}"

Combined Research Findings (Summaries and error notes from web research for multiple sub-queries):
--- START OF FINDINGS ---
{findings_text}
--- END OF FINDINGS ---

Based **only** on the provided research findings, please generate a comprehensive and well-structured research report addressing the original user task: "{task}". Follow all instructions in the system prompt."""

        try:
            # Use a powerful model for the final synthesis
            final_report = await call_llm(prompt, settings.openrouter_model_reporter, system_prompt=system_prompt, temperature=0.5) # Slightly higher temp for better writing flow
            logger.info(f"Successfully generated final report for task: '{task}'")
            return final_report
        except Exception as e:
            logger.error(f"Error generating final report for task '{task}': {e}")
            return f"Error: Failed to generate the final report due to an internal LLM error."