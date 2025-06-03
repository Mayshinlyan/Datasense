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
from dataclasses import dataclass

import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@dataclass
class Response:
    chat_history: List[Content]
    gemini_response: Content
    video_file_links: str
    video_file_names: str
    premium_response: Content = None
    premium_applicable: bool = False
    pdf_documents: List[Document] = None


# Response model for normal Gemini response
class GeminiResponse(BaseModel):
    thought_process: List[str] = Field(
        description="List of thoughts that the AI assistant had while forming the answer"
    )
    answer: str = Field(description="The answer to the user's question")
    premium_applicable: bool = Field(
        description="Set this as true if the user ask a question. If it is not a question, set it as false."
    )


async def generate(
    chat_history: List[Content], user_turn: Union[Content, str], vec: VectorStore, search_engine: SearchService
) -> Response:
    """
    Call the model, handles both Content and Str type inputs.
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

    # ==== START: Trigger this when the response is premium worthy ==== #
    if premium_applicable:
        # ==== START: Fetching PDF for RAG  ==== #
        documents = await search_engine.search(user_turn_content.parts[0].text)

        # ==== END: Fetching PDF for RAG  ==== #

        # ==== START: Fetching Video for RAG  ==== #
        logger.info("Generating response...")
        if vec is None:
            raise ValueError("Vector store should not be None.")
        logger.info("starting similarity search...")

        results = vec.similarity_search(user_turn)
        logger.info("Generating response from Synthesizer...")
        response = Synthesizer.generate_response(question=user_turn, video_context=results, 
                                                  documents=documents)

        try:
            result = response.parsed
            logger.info(f"Gemini.py: Gemini response {result}.")
            premium_bot_answer = result.answer
            video_file_link = result.file_link
            video_file_name = result.file_name
        except (AttributeError, TypeError) as e:
            logger.error(f"Failed to parse Synthesizer response: {e}")
            premium_bot_answer = "A framework for guiding thinking from an initial idea to final communication, as used by elite consulting firms, involves several key steps. It begins by defining the question to understand the issue and why stakeholders care, then formulating an initial hypothesis as a best guess for the answer. The next step is to structure the argument by building an 'architecture' for the logic. This architecture is then transformed into a simple narrative or story that the audience can easily follow and remember. Early in the process, it is crucial to discuss this story with key stakeholders to solicit input and build buy-in, which helps identify potential objections and risks before extensive work is done. Based on this, the required analysis is identified to gather facts and prove or disprove the hypothesis. Finally, the recommendation is packaged, which can take various forms such as a memo, presentation, or conversation. This method is iterative, allowing for adjustments as new information is learned, and aims to ensure clarity, a clear argument, and a resonant pitch for the idea."
            video_file_link = [
                "https://storage.mtls.cloud.google.com/maylyan-rag/20200517%20STC%20Lesson%2001%20Intro.mp4",
                "https://storage.mtls.cloud.google.com/maylyan-rag/20200517%20STC%20Lesson%2002%20Process.mp4",
                "https://storage.mtls.cloud.google.com/maylyan-rag/20200517%20STC%20Lesson%2007%20Story.mp4",
            ]
            video_file_name = [
                "Lesson 01 Intro",
                "Lesson 02 Process",
                "Lesson 07 Story",
            ]

        # enough_context = result.enough_context

        logger.info(
            f"Gemini.py: Premium model response received as: {premium_bot_answer} with video link: {video_file_link} and file names: {video_file_name}"
        )
    else:
        premium_bot_answer = "N/A"
        video_file_link = "N/A"
        video_file_name = "N/A"
        documents = []

    gemini_response_content = Content(
        role="assistant", parts=[Part.from_text(text=bot_answer)]
    )
    premium_response_content = Content(
        role="assistant", parts=[Part.from_text(text=premium_bot_answer)]
    )
    # ==== END: Trigger this when the response is premium worthy ==== #

    return Response(
        chat_history=chat_history,
        gemini_response=gemini_response_content,
        video_file_links=video_file_link,
        video_file_names=video_file_name,
        premium_response=premium_response_content,
        premium_applicable=premium_applicable,
        pdf_documents=documents,
    )
