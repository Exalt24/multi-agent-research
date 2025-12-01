# Multi-Agent Market Research Platform

AI-powered competitive intelligence system using 7 specialized agents orchestrated with LangGraph.

## Status: 🚧 In Development (Vertical Slice Complete)

**Current Progress:** Web Research Agent working end-to-end

## Quick Start

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys (GROQ_API_KEY, TAVILY_API_KEY optional)

# Run server
python -m app.main
```

Server runs at: `http://localhost:8000`

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Run test script
python test_api.py
```

## Current Features (Vertical Slice)

✅ **Core Infrastructure:**
- FastAPI backend with async support
- LangGraph state management
- Ollama + Groq LLM fallback
- Redis/Memory checkpointer

✅ **Web Research Agent:**
- Tavily search (primary, requires API key)
- DuckDuckGo search (fallback, free)
- Web scraping with BeautifulSoup
- RAG integration (queries Project 1 knowledge base)
- LLM analysis with structured output

✅ **Working Endpoints:**
- `GET /health` - Health check
- `POST /api/research` - Start research workflow

## Architecture

```
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  LangGraph      │
│  Workflow       │
└────────┬────────┘
         │
         v
┌──────────────────────────┐
│  Web Research Agent      │
│  - Tavily Search         │
│  - DuckDuckGo Search     │
│  - Web Scraping          │
│  - RAG Integration       │
│  - LLM Analysis          │
└──────────────────────────┘
```

## Environment Variables

```bash
# Required
GROQ_API_KEY=your_key_here          # For cloud LLM (or use Ollama locally)

# Optional
TAVILY_API_KEY=your_key_here        # Better search quality (fallback to DuckDuckGo)
OLLAMA_BASE_URL=http://localhost:11434  # For local LLM

# Auto-configured
RAG_API_URL=https://enterprise-rag-api.onrender.com/api  # Project 1 integration
```

## Example Request

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare Notion vs Coda vs ClickUp",
    "companies": ["Notion", "Coda", "ClickUp"],
    "analysis_depth": "standard"
  }'
```

## Next Steps

- [ ] Implement remaining 6 agents (Coordinator, Financial Intel, Data Analyst, Fact Checker, Content Synthesizer, Data Viz)
- [ ] Complete LangGraph workflow with parallel/sequential execution
- [ ] Add HITL approval gates
- [ ] Build WebSocket real-time monitoring
- [ ] Create Next.js frontend
- [ ] Add comprehensive testing
- [ ] Deploy to Render + Vercel

## Tech Stack

**Backend:**
- FastAPI, LangChain, LangGraph, Pydantic
- Ollama + Groq (LLMs)
- Tavily + DuckDuckGo (search)
- Redis (state persistence)

**Frontend:**
- Next.js 16, TypeScript, Tailwind CSS

**Deployment:**
- Render (backend), Vercel (frontend)

## Project Structure

```
multi-agent-research/
├── backend/
│   ├── app/
│   │   ├── agents/           # Agent implementations
│   │   │   ├── state.py      # State schema
│   │   │   ├── base.py       # Base agent class
│   │   │   ├── web_research.py
│   │   │   ├── graph.py      # LangGraph workflow
│   │   │   └── tools/        # Search, RAG, etc.
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # Config, LLM, checkpointer
│   │   └── main.py           # FastAPI app
│   ├── tests/
│   ├── requirements.txt
│   └── .env
└── frontend/                 # Next.js app (not started yet)
```

## License

MIT
