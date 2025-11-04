# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["CheckpointConfig"]


class CheckpointConfig(BaseModel):
    output_dir: Optional[str] = None
    """Output directory for checkpoints"""

    save_end_of_training: Optional[bool] = None
    """Save checkpoint at end of training"""

    save_interval: Optional[int] = None
    """Save every N steps"""

    type: Optional[str] = None
    """Checkpoint type (e.g., 'huggingface')"""
