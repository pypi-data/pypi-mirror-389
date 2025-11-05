# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["DeepspeedConfig", "ZeroOptimization"]


class ZeroOptimization(BaseModel):
    stage: Optional[int] = None
    """ZeRO stage (0, 1, 2, or 3)"""


class DeepspeedConfig(BaseModel):
    zero_optimization: Optional[ZeroOptimization] = None
    """DeepSpeed ZeRO optimization configuration"""
