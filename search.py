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
    snippets: List[str] = None
    segment_content: str = ""

def search_documents(
    project_id: str,
    location: str,
    engine_id: str,
    search_query: str,
) -> List[Document]:
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    client = discoveryengine.SearchServiceClient(client_options=client_options)
    serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config"
    logging.info(f"search engine serving config {serving_config}")
    content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
        # For information about snippets, refer to:
        # https://cloud.google.com/generative-ai-app-builder/docs/snippets
        snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
            return_snippet=True
        ),
        extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
            # For information about extractive content, refer to:
            # https://cloud.google.com/generative-ai-app-builder/docs/extractive-content
            max_extractive_segment_count=5,
        ),
        # For information about search summaries, refer to:
        # https://cloud.google.com/generative-ai-app-builder/docs/get-search-summaries
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
    # Refer to the `SearchRequest` reference for all supported fields:
    # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.SearchRequest
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=search_query,
        page_size=10,
        content_search_spec=content_search_spec,
        query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
            condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
        ),
        spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
            mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
        ),
        # Optional: Use fine-tuned model for this request
        # custom_fine_tuning_spec=discoveryengine.CustomFineTuningSpec(
        #     enable_search_adaptor=True
        # ),
    )
    page_result = client.search(request)
    # Handle the response
    document_list = []
    for result in page_result:
        derived_struct_data = result.document.derived_struct_data
        derived_snippets = derived_struct_data.get("snippets", [])
        snippet_list = []
        for i, snippet_item_struct in enumerate(derived_snippets):
            snippet_item = snippet_item_struct.get("snippet", "")
            snippet_list.append(snippet_item)
        extractive_segments = derived_struct_data.get("extractive_segments", [])
        page = 1
        segment_content = ""
        if extractive_segments:
            page = extractive_segments[0].get("pageNumber", 1)
        segment_content = '\n'.join(segment.get("content", "")for segment in extractive_segments) 
        authenticated_link = derived_struct_data.get("link", "")
        document = Document(
            title=derived_struct_data.get("title", ""),
            snippets=snippet_list,
            link=f'{authenticated_url(derived_struct_data.get("link", ""))}#page={page}',
            segment_content=segment_content
        )

        document_list.append(document)

    return document_list

def authenticated_url(
    gsutil_uri: str
) -> str:
    """
    Returns an authenticated URL for a Google Cloud Storage URI.
    
    Args:
        gsutil_uri (str): The Google Cloud Storage URI.
    
    Returns:
        str: The authenticated URL.
    """
    if not gsutil_uri.startswith("gs://"):
        raise ValueError("The provided URI must start with 'gs://'")
    gsutil_uri = gsutil_uri[5:]  # Remove 'gs://'
    return f"https://storage.mtls.cloud.google.com/{gsutil_uri}"