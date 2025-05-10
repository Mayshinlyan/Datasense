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

import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def generate(chat_history: List[Content], user_turn: Union[Content,str]) -> Tuple[List[Content], Content]:
    """
    Call the model, handles both Content and Str type inputs.
    """

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

    # # Configure the client and tool
    # client = genai.Client(
    #     vertexai=True,
    #     project=datasenseconfig.gcp_project,
    #     location=datasenseconfig.gcp_location,
    # )


    # generate_content_config = types.GenerateContentConfig(
    #     temperature = datasenseconfig.model_temperature,
    #     # top_p = datasenseconfig.model_top_p,
    #     # max_output_tokens = datasenseconfig.model_max_output_tokens,
    #     # response_modalities = ["TEXT"], # We're only supporting TEXT for now.
    #     tools=[similarity_search],
    #     # safety_settings = [
    #     #     types.SafetySetting(
    #     #         category="HARM_CATEGORY_HATE_SPEECH",
    #     #         threshold="OFF"
    #     #     ),
    #     #     types.SafetySetting(
    #     #         category="HARM_CATEGORY_DANGEROUS_CONTENT",
    #     #         threshold="OFF"
    #     #     ),
    #     #     types.SafetySetting(
    #     #         category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
    #     #         threshold="OFF"
    #     #     ),
    #     #     types.SafetySetting(
    #     #         category="HARM_CATEGORY_HARASSMENT",
    #     #         threshold="OFF"
    #     #     )
    #     # ],
    #     system_instruction=[types.Part.from_text(text=datasenseconfig.system_instruction)],
    # )


    # response = client.models.generate_content(
    #     model = datasenseconfig.gcp_model,
    #     contents = chat_history,
    #     config = generate_content_config,
    # )
    logger.info("initializing vector store...")
    vec = VectorStore()
    logger.info("similarity search...")
    results = vec.similarity_search(user_turn)
    response = Synthesizer.generate_response(question=user_turn, context=results)
    result = response.parsed

    bot_answer = result.answer
    video_file_link = result.file_link
    enough_context = result.enough_context

    logger.info(f"Model response received as: {bot_answer} with video link: {video_file_link}")

    model_response_content = Content(
        role="assistant",
        parts=[
            Part.from_text(text=bot_answer)
        ]
    )

    return (chat_history, model_response_content, video_file_link, enough_context)

