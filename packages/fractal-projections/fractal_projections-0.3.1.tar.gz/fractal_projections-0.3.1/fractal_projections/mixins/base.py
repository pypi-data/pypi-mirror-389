from abc import ABC, abstractmethod
from typing import Any, Iterator, List

from fractal_projections.projections.query import QueryProjection


class ProjectionsMixin(ABC):
    """
    Abstract base class for projection query capabilities.

    Projections allow for advanced querying with aggregations, grouping,
    and computed fields that may not map directly to domain entities.

    Implementations should be database-specific (e.g., PostgresProjectionsMixin,
    MongoProjectionsMixin) and must be used alongside their corresponding
    repository mixins from fractal-repositories.

    Requires fractal_projections package for QueryProjection support.
    """

    @abstractmethod
    def find_with_projection(self, query_projection: QueryProjection) -> Iterator[Any]:
        """
        Execute a query projection with projections, aggregates, filters, etc.

        Args:
            query_projection: QueryProjection from fractal_projections package
                defining filters, projections, grouping, ordering, etc.

        Returns:
            Iterator of raw results (dicts/objects) - may not map to domain entities
            since projections can include aggregations and computed fields.

        Example:
            projection = QueryProjection(
                filters=[{"field": "age", "operator": ">", "value": 18}],
                projections=["name", "email"],
                group_by=["name"],
            )
            for result in repo.find_with_projection(projection):
                print(result)  # {'name': 'John', 'email': 'john@example.com'}
        """
        raise NotImplementedError

    @abstractmethod
    def count_with_projection(self, query_projection: QueryProjection) -> int:
        """
        Count rows matching the query projection criteria.

        Args:
            query_projection: QueryProjection from fractal_projections package

        Returns:
            Number of rows matching the projection's filters
            (ignores SELECT/projection fields, only uses WHERE conditions)

        Example:
            projection = QueryProjection(
                filters=[{"field": "age", "operator": ">", "value": 18}]
            )
            count = repo.count_with_projection(projection)  # Returns: 42
        """
        raise NotImplementedError

    @abstractmethod
    def explain_query(self, query_projection: QueryProjection) -> List[str]:
        """
        Get the query execution plan for performance analysis.

        Args:
            query_projection: QueryProjection from fractal_projections package

        Returns:
            List of strings representing the query execution plan
            (format varies by database: EXPLAIN for PostgreSQL, explain() for MongoDB, etc.)

        Example:
            projection = QueryProjection(
                filters=[{"field": "age", "operator": ">", "value": 18}],
                projections=["name"],
            )
            plan = repo.explain_query(projection)
            # PostgreSQL: ['Seq Scan on users  (cost=0.00..35.50 rows=10 width=32)', ...]
        """
        raise NotImplementedError
