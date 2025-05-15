import os
from google import genai
import vertexai
import logging
import pandas as pd
import uuid
from datetime import datetime
import asyncio


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

    # PROJECT_ID = str(os.environ.get("GOOGLE_CLOUD_PROJECT", "lamb-puppy-215354"))
    PROJECT_ID = str(os.environ.get("GOOGLE_CLOUD_PROJECT", "maylyan-test"))
    LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")

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

def extractVideoTranscript(gcs_uri: str):
    """Transcribe speech from a video stored on GCS."""
    logger.info(f"{gcs_uri} Video is being processed...")
    start_time = datetime.now()
    video_client = videointelligence.VideoIntelligenceServiceClient()
    features = [videointelligence.Feature.SPEECH_TRANSCRIPTION]

    config = videointelligence.SpeechTranscriptionConfig(
        language_code="en-US", enable_automatic_punctuation=True
    )
    video_context = videointelligence.VideoContext(speech_transcription_config=config)

    operation = video_client.annotate_video(
        request={
            "features": features,
            "input_uri": gcs_uri,
            "video_context": video_context,
        }
    )

    result = operation.result()

    annotation_results = result.annotation_results[0]
    final_transcript = ""
    for speech_transcription in annotation_results.speech_transcriptions:
    # The number of alternatives for each transcription is limited by
    # SpeechTranscriptionConfig.max_alternatives.
    # Each alternative is a different possible transcription
    # and has its own confidence score.
        transcript = speech_transcription.alternatives[0].transcript
        final_transcript += transcript

    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Video processing completed in: {duration}")

    return final_transcript

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

    if os.path.exists("./data/video_data.csv"):
        df.to_csv("./data/video_data.csv", mode='a', header=False, index=False)
    else:
        df.to_csv("./data/video_data.csv", mode='w', header=True, index=False)

    logger.info(f"Inserted {videoFilePath} to CSV")

    return df

def main():
    """Main function to run the script."""
    # Initialize the GenAI client
    client = initialize_client()

    # Example file path and transcript - innovation video
    transcript = extractVideoTranscript("gs://maylyan-rag/HFIN_2621_BCS_R.mp4")
    partner = "Hearst Television"
    videofilepath = "https://storage.mtls.cloud.google.com/maylyan-rag-test/HFIN_2621_BCS_R.mp4"

    # Prepare the record
    insert_transcript_to_csv(videofilepath, transcript, partner)



    # Example file path and transcript - dog
    transcript = extractVideoTranscript("gs://maylyan-rag/LDOG_3387_BCS.mp4")
    partner = "Hearst Television"
    videofilepath = "https://storage.mtls.cloud.google.com/maylyan-rag/LDOG_3387_BCS.mp4"

    # Prepare the record
    insert_transcript_to_csv(videofilepath, transcript, partner)

