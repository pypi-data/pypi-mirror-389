"""
Real integration tests for MongoDB builder against actual MongoDB

These tests use mongomock to simulate MongoDB without requiring a real MongoDB server.
The tests create a mock database, populate it with test data,
and execute the generated aggregation pipelines to verify they work correctly.
"""

import pytest

pytest.importorskip("mongomock")

import mongomock
from fractal_specifications.generic.collections import AndSpecification, OrSpecification
from fractal_specifications.generic.operators import (
    EqualsSpecification,
    GreaterThanEqualSpecification,
    GreaterThanSpecification,
    InSpecification,
    LessThanSpecification,
)

from fractal_projections.builders.mongo import MongoProjectionBuilder
from fractal_projections.projections.fields import (
    AggregateFunction,
    AggregateProjection,
    FieldProjection,
    ProjectionList,
)
from fractal_projections.projections.grouping import GroupingProjection
from fractal_projections.projections.limiting import LimitProjection
from fractal_projections.projections.ordering import OrderingList, OrderingProjection
from fractal_projections.projections.query import QueryProjection


@pytest.fixture
def mongo_collection(test_user_data):
    """Create a mock MongoDB collection with test data"""
    client = mongomock.MongoClient()
    db = client.test_db
    collection = db.users

    # Convert shared test data to MongoDB format (id -> _id)
    mongo_data = []
    for user in test_user_data:
        mongo_user = user.copy()
        mongo_user["_id"] = mongo_user.pop("id")
        mongo_data.append(mongo_user)

    # Insert test data
    collection.insert_many(mongo_data)

    yield collection


class TestMongoRealIntegration:
    """Real integration tests against MongoDB (using mongomock)"""

    def test_simple_find_all(self, mongo_collection):
        """Test simple find all documents"""
        query = QueryProjection()

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        assert len(result) == 8
        assert result[0]["name"] == "Alice"

    def test_project_specific_fields(self, mongo_collection):
        """Test projection with specific fields"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("age"),
                ]
            )
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        assert len(result) == 8
        assert "name" in result[0]
        assert "age" in result[0]
        # Other fields should not be present (except _id which MongoDB always includes)
        assert "email" not in result[0]

    def test_filter_equals(self, mongo_collection):
        """Test $match with equals filter"""
        query = QueryProjection(
            filter=EqualsSpecification("status", "active"),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        assert len(result) == 5  # 5 active users
        names = [doc["name"] for doc in result]
        assert "Alice" in names
        assert "Bob" in names
        assert "Charlie" not in names  # inactive

    def test_filter_greater_than(self, mongo_collection):
        """Test $match with greater than filter"""
        query = QueryProjection(
            filter=GreaterThanSpecification("age", 30),
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("age"),
                ]
            ),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        assert len(result) == 4  # 4 users older than 30
        for doc in result:
            assert doc["age"] > 30

    def test_filter_in_clause(self, mongo_collection):
        """Test $match with $in operator"""
        query = QueryProjection(
            filter=InSpecification("department", ["Engineering", "Sales"]),
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("department"),
                ]
            ),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        assert len(result) == 6  # 4 Engineering + 2 Sales
        for doc in result:
            assert doc["department"] in ["Engineering", "Sales"]

    def test_filter_and_condition(self, mongo_collection):
        """Test $match with AND condition"""
        query = QueryProjection(
            filter=AndSpecification(
                [
                    EqualsSpecification("status", "active"),
                    GreaterThanEqualSpecification("age", 30),
                ]
            ),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        # Alice (30), Eve (32) - Grace (29) is excluded
        assert len(result) == 2
        names = [doc["name"] for doc in result]
        assert "Alice" in names
        assert "Eve" in names

    def test_filter_or_condition(self, mongo_collection):
        """Test $match with OR condition"""
        query = QueryProjection(
            filter=OrSpecification(
                [
                    EqualsSpecification("department", "Sales"),
                    LessThanSpecification("age", 27),
                ]
            ),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        # Sales: Charlie, Frank; Age < 27: Bob (25)
        assert len(result) == 3
        names = [doc["name"] for doc in result]
        assert "Bob" in names
        assert "Charlie" in names
        assert "Frank" in names

    def test_sort_ascending(self, mongo_collection):
        """Test $sort ascending"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("age"),
                ]
            ),
            ordering=OrderingList([OrderingProjection("age", ascending=True)]),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        # Should be ordered by age ascending
        ages = [doc["age"] for doc in result]
        assert ages == sorted(ages)
        assert result[0]["name"] == "Bob"  # Youngest (25)
        assert result[-1]["name"] == "Frank"  # Oldest (40)

    def test_sort_descending(self, mongo_collection):
        """Test $sort descending"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("salary"),
                ]
            ),
            ordering=OrderingList([OrderingProjection("salary", ascending=False)]),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        # Should be ordered by salary descending
        salaries = [doc["salary"] for doc in result]
        assert salaries == sorted(salaries, reverse=True)
        assert result[0]["name"] == "Eve"  # Highest salary (80000)

    def test_limit(self, mongo_collection):
        """Test $limit stage"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            limiting=LimitProjection(3),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        assert len(result) == 3

    def test_limit_with_offset(self, mongo_collection):
        """Test $limit with $skip"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            ordering=OrderingList([OrderingProjection("_id", ascending=True)]),
            limiting=LimitProjection(3, offset=2),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        assert len(result) == 3
        # With offset 2, should start from 3rd user (Charlie)
        assert result[0]["name"] == "Charlie"

    def test_group_by_with_count(self, mongo_collection):
        """Test $group with COUNT aggregate"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("department"),
                    AggregateProjection(AggregateFunction.COUNT, alias="count"),
                ]
            ),
            grouping=GroupingProjection(["department"]),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        # Should have 3 departments
        assert len(result) == 3

        # Convert to dict for easier testing
        dept_counts = {doc["department"]: doc["count"] for doc in result}
        assert dept_counts["Engineering"] == 4
        assert dept_counts["Sales"] == 2
        assert dept_counts["Marketing"] == 2

    def test_group_by_with_avg(self, mongo_collection):
        """Test $group with AVG aggregate"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("department"),
                    AggregateProjection(
                        AggregateFunction.AVG, field="salary", alias="avg_salary"
                    ),
                ]
            ),
            grouping=GroupingProjection(["department"]),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        assert len(result) == 3

        # Engineering: (75000 + 65000 + 80000 + 76000) / 4 = 74000
        dept_avgs = {doc["department"]: doc["avg_salary"] for doc in result}
        assert abs(dept_avgs["Engineering"] - 74000.0) < 0.01

    def test_group_by_with_multiple_aggregates(self, mongo_collection):
        """Test $group with multiple aggregates"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("status"),
                    AggregateProjection(AggregateFunction.COUNT, alias="count"),
                    AggregateProjection(
                        AggregateFunction.AVG, field="age", alias="avg_age"
                    ),
                    AggregateProjection(
                        AggregateFunction.MIN, field="salary", alias="min_salary"
                    ),
                    AggregateProjection(
                        AggregateFunction.MAX, field="salary", alias="max_salary"
                    ),
                ]
            ),
            grouping=GroupingProjection(["status"]),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        # Should have 3 statuses
        assert len(result) == 3

        # Find active status row
        active_doc = [doc for doc in result if doc["status"] == "active"][0]
        assert active_doc["count"] == 5  # 5 active users
        # avg_age for active: (30+25+28+32+29)/5 = 28.8
        assert abs(active_doc["avg_age"] - 28.8) < 0.1

    def test_count_query(self, mongo_collection):
        """Test optimized COUNT query"""
        query = QueryProjection(filter=EqualsSpecification("status", "active"))

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build_count(query)

        result = list(mongo_collection.aggregate(pipeline))

        assert result[0]["count"] == 5  # 5 active users

    def test_global_aggregation_no_grouping(self, mongo_collection):
        """Test aggregation without grouping (global aggregation)"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    AggregateProjection(AggregateFunction.COUNT, alias="total"),
                    AggregateProjection(
                        AggregateFunction.AVG, field="salary", alias="avg_salary"
                    ),
                ]
            )
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        assert len(result) == 1
        assert result[0]["total"] == 8
        # Average salary of all users
        expected_avg = (
            75000 + 65000 + 70000 + 68000 + 80000 + 72000 + 69000 + 76000
        ) / 8
        assert abs(result[0]["avg_salary"] - expected_avg) < 0.01

    def test_complex_query(self, mongo_collection):
        """Test complex query with multiple features"""
        query = QueryProjection(
            filter=AndSpecification(
                [
                    InSpecification("status", ["active", "pending"]),
                    GreaterThanSpecification("age", 25),
                ]
            ),
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("age"),
                    FieldProjection("department"),
                    FieldProjection("salary"),
                ]
            ),
            ordering=OrderingList(
                [
                    OrderingProjection("department", ascending=True),
                    OrderingProjection("salary", ascending=False),
                ]
            ),
            limiting=LimitProjection(5),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        result = list(mongo_collection.aggregate(pipeline))

        # Should have results
        assert len(result) > 0
        assert len(result) <= 5

        # All should be active or pending, and age > 25
        for doc in result:
            assert doc["age"] > 25
