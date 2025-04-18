import os
from google import genai
from google.genai.types import GenerateContentConfig
import vertexai
import logging
from pydantic import BaseModel, Field
import pandas as pd
import uuid
from datetime import datetime


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

    logger.info("\nProcessing video.")


    result = operation.result(timeout=600)

    annotation_results = result.annotation_results[0]

    logger.info(result)

    with open(f"./data/output.txt", 'a') as f:
        for speech_transcription in annotation_results.speech_transcriptions:
            for alternative in speech_transcription.alternatives:
                # print("Alternative level information:")
                # print("Transcript: {}".format(alternative.transcript))
                # print("Confidence: {}\n".format(alternative.confidence))

                f.write(alternative.transcript)
                # f.write("Confidence: {}\n".format(alternative.confidence))



    logger.info( annotation_results )

# Prepare data for insertion
def prepare_record(videoFilePath: str, transcriptFilePath: str, partner: str):
    """Prepare a record for insertion into the vector store.

    This function creates a record with a UUID version 1 as the ID, which captures
    the current time or a specified time.

    """

    with open(transcriptFilePath, 'r') as f:
        transcript = f.read()
        logger.info(f"Loaded Transcript")

    record = pd.Series(
        {
            "id": str(uuid.uuid1()),
            "metadata": {
                "partner": partner,
                "created_at": datetime.now().isoformat(),
            },
            "video_file_path": videoFilePath,
            "transcript": transcript
        }
    )

    # Convert the record to a DataFrame
    df = pd.DataFrame([record])

    # # Set the 'uuid_col' as the index
    # df.set_index('id', inplace=True)

    if os.path.exists("./data/out.csv"):
        df.to_csv("./data/out.csv", mode='a', header=False, index=False)
    else:
        df.to_csv("./data/out.csv", mode='w', header=True, index=False)

    log.info(f"Prepared record for {videoFilePath}")


# Example file path and transcript
transcript = "./data/innovation_transcript.txt"
partner = "Hearst Television"
videofilepath = "https://drive.google.com/corp/drive/folders/1UkenEMoNWJoAdH3OSROPnA5OtN5WCDyH"

# Prepare the record
prepare_record(videofilepath, transcript, partner)

