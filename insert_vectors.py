from datetime import datetime

import pandas as pd
from database import VectorStore

# Initialize VectorStore
vec = VectorStore()

# Read the CSV file
df = pd.read_csv("../data/out.csv", sep=",")


# optional method to see CSV file in df
def csv_to_df(row):
    """Prepare a record for insertion into the vector store.
    """
    return pd.Series(
        {
            "id": row["id"],
            "partner": row["partner"],
            "created_at": row["created_at"],
            "video_file_path": row["video_file_path"],
            "transcript": row["transcript"],
        }
    )

records_df = df.apply(csv_to_df, axis=1)

def insert_vectors():

    # Create tables and insert data
    # vec.create_table()
    vec.upsert("../data/out.csv")
    vec.create_index()  # IVFFlatIndex

    vec.similarity_search("What is the best breed of dog to adopt?")


