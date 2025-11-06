"""PostgreSQL projection mixin for fractal-repositories integration."""

from typing import Any, Iterator, List, Protocol

import psycopg2
import psycopg2.extras

from fractal_projections.builders.postgres import PostgresProjectionBuilder
from fractal_projections.mixins.base import ProjectionsMixin
from fractal_projections.projections.query import QueryProjection


class _PostgresRepositoryProtocol(Protocol):
    """Protocol defining the interface required by PostgresProjectionsMixin."""

    table_name: str

    def _get_connection(self) -> Any: ...


class PostgresProjectionsMixin(ProjectionsMixin):
    """
    PostgreSQL implementation of projection query capabilities.

    Provides advanced querying with projections, aggregations, grouping, and
    computed fields using fractal_projections.PostgresProjectionBuilder.

    Must be used with PostgresRepositoryMixin from fractal-repositories.

    Example:
        from fractal_repositories.contrib.postgresql import PostgresRepositoryMixin
        from fractal_projections import PostgresProjectionsMixin

        class MyRepository(PostgresRepositoryMixin[MyEntity],
                          PostgresProjectionsMixin):
            entity = MyEntity
    """

    def find_with_projection(
        self: _PostgresRepositoryProtocol, query_projection: QueryProjection
    ) -> Iterator[Any]:
        """
        Execute a complete query projection with projections, aggregates, etc.

        Returns raw results (not domain entities) since projections may not map to entities.
        """
        builder = PostgresProjectionBuilder(self.table_name)
        query, params = builder.build(query_projection)

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params)
                for row in cur:
                    yield dict(row)

    def count_with_projection(
        self: _PostgresRepositoryProtocol, query_projection: QueryProjection
    ) -> int:
        """Count rows matching the query projection (ignores projections)"""
        builder = PostgresProjectionBuilder(self.table_name)
        query, params = builder.build_count(query_projection)

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchone()[0]

    def explain_query(
        self: _PostgresRepositoryProtocol, query_projection: QueryProjection
    ) -> List[str]:
        """Get query execution plan for performance analysis"""
        builder = PostgresProjectionBuilder(self.table_name)
        query, params = builder.explain(query_projection)

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return [row[0] for row in cur.fetchall()]
