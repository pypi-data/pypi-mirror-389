# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel

__all__ = ["ModelConfig", "BakedAdapterConfig"]


class BakedAdapterConfig(BaseModel):
    bias: Optional[str] = None
    """Bias setting (e.g., 'none')"""

    lora_alpha: Optional[int] = None
    """LoRA alpha parameter"""

    lora_dropout: Optional[float] = None
    """LoRA dropout rate"""

    r: Optional[int] = None
    """LoRA rank"""

    target_modules: Optional[str] = None
    """Target modules (e.g., 'all-linear')"""


class ModelConfig(BaseModel):
    adapter_paths: Optional[List[str]] = None
    """Paths to adapter checkpoints"""

    baked_adapter_config: Optional[BakedAdapterConfig] = None
    """LoRA adapter configuration"""

    name_or_path: Optional[str] = None
    """Base model name or path"""

    parent_peft_dir: Optional[str] = None
    """Parent PEFT directory"""

    type: Optional[str] = None
    """Model type (e.g., 'bake')"""
