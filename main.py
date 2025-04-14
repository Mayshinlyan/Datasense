from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.exceptions import HTTPException

import datasense as ds
from datasenseconfig import datasenseconfig
from datasense_types import UserMessage

app = FastAPI()

# Static
app.mount("/static", StaticFiles(directory="static"), name="static")


print("Datasense Server starting up.")
print("Project: ", datasenseconfig.gcp_project)
print("Location: ", datasenseconfig.gcp_location)
print("Model: ", datasenseconfig.gcp_model)
print("Temperature: ", datasenseconfig.model_temperature)
print("Top P: ", datasenseconfig.model_top_p)
print("Max Output Tokens: ", datasenseconfig.model_max_output_tokens)
print("System Instruction: ", datasenseconfig.system_instruction)

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
        response = ds.chat_response(user_message.chatHistory, user_message.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
async def reset_chat():
    """
    Reset
    """
    return {"message": "reset!"}