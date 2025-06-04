'''
This library provides the interface for connecting with the Vertex AI search app. 

Example of using this library

from search import search_sample
from config import get_settings

search_setting = get_settings().search_engine
documents = search_documents(
        project_id=search_setting.project_number,
        location=search_setting.location,
        engine_id=search_setting.engine_id,
        search_query=user_message.message,
)

'''

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
import logging 
from dataclasses import dataclass
from typing import Dict, List, Union
from google.protobuf.struct_pb2 import Struct, ListValue, Value

@dataclass
class Document:
    title: str = ""
    link: str  = ""
    link_with_page: str = ""
    snippets: List[str] = None
    segment_content: str = ""
    page_number: int = 1

class SearchService:
    """A reusable service for interacting with Vertex AI Search."""

    def __init__(self, client, serving_config: str):
        """
        Private constructor. Use the `create` classmethod for initialization.
        """
        self.client = client
        self.serving_config = serving_config
        logging.info(f"SearchService instance configured for: {self.serving_config}")

    @classmethod
    async def create(cls, project_id: str, location: str, engine_id: str):
        """
        Asynchronously creates and initializes the SearchService.
        """
        client_options = (
            ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
            if location != "global"
            else None
        )
        client = discoveryengine.SearchServiceAsyncClient(client_options=client_options)

        serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config"
        return cls(client, serving_config)

    async def search(self, search_query: str) -> List[Document]:
        """
        Performs an asynchronous search against the configured engine.

        Args:
            search_query: The user's query string.

        Returns:
            A list of Document objects.
        """
        content_search_spec = self._build_content_search_spec()

        request = discoveryengine.SearchRequest(
            serving_config=self.serving_config,
            query=search_query,
            page_size=5,
            content_search_spec=content_search_spec,
            query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
                condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
            ),
            spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
                mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
            ),
        )

        search_results_pager = await self.client.search(request)

        document_list = []
        async for result in search_results_pager:
            document = self._parse_search_result(result)
            document_list.append(document)

        return document_list
    
    def _build_content_search_spec(self) -> discoveryengine.SearchRequest.ContentSearchSpec:
        """Builds the content search specification."""
        return discoveryengine.SearchRequest.ContentSearchSpec(
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=True
            ),
            extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
                max_extractive_segment_count=5,
            ),
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=5,
                include_citations=True,
                ignore_adversarial_query=True,
                ignore_non_summary_seeking_query=True,
                model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
                    preamble="YOUR_CUSTOM_PROMPT"
                ),
                model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelSpec(
                    version="stable",
                ),
            ),
        )

    def _parse_search_result(self, result: discoveryengine.SearchResponse.SearchResult) -> Document:
        """
        Parses a single search result into a Document object.
        """
        derived_struct = result.document.derived_struct_data
        snippet_list = [
            item.get("snippet", "") for item in derived_struct.get("snippets", [])
        ]
        extractive_segments = derived_struct.get("extractive_segments", [])
        page_number = 1
        if extractive_segments:
            page_number = int(extractive_segments[0].get("pageNumber", 1))
        
        segment_content = '\n'.join(
            segment.get("content", "") for segment in extractive_segments
        )
        gcs_link = derived_struct.get("link", "")
        authenticated_link = self._get_authenticated_url(gcs_link)

        return Document(
            title=derived_struct.get("title", ""),
            snippets=snippet_list,
            link=authenticated_link,
            page_number=page_number,
            link_with_page=f'{authenticated_link}#page={page_number}',
            segment_content=segment_content
        )

    @staticmethod
    def _get_authenticated_url(gsutil_uri: str) -> str:
        """
        Converts a gs:// URI to a usable HTTPS URL.
        """
        if not gsutil_uri:
            return ""
        if not gsutil_uri.startswith("gs://"):
            logging.warning(f"URI '{gsutil_uri}' is not a valid GCS URI. Returning as is.")
            return gsutil_uri
        
        path = gsutil_uri.replace("gs://", "", 1)
        return f"https://storage.mtls.cloud.google.com/{path}"
