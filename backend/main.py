# backend/app/main.py
import logging
import asyncio
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .websocket import manager
from .agent_runner import run_research_task

# Configure logging for the FastAPI app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
logger = logging.getLogger("FastAPIApp")

app = FastAPI(title="Web Research Agent API")

# Configure CORS
origins = [
    "http://localhost:3000",  # Allow React dev server
    "http://127.0.0.1:3000",
    # Add your deployed frontend URL here if applicable
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    query: str

@app.post("/research")
async def start_research(request: ResearchRequest, http_request: Request):
    """
    Endpoint to initiate a research task.
    Triggers the agent in the background and returns immediately.
    Client needs to connect via WebSocket for updates.
    """
    client_ip = http_request.client.host if http_request.client else "unknown"
    logger.info(f"Received research request from {client_ip} for query: '{request.query}'")
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Generate a unique client/task ID for WebSocket tracking
    client_id = str(uuid.uuid4())
    logger.info(f"Generated client ID: {client_id}")

    # Start the research task in the background without awaiting it here
    asyncio.create_task(run_research_task(client_id, request.query))

    # Return the client_id so the frontend knows which WebSocket to connect to
    return {"message": "Research task started.", "client_id": client_id}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for streaming updates to the client."""
    await manager.connect(websocket, client_id)
    try:
        while True:
            # Keep the connection alive, waiting for messages (optional)
            # Or just handle disconnects
            # data = await websocket.receive_text() # Example: if frontend needs to send data
            # await manager.send_personal_message(f"Message text was: {data}", client_id)
            await asyncio.sleep(1) # Keep loop alive without busy-waiting
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}", exc_info=True)
        manager.disconnect(client_id)
        # Ensure the connection is closed if an unexpected error occurs
        try:
            await websocket.close()
        except Exception:
            pass # Ignore errors during close


@app.get("/")
async def read_root():
    return {"message": "Web Research Agent API is running."}

# Optional: Add lifespan management if needed for setup/teardown
# from contextlib import asynccontextmanager
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Load the ML model
#     print("Starting up...")
#     yield
#     # Clean up the ML model and release the resources
#     print("Shutting down...")
# app = FastAPI(lifespan=lifespan)

# --- How to run (from backend/ directory) ---
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000