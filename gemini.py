"""
Helper functions to work with Gemini
"""

from google import genai
from google.genai import types
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


# Response model for normal Gemini response
class GeminiResponse(BaseModel):
    thought_process: List[str] = Field(
        description="List of thoughts that the AI assistant had while forming the answer"
    )
    answer: str = Field(description="The answer to the user's question")
    premium_applicable: bool = Field(
        description="Set this as true if the user ask a question. If it is not a question, set it as false."
    )


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

    generate_content_config = types.GenerateContentConfig(
        temperature=get_settings().llm.model_temperature,
        system_instruction=get_settings().llm.system_instruction,
        response_mime_type="application/json",
        response_schema=GeminiResponse,
    )

    response = client.models.generate_content(
        model=get_settings().llm.gcp_model,
        contents=chat_history,
        config=generate_content_config,
    )

    result = response.parsed
    bot_answer = result.answer
    premium_applicable = result.premium_applicable

    logger.info(f"Gemini.py: Normal Gemini response received. ")
    # ==== END: Normal Gemini Response without RAG ==== #

    # gemini_response_content = Content(
    #     role="assistant", parts=[Part.from_text(text=bot_answer)]
    # )

    if premium_applicable:
        logger.info(
            "Gemini.py: Premium response is applicable. Generating premium response."
        )

        asyncio.create_task(
            generate_premium_response(
                chat_history, user_turn_content, client_id, vector_store, search_engine
            )
        )
    # ==== END: Trigger this when the response is premium worthy ==== #

    return NormalResponse(
        chat_history=chat_history,
        gemini_response=bot_answer,
        premium_applicable=premium_applicable,
    )


from typing import Dict
from fastapi import WebSocket
import json

# Global store for active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


async def generate_premium_response(
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
                    "status": "started",
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

        # ==== START: Fetching PDF for RAG  ==== #
        await websocket.send_text(
            json.dumps(
                {
                    "status": "searching",
                    "message": "Searching for relevant documents...",
                }
            )
        )
        documents = await search_engine.search(user_question)

        # ==== END: Fetching PDF for RAG  ==== #


        # ==== START: Fetching Video for RAG  ==== #
        logger.info("Generating response...")
        if vec is None:
            raise ValueError("Vector store should not be None.")
        logger.info("starting similarity search...")

        await websocket.send_text(
            json.dumps(
                {
                    "status": "searching_videos",
                    "message": "Searching for relevant videos...",
                }
            )
        )

        results = vec.similarity_search(user_question)
        logger.info("Generating response from Synthesizer...")

        await websocket.send_text(
            json.dumps(
                {"status": "synthesizing", "message": "Synthesizing the findings..."}
            )
        )

        try:
            response = await Synthesizer.generate_response(
                question=user_question, video_context=results, documents=documents
            )

            logger.info(f"gemini.py: Synthesized response received: {response}")

            premium_bot_answer = response.answer
            video_file_link = response.file_link
            video_file_name = response.file_name
            thumbnail_link = response.thumbnail_link
            partner_name = response.partner_name

            # premium_response_content = Content(
            #     role="assistant", parts=[Part.from_text(text=premium_bot_answer)]
            # )

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
                            ],  # Convert Document dataclass to dict
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
