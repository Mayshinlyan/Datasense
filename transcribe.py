import os
from google import genai
from google.genai.types import GenerateContentConfig
import vertexai
import logging
from pydantic import BaseModel, Field
import pandas as pd
import uuid
from datetime import datetime
from config import DatabaseSettings


MODEL_ID = "gemini-2.0-flash-001"


# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def initialize_client():

    """Initializes a GenAI client with project and location settings."""

    logger.info(f"Initalizing GenAI client")

    db_settings = DatabaseSettings()
    PROJECT_ID = db_settings.db_project
    LOCATION = DatabaseSettings().db_location

    vertexai.init(project=PROJECT_ID, location=LOCATION)
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    if not client._api_client.vertexai:
        logger.info(f"Using Gemini Developer API.")
    elif client._api_client.project:
        logger.info(
            f"Using Vertex AI with project: {client._api_client.project} in location: {client._api_client.location}"
        )
    elif client._api_client.api_key:
        logger.info(
            f"Using Vertex AI in express mode with API key: {client._api_client.api_key[:5]}...{client._api_client.api_key[-5:]}"
        )

    return client

from google.cloud import videointelligence

async def extractVideoTranscript(gcs_uri: str):
    """Transcribe speech from a video stored on GCS."""

    video_client = videointelligence.VideoIntelligenceServiceClient()
    features = [videointelligence.Feature.SPEECH_TRANSCRIPTION]

    config = videointelligence.SpeechTranscriptionConfig(
        language_code="en-US", enable_automatic_punctuation=True
    )
    video_context = videointelligence.VideoContext(speech_transcription_config=config)

    logger.info("\nProcessing video.")

    operation = await video_client.annotate_video(
        request={
            "features": features,
            "input_uri": gcs_uri,
            "video_context": video_context,
        }
    )

    result = operation.result()

    annotation_results = result.annotation_results[0]

    # logger.info(result)

    logger.info(annotation_results)

    return annotation_results

# compile the videos data into one data file
def insert_transcript_to_csv(videoFilePath: str, transcript: str, partner: str):
    """Prepare a record for insertion into the vector store.

    This function creates a record with a UUID version 1 as the ID, which captures
    the current time or a specified time.

    """

    record = pd.Series(
        {
            "id": str(uuid.uuid1()),
            "partner": partner,
            "created_at": datetime.now().isoformat(),
            "video_file_path": videoFilePath,
            "transcript": transcript
        }
    )

    # Convert the record to a DataFrame
    df = pd.DataFrame([record])

    if os.path.exists("../data/out.csv"):
        df.to_csv("../data/out.csv", mode='a', header=False, index=False)
    else:
        df.to_csv("../data/out.csv", mode='w', header=True, index=False)

    logger.info(f"Inserted {videoFilePath} to CSV")

    return df

def main():
    """Main function to run the script."""
    # Initialize the GenAI client
    client = initialize_client()

    # Example file path and transcript - dog
    transcript = extractVideoTranscript("gs://maylyan-rag/LDOG_3387_BCS.mp4")
    partner = "Hearst Television"
    videofilepath = "https://storage.mtls.cloud.google.com/maylyan-rag/LDOG_3387_BCS.mp4"

    # Prepare the record
    insert_transcript_to_csv(videofilepath, transcript, partner)

