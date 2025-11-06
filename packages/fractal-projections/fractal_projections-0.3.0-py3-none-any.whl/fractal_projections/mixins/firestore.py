"""Firestore projection mixin for fractal-repositories integration."""

from typing import Any, Iterable, Iterator, List, Protocol, Union

from google.cloud.firestore_v1 import DocumentSnapshot, FieldFilter, Query
from google.cloud.firestore_v1.base_collection import BaseCollectionReference
from google.cloud.firestore_v1.base_query import BaseQuery

from fractal_projections.builders.firestore import FirestoreProjectionBuilder
from fractal_projections.mixins.base import ProjectionsMixin
from fractal_projections.projections.query import QueryProjection


class _FirestoreRepositoryProtocol(Protocol):
    """Protocol defining the interface required by FirestoreProjectionsMixin."""

    collection: Union[BaseCollectionReference, BaseQuery]

    @staticmethod
    def _get_collection_stream(collection) -> Iterable[DocumentSnapshot]: ...


class FirestoreProjectionsMixin(ProjectionsMixin):
    """
    Firestore implementation of projection query capabilities.

    Provides advanced querying with projections, aggregations, and filtering
    using fractal_projections.FirestoreProjectionBuilder.

    Must be used with FirestoreRepositoryMixin from fractal-repositories.

    Example:
        from fractal_repositories.contrib.gcp.firestore import FirestoreRepositoryMixin
        from fractal_projections import FirestoreProjectionsMixin

        class MyRepository(FirestoreRepositoryMixin[MyEntity],
                          FirestoreProjectionsMixin):
            entity = MyEntity
    """

    def find_with_projection(
        self: _FirestoreRepositoryProtocol, query_projection: QueryProjection
    ) -> Iterator[Any]:
        """
        Execute a complete query projection with projections, aggregates, etc.

        Returns raw results (not domain entities) since projections may not map to entities.
        """
        builder = FirestoreProjectionBuilder()
        query_config = builder.build(query_projection)

        # Apply query configuration to collection
        collection = self.collection
        if filters := query_config.get("where_clauses"):
            for f in filters:
                collection = collection.where(filter=FieldFilter(*f))

        if order_by := query_config.get("order_by"):
            for ordering in order_by:
                collection = collection.order_by(
                    ordering["field"],
                    direction=(
                        Query.DESCENDING
                        if ordering.get("direction") == "DESC"
                        else Query.ASCENDING
                    ),
                )

        if limit := query_config.get("limit"):
            collection = collection.limit(limit)

        for doc in self._get_collection_stream(collection):
            yield doc.to_dict()

    def count_with_projection(
        self: _FirestoreRepositoryProtocol, query_projection: QueryProjection
    ) -> int:
        """Count rows matching the query projection (ignores projections)"""
        builder = FirestoreProjectionBuilder()
        query_config = builder.build_count(query_projection)

        # Apply filters to collection
        collection = self.collection
        if filters := query_config.get("where_clauses"):
            for f in filters:
                collection = collection.where(filter=FieldFilter(*f))

        count_query = collection.count()
        result = count_query.get()  # type: ignore

        return result[0][0].value if result else 0  # type: ignore

    def explain_query(
        self: _FirestoreRepositoryProtocol, query_projection: QueryProjection
    ) -> List[str]:
        """Get query explanation (Firestore doesn't provide EXPLAIN, returns query structure)"""
        builder = FirestoreProjectionBuilder()
        query_config = builder.build(query_projection)
        return [str(query_config)]
