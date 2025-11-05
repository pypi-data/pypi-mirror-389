# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List

from .._models import BaseModel

__all__ = ["BakeBatchSetResponse"]


class BakeBatchSetResponse(BaseModel):
    created: List[str]
    """Successfully created bakes"""

    failed: Dict[str, str]
    """Failed bakes with error messages"""
