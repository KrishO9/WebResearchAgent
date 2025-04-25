Original Task: Recent terrorist attacks in India

----------------------------------------------------------------------

# Report on Recent Terrorist Attacks in India (2021-2023)

## Introduction
This report synthesizes available data on terrorist incidents in India from 2021 to 2023, focusing on attack patterns, affected regions, responsible groups, and government responses. Due to technical limitations in accessing several cited sources, the analysis relies on contextual clues from URLs and partial metadata. Notably, some referenced incidents (e.g., the 2025 Pahalgam attack) fall outside the specified timeframe but are included to reflect available information trends.

---

## Key Findings

### 1. **Geographic Hotspots**
The **Jammu and Kashmir region** remains the primary focus of terrorist activity, with multiple sources referencing attacks in Pahalgam (April 2025) and heightened alerts in Srinagar. Other regions under increased vigilance include:
- **Himachal Pradesh** (post-bomb threat alerts)
- Major cities like **Delhi, Mumbai, Jaipur, and Amritsar**, which were placed on high alert following the 2025 Kashmir attack.

### 2. **Responsible Groups**
- **The Resistance Front (TRF)**, described as an offshoot of the Pakistan-based **Lashkar-e-Taiba (LeT)**, claimed responsibility for the 2025 Pahalgam attack targeting tourists.
- TRF is characterized in source metadata as a "proxy terror group" with ties to cross-border networks.

### 3. **Government Responses**
Following the 2025 Pahalgam attack, India reportedly:
- Imposed **diplomatic pressure on Pakistan**, including threats to revise the Indus Water Treaty.
- Enhanced **counter-terrorism coordination** through high-level security meetings (e.g., CCS meetings).
- Deployed heightened security measures in urban centers and tourist areas.

### 4. **Tactical Shifts**
While detailed trend analyses (2020–2023) were inaccessible, the 2025 Pahalgam incident suggests:
- **Civilian targeting**, particularly tourists, to destabilize local economies and attract international attention.
- Use of **proxy groups** like TRF to obscure direct involvement of established organizations.

---

## Limitations
- **Data gaps**: Critical sources from government reports (e.g., U.S. State Department, SATP) and media outlets could not be accessed.     
- **Temporal inconsistencies**: Some cited incidents (e.g., 2025 attacks) exceed the requested 2021–2023 scope but reflect the most frequently referenced events in available data.

---

## Conclusion
Recent terrorist activity in India remains concentrated in Jammu and Kashmir, with emerging threats to economic hubs and civilian targets. The involvement of proxy groups like TRF highlights evolving tactics to circumvent international scrutiny. While the Indian government has responded with diplomatic and security measures, comprehensive assessments are hindered by incomplete data access. Further monitoring of Kashmir and urban centers is critical to understanding ongoing risks.

======================================================================




**Explanation of Diagram:**

*   -queries (or the single original query). It creates parallel tasks, one for each query, using `asyncio.gather`**User Interface:** Starts with the user query.
*   **Orchestrator:** Manages the overall flow to call `ResearchAgent.research_sub_query`.
4.  **Execute Sub-Query Research (for, passing data between agents.
*   **Planning Phase:** The Planner Agent uses its LLM to generate sub-queries. each parallel task):**
    *   **a. Search:** `ResearchAgent` calls `search_tavily`.
        *   *Decision:* If `search_tavily` returns an empty list of URLs, the agent
*   **Concurrent Research Phase:** Multiple Research Agents work in parallel. Each uses Tavily for search, Firecrawl for scraping logs a warning and prepares an error note ("No relevant web search results found.") for this sub-query, skipping subsequent steps for this task.
        *   *Decision:* If URLs are found, proceed to scraping.
    *, and another LLM for summarizing relevant content for its specific sub-query. They produce findings or error notes.
*   **Aggregation:** The Orchestrator collects results from all Research Agents.
*   **Reporting Phase:** The Report   **b. Scrape & Summarize:** `ResearchAgent` calls `scrape_and_summarize_urls`. This Agent takes all findings and uses its LLM to synthesize the final report.
*   **Output:** The report is displayed. function iterates through URLs.
        *   **i. Rate Limit Check:** Before scraping a URL, `scrape_with_fire

### 3. Step-by-Step Decision Making

1.  **Receive Query:** The system gets the `crawl` checks the `RateLimiter`.
            *   *Decision:* If the limit is hit, wait for the specified backoff period before proceeding.
        *   **ii. Attempt Scrape:** `scrape_with_firecrawl` callstask` string from the user.
2.  **Initialize:** Load config, API keys, and create agent instances.
 Firecrawl API.
            *   *Decision:* If Firecrawl returns a `400 Bad Request` (3.  **Analyze Query (Planner):** Send the `task` to the Planner LLM to understand intent, constraints, and needed info types.
4.  **Generate Sub-Queries (Planner):** Based on analysis, formulate specificAPI call error) or other non-rate-limit exception, log the error and return an error note ("Could not scrape... Firecrawl error...").
            *   *Decision:* If Firecrawl returns a `429 Rate Limit` sub-queries via LLM.
5.  **Validate Plan (Planner):** Check if LLM output is a valid JSON error, wait the suggested time (or default) and *retry the scrape once*. If the retry fails, return an error note (" list of strings. If not, attempt repair. If still invalid or empty, *decide* to fallback to using the original `task` as the only sub-query.
6.  **Initiate Research (OrchestratorCould not scrape... Rate limit hit...").
            *   *Decision:* If Firecrawl returns successfully but the content is empty/invalid, log a warning and return an error note ("Could not scrape... No valid content...").
            *   *Decision):** *Decide* to run research concurrently. Create an async task for each sub-query, passing it and:* If Firecrawl returns valid Markdown, proceed to summarization.
        *   **iii. Attempt Summarization:** ` the original `task` to a `ResearchAgent`.
7.  **Perform Search (Researcher):** For asummarize_with_llm` is called with the scraped content.
            *   *Decision:* If the given sub-query, *decide* to call Tavily Search.
8.  **Evaluate Search Results (Researcher content is too short, skip the LLM call and return an info note ("Content was too short...").
            *):** *Decide* whether URLs were returned. If not, generate an error note and stop research for this sub-   *Decision:* Call the researcher LLM. If the LLM call fails (e.g., API error, `ValueErrorquery. If yes, proceed.
9.  **Attempt Scrape (Scraper Utility):** For each URL, *dec` from invalid response structure), log the error and return an error note ("Could not summarize... LLM processing error..."). Includeide* to call Firecrawl after acquiring a rate limit lock.
10. **Evaluate Scrape (Scraper Utility):** *Decide* if Firecrawl returned valid Markdown content. If not (due to errors like 400, specific error if possible. Check if error suggests context length issues and potentially try a truncated version (optional fallback).
            *   *Decision:* If the LLM call succeeds, return the formatted summary ("Source: ... Summary: ...").
     5xx, or empty result), generate a scraping error note. Handle 429 Rate Limit errors by **   **c. Consolidate:** `ResearchAgent` gathers all the returned strings (summaries or error notes) for its sub-query and formats them into a single block.
5.  **Aggregate & Check Findings:** The `deciding* to wait and retry once. If retry fails, generate an error note.
11. **Attemptmain.py` orchestrator waits for all parallel `research_sub_query` tasks to finish. It collects all the returned Summarization (Scraper Utility):** If scraping yielded content, *decide* to call the Researcher LLM.
12. **Evaluate Summarization (Scraper Utility):** *Decide* if the LLM call was successful findings blocks.
    *   *Decision:* If *no* findings blocks were successfully returned (all tasks failed critically and returned content. If not (due to API errors, `NoneType` errors, potentially context length issues), generate a before returning even an error note), log a fatal error and stop.
    *   *Decision:* If *all* findings summarization error note.
13. **Consolidate Findings (Researcher):** Collect all generated summaries and error notes for the blocks contain only error notes indicating scraping/summarization failed for every URL attempted, log a critical error and stop (or potentially allow sub-query.
14. **Aggregate Results (Orchestrator):** Wait for all concurrent research tasks. the reporter to state this).
    *   *Decision:* If at least some findings (even if containing error notes) were gathered Collect all the consolidated findings/error blocks.
15. **Evaluate Aggregation (Orchestrator):**, proceed to reporting.
6.  **Synthesize Report:** `main.py` calls `ReportAgent.write_report *Decide* if *any* findings (even if just error notes) were collected. If not, stop and report failure.
16. **Generate Report (Reporter):** Combine all findings. *Decide* to call the Reporter` with the aggregated findings.
    *   *Decision:* `ReportAgent` sends the combined text and instructions to the reporter LLM. If the LLM call fails, log the error and return a final error message ("Failed to generate... LLM with the synthesis prompt.
17. **Evaluate Report Generation (Reporter):** *Decide* if the LLM call succeeded. If not, return a final error message. If yes, return the generated report text.
18 LLM error...").
    *   *Decision:* If the LLM succeeds, return the generated report text.
7.  **Output:** `main.py` prints the final string received from `ReportAgent` (either the report. **Output Result (Orchestrator):** Print the final report or error message received from the Reporter.

### 4. Handling Problems

The system has several mechanisms to handle common issues:

1.  **Unreachable Websites / or an error message).

---

**4. Handling Problems (Error Handling & Robustness)**

The system incorporates several layers to handle common issues:

1.  **LLM Failures (OpenRouter):**
    * Scrape Failures (e.g., Blocks, Timeouts):**
    *   **Detection:** The `scrape   **API Errors/Timeouts:** `try...except` blocks around `aclient.chat.completions_with_firecrawl` function uses a `try...except` block to catch exceptions during the Firecrawl API call.create` in `utils/llm.py` catch generic exceptions, log them, and re-raise them (e.g., connection errors, timeouts, HTTP status errors like 403, 500). Fire. The calling functions (`generate_sub_queries`, `summarize_with_llm`, `write_report`)crawl itself handles much of the complexity of rendering dynamic sites.
    *   **Handling:** If an error occurs (and have their own `try...except` blocks to catch these re-raised errors.
    *   **Invalid/Empty Success isn't a rate limit), it's logged, and the function returns `None`. The calling function (`process_url Response (`NoneType` Error):** The improved `call_llm` function now explicitly checks if `response.choices``) then converts this `None` into a specific error string (e.g., `"Source: [URL]\nError is valid and non-empty before accessing it. If not, it logs details and raises a `ValueError`. This is caught by the: Could not scrape or extract content using Firecrawl."`).
    *   **Impact:** This error note for the specific URL calling functions.
    *   **Malformed JSON (Planner):** `PlanningAgent` uses `json_repair. is passed along with successful summaries to the Report Agent. The final report will mention that information from that source was unavailable.

2loads` as a fallback if the initial `json.loads` fails on the planner's response. If repair also.  **Rate Limits (Firecrawl 429):**
    *   **Detection:** The `scrape fails, it defaults to using the original query.
    *   **Context Length Exceeded:** While basic character truncation was added to_with_firecrawl` function specifically checks the exception for indications of a rate limit error (status code 42 `scrape_with_firecrawl`, the primary defense is now the *fallback* logic within `summarize_with9 or keywords in the message).
    *   **Handling:** It implements a **retry mechanism with exponential backoff (simplified here to a fixed wait + retry)**. It waits for a suggested period (extracted from the error or a default) and_llm`. If the initial LLM call fails with a context-length-related error (heuristic check), it attempts a attempts the scrape *one* more time.
    *   **Impact:** This increases the chance of success on temporary simple character truncation and retries the summary once. If that also fails, or the error wasn't context-related, it rate limits. If the retry also fails, it proceeds as a standard scrape failure (returns `None`, leading to an error note returns an error note. The reporter doesn't currently truncate, relying on powerful models with large contexts, but would return an error if).

3.  **Conflicting Information:**
    *   **Detection:** This isn't detected automatically by the combined input is truly excessive and causes an LLM failure.

2.  **Web Search Failures (Tavily code but is handled during the synthesis stage. The `ReportAgent` receives summaries from potentially different sources gathered for different sub-queries):**
    *   **API Errors:** `try...except` in `utils/web_search.search_tavily` catches errors and returns an empty list `[]`.
    *   **No Results:** `Research.
    *   **Handling:** The **Reporter LLM** is explicitly instructed via its system prompt to identify and handle conflicts: *"If you encounter contradictory information between sources, acknowledge it neutrally (e.g., 'Some sources suggest X,Agent` checks if the returned list is empty. If so, it generates an error note for that sub-query ("No relevant web search results found.") and doesn't proceed to scraping for that task.

3.  **Web Scraping Fail while others indicate Y.')"*.
    *   **Impact:** The final report aims to present a balanced view reflectingures (Firecrawl):**
    *   **API Call Errors (`400 Bad Request`):** The `try...except` in `scrape_with_firecrawl` catches these. Currently, it logs the error and returns ` the different perspectives found in the sources, rather than silently discarding information or arbitrarily choosing one version.

4.  **LLMNone`, causing `process_url` to generate an error note ("Could not scrape... Firecrawl error..."). * Errors (API Failures, Invalid Responses):**
    *   **Detection:** The `utils/llm.callFurther improvement: Analyze the specific 400 error message if possible.*
    *   **Rate Limits (`429 Too Many Requests`):** Handled specifically. The code detects the error, waits for a suggested or default period, and ret_llm` function includes robust checks. It catches API connection errors, timeouts, and crucially, checks if a successful HTTP response (`200 OK`) actually contains the expected `choices` data structure.
    *   **Handling:**
        ries the scrape *once*. If the retry fails, it returns `None`, leading to an error note.
    *   If `choices` is missing or `None` after a 200 OK, it raises a `ValueError`.
        *   General exceptions during the API call are re-raised.
        *   The calling functions (`generate*   **Timeouts/Connection Errors:** Caught by the general `try...except` in `scrape_with__sub_queries`, `summarize_with_llm`, `write_report`) wrap their `call_llfirecrawl`, logged, and returns `None`, leading to an error note.
    *   **Empty/Invalid Content:** Ifm` invocations in `try...except Exception`.
        *   On catching an error, they log it and return a fallback Firecrawl succeeds but returns no usable Markdown, this is detected, logged, and returns `None`, leading to an error note.
    *   **`robots.txt`:** *Currently not implemented.* A production system *must* add a value (the original query for the planner, an error note string for the summarizer, or a final error report message check before scraping any URL to respect `robots.txt` rules, skipping disallowed URLs.

4.  **Conf for the reporter).
    *   **Impact:** Prevents the system from crashing on LLM issues and incorporates failurelicting Information:**
    *   This is handled during the **Reporting Stage**. The `ReportAgent`'s system prompt explicitly information into the process flow or final output.

5.  **Planning Failures (Invalid JSON, No Sub-Queries instructs the LLM *not* to try and resolve contradictions definitively but to *acknowledge* them neutrally in the report):**
    *   **Detection:** The `PlanningAgent` uses `json_repair` and type checking.
    *   **Handling:** If it cannot produce a valid list of sub-queries, it defaults to using the original user ` (e.g., "Source A states X, while Source B suggests Y regarding this point."). The synthesis focuses on presenting the range of information found.

5.  **Concurrency Control:**
    *   The `RateLimiter` class combinedtask` as a single sub-query.
    *   **Impact:** Allows the research process to continue even if planning with `asyncio.sleep` in the retry logic manages requests to Firecrawl, preventing overwhelming the API (though tuning fails, attempting research on the broader original topic.

6.  **No Search Results:**
    *   **Detection:** The `ResearchAgent` checks the list of URLs returned by Tavily.
    *   **Handling:** If the list might be needed).
    *   `asyncio.gather` manages the concurrency of the `ResearchAgent` tasks is empty, it skips the scraping/summarization step and returns an error note for that sub-query.
    *   ** themselves.

By implementing these checks, fallbacks, and specific error handling routines, the agent aims to complete the research process evenImpact:** Prevents unnecessary scraping attempts and informs the reporter that no web sources were found for that specific sub-topic.