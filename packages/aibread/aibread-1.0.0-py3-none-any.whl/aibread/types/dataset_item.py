# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["DatasetItem"]


class DatasetItem(BaseModel):
    target: str
    """Target name"""

    weight: Optional[float] = None
    """Dataset weight"""
