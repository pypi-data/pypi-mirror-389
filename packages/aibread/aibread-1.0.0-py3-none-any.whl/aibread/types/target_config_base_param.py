# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable, Optional
from typing_extensions import Required, TypedDict

from .._types import SequenceNotStr

__all__ = ["TargetConfigBaseParam", "Generator"]


class Generator(TypedDict, total=False):
    type: Required[str]
    """Generator type: oneshot_qs, hardcoded, persona, from_dataset, custom"""

    dataset: Optional[str]
    """Dataset name for from_dataset"""

    model: Optional[str]
    """Model name for oneshot_qs"""

    numq: Optional[int]
    """Number of questions to generate"""

    questions: Optional[SequenceNotStr[str]]
    """Hardcoded questions"""

    seed: Optional[int]
    """Random seed"""

    temperature: Optional[float]
    """Generation temperature (0.0-2.0)"""

    template_path: Optional[str]
    """Custom template path"""


class TargetConfigBaseParam(TypedDict, total=False):
    extra_kwargs: Optional[Dict[str, object]]
    """Additional kwargs passed to chat.completions.create()"""

    generators: Optional[Iterable[Generator]]
    """Data generation strategies"""

    max_concurrency: Optional[int]
    """Maximum concurrent requests"""

    max_tokens: Optional[int]
    """Maximum tokens to generate"""

    model_name: Optional[str]
    """Base model for rollout"""

    num_traj_per_stimulus: Optional[int]
    """Number of trajectories per stimulus"""

    temperature: Optional[float]
    """Generation temperature (0.0-2.0)"""

    u: Optional[str]
    """Unconditioned stimulus prompt name"""

    v: Optional[str]
    """Conditioned stimulus prompt name"""
