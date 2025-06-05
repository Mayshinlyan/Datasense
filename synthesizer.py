from typing import List
import pandas as pd
from pydantic import BaseModel, Field

from google import genai
from google.genai import types
import logging
from config import get_settings
from search import Document

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class SynthesizedResponse(BaseModel):
    thought_process: str = Field(
        description="Thoughts that the AI assistant had while synthesizing the answer"
    )
    file_link: List[str] = Field(
        description="A list of video file paths associated with the context"
    )
    partner_name: List[str] = Field(
        description="The list of the partner associated with the context"
    )
    file_name: List[str] = Field(
        description="A list of file name associated with the context"
    )
    thumbnail_link: List[str] = Field(
        description="A list of thumbnail links associated with the context"
    )
    answer: str = Field(description="The synthesized answer to the user's question")
    enough_context: bool = Field(
        description="Whether the assistant has enough context to answer the question"
    )


class Synthesizer:
    @staticmethod
    async def generate_response(
        question: str, video_context: pd.DataFrame, documents: List[Document]
    ) -> SynthesizedResponse:
        """Generates a synthesized response based on the question and context.

        Args:
            question: The user's question.
            context: The relevant context retrieved from the knowledge base.

        Returns:
            A SynthesizedResponse containing thought process and answer.
        """
        video_context_str = Synthesizer.dataframe_to_json(
            video_context,
            columns_to_keep=[
                "video_file_path",
                "page_content",
                "partner",
                "file_name",
                "thumbnail_uri",
            ],
        )
        documents_str = ".".join([doc.segment_content for doc in documents])

        SYSTEM_PROMPT = f"""
            # Role and Purpose
            You are an AI assistant. Your task is to synthesize a coherent and helpful answer
            based on the given question and relevant context retrieved from a knowledge database.

            # Guidelines:

            1. Provide a clear and concise answer to the question based on the context.
            2. The context is retrieved based on cosine similarity, so some information might be missing or irrelevant.
            3. Do not use first person perspective.
            4. Do not make up or infer information not present in the provided context.
            5. Maintain a helpful and professional tone appropriate for customer service.

            Here is the relevant context retrieved from the knowledge database:
            {video_context_str} {documents_str}

            # Output Format
            Your response MUST be a JSON object that strictly adheres to the following schema.
            Ensure all fields are present and correctly typed.

            ```json
            {{
                "thought_process": "",
                "file_link": [],
                "partner_name": [],
                "file_name": [],
                "thumbnail_link": [],
                "answer": "",
                "enough_context": true or false
            }}
        ```

            Review the question from the user:
        """

        # Configure the client and tool
        client = genai.Client(
            vertexai=True,
            project=get_settings().llm.gcp_project,
            location=get_settings().llm.gcp_location,
        )
        generate_content_config = types.GenerateContentConfig(
            temperature=0.3,
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=SynthesizedResponse,
            tools=[],
        )
        response = client.models.generate_content(
            model=get_settings().llm.gcp_model,
            contents=question,
            config=generate_content_config,
        )

        logger.info(f"Synthesizer.py: Synthesized response received: {response.text}")
        logger.info(f"Synthesizer.py: Parsed response received: {response.parsed}")

        return response.parsed

    @staticmethod
    def dataframe_to_json(
        context: pd.DataFrame,
        columns_to_keep: List[str],
    ) -> str:
        """
        Convert the context DataFrame to a JSON string.

        Args:
            context (pd.DataFrame): The context DataFrame.
            columns_to_keep (List[str]): The columns to include in the output.

        Returns:
            str: A JSON string representation of the selected columns.
        """
        if context.empty:
            logger.warning("The context DataFrame is empty.")
            return "[]"
        return context[columns_to_keep].to_json(orient="records", indent=2)
