"""
Helper functions to work with Gemini
"""

from google import genai
from google.genai import types, Client
from google.genai.types import Part, Content

from typing import List, Tuple, Union

from config import get_settings
from database import VectorStore
from synthesizer import Synthesizer
from pydantic import BaseModel, Field
from search import SearchService, Document
from dataclasses import dataclass, asdict

import logging, asyncio

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Response schema for normal Gemini answer
class GeminiAnswerResponse(BaseModel):
    answer: str = Field(description="The answer to the user's question")

# Response schema for Gemini classifier to determine if premium content is applicable
class GeminiClassifierResponse(BaseModel):
    premium_applicable: bool = Field(
        description=(
            "Set to true ONLY if the user's query is a request for substantive "
            "information, data, or analysis. Set to false for simple greetings "
            "or conversational filler."
        )
    )

@dataclass
class PremiumResponse:
    chat_history: List[Content]
    gemini_response: str
    video_file_links: str
    video_file_names: str
    thumbnail_links: str
    partner_names: str
    premium_response: Content = None
    premium_applicable: bool = False
    pdf_documents: List[Document] = None


@dataclass
class NormalResponse:
    chat_history: List[Content]
    gemini_response: str
    premium_applicable: bool = False

# Function to generate configuration for Gemini content generation
def generate_config(response_schema) -> types.GenerateContentConfig:
    """
    Generate configuration for Gemini content generation.
    """
    return types.GenerateContentConfig(
        temperature=get_settings().llm.model_temperature,
        system_instruction=get_settings().llm.system_instruction,
        response_mime_type="application/json",
        response_schema=response_schema,
    )

async def generate_answer(client: Client, chat_history: List[Content]) -> str:
    logger.info("Getting initial text answer from Gemini.")

    response = await client.aio.models.generate_content(
        model=get_settings().llm.gcp_model,
        contents=chat_history,
        config=generate_config(GeminiAnswerResponse),
    )
    return response.parsed.answer

async def is_premium_applicable(client: Client, chat_history: List[Content]) -> bool:
    logger.info("Getting 'premium_applicable' flag from Gemini.")
    user_question = chat_history[-1].parts[0].text

    classifier_prompt = (
        f"Analyze the following user query and determine if it is a request for "
        f"substantive information. User Query: \"{user_question}\""
    )

    response = await client.aio.models.generate_content(
        model=get_settings().llm.gcp_model,
        contents=[classifier_prompt],
        config=generate_config(GeminiClassifierResponse)
    )
    return response.parsed.premium_applicable


async def generate_normal_response(
    chat_history: List[Content],
    user_turn: Union[Content, str],
    client_id: str,
    vector_store: VectorStore,
    search_engine: SearchService,
) -> NormalResponse:
    """
    Normal Gemini response without RAG.
    """

    logger.info("Gemini.py: Generating response from Gemini model.")

    if isinstance(user_turn, str):
        user_turn_content = Content(role="user", parts=[Part.from_text(text=user_turn)])
    elif isinstance(user_turn, Content):
        user_turn_content = user_turn
    else:
        raise TypeError("user_turn must be of type Content or str")

    chat_history.append(user_turn_content)

    # ==== START: Normal Gemini Response without RAG ==== #

    # Configure the client and tool
    client = genai.Client(
        vertexai=True,
        project=get_settings().llm.gcp_project,
        location=get_settings().llm.gcp_location,
    )

    answer_task = asyncio.create_task(generate_answer(client, chat_history))
    premium_flag_task = asyncio.create_task(is_premium_applicable(client, chat_history))

    answer, premium_applicable = await asyncio.gather(answer_task, premium_flag_task)

    logger.info(f"Gemini.py: Normal Gemini response received. ")
    if premium_applicable:
        logger.info("Triggering background premium content generation flow.")
        asyncio.create_task(
            trigger_premium_flow(
                chat_history, user_turn_content, client_id, vector_store, search_engine
            )
        )

    return NormalResponse(
        chat_history=chat_history,
        gemini_response=answer,
        premium_applicable=premium_applicable,
    )


from typing import Dict
from fastapi import WebSocket
import json

# Global store for active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


async def trigger_premium_flow(
    chat_history: List[Content],
    user_turn_content: Content,
    client_id: str,
    vec: VectorStore,
    search_engine: SearchService,
):
    """
    Premium Gemini response with RAG.
    """
    # ==== START: Trigger this when the response is premium worthy ==== #
    logger.info(
        f"Gemini.py: Starting premium response generation for client {client_id}"
    )

    websocket = active_connections.get(client_id)

    logger.info(f"Gemini.py: Active connections: {websocket}")
    if not websocket:
        logger.error(
            f"Gemini.py: No active WebSocket connection found for client {client_id}"
        )
        return

    try:
        await websocket.send_text(
            json.dumps(
                {
                    "status": "premium_started",
                    "message": "Starting premium response generation...",
                }
            )
        )
    except Exception as e:
        logger.error(
            f"Gemini.py: Failed to send initial message to WebSocket for client {client_id}: {e}"
        )
        return

    try:
        user_question = user_turn_content.parts[0].text

        await websocket.send_text(json.dumps({"status": "searching", "message": "Searching for relevant documents and videos..."}))
        
        search_task = asyncio.create_task(search_engine.search(user_question))
        video_task = asyncio.to_thread(vec.similarity_search, user_question)

        documents, video_results = await asyncio.gather(search_task, video_task)
        await websocket.send_text(json.dumps({"status": "synthesizing", "message": "Synthesizing DataSense response..."}))
        try:
            response = await Synthesizer.generate_response(
                question=user_question, video_context=video_results, documents=documents
            )
            logger.info(f"gemini.py: Synthesized response received")

            premium_bot_answer = response.answer
            video_file_link = response.file_link
            video_file_name = response.file_name
            thumbnail_link = response.thumbnail_link
            partner_name = response.partner_name
            await websocket.send_text(
                json.dumps(
                    {
                        "status": "completed",
                        "data": {
                            "gemini_response": premium_bot_answer,
                            "video_file_links": video_file_link,
                            "video_file_names": video_file_name,
                            "thumbnail_links": thumbnail_link,
                            "partner_names": partner_name, 
                            "pdf_documents": [
                                asdict(doc) for doc in documents
                            ], 
                        },
                    }
                )
            )
        except (AttributeError, TypeError) as e:
            logger.error(f"Failed to parse Synthesizer response: {e}")
            await websocket.send_text(
                json.dumps(
                    {
                        "status": "error",
                        "message": "Failed to generate premium response",
                        "error": str(e),
                    }
                )
            )

    except Exception as e:
        logger.error(
            f"Gemini.py: Error during premium response generation for client {client_id}: {e}"
        )
        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "status": "error",
                        "message": "An error occurred during premium response generation",
                        "error": str(e),
                    }
                )
            )
        except Exception as ws_error:
            logger.error(
                f"Gemini.py: Failed to send error message to WebSocket for client {client_id}: {ws_error}"
            )
