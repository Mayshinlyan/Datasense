from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_core.documents import Document
from langchain_google_alloydb_pg import AlloyDBEngine, AlloyDBVectorStore
from langchain_google_vertexai import VertexAIEmbeddings
from config import get_settings
import pandas as pd

import logging
from langchain_google_alloydb_pg.indexes import IVFFlatIndex
from typing import Any, List, Optional, Tuple, Union
from google.cloud.alloydb.connector import Connector, IPTypes
from sqlalchemy import text, inspect

def setup_logging():
    """Configure basic logging for the application."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    return logger

logger = setup_logging()



class VectorStore:
    """A class for managing vector operations and database interactions."""

    def __init__(self):
        """Initialize the VectorStore with settings, AlloyDB Vector client."""
        self.settings = get_settings().database
        self.engine = self.create_db()
        self.create_table() # Create the table if it doesn't exist

        embedding_service=VertexAIEmbeddings(
            model_name=self.settings.embedding_model, project=self.settings.db_project
        )
        self.vector_store = AlloyDBVectorStore.create_sync(
            self.engine,
            table_name=self.settings.table,
            embedding_service=embedding_service,
        )

    def create_db(self):
        """Create the database"""
        try:
            engine =  AlloyDBEngine.from_instance(
                'lamb-puppy-215354',
                'us-central1',
                'datasense',
                'datasense-primary',
                database="postgres", # Connect to the default 'postgres' database initially
                user="postgres",
                password='5kL<?7{OXq]a',
            )

            return engine # Return the engine object

        except Exception as e:
             # The print statement after this catch in main.py might still run
             # because the exception is caught here and not re-raised.
             # Consider adding `raise e` here if an DB init error should stop the app.
             logger.error(f"Error creating AlloyDBEngine or initializing table: {e}")
             # Depending on how critical the DB is, you might re-raise or exit here
             # raise # Re-raise the caught exception
             return None # Return None or handle the error if not re-raising

    def create_table(self):
        """Create the necessary tables in the database"""

        try:
            self.engine.init_vectorstore_table(
                table_name=self.settings.table,
                vector_size=768,  # Vector size for VertexAI model(text-embedding-005)
            )
            logger.info(f"Successfully initialized vectorstore table '{self.settings.table}'.")

            return True  # Indicate success
        except Exception as e:
            logger.error(f"Error creating AlloyDBEngine or initializing table: {e}")

            return False

    def create_index(self) -> None:
        """Create the StreamingDiskANN index to spseed up similarity search"""
        index = IVFFlatIndex()
        self.vector_store.apply_vector_index(index)
        logger.info(f"Successfully created index '{index}' for table '{self.settings.table}'.")

    def upsert(self, csv_file: str):
        """
        Insert or update records in the database from a pandas DataFrame.

        Args:
            csv_file: Path to the CSV file containing the data to be inserted.
        """

        # Step 2: load the CSV
        metadata = [
            'id',
            'partner',
            'created_at',
            "video_file_path",
        ]
        loader = CSVLoader(file_path=csv_file, metadata_columns=metadata)
        docs = loader.load()

        # Add data to the vector store
        ids = [docs[i].metadata["id"] for i in range(len(docs))]


        self.vector_store.add_documents(docs, ids=ids)
        logging.info(
            f"Inserted records into {self.settings.table}"
        )

    def similarity_search(self, query: str) -> list[Document]:
        """Searches and returns videos.

        Args:
        query: The user query to search for related items

        Returns:
        List[Document]: A list of Documents
        """
        try:
            docs = self.vector_store.similarity_search(query, k=5)
            logger.info(f"Found similar documents {docs}")
        except Exception as e:
            logger.error(f"Error during similarity search: {e}")

        logger.info(docs)
        # retriever = self.vector_store.as_retriever(search_type="similarity_score_threshold",
        # search_kwargs={'score_threshold': 0.5})
        print("Querying the vector store...")

        df = self._create_dataframe_from_results(docs)

        print(df)

        return df

    def _create_dataframe_from_results(
        self,
        results: List[Tuple[Any, ...]],
    ) -> pd.DataFrame:
        """
        Create a pandas DataFrame from the search results.

        Args:
            results: A list of Documents containing the search results.

        Returns:
            A pandas DataFrame containing the formatted search results.
        """
        data = []
        for doc in results:
            data.append({
                'id': doc.metadata.get('id'),
                'partner': doc.metadata.get('partner'),
                'created_at': doc.metadata.get('created_at'),
                'video_file_path': doc.metadata.get('video_file_path'),
                'page_content': doc.page_content,
            })
        df = pd.DataFrame(data)

        return df

    # results = [Document(metadata={'source': '../data/out.csv', 'row': 1, 'id': 'f79e6bbc-1d5f-11f0-9d3f-fa0a240152c3', 'partner': 'Hearst Television', 'created_at': '2025-04-19T13:50:46.193881', 'video_file_path': 'https://drive.google.com/corp/drive/folders/1UkenEMoNWJoAdH3OSROPnA5OtN5WCDyH'}, page_content="transcript: Welcome to the Henry Ford's Innovation Nation. I'm Mo Rocca and today will astonish you. Coming up the Precision."),
    # Document(metadata={'source': '../data/out.csv', 'row': 0, 'id': 'f3b08f26-1d5f-11f0-9d3f-fa0a240152c3', 'partner': 'Hearst Television', 'created_at': '2025-04-19T13:50:39.601865', 'video_file_path': 'https://drive.google.com/file/d/1uxYSvoZvTjRcWk-dutVjjTMCsytkfuX6/'}, page_content="transcript: I'm Brandon McMillan. And for 7 years")]

 #   async def main():
 #       vec = VectorStore()

 #       db = await vec.create_db()

 #   main()