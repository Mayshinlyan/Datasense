"""
DataSense Library
"""
from typing import List, Dict
from gemini import generate, Response
from google.genai.types import Part, Content
from config import setup_logging
from search import SearchService

logger = setup_logging()


async def chat_response(history_obj: List[Dict], user_input: str, vector_store, search_engine: SearchService) -> Response:
    """
    Takes user input. Gets Gemini response.
    """
    content_history: List[Content] = []
    for item in history_obj:
        if item['role'] == 'user':
            content_history.append(Content(role='user', parts=[Part.from_text(text=item['content'])]))
        elif item['role'] == 'assistant':
            content_history.append(Content(role='assistant', parts=[Part.from_text(text=item['content'])]))

    logger.info(f"datasense.py: Content history prepared with {len(content_history)} turns.")
    try:
       response = await generate(content_history, user_input, vector_store, search_engine)
       logger.info(f"datasense.py: Gemini response generated successfully.", extra={"response": response})
    except Exception as e:
        logger.error(f"datasense.py: Error generating response: {e}")
        raise e
    logger.info(f"datasense.py: Gemini response received.") 

    return response
