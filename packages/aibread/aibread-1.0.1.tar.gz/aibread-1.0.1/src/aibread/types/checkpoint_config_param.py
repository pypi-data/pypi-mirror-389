# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["CheckpointConfigParam"]


class CheckpointConfigParam(TypedDict, total=False):
    output_dir: Optional[str]
    """Output directory for checkpoints"""

    save_end_of_training: Optional[bool]
    """Save checkpoint at end of training"""

    save_interval: Optional[int]
    """Save every N steps"""

    type: Optional[str]
    """Checkpoint type (e.g., 'huggingface')"""
