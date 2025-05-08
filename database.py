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
from sqlalchemy import text

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

        # self.engine = AlloyDBEngine.from_instance(
        #     self.settings.db_project , self.settings.db_location, self.settings.db_location, self.settings.instance, self.settings.database, self.settings.dbuser, self.settings.dbpassword
        # )
        # logger.info("Successfully created AlloyDBEngine instance.")


        # # Initialize the vector store
        # self.vector_store = AlloyDBVectorStore.create_sync(
        #     self.engine,
        #     table_name=self.settings.table,
        #     embedding_service=VertexAIEmbeddings(
        #         model_name="text-embedding-005", project=self.settings.db_project
        #     )
        # )
        logger.info("Initialized the vector store.")
    
    async def create_db(self):
        """Create the database"""
        try:
            engine =  await AlloyDBEngine.afrom_instance(
                'lamb-puppy-215354',
                'us-central1',
                'datasense',
                'datasense-primary',
                database="postgres", # Connect to the default 'postgres' database initially
                user="postgres",
                password='5kL<?7{OXq]a',
            )

            # --- REMOVE THIS BLOCK ---
            # with engine._pool.connect() as conn:
            #     await print('hi')
            # -------------------------

            # This block now correctly uses 'async with' to connect
            async with engine._pool.connect() as conn:
                # Note: Creating a database within a connection pool might not be the standard way.
                # Usually, CREATE DATABASE is done once via gcloud CLI or a separate script,
                # or potentially on a connection *not* from the pool, or on a connection
                # established specifically to the 'postgres' db to create another one.
                # The `COMMIT` here is also unusual in this context.
                # However, to fix the specific error, this block's syntax is correct (using async with).

                # You might need to adjust this logic depending on how AlloyDBEngine
                # expects you to ensure the target database exists.
                # The 'CREATE DATABASE' command is typically run only once.

                # await conn.execute(text("COMMIT")) # COMMIT is often implicit or managed by the pool/framework
                # await conn.execute(text(f"CREATE DATABASE {self.settings.database}")) # This might fail if run here

                 # Consider if you just need the engine object here and table creation/checks
                 # happen elsewhere after the engine is returned/stored.
                 # If the goal is *just* to get the engine:
                 return engine # <-- If you only need the engine instance

            # If the goal is to get the engine AND ensure the table exists,
            # you might do table initialization *after* getting the engine,
            # potentially using engine.run_sync() for sync methods or ensuring
            # ainit_vectorstore_table is called correctly.

            # Given the original structure and the name create_db, it seems the intent
            # was to get the engine and possibly ensure the database exists.
            # Let's assume the intent is to get the engine for now.
            return engine # Return the engine object

        except Exception as e:
             # The print statement after this catch in main.py might still run
             # because the exception is caught here and not re-raised.
             # Consider adding `raise e` here if an DB init error should stop the app.
             logger.error(f"Error creating AlloyDBEngine or initializing table: {e}")
             # Depending on how critical the DB is, you might re-raise or exit here
             # raise # Re-raise the caught exception
             return None # Return None or handle the error if not re-raising


    # ... rest of the VectorStore class ...

    def create_table(self):
        """Create the necessary tables in the database"""
        try:
            self.engine.ainit_vectorstore_table(
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

        docs = self.vector_store.similarity_search(query, k=5)

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