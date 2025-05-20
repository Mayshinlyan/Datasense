import os
from google import genai
import vertexai
import logging
import pandas as pd
import uuid
from datetime import datetime
import asyncio
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
            "input_uri": f"{gcs_uri}",
            "video_context": video_context,
        }
    )

    result = operation.result()

    annotation_results = result.annotation_results[0]
    final_transcript = ""
    for speech_transcription in annotation_results.speech_transcriptions:
        transcript = speech_transcription.alternatives[0].transcript
        final_transcript += transcript

    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Video processing completed in: {duration}")

    return final_transcript

def insert_transcript_to_csv(videoFileName:str, videoFilePath: str, GCSUri:str, transcript: str, partner: str):
    """Prepare a record for insertion into the vector store.

    This function creates a record with a UUID version 1 as the ID, which captures the current time or a specified time.
    """
    logger.info(f"Inserting transcript to csv for {videoFileName}")

    record = pd.Series(
        {
            "id": str(uuid.uuid1()),
            "partner": str(partner),
            "created_at": datetime.now().isoformat(),
            "file_name": str(videoFileName),
            "video_file_path": str(videoFilePath),
            "gcs_uri": str(GCSUri),
            "transcript": str(transcript)
        }
    )

    # Convert the record to a DataFrame
    df = pd.DataFrame([record])

    if os.path.exists("./data/output_transcribed_videodata.csv"):
        df.to_csv("./data/output_transcribed_videodata.csv", mode='a', header=False, index=False)
        logger.info(f"Appended transcript for {videoFileName} into the CSV")
    else:
        df.to_csv("./data/output_transcribed_videodata.csv", mode='w', header=True, index=False)
        logger.info(f"Created new CSV and inserted transcript for {videoFileName}")

    return df

def transcription_pipeline(input_csv_filepath: str):
    """Main function to run the transcription pipeline. Input CSV file contains two columns: video_file_path and partner."""

    # Initialize the GenAI client
    initialize_client()

    # Read and loop through each row in the CSV file
    df = pd.read_csv(input_csv_filepath, sep=",")

    for index, row in df.iterrows():
        partner = row["partner"]
        videoFileName = row["videoFileName"]
        GCSUri = row["GCSUri"]
        videoFilePath = row["videoFilePath"]

        logger.info(f"Read CSV data for {partner},{videoFileName},{videoFilePath},{GCSUri}")

        # Extract the transcript from the video file
        transcript = extractVideoTranscript(GCSUri)

        # Insert the transcript into the CSV file
        insert_transcript_to_csv(videoFileName, videoFilePath, GCSUri, transcript, partner)

    logger.info("All transcripts have been processed and inserted into the CSV file.")


def main():

    """Main function to run the script."""
    transcription_pipeline("./data/input_file.csv")


