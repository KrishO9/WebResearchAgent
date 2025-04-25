# backend/app/agent_runner.py
import asyncio
import logging
import traceback
from typing import Callable, Coroutine

# Assuming AIAgent is directly inside backend/
from AIAgent.main import run_research as run_agent_research_logic
from AIAgent.utils.config import settings as agent_settings

from .websocket import manager

logger = logging.getLogger(__name__)

# Define message types
MSG_TYPE_LOG = "log"
MSG_TYPE_STATUS = "status"
MSG_TYPE_REPORT_CHUNK = "report_chunk"
MSG_TYPE_FINAL_REPORT = "final_report"
MSG_TYPE_SOURCES = "sources"
MSG_TYPE_ERROR = "error"

async def stream_message_to_client(client_id: str, message_type: str, data: dict):
    """Formats and sends a message via the WebSocket manager."""
    # Ensure data has a structure the frontend expects
    # Example: always include a 'message' field for logs/status
    payload = {"type": message_type, **data}
    if message_type in [MSG_TYPE_LOG, MSG_TYPE_STATUS, MSG_TYPE_ERROR] and 'message' not in data:
        payload['message'] = str(data) # Basic fallback
        logger.warning(f"Payload for type {message_type} missing 'message' field: {data}")

    await manager.send_personal_message(payload, client_id)

async def run_research_task(client_id: str, task: str):
    """
    Runs the research agent logic and streams updates/results to the client.
    """
    global_error = False
    final_report_content = ""
    try:
        logger.info(f"Starting research task '{task}' for client {client_id}")

        # Define the actual callback function to pass to the agent logic
        async def send_update_callback(level: str, msg_type: str, data: dict):
            """Callback for the agent logic to send updates."""
            # Map internal types/levels to WebSocket message types if needed
            # Example: Maybe agent uses "info" level, map to "log" type for WS
            websocket_message_type = msg_type # Default to using agent's type

            # Ensure data is a dictionary for consistency
            if not isinstance(data, dict):
                logger.warning(f"Callback received non-dict data for type {msg_type}: {data}. Wrapping.")
                data = {"content": data} # Wrap non-dict data

            # Add log level if it's a log message for frontend clarity
            if websocket_message_type == MSG_TYPE_LOG:
                data['level'] = level

            await stream_message_to_client(client_id, websocket_message_type, data)

        # --- REMOVE SIMULATION ---
        # --- CALL ACTUAL AGENT LOGIC ---
        logger.info("Invoking actual agent research logic...")
        # Pass the callback function to the agent's main execution function
        final_report_content = await run_agent_research_logic(
            task=task,
            send_update_callback=send_update_callback # Pass the actual callback
        )
        logger.info("Agent research logic finished.")
        # --- END ACTUAL CALL ---

        # If the agent logic doesn't explicitly send a final "done" status via callback,
        # send one from here. (It's better if the agent does it).
        # Example: await stream_message_to_client(client_id, MSG_TYPE_STATUS, {"status": "done", "message": "Research complete."})

    except Exception as e:
        global_error = True
        error_message = f"An error occurred during research task '{task}': {e}"
        tb_str = traceback.format_exc()
        logger.error(error_message, exc_info=True)
        logger.error(f"Traceback: {tb_str}")
        try:
            await stream_message_to_client(client_id, MSG_TYPE_ERROR, {"message": f"An internal server error occurred. Please check server logs. Error hint: {e}"})
            await stream_message_to_client(client_id, MSG_TYPE_STATUS, {"status": "error", "message": "Research failed."})
        except Exception as ws_error:
            logger.error(f"Failed to send error message to client {client_id}: {ws_error}")
    finally:
        logger.info(f"Finished research task execution wrapper for client {client_id}. Global Error: {global_error}")
        # Ensure the final 'done' or 'error' status was sent by the agent logic or send it here.
        # Example check (needs state management):
        # if not status_was_final:
        #    await stream_message_to_client(client_id, MSG_TYPE_STATUS, {"status": "error" if global_error else "done", "message": "Task execution finished."})