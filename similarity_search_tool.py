from langchain_core.documents import Document
from langchain_google_alloydb_pg import AlloyDBEngine, AlloyDBVectorStore
from langchain_google_vertexai import VertexAIEmbeddings
from pydantic import BaseModel, Field

import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

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
# Create Similarity Search Tool
# ----------------------------------------

class video_rag_file(BaseModel):
    file_link: str  = Field(
        description="the link to the video file"
    )
    transcript: str = Field(
        description="the transcript of the video"
    )


def similarity_search(query: str) -> video_rag_file:
    """Searches and returns videos.

    Args:
      query: The user query to search for related items

    Returns:
      List[Document]: A list of Documents
    """
    logger.info("Querying the vector store...")
    engine = AlloyDBEngine.from_instance(
        PROJECT_ID,
        REGION,
        CLUSTER,
        INSTANCE,
        DATABASE,
        # Uncomment to use built-in authentication instead of IAM authentication
        user="postgres",
        password=PASSWORD,
    )

    vector_store = AlloyDBVectorStore.create_sync(
        engine,
        table_name=TABLE_NAME,
        embedding_service=VertexAIEmbeddings(
            model_name="text-embedding-005", project=PROJECT_ID
        ),
    )
    retriever = vector_store.as_retriever()

    result = retriever.invoke(query)
    logger.info("Info retrieved")

    video_file_path = result[0].metadata.get("video_file_path")
    transcript = result[0].page_content


    return result[0]





