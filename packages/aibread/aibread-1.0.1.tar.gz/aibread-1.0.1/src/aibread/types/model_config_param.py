# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

from .._types import SequenceNotStr

__all__ = ["ModelConfigParam", "BakedAdapterConfig"]


class BakedAdapterConfig(TypedDict, total=False):
    bias: Optional[str]
    """Bias setting (e.g., 'none')"""

    lora_alpha: Optional[int]
    """LoRA alpha parameter"""

    lora_dropout: Optional[float]
    """LoRA dropout rate"""

    r: Optional[int]
    """LoRA rank"""

    target_modules: Optional[str]
    """Target modules (e.g., 'all-linear')"""


class ModelConfigParam(TypedDict, total=False):
    adapter_paths: Optional[SequenceNotStr[str]]
    """Paths to adapter checkpoints"""

    baked_adapter_config: Optional[BakedAdapterConfig]
    """LoRA adapter configuration"""

    name_or_path: Optional[str]
    """Base model name or path"""

    parent_peft_dir: Optional[str]
    """Parent PEFT directory"""

    type: Optional[str]
    """Model type (e.g., 'bake')"""
