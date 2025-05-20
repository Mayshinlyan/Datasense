"""
Configuration
"""
import os
from dotenv import load_dotenv
import logging
from functools import lru_cache
from pydantic import BaseModel, Field

load_dotenv(dotenv_path="../.env")

def setup_logging():
    """Configure basic logging for the application."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    return logger

def _get_config_variable(variable_name: str, default_value: str) -> str:
        """
        Return a default value if variable does not exist
        """
        variable_value = os.environ.get(variable_name)
        if variable_value is None:
            variable_value = default_value
        return variable_value

class SearchEngineSettings(BaseModel):
    project_number: str = _get_config_variable("GCP_PROJECT_NUMBER", "176935887576")
    engine_id: str = _get_config_variable("VERTEXAI_SEARCH_ENGINE_ID", "datasense-test_1744153572996")
    location: str = _get_config_variable("SEARCH_ENGINE_LOCATION", "global")

class LLMSettings(BaseModel):
    """
    LLM specific configuration
    """
    debug_mode: bool = _get_config_variable("DEBUG_MODE", "False")

    gcp_project: str = _get_config_variable("GCP_PROJECT", "lamb-puppy-215354")
    gcp_location: str = _get_config_variable("GCP_LOCATION", "us-central1")
    gcp_model: str = _get_config_variable("GCP_MODEL", 'gemini-2.0-flash-001')

    # Gemini settings
    model_temperature: float = _get_config_variable("MODEL_TEMPERATURE", "0.5")
    model_top_p: float = _get_config_variable("MODEL_TOP_P", "0.8")
    model_max_output_tokens: int = _get_config_variable("MODEL_MAX_OUTPUT_TOKENS", "1024")

    system_instruction: str = _get_config_variable("SYSTEM_INSTRUCTION", "You are an AI assistant for question-answering tasks. Answer the user response concisely. For questions that are not mundane, use the retrieval augmented generation (RAG) process to improve the answer.")


class DatabaseSettings(BaseModel):
    """
    Database specific configuration
    """
    db_project: str = _get_config_variable("GCP_PROJECT", "lamb-puppy-215354")
    db_location: str = _get_config_variable("GCP_LOCATION", "us-central1")
    cluster: str = _get_config_variable("DB_CLUSTER", 'datasense')
    instance: str = _get_config_variable("DB_INSTANCE", 'datasense-primary')
    database: str = _get_config_variable("DB_DATABASE", 'postgres')
    table: str = _get_config_variable("YDB_TABLE_NAME", 'partnertable')
    dbuser: str = _get_config_variable("DB_USER", 'postgres')
    dbpassword: str = _get_config_variable("DB_PASSWORD", '5kL<?7{OXq]a')
    staging_bucket: str = _get_config_variable("DB_STAGING_BUCKET", "gs://datasense_alloydb_vectorstore")
    embedding_vector_size: int = _get_config_variable("EMBEDDING_VECTOR_SIZE", "768")
    embedding_model: str = _get_config_variable("EMBEDDING_MODEL", "text-embedding-005")


class Settings(BaseModel):
    """Main settings class combining all sub-settings."""

    llm: LLMSettings = Field(default_factory=LLMSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    search_engine: SearchEngineSettings = Field(default_factory=SearchEngineSettings)

@lru_cache
def get_settings() -> Settings:
    """Create and return a cached instance of the Settings."""
    settings = Settings()
    setup_logging()
    return settings

