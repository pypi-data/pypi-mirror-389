# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .._models import BaseModel

__all__ = ["RepoListResponse", "Item"]


class Item(BaseModel):
    repo_name: str
    """Repository name"""


class RepoListResponse(BaseModel):
    items: List[Item]
    """List of repositories"""
