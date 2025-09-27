"""
Database index management for optimal query performance.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from sqlalchemy import MetaData, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class IndexStrategy(Enum):
    """Index optimization strategies."""

    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    PARTIAL = "partial"
    COMPOSITE = "composite"
    COVERING = "covering"


@dataclass
class IndexRecommendation:
    """Index recommendation with performance impact estimate."""

    table_name: str
    columns: list[str]
    index_type: IndexStrategy
    estimated_benefit: float
    creation_cost: float
    maintenance_cost: float
    reason: str


@dataclass
class IndexUsageStats:
    """Statistics for index usage analysis."""

    index_name: str
    table_name: str
    scans: int
    tuples_read: int
    tuples_fetched: int
    usage_ratio: float
    size_mb: float


class IndexManager:
    """Comprehensive index management and optimization."""

    def __init__(self, engine: Engine):
        self.engine = engine
        self.metadata = MetaData()
        self.query_patterns: dict[str, int] = {}
        self.index_recommendations: list[IndexRecommendation] = []

    def analyze_query_patterns(self, queries: list[str]) -> dict[str, Any]:
        """Analyze query patterns to identify indexing opportunities."""
        patterns = {
            "where_clauses": {},
            "join_conditions": {},
            "order_by_columns": {},
            "group_by_columns": {},
            "table_access_frequency": {},
        }

        for query in queries:
            query_lower = query.lower()

            # Extract WHERE clause patterns
            self._extract_where_patterns(query_lower, patterns["where_clauses"])

            # Extract JOIN patterns
            self._extract_join_patterns(query_lower, patterns["join_conditions"])

            # Extract ORDER BY patterns
            self._extract_order_by_patterns(query_lower, patterns["order_by_columns"])

            # Extract GROUP BY patterns
            self._extract_group_by_patterns(query_lower, patterns["group_by_columns"])

            # Track table access frequency
            self._track_table_access(query_lower, patterns["table_access_frequency"])

        return patterns

    def _extract_where_patterns(self, query: str, patterns: dict[str, int]):
        """Extract WHERE clause column usage patterns."""
        import re

        # Simple regex to find WHERE conditions
        where_match = re.search(
            r"where\s+(.+?)(?:\s+order\s+by|\s+group\s+by|\s+limit|$)", query
        )
        if where_match:
            where_clause = where_match.group(1)
            # Extract column references (simplified)
            columns = re.findall(
                r"(\w+\.\w+|\w+)\s*(?:=|<|>|<=|>=|!=|like|in)", where_clause
            )
            for col in columns:
                patterns[col] = patterns.get(col, 0) + 1

    def _extract_join_patterns(self, query: str, patterns: dict[str, int]):
        """Extract JOIN condition patterns."""
        import re

        join_matches = re.findall(
            r"join\s+\w+\s+on\s+(.+?)(?:\s+where|\s+join|\s+order|\s+group|$)", query
        )
        for join_condition in join_matches:
            # Extract column pairs from join conditions
            columns = re.findall(r"(\w+\.\w+|\w+)", join_condition)
            for col in columns:
                patterns[col] = patterns.get(col, 0) + 1

    def _extract_order_by_patterns(self, query: str, patterns: dict[str, int]):
        """Extract ORDER BY column patterns."""
        import re

        order_match = re.search(r"order\s+by\s+(.+?)(?:\s+limit|$)", query)
        if order_match:
            order_clause = order_match.group(1)
            columns = re.findall(r"(\w+\.\w+|\w+)", order_clause)
            for col in columns:
                patterns[col] = patterns.get(col, 0) + 1

    def _extract_group_by_patterns(self, query: str, patterns: dict[str, int]):
        """Extract GROUP BY column patterns."""
        import re

        group_match = re.search(r"group\s+by\s+(.+?)(?:\s+order|\s+limit|$)", query)
        if group_match:
            group_clause = group_match.group(1)
            columns = re.findall(r"(\w+\.\w+|\w+)", group_clause)
            for col in columns:
                patterns[col] = patterns.get(col, 0) + 1

    def _track_table_access(self, query: str, patterns: dict[str, int]):
        """Track table access frequency."""
        import re

        # Extract table names from FROM and JOIN clauses
        tables = re.findall(r"(?:from|join)\s+(\w+)", query)
        for table in tables:
            patterns[table] = patterns.get(table, 0) + 1

    def generate_index_recommendations(
        self, query_patterns: dict[str, Any]
    ) -> list[IndexRecommendation]:
        """Generate index recommendations based on query patterns."""
        recommendations = []

        # Recommend indexes for frequently used WHERE clause columns
        for column, frequency in query_patterns["where_clauses"].items():
            if frequency >= 5:  # Threshold for recommendation
                table_name = self._extract_table_name(column)
                column_name = self._extract_column_name(column)

                recommendation = IndexRecommendation(
                    table_name=table_name,
                    columns=[column_name],
                    index_type=IndexStrategy.BTREE,
                    estimated_benefit=frequency * 0.1,
                    creation_cost=0.5,
                    maintenance_cost=0.1,
                    reason=f"Frequently used in WHERE clauses ({frequency} times)",
                )
                recommendations.append(recommendation)

        # Recommend composite indexes for JOIN conditions
        join_pairs = self._identify_join_pairs(query_patterns["join_conditions"])
        for pair in join_pairs:
            if pair["frequency"] >= 3:
                recommendation = IndexRecommendation(
                    table_name=pair["table"],
                    columns=pair["columns"],
                    index_type=IndexStrategy.COMPOSITE,
                    estimated_benefit=pair["frequency"] * 0.15,
                    creation_cost=1.0,
                    maintenance_cost=0.2,
                    reason=f"Frequently used in JOIN conditions ({pair['frequency']} times)",
                )
                recommendations.append(recommendation)

        # Recommend indexes for ORDER BY columns
        for column, frequency in query_patterns["order_by_columns"].items():
            if frequency >= 3:
                table_name = self._extract_table_name(column)
                column_name = self._extract_column_name(column)

                recommendation = IndexRecommendation(
                    table_name=table_name,
                    columns=[column_name],
                    index_type=IndexStrategy.BTREE,
                    estimated_benefit=frequency * 0.12,
                    creation_cost=0.5,
                    maintenance_cost=0.1,
                    reason=f"Frequently used in ORDER BY clauses ({frequency} times)",
                )
                recommendations.append(recommendation)

        self.index_recommendations = recommendations
        return recommendations

    def _extract_table_name(self, column_ref: str) -> str:
        """Extract table name from column reference."""
        if "." in column_ref:
            return column_ref.split(".")[0]
        return "unknown_table"  # Would need more context to determine

    def _extract_column_name(self, column_ref: str) -> str:
        """Extract column name from column reference."""
        if "." in column_ref:
            return column_ref.split(".")[1]
        return column_ref

    def _identify_join_pairs(
        self, join_conditions: dict[str, int]
    ) -> list[dict[str, Any]]:
        """Identify column pairs used in JOIN conditions."""
        pairs = []
        # Simplified implementation - would need more sophisticated parsing
        for condition, frequency in join_conditions.items():
            table = self._extract_table_name(condition)
            column = self._extract_column_name(condition)
            pairs.append({"table": table, "columns": [column], "frequency": frequency})
        return pairs

    def get_existing_indexes(self, table_name: str) -> list[dict[str, Any]]:
        """Get information about existing indexes on a table."""
        query = text(
            """
            SELECT
                indexname,
                indexdef,
                pg_size_pretty(pg_relation_size(indexname::regclass)) as size
            FROM pg_indexes
            WHERE tablename = :table_name
        """
        )

        with self.engine.connect() as conn:
            result = conn.execute(query, {"table_name": table_name})
            return [dict(row) for row in result]

    def get_index_usage_stats(
        self, table_name: str | None = None
    ) -> list[IndexUsageStats]:
        """Get index usage statistics."""
        where_clause = "WHERE schemaname = 'public'"
        if table_name:
            where_clause += f" AND tablename = '{table_name}'"

        query = text(
            f"""
            SELECT
                indexrelname as index_name,
                tablename as table_name,
                idx_scan as scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched,
                CASE
                    WHEN idx_scan = 0 THEN 0
                    ELSE round((idx_tup_fetch::numeric / idx_tup_read::numeric) * 100, 2)
                END as usage_ratio,
                round(pg_relation_size(indexrelid) / 1024.0 / 1024.0, 2) as size_mb
            FROM pg_stat_user_indexes
            {where_clause}
            ORDER BY idx_scan DESC
        """
        )

        with self.engine.connect() as conn:
            result = conn.execute(query)
            return [
                IndexUsageStats(
                    index_name=row.index_name,
                    table_name=row.table_name,
                    scans=row.scans,
                    tuples_read=row.tuples_read,
                    tuples_fetched=row.tuples_fetched,
                    usage_ratio=row.usage_ratio,
                    size_mb=row.size_mb,
                )
                for row in result
            ]

    def identify_unused_indexes(self, min_scans: int = 100) -> list[IndexUsageStats]:
        """Identify potentially unused indexes."""
        all_stats = self.get_index_usage_stats()
        return [stat for stat in all_stats if stat.scans < min_scans]

    def create_recommended_indexes(
        self, recommendations: list[IndexRecommendation] | None = None
    ) -> dict[str, bool]:
        """Create indexes based on recommendations."""
        recommendations = recommendations or self.index_recommendations
        results = {}

        for rec in recommendations:
            try:
                index_name = f"idx_{rec.table_name}_{'_'.join(rec.columns)}"

                # Create index SQL based on strategy
                if rec.index_type == IndexStrategy.BTREE:
                    sql = f"CREATE INDEX {index_name} ON {rec.table_name} USING btree ({', '.join(rec.columns)})"
                elif rec.index_type == IndexStrategy.HASH:
                    sql = f"CREATE INDEX {index_name} ON {rec.table_name} USING hash ({', '.join(rec.columns)})"
                elif rec.index_type == IndexStrategy.COMPOSITE:
                    sql = f"CREATE INDEX {index_name} ON {rec.table_name} ({', '.join(rec.columns)})"
                else:
                    sql = f"CREATE INDEX {index_name} ON {rec.table_name} ({', '.join(rec.columns)})"

                with self.engine.connect() as conn:
                    conn.execute(text(sql))
                    conn.commit()

                results[index_name] = True
                logger.info(f"Created index: {index_name}")

            except Exception as e:
                logger.error(
                    f"Failed to create index for {rec.table_name}.{rec.columns}: {e}"
                )
                results[f"{rec.table_name}_{'_'.join(rec.columns)}"] = False

        return results

    def drop_unused_indexes(
        self, unused_indexes: list[IndexUsageStats]
    ) -> dict[str, bool]:
        """Drop unused indexes to improve write performance."""
        results = {}

        for index_stat in unused_indexes:
            try:
                sql = f"DROP INDEX IF EXISTS {index_stat.index_name}"

                with self.engine.connect() as conn:
                    conn.execute(text(sql))
                    conn.commit()

                results[index_stat.index_name] = True
                logger.info(f"Dropped unused index: {index_stat.index_name}")

            except Exception as e:
                logger.error(f"Failed to drop index {index_stat.index_name}: {e}")
                results[index_stat.index_name] = False

        return results

    def generate_optimization_report(self) -> dict[str, Any]:
        """Generate comprehensive index optimization report."""
        all_stats = self.get_index_usage_stats()
        unused = self.identify_unused_indexes()

        total_indexes = len(all_stats)
        unused_count = len(unused)
        total_size_mb = sum(stat.size_mb for stat in all_stats)
        unused_size_mb = sum(stat.size_mb for stat in unused)

        return {
            "total_indexes": total_indexes,
            "unused_indexes": unused_count,
            "unused_percentage": (
                (unused_count / total_indexes * 100) if total_indexes > 0 else 0
            ),
            "total_size_mb": total_size_mb,
            "unused_size_mb": unused_size_mb,
            "potential_savings_mb": unused_size_mb,
            "recommendations_count": len(self.index_recommendations),
            "top_used_indexes": sorted(all_stats, key=lambda x: x.scans, reverse=True)[
                :10
            ],
            "unused_indexes": unused,
        }
