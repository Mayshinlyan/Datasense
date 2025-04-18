"""
Configuration
"""

import os
from dotenv import load_dotenv

class DatasenseConfig:
    """
    Datasense specific configuration
    """

    def __init__(self):
        load_dotenv()
        self.debug_mode = self._get_config_variable("DEBUG_MODE", "False")

        self.gcp_project = self._get_config_variable("GCP_PROJECT", None)
        self.gcp_location = self._get_config_variable("GCP_LOCATION", "us-central1")
        self.gcp_model = self._get_config_variable("GCP_MODEL", 'gemini-2.0-flash-001')


        self.model_temperature = self._get_config_variable("MODEL_TEMPERATURE", "0.2")
        self.model_top_p = self._get_config_variable("MODEL_TOP_P", "0.8")
        self.model_max_output_tokens = self._get_config_variable("MODEL_MAX_OUTPUT_TOKENS", "1024")

        self.system_instruction = self._get_config_variable("SYSTEM_INSTRUCTION", "You are helpful assistant.")

    def _get_config_variable(self, variable_name: str, default_value: str) -> str:
        """
        Return a default value if variable does not exist
        """
        variable_value = os.environ.get(variable_name)
        if variable_value is None:
            variable_value = default_value
        return variable_value


datasenseconfig = DatasenseConfig()
