# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List

from .._models import BaseModel

__all__ = ["TargetBatchSetResponse"]


class TargetBatchSetResponse(BaseModel):
    created: List[str]
    """Successfully created targets"""

    failed: Dict[str, str]
    """Failed targets with error messages"""
