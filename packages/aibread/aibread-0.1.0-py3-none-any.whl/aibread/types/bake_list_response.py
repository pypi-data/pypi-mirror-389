# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .._models import BaseModel

__all__ = ["BakeListResponse", "Item"]


class Item(BaseModel):
    bake_name: str


class BakeListResponse(BaseModel):
    items: List[Item]
