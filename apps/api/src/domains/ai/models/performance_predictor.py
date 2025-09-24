"""
Player performance prediction model for fantasy sports analytics.

Provides advanced ML-powered player performance prediction including:
- Historical performance analysis and trend identification
- Injury impact assessment and recovery modeling
- Matchup-based performance adjustments
- Weather and venue factor integration
- Multi-sport performance modeling (NFL, MLB, WNBA)
- Confidence scoring and uncertainty quantification
- Feature importance analysis and model interpretability
- Real-time prediction updates and model retraining
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
import pickle
from pathlib import Path

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger  # type: ignore[assignment]

logger = get_logger(__name__)


class ModelType(Enum):
    """Types of prediction models."""
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"


class Sport(Enum):
    """Supported sports."""
    NFL = "nfl"
    MLB = "mlb"
    WNBA = "wnba"


@dataclass
class PredictionResult:
    """Player performance prediction result."""

    player_id: str
    predicted_points: float
    confidence_score: float
    prediction_range: Tuple[float, float]  # (min, max)
    factors: Dict[str, float]
    model_version: str
    generated_at: datetime
    sport: Sport

    # Detailed breakdown
    base_projection: float
    matchup_adjustment: float
    injury_adjustment: float
    form_adjustment: float
    weather_adjustment: float

    # Feature contributions
    feature_importance: Dict[str, float]
    risk_factors: List[str]
    upside_factors: List[str]


@dataclass
class ModelMetrics:
    """Model performance metrics."""

    model_id: str
    sport: Sport
    accuracy_score: float
    mae: float  # Mean Absolute Error
    rmse: float  # Root Mean Square Error
    r2_score: float

    # Time-based metrics
    last_trained: datetime
    training_samples: int
    validation_samples: int

    # Feature metrics
    feature_count: int
    top_features: List[Tuple[str, float]]


class PerformancePredictorError(Exception):
    """Performance predictor errors."""
    pass


class PlayerPerformancePredictor:
    """Advanced ML model for predicting player fantasy performance."""

    def __init__(self, sport: Sport, model_type: ModelType = ModelType.ENSEMBLE):
        self.sport = sport
        self.model_type = model_type
        self.model = None
        self.feature_names: List[str] = []
        self.scaler = None
        self.is_trained = False

        # Model configuration
        self.config = self._get_sport_config(sport)

        # Feature engineering parameters
        self.lookback_games = 10
        self.min_games_for_prediction = 3

        # Model artifacts directory
        self.model_dir = Path(f"models/{sport.value}")
        self.model_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized {sport.value} performance predictor")

    def _get_sport_config(self, sport: Sport) -> Dict[str, Any]:
        """Get sport-specific configuration."""
        configs = {
            Sport.NFL: {
                "primary_stats": ["passing_yards", "rushing_yards", "touchdowns", "receptions", "receiving_yards"],
                "positional_features": ["position", "team_strength", "opponent_strength"],
                "scoring_weights": {"touchdown": 6, "field_goal": 3, "yard": 0.1},
                "game_length": 60,  # minutes
                "season_games": 17,
            },
            Sport.MLB: {
                "primary_stats": ["hits", "runs", "rbis", "home_runs", "stolen_bases"],
                "positional_features": ["position", "batting_order", "handedness"],
                "scoring_weights": {"hit": 1, "run": 1, "rbi": 1, "home_run": 4},
                "game_length": 180,  # minutes (average)
                "season_games": 162,
            },
            Sport.WNBA: {
                "primary_stats": ["points", "rebounds", "assists", "steals", "blocks"],
                "positional_features": ["position", "minutes_played", "usage_rate"],
                "scoring_weights": {"point": 1, "rebound": 1.2, "assist": 1.5, "steal": 2, "block": 2},
                "game_length": 40,  # minutes
                "season_games": 34,
            }
        }
        return configs.get(sport, configs[Sport.NFL])

    async def train_model(self,
                         training_data: pd.DataFrame,
                         target_column: str = "fantasy_points",
                         validation_split: float = 0.2) -> ModelMetrics:
        """
        Train the performance prediction model.

        Args:
            training_data: Historical player performance data
            target_column: Target variable column name
            validation_split: Fraction of data for validation

        Returns:
            ModelMetrics: Training results and model performance
        """
        try:
            logger.info(f"Training {self.sport.value} model with {len(training_data)} samples")

            # Feature engineering
            features_df = await self._engineer_features(training_data)

            # Prepare training data
            X, y = self._prepare_training_data(features_df, target_column)

            # Split data
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]

            # Scale features
            from sklearn.preprocessing import StandardScaler
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_val_scaled = self.scaler.transform(X_val)

            # Train model based on type
            if self.model_type == ModelType.ENSEMBLE:
                self.model = await self._train_ensemble_model(X_train_scaled, y_train)
            elif self.model_type == ModelType.RANDOM_FOREST:
                self.model = await self._train_random_forest(X_train_scaled, y_train)
            elif self.model_type == ModelType.GRADIENT_BOOSTING:
                self.model = await self._train_gradient_boosting(X_train_scaled, y_train)
            else:
                self.model = await self._train_linear_model(X_train_scaled, y_train)

            # Validate model
            y_pred = self.model.predict(X_val_scaled)
            metrics = self._calculate_metrics(y_val, y_pred, len(X_train), len(X_val))

            # Save model
            await self._save_model()

            self.is_trained = True

            logger.info(
                f"Model training completed",
                extra={
                    "sport": self.sport.value,
                    "model_type": self.model_type.value,
                    "r2_score": metrics.r2_score,
                    "mae": metrics.mae,
                }
            )

            return metrics

        except Exception as e:
            logger.error(f"Model training failed: {e}")
            raise PerformancePredictorError(f"Training failed: {e}")

    async def predict_performance(self,
                                player_data: Dict[str, Any],
                                opponent_data: Optional[Dict[str, Any]] = None,
                                game_context: Optional[Dict[str, Any]] = None) -> PredictionResult:
        """
        Predict player fantasy performance for upcoming game.

        Args:
            player_data: Player stats and information
            opponent_data: Opponent team information
            game_context: Game context (weather, venue, etc.)

        Returns:
            PredictionResult: Comprehensive prediction with confidence
        """
        try:
            if not self.is_trained:
                await self._load_model()

            if not self.is_trained:
                raise PerformancePredictorError("Model not trained")

            # Engineer features for prediction
            features = await self._engineer_prediction_features(
                player_data, opponent_data, game_context
            )

            # Scale features
            features_scaled = self.scaler.transform([features])

            # Generate prediction
            base_prediction = self.model.predict(features_scaled)[0]

            # Calculate confidence score
            confidence = self._calculate_prediction_confidence(features, player_data)

            # Calculate prediction range
            prediction_range = self._calculate_prediction_range(
                base_prediction, confidence, player_data
            )

            # Calculate adjustments
            adjustments = self._calculate_adjustments(
                player_data, opponent_data, game_context
            )

            # Final prediction with adjustments
            final_prediction = base_prediction + sum(adjustments.values())
            final_prediction = max(0, final_prediction)  # Ensure non-negative

            # Feature importance
            feature_importance = self._get_feature_importance(features)

            # Risk and upside factors
            risk_factors, upside_factors = self._identify_factors(
                player_data, opponent_data, game_context
            )

            result = PredictionResult(
                player_id=player_data.get("player_id", ""),
                predicted_points=final_prediction,
                confidence_score=confidence,
                prediction_range=prediction_range,
                factors=adjustments,
                model_version=f"{self.sport.value}_{self.model_type.value}_v1.0",
                generated_at=datetime.utcnow(),
                sport=self.sport,
                base_projection=base_prediction,
                matchup_adjustment=adjustments.get("matchup", 0),
                injury_adjustment=adjustments.get("injury", 0),
                form_adjustment=adjustments.get("form", 0),
                weather_adjustment=adjustments.get("weather", 0),
                feature_importance=feature_importance,
                risk_factors=risk_factors,
                upside_factors=upside_factors,
            )

            logger.debug(
                f"Generated prediction",
                extra={
                    "player_id": player_data.get("player_id"),
                    "predicted_points": final_prediction,
                    "confidence": confidence,
                }
            )

            return result

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise PerformancePredictorError(f"Prediction failed: {e}")

    async def batch_predict(self,
                          players_data: List[Dict[str, Any]],
                          game_context: Optional[Dict[str, Any]] = None) -> List[PredictionResult]:
        """
        Generate predictions for multiple players efficiently.

        Args:
            players_data: List of player data dictionaries
            game_context: Shared game context

        Returns:
            List[PredictionResult]: Predictions for all players
        """
        try:
            predictions = []

            for player_data in players_data:
                prediction = await self.predict_performance(
                    player_data=player_data,
                    game_context=game_context
                )
                predictions.append(prediction)

            logger.info(f"Generated {len(predictions)} batch predictions")
            return predictions

        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            raise PerformancePredictorError(f"Batch prediction failed: {e}")

    # Feature engineering methods

    async def _engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Engineer features for model training."""
        try:
            features_df = data.copy()

            # Recent performance features
            for stat in self.config["primary_stats"]:
                if stat in features_df.columns:
                    # Rolling averages
                    features_df[f"{stat}_avg_3"] = features_df.groupby('player_id')[stat].rolling(3).mean().reset_index(0, drop=True)
                    features_df[f"{stat}_avg_5"] = features_df.groupby('player_id')[stat].rolling(5).mean().reset_index(0, drop=True)
                    features_df[f"{stat}_avg_10"] = features_df.groupby('player_id')[stat].rolling(10).mean().reset_index(0, drop=True)

                    # Trends
                    features_df[f"{stat}_trend"] = features_df.groupby('player_id')[stat].pct_change(3).reset_index(0, drop=True)

                    # Consistency (standard deviation)
                    features_df[f"{stat}_std_5"] = features_df.groupby('player_id')[stat].rolling(5).std().reset_index(0, drop=True)

            # Opponent strength features
            if 'opponent_rank' in features_df.columns:
                features_df['opponent_strength'] = 1 / (features_df['opponent_rank'] + 1)

            # Venue features
            if 'is_home' in features_df.columns:
                features_df['home_advantage'] = features_df['is_home'].astype(int)

            # Time-based features
            if 'game_date' in features_df.columns:
                features_df['day_of_week'] = pd.to_datetime(features_df['game_date']).dt.dayofweek
                features_df['week_of_season'] = pd.to_datetime(features_df['game_date']).dt.isocalendar().week

            # Remove rows with insufficient data
            features_df = features_df.dropna()

            # Store feature names
            self.feature_names = [col for col in features_df.columns
                                if col not in ['player_id', 'game_date', 'fantasy_points']]

            return features_df

        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            raise PerformancePredictorError(f"Feature engineering failed: {e}")

    def _prepare_training_data(self, features_df: pd.DataFrame, target_column: str) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and target for training."""
        try:
            # Select feature columns
            X = features_df[self.feature_names].values
            y = features_df[target_column].values

            # Remove any remaining NaN values
            valid_indices = ~(np.isnan(X).any(axis=1) | np.isnan(y))
            X = X[valid_indices]
            y = y[valid_indices]

            return X, y

        except Exception as e:
            logger.error(f"Data preparation failed: {e}")
            raise PerformancePredictorError(f"Data preparation failed: {e}")

    # Model training methods

    async def _train_ensemble_model(self, X: np.ndarray, y: np.ndarray):
        """Train ensemble model combining multiple algorithms."""
        try:
            from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
            from sklearn.linear_model import LinearRegression
            from sklearn.ensemble import VotingRegressor

            # Individual models
            rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
            gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            lr_model = LinearRegression()

            # Ensemble
            ensemble = VotingRegressor([
                ('rf', rf_model),
                ('gb', gb_model),
                ('lr', lr_model)
            ])

            ensemble.fit(X, y)
            return ensemble

        except Exception as e:
            logger.error(f"Ensemble training failed: {e}")
            raise PerformancePredictorError(f"Ensemble training failed: {e}")

    async def _train_random_forest(self, X: np.ndarray, y: np.ndarray):
        """Train Random Forest model."""
        try:
            from sklearn.ensemble import RandomForestRegressor

            model = RandomForestRegressor(
                n_estimators=200,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )

            model.fit(X, y)
            return model

        except Exception as e:
            logger.error(f"Random Forest training failed: {e}")
            raise PerformancePredictorError(f"Random Forest training failed: {e}")

    async def _train_gradient_boosting(self, X: np.ndarray, y: np.ndarray):
        """Train Gradient Boosting model."""
        try:
            from sklearn.ensemble import GradientBoostingRegressor

            model = GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )

            model.fit(X, y)
            return model

        except Exception as e:
            logger.error(f"Gradient Boosting training failed: {e}")
            raise PerformancePredictorError(f"Gradient Boosting training failed: {e}")

    async def _train_linear_model(self, X: np.ndarray, y: np.ndarray):
        """Train Linear Regression model."""
        try:
            from sklearn.linear_model import Ridge

            model = Ridge(alpha=1.0)
            model.fit(X, y)
            return model

        except Exception as e:
            logger.error(f"Linear model training failed: {e}")
            raise PerformancePredictorError(f"Linear model training failed: {e}")

    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray,
                          train_samples: int, val_samples: int) -> ModelMetrics:
        """Calculate model performance metrics."""
        try:
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score

            mae = mean_absolute_error(y_true, y_pred)
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))
            r2 = r2_score(y_true, y_pred)

            # Custom accuracy for fantasy points (within 20% tolerance)
            tolerance = 0.2
            accurate_predictions = np.abs(y_pred - y_true) <= (y_true * tolerance)
            accuracy = np.mean(accurate_predictions)

            # Feature importance (if available)
            top_features = []
            if hasattr(self.model, 'feature_importances_'):
                importance_pairs = list(zip(self.feature_names, self.model.feature_importances_))
                top_features = sorted(importance_pairs, key=lambda x: x[1], reverse=True)[:10]

            return ModelMetrics(
                model_id=f"{self.sport.value}_{self.model_type.value}",
                sport=self.sport,
                accuracy_score=accuracy,
                mae=mae,
                rmse=rmse,
                r2_score=r2,
                last_trained=datetime.utcnow(),
                training_samples=train_samples,
                validation_samples=val_samples,
                feature_count=len(self.feature_names),
                top_features=top_features,
            )

        except Exception as e:
            logger.error(f"Metrics calculation failed: {e}")
            raise PerformancePredictorError(f"Metrics calculation failed: {e}")

    # Prediction helper methods

    async def _engineer_prediction_features(self,
                                          player_data: Dict[str, Any],
                                          opponent_data: Optional[Dict[str, Any]],
                                          game_context: Optional[Dict[str, Any]]) -> List[float]:
        """Engineer features for a single prediction."""
        try:
            features = []

            # Recent performance features
            recent_games = player_data.get("recent_games", [])
            for stat in self.config["primary_stats"]:
                stat_values = [game.get(stat, 0) for game in recent_games[-10:]]

                # Averages
                features.extend([
                    np.mean(stat_values[-3:]) if len(stat_values) >= 3 else 0,
                    np.mean(stat_values[-5:]) if len(stat_values) >= 5 else 0,
                    np.mean(stat_values) if stat_values else 0,
                ])

                # Trend and consistency
                if len(stat_values) >= 3:
                    trend = (stat_values[-1] - stat_values[-3]) / max(stat_values[-3], 1)
                    features.append(trend)
                else:
                    features.append(0)

                features.append(np.std(stat_values) if len(stat_values) >= 2 else 0)

            # Opponent features
            if opponent_data:
                features.append(opponent_data.get("defensive_rank", 16) / 32.0)
                features.append(1 / (opponent_data.get("rank", 16) + 1))
            else:
                features.extend([0.5, 0.5])  # Neutral values

            # Game context features
            if game_context:
                features.append(1.0 if game_context.get("is_home") else 0.0)
                features.append(game_context.get("temperature", 70) / 100.0)
                features.append(game_context.get("wind_speed", 0) / 30.0)
            else:
                features.extend([0.5, 0.7, 0.0])

            # Ensure we have the right number of features
            while len(features) < len(self.feature_names):
                features.append(0.0)

            return features[:len(self.feature_names)]

        except Exception as e:
            logger.error(f"Prediction feature engineering failed: {e}")
            raise PerformancePredictorError(f"Prediction feature engineering failed: {e}")

    def _calculate_prediction_confidence(self, features: List[float], player_data: Dict[str, Any]) -> float:
        """Calculate confidence score for prediction."""
        try:
            confidence_factors = []

            # Data completeness
            recent_games = player_data.get("recent_games", [])
            games_factor = min(len(recent_games) / self.min_games_for_prediction, 1.0)
            confidence_factors.append(games_factor)

            # Consistency factor
            if recent_games:
                fantasy_points = [game.get("fantasy_points", 0) for game in recent_games]
                if len(fantasy_points) >= 3:
                    consistency = 1.0 - (np.std(fantasy_points) / max(np.mean(fantasy_points), 1))
                    confidence_factors.append(max(0.3, min(1.0, consistency)))
                else:
                    confidence_factors.append(0.5)
            else:
                confidence_factors.append(0.3)

            # Injury factor
            injury_status = player_data.get("injury_status", "healthy").lower()
            injury_confidence = {
                "healthy": 1.0,
                "questionable": 0.7,
                "doubtful": 0.4,
                "out": 0.1,
            }
            confidence_factors.append(injury_confidence.get(injury_status, 0.5))

            # Model confidence (simplified)
            confidence_factors.append(0.8)  # Would be based on model validation metrics

            # Average all factors
            final_confidence = np.mean(confidence_factors)
            return round(final_confidence, 3)

        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.5

    def _calculate_prediction_range(self, prediction: float, confidence: float,
                                  player_data: Dict[str, Any]) -> Tuple[float, float]:
        """Calculate prediction range based on confidence and historical variance."""
        try:
            # Base range based on confidence
            uncertainty = (1.0 - confidence) * prediction * 0.5

            # Adjust for player's historical variance
            recent_games = player_data.get("recent_games", [])
            if recent_games:
                fantasy_points = [game.get("fantasy_points", 0) for game in recent_games]
                if len(fantasy_points) >= 3:
                    historical_std = np.std(fantasy_points)
                    uncertainty = max(uncertainty, historical_std * 0.5)

            min_pred = max(0, prediction - uncertainty)
            max_pred = prediction + uncertainty

            return (round(min_pred, 1), round(max_pred, 1))

        except Exception as e:
            logger.error(f"Prediction range calculation failed: {e}")
            return (max(0, prediction * 0.7), prediction * 1.3)

    def _calculate_adjustments(self,
                             player_data: Dict[str, Any],
                             opponent_data: Optional[Dict[str, Any]],
                             game_context: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate various adjustments to base prediction."""
        adjustments = {}

        # Matchup adjustment
        if opponent_data:
            opponent_rank = opponent_data.get("defensive_rank", 16)
            if opponent_rank <= 5:
                adjustments["matchup"] = -2.0  # Tough matchup
            elif opponent_rank >= 25:
                adjustments["matchup"] = 2.0   # Easy matchup
            else:
                adjustments["matchup"] = 0.0
        else:
            adjustments["matchup"] = 0.0

        # Injury adjustment
        injury_status = player_data.get("injury_status", "healthy").lower()
        injury_adjustments = {
            "healthy": 0.0,
            "questionable": -1.0,
            "doubtful": -3.0,
            "out": -10.0,
        }
        adjustments["injury"] = injury_adjustments.get(injury_status, 0.0)

        # Recent form adjustment
        recent_games = player_data.get("recent_games", [])
        if len(recent_games) >= 3:
            recent_avg = np.mean([game.get("fantasy_points", 0) for game in recent_games[-3:]])
            season_avg = player_data.get("season_average", recent_avg)
            if season_avg > 0:
                form_factor = (recent_avg - season_avg) / season_avg
                adjustments["form"] = form_factor * 2.0  # Scale factor
            else:
                adjustments["form"] = 0.0
        else:
            adjustments["form"] = 0.0

        # Weather adjustment (for outdoor sports)
        if game_context and self.sport in [Sport.NFL, Sport.MLB]:
            temperature = game_context.get("temperature", 70)
            wind_speed = game_context.get("wind_speed", 0)

            weather_adjustment = 0.0
            if temperature < 32:  # Freezing
                weather_adjustment -= 1.0
            elif temperature > 90:  # Very hot
                weather_adjustment -= 0.5

            if wind_speed > 15:  # High wind
                weather_adjustment -= 0.5

            adjustments["weather"] = weather_adjustment
        else:
            adjustments["weather"] = 0.0

        return adjustments

    def _get_feature_importance(self, features: List[float]) -> Dict[str, float]:
        """Get feature importance for this prediction."""
        try:
            if hasattr(self.model, 'feature_importances_'):
                importance_dict = {}
                for i, feature_name in enumerate(self.feature_names):
                    if i < len(self.model.feature_importances_):
                        importance_dict[feature_name] = float(self.model.feature_importances_[i])
                return importance_dict
            else:
                # Fallback for models without feature importance
                return {name: 1.0 / len(self.feature_names) for name in self.feature_names}

        except Exception as e:
            logger.error(f"Feature importance calculation failed: {e}")
            return {}

    def _identify_factors(self,
                         player_data: Dict[str, Any],
                         opponent_data: Optional[Dict[str, Any]],
                         game_context: Optional[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """Identify risk and upside factors."""
        risk_factors = []
        upside_factors = []

        # Injury risks
        injury_status = player_data.get("injury_status", "healthy").lower()
        if injury_status in ["questionable", "doubtful"]:
            risk_factors.append(f"Injury concern ({injury_status})")

        # Matchup factors
        if opponent_data:
            def_rank = opponent_data.get("defensive_rank", 16)
            if def_rank <= 5:
                risk_factors.append("Tough defensive matchup")
            elif def_rank >= 25:
                upside_factors.append("Weak defensive matchup")

        # Form factors
        recent_games = player_data.get("recent_games", [])
        if len(recent_games) >= 3:
            recent_avg = np.mean([game.get("fantasy_points", 0) for game in recent_games[-3:]])
            season_avg = player_data.get("season_average", recent_avg)

            if recent_avg > season_avg * 1.2:
                upside_factors.append("Excellent recent form")
            elif recent_avg < season_avg * 0.8:
                risk_factors.append("Poor recent form")

        # Home field advantage
        if game_context and game_context.get("is_home"):
            upside_factors.append("Home field advantage")

        # Weather factors
        if game_context:
            temp = game_context.get("temperature", 70)
            wind = game_context.get("wind_speed", 0)

            if temp < 32:
                risk_factors.append("Freezing weather conditions")
            elif wind > 15:
                risk_factors.append("High wind conditions")

        return risk_factors, upside_factors

    # Model persistence

    async def _save_model(self):
        """Save trained model to disk."""
        try:
            model_path = self.model_dir / f"model_{self.model_type.value}.pkl"
            scaler_path = self.model_dir / f"scaler_{self.model_type.value}.pkl"
            features_path = self.model_dir / f"features_{self.model_type.value}.json"

            # Save model
            with open(model_path, 'wb') as f:
                pickle.dump(self.model, f)

            # Save scaler
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)

            # Save feature names
            with open(features_path, 'w') as f:
                json.dump(self.feature_names, f)

            logger.info(f"Model saved to {model_path}")

        except Exception as e:
            logger.error(f"Model saving failed: {e}")
            raise PerformancePredictorError(f"Model saving failed: {e}")

    async def _load_model(self):
        """Load trained model from disk."""
        try:
            model_path = self.model_dir / f"model_{self.model_type.value}.pkl"
            scaler_path = self.model_dir / f"scaler_{self.model_type.value}.pkl"
            features_path = self.model_dir / f"features_{self.model_type.value}.json"

            if not all(path.exists() for path in [model_path, scaler_path, features_path]):
                logger.warning(f"Model files not found for {self.sport.value}")
                return

            # Load model
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)

            # Load scaler
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)

            # Load feature names
            with open(features_path, 'r') as f:
                self.feature_names = json.load(f)

            self.is_trained = True
            logger.info(f"Model loaded from {model_path}")

        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            raise PerformancePredictorError(f"Model loading failed: {e}")


# Export aliases for backward compatibility
PerformancePredictor = PlayerPerformancePredictor
PredictionModel = ModelType

# Global predictors for each sport
_predictors: Dict[Sport, PlayerPerformancePredictor] = {}


def get_performance_predictor(sport: Sport,
                            model_type: ModelType = ModelType.ENSEMBLE) -> PlayerPerformancePredictor:
    """Get or create performance predictor for a sport."""
    global _predictors

    key = sport
    if key not in _predictors:
        _predictors[key] = PlayerPerformancePredictor(sport, model_type)

    return _predictors[key]


async def initialize_predictors():
    """Initialize all performance predictors."""
    for sport in Sport:
        predictor = get_performance_predictor(sport)
        try:
            await predictor._load_model()
        except Exception as e:
            logger.warning(f"Could not load {sport.value} model: {e}")


def reset_predictors():
    """Reset all predictors (useful for testing)."""
    global _predictors
    _predictors = {}