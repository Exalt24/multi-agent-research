# Multi-Agent Market Research Platform

**AI-powered competitive intelligence using 7 specialized agents orchestrated with LangGraph**

🔗 **Live Demo:** https://multi-agent-research-frontend.vercel.app
⚙️ **API Endpoint:** https://multi-agent-research-api.onrender.com

---

## Overview

A production-ready multi-agent AI system that automates market research and competitive analysis. Seven specialized agents work together to gather data, analyze competitors, validate findings, and generate comprehensive reports with visualizations.

### Key Metrics
- **Time Reduction:** Manual research 6-8 hours → Agent system 1.75 minutes (200x+ faster with parallel execution)
- **Agents:** 7 specialized agents with distinct roles (2 parallel execution stages)
- **Cost:** $0/month (free tier APIs: Tavily, Groq, Redis Cloud)
- **Real-Time:** WebSocket monitoring with Human-in-the-Loop approval gates
- **Tech Stack:** LangGraph, FastAPI, Next.js 16, Ollama/Groq, Redis, Chart.js, tiktoken

---

## The 7 Agents

| Agent | Role | Tools Used | Execution |
|-------|------|------------|-----------|
| **Coordinator** | Creates strategic plan with objectives, priorities, focus areas | LLM with JSON output | Sequential |
| **Web Research** | Gathers competitive intelligence using coordinator's search priorities | Tavily, DuckDuckGo, Redis cache, web scraping, RAG API | **Parallel** (with Financial) |
| **Financial Intelligence** | Researches funding, revenue, growth using coordinator's financial priorities | Tavily, DuckDuckGo, Redis cache, web scraping | **Parallel** (with Web) |
| **Data Analyst** | Creates SWOT, feature matrix using coordinator's comparison angles | LLM analysis, web + financial data | Sequential |
| **Fact Checker** | Validates claims with HITL approval gate if issues detected | LLM validation, human oversight | Sequential |
| **Content Synthesizer** | Writes summary + report structured around coordinator's objectives | LLM generation (2 calls) | **Parallel** (with Data Viz) |
| **Data Visualization** | Generates Chart.js specs for frontend rendering | LLM recommendations | **Parallel** (with Content Synth) |

---

## Architecture

```
┌────────────────────────────────────────────────────┐
│                   User Input                       │
│          "Compare Notion vs Coda vs ClickUp"       │
└──────────────────┬─────────────────────────────────┘
                   │
                   v
┌──────────────────────────────────────────────────────┐
│              FastAPI Backend (main.py)               │
│         LangGraph + WebSocket + HITL + Redis         │
└──────────────────┬───────────────────────────────────┘
                   │
      ┌────────────┴────────────┐
      v                         v
┌─────────────┐         ┌──────────────┐
│ Coordinator │         │  WebSocket   │
│   Agent     │         │   Manager    │
│  (10s)      │         │ (Real-time)  │
└──────┬──────┘         └──────┬───────┘
       │                       │
       │ Creates strategic     │
       │ guidance:             │
       │ - search_priorities   │
       │ - financial_priorities│
       │ - comparison_angles   │
       │ - depth_settings      │
       v                       │
┌──────────────────────────────┴──────────────┐
│         PARALLEL STAGE 1 (Research)         │
│  Web Research (40s)  │  Financial Intel(30s)│
│  - Uses priorities   │  - Uses priorities   │
│  - Redis cache       │  - Redis cache       │
│  - Web scraping      │  - Web scraping      │
│  - RAG integration   │                      │
└──────────────────┬──────────────────────────┘
                   │ (Both complete)
                   v
┌──────────────────┐
│  Data Analyst    │◄───── Real-time updates
│     (20s)        │
│ - Combines data  │
│ - Uses angles    │
└────────┬─────────┘
         │
         v
┌──────────────────┐
│  Fact Checker    │◄───── Real-time updates
│     (15s)        │
│ - HITL gate      │◄──┐
│ - Human approval │   │ (if issues)
└────────┬─────────┘   │
         │             │
         v             │
┌──────────────────────┴──────────────────┐
│       PARALLEL STAGE 2 (Output)         │
│  Content Synth (20s) │  Data Viz (15s)  │
│  - Uses objectives   │  - Chart.js      │
│  - 2 LLM calls       │  - Frontend ready│
└──────────┬──────────────────┬────────────┘
           │                  │
           v                  v
     ┌──────────────┐    ┌──────────┐
     │ Final Report │    │  Charts  │
     │ - Summary    │    │ - Bar    │
     │ - Full MD    │    │ - Line   │
     │ - PDF export │    │ - Pie    │
     └──────┬───────┘    └────┬─────┘
            │                 │
            v                 v
      ┌─────────────────────────┐
      │    Frontend Display      │
      │  - Research Strategy     │
      │  - Live Agent Status     │
      │  - Final Results         │
      │  - Interactive Charts    │
      │  - Download (PDF/MD/JSON)│
      └──────────────────────────┘

Total Time: ~105 seconds (1.75 minutes) with parallel execution
vs. 150 seconds (2.5 minutes) sequential - 30% faster!
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama (optional, for local LLM) OR Groq API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add:
# - GROQ_API_KEY (required for production)
# - TAVILY_API_KEY (optional, improves search quality)

# Run server
python -m app.main
```

Server runs at: `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# For local dev, defaults work
# For production, set NEXT_PUBLIC_API_URL

# Run dev server
npm run dev
```

Frontend runs at: `http://localhost:3000`

---

## Features

### Core Capabilities

✅ **Strategic Multi-Agent Orchestration**
- 7 specialized agents with coordinator-driven execution
- LangGraph state machines with parallel execution (2 stages)
- Strategic coordinator generates: objectives, priorities, focus areas, depth settings
- All agents adapt behavior based on coordinator's guidance
- Error handling with exponential backoff retries (3 attempts)

✅ **Intelligent Research with Caching**
- Redis-backed search caching (5-10x speedup, protects Tavily quota)
- Dual search: Tavily API (premium) + DuckDuckGo (free fallback)
- Web scraping for comprehensive depth (full page content)
- RAG integration (queries Project 1 Enterprise RAG knowledge base)
- Depth-based research: light (fast) / standard (balanced) / comprehensive (thorough)

✅ **Comprehensive Analysis**
- SWOT analysis per company (with financial metrics)
- Feature comparison matrix (coordinator's comparison angles prioritized)
- Market positioning insights
- Pricing comparisons with financial context
- Fact-checking with confidence scores + Human-in-the-Loop approval gates

✅ **Professional Output**
- Research strategy (coordinator's plan visible to users)
- Executive summary (2-3 paragraphs, objectives-focused)
- Detailed markdown report (structured around research objectives)
- Interactive Chart.js visualizations (bar, line, pie, doughnut)
- PDF export with embedded charts
- Source attribution with URLs

✅ **Real-Time Monitoring & Human Oversight**
- WebSocket live updates (agent status, progress, messages)
- Loading skeletons for better UX
- Human-in-the-Loop approval gates (pause workflow for quality review)
- Approval modal with context preview
- Cost tracking with tiktoken (accurate per-call, per-agent breakdown)

✅ **Production Features**
- Parallel execution (30% faster: 105s vs 150s)
- Accurate token counting (tiktoken, auto-detects llama3 vs llama-3.3-70b)
- Per-company and per-call cost tracking
- Rate limiting (5 req/min, protects quotas)
- Configuration validation (fail-fast on startup)
- Redis caching with 1-hour TTL
- Health check endpoints (service, cache, LLM)
- Error handling with proper logging
- Docker deployment
- Zero deprecation warnings

---

## API Endpoints

### REST API

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/health` | Health check | None |
| GET | `/api/cache/stats` | Cache performance metrics | None |
| GET | `/api/llm/health` | LLM provider status | None |
| POST | `/api/research` | Start research workflow | 5/minute |
| POST | `/api/approval/respond` | Submit HITL approval decision | None |
| GET | `/api/approval/pending/{session_id}` | Get pending approvals | None |
| GET | `/docs` | Interactive API documentation (Swagger) | None |
| GET | `/redoc` | API documentation (ReDoc) | None |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `WS /ws/research/{session_id}` | Real-time agent updates, HITL approvals, workflow status |

### Message Types (WebSocket)
- `workflow_started` - Research begins
- `agent_status` - Agent progress updates
- `approval_request` - Human approval needed
- `approval_received` - Approval processed
- `workflow_complete` - Research finished
- `workflow_failed` - Research error

### Example Request

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

## Deployment

### Deploy Backend to Render

1. Go to https://dashboard.render.com/select-repo
2. Select `multi-agent-research` repository
3. Render will auto-detect `render.yaml`
4. Add environment variables:
   - `GROQ_API_KEY` (required)
   - `TAVILY_API_KEY` (required)
   - `REDIS_URL` (optional, uses memory fallback)
5. Deploy!

### Deploy Frontend to Vercel

Via Vercel Dashboard or CLI:
```bash
cd frontend
vercel --prod --yes
```

After backend deployment, update Vercel environment variables:
```bash
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
NEXT_PUBLIC_WS_URL=wss://your-backend.onrender.com
```

---

## Tech Stack

### Backend
- **Framework:** FastAPI (async, auto-docs)
- **Agent Orchestration:** LangGraph (state machines)
- **LLMs:** Ollama (local dev), Groq (cloud production)
- **Search:** Tavily API (primary), DuckDuckGo (fallback)
- **Search Caching:** Redis (cloud-hosted)
- **Web Scraping:** BeautifulSoup4, requests
- **RAG Integration:** Project 1 Enterprise RAG API

### Frontend
- **Framework:** Next.js 16 (App Router, Turbopack)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Real-Time:** WebSocket client
- **Deployment:** Vercel

### Free Tier Services
- **Groq:** 30 requests/min (LLM)
- **Tavily:** 500/month (search - protected by Redis caching)
- **Redis Cloud:** Free tier available (search result caching)
- **Render:** 750 hours/month (backend)
- **Vercel:** Unlimited (frontend)

**Total Cost:** $0/month

---

## Project Structure

```
multi-agent-research/
├── backend/
│   ├── app/
│   │   ├── agents/                    # Agent implementations
│   │   │   ├── state.py               # MarketResearchState schema with Literal types
│   │   │   ├── state_utils.py         # Timestamp & state helper functions
│   │   │   ├── base.py                # BaseAgent with retry, HITL, cost tracking
│   │   │   ├── coordinator.py         # Strategic planning with JSON output
│   │   │   ├── web_research.py        # Web search + scraping + RAG
│   │   │   ├── financial_intel.py     # Financial data research
│   │   │   ├── data_analyst.py        # SWOT + comparisons
│   │   │   ├── fact_checker.py        # Validation + HITL gate
│   │   │   ├── content_synthesizer.py # Report generation (2 LLM calls)
│   │   │   ├── data_viz.py            # Chart.js specifications
│   │   │   ├── graph.py               # LangGraph with parallel execution
│   │   │   └── tools/                 # Agent tools
│   │   │       ├── search.py          # Tavily, DuckDuckGo, Redis cache
│   │   │       └── rag_client.py      # Project 1 integration
│   │   ├── api/
│   │   │   ├── schemas.py             # Pydantic models + HITL schemas
│   │   │   └── websocket.py           # WebSocket manager + HITL messages
│   │   ├── core/
│   │   │   ├── config.py              # Settings with validation
│   │   │   ├── llm.py                 # LLM manager (Ollama/Groq)
│   │   │   └── tokens.py              # tiktoken utilities
│   │   ├── services/
│   │   │   ├── cache.py               # Redis search result caching
│   │   │   └── hitl_manager.py        # Human-in-the-Loop approval manager
│   │   └── main.py                    # FastAPI app with rate limiting
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx               # Home (research form)
│   │   │   └── research/
│   │   │       └── [sessionId]/page.tsx  # Live monitoring + results
│   │   ├── components/
│   │   │   ├── AgentCard.tsx          # Agent status card
│   │   │   ├── AgentCardSkeleton.tsx  # Loading skeletons
│   │   │   ├── ChartRenderer.tsx      # Chart.js renderer
│   │   │   └── ApprovalModal.tsx      # HITL approval UI
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts        # WebSocket client + HITL
│   │   └── utils/
│   │       └── pdfExport.ts           # PDF generation with charts
│   └── package.json
│
├── render.yaml                         # Render deployment config
├── README.md                           # User documentation
└── SYSTEM-KNOWLEDGE.md                 # Technical deep dive
```

---

## How It Works

### Workflow Execution

```
1. User submits query + companies → Frontend
2. Frontend POST /api/research → Backend (rate-limited: 5/min)
3. Backend creates session_id, returns immediately (<100ms)
4. Frontend connects WebSocket, receives live updates
5. LangGraph executes agents with parallel optimization:

   Coordinator Agent (10s)
   ↓ Generates strategic guidance (JSON):
     - research_objectives (what questions to answer)
     - search_priorities (keywords per company)
     - financial_priorities (metrics to collect)
     - comparison_angles (dimensions to compare)
     - depth_settings (light/standard/comprehensive per agent)

   ┌─────────────────────┴────────────────────┐
   │       PARALLEL STAGE 1: Research         │
   ├─────────────────────┬────────────────────┤
   Web Research (40s)    Financial Intel (30s)
   - Uses search_priorities from coordinator
   - Redis cache check first (5-10x speedup)
   - Depth-based search volume
   - Web scraping (comprehensive depth)
   - RAG integration
   ↓                     ↓
   └─────────────────────┬────────────────────┘
                         │ (Both complete)
   Data Analyst Agent (20s)
   ↓ Combines web + financial data
   ↓ Uses coordinator's comparison_angles
   ↓ Depth-based sections (light/standard/comprehensive)

   Fact Checker Agent (15s)
   ↓ Validates claims
   ↓ HITL Gate: If issues detected →
     - Pauses workflow
     - Modal appears with report preview
     - User decides: Continue or Stop
     - Workflow resumes or ends based on decision

   ┌─────────────────────┴────────────────────┐
   │       PARALLEL STAGE 2: Output           │
   ├─────────────────────┬────────────────────┤
   Content Synth (20s)   Data Viz (15s)
   - Uses objectives      - Generates Chart.js
   - 2 LLM calls          - Bar/Line/Pie/Doughnut
   ↓                     ↓
   └─────────────────────┬────────────────────┘
                         │
   Final Report Complete (105 seconds total)

6. Backend sends workflow_complete via WebSocket
7. Frontend displays: strategy, results, charts, downloads

Total Time: 105 seconds (1.75 minutes) - 30% faster than sequential!
WebSocket: Real-time updates at every step
```

### State Management

All agents share a single `MarketResearchState` (TypedDict) that accumulates:
- **Strategic guidance** (coordinator's objectives, priorities, angles, depth settings)
- Research findings (Web + Financial, uses operator.add for parallel-safe accumulation)
- Competitor profiles (web research data)
- Financial data (funding, revenue, growth)
- Comparative analysis (SWOT, feature matrix, positioning)
- Fact-check results (with operator.add)
- Final report + executive summary
- Visualizations (Chart.js specs, with operator.add)
- **Active agents** (current_agent: List[str] with operator.add - shows which agents are running, including parallel pairs)
- **Cost tracking** (cost_tracking: List[Dict] with operator.add - per-agent cost info from all 7 agents)
- Errors (with operator.add for parallel error collection)
- HITL state (pending approvals, responses)

**operator.add pattern:** Fields marked with `Annotated[List[T], operator.add]` automatically concatenate when multiple agents write to them in parallel. Critical for parallel execution:
- `current_agent` accumulates all active agents (shows "2 agents running" during parallel stages)
- `cost_tracking` preserves costs from all agents including those running in parallel
- `errors` collects errors from any parallel agent without overwriting
- `research_findings`, `fact_check_results`, `visualizations` all use this pattern

LangGraph passes state through the workflow, each agent reads coordinator's guidance and updates relevant fields.

---

## Example Output

**Input:**
```
Query: "Compare Notion vs Coda vs ClickUp for project management"
Companies: ["Notion", "Coda", "ClickUp"]
```

**Output (Generated Report):**

### Executive Summary
Notion, Coda, and ClickUp are leading project management platforms offering collaborative workspaces. Notion leads in customization and knowledge management, Coda excels in document-database hybrid capabilities, and ClickUp provides comprehensive task management features. Pricing varies from free tiers to enterprise plans.

### Comparative Analysis
[Feature comparison matrix, SWOT for each, market positioning]

### Visualizations
- Feature comparison radar chart
- Pricing scatter plot
- Market positioning matrix

### Sources
[15+ URLs from Tavily, DuckDuckGo, scraped websites]

---

## Development

### Run Tests

```bash
cd backend
pytest tests/
```

### Test API

```bash
# Health check
curl http://localhost:8000/health

# Full workflow test
python test_api.py
```

### WebSocket Testing

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/research/session-id-here");
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```

---

## Environment Variables

### Backend (.env)

```bash
# LLM Configuration
GROQ_API_KEY=your_groq_key              # Required for production
OLLAMA_BASE_URL=http://localhost:11434  # For local development

# Search APIs
TAVILY_API_KEY=your_tavily_key          # Required for quality search

# Redis (Search Result Caching)
REDIS_URL=your_upstash_redis_url        # Optional, uses in-memory fallback

# RAG Integration (Project 1)
RAG_API_URL=https://enterprise-rag-api.onrender.com/api

# Application
ENVIRONMENT=development  # or 'production'
LOG_LEVEL=INFO
MAX_PARALLEL_AGENTS=2   # Used for parallel execution stages
AGENT_TIMEOUT=120       # Timeout per agent in seconds
CACHE_TTL=3600          # Search cache TTL (1 hour)
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000           # Dev
# NEXT_PUBLIC_API_URL=https://your-backend.onrender.com  # Production

NEXT_PUBLIC_WS_URL=ws://localhost:8000              # Dev
# NEXT_PUBLIC_WS_URL=wss://your-backend.onrender.com     # Production
```

---

## Cost Analysis

| Service | Free Tier | Usage | Cost |
|---------|-----------|-------|------|
| **Groq API** | 30 req/min | LLM inference | $0 |
| **Tavily** | 500/month | Web search (with Redis caching to save quota) | $0 |
| **Redis Cloud** | Free tier (varies by provider) | Search result caching (1-hour TTL) | $0 |
| **Render** | 750 hrs/month | Backend hosting | $0 |
| **Vercel** | Unlimited | Frontend hosting | $0 |
| **Ollama** | Unlimited | Local dev LLM | $0 |
| **Total** | | | **$0/month** |

**Quota Protection:**
- Rate limiting: 5 research requests/minute (prevents quota exhaustion)
- Redis caching: 5-10x speedup on repeated queries, saves Tavily searches
- Coordinator depth settings: Light queries use fewer API calls

---

## Features Roadmap

### ✅ Completed (Production-Ready)
- [x] 7 specialized agents with distinct roles
- [x] LangGraph orchestration with parallel execution (2 stages, 30% speedup)
- [x] Strategic coordinator with JSON-structured guidance
- [x] Coordinator-driven agent behavior (priorities, objectives, angles, depth)
- [x] FastAPI backend with rate limiting (5 req/min)
- [x] WebSocket real-time monitoring
- [x] Next.js 16 frontend (App Router, Turbopack)
- [x] Redis search result caching (5-10x speedup)
- [x] Accurate token counting (tiktoken with model auto-detection)
- [x] Per-company and per-call cost tracking
- [x] RAG integration (Project 1 Enterprise RAG)
- [x] Human-in-the-Loop (HITL) approval gates with quality detection
- [x] Chart rendering (Chart.js: bar, line, pie, doughnut)
- [x] PDF export with embedded charts (jsPDF + html2canvas)
- [x] Loading skeletons for better UX
- [x] Configuration validation (fail-fast on startup)
- [x] Depth-based research (light/standard/comprehensive)
- [x] Web scraping for comprehensive depth
- [x] Docker deployment
- [x] Vercel deployment
- [x] Zero deprecation warnings
- [x] Zero bare except blocks
- [x] Zero dead code

### 🔄 Future Enhancements
- [ ] Qdrant vector storage for historical research (semantic search of past research)
- [ ] Agent performance A/B testing (compare LLM models, prompt variations)
- [ ] Workflow templates (pre-configured for specific industries)
- [ ] Multi-language support (research in non-English markets)
- [ ] Email report delivery (schedule research, receive via email)
- [ ] API authentication (user accounts, usage tracking)

---

## Deployment Instructions

### Backend (Render)

**Option A: One-Click Deploy (render.yaml)**
1. Fork/clone this repo
2. Visit https://dashboard.render.com/select-repo
3. Select `multi-agent-research`
4. Render auto-detects `render.yaml`
5. Add environment variables (GROQ_API_KEY, TAVILY_API_KEY)
6. Deploy!

**Option B: Manual Deploy**
1. New Web Service on Render
2. Connect GitHub repo
3. Settings:
   - **Runtime:** Docker
   - **Dockerfile Path:** ./backend/Dockerfile
   - **Docker Context:** ./backend
4. Add environment variables
5. Deploy

**Environment variables to add:**
- `GROQ_API_KEY` (required)
- `TAVILY_API_KEY` (required)
- `REDIS_URL` (optional, your Redis connection URL)
- `ENVIRONMENT=production`

### Frontend (Vercel)

Already deployed! Update after backend deployment:

```bash
# In Vercel dashboard, add these environment variables:
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
NEXT_PUBLIC_WS_URL=wss://your-backend.onrender.com

# Then redeploy:
cd frontend
vercel --prod --yes
```

---

---

## Performance & Optimization

### Speed Optimizations (30% Faster Than Sequential)
- **Parallel execution:** 2 stages run concurrently (Research + Output phases)
  - Stage 1: Web Research + Financial Intel (saves 30s)
  - Stage 2: Content Synthesizer + Data Viz (saves 15s)
  - Total: 105s vs 150s = 30% faster
- **Redis caching:** 5-10x speedup on repeated queries, 1-hour TTL
- **Depth-based execution:** Light queries skip unnecessary work
- **LLM fallback:** Ollama (dev) → Groq (prod) seamless switching
- **Web scraping:** Only for comprehensive depth (smart resource usage)

### Memory Optimization (512MB Render Free Tier)
- Lazy agent loading (agents created only when needed)
- Token-aware truncation (tiktoken prevents context overflow)
- Connection pooling (Redis, httpx)
- Parallel execution designed for memory safety (different state fields)
- Smart caching reduces redundant API calls

### Accuracy Optimizations
- **tiktoken integration:** 0% error vs 22.9% error with len//4 estimation
- **Model auto-detection:** Uses correct tokenizer (llama3 or llama-3.3-70b)
- **Per-company cost tracking:** Aggregates actual LLM calls (not approximations)
- **Per-call cost tracking:** Content Synthesizer tracks summary + report separately

---

## Testing

```bash
cd backend

# Run all tests
pytest

# Run specific tests
pytest tests/unit/
pytest tests/integration/

# Test API manually
python test_api.py
```

---

## Troubleshooting

### Backend won't start
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Or add GROQ_API_KEY to .env
- Check Python version: `python --version` (need 3.11+)

### Frontend won't connect
- Check API URL in .env.local
- Verify backend is running on correct port
- Check CORS settings in backend/app/main.py

### WebSocket not connecting
- Verify WebSocket URL (ws:// for http, wss:// for https)
- Check session_id is valid
- Look for errors in browser console

---

## Tech Highlights for Portfolio

**What Makes This Unique:**
- **7 specialized agents** with strategic coordinator that actually controls execution (not just documentation)
- **Parallel execution** at 2 stages using LangGraph (30% speedup, production-grade concurrency)
- **Strategic coordination pattern:** Coordinator generates JSON guidance (objectives, priorities, angles) that all downstream agents use
- **Human-in-the-Loop gates:** Quality-based workflow pausing with approval UI
- **Redis caching** for search results (5-10x speedup, quota protection)
- **Accurate token counting** with tiktoken and model auto-detection
- **Real-time WebSocket** with 6 message types (status, approval, completion, etc.)
- **Microservices integration** (Project 1 RAG API, Project 2 Multi-Agent)
- **Complete feature set:** Charts, PDF export, HITL, caching, rate limiting, validation
- **100% free tier** ($0/month production cost)
- **Zero technical debt:** No deprecations, no dead code, no bare excepts

**Interview Talking Points:**
- **Strategic multi-agent orchestration:** How coordinator guides 7 agents with structured parameters
- **Parallel execution in LangGraph:** Fan-out/fan-in patterns, operator.add for state merging
- **State management:** TypedDict with operator.add for parallel-safe accumulation
- **Cost optimization:** Free tier architecture with Redis caching, rate limiting, depth-based execution
- **Real-time communication:** WebSocket pub/sub, HITL approval flow, concurrent connection handling
- **Production patterns:** Retry logic, exponential backoff, timeout protection, graceful degradation
- **Microservice integration:** Async HTTP with httpx, error resilience, health checks
- **Token accuracy:** tiktoken integration, model auto-detection (llama3 vs llama-3.3-70b)
- **Quality gates:** HITL with keyword detection, approval timeout handling, workflow control
- **End-to-end system:** Backend (FastAPI/LangGraph) + Frontend (Next.js/Chart.js) + Caching (Redis) + RAG (Project 1)

---

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
