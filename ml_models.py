"""
ML Model Training & Prediction Module
XGBoost, LightGBM, LSTM models for price direction prediction
"""
import pandas as pd
import numpy as np
import pickle
import logging
from typing import Dict, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("LightGBM not available")

try:
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not available")


class PriceDirectionModel:
    """ML model for predicting price direction"""
    
    def __init__(self, model_type: str = 'xgboost'):
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.is_trained = False
    
    def train(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2) -> Dict:
        """Train the model"""
        if X.empty or y.empty:
            logger.error("Empty training data")
            return {}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        self.feature_columns = X.columns.tolist()
        
        # Train model based on type
        if self.model_type == 'xgboost' and XGBOOST_AVAILABLE:
            self.model = self._train_xgboost(X_train_scaled, y_train)
        elif self.model_type == 'lightgbm' and LIGHTGBM_AVAILABLE:
            self.model = self._train_lightgbm(X_train_scaled, y_train)
        elif self.model_type == 'lstm' and TENSORFLOW_AVAILABLE:
            self.model = self._train_lstm(X_train_scaled, y_train)
        else:
            logger.error(f"Model type {self.model_type} not available")
            return {}
        
        # Evaluate
        train_pred = self.model.predict(X_train_scaled)
        test_pred = self.model.predict(X_test_scaled)
        
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        
        self.is_trained = True
        
        logger.info(f"Model trained - Train Acc: {train_acc:.3f}, Test Acc: {test_acc:.3f}")
        
        return {
            'train_accuracy': train_acc,
            'test_accuracy': test_acc,
            'classification_report': classification_report(y_test, test_pred)
        }
    
    def _train_xgboost(self, X_train: np.ndarray, y_train: pd.Series) -> xgb.XGBClassifier:
        """Train XGBoost model"""
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            eval_metric='mlogloss'
        )
        model.fit(X_train, y_train)
        return model
    
    def _train_lightgbm(self, X_train: np.ndarray, y_train: pd.Series) -> lgb.LGBMClassifier:
        """Train LightGBM model"""
        model = lgb.LGBMClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        model.fit(X_train, y_train)
        return model
    
    def _train_lstm(self, X_train: np.ndarray, y_train: pd.Series) -> keras.Model:
        """Train LSTM model"""
        # Reshape for LSTM (samples, timesteps, features)
        # For now, reshape to (samples, 1, features)
        X_train_reshaped = X_train.reshape(X_train.shape[0], 1, X_train.shape[1])
        
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(1, X_train.shape[1])),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(3, activation='softmax')  # 3 classes: -1, 0, 1
        ])
        
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        
        # Convert labels to numeric
        y_train_numeric = y_train.map({-1: 0, 0: 1, 1: 2}).values
        
        model.fit(X_train_reshaped, y_train_numeric, epochs=10, batch_size=32, verbose=0)
        
        return model
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict price direction"""
        if not self.is_trained or self.model is None:
            logger.error("Model not trained")
            return np.array([])
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Predict
        if self.model_type == 'lstm':
            X_reshaped = X_scaled.reshape(X_scaled.shape[0], 1, X_scaled.shape[1])
            predictions = self.model.predict(X_reshaped, verbose=0)
            # Convert back from one-hot
            predictions = np.argmax(predictions, axis=1) - 1  # -1, 0, 1
        else:
            predictions = self.model.predict(X_scaled)
        
        return predictions
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities"""
        if not self.is_trained or self.model is None:
            logger.error("Model not trained")
            return np.array([])
        
        X_scaled = self.scaler.transform(X)
        
        if self.model_type == 'lstm':
            X_reshaped = X_scaled.reshape(X_scaled.shape[0], 1, X_scaled.shape[1])
            probabilities = self.model.predict(X_reshaped, verbose=0)
        else:
            probabilities = self.model.predict_proba(X_scaled)
        
        return probabilities
    
    def save_model(self, filepath: str):
        """Save model to file"""
        if not self.is_trained:
            logger.error("Model not trained")
            return
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'model_type': self.model_type
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load model from file"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.model_type = model_data['model_type']
            self.is_trained = True
            
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")


class NewsSentimentModel:
    """NLP model for news sentiment analysis"""
    
    def __init__(self):
        self.model = None
        self.is_trained = False
    
    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of news text"""
        if not text:
            return {'sentiment': 0.0, 'confidence': 0.0}
        
        # Simple sentiment analysis (can be replaced with FinBERT)
        # For now, use keyword-based approach
        positive_words = ['profit', 'gain', 'rise', 'surge', 'growth', 'positive', 'bullish']
        negative_words = ['loss', 'fall', 'decline', 'drop', 'negative', 'bearish', 'crash']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count == 0 and negative_count == 0:
            sentiment = 0.0
        else:
            sentiment = (positive_count - negative_count) / (positive_count + negative_count + 1)
        
        confidence = min(abs(sentiment) * 2, 1.0)
        
        return {
            'sentiment': np.clip(sentiment, -1.0, 1.0),
            'confidence': confidence
        }
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract named entities (companies, sectors) from text"""
        # Placeholder - would use spaCy NER or FinBERT
        entities = []
        # Simple keyword matching
        companies = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICI']
        for company in companies:
            if company in text.upper():
                entities.append(company)
        return entities


class ModelEnsemble:
    """Ensemble of multiple models for better predictions"""
    
    def __init__(self, models: list):
        self.models = models
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict using ensemble (majority voting)"""
        predictions = []
        for model in self.models:
            if model.is_trained:
                pred = model.predict(X)
                predictions.append(pred)
        
        if not predictions:
            return np.array([])
        
        # Majority voting
        predictions_array = np.array(predictions)
        ensemble_pred = np.apply_along_axis(
            lambda x: np.bincount(x.astype(int) + 1).argmax() - 1,
            axis=0,
            arr=predictions_array
        )
        
        return ensemble_pred
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Average probabilities from all models"""
        probabilities = []
        for model in self.models:
            if model.is_trained:
                prob = model.predict_proba(X)
                probabilities.append(prob)
        
        if not probabilities:
            return np.array([])
        
        # Average probabilities
        avg_prob = np.mean(probabilities, axis=0)
        return avg_prob


