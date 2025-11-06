"""
Rules-based inference adapter.

Evaluates features using rule-based logic.
"""

import logging
from typing import Dict, List, Any
import yaml
from pathlib import Path

from .base import InferenceAdapter
from ...bus import SignalEvent

logger = logging.getLogger(__name__)


class RulesAdapter(InferenceAdapter):
    """Rules-based inference adapter."""
    
    def __init__(self, rules_file: str = None, **kwargs):
        super().__init__("rules", **kwargs)
        self.rules_file = rules_file
        self.rules = []
        self._load_rules()
    
    def _load_rules(self) -> None:
        """Load rules from file."""
        if not self.rules_file or not Path(self.rules_file).exists():
            # Default rules
            self.rules = [
                {
                    "name": "price_momentum_up",
                    "condition": "momentum > 0.01",
                    "signal": 1.0,
                    "score": 0.8
                },
                {
                    "name": "price_momentum_down", 
                    "condition": "momentum < -0.01",
                    "signal": -1.0,
                    "score": 0.8
                },
                {
                    "name": "high_volatility",
                    "condition": "volatility > 0.3",
                    "signal": 0.0,
                    "score": 0.9
                },
                {
                    "name": "rsi_overbought",
                    "condition": "rsi > 70",
                    "signal": -1.0,
                    "score": 0.7
                },
                {
                    "name": "rsi_oversold",
                    "condition": "rsi < 30",
                    "signal": 1.0,
                    "score": 0.7
                }
            ]
            return
        
        try:
            with open(self.rules_file, 'r') as f:
                self.rules = yaml.safe_load(f)
            logger.info(f"Loaded {len(self.rules)} rules from {self.rules_file}")
        except Exception as e:
            logger.error(f"Failed to load rules from {self.rules_file}: {e}")
            self.rules = []
    
    def _evaluate_condition(self, condition: str, features: Dict[str, Any]) -> bool:
        """Evaluate a condition string against features."""
        try:
            # Simple condition evaluation
            # Replace feature names with values
            expr = condition
            for key, value in features.items():
                if isinstance(value, (int, float)):
                    expr = expr.replace(key, str(value))
            
            # Evaluate expression
            result = eval(expr)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False
    
    async def evaluate(self, symbol: str, features: Dict[str, Any]) -> List[SignalEvent]:
        """Evaluate features using rules."""
        if not self.enabled:
            return []
        
        signals = []
        
        for rule in self.rules:
            try:
                # Check if condition is met
                if self._evaluate_condition(rule["condition"], features):
                    # Create signal
                    signal = self._create_signal(
                        symbol=symbol,
                        name=rule["name"],
                        value=rule["signal"],
                        score=rule.get("score", 0.5),
                        metadata={
                            "rule": rule["name"],
                            "condition": rule["condition"],
                            "features": features
                        }
                    )
                    signals.append(signal)
                    
                    logger.debug(f"Rule '{rule['name']}' triggered for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error evaluating rule '{rule.get('name', 'unknown')}': {e}")
                continue
        
        self.last_evaluation = datetime.utcnow()
        self.evaluation_count += 1
        
        return signals
    
    def add_rule(self, rule: Dict[str, Any]) -> None:
        """Add a new rule."""
        self.rules.append(rule)
        logger.info(f"Added rule: {rule.get('name', 'unnamed')}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name."""
        original_count = len(self.rules)
        self.rules = [r for r in self.rules if r.get("name") != rule_name]
        removed = len(self.rules) < original_count
        
        if removed:
            logger.info(f"Removed rule: {rule_name}")
        else:
            logger.warning(f"Rule not found: {rule_name}")
        
        return removed
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """Get all rules."""
        return self.rules.copy()
    
    def save_rules(self, file_path: str) -> None:
        """Save rules to file."""
        try:
            with open(file_path, 'w') as f:
                yaml.dump(self.rules, f, default_flow_style=False)
            logger.info(f"Saved {len(self.rules)} rules to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save rules to {file_path}: {e}")
            raise
