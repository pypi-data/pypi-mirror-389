# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional

from ..._models import BaseModel

__all__ = ["RolloutGetOutputResponse"]


class RolloutGetOutputResponse(BaseModel):
    has_more: bool
    """Whether more data is available"""

    limit: int
    """Page size"""

    lines: int
    """Total number of output lines"""

    offset: int
    """Starting line offset"""

    output: List[Dict[str, object]]
    """Paginated output data"""

    status: str
    """Job status: not_started, running, complete"""

    parameters: Optional[Dict[str, object]] = None
    """Rollout parameters"""
