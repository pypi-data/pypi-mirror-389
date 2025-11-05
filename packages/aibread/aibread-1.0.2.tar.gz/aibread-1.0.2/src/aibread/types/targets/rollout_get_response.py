# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from ..._models import BaseModel

__all__ = ["RolloutGetResponse"]


class RolloutGetResponse(BaseModel):
    lines: int
    """Number of output lines"""

    status: str
    """Job status: not_started, running, complete"""

    parameters: Optional[Dict[str, object]] = None
    """Job parameters"""
