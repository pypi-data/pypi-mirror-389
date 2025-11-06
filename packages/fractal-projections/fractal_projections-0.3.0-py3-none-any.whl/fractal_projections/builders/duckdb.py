"""
DuckDB Projection Builder

Converts generic projections to DuckDB-specific SQL syntax.
DuckDB is similar to PostgreSQL but uses ? placeholders for parameterized queries.
"""

from typing import Any, List, Tuple

from fractal_specifications.contrib.duckdb.specifications import (
    DuckDBSpecificationBuilder,
)

from fractal_projections.builders.base import ProjectionBuilder
from fractal_projections.projections.fields import (
    AggregateFunction,
    AggregateProjection,
    FieldProjection,
    ProjectionList,
)
from fractal_projections.projections.grouping import GroupingProjection
from fractal_projections.projections.limiting import LimitProjection
from fractal_projections.projections.ordering import OrderingList
from fractal_projections.projections.query import QueryProjection


class DuckDBProjectionBuilder(ProjectionBuilder):
    """Builds DuckDB-specific SQL from projection objects and complete queries"""

    def __init__(self, table_name: str = None):
        """
        Initialize builder, optionally with a table name for complete queries

        Args:
            table_name: Name of the table to query (required for build(), build_count(), explain())
        """
        super().__init__(table_name)
        self.table_name = table_name  # Alias for backwards compatibility

    @staticmethod
    def build_select(projection: ProjectionList) -> str:
        """Convert ProjectionList to DuckDB SELECT clause"""
        if not projection.fields:
            return "*"

        field_exprs = []
        for field_spec in projection.fields:
            if isinstance(field_spec, FieldProjection):
                expr = DuckDBProjectionBuilder._build_field_projection(field_spec)
            elif isinstance(field_spec, AggregateProjection):
                expr = DuckDBProjectionBuilder._build_aggregate_projection(field_spec)
            else:
                raise ValueError(f"Unknown projection type: {type(field_spec)}")

            field_exprs.append(expr)

        select_clause = ", ".join(field_exprs)

        if projection.distinct:
            select_clause = f"DISTINCT {select_clause}"

        return select_clause

    @staticmethod
    def _build_field_projection(field: FieldProjection) -> str:
        """Convert FieldProjection to DuckDB field expression"""
        expr = field.field
        if field.alias:
            expr += f" AS {field.alias}"
        return expr

    @staticmethod
    def _build_aggregate_projection(agg: AggregateProjection) -> str:
        """Convert AggregateProjection to DuckDB aggregate expression"""
        if agg.function == AggregateFunction.COUNT and agg.field is None:
            expr = "COUNT(*)"
        elif agg.function == AggregateFunction.COUNT_DISTINCT:
            expr = f"COUNT(DISTINCT {agg.field})"
        else:
            expr = f"{agg.function.value}({agg.field})"

        if agg.alias:
            expr += f" AS {agg.alias}"
        return expr

    @staticmethod
    def build_group_by(grouping: GroupingProjection) -> str:
        """Convert GroupingProjection to DuckDB GROUP BY clause"""
        return ", ".join(grouping.fields)

    @staticmethod
    def build_order_by(ordering: OrderingList) -> str:
        """Convert OrderingList to DuckDB ORDER BY clause"""
        if not ordering:
            return ""

        order_exprs = []
        for order_proj in ordering:
            direction = "ASC" if order_proj.ascending else "DESC"
            expr = f"{order_proj.field} {direction}"
            order_exprs.append(expr)

        return ", ".join(order_exprs)

    @staticmethod
    def build_limit(limit: LimitProjection) -> str:
        """Convert LimitProjection to DuckDB LIMIT/OFFSET clause"""
        sql = f"LIMIT {limit.limit}"
        if limit.offset > 0:
            sql += f" OFFSET {limit.offset}"
        return sql

    def build(self, query_projection: QueryProjection) -> Tuple[str, List[Any]]:
        """
        Build complete DuckDB query from QueryProjection

        Args:
            query_projection: The query projection to convert

        Returns:
            Tuple of (query_string, parameters)

        Example:
            builder = DuckDBProjectionBuilder("users")
            sql, params = builder.build(query)
        """
        if not self.table_name:
            raise ValueError(
                "table_name is required for build(). Initialize with DuckDBProjectionBuilder(table_name)"
            )

        query_parts = []
        params: List[Any] = []

        # SELECT clause
        if query_projection.projection:
            select_clause = f"SELECT {self.build_select(query_projection.projection)}"
        else:
            select_clause = "SELECT *"
        query_parts.append(select_clause)

        # FROM clause
        query_parts.append(f"FROM {self.table_name}")

        # WHERE clause
        if query_projection.filter:
            where_clause, where_params = DuckDBSpecificationBuilder.build(
                query_projection.filter
            )
            if where_clause and where_clause != "TRUE":
                query_parts.append(f"WHERE {where_clause}")
                params.extend(where_params)

        # GROUP BY clause
        if query_projection.grouping:
            group_clause = f"GROUP BY {self.build_group_by(query_projection.grouping)}"
            query_parts.append(group_clause)

        # ORDER BY clause
        if query_projection.ordering:
            order_clause = f"ORDER BY {self.build_order_by(query_projection.ordering)}"
            query_parts.append(order_clause)

        # LIMIT/OFFSET clause
        if query_projection.limiting:
            limit_clause = self.build_limit(query_projection.limiting)
            query_parts.append(limit_clause)

        query = " ".join(query_parts)
        return query, params

    def build_count(self, query_projection: QueryProjection) -> Tuple[str, List[Any]]:
        """
        Build optimized COUNT query from QueryProjection

        Ignores SELECT, ORDER BY, and LIMIT clauses for better performance.

        Args:
            query_projection: The query projection to convert

        Returns:
            Tuple of (query_string, parameters)
        """
        if not self.table_name:
            raise ValueError(
                "table_name is required for build_count(). Initialize with DuckDBProjectionBuilder(table_name)"
            )

        query_parts = ["SELECT COUNT(*)"]
        params: List[Any] = []

        # FROM clause
        query_parts.append(f"FROM {self.table_name}")

        # WHERE clause
        if query_projection.filter:
            where_clause, where_params = DuckDBSpecificationBuilder.build(
                query_projection.filter
            )
            if where_clause and where_clause != "TRUE":
                query_parts.append(f"WHERE {where_clause}")
                params.extend(where_params)

        query = " ".join(query_parts)
        return query, params

    def explain(self, query_projection: QueryProjection) -> Tuple[str, List[Any]]:
        """
        Build EXPLAIN query for performance analysis

        Args:
            query_projection: The query projection to analyze

        Returns:
            Tuple of (explain_query_string, parameters)
        """
        if not self.table_name:
            raise ValueError(
                "table_name is required for explain(). Initialize with DuckDBProjectionBuilder(table_name)"
            )

        query, params = self.build(query_projection)
        explain_query = f"EXPLAIN {query}"
        return explain_query, params
