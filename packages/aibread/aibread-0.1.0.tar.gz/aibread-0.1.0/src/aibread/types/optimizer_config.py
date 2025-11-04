# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["OptimizerConfig"]


class OptimizerConfig(BaseModel):
    learning_rate: Optional[float] = None
    """Learning rate"""
