# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .._models import BaseModel

__all__ = ["TargetListResponse", "Item"]


class Item(BaseModel):
    target_name: str


class TargetListResponse(BaseModel):
    items: List[Item]
