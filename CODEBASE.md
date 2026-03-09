MULTI-AGENT MARKET RESEARCH PLATFORM -- INTERVIEW CHEAT SHEET

ONE-LINER

"It's a multi-agent research platform where 7 AI agents coordinate through LangGraph to produce comprehensive market research reports with real-time progress tracking and human-in-the-loop approval gates."

---

THE ANSWER THAT COST YOU THE INTERVIEW

Q: "What models are you using?"

"Groq's llama-3.3-70b-versatile for production because it's the fastest inference provider for open-source models, we're talking 3,000+ tokens per second compared to maybe 600 from proprietary providers. In development I use Ollama running llama3 locally so I don't burn API credits while testing. The system has a 2-tier fallback: tries Ollama first in dev, falls back to Groq if Ollama isn't running. In production it's Groq-only, fail-fast. No Ollama on Render since there's no local GPU."

Never blank on this again. The model names are llama-3.3-70b-versatile (Groq) and llama3 (Ollama). They're defined in backend/app/core/config.py at the default_llm_model and local_llm_model settings.

---

QUICK FACTS

What it does: 7 AI agents research companies in parallel, produce reports with charts
Frontend: Next.js 16, React, Chart.js for data visualization
Backend: FastAPI (Python), LangGraph for agent orchestration
LLM (Production): Groq llama-3.3-70b-versatile (self-imposed 8192 token limit, model supports 128K)
LLM (Dev): Ollama llama3 (local, free)
Database: No traditional DB. State flows through LangGraph's TypedDict
Cache: Redis (Upstash) for search results, 1-hour TTL, prefix "mar:search:"
Search APIs: Tavily (primary), DuckDuckGo (fallback)
Real-time: WebSocket (native FastAPI) for live agent progress
Token counting: tiktoken (0% error vs 22.9% with estimation)
Key metric: 30% faster than sequential execution via parallel agent stages
Deployment: Backend on Render (Docker), Frontend on Vercel
Live Demo: https://multi-agent-research-frontend.vercel.app
GitHub: https://github.com/Exalt24/multi-agent-research

---

ARCHITECTURE IN PLAIN ENGLISH

A user submits a research query like "Compare Notion vs Coda vs ClickUp." The backend creates a session, returns a session ID, and the frontend opens a WebSocket connection to that session for real-time updates. LangGraph kicks off the Coordinator agent, which generates a strategic research plan as JSON with objectives, search priorities, and depth settings. Then Web Research and Financial Intelligence run in parallel (that's where the 30% speedup comes from), both writing to shared state using operator.add reducers so there are no conflicts. After both finish, Data Analyst combines their output, Fact Checker validates it with an optional human-in-the-loop gate, then Content Synthesizer and Data Visualization run in parallel to produce the final markdown report and Chart.js specs. The whole thing takes about 105 seconds.

---

EVERY POSSIBLE INTERVIEW QUESTION

WHAT/HOW QUESTIONS

Q: What are the 7 agents and what does each one do?

"Coordinator generates the research plan as structured JSON with objectives and search priorities. Web Research uses Tavily and DuckDuckGo to find competitive intelligence, with Redis caching so repeated searches don't burn API credits. Financial Intelligence does the same but focused on funding, revenue, and valuation data. Data Analyst takes both outputs and creates SWOT analysis, feature comparison matrices, and market positioning. Fact Checker validates claims and triggers a human-in-the-loop gate if it finds issues. Content Synthesizer makes two LLM calls to write an executive summary and full report. Data Visualization generates Chart.js specs for bar, line, pie, and doughnut charts."

Q: How do the agents communicate?

"They don't talk directly to each other, and that's a deliberate choice. LangGraph supports different communication patterns, including conversational message-passing like AutoGen uses, but I went with shared state through a TypedDict instead. The reason is that market research is a pipeline, not a conversation. Each agent has a specific job: produce output, put it in state, move on. There's no back-and-forth negotiation needed. Fields like research_findings use Annotated with operator.add, which means parallel agents can append to the same list without conflicts. The Coordinator writes objectives and priorities, downstream agents read those to guide their work, then write their results back. LangGraph handles the merge automatically.

The trade-off is flexibility. If I wanted agents to challenge each other's findings or iteratively refine a report through debate, message-passing would be better. CrewAI does this well with its role-based crew model. But for a deterministic research pipeline, shared state is simpler and more predictable."

Q: How does the search work?

"SearchManager class tries Tavily first with advanced search depth, falls back to DuckDuckGo if Tavily rate limits or fails. Before hitting any API, it checks Redis cache using an MD5 hash of the query plus parameters, with the cache prefix 'mar:search:' to namespace it from other apps sharing the same Redis instance. Cache TTL is 1 hour since market data goes stale. For comprehensive depth, it also scrapes the top 2 URLs using BeautifulSoup to get full page content. There's also a RAG client that queries my Enterprise RAG Knowledge Base API for internal document search.

Why Tavily over alternatives? I evaluated SerpAPI and Brave Search too. SerpAPI is great if you need structured SERP data from multiple engines, like for SEO monitoring, but it's overkill for research agents that just need content. Brave Search has its own independent index which is cool for privacy, but Tavily was purpose-built for AI agents with LangChain integration out of the box and returns pre-ranked, citation-ready results. It also gives you up to 20 sources per query with its advanced depth. The 1,000 free searches per month beat SerpAPI's 250. DuckDuckGo as fallback is the pragmatic choice since it's completely free with no API key needed, even if the results aren't as well-structured.

The limitation is that Tavily uses its own proprietary ranking algorithm, so you're trusting their relevance scoring rather than getting raw Google results. For most research use cases that's fine, but if I needed exact SERP positions or structured product data, I'd switch to SerpAPI."

Q: How does the human-in-the-loop work?

"This is actually where the codebase differs from what you might expect with LangGraph. LangGraph has a built-in interrupt() function that pauses the graph and waits for human input through a checkpointer. It's the 'official' way to do HITL, and it works well for simpler cases where you pause, get input, and resume.

I built a custom HITLManager using asyncio Events instead. Here's why: the interrupt() pattern assumes the human is interacting through the same interface that's running the graph, like a CLI or notebook. In my case, the approval request needs to go through WebSocket to a browser frontend, and the approval response comes back through a REST endpoint (POST to the approval API), not through the graph runner. The flow is: Fact Checker detects issues, calls HITLManager.request_approval(), which broadcasts an approval_request message via WebSocket to the frontend. The frontend shows an approve/reject dialog. When the user clicks, the frontend hits a REST API endpoint, which resolves the asyncio Event that the workflow is awaiting. There's a 5-minute timeout so workflows don't hang forever if the user walks away, at which point it auto-continues.

The trade-off is that I lose LangGraph's built-in checkpointing for the HITL state. If the server crashes during the wait, the approval state is lost. With interrupt() and a proper checkpointer (like PostgresSQL-backed), you could resume after a crash. For a research tool where the wait is at most 5 minutes, I accepted that trade-off. For a production system handling financial approvals, I'd use interrupt() with persistent checkpointing."

Q: How do you handle real-time progress updates?

"Native FastAPI WebSocket, not Socket.IO. Each session gets its own connection at /ws/research/{session_id}. The WebSocketManager tracks active connections per session and broadcasts 6 message types: workflow_started, agent_status with 0-100 progress, approval_request for HITL, approval_received, workflow_complete with all results, and workflow_failed. The frontend uses a custom useWebSocket hook that tracks each agent's status.

Honestly, SSE (Server-Sent Events) would have been simpler and probably sufficient. The industry consensus in 2025 is that SSE beats WebSockets for 95% of real-time apps because most only need server-to-client push, which is exactly my use case. The agent progress updates are one-directional. The reason I chose WebSocket is that I also need the HITL approval flow, where the frontend sends approval responses back. But looking at it now, the approval actually goes through a REST endpoint, not the WebSocket. So SSE for the progress streaming plus REST for the approval POST would have been cleaner and avoided the connection management complexity.

WebSocket does give me lower latency and avoids HTTP overhead per message, which matters when you're pushing dozens of progress updates per second. But SSE auto-reconnects on network drops, works better through proxies and CDNs, and benefits from HTTP/2 multiplexing. If I rebuilt this, I'd seriously consider SSE for the streaming and keep REST for the bidirectional interactions."

Q: How does token counting work?

"I use tiktoken with the cl100k_base encoding, which is the same tokenizer GPT-4 and Llama models use. It gives 0% error compared to the naive len(text)//4 estimation which has 22.9% error. Every agent tracks its own input and output tokens, estimates cost per call, and appends that to the shared cost_tracking list in state. The encoder is cached with lru_cache so it only loads once.

One nuance: cl100k_base is technically OpenAI's tokenizer, and Llama models use a different tokenizer (SentencePiece). The token counts won't be perfectly accurate for Llama, but they're close enough for cost estimation purposes. The alternative would be loading the actual Llama tokenizer, which adds a heavy dependency for marginal accuracy improvement in cost tracking."

Q: What's your database schema look like?

"There's no traditional database. All data flows through LangGraph's MarketResearchState TypedDict. It has about 20 fields: input fields like query and companies, coordinator guidance like research_objectives and search_priorities, research output fields with operator.add for parallel safety, analysis fields, output fields for the final report and charts, and metadata like session_id, timestamps, errors, and cost tracking. Redis caches search results but nothing persists long-term.

This is a real limitation I'd fix in a production version. Right now if a user researches 'Notion vs Coda' and comes back the next day, they have to re-run the entire 105-second workflow. Adding PostgreSQL for completed research results would let users retrieve past reports instantly. I skipped it because this is a portfolio project demonstrating agent orchestration, not a SaaS product, and adding a database would have shifted focus away from the multi-agent architecture which is the interesting part."

Q: How do you handle errors and failures?

"Three layers. At the agent level, each agent has a BaseAgent class that retries up to 3 times with exponential backoff and a 120-second timeout. If all retries fail, it returns a graceful error dict that gets appended to the shared errors list without crashing the whole workflow. At the search level, Tavily failing triggers DuckDuckGo fallback. Redis unavailable triggers in-memory cache fallback. Ollama not running triggers Groq fallback. At the workflow level, the RAG client is optional, so if the Enterprise RAG API is down, research continues with web search only.

One thing I'd improve: the retry logic is generic across all agents. In practice, a Coordinator failure (no research plan) should probably fail-fast since nothing downstream can work without it, while a Data Visualization failure is non-critical and the report can still be delivered without charts. I'd add criticality levels to agents so the error handling is proportional to impact."

Q: How do you handle security?

"Rate limiting at 5 requests per minute per IP using slowapi. Pydantic validation on all request inputs. CORS whitelisting for allowed origins. WebSocket connections are scoped to session IDs. Error messages are truncated to 200 characters to prevent information leakage. Environment variables validated on startup with fail-fast if required keys are missing.

What's missing: there's no authentication. Any user can start a research session and consume LLM credits. For a portfolio demo that's fine since Groq's free tier absorbs the cost. For production I'd add JWT auth and per-user rate limits tied to subscription tiers."

WHY QUESTIONS (ARCHITECTURAL DECISIONS)

Q: Why Groq instead of OpenAI or Anthropic?

"Cost and speed, but let me be specific about the trade-offs. This system makes 10-15 LLM calls per research run across 7 agents. At OpenAI's GPT-4o pricing, that's real money per query. Groq serves llama-3.3-70b-versatile at 3,000+ tokens per second with a free tier. For a portfolio project, that's a no-brainer.

But there are real trade-offs. Groq has no proprietary frontier models. The quality ceiling is whatever the best open-source model is, which right now is Llama 3.3 70B. For most research tasks it's plenty, but for nuanced financial analysis or complex reasoning, GPT-4o or Claude would produce noticeably better output. Anthropic's Claude is particularly good at following complex instructions and producing well-structured outputs, which would help with the Content Synthesizer agent.

The other risk is vendor lock-in to Groq's infrastructure. If Groq changes pricing or has downtime, I'm stuck. The mitigation is that LangChain abstracts the provider, so swapping to OpenAI or Anthropic is a config change, not a rewrite. I've already proven that with the Ollama fallback in dev.

If this were a paid product, I'd probably use a mix: Groq for the speed-critical parallel agents (Web Research, Financial Intelligence) where throughput matters more than reasoning depth, and GPT-4o or Claude for the quality-critical agents (Data Analyst, Content Synthesizer) where output quality directly impacts the final report."

Q: Why LangGraph instead of CrewAI, AutoGen, or just running functions sequentially?

"I evaluated all three alternatives. CrewAI is the fastest to prototype with since it's role-based, you define a 'crew' of agents with tasks and it handles orchestration. But it's opinionated and abstracts away the control flow. When I needed custom parallel fan-out (Web Research + Financial Intelligence) followed by sequential analysis, then another parallel fan-out (Content Synthesizer + Data Viz), CrewAI's sequential/hierarchical patterns didn't map cleanly to my workflow shape.

AutoGen is great for conversational multi-agent patterns where agents debate and iterate, like a code review loop. But market research is a pipeline, not a conversation. I don't need agents arguing with each other, I need them executing specific tasks in a specific order with controlled parallelism.

OpenAI Swarm is the simplest option but it has no formal state management or orchestration. You're manually wiring everything through function docstrings that the LLM interprets. For 7 agents with parallel stages, that's too fragile.

LangGraph gave me three things I needed: explicit graph-based control flow where I define exactly which agents run in parallel, TypedDict state with operator.add reducers for safe parallel writes, and built-in support for conditional routing and subgraphs. The graph-as-code pattern also makes the workflow instantly readable. Anyone can look at graph.py and understand the execution order.

The trade-off is complexity. LangGraph has a steeper learning curve than CrewAI, and you write more boilerplate. For a 2-agent system, CrewAI would be faster. For 7 agents with mixed parallel/sequential stages and HITL gates, LangGraph's explicitness is worth it.

The industry seems to be moving toward mixing frameworks, where a LangGraph 'brain' might orchestrate a CrewAI sub-team for specific tasks. I haven't needed that level of composition, but it's a pattern I'd explore for more complex systems."

Q: Why Tavily over just scraping everything?

"Tavily returns structured, relevant search results ranked by quality. Scraping gives you raw HTML you have to parse and filter. For a research tool, I need quality results fast, not just volume. DuckDuckGo is the free fallback, but Tavily's advanced search depth gives better competitive intelligence data.

The deeper reason is reliability. Web scraping breaks constantly as sites change their markup. Tavily abstracts that away and gives me a stable API. The trade-off is that I'm limited to what Tavily's algorithm thinks is relevant, and the free tier caps at 1,000 queries/month. For a portfolio project that's plenty, but a production research tool would need a paid plan or a more aggressive caching strategy."

Q: Why FastAPI for the backend?

"Async support is critical since I'm running parallel agents and WebSocket connections. FastAPI handles that natively with asyncio. It also gives me automatic Pydantic validation and OpenAPI docs.

Django was the other option since I know it well, but Django's async support is still catching up, and the ORM overhead is wasted when I have no database. Flask with gevent could work but WebSocket support isn't native. FastAPI was the natural fit for an async-first, API-heavy backend with WebSocket needs."

Q: Why Redis for caching instead of just in-memory?

"Persistence across server restarts and shared state if I ever scale to multiple workers. The free tier on Upstash is more than enough. In-memory cache is the fallback if Redis goes down, so I get the best of both worlds.

The Upstash choice specifically is because it's serverless Redis, so I'm not paying for an always-on instance. Each cache operation is a pay-per-request call. For a portfolio project with sporadic traffic, that's cheaper than a dedicated Redis instance on any cloud provider."

Q: Why did you self-impose an 8192 token context limit when the model supports 128K?

"Great question, and it's a deliberate engineering decision. The model technically supports 128K context, but there are three reasons I capped it at 8192.

First, cost and speed. Larger context windows mean more tokens processed per call, which means slower responses and higher costs even on Groq's free tier. With 10-15 LLM calls per research run, keeping each call lean matters for total execution time.

Second, quality degradation. Research consistently shows that LLM performance degrades with longer contexts, even when models technically support large windows. Models don't use their context uniformly. They tend to focus on the beginning and end while losing information in the middle. By truncating to 8192 tokens and being selective about what goes in, I'm actually getting better output than if I dumped 50K tokens of raw research and hoped the model would find the relevant parts.

Third, it forces good information architecture. Instead of being lazy and stuffing everything into context, each agent has to produce concise, structured output. The Content Synthesizer truncates findings at 5000 tokens, which means it works with the most important data. If I removed the limit, agents would become sloppy about output quality because 'the context window can handle it.'

The trade-off is real though: deeply complex topics lose detail in the truncation. If I were building this for a research firm, I'd use a tiered approach, 8K for most agents but allow 32K or 64K for the Content Synthesizer where comprehensive output matters most. I'd also implement smarter compression, like summarizing research findings before passing them downstream instead of just truncating."

WALK ME THROUGH QUESTIONS

Q: Walk me through what happens when a user submits a research query.

"User fills out a form with a query like 'Compare Notion vs Coda' and selects analysis depth (basic, standard, or comprehensive). Frontend POSTs to /api/research, backend returns a session_id immediately. Frontend opens a WebSocket to /ws/research/{session_id}. Backend initializes a MarketResearchState with the query and companies, then runs the LangGraph workflow. Coordinator runs first (10 seconds), generates the plan. Web Research and Financial Intelligence run in parallel (30 seconds total instead of 60). Data Analyst combines their output (20 seconds). Fact Checker validates, maybe triggers HITL (15 seconds). Content Synthesizer and Data Viz run in parallel (20 seconds). Total: about 105 seconds. Each agent broadcasts progress via WebSocket so the frontend shows live status cards. When complete, the frontend gets the full report, charts, and cost breakdown."

Q: Walk me through how you tested this.

"I tested each agent independently first by mocking the LLM responses and verifying the state mutations. Then integration testing the full graph with real API calls. The main thing I validated was parallel state merging, making sure operator.add actually concatenates findings from Web Research and Financial Intelligence without losing data. I also tested the HITL timeout to make sure workflows don't hang forever if the user walks away.

Honestly, the testing coverage could be better. I don't have proper end-to-end tests that verify the full workflow from REST API call through WebSocket progress to final report delivery. That's because the 105-second execution time makes E2E tests slow and expensive (API credits). In a production setting, I'd mock the LLM layer and test the orchestration logic separately from the AI quality."

WHAT WOULD YOU CHANGE QUESTIONS

Q: What would you do differently if you rebuilt this?

"Several things. First, structured output from the LLM instead of parsing JSON from free-text responses. The Coordinator generates a research plan as JSON, and sometimes the LLM wraps it in markdown code blocks or adds commentary. I have parsing logic to handle that, but structured output would eliminate the problem. LangChain now has good support for this with output parsers and Pydantic models.

Second, persistent storage. Users should be able to reference past research without re-running 105-second workflows.

Third, SSE instead of WebSocket for the progress streaming, since the progress updates are purely server-to-client. Keep the REST endpoint for HITL approvals.

Fourth, agent-level criticality. Not all agent failures should be treated equally. The Coordinator failing should abort the run. Data Visualization failing should just skip charts and deliver the report.

Fifth, I'd look at LangGraph's interrupt() with a PostgreSQL-backed checkpointer for HITL instead of my custom asyncio Events approach. The built-in pattern gives you crash recovery for free, and the checkpoint persistence means a server restart mid-approval doesn't lose the workflow state."

Q: What are the limitations?

"The self-imposed 8192 token context means I truncate long research findings before passing them to downstream agents. Content Synthesizer truncates at 5000 tokens. That means really deep research on complex topics loses some detail. The model supports 128K, so I could increase this, but the trade-off is speed, cost, and quality degradation with longer contexts, models get less reliable as input length grows.

The free tier on Tavily has a 1,000 queries per month limit, so heavy usage would need a paid plan or more aggressive caching.

No authentication means anyone can consume LLM credits through the demo.

No persistent storage means completed research evaporates when the session ends.

The HITL implementation uses in-memory asyncio Events, so a server crash during the approval wait loses that workflow state. LangGraph's interrupt() with persistent checkpointing would solve this.

The system assumes English-language research. The search queries, agent prompts, and report structure are all English-only."

Q: How would you scale this?

"The main bottleneck is LLM calls, not compute. I'd add a job queue (BullMQ like I use in AutoFlow Pro, or Celery since the backend is Python) so research requests get queued instead of blocking. Multiple workers could process different research requests in parallel. I'd also add persistent storage so completed research can be retrieved without re-running.

For WebSocket scaling, I'd swap the in-process WebSocket for a managed pub/sub service like Redis Pub/Sub or Ably. FastAPI WebSocket works fine for a single server instance, but doesn't scale horizontally since connections are bound to the process that created them.

For the LLM layer, I'd implement a token budget per user tied to subscription tiers, with queue priority based on plan level. Free users get queued behind paid users.

If I needed to handle thousands of concurrent research sessions, I'd also look at splitting the LangGraph execution into separate microservices per agent, but that's over-engineering for anything short of enterprise scale."

---

MODELS AND LIBRARIES CHEAT SHEET

llama-3.3-70b-versatile (Groq): Production LLM, self-imposed 8192 token limit (model supports 128K). Fastest open-source inference at 3,000+ tok/s, generous free tier. Chose over GPT-4o for cost, over Claude for Groq's speed advantage with open-source models.

llama3 (Ollama): Dev LLM, runs locally. Zero API cost during development. Fallback in dev so I'm not dependent on internet connectivity while iterating.

LangGraph 1.0.4: Agent orchestration as directed graph. Chose over CrewAI (too opinionated for custom parallel patterns), AutoGen (conversational model doesn't fit pipeline architecture), OpenAI Swarm (no formal state management).

LangChain 1.1.0: LLM abstraction layer. Makes Groq/Ollama swappable without changing agent code. Some might argue this is unnecessary indirection, but the dev/prod provider swap justifies it.

langchain-groq: Groq provider for LangChain. Connects to Groq's API.

langchain-ollama: Ollama provider for LangChain. Connects to local Ollama.

Tavily: Web search API. Primary search, advanced depth, structured results. AI-native with LangChain integration. Chose over SerpAPI (overkill, lower free tier) and Brave Search (good but less AI-optimized).

DuckDuckGo (ddgs): Free web search. Fallback when Tavily rate limits. No API key needed, completely free, acceptable quality for backup.

tiktoken (cl100k_base encoding): Accurate token counting, 0% error vs 22.9% estimation. Note: technically OpenAI's tokenizer, not exact for Llama, but close enough for cost tracking.

Redis (Upstash): Search result caching, 1-hour TTL, "mar:search:" prefix. Serverless (pay-per-request), cheaper than dedicated Redis for sporadic traffic. In-memory fallback if Redis is down.

FastAPI: Backend framework. Async-native, WebSocket support, Pydantic validation, OpenAPI docs. Chose over Django (async still catching up, ORM overhead wasted with no DB) and Flask (no native WebSocket).

Next.js 16: Frontend framework. App Router, Turbopack, React 19.

Qdrant Client: RAG API integration. Queries Enterprise RAG project for internal docs. Optional dependency, system works without it.

BeautifulSoup4: Web scraping. Full page content extraction for comprehensive research depth.

Chart.js (frontend): Data visualization. Renders bar, line, pie, doughnut charts from agent-generated specs.

Pydantic: Request/response validation. Type-safe API contracts.

slowapi: Rate limiting. 5 req/min per IP. Simple but effective for a demo.

httpx: Async HTTP client. RAG API calls. Chose over requests because async matters in an asyncio-based backend.

jsPDF + html2canvas (frontend): PDF export. Export research reports as PDF.

---

KEY FILES MAP

If they ask about agent orchestration / graph definition: backend/app/agents/graph.py
If they ask about how state works / parallel safety: backend/app/agents/state.py
If they ask about LLM configuration / fallback logic: backend/app/core/llm.py
If they ask about model names and settings: backend/app/core/config.py
If they ask about Coordinator agent / research planning: backend/app/agents/coordinator.py
If they ask about web research / search strategy: backend/app/agents/web_research.py
If they ask about search manager (Tavily/DDG/cache): backend/app/agents/tools/search.py
If they ask about human-in-the-loop flow: backend/app/services/hitl_manager.py
If they ask about token counting / cost tracking: backend/app/core/tokens.py
If they ask about WebSocket real-time updates: backend/app/api/websocket.py
If they ask about Redis caching: backend/app/services/cache.py
If they ask about RAG integration: backend/app/agents/tools/rag_client.py
If they ask about base agent (retry, error handling): backend/app/agents/base.py
If they ask about financial intelligence agent: backend/app/agents/financial_intel.py
If they ask about data analyst agent: backend/app/agents/data_analyst.py
If they ask about fact checker agent: backend/app/agents/fact_checker.py
If they ask about content synthesizer agent: backend/app/agents/content_synthesizer.py
If they ask about data visualization agent: backend/app/agents/data_viz.py
If they ask about all Python dependencies: backend/requirements.txt
If they ask about frontend dependencies: frontend/package.json
If they ask about Docker deployment: backend/Dockerfile
