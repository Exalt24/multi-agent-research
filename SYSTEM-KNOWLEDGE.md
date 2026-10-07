# Design notes

How the Multi-Agent Market Research Platform is put together and why. Everything here can be checked against the code in `backend/app/`; the README covers setup and usage.

## Why LangGraph

I wanted explicit control over the order of stages and over what each agent can read and write, and CrewAI hides more of that than I wanted. LangGraph gives a state machine over a typed shared state, fan-out and fan-in for the two parallel stages, and it sits on top of LangChain, which the agents already use for the LLM clients. The cost is more boilerplate than a higher-level framework.

## The graph

`backend/app/agents/graph.py` defines seven nodes:

1. `coordinator`
2. `web_research` and `financial_intel`, both started by the coordinator, both feeding `data_analyst`
3. `data_analyst`
4. `fact_checker`
5. `content_synthesizer` and `data_viz`, both started by the fact checker, both ending the run

LangGraph runs the two branches of each fan-out concurrently and holds the receiving node until both have finished. The branches write to different state fields, so they do not overwrite each other. A comment in `graph.py` estimates the time saved by the parallel stages; it is an estimate, not a measurement, and I have not benchmarked the pipeline against a sequential version.

## Shared state

`MarketResearchState` in `agents/state.py` is a TypedDict. Lists that more than one agent can append to are declared `Annotated[List[...], operator.add]`: `research_findings`, `current_agent`, `cost_tracking`, `errors`, `fact_check_results`, `visualizations` and `messages`. When two parallel branches each return a list for one of those fields, LangGraph concatenates them. Plain fields such as `competitor_profiles`, `financial_data`, `comparative_analysis` and `final_report` have a single writer.

Agents never call each other. Each reads what it needs from state and returns a dict of fields to merge back.

## The coordinator pattern

The coordinator returns JSON with `research_objectives`, `search_priorities` (per company), `financial_priorities`, `comparison_angles`, `depth_settings` and a `research_plan` shown to the user. Downstream agents use it:

- Web research builds its search queries from `search_priorities` and takes its depth from `depth_settings`. Depth sets the query count (2, 3 or 4), results per query (2, 3 or 5), RAG chunks (1, 2 or 4) and whether to scrape the top pages in full (comprehensive only).
- Financial intelligence builds its query from `financial_priorities`.
- The analyst puts `comparison_angles` in its prompt.
- The synthesizer frames the report around `research_objectives`.

## Base agent

All agents extend `BaseAgent` (`agents/base.py`), which owns the parts every agent needs: WebSocket status updates, the approval request helper, cost tracking with tiktoken, a per-agent timeout (`AGENT_TIMEOUT`, 120 seconds by default) and retries, up to five attempts. On a rate-limit error the agent moves to the next model in `FALLBACK_LLM_MODELS` because Groq's quotas are per model, per minute and per day, so waiting does not clear a daily ceiling. When the fallback list is used up it waits as long as Groq's error message says, capped at 30 seconds. Other errors back off exponentially. Provider errors are logged in full and shown to the user as one plain sentence.

## Token budgets

The content synthesizer carries the output of every upstream agent in its prompt, which is the call most likely to exceed Groq's free-tier ceiling of about 8,000 tokens per minute per model. Its truncation budgets are named constants at the top of `content_synthesizer.py` (`SUMMARY_ANALYSIS_TOKENS`, `REPORT_RESEARCH_TOKENS` and so on), with the arithmetic in a comment, and each call caps its own completion length. Before September 2026 the budgets had been sized for an 8,192-token context window instead of the per-minute limit, and the synthesizer could not finish on the free tier.

## Search and the RAG service

`agents/tools/search.py` has a `SearchManager` that tries Tavily first when a key is set and falls back to DuckDuckGo, plus a scraper for full page content. Results go through `services/cache.py`, which uses Redis when `REDIS_URL` is set and an in-memory store otherwise, with a one-hour TTL. The web research agent also asks the Enterprise RAG Knowledge Base API (`agents/tools/rag_client.py`, `POST {RAG_API_URL}/query`) and continues without its answer if the call fails.

## LLM selection

`core/llm.py`: with `ENVIRONMENT=production` the app uses Groq only. In development it tries Ollama first and falls back to Groq if Ollama is not running. The Groq model is `DEFAULT_LLM_MODEL` (default `openai/gpt-oss-120b`). It was hardcoded to `llama-3.3-70b-versatile` until Groq retired that model on 2026-09-07 and every agent started failing; making it a setting was the fix.

## The approval gate

`agents/fact_checker.py` checks the report text for "unverified", "could not verify", "insufficient evidence" or "contradictory". If one is present it calls `_request_approval` with two options, "Continue Anyway" and "Stop Workflow", and a 300-second timeout. `services/hitl_manager.py` holds the pending request and resolves it when the browser posts to `/api/approval/respond`. Stopping marks the workflow failed. A timeout or an approval error lets the run continue, so a closed browser tab cannot hold a run forever.

## Real-time updates

`api/websocket.py` keeps the connections for each session id and broadcasts agent status messages. `useWebSocket.ts` on the frontend consumes them and drives the agent cards and the approval modal. The frontend measures how long each agent has been working itself, because the status messages carry no usable timestamp.

## Rate limiting and configuration

`/api/research` is limited to 5 requests per minute per IP with slowapi. `core/config.py` validates settings at startup: production requires `GROQ_API_KEY` and `TAVILY_API_KEY`, and development requires either a Groq key or a running Ollama.

## Testing

There is one end-to-end smoke test, `backend/test_api.py`, which posts a research request to a running local server. There are no unit tests. Adding some, with the LLM and search mocked, is the obvious next piece of work.

## What I would change

- Write the tests alongside the agents instead of after them.
- Time each agent per run and record it, so the parallel-stage savings could be stated as a measurement.
- Store finished research so later runs can reuse it, which is the last item under "Not done" in the README.
