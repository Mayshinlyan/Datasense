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

import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Response model for normal Gemini response
class GeminiResponse(BaseModel):
    thought_process: List[str] = Field(
        description="List of thoughts that the AI assistant had while forming the answer"
    )
    answer: str = Field(description="The answer to the user's question")
    premium_applicable: bool = Field(
        description="Whether the answer can be further improved by the retrival augement generation (RAG) process."
    )

def generate(chat_history: List[Content], user_turn: Union[Content,str], vec: VectorStore) -> Tuple[List[Content], Content]:
    """
    Call the model, handles both Content and Str type inputs.
    """

    logger.info("Gemini.py: Generating response from Gemini model.")

    if isinstance(user_turn, str):
        user_turn_content = Content(
            role="user",
            parts=[
                Part.from_text(text=user_turn)
            ]
        )
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
        temperature = get_settings().llm.model_temperature,
        system_instruction=get_settings().llm.system_instruction,
        response_mime_type="application/json",
        response_schema=GeminiResponse,
    )

    response = client.models.generate_content(
        model = get_settings().llm.gcp_model,
        contents = chat_history,
        config = generate_content_config,
    )

    result = response.parsed
    bot_answer = result.answer
    premium_applicable = result.premium_applicable

    logger.info(f"Gemini.py: Normal Gemini response received. {bot_answer} ,{premium_applicable}")
    # ==== END: Normal Gemini Response without RAG ==== #

    # ==== START: Trigger this when the response is premium worthy ==== #
    if premium_applicable:

        logger.info("Generating response...")
        if vec is None:
            raise ValueError("Vector store should not be None.")
        logger.info("starting similarity search...")
        results = vec.similarity_search(user_turn)
        logger.info("Generating response from Synthesizer...")
        response = Synthesizer.generate_response(question=user_turn, context=results)
        result = response.parsed
        logger.info(f"Gemini.py: Gemini response {result}.")

        premium_bot_answer = result.answer
        video_file_link = result.file_link
        video_file_name = result.file_name

        # enough_context = result.enough_context

        logger.info(f"Gemini.py: Premium model response received as: {premium_bot_answer} with video link: {video_file_link} and file names: {video_file_name}")
    else:
        premium_bot_answer = "N/A"
        video_file_link = "N/A"
        video_file_name = "N/A"

    gemini_response_content = Content(
        role="assistant",
        parts=[
            Part.from_text(text=bot_answer)
        ]
    )
    premium_response_content = Content(
        role="assistant",
        parts=[
            Part.from_text(text=premium_bot_answer)
        ]
    )
        # ==== END: Trigger this when the response is premium worthy ==== #




    return (chat_history, gemini_response_content, video_file_link, video_file_name, premium_response_content)

