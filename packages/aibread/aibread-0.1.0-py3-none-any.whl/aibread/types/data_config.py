# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel

__all__ = ["DataConfig", "Source"]


class Source(BaseModel):
    max_samples: Optional[int] = None
    """Maximum samples to use (-1 for all)"""

    name_or_path: Optional[str] = None
    """Path to data file"""

    type: Optional[str] = None
    """Source type (e.g., 'bake_jsonl')"""


class DataConfig(BaseModel):
    beta: Optional[float] = None
    """Beta parameter for training"""

    cache_dir: Optional[str] = None
    """Cache directory"""

    dl_num_workers: Optional[int] = None
    """Number of dataloader workers"""

    max_length: Optional[int] = None
    """Maximum sequence length"""

    sources: Optional[List[Source]] = None
    """List of data sources"""

    temperature: Optional[float] = None
    """Sampling temperature"""

    train_eval_split: Optional[List[float]] = None
    """Train/eval split ratio [train, eval]"""

    type: Optional[str] = None
    """Data type (e.g., 'single_baker')"""
