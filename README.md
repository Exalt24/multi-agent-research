# Multi-Agent Market Research Platform

**AI-powered competitive intelligence using 7 specialized agents orchestrated with LangGraph**

🔗 **Live Demo (Frontend):** https://frontend-g5urynyrg-exalt24s-projects.vercel.app
📘 **GitHub:** https://github.com/Exalt24/multi-agent-research

---

## Overview

A production-ready multi-agent AI system that automates market research and competitive analysis. Seven specialized agents work together to gather data, analyze competitors, validate findings, and generate comprehensive reports with visualizations.

### Key Metrics
- **Time Reduction:** Manual research 6-8 hours → Agent system 2-3 minutes (100x+ faster)
- **Agents:** 7 specialized agents with distinct roles
- **Cost:** $0/month (free tier APIs: Tavily, Groq, Upstash Redis)
- **Real-Time:** WebSocket monitoring of agent execution
- **Tech Stack:** LangGraph, FastAPI, Next.js, Ollama/Groq

---

## The 7 Agents

| Agent | Role | Tools Used |
|-------|------|------------|
| **Coordinator** | Plans workflow and manages execution | LLM reasoning |
| **Web Research** | Gathers competitive intelligence | Tavily, DuckDuckGo, web scraping, RAG API |
| **Financial Intelligence** | Researches funding, valuations, growth | Tavily, DuckDuckGo |
| **Data Analyst** | Creates SWOT, feature comparisons | LLM analysis |
| **Fact Checker** | Validates claims, confidence scoring | Cross-referencing, LLM |
| **Content Synthesizer** | Writes executive summary + full report | LLM generation |
| **Data Visualization** | Generates chart specifications | LLM recommendations |

---

## Architecture

```
┌────────────────────────────────────────────────────┐
│                   User Input                       │
│          "Compare Notion vs Coda vs ClickUp"       │
└──────────────────┬─────────────────────────────────┘
                   │
                   v
┌──────────────────────────────────────────────────┐
│              FastAPI Backend                      │
│         (LangGraph Workflow Engine)               │
└──────────────────┬───────────────────────────────┘
                   │
      ┌────────────┴────────────┐
      v                         v
┌─────────────┐         ┌──────────────┐
│ Coordinator │         │  WebSocket   │
│   Agent     │         │   Manager    │
└──────┬──────┘         └──────┬───────┘
       │                       │
       v                       │ (Real-time updates)
┌──────────────────┐           │
│  Web Research    │◄──────────┤
│     Agent        │           │
└────────┬─────────┘           │
         │                     │
         v                     │
┌──────────────────┐           │
│ Financial Intel  │◄──────────┤
│     Agent        │           │
└────────┬─────────┘           │
         │                     │
         v                     │
┌──────────────────┐           │
│  Data Analyst    │◄──────────┤
│     Agent        │           │
└────────┬─────────┘           │
         │                     │
         v                     │
┌──────────────────┐           │
│  Fact Checker    │◄──────────┤
│     Agent        │           │
└────────┬─────────┘           │
         │                     │
    ┌────┴────┐                │
    v         v                │
┌─────────┐ ┌──────────┐       │
│Content  │ │Data Viz  │◄──────┤
│Synth.   │ │  Agent   │       │
└────┬────┘ └────┬─────┘       │
     └──────┬────┘             │
            v                  v
     ┌──────────────┐    ┌──────────┐
     │ Final Report │    │ Frontend │
     └──────────────┘    │ (Real-   │
                         │  time    │
                         │  UI)     │
                         └──────────┘
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

✅ **Multi-Agent Orchestration**
- 7 specialized agents working together
- LangGraph state management
- Sequential + parallel execution (future)
- Error handling and retries

✅ **Intelligent Research**
- Web search (Tavily + DuckDuckGo)
- Web scraping and content extraction
- Financial data gathering
- RAG integration (Project 1 knowledge base)

✅ **Comprehensive Analysis**
- SWOT analysis per company
- Feature comparison matrix
- Market positioning insights
- Pricing comparisons
- Fact-checking with confidence scores

✅ **Professional Output**
- Executive summary (2-3 paragraphs)
- Detailed markdown report
- Chart specifications (Chart.js format)
- Source attribution

✅ **Real-Time Monitoring**
- WebSocket live updates
- Agent status tracking
- Progress bars per agent
- Cost tracking

✅ **Production Features**
- Cost tracking (tokens, estimated $)
- Error handling with retries
- State persistence (Redis)
- Health check endpoint
- Docker deployment

---

## API Endpoints

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/research` | Start research workflow |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `WS /ws/research/{session_id}` | Real-time agent updates |

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

**Already deployed!** https://frontend-g5urynyrg-exalt24s-projects.vercel.app

To redeploy:
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
- **State Persistence:** Redis (Upstash Cloud)
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
- **Tavily:** 1,000/month (search)
- **Upstash Redis:** 10K commands/day (state)
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
│   │   │   ├── state.py               # MarketResearchState schema
│   │   │   ├── base.py                # BaseAgent class
│   │   │   ├── coordinator.py         # Workflow planning
│   │   │   ├── web_research.py        # Web search + scraping
│   │   │   ├── financial_intel.py     # Financial data
│   │   │   ├── data_analyst.py        # SWOT + comparisons
│   │   │   ├── fact_checker.py        # Validation
│   │   │   ├── content_synthesizer.py # Report generation
│   │   │   ├── data_viz.py            # Chart specs
│   │   │   ├── graph.py               # LangGraph workflow
│   │   │   └── tools/                 # Agent tools
│   │   │       ├── search.py          # Tavily, DuckDuckGo
│   │   │       └── rag_client.py      # RAG integration
│   │   ├── api/
│   │   │   ├── schemas.py             # Pydantic models
│   │   │   └── websocket.py           # WebSocket manager
│   │   ├── core/
│   │   │   ├── config.py              # Settings
│   │   │   ├── llm.py                 # LLM manager
│   │   │   └── checkpointer.py        # State persistence
│   │   └── main.py                    # FastAPI app
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
│   │   │       └── [sessionId]/page.tsx  # Agent monitoring
│   │   ├── components/
│   │   │   └── AgentCard.tsx          # Agent status card
│   │   └── hooks/
│   │       └── useWebSocket.ts        # WebSocket client
│   └── package.json
│
├── render.yaml                         # Render deployment config
└── README.md
```

---

## How It Works

### Workflow Execution

```
1. User submits query + companies → Frontend
2. Frontend POST /api/research → Backend
3. Backend creates session_id, initializes state
4. LangGraph executes agents sequentially:

   Coordinator Agent
   ↓ (plans workflow)
   Web Research Agent
   ↓ (searches Tavily/DuckDuckGo, scrapes websites, queries RAG)
   Financial Intelligence Agent
   ↓ (gathers funding, growth, team data)
   Data Analyst Agent
   ↓ (creates SWOT, feature matrix, comparisons)
   Fact Checker Agent
   ↓ (validates claims, assigns confidence scores)
   Content Synthesizer Agent
   ↓ (writes executive summary + full report)
   Data Visualization Agent
   ↓ (generates Chart.js specifications)
   Final Report Complete

5. Backend returns complete research to frontend
6. Frontend displays results

WebSocket: All agents emit real-time status updates during execution
```

### State Management

All agents share a single `MarketResearchState` (TypedDict) that accumulates:
- Research findings (Web + Financial)
- Competitor profiles
- Comparative analysis
- Fact-check results
- Final report
- Visualizations
- Cost tracking
- Errors

LangGraph passes state through the workflow, each agent reads and updates it.

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

# Redis (State Persistence)
REDIS_URL=your_upstash_redis_url        # Optional, uses memory fallback

# RAG Integration
RAG_API_URL=https://enterprise-rag-api.onrender.com/api

# Application
ENVIRONMENT=development  # or 'production'
LOG_LEVEL=INFO
MAX_PARALLEL_AGENTS=2
AGENT_TIMEOUT=120
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
| **Tavily** | 1,000/month | Web search | $0 |
| **Upstash Redis** | 10K cmd/day | State persistence | $0 |
| **Render** | 750 hrs/month | Backend hosting | $0 |
| **Vercel** | Unlimited | Frontend hosting | $0 |
| **Ollama** | Unlimited | Local dev LLM | $0 |
| **Total** | | | **$0/month** |

---

## Features Roadmap

### ✅ Completed
- [x] 7 specialized agents
- [x] LangGraph orchestration
- [x] FastAPI backend
- [x] WebSocket real-time monitoring
- [x] Next.js frontend
- [x] State persistence (Redis)
- [x] Cost tracking
- [x] RAG integration (Project 1)
- [x] Docker deployment
- [x] Vercel deployment

### 🔄 Future Enhancements
- [ ] Human-in-the-Loop (HITL) approval gates
- [ ] Parallel agent execution (LangGraph Send API)
- [ ] Qdrant vector storage for historical research
- [ ] Chart rendering (Chart.js integration)
- [ ] Export reports (PDF, DOCX)
- [ ] Agent performance A/B testing
- [ ] Workflow templates (pre-configured use cases)

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
- `REDIS_URL` (optional, your Upstash URL)
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

## Integration with Project 1 (Enterprise RAG)

This platform integrates with the Enterprise RAG Knowledge Base:
- **Agent:** Web Research Agent
- **Use Case:** Queries existing knowledge before web search
- **API Endpoint:** `https://enterprise-rag-api.onrender.com/api/query`
- **Benefit:** Reduces redundant searches, leverages historical data

**Microservices Architecture:** Agents can call Project 1's RAG API as a tool, demonstrating composable AI systems.

---

## Performance & Optimization

### Memory Optimization (512MB Render Free Tier)
- Lazy agent loading
- Streaming LLM responses
- Connection pooling (Redis)
- Sequential execution (reduces concurrent memory)

### Speed Optimizations
- Redis caching for repeated queries
- LLM fallback (Ollama → Groq)
- Parallel search queries where possible
- Efficient state management

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
- 7 agents (most tutorials show 2-3)
- LangGraph state machines (production pattern)
- Real-time WebSocket monitoring
- Microservices integration (RAG API)
- 100% free tier ($0/month)
- Production-ready (Docker, health checks, error handling)

**Interview Talking Points:**
- Multi-agent orchestration strategies
- State management in distributed systems
- Cost optimization (free tier architecture)
- Real-time communication (WebSocket)
- Error handling and retries in AI systems

---

## Credits

Built by Daniel Alexis Cruz as Project 2 in AI Automation Portfolio

**Related Projects:**
- [Project 1: Enterprise RAG Knowledge Base](https://github.com/Exalt24/enterprise-rag-knowledge-base)

---

## License

MIT
