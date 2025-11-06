"""
Usage Examples for the Fractal Projections Library

This file demonstrates how to use the fractal_projections library
for building database-agnostic query projections.

ARCHITECTURE OVERVIEW:
- Projections: Database-agnostic data shaping definitions (NOT specifications!)
- Builders: Database-specific query generation
  - PostgresProjectionBuilder: Converts projections to PostgreSQL SQL
  - MongoProjectionBuilder: Converts projections to MongoDB aggregation pipelines
  - FirestoreProjectionBuilder: Converts projections to Firestore query configs
  - ElasticsearchProjectionBuilder: Converts projections to ES query DSL

This separation allows the same projections to work across
different databases with optimized native queries for each backend.
"""

from fractal_specifications.generic.collections import AndSpecification
from fractal_specifications.generic.operators import (
    EqualsSpecification,
    GreaterThanSpecification,
    InSpecification,
)

from fractal_projections.projections import (
    AggregateFunction,
    AggregateProjection,
    FieldProjection,
    GroupingProjection,
    LimitProjection,
    OrderingList,
    OrderingProjection,
    ProjectionList,
    QueryProjection,
    QueryProjectionBuilder,
    count,
    select_distinct,
)


def example_basic_select():
    """Basic field selection with filtering"""
    # SELECT organization_id, query FROM syncevent WHERE success = true
    query_projection = QueryProjection(
        filter=EqualsSpecification("success", True),
        projection=ProjectionList(
            [FieldProjection("organization_id"), FieldProjection("query")]
        ),
    )
    return query_projection


def example_distinct_select():
    """SELECT DISTINCT with ordering"""
    # SELECT DISTINCT organization_id FROM syncevent ORDER BY organization_id
    query_projection = QueryProjection(
        projection=ProjectionList([FieldProjection("organization_id")], distinct=True),
        ordering=OrderingList([OrderingProjection("organization_id")]),
    )
    return query_projection


def example_aggregates():
    """Aggregation queries without grouping"""
    # SELECT COUNT(*), AVG(rows), MAX(extraction_ts) FROM syncevent WHERE success = true
    query_projection = QueryProjection(
        filter=EqualsSpecification("success", True),
        projection=ProjectionList(
            [
                AggregateProjection(AggregateFunction.COUNT),
                AggregateProjection(AggregateFunction.AVG, "rows", "avg_rows"),
                AggregateProjection(
                    AggregateFunction.MAX, "extraction_ts", "latest_extraction"
                ),
            ]
        ),
    )
    return query_projection


def example_group_by():
    """Grouping with aggregates"""
    # SELECT organization_id, COUNT(*), SUM(rows)
    # FROM syncevent
    # WHERE success = true
    # GROUP BY organization_id
    # ORDER BY COUNT(*) DESC
    query_projection = QueryProjection(
        filter=EqualsSpecification("success", True),
        projection=ProjectionList(
            [
                FieldProjection("organization_id"),
                AggregateProjection(AggregateFunction.COUNT, alias="total_syncs"),
                AggregateProjection(AggregateFunction.SUM, "rows", "total_rows"),
            ]
        ),
        grouping=GroupingProjection(["organization_id"]),
        ordering=OrderingList([OrderingProjection("total_syncs", ascending=False)]),
    )
    return query_projection


def example_complex_query():
    """Complex query with multiple conditions, grouping, and limits"""
    complex_filter = AndSpecification(
        [
            EqualsSpecification("success", True),
            GreaterThanSpecification("rows", 100),
            InSpecification("organization_id", ["org1", "org2"]),
        ]
    )

    query_projection = QueryProjection(
        filter=complex_filter,
        projection=ProjectionList(
            [
                FieldProjection("organization_id"),
                FieldProjection("connection_id"),
                AggregateProjection(AggregateFunction.COUNT, alias="sync_count"),
                AggregateProjection(AggregateFunction.AVG, "rows", "avg_rows"),
            ]
        ),
        grouping=GroupingProjection(["organization_id", "connection_id"]),
        ordering=OrderingList(
            [
                OrderingProjection("avg_rows", ascending=False),
                OrderingProjection("sync_count", ascending=False),
            ]
        ),
        limiting=LimitProjection(10, 20),
    )
    return query_projection


def example_builder_pattern():
    """Using the fluent builder pattern"""

    # Simple distinct select
    query1 = select_distinct("organization_id").order_by("organization_id").build()

    # Count query
    query2 = count().filter(EqualsSpecification("success", True)).build()

    # Complex aggregation with grouping
    query3 = (
        QueryProjectionBuilder()
        .filter(EqualsSpecification("success", True))
        .select("organization_id", "connection_id")
        .count(alias="total_syncs")
        .avg("rows", "avg_rows")
        .sum("rows", "total_rows")
        .group_by("organization_id", "connection_id")
        .order_by_desc("total_syncs")
        .order_by("organization_id")
        .limit(50)
        .build()
    )

    return [query1, query2, query3]


def example_count_distinct():
    """COUNT DISTINCT queries"""
    # SELECT COUNT(DISTINCT organization_id) FROM syncevent WHERE success = true
    query_projection = QueryProjection(
        filter=EqualsSpecification("success", True),
        projection=ProjectionList(
            [
                AggregateProjection(
                    AggregateFunction.COUNT_DISTINCT, "organization_id", "unique_orgs"
                )
            ]
        ),
    )
    return query_projection


# ============================================================================
# Usage with Repository Mixins
# ============================================================================
#
# The ProjectionsMixin interface provides three methods:
# - find_with_projection(query_projection) -> Iterator[dict]
# - count_with_projection(query_projection) -> int
# - explain_query(query_projection) -> List[str]
#
# All database-specific mixins follow this same interface. The mixin
# internally handles building the appropriate database-specific query.


def example_repository_usage_postgres():
    """Example using PostgresProjectionsMixin"""
    from fractal_repositories.contrib.postgres import PostgresRepositoryMixin

    from fractal_projections.mixins import PostgresProjectionsMixin

    class UserRepository(PostgresRepositoryMixin, PostgresProjectionsMixin):
        table_name = "users"

    # Create repository instance
    repository = UserRepository()

    # Define your query projection
    query_projection = example_group_by()

    # Execute query - mixin handles all builder logic internally
    results = list(repository.find_with_projection(query_projection))
    # Returns: [{'organization_id': 'org1', 'total_syncs': 10, 'total_rows': 5000}, ...]

    # Count matching records
    count = repository.count_with_projection(query_projection)

    # Get query execution plan for optimization
    plan = repository.explain_query(query_projection)
    return results, count, plan


def example_repository_usage_django():
    """Example using DjangoProjectionsMixin"""
    from django.db import models
    from fractal_repositories.contrib.django import DjangoModelRepositoryMixin

    from fractal_projections.mixins import DjangoProjectionsMixin

    # Define your Django model
    class User(models.Model):
        name = models.CharField(max_length=100)
        email = models.EmailField()
        age = models.IntegerField()

        class Meta:
            db_table = "users"

    # Create repository with projection support
    class UserRepository(DjangoModelRepositoryMixin, DjangoProjectionsMixin):
        entity = User
        django_model = User

    repository = UserRepository()
    query_projection = example_group_by()

    # Execute query - returns dictionaries, not model instances
    results = list(repository.find_with_projection(query_projection))
    count = repository.count_with_projection(query_projection)
    plan = repository.explain_query(query_projection)
    return results, count, plan


def example_repository_usage_mongo():
    """Example using MongoProjectionsMixin"""
    from fractal_repositories.contrib.mongo import MongoRepositoryMixin
    from pymongo import MongoClient

    from fractal_projections.mixins import MongoProjectionsMixin

    class EventRepository(MongoRepositoryMixin, MongoProjectionsMixin):
        def __init__(self, collection):
            self.collection = collection

    # Create repository with MongoDB collection
    client = MongoClient("mongodb://localhost:27017")
    collection = client.mydb.events
    repository = EventRepository(collection)

    query_projection = example_group_by()

    # Execute aggregation pipeline - mixin handles pipeline building
    results = list(repository.find_with_projection(query_projection))
    # Returns: [{'organization_id': 'org1', 'total_syncs': 10, 'total_rows': 5000}, ...]

    count = repository.count_with_projection(query_projection)
    plan = repository.explain_query(query_projection)
    return results, count, plan


def example_repository_usage_duckdb():
    """Example using DuckDBProjectionsMixin"""
    import duckdb
    from fractal_repositories.contrib.duckdb import DuckDBRepositoryMixin

    from fractal_projections.mixins import DuckDBProjectionsMixin

    class AnalyticsRepository(DuckDBRepositoryMixin, DuckDBProjectionsMixin):
        table_name = "analytics_events"

        def __init__(self, connection):
            self.connection = connection

    # Create repository with DuckDB connection
    conn = duckdb.connect("my_database.duckdb")
    repository = AnalyticsRepository(conn)

    query_projection = example_group_by()

    # Execute query
    results = list(repository.find_with_projection(query_projection))
    count = repository.count_with_projection(query_projection)
    plan = repository.explain_query(query_projection)
    return results, count, plan


def example_repository_usage_firestore():
    """Example using FirestoreProjectionsMixin"""
    from fractal_repositories.contrib.firestore import FirestoreRepositoryMixin
    from google.cloud import firestore

    from fractal_projections.mixins import FirestoreProjectionsMixin

    class DocumentRepository(FirestoreRepositoryMixin, FirestoreProjectionsMixin):
        collection_name = "documents"

        def __init__(self, db):
            self.db = db

    # Create repository with Firestore client
    db = firestore.Client()
    repository = DocumentRepository(db)

    query_projection = example_group_by()

    # Execute query - note: Firestore has limited aggregation support
    # Complex aggregations may require client-side processing
    results = list(repository.find_with_projection(query_projection))
    count = repository.count_with_projection(query_projection)
    plan = repository.explain_query(query_projection)
    return results, count, plan
