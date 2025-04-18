import asyncio
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_core.documents import Document
from langchain_google_alloydb_pg import AlloyDBEngine, AlloyDBVectorStore
from langchain_google_vertexai import VertexAIEmbeddings

import logging


def logger():
    # Set up logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)

    return logger
logger = logger()

PROJECT_ID="maylyan-test"
LOCATION="us-central1"

STAGING_BUCKET_NAME="alloydb_vectorstore"
STAGING_BUCKET=f"gs://{STAGING_BUCKET_NAME}"
REGION="us-central1"
CLUSTER="datasense"
INSTANCE="datasense"
DATABASE="datasensedb"
TABLE_NAME="datasensehearst"
PASSWORD="datasense"

# ----------------------------------------
# Create Connection to the Instance
# ----------------------------------------

from google.cloud.alloydb.connector import Connector, IPTypes
import sqlalchemy


# function to return the database connection
def getconn():
    connection_string = f"projects/{PROJECT_ID}/locations/{LOCATION}/clusters/{CLUSTER}/instances/{INSTANCE}"
# initialize Connector object
    connector = Connector()

    conn = connector.connect(
        connection_string,
        "pg8000",
        user="postgres",
        password=PASSWORD,
        db="postgres",
        enable_iam_auth=False,
        ip_type=IPTypes.PUBLIC,
    )



    return conn


# ----------------------------------------
# Create New Database
# ----------------------------------------
def create_db():

    connection_string = f"projects/{PROJECT_ID}/locations/{LOCATION}/clusters/{CLUSTER}/instances/{INSTANCE}"

    # initialize Connector object
    connector = Connector()
    # create connection pool
    pool = sqlalchemy.create_engine(
        "postgresql+pg8000://", creator=getconn, isolation_level="AUTOCOMMIT"
    )

    with pool.connect() as db_conn:
        db_conn.execute(sqlalchemy.text(f"CREATE DATABASE {DATABASE}"))
    connector.close()

# ----------------------------------------
# Create Connection to the New Database
# ----------------------------------------

from google.cloud.alloydb.connector import Connector, IPTypes
import sqlalchemy

# function to return the database connection
def getconn():

    connection_string = f"projects/{PROJECT_ID}/locations/{LOCATION}/clusters/{CLUSTER}/instances/{INSTANCE}"
    # initialize Connector object
    connector = Connector()

    conn = connector.connect(
        connection_string,
        "pg8000",
        user="postgres",
        password=PASSWORD,
        db=DATABASE,
        enable_iam_auth=False,
        ip_type=IPTypes.PUBLIC,
    )
    return conn


# ----------------------------------------
# Create table
# ----------------------------------------

async def create_table():
    try:
        engine = await AlloyDBEngine.afrom_instance(
            PROJECT_ID, REGION, CLUSTER, INSTANCE, DATABASE, user="postgres", password=PASSWORD
        )
        logger.info("Successfully created AlloyDBEngine instance.")

        await engine.ainit_vectorstore_table(
            table_name=TABLE_NAME,
            vector_size=768,  # Vector size for VertexAI model(text-embedding-005)
        )
        logger.info(f"Successfully initialized vectorstore table '{TABLE_NAME}'.")
        return True  # Indicate success
    except Exception as e:
        logger.error(f"Error creating AlloyDBEngine or initializing table: {e}")

        return False

# ----------------------------------------
# Process the data
# ----------------------------------------

# Load the CSV file
# metadata = [
#     "show_id",
#     "type",
#     "country",
#     "date_added",
#     "release_year",
#     "rating",
#     "duration",
#     "listed_in",
# ]
# loader = CSVLoader(file_path="./movies.csv", metadata_columns=metadata)
# docs = loader.load()
# docs[0]

# ----------------------------------------
# Load the data into the Vector Store
# ----------------------------------------

async def initializeVecStore():
    engine = await AlloyDBEngine.afrom_instance(
        PROJECT_ID, REGION, CLUSTER, INSTANCE, DATABASE, user="postgres", password=PASSWORD
    )
    logger.info("Successfully created AlloyDBEngine instance.")


# Initialize the vector store
    vector_store = await AlloyDBVectorStore.create(
        engine,
        table_name=TABLE_NAME,
        embedding_service=VertexAIEmbeddings(
            model_name="text-embedding-005", project=PROJECT_ID
        ),
    )
    logger.info("Initialized the vector store.")

    # Step 1: create connection to the database
    pool = sqlalchemy.create_engine("postgresql+pg8000://", creator=getconn)

    # Step 2: load the CSV
    metadata = [
        "id",
        "metadata",
        "video_file_path",
    ]
    loader = CSVLoader(file_path="./data/out.csv", metadata_columns=metadata)
    docs = loader.load()
    docs[0]

    # Add data to the vector store
    ids = [docs[i].metadata["id"] for i in range(len(docs))]

    await vector_store.aadd_documents(docs, ids=ids)

    logger.info("Added documents to the vector store.")



async def main():


    # Step 3: add the data to the vector store
    initializeVecStore()

# if __name__ == "__main__":
#     asyncio.run(main())

