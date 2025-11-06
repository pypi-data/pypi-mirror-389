"""DuckDB projection mixin for fractal-repositories integration."""

from typing import Any, Iterator, List, Protocol

import duckdb

from fractal_projections.builders.duckdb import DuckDBProjectionBuilder
from fractal_projections.mixins.base import ProjectionsMixin
from fractal_projections.projections.query import QueryProjection


class _DuckDBRepositoryProtocol(Protocol):
    """Protocol defining the interface required by DuckDBProjectionsMixin."""

    table_name: str
    connection: duckdb.DuckDBPyConnection

    def _row_to_domain(self, row: tuple) -> Any: ...


class DuckDBProjectionsMixin(ProjectionsMixin):
    """
    DuckDB implementation of projection query capabilities.

    Provides advanced querying with projections, aggregations, grouping, and
    computed fields using fractal_projections.DuckDBProjectionBuilder.

    Must be used with DuckDBRepositoryMixin from fractal-repositories.

    Example:
        from fractal_repositories.contrib.duckdb import DuckDBRepositoryMixin
        from fractal_projections import DuckDBProjectionsMixin

        class MyRepository(DuckDBRepositoryMixin[MyEntity],
                          DuckDBProjectionsMixin):
            entity = MyEntity
    """

    def find_with_projection(
        self: _DuckDBRepositoryProtocol, query_projection: QueryProjection
    ) -> Iterator[Any]:
        """
        Execute a complete query projection with projections, aggregates, etc.

        Returns raw results (not domain entities) since projections may not map to entities.
        """
        builder = DuckDBProjectionBuilder(self.table_name)
        query, params = builder.build(query_projection)

        result = self.connection.execute(query, params)
        column_names = [desc[0] for desc in result.description]

        for row in result.fetchall():
            yield dict(zip(column_names, row, strict=True))

    def count_with_projection(
        self: _DuckDBRepositoryProtocol, query_projection: QueryProjection
    ) -> int:
        """Count rows matching the query projection (ignores projections)"""
        builder = DuckDBProjectionBuilder(self.table_name)
        query, params = builder.build_count(query_projection)

        result = self.connection.execute(query, params).fetchone()
        return result[0] if result else 0

    def explain_query(
        self: _DuckDBRepositoryProtocol, query_projection: QueryProjection
    ) -> List[str]:
        """Get query execution plan for performance analysis"""
        builder = DuckDBProjectionBuilder(self.table_name)
        query, params = builder.explain(query_projection)

        result = self.connection.execute(query, params)
        return [row[0] for row in result.fetchall()]
