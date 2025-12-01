"""FastAPI application for multi-agent market research."""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .core.config import get_settings
from .api.schemas import ResearchRequest, ResearchResponse, HealthResponse
from .api.websocket import get_ws_manager
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
        # Keep connection alive and receive messages
        while True:
            data = await websocket.receive_text()
            # Echo back (can implement client commands here if needed)
            await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, session_id)


@app.post("/api/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest):
    """Start a research workflow.

    Args:
        request: Research request with query and companies

    Returns:
        Session ID to connect to WebSocket for real-time updates
    """
    import asyncio
    import uuid

    try:
        print(f">>> Starting research: {request.query}")
        print(f"Companies: {', '.join(request.companies)}")

        # Generate session ID
        session_id = str(uuid.uuid4())

        # Run research in background task
        async def run_in_background():
            try:
                final_state = await run_research(
                    query=request.query,
                    companies=request.companies,
                    analysis_depth=request.analysis_depth,
                    session_id=session_id
                )
                print(f">>> Research completed for session {session_id}")

                # Send final results via WebSocket
                await ws_manager.send_update(session_id, {
                    "type": "workflow_complete",
                    "session_id": session_id,
                    "status": "completed",
                    "data": {
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
            message=f"Research started for {len(request.companies)} companies. Connect to WebSocket for updates.",
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
