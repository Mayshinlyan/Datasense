import pandas as pd
from database import VectorStore
from config import setup_logging
import asyncio

logger = setup_logging()


# optional method to see CSV file in df
def csv_to_df(row):
    """Prepare a record for insertion into the vector store."""
    return pd.Series(
        {
            "id": row["id"],
            "partner": row["partner"],
            "created_at": row["created_at"],
            "file_name": row["file_name"],
            "video_file_path": row["video_file_path"],
            "video_uri": row["video_uri"],
            "thumbnail_uri": row["thumbnail_uri"],
            "transcript": row["transcript"],
        }
    )


async def insert_records_to_vector_store(vec, transcribed_csv_file: str):
    """Insert records into the vector store from a CSV file."""
    # insert records from CSV file to vector store
    vec.upsert(transcribed_csv_file)

    # Reindex the vector store with new data
    response = await vec.vector_store.areindex()

    if response:
        logger.info("Reindexing completed successfully.")


async def main():
    """Main function to insert records into the vector store."""
    # Initialize VectorStore
    vec = await VectorStore.create()

    await insert_records_to_vector_store(vec, "./data/output_transcribed_videodata.csv")

    vec.similarity_search(
        "How should I package my final recommendation, especially for senior executives who don't want lengthy documents?"
    )
if __name__ == "__main__":
    asyncio.run(main())
