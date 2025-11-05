# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import TypedDict

__all__ = ["DataConfigParam", "Source"]


class Source(TypedDict, total=False):
    max_samples: Optional[int]
    """Maximum samples to use (-1 for all)"""

    name_or_path: Optional[str]
    """Path to data file"""

    type: Optional[str]
    """Source type (e.g., 'bake_jsonl')"""


class DataConfigParam(TypedDict, total=False):
    beta: Optional[float]
    """Beta parameter for training"""

    cache_dir: Optional[str]
    """Cache directory"""

    dl_num_workers: Optional[int]
    """Number of dataloader workers"""

    max_length: Optional[int]
    """Maximum sequence length"""

    sources: Optional[Iterable[Source]]
    """List of data sources"""

    temperature: Optional[float]
    """Sampling temperature"""

    train_eval_split: Optional[Iterable[float]]
    """Train/eval split ratio [train, eval]"""

    type: Optional[str]
    """Data type (e.g., 'single_baker')"""
