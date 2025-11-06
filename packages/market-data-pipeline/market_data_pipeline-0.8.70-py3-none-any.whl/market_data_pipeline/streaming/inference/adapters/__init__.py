"""
Inference adapters for market_data_pipeline streaming.

Provides different types of inference adapters (rules, ML models).
"""

from .base import InferenceAdapter
from .rules import RulesAdapter
from .sklearn import SklearnAdapter

__all__ = ["InferenceAdapter", "RulesAdapter", "SklearnAdapter"]
