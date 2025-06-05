from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.exceptions import HTTPException

import datasense as ds
from config import get_settings, setup_logging
from datasense_types import UserMessage
from search import SearchService

from database import VectorStore  # Assuming VectorStore class is in database.py
import asyncio  # You might need this if your setup logic uses async features directly,

# but @app.on_event("startup") handles the async context
from gemini import active_connections


app = FastAPI()
logger = setup_logging()


@app.on_event("startup")
async def startup_db_client():
    print("Running application startup tasks...")
    try:
        app.state.vector_store = await VectorStore.create()
        search_settings = get_settings().search_engine
        app.state.search_engine = await SearchService.create(
            project_id=search_settings.project_number,
            location=search_settings.location,
            engine_id=search_settings.engine_id,
        )

    except Exception as e:
        print(f"CRITICAL: Error during async client initialization: {e}")


# --- You might want a shutdown event to close connections cleanly ---
# @app.on_event("shutdown")
# async def shutdown_db_client():
#     if hasattr(app.state, 'db') and app.state.db:
#         print("Closing database connection...")
#         # Assuming your db object has a close method or similar
#         # await app.state.db.close() # Example: Adjust based on your db library
#         print("Database connection closed.")


# Static
app.mount("/static", StaticFiles(directory="static"), name="static")


print("Datasense Server starting up.")
print("Project: ", get_settings().llm.gcp_project)
print("Location: ", get_settings().llm.gcp_location)
print("Model: ", get_settings().llm.gcp_model)
print("Temperature: ", get_settings().llm.model_temperature)
print("Top P: ", get_settings().llm.model_top_p)
print("Max Output Tokens: ", get_settings().llm.model_max_output_tokens)
print("System Instruction: ", get_settings().llm.system_instruction)


@app.get("/")
async def root():
    with open(f"static/index.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(content="Error loading index.html", status_code=500)


@app.post("/chat")
async def post_chat(user_message: UserMessage):
    """
    Takes user input. Gets Gemini response.
    Returns normal response immediately and processes premium response asynchronously if applicable.
    """
    try:
        return await ds.chat_response(
            user_message.chatHistory,
            user_message.message,
            user_message.clientId,
            app.state.vector_store,
            app.state.search_engine,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
async def reset_chat():
    """
    Reset
    """
    return {"message": "reset!"}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    print(f"Client ID: {client_id} and websocket: {websocket}")
    active_connections[client_id] = websocket

    try:
        while True:
            # await ds.premium_response()

            data = await websocket.receive_text()
            print(f"Received data: {data}")
            # Keep connection alive
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if client_id in active_connections:
            print(f"Client ID: {client_id} disconnected")
            active_connections.pop(client_id, None)
            print(f"Active connections: {active_connections}")

    # for i in range(5):
    #     await asyncio.sleep(1)
    #     await websocket.send_text(f"Progress: {i * 20}%")
    # await websocket.send_text("Done!")
    # await websocket.close()
