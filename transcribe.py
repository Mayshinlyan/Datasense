import os
from google import genai
import vertexai
import logging
import pandas as pd
import uuid
from datetime import datetime
import asyncio
from config import DatabaseSettings, LLMSettings


MODEL_ID = LLMSettings().gcp_model


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


from google.cloud.video import transcoder_v1
from google.cloud.video.transcoder_v1.services.transcoder_service import (
    TranscoderServiceClient,
)


def generate_thumbnail(
    project_id: str,
    location: str,
    input_uri: str,
    output_uri: str,
    encodedVideoFileName: str,
) -> transcoder_v1.types.resources.Job:
    """Creates a job based on an ad-hoc job configuration that generates two spritesheets.

    Args:
        project_id: The GCP project ID.
        location: The location to start the job in.
        input_uri: Uri of the video in the Cloud Storage bucket.
        output_uri: Uri of the video output folder in the Cloud Storage bucket.

    Returns:
        The job resource.
    """

    client = TranscoderServiceClient()

    from google.protobuf.duration_pb2 import Duration

    # Create a Duration object for the offset
    start_time_offset = Duration(seconds=3)

    parent = f"projects/{project_id}/locations/{location}"
    job = transcoder_v1.types.Job()
    job.input_uri = f"{input_uri}"
    job.output_uri = f"{output_uri}"
    job.config = transcoder_v1.types.JobConfig(
        elementary_streams=[
            # This section defines the output video stream.
            transcoder_v1.types.ElementaryStream(
                key="video-stream0",
                video_stream=transcoder_v1.types.VideoStream(
                    h264=transcoder_v1.types.VideoStream.H264CodecSettings(
                        height_pixels=360,
                        width_pixels=640,
                        bitrate_bps=550000,
                        frame_rate=60,
                    ),
                ),
            )
        ],
        # # This section multiplexes the output audio and video together into a container.
        mux_streams=[
            transcoder_v1.types.MuxStream(
                key="mp4", container="mp4", elementary_streams=["video-stream0"]
            ),
        ],
        sprite_sheets=[
            # Generate a 10x10 sprite sheet with 64x32px images.
            transcoder_v1.types.SpriteSheet(
                file_prefix=encodedVideoFileName,
                sprite_width_pixels=1280,
                sprite_height_pixels=720,
                column_count=1,
                row_count=1,
                total_count=1,
                start_time_offset=start_time_offset,
            )
        ],
    )

    print(f"Creating Transcoder job in {location} for input: {input_uri}")
    try:
        response = client.create_job(parent=parent, job=job)
        print(f"Transcoder job created: {response.name}")
        print("Monitoring job status...")
        while response.state not in [
            transcoder_v1.Job.ProcessingState.SUCCEEDED,
            transcoder_v1.Job.ProcessingState.FAILED,
        ]:
            job = client.get_job(name=response.name)
            print(f"Job state: {transcoder_v1.Job.ProcessingState(job.state).name}")
            import time

            time.sleep(10)  # Wait for 10 seconds before polling again

            if job.state == transcoder_v1.Job.ProcessingState.SUCCEEDED:
                print(
                    f"Transcoder job succeeded! Thumbnail output to: https://storage.mtls.cloud.google.com/maylyan-rag/thumbnail/{encodedVideoFileName}0000000000.jpeg"
                )
                response.state = transcoder_v1.Job.ProcessingState.SUCCEEDED
            else:
                print(f"Transcoder job failed: {job.error.details}")
                print(f"Full error: {job.error}")
                # response.state = transcoder_v1.Job.ProcessingState.FAILED
    except Exception as e:
        print(f"Error: {e}")

    thumbnail_uri = f"https://storage.mtls.cloud.google.com/maylyan-rag/thumbnail/{encodedVideoFileName}0000000000.jpeg"

    return thumbnail_uri


def insert_transcript_to_csv(
    videoFileName: str,
    videoFilePath: str,
    GCSUri: str,
    transcript: str,
    partner: str,
    thumbnail_uri: str,
):
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
            "video_uri": str(GCSUri),
            "thumbnail_uri": str(thumbnail_uri),
            "transcript": str(transcript),
        }
    )

    # Convert the record to a DataFrame
    df = pd.DataFrame([record])

    if os.path.exists("./data/output_transcribed_videodata.csv"):
        df.to_csv(
            "./data/output_transcribed_videodata.csv",
            mode="a",
            header=False,
            index=False,
        )
        logger.info(f"Appended transcript for {videoFileName} into the CSV")
    else:
        df.to_csv(
            "./data/output_transcribed_videodata.csv",
            mode="w",
            header=True,
            index=False,
        )
        logger.info(f"Created new CSV and inserted transcript for {videoFileName}")

    return df


import urllib.parse


def transcription_pipeline(input_csv_filepath: str):
    """Main function to run the transcription pipeline. Input CSV file contains two columns: video_file_path and partner."""

    # Initialize the GenAI client
    initialize_client()

    # Read and loop through each row in the CSV file
    df = pd.read_csv(input_csv_filepath, sep=",")

    for index, row in df.iterrows():
        partner = row["partner"]
        videoFileName = row["videoFileName"]
        encodedVideoFileName = urllib.parse.quote(videoFileName)
        GCSUri = row["GCSUri"]
        videoFilePath = row["videoFilePath"]

        logger.info(
            f"Read CSV data for {partner},{videoFileName},{videoFilePath},{GCSUri}"
        )

        # Extract the thumbnail from the video file
        thumbnail_uri = generate_thumbnail(
            "lamb-puppy-215354",
            "us-central1",
            GCSUri,
            "gs://maylyan-rag/thumbnail/",
            encodedVideoFileName,
        )

        # Extract the transcript from the video file
        transcript = extractVideoTranscript(GCSUri)

        # Insert the transcript into the CSV file
        insert_transcript_to_csv(
            videoFileName, videoFilePath, GCSUri, transcript, partner, thumbnail_uri
        )

    logger.info("All transcripts have been processed and inserted into the CSV file.")


def main():
    """Main function to run the script."""
    transcription_pipeline("./data/input_file.csv")
