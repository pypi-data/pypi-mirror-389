"""
Scikit-learn inference adapter.

Evaluates features using trained ML models.
"""

import logging
from typing import Dict, List, Any, Optional
import pickle
from pathlib import Path
import numpy as np

from .base import InferenceAdapter
from ...bus import SignalEvent

logger = logging.getLogger(__name__)


class SklearnAdapter(InferenceAdapter):
    """Scikit-learn inference adapter."""
    
    def __init__(self, model_path: str = None, feature_names: List[str] = None, **kwargs):
        super().__init__("sklearn", **kwargs)
        self.model_path = model_path
        self.feature_names = feature_names or []
        self.model = None
        self.feature_selector = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the trained model."""
        if not self.model_path or not Path(self.model_path).exists():
            logger.warning(f"Model file not found: {self.model_path}")
            return
        
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            if isinstance(model_data, dict):
                self.model = model_data.get("model")
                self.feature_selector = model_data.get("feature_selector")
                self.feature_names = model_data.get("feature_names", self.feature_names)
            else:
                self.model = model_data
            
            logger.info(f"Loaded model from {self.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load model from {self.model_path}: {e}")
            self.model = None
    
    def _prepare_features(self, features: Dict[str, Any]) -> Optional[np.ndarray]:
        """Prepare features for model prediction."""
        if not self.model:
            return None
        
        try:
            # Extract features in the correct order
            feature_vector = []
            for name in self.feature_names:
                value = features.get(name, 0.0)
                if isinstance(value, (int, float)):
                    feature_vector.append(float(value))
                else:
                    feature_vector.append(0.0)
            
            # Convert to numpy array
            X = np.array(feature_vector).reshape(1, -1)
            
            # Apply feature selection if available
            if self.feature_selector:
                X = self.feature_selector.transform(X)
            
            return X
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return None
    
    async def evaluate(self, symbol: str, features: Dict[str, Any]) -> List[SignalEvent]:
        """Evaluate features using the ML model."""
        if not self.enabled or not self.model:
            return []
        
        try:
            # Prepare features
            X = self._prepare_features(features)
            if X is None:
                return []
            
            # Make prediction
            prediction = self.model.predict(X)[0]
            probability = None
            
            # Get probability if available
            if hasattr(self.model, "predict_proba"):
                proba = self.model.predict_proba(X)[0]
                probability = float(max(proba))
            
            # Create signal
            signal = self._create_signal(
                symbol=symbol,
                name="ml_prediction",
                value=float(prediction),
                score=probability,
                metadata={
                    "model": self.model_path,
                    "features": features,
                    "prediction": float(prediction)
                }
            )
            
            self.last_evaluation = datetime.utcnow()
            self.evaluation_count += 1
            
            return [signal]
            
        except Exception as e:
            logger.error(f"Error in ML model evaluation: {e}")
            return []
    
    def update_model(self, model_path: str) -> None:
        """Update the model file."""
        self.model_path = model_path
        self._load_model()
        logger.info(f"Updated model to {model_path}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if not self.model:
            return {"status": "no_model"}
        
        info = {
            "status": "loaded",
            "model_path": self.model_path,
            "feature_names": self.feature_names,
            "model_type": type(self.model).__name__
        }
        
        if hasattr(self.model, "n_features_in_"):
            info["n_features"] = self.model.n_features_in_
        
        return info
