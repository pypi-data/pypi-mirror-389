# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel
from .data_config import DataConfig
from .dataset_item import DatasetItem
from .model_config import ModelConfig
from .wandb_config import WandbConfig
from .deepspeed_config import DeepspeedConfig
from .optimizer_config import OptimizerConfig
from .scheduler_config import SchedulerConfig
from .checkpoint_config import CheckpointConfig

__all__ = ["BakeResponse", "Config"]


class Config(BaseModel):
    checkpoint: Optional[List[CheckpointConfig]] = None
    """Checkpoint configuration"""

    data: Optional[DataConfig] = None
    """Data configuration for training"""

    datasets: Optional[List[DatasetItem]] = None
    """List of datasets"""

    deepspeed: Optional[DeepspeedConfig] = None
    """DeepSpeed configuration"""

    epochs: Optional[int] = None
    """Number of epochs"""

    eval_interval: Optional[int] = None
    """Evaluation interval"""

    gradient_accumulation_steps: Optional[int] = None
    """Gradient accumulation steps"""

    micro_batch_size: Optional[int] = None
    """Micro batch size"""

    model: Optional[ModelConfig] = None
    """Model configuration for baking"""

    optimizer: Optional[OptimizerConfig] = None
    """Optimizer configuration"""

    scheduler: Optional[SchedulerConfig] = None
    """Learning rate scheduler configuration"""

    seed: Optional[int] = None
    """Random seed"""

    total_trajectories: Optional[int] = None
    """Total trajectories"""

    train_log_iter_interval: Optional[int] = None
    """Training log interval"""

    type: Optional[str] = None
    """Bake type (e.g., 'single_baker')"""

    wandb: Optional[WandbConfig] = None
    """Weights & Biases configuration"""


class BakeResponse(BaseModel):
    bake_name: str

    config: Config
    """Base bake configuration fields (for responses - all optional)"""

    status: str
    """Status: 'incomplete' or 'complete'"""

    job: Optional[str] = None
    """Job type if incomplete"""
