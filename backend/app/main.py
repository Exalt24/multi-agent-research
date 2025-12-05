"""FastAPI application for multi-agent market research."""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .core.config import get_settings
from .api.schemas import ResearchRequest, ResearchResponse, HealthResponse, ApprovalResponse
from .api.websocket import get_ws_manager
from .agents.graph import run_research
from .services.cache import search_cache
from .services.hitl_manager import hitl_manager
from .core.llm import llm_health_check
import uvicorn

settings = get_settings()

# Rate limiter (protects free tier quotas)
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI app."""
    # Startup
    print(">>> Multi-Agent Research Platform starting...")
    print(f"Environment: {settings.environment}")

    # Validate configuration
    try:
        settings.validate_requirements()
        print("[OK] Configuration validated successfully")
    except ValueError as e:
        print(f"[ERROR] Configuration validation failed:\n{e}")
        raise

    print(f"LLM: {'Ollama (local)' if settings.use_ollama else 'Groq (cloud)'}")

    # Show cache status
    cache_stats = search_cache.get_stats()
    print(f"Cache: {cache_stats['cache_type']} ({'Redis connected' if cache_stats['redis_connected'] else 'In-memory fallback'})")

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

# Add rate limiter state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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


@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get search cache statistics.

    Returns cache hit rate, entries, and connection status.
    Useful for monitoring cache performance and Tavily quota savings.
    """
    return search_cache.get_stats()


@app.get("/api/llm/health")
async def get_llm_health():
    """Check LLM provider availability and configuration.

    Returns which LLM providers are configured and available.
    Useful for debugging LLM connection issues.
    """
    return llm_health_check()


@app.post("/api/approval/respond")
async def submit_approval(approval: ApprovalResponse):
    """Submit user response to an approval request.

    Args:
        approval: User's approval decision

    Returns:
        Success status
    """
    success = hitl_manager.submit_approval_response(
        session_id=approval.session_id,
        approval_id=approval.approval_id,
        decision=approval.decision,
        feedback=approval.feedback
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Approval request {approval.approval_id} not found"
        )

    # Notify via WebSocket that approval was received
    ws_manager = get_ws_manager()
    await ws_manager.send_update(approval.session_id, {
        "type": "approval_received",
        "approval_id": approval.approval_id,
        "decision": approval.decision
    })

    return {"status": "success", "message": "Approval received"}


@app.get("/api/approval/pending/{session_id}")
async def get_pending_approvals(session_id: str):
    """Get all pending approval requests for a session.

    Args:
        session_id: Research session ID

    Returns:
        List of pending approvals
    """
    approvals = hitl_manager.get_pending_approvals(session_id)
    return {"session_id": session_id, "pending_approvals": approvals}


@app.websocket("/ws/research/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time research updates.

    Args:
        websocket: WebSocket connection
        session_id: Research session ID to monitor
    """
    ws_manager = get_ws_manager()
    await ws_manager.connect(websocket, session_id)

    try:
        # Keep connection alive and listen for disconnect
        while True:
            data = await websocket.receive_text()
            # Client messages are currently not used (updates are server-initiated)
            # Future: Could implement commands like "pause", "cancel", "resume"
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, session_id)


@app.post("/api/research", response_model=ResearchResponse)
@limiter.limit("5/minute")  # Limit to 5 research requests per minute (protects Tavily quota)
async def start_research(body: ResearchRequest, request: Request):
    """Start a research workflow.

    Args:
        body: Research request with query and companies
        request: FastAPI Request object (required for rate limiting - must be named 'request')

    Returns:
        Session ID to connect to WebSocket for real-time updates

    Rate Limit:
        5 requests per minute per IP address.
        Protects Tavily API quota (500 searches/month free tier).
    """
    import asyncio
    import uuid

    try:
        print(f">>> Starting research: {body.query}")
        print(f"Companies: {', '.join(body.companies)}")

        # Get WebSocket manager
        ws_manager = get_ws_manager()

        # Generate session ID
        session_id = str(uuid.uuid4())

        # Run research in background task
        async def run_in_background():
            try:
                # Send initial "workflow started" message
                await ws_manager.send_update(session_id, {
                    "type": "workflow_started",
                    "session_id": session_id,
                    "status": "started",
                    "message": "Research workflow initiated"
                })

                final_state = await run_research(
                    query=body.query,
                    companies=body.companies,
                    analysis_depth=body.analysis_depth,
                    session_id=session_id
                )
                print(f">>> Research completed for session {session_id}")

                # Send final results via WebSocket
                await ws_manager.send_update(session_id, {
                    "type": "workflow_complete",
                    "session_id": session_id,
                    "status": "completed",
                    "data": {
                        "research_plan": final_state.get("research_plan", ""),
                        "competitor_profiles": final_state.get("competitor_profiles", {}),
                        "comparative_analysis": final_state.get("comparative_analysis", {}),
                        "executive_summary": final_state.get("executive_summary", ""),
                        "final_report": final_state.get("final_report", ""),
                        "visualizations": final_state.get("visualizations", []),
                        "cost_tracking": final_state.get("cost_tracking", {})
                    }
                })
            except Exception as e:
                print(f">>> Research failed for session {session_id}: {e}")
                await ws_manager.send_update(session_id, {
                    "type": "workflow_failed",
                    "session_id": session_id,
                    "error": str(e)
                })

        # Start background task
        asyncio.create_task(run_in_background())

        # Return immediately with session ID
        return ResearchResponse(
            session_id=session_id,
            status="started",
            message=f"Research started for {len(body.companies)} companies. Connect to WebSocket for updates.",
            data={}
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
