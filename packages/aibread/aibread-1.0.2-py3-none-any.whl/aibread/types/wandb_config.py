# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel

__all__ = ["WandbConfig"]


class WandbConfig(BaseModel):
    enable: Optional[bool] = None
    """Enable wandb logging"""

    entity: Optional[str] = None
    """Wandb entity/team"""

    name: Optional[str] = None
    """Run name"""

    project: Optional[str] = None
    """Wandb project name"""

    tags: Optional[List[str]] = None
    """Tags for this run"""
