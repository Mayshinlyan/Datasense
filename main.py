from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.exceptions import HTTPException

import datasense as ds
from config import get_settings
from datasense_types import UserMessage

from database import VectorStore # Assuming VectorStore class is in database.py
import asyncio # You might need this if your setup logic uses async features directly,
               # but @app.on_event("startup") handles the async context

app = FastAPI()

@app.on_event("startup")
async def startup_db_client():
    print("Running application startup tasks...")
    try:
        # This is the logic that was in your database.py's async def main()
        vec = VectorStore()
        app.state.vector_store = vec
        print("vector store initialized and stored in app.state.vector_store.")

    except Exception as e:
        print(f"Error during startup database initialization: {e}")
        # Depending on how critical this is, you might want to exit
        # import os
        # os._exit(1) # Force exit if DB is essential

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
    Validates if premium dataset applies to response, sets premium flag if so.
    """
    try:
        response = ds.chat_response(user_message.chatHistory, user_message.message, app.state.vector_store)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
async def reset_chat():
    """
    Reset
    """
    return {"message": "reset!"}