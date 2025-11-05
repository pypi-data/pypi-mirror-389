# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .._models import BaseModel

__all__ = ["PromptListResponse", "Item"]


class Item(BaseModel):
    prompt_name: str
    """Prompt identifier"""


class PromptListResponse(BaseModel):
    items: List[Item]
    """List of prompts"""
