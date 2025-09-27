"""
Advanced lineup optimization algorithm for fantasy sports.

Provides comprehensive lineup optimization including:
- Multi-objective optimization (points, risk, ceiling)
- Positional constraints and roster requirements
- Budget constraints for salary cap formats
- Player correlation and stacking strategies
- Injury risk assessment and mitigation
- Advanced mathematical optimization techniques
- Real-time lineup adjustments
- Tournament and cash game strategies
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging

    get_logger = logging.getLogger  # type: ignore[assignment]

from domains.ai.models.performance_predictor import Sport, get_performance_predictor

logger = get_logger(__name__)


class OptimizationObjective(Enum):
    """Optimization objectives."""

    MAX_POINTS = "max_points"
    MAX_CEILING = "max_ceiling"
    MIN_RISK = "min_risk"
    BALANCED = "balanced"
    CONTRARIAN = "contrarian"


class LineupStrategy(Enum):
    """Lineup construction strategies."""

    CASH_GAME = "cash_game"  # Conservative, high floor
    TOURNAMENT = "tournament"  # High upside, higher risk
    BALANCED = "balanced"  # Mix of safety and upside
    CONTRARIAN = "contrarian"  # Low ownership plays


@dataclass
class PlayerProjection:
    """Enhanced player projection for optimization."""

    player_id: str
    name: str
    position: str
    team: str
    salary: int
    projected_points: float
    floor: float
    ceiling: float
    ownership_projection: float
    injury_risk: float
    value: float  # points per dollar

    # Advanced metrics
    consistency: float
    recent_form: float
    matchup_grade: str
    weather_impact: float

    # Correlation data
    team_correlation: float
    position_correlation: float


@dataclass
class LineupConstraints:
    """Lineup construction constraints."""

    max_salary: int
    positions: dict[str, int]  # position -> required count
    max_per_team: int
    min_teams: int
    max_ownership: float | None = None
    banned_players: set[str] = None
    locked_players: set[str] = None


@dataclass
class OptimizedLineup:
    """Optimized lineup result."""

    players: list[PlayerProjection]
    total_salary: int
    projected_points: float
    projected_floor: float
    projected_ceiling: float
    risk_score: float
    value_score: float

    # Advanced metrics
    team_distribution: dict[str, int]
    position_distribution: dict[str, int]
    ownership_total: float
    correlation_score: float

    # Strategy metrics
    strategy_fit: float
    contrarian_score: float

    optimization_objective: OptimizationObjective
    generated_at: datetime


class LineupOptimizerError(Exception):
    """Lineup optimizer errors."""


class LineupOptimizer:
    """Advanced lineup optimization engine."""

    def __init__(self, sport: Sport):
        self.sport = sport
        self.performance_predictor = get_performance_predictor(sport)

        # Sport-specific configurations
        self.position_configs = self._get_position_configs(sport)
        self.correlation_matrix = self._initialize_correlation_matrix()

        # Optimization parameters
        self.population_size = 1000
        self.generations = 100
        self.mutation_rate = 0.1

        logger.info(f"Initialized lineup optimizer for {sport.value}")

    def _get_position_configs(self, sport: Sport) -> dict[str, Any]:
        """Get sport-specific position configurations."""
        configs = {
            Sport.NFL: {
                "positions": {
                    "QB": 1,
                    "RB": 2,
                    "WR": 3,
                    "TE": 1,
                    "FLEX": 1,
                    "K": 1,
                    "DEF": 1,
                },
                "flex_positions": ["RB", "WR", "TE"],
                "max_per_team": 4,
                "min_teams": 3,
                "salary_cap": 60000,
            },
            Sport.MLB: {
                "positions": {
                    "C": 1,
                    "1B": 1,
                    "2B": 1,
                    "3B": 1,
                    "SS": 1,
                    "OF": 3,
                    "UTIL": 1,
                    "P": 2,
                },
                "flex_positions": ["C", "1B", "2B", "3B", "SS", "OF"],
                "max_per_team": 5,
                "min_teams": 2,
                "salary_cap": 50000,
            },
            Sport.WNBA: {
                "positions": {
                    "PG": 1,
                    "SG": 1,
                    "SF": 1,
                    "PF": 1,
                    "C": 1,
                    "G": 1,
                    "F": 1,
                    "UTIL": 1,
                },
                "flex_positions": ["PG", "SG", "SF", "PF", "C"],
                "max_per_team": 4,
                "min_teams": 3,
                "salary_cap": 40000,
            },
        }
        return configs.get(sport, configs[Sport.NFL])

    def _initialize_correlation_matrix(self) -> dict[tuple[str, str], float]:
        """Initialize player correlation matrix."""
        # This would be populated with historical correlation data
        return defaultdict(float)

    async def optimize_lineup(
        self,
        available_players: list[dict[str, Any]],
        constraints: LineupConstraints | None = None,
        objective: OptimizationObjective = OptimizationObjective.MAX_POINTS,
        strategy: LineupStrategy = LineupStrategy.BALANCED,
        num_lineups: int = 1,
    ) -> list[OptimizedLineup]:
        """
        Optimize fantasy lineup using advanced algorithms.

        Args:
            available_players: Pool of available players
            constraints: Lineup construction constraints
            objective: Optimization objective
            strategy: Lineup strategy
            num_lineups: Number of lineups to generate

        Returns:
            List[OptimizedLineup]: Optimized lineups
        """
        try:
            logger.info(
                "Optimizing lineup",
                extra={
                    "sport": self.sport.value,
                    "players": len(available_players),
                    "objective": objective.value,
                    "strategy": strategy.value,
                    "num_lineups": num_lineups,
                },
            )

            # Generate player projections
            projections = await self._generate_projections(available_players)

            # Set default constraints if not provided
            if constraints is None:
                constraints = self._get_default_constraints()

            # Select optimization algorithm based on problem size
            if len(projections) < 50:
                lineups = await self._brute_force_optimization(
                    projections, constraints, objective, strategy, num_lineups
                )
            elif len(projections) < 200:
                lineups = await self._genetic_algorithm_optimization(
                    projections, constraints, objective, strategy, num_lineups
                )
            else:
                lineups = await self._heuristic_optimization(
                    projections, constraints, objective, strategy, num_lineups
                )

            # Post-process and validate lineups
            validated_lineups = []
            for lineup in lineups:
                if self._validate_lineup(lineup, constraints):
                    enhanced_lineup = await self._enhance_lineup_analysis(
                        lineup, strategy
                    )
                    validated_lineups.append(enhanced_lineup)

            logger.info(f"Generated {len(validated_lineups)} valid lineups")
            return validated_lineups

        except Exception as e:
            logger.error(f"Lineup optimization failed: {e}")
            raise LineupOptimizerError(f"Optimization failed: {e}")

    async def _generate_projections(
        self, available_players: list[dict[str, Any]]
    ) -> list[PlayerProjection]:
        """Generate enhanced projections for all available players."""
        try:
            projections = []

            for player_data in available_players:
                # Get AI prediction
                try:
                    prediction = await self.performance_predictor.predict_performance(
                        player_data
                    )
                    projected_points = prediction.predicted_points
                    confidence = prediction.confidence_score
                except Exception as e:
                    logger.warning(
                        f"Prediction failed for player {player_data.get('player_id')}: {e}"
                    )
                    projected_points = player_data.get("projected_points", 0)
                    confidence = 0.5

                # Calculate floor and ceiling
                floor, ceiling = self._calculate_floor_ceiling(
                    projected_points, confidence, player_data
                )

                # Calculate additional metrics
                salary = player_data.get("salary", 1)
                value = projected_points / max(salary / 1000, 1)  # Points per $1K

                consistency = self._calculate_consistency(player_data)
                recent_form = self._calculate_recent_form(player_data)
                injury_risk = self._calculate_injury_risk(player_data)
                ownership_projection = self._estimate_ownership(
                    player_data, projected_points, salary
                )

                projection = PlayerProjection(
                    player_id=player_data.get("player_id", ""),
                    name=player_data.get("name", ""),
                    position=player_data.get("position", ""),
                    team=player_data.get("team", ""),
                    salary=salary,
                    projected_points=projected_points,
                    floor=floor,
                    ceiling=ceiling,
                    ownership_projection=ownership_projection,
                    injury_risk=injury_risk,
                    value=value,
                    consistency=consistency,
                    recent_form=recent_form,
                    matchup_grade=self._grade_matchup(player_data),
                    weather_impact=self._calculate_weather_impact(player_data),
                    team_correlation=self._get_team_correlation(player_data),
                    position_correlation=self._get_position_correlation(player_data),
                )

                projections.append(projection)

            return projections

        except Exception as e:
            logger.error(f"Projection generation failed: {e}")
            raise LineupOptimizerError(f"Projection generation failed: {e}")

    def _calculate_floor_ceiling(
        self, projected_points: float, confidence: float, player_data: dict[str, Any]
    ) -> tuple[float, float]:
        """Calculate player's floor and ceiling projections."""
        try:
            # Base variance calculation
            variance_factor = 1.0 - confidence
            projected_points * variance_factor * 0.4

            # Adjust for player type
            position = player_data.get("position", "")
            if position in ["QB", "P"]:  # More consistent positions
                floor_factor = 0.7
                ceiling_factor = 1.4
            elif position in ["RB", "WR"]:  # More volatile positions
                floor_factor = 0.5
                ceiling_factor = 1.8
            else:
                floor_factor = 0.6
                ceiling_factor = 1.5

            # Calculate floor and ceiling
            floor = max(0, projected_points * floor_factor)
            ceiling = projected_points * ceiling_factor

            # Adjust based on recent variance
            recent_games = player_data.get("recent_games", [])
            if len(recent_games) >= 3:
                recent_points = [game.get("fantasy_points", 0) for game in recent_games]
                recent_std = np.std(recent_points)

                # Incorporate actual variance
                floor = max(0, projected_points - recent_std)
                ceiling = projected_points + recent_std * 1.5

            return round(floor, 1), round(ceiling, 1)

        except Exception as e:
            logger.error(f"Floor/ceiling calculation failed: {e}")
            return projected_points * 0.6, projected_points * 1.4

    def _calculate_consistency(self, player_data: dict[str, Any]) -> float:
        """Calculate player consistency score."""
        try:
            recent_games = player_data.get("recent_games", [])
            if len(recent_games) < 3:
                return 0.5

            fantasy_points = [game.get("fantasy_points", 0) for game in recent_games]
            if not fantasy_points or max(fantasy_points) == 0:
                return 0.5

            # Coefficient of variation (lower is more consistent)
            cv = np.std(fantasy_points) / max(np.mean(fantasy_points), 1)
            consistency = max(0.0, min(1.0, 1.0 - cv))

            return round(consistency, 3)

        except Exception as e:
            logger.error(f"Consistency calculation failed: {e}")
            return 0.5

    def _calculate_recent_form(self, player_data: dict[str, Any]) -> float:
        """Calculate recent form trend."""
        try:
            recent_games = player_data.get("recent_games", [])
            if len(recent_games) < 3:
                return 0.5

            # Compare recent 3 games to previous 3 games
            recent_3 = [game.get("fantasy_points", 0) for game in recent_games[-3:]]
            previous_3 = (
                [game.get("fantasy_points", 0) for game in recent_games[-6:-3]]
                if len(recent_games) >= 6
                else recent_3
            )

            recent_avg = np.mean(recent_3)
            previous_avg = np.mean(previous_3)

            if previous_avg == 0:
                return 0.5

            # Calculate improvement ratio
            improvement = (recent_avg - previous_avg) / previous_avg
            form_score = 0.5 + (improvement * 0.5)  # Scale to 0-1

            return max(0.0, min(1.0, form_score))

        except Exception as e:
            logger.error(f"Recent form calculation failed: {e}")
            return 0.5

    def _calculate_injury_risk(self, player_data: dict[str, Any]) -> float:
        """Calculate injury risk score."""
        injury_status = player_data.get("injury_status", "healthy").lower()

        injury_risks = {
            "healthy": 0.0,
            "questionable": 0.3,
            "doubtful": 0.7,
            "out": 1.0,
            "ir": 1.0,
        }

        return injury_risks.get(injury_status, 0.1)

    def _estimate_ownership(
        self, player_data: dict[str, Any], projected_points: float, salary: int
    ) -> float:
        """Estimate player ownership percentage."""
        try:
            # Simplified ownership model based on value and name recognition
            value = projected_points / max(salary / 1000, 1)

            # Base ownership on value
            if value > 3.0:
                base_ownership = 0.4
            elif value > 2.5:
                base_ownership = 0.3
            elif value > 2.0:
                base_ownership = 0.2
            else:
                base_ownership = 0.1

            # Adjust for salary tier
            if salary > 9000:
                base_ownership += 0.1  # Studs get higher ownership
            elif salary < 5000:
                base_ownership -= 0.05  # Value plays get lower ownership

            # Add some randomness
            ownership = base_ownership + np.random.normal(0, 0.05)
            return max(0.01, min(0.8, ownership))

        except Exception as e:
            logger.error(f"Ownership estimation failed: {e}")
            return 0.15

    def _grade_matchup(self, player_data: dict[str, Any]) -> str:
        """Grade the player's matchup."""
        opponent_rank = player_data.get("opponent_defensive_rank", 16)

        if opponent_rank <= 5:
            return "D"
        elif opponent_rank <= 10:
            return "C"
        elif opponent_rank <= 20:
            return "B"
        else:
            return "A"

    def _calculate_weather_impact(self, player_data: dict[str, Any]) -> float:
        """Calculate weather impact on performance."""
        game_context = player_data.get("game_context", {})

        if not game_context or self.sport == Sport.WNBA:  # Indoor sport
            return 0.0

        impact = 0.0
        temperature = game_context.get("temperature", 70)
        wind_speed = game_context.get("wind_speed", 0)
        precipitation = game_context.get("precipitation", 0)

        # Temperature impact
        if temperature < 32:
            impact -= 0.1
        elif temperature > 90:
            impact -= 0.05

        # Wind impact (especially for passing games)
        if wind_speed > 15:
            impact -= 0.1

        # Precipitation impact
        if precipitation > 0:
            impact -= 0.05

        return impact

    def _get_team_correlation(self, player_data: dict[str, Any]) -> float:
        """Get team correlation factor."""
        # This would be based on historical team correlation data
        return 0.1  # Simplified

    def _get_position_correlation(self, player_data: dict[str, Any]) -> float:
        """Get position correlation factor."""
        # This would be based on positional correlation analysis
        return 0.05  # Simplified

    def _get_default_constraints(self) -> LineupConstraints:
        """Get default constraints for the sport."""
        config = self.position_configs

        return LineupConstraints(
            max_salary=config["salary_cap"],
            positions=config["positions"],
            max_per_team=config["max_per_team"],
            min_teams=config["min_teams"],
            banned_players=set(),
            locked_players=set(),
        )

    # Optimization algorithms

    async def _genetic_algorithm_optimization(
        self,
        projections: list[PlayerProjection],
        constraints: LineupConstraints,
        objective: OptimizationObjective,
        strategy: LineupStrategy,
        num_lineups: int,
    ) -> list[OptimizedLineup]:
        """Genetic algorithm optimization for large player pools."""
        try:
            logger.info("Using genetic algorithm optimization")

            # Initialize population
            population = self._initialize_population(projections, constraints)

            best_lineups = []

            for _generation in range(self.generations):
                # Evaluate fitness
                fitness_scores = []
                for individual in population:
                    fitness = self._calculate_fitness(individual, objective, strategy)
                    fitness_scores.append(fitness)

                # Select best individuals
                sorted_indices = np.argsort(fitness_scores)[::-1]
                elite_size = int(0.1 * len(population))
                elite = [population[i] for i in sorted_indices[:elite_size]]

                # Store best lineups
                for i in range(min(num_lineups, elite_size)):
                    if elite[i] not in best_lineups:
                        lineup = self._create_optimized_lineup(
                            elite[i], objective, strategy
                        )
                        best_lineups.append(lineup)

                # Generate new population
                new_population = elite.copy()

                while len(new_population) < self.population_size:
                    # Selection
                    parent1 = self._tournament_selection(population, fitness_scores)
                    parent2 = self._tournament_selection(population, fitness_scores)

                    # Crossover
                    child = self._crossover(parent1, parent2, projections, constraints)

                    # Mutation
                    if np.random.random() < self.mutation_rate:
                        child = self._mutate(child, projections, constraints)

                    new_population.append(child)

                population = new_population

            return best_lineups[:num_lineups]

        except Exception as e:
            logger.error(f"Genetic algorithm optimization failed: {e}")
            raise LineupOptimizerError(f"Genetic algorithm failed: {e}")

    async def _heuristic_optimization(
        self,
        projections: list[PlayerProjection],
        constraints: LineupConstraints,
        objective: OptimizationObjective,
        strategy: LineupStrategy,
        num_lineups: int,
    ) -> list[OptimizedLineup]:
        """Heuristic optimization for very large player pools."""
        try:
            logger.info("Using heuristic optimization")

            lineups = []

            # Sort players by different criteria for diversity
            sort_criteria = [
                ("projected_points", True),
                ("value", True),
                ("ceiling", True),
                ("floor", True),
            ]

            for criterion, descending in sort_criteria:
                if len(lineups) >= num_lineups:
                    break

                # Sort players by criterion
                sorted_players = sorted(
                    projections, key=lambda p: getattr(p, criterion), reverse=descending
                )

                # Greedy selection with constraints
                lineup = self._greedy_lineup_construction(
                    sorted_players, constraints, objective, strategy
                )

                if lineup and self._validate_lineup(lineup, constraints):
                    optimized_lineup = self._create_optimized_lineup(
                        lineup, objective, strategy
                    )
                    lineups.append(optimized_lineup)

            # Fill remaining slots with random sampling
            while len(lineups) < num_lineups:
                random_lineup = self._random_lineup_construction(
                    projections, constraints
                )

                if random_lineup and self._validate_lineup(random_lineup, constraints):
                    optimized_lineup = self._create_optimized_lineup(
                        random_lineup, objective, strategy
                    )
                    lineups.append(optimized_lineup)

            return lineups

        except Exception as e:
            logger.error(f"Heuristic optimization failed: {e}")
            raise LineupOptimizerError(f"Heuristic optimization failed: {e}")

    async def _brute_force_optimization(
        self,
        projections: list[PlayerProjection],
        constraints: LineupConstraints,
        objective: OptimizationObjective,
        strategy: LineupStrategy,
        num_lineups: int,
    ) -> list[OptimizedLineup]:
        """Brute force optimization for small player pools."""
        try:
            logger.info("Using brute force optimization")

            # This is a simplified version - full brute force would be computationally expensive
            # We'll use a smart enumeration approach

            best_lineups = []
            attempts = 0
            max_attempts = 10000

            while len(best_lineups) < num_lineups and attempts < max_attempts:
                lineup = self._smart_random_lineup(projections, constraints)

                if lineup and self._validate_lineup(lineup, constraints):
                    optimized_lineup = self._create_optimized_lineup(
                        lineup, objective, strategy
                    )

                    # Check if this lineup is significantly different
                    if not self._is_similar_lineup(optimized_lineup, best_lineups):
                        best_lineups.append(optimized_lineup)

                attempts += 1

            # Sort by fitness
            best_lineups.sort(
                key=lambda l: self._calculate_lineup_fitness(l, objective, strategy),
                reverse=True,
            )

            return best_lineups

        except Exception as e:
            logger.error(f"Brute force optimization failed: {e}")
            raise LineupOptimizerError(f"Brute force optimization failed: {e}")

    # Helper methods for optimization

    def _initialize_population(
        self, projections: list[PlayerProjection], constraints: LineupConstraints
    ) -> list[list[PlayerProjection]]:
        """Initialize genetic algorithm population."""
        population = []

        for _ in range(self.population_size):
            lineup = self._random_lineup_construction(projections, constraints)
            if lineup:
                population.append(lineup)

        return population

    def _calculate_fitness(
        self,
        lineup: list[PlayerProjection],
        objective: OptimizationObjective,
        strategy: LineupStrategy,
    ) -> float:
        """Calculate fitness score for a lineup."""
        if not lineup:
            return 0.0

        total_points = sum(p.projected_points for p in lineup)
        total_ceiling = sum(p.ceiling for p in lineup)
        total_floor = sum(p.floor for p in lineup)
        risk_score = sum(p.injury_risk for p in lineup) / len(lineup)

        if objective == OptimizationObjective.MAX_POINTS:
            return total_points
        elif objective == OptimizationObjective.MAX_CEILING:
            return total_ceiling
        elif objective == OptimizationObjective.MIN_RISK:
            return total_floor - risk_score * 10
        else:  # BALANCED
            return (
                total_points * 0.6
                + total_ceiling * 0.2
                + total_floor * 0.2
                - risk_score * 5
            )

    def _tournament_selection(
        self, population: list[list[PlayerProjection]], fitness_scores: list[float]
    ) -> list[PlayerProjection]:
        """Tournament selection for genetic algorithm."""
        tournament_size = 5
        tournament_indices = np.random.choice(
            len(population), tournament_size, replace=False
        )
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_index = tournament_indices[np.argmax(tournament_fitness)]
        return population[winner_index]

    def _crossover(
        self,
        parent1: list[PlayerProjection],
        parent2: list[PlayerProjection],
        projections: list[PlayerProjection],
        constraints: LineupConstraints,
    ) -> list[PlayerProjection]:
        """Crossover operation for genetic algorithm."""
        # Simple uniform crossover
        child = []
        used_players = set()

        # Try to take players from both parents
        all_parent_players = parent1 + parent2
        np.random.shuffle(all_parent_players)

        for player in all_parent_players:
            if player.player_id not in used_players:
                temp_lineup = [*child, player]
                if self._can_add_player(temp_lineup, player, constraints):
                    child.append(player)
                    used_players.add(player.player_id)

        # Fill remaining positions if needed
        if len(child) < sum(constraints.positions.values()):
            child = self._complete_lineup(child, projections, constraints)

        return child

    def _mutate(
        self,
        lineup: list[PlayerProjection],
        projections: list[PlayerProjection],
        constraints: LineupConstraints,
    ) -> list[PlayerProjection]:
        """Mutation operation for genetic algorithm."""
        if not lineup:
            return lineup

        # Random player substitution
        mutation_lineup = lineup.copy()

        # Remove random player
        remove_index = np.random.randint(len(mutation_lineup))
        removed_player = mutation_lineup.pop(remove_index)

        # Add replacement player
        available_players = [
            p
            for p in projections
            if p.player_id not in [pl.player_id for pl in mutation_lineup]
        ]
        suitable_players = [
            p for p in available_players if p.position == removed_player.position
        ]

        if suitable_players:
            replacement = np.random.choice(suitable_players)
            mutation_lineup.append(replacement)

        return mutation_lineup

    def _greedy_lineup_construction(
        self,
        sorted_players: list[PlayerProjection],
        constraints: LineupConstraints,
        objective: OptimizationObjective,
        strategy: LineupStrategy,
    ) -> list[PlayerProjection]:
        """Greedy lineup construction algorithm."""
        lineup = []
        used_players = set()
        position_counts = dict.fromkeys(constraints.positions.keys(), 0)
        total_salary = 0

        for player in sorted_players:
            if player.player_id in used_players:
                continue

            # Check constraints
            if self._can_add_player([*lineup, player], player, constraints):
                lineup.append(player)
                used_players.add(player.player_id)
                position_counts[player.position] += 1
                total_salary += player.salary

                # Check if lineup is complete
                if len(lineup) == sum(constraints.positions.values()):
                    break

        return lineup if len(lineup) == sum(constraints.positions.values()) else None

    def _random_lineup_construction(
        self, projections: list[PlayerProjection], constraints: LineupConstraints
    ) -> list[PlayerProjection]:
        """Random lineup construction with constraints."""
        lineup = []
        available_players = projections.copy()
        np.random.shuffle(available_players)

        for position, count in constraints.positions.items():
            position_players = [
                p
                for p in available_players
                if p.position == position
                and p.player_id not in [pl.player_id for pl in lineup]
            ]

            for _ in range(count):
                if not position_players:
                    break

                player = np.random.choice(position_players)
                if self._can_add_player([*lineup, player], player, constraints):
                    lineup.append(player)
                    position_players.remove(player)

        return lineup if len(lineup) == sum(constraints.positions.values()) else None

    def _smart_random_lineup(
        self, projections: list[PlayerProjection], constraints: LineupConstraints
    ) -> list[PlayerProjection]:
        """Smart random lineup construction with bias toward good players."""
        lineup = []

        # Weight players by projected points for selection
        weights = np.array([p.projected_points for p in projections])
        weights = weights / weights.sum()

        available_players = projections.copy()

        for position, count in constraints.positions.items():
            position_players = [
                p
                for p in available_players
                if p.position == position
                and p.player_id not in [pl.player_id for pl in lineup]
            ]
            position_weights = [weights[projections.index(p)] for p in position_players]

            if not position_players:
                continue

            for _ in range(count):
                if not position_players:
                    break

                # Weighted random selection
                if position_weights:
                    position_weights = np.array(position_weights)
                    position_weights = position_weights / position_weights.sum()

                    player_index = np.random.choice(
                        len(position_players), p=position_weights
                    )
                    player = position_players[player_index]

                    if self._can_add_player([*lineup, player], player, constraints):
                        lineup.append(player)
                        position_players.remove(player)
                        position_weights = np.delete(position_weights, player_index)

        return lineup if len(lineup) == sum(constraints.positions.values()) else None

    def _can_add_player(
        self,
        lineup: list[PlayerProjection],
        player: PlayerProjection,
        constraints: LineupConstraints,
    ) -> bool:
        """Check if player can be added to lineup."""
        # Salary check
        total_salary = sum(p.salary for p in lineup)
        if total_salary > constraints.max_salary:
            return False

        # Team constraints
        team_counts = defaultdict(int)
        for p in lineup:
            team_counts[p.team] += 1

        if team_counts[player.team] >= constraints.max_per_team:
            return False

        # Banned players
        return not (constraints.banned_players and player.player_id in constraints.banned_players)

    def _complete_lineup(
        self,
        partial_lineup: list[PlayerProjection],
        projections: list[PlayerProjection],
        constraints: LineupConstraints,
    ) -> list[PlayerProjection]:
        """Complete a partial lineup."""
        lineup = partial_lineup.copy()
        used_players = {p.player_id for p in lineup}

        position_counts = defaultdict(int)
        for p in lineup:
            position_counts[p.position] += 1

        # Fill missing positions
        for position, required_count in constraints.positions.items():
            current_count = position_counts[position]
            needed = required_count - current_count

            if needed > 0:
                available = [
                    p
                    for p in projections
                    if p.position == position and p.player_id not in used_players
                ]

                # Sort by value and take best available
                available.sort(key=lambda p: p.projected_points, reverse=True)

                for i in range(min(needed, len(available))):
                    player = available[i]
                    if self._can_add_player([*lineup, player], player, constraints):
                        lineup.append(player)
                        used_players.add(player.player_id)

        return lineup

    def _validate_lineup(
        self, lineup: OptimizedLineup, constraints: LineupConstraints
    ) -> bool:
        """Validate lineup against constraints."""
        players = lineup.players if isinstance(lineup, OptimizedLineup) else lineup

        if not players:
            return False

        # Check position requirements
        position_counts = defaultdict(int)
        for player in players:
            position_counts[player.position] += 1

        for position, required in constraints.positions.items():
            if position_counts[position] != required:
                return False

        # Check salary cap
        total_salary = sum(p.salary for p in players)
        if total_salary > constraints.max_salary:
            return False

        # Check team constraints
        team_counts = defaultdict(int)
        for player in players:
            team_counts[player.team] += 1

        if max(team_counts.values()) > constraints.max_per_team:
            return False

        if len(team_counts) < constraints.min_teams:
            return False

        # Check banned players
        if constraints.banned_players:
            for player in players:
                if player.player_id in constraints.banned_players:
                    return False

        return True

    def _create_optimized_lineup(
        self,
        players: list[PlayerProjection],
        objective: OptimizationObjective,
        strategy: LineupStrategy,
    ) -> OptimizedLineup:
        """Create OptimizedLineup object with analysis."""
        total_salary = sum(p.salary for p in players)
        projected_points = sum(p.projected_points for p in players)
        projected_floor = sum(p.floor for p in players)
        projected_ceiling = sum(p.ceiling for p in players)

        # Calculate metrics
        risk_score = sum(p.injury_risk for p in players) / len(players)
        value_score = projected_points / max(total_salary / 1000, 1)

        # Team and position distribution
        team_dist = defaultdict(int)
        pos_dist = defaultdict(int)
        for player in players:
            team_dist[player.team] += 1
            pos_dist[player.position] += 1

        ownership_total = sum(p.ownership_projection for p in players)
        correlation_score = self._calculate_correlation_score(players)

        # Strategy fit
        strategy_fit = self._calculate_strategy_fit(players, strategy)
        contrarian_score = 1.0 - (ownership_total / len(players))

        return OptimizedLineup(
            players=players,
            total_salary=total_salary,
            projected_points=round(projected_points, 2),
            projected_floor=round(projected_floor, 2),
            projected_ceiling=round(projected_ceiling, 2),
            risk_score=round(risk_score, 3),
            value_score=round(value_score, 3),
            team_distribution=dict(team_dist),
            position_distribution=dict(pos_dist),
            ownership_total=round(ownership_total, 3),
            correlation_score=round(correlation_score, 3),
            strategy_fit=round(strategy_fit, 3),
            contrarian_score=round(contrarian_score, 3),
            optimization_objective=objective,
            generated_at=datetime.utcnow(),
        )

    def _calculate_correlation_score(self, players: list[PlayerProjection]) -> float:
        """Calculate lineup correlation score."""
        # Simplified correlation calculation
        team_correlation = 0.0
        teams = defaultdict(int)

        for player in players:
            teams[player.team] += 1

        # Penalty for too many players from same team
        for _team, count in teams.items():
            if count > 1:
                team_correlation += (count - 1) * 0.1

        return min(1.0, team_correlation)

    def _calculate_strategy_fit(
        self, players: list[PlayerProjection], strategy: LineupStrategy
    ) -> float:
        """Calculate how well lineup fits the strategy."""
        if strategy == LineupStrategy.CASH_GAME:
            # Favor consistency and floor
            consistency_avg = sum(p.consistency for p in players) / len(players)
            floor_ratio = sum(p.floor for p in players) / sum(
                p.projected_points for p in players
            )
            return (consistency_avg + floor_ratio) / 2

        elif strategy == LineupStrategy.TOURNAMENT:
            # Favor ceiling and upside
            ceiling_ratio = sum(p.ceiling for p in players) / sum(
                p.projected_points for p in players
            )
            return min(1.0, ceiling_ratio / 1.5)

        elif strategy == LineupStrategy.CONTRARIAN:
            # Favor low ownership
            ownership_avg = sum(p.ownership_projection for p in players) / len(players)
            return 1.0 - ownership_avg

        else:  # BALANCED
            return 0.7  # Neutral score

    def _calculate_lineup_fitness(
        self,
        lineup: OptimizedLineup,
        objective: OptimizationObjective,
        strategy: LineupStrategy,
    ) -> float:
        """Calculate overall lineup fitness."""
        base_score = lineup.projected_points

        if objective == OptimizationObjective.MAX_CEILING:
            base_score = lineup.projected_ceiling
        elif objective == OptimizationObjective.MIN_RISK:
            base_score = lineup.projected_floor - lineup.risk_score * 10

        # Apply strategy modifiers
        strategy_bonus = lineup.strategy_fit * 5

        return base_score + strategy_bonus

    def _is_similar_lineup(
        self, lineup: OptimizedLineup, existing_lineups: list[OptimizedLineup]
    ) -> bool:
        """Check if lineup is too similar to existing lineups."""
        for existing in existing_lineups:
            overlap = len(
                {p.player_id for p in lineup.players}
                & {p.player_id for p in existing.players}
            )

            # If more than 6 players overlap, consider it too similar
            if overlap > 6:
                return True

        return False

    async def _enhance_lineup_analysis(
        self, lineup: OptimizedLineup, strategy: LineupStrategy
    ) -> OptimizedLineup:
        """Enhance lineup with additional analysis."""
        # This could include more advanced analysis
        # For now, just return the lineup as-is
        return lineup


# Global optimizer instances
_optimizers: dict[Sport, LineupOptimizer] = {}


def get_lineup_optimizer(sport: Sport) -> LineupOptimizer:
    """Get or create lineup optimizer for a sport."""
    global _optimizers

    if sport not in _optimizers:
        _optimizers[sport] = LineupOptimizer(sport)

    return _optimizers[sport]


def reset_optimizers():
    """Reset all optimizers (useful for testing)."""
    global _optimizers
    _optimizers = {}
