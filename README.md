# Multi-Agent Market Research Platform

Seven LangGraph agents that research a set of companies, fact-check the findings, and write a comparison report with charts.

**Live demo:** https://multi-agent-research-frontend.vercel.app
**API:** https://multi-agent-research-api.onrender.com (interactive docs at `/docs`)

A full run takes a few minutes, and the demo runs on free tiers (Groq, Tavily, Render), so a run can hit Groq's free-tier limits and slow down or fail. The backend sleeps when idle, so the first request after a quiet spell is slow.

---

## What it does

You give it a query and a list of companies. A coordinator agent plans the research, two agents gather web and financial data in parallel, an analyst builds SWOT and feature comparisons, a fact checker reviews the claims, and two more agents write the report and generate chart specs in parallel. Progress streams to the browser over a WebSocket while it runs. The result can be downloaded as PDF, Markdown or JSON.

- **Agents:** 7, with two parallel stages (research, then output)
- **Human in the loop:** one gate, in the fact checker (see below)
- **Stack:** LangGraph, FastAPI, Next.js 16, Groq (Ollama for local development), Redis, Chart.js, tiktoken
- **Cost:** runs on free tiers (Groq, Tavily, Render, Vercel), with Redis optional

## What broke

On 2026-09-07 Groq retired the `llama-3.3-70b-versatile` model name, and this demo and the Enterprise RAG service it calls both started failing on the same day. Every agent died on a raw `model_not_found` error. The fix was to make the model a setting (`DEFAULT_LLM_MODEL`, default `openai/gpt-oss-120b`) so the next retirement is an environment variable change instead of a code change.

That same week I found the content synthesizer could never succeed on the free tier: its two calls asked for roughly eleven thousand tokens against a per-minute ceiling of eight thousand. The token budgets are now named constants in `content_synthesizer.py`, and a rate-limited agent now moves to the next model in `FALLBACK_LLM_MODELS`, because Groq's quotas are per model, and once that list is used up it waits as long as Groq asks.

---

## The 7 agents

| Agent | Role | Tools | Execution |
|-------|------|-------|-----------|
| **Coordinator** | Plans the run: objectives, search priorities, financial priorities, comparison angles, depth per agent | LLM with JSON output | Sequential |
| **Web Research** | Gathers competitive intelligence using the coordinator's search priorities | Tavily, DuckDuckGo, search cache, page scraping, Enterprise RAG API | Parallel with Financial |
| **Financial Intelligence** | Researches funding, revenue and growth | Tavily, DuckDuckGo, search cache, page scraping | Parallel with Web |
| **Data Analyst** | SWOT and feature matrix, using the coordinator's comparison angles | LLM over web and financial data | Sequential |
| **Fact Checker** | Reviews the analysis and can pause the run for a human decision | LLM, approval gate | Sequential |
| **Content Synthesizer** | Writes the summary and the full report around the coordinator's objectives | LLM, two calls | Parallel with Data Viz |
| **Data Visualization** | Produces Chart.js specs (bar, line, pie, doughnut) for the frontend | LLM | Parallel with Synthesizer |

The coordinator's output is used, not decorative: its priorities become the search queries, its comparison angles go into the analyst's prompt, and its objectives frame the report. Its depth settings (light, standard, comprehensive) change how many queries, results, RAG chunks and scraped pages each agent uses.

## The human-in-the-loop gate

There is exactly one. After the fact checker writes its report, the backend looks for the words "unverified", "could not verify", "insufficient evidence" or "contradictory". If any appear, the run pauses and the browser shows an approval modal with a preview of the report and two choices, continue or stop. If nobody answers within 300 seconds, the run continues. If the approval mechanism itself errors, the run also continues.

## Architecture

```
User query + companies
        |
        v
FastAPI (main.py): LangGraph, WebSocket updates, rate limiting
        |
        v
Coordinator
        |
        +-------------------+
        v                   v
  Web Research        Financial Intel      (parallel stage 1)
        |                   |
        +---------+---------+
                  v
            Data Analyst
                  |
                  v
            Fact Checker  <---- approval gate (continue or stop)
                  |
        +---------+---------+
        v                   v
 Content Synthesizer    Data Viz           (parallel stage 2)
        |                   |
        +---------+---------+
                  v
   Report, charts, PDF / Markdown / JSON export
```

I have not timed the stages, so the diagram carries no durations. Run time depends on the model, the depth setting and Groq's rate limits.

### State

All agents share one `MarketResearchState` (a TypedDict). Fields that parallel agents write to (`research_findings`, `current_agent`, `cost_tracking`, `errors`, `fact_check_results`, `visualizations`) are declared `Annotated[List[...], operator.add]`, so LangGraph concatenates what each branch returns instead of letting one overwrite the other. Fields that only one agent writes (`competitor_profiles`, `financial_data`, `final_report`) are plain.

---

## Quick start

Prerequisites: Python 3.11+, Node.js 18+, and either a Groq API key or a local Ollama.

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Add GROQ_API_KEY. Add TAVILY_API_KEY for better search (DuckDuckGo is the fallback).

python -m app.main
```

The server runs at `http://localhost:8000`. In development it uses Ollama if one is running and Groq otherwise. With `ENVIRONMENT=production` it uses Groq only and requires both `GROQ_API_KEY` and `TAVILY_API_KEY`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local      # defaults work for local development
npm run dev
```

The frontend runs at `http://localhost:3000`.

### Example request

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare Notion vs Coda vs ClickUp",
    "companies": ["Notion", "Coda", "ClickUp"],
    "analysis_depth": "standard"
  }'
```

---

## API

| Method | Endpoint | Description | Rate limit |
|--------|----------|-------------|------------|
| GET | `/health` | Health check | None |
| GET | `/api/cache/stats` | Search cache hits, misses and backend in use | None |
| GET | `/api/llm/health` | Which LLM provider and model is active | None |
| POST | `/api/research` | Start a research run | 5 per minute per IP |
| POST | `/api/approval/respond` | Answer the approval gate | None |
| GET | `/api/approval/pending/{session_id}` | List pending approvals | None |
| GET | `/docs`, `/redoc` | Swagger and ReDoc | None |

`WS /ws/research/{session_id}` streams `workflow_started`, `agent_status`, `approval_request`, `approval_received`, `workflow_complete` and `workflow_failed`.

---

## Configuration

Backend `.env`:

```bash
GROQ_API_KEY=your_groq_key          # required in production
TAVILY_API_KEY=your_tavily_key      # required in production, optional in development
REDIS_URL=your_redis_url            # optional, an in-memory cache is used without it
ENVIRONMENT=development             # or production

# Optional: override the Groq model. Set this when Groq retires one.
# DEFAULT_LLM_MODEL=openai/gpt-oss-120b
# Optional: models to move to when the default is rate limited (comma separated).
# FALLBACK_LLM_MODELS=openai/gpt-oss-20b,qwen/qwen3.8-27b
```

Other settings (`RAG_API_URL`, `OLLAMA_BASE_URL`, `LOG_LEVEL`, `CACHE_TTL`, `MAX_PARALLEL_AGENTS`, `AGENT_TIMEOUT`) have defaults in `backend/app/core/config.py`.

Frontend `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Behaviour worth knowing

- **Search cache.** Search results are cached for one hour (`CACHE_TTL`), in Redis when `REDIS_URL` is set and in memory otherwise. The deployed API currently reports `"cache_type": "in-memory"` at `/api/cache/stats`, so the demo is not using Redis right now.
- **Rate limit.** `/api/research` allows 5 requests per minute per IP, which protects the Tavily and Groq quotas.
- **Retries.** Each agent makes up to 5 attempts. When the default model is rate limited, the agent moves to the next model in `FALLBACK_LLM_MODELS`. Once that list is used up, or for any other error, it waits before retrying: as long as Groq says when it says (capped at 30 seconds), otherwise 1, 2, 4 and 8 seconds.
- **Token counting.** tiktoken counts tokens for the cost tracking and for truncating prompts to fit the model's per-minute budget.
- **RAG.** The web research agent asks the [Enterprise RAG Knowledge Base](https://github.com/Exalt24/enterprise-rag-knowledge-base) for existing knowledge and carries on without it if that service is down or slow.
- **Fail-fast config.** The backend refuses to start in production without its API keys.

---

## Deployment

### Backend on Render

The backend ships as a Docker image, so deploy it as a Docker web service. There is no `render.yaml`.

1. Create a new Web Service on https://dashboard.render.com and connect this repository.
2. Set the runtime to Docker, with Dockerfile path `./backend/Dockerfile` and build context `./backend`.
3. Add `GROQ_API_KEY` and `TAVILY_API_KEY`, optionally `REDIS_URL`, and set `ENVIRONMENT=production`.
4. Deploy. The container exposes port 8000 and a `/health` check.

### Frontend on Vercel

```bash
cd frontend
vercel --prod --yes
```

Set `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` (`wss://`) to the backend URL before building.

---

## Project structure

```
multi-agent-research/
├── backend/
│   ├── app/
│   │   ├── agents/          # one file per agent, plus base.py, state.py, graph.py
│   │   │   └── tools/       # search.py (Tavily, DuckDuckGo, scraper), rag_client.py
│   │   ├── api/             # schemas.py, websocket.py
│   │   ├── core/            # config.py, llm.py, tokens.py
│   │   ├── services/        # cache.py, hitl_manager.py
│   │   └── main.py          # FastAPI app and rate limiting
│   ├── test_api.py          # end-to-end smoke test
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── app/             # home form, live research page
│       ├── components/      # AgentCard, ChartRenderer, ApprovalModal
│       ├── hooks/           # useWebSocket.ts
│       └── utils/           # pdfExport.ts (jsPDF, html2canvas)
├── README.md
└── SYSTEM-KNOWLEDGE.md      # design notes
```

---

## Testing

The only test is a smoke test, `backend/test_api.py`. With the backend running, it posts a research request to `http://localhost:8000` and prints the result. There are no unit tests.

```bash
cd backend
python test_api.py
```

## Troubleshooting

- **Backend will not start:** check that Ollama is running (`curl http://localhost:11434/api/tags`) or put a `GROQ_API_KEY` in `.env`. Python 3.11 or newer is required.
- **A run fails with a model error:** the configured Groq model may have been retired. Set `DEFAULT_LLM_MODEL` to one Groq currently serves.
- **Frontend cannot connect:** check `NEXT_PUBLIC_API_URL` and the CORS origins in `backend/app/core/config.py`.
- **WebSocket will not connect:** use `ws://` against http and `wss://` against https, and check the session id.

## Not done

- No unit or integration tests beyond the smoke test.
- No authentication or per-user accounts.
- Search results are cached, but past research is not stored or searchable.

## License

MIT, see [LICENSE](LICENSE).
