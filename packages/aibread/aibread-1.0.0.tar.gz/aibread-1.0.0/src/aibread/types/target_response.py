# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel
from .target_config_base import TargetConfigBase

__all__ = ["TargetResponse"]


class TargetResponse(BaseModel):
    config: TargetConfigBase
    """Base target configuration"""

    target_name: str
