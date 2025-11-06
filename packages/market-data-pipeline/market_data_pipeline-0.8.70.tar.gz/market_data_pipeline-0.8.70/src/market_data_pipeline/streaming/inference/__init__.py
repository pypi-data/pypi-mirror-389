"""
Inference module for market_data_pipeline streaming.

Provides signal generation and inference capabilities.
"""

from .engine import InferenceEngine
from .adapters.rules import RulesAdapter
from .adapters.sklearn import SklearnAdapter

__all__ = ["InferenceEngine", "RulesAdapter", "SklearnAdapter"]
