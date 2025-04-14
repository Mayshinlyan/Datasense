"""
Datasense types
"""
from typing import List, Dict, TypedDict, Literal
from google.genai import types

from pydantic import BaseModel

class UserMessage(BaseModel):
    """
    Represents the user's message in the request payload.
    """
    message: str
    chatHistory: List[dict]
