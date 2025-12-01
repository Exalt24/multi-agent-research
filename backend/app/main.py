"""FastAPI application for multi-agent market research."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .core.config import get_settings
from .api.schemas import ResearchRequest, ResearchResponse, HealthResponse
from .agents.graph import run_research
import uvicorn

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI app."""
    # Startup
    print(">>> Multi-Agent Research Platform starting...")
    print(f"Environment: {settings.environment}")
    print(f"LLM: {'Ollama (local)' if settings.use_ollama else 'Groq (cloud)'}")

    yield

    # Shutdown
    print(">>> Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Market Research Platform",
    description="AI-powered competitive intelligence using 7 specialized agents",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Multi-Agent Research Platform is running"
    )


@app.post("/api/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest):
    """Start a research workflow.

    Args:
        request: Research request with query and companies

    Returns:
        Research results
    """
    try:
        print(f">>> Starting research: {request.query}")
        print(f"Companies: {', '.join(request.companies)}")

        # Run research workflow
        final_state = await run_research(
            query=request.query,
            companies=request.companies,
            analysis_depth=request.analysis_depth
        )

        # Check for errors
        errors = final_state.get("errors", [])
        if errors:
            error_messages = [e.get("error", "") for e in errors]
            raise HTTPException(
                status_code=500,
                detail=f"Research failed: {'; '.join(error_messages)}"
            )

        # Return results
        return ResearchResponse(
            session_id=final_state.get("session_id", ""),
            status="completed",
            message=f"Successfully researched {len(request.companies)} companies",
            data={
                "competitor_profiles": final_state.get("competitor_profiles", {}),
                "research_findings": final_state.get("research_findings", []),
                "cost_tracking": final_state.get("cost_tracking", {})
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Research error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )
