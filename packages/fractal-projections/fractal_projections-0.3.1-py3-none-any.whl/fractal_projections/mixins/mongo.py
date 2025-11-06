"""MongoDB projection mixin for fractal-repositories integration."""

from typing import Any, Iterator, List, Protocol

from pymongo.collection import Collection

from fractal_projections.builders.mongo import MongoProjectionBuilder
from fractal_projections.mixins.base import ProjectionsMixin
from fractal_projections.projections.query import QueryProjection


class _MongoRepositoryProtocol(Protocol):
    """Protocol defining the interface required by MongoProjectionsMixin."""

    collection: Collection


class MongoProjectionsMixin(ProjectionsMixin):
    """
    MongoDB implementation of projection query capabilities.

    Provides advanced querying with projections, aggregations, and grouping
    using fractal_projections.MongoProjectionBuilder.

    Must be used with MongoRepositoryMixin from fractal-repositories.

    Example:
        from fractal_repositories.contrib.mongo import MongoRepositoryMixin
        from fractal_projections import MongoProjectionsMixin

        class MyRepository(MongoRepositoryMixin[MyEntity],
                          MongoProjectionsMixin):
            entity = MyEntity
    """

    def find_with_projection(
        self: _MongoRepositoryProtocol, query_projection: QueryProjection
    ) -> Iterator[Any]:
        """
        Execute a complete query projection with projections, aggregates, etc.

        Returns raw results (not domain entities) since projections may not map to entities.
        """
        builder = MongoProjectionBuilder()
        pipeline = builder.build(query_projection)

        for result in self.collection.aggregate(pipeline):
            yield result

    def count_with_projection(
        self: _MongoRepositoryProtocol, query_projection: QueryProjection
    ) -> int:
        """Count rows matching the query projection (ignores projections)"""
        builder = MongoProjectionBuilder()
        pipeline = builder.build_count(query_projection)

        result = list(self.collection.aggregate(pipeline))
        return result[0]["count"] if result and "count" in result[0] else 0

    def explain_query(
        self: _MongoRepositoryProtocol, query_projection: QueryProjection
    ) -> List[str]:
        """Get query execution plan for performance analysis"""
        builder = MongoProjectionBuilder()
        pipeline = builder.build(query_projection)

        # MongoDB explain returns a dict, convert to list of strings
        explain_result = self.collection.aggregate(pipeline, explain=True)
        return [str(explain_result)]
