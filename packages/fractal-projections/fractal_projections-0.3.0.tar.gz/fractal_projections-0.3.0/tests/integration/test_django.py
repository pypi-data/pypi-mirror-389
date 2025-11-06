"""
Real integration tests for Django builder against actual Django ORM

These tests use Django's test framework with an in-memory SQLite database.
They create a test model, populate it with data, and execute real Django queries.

To run these tests, Django and pytest-django must be installed:
    pip install django pytest-django

If not available, these tests will be skipped.
"""

import pytest

# Skip if Django or pytest-django is not available
pytest.importorskip("django")
pytest.importorskip("pytest_django")

# Configure Django settings before importing Django modules

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
        ],
        SECRET_KEY="test-secret-key",
    )
    django.setup()

from django.db import models
from fractal_specifications.generic.collections import AndSpecification, OrSpecification
from fractal_specifications.generic.operators import (
    EqualsSpecification,
    GreaterThanEqualSpecification,
    GreaterThanSpecification,
    InSpecification,
    LessThanSpecification,
)

from fractal_projections.builders.django import DjangoProjectionBuilder
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


# Define test model
class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    age = models.IntegerField()
    status = models.CharField(max_length=20)
    department = models.CharField(max_length=50)
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        app_label = "test_app"
        db_table = "test_users"


@pytest.fixture(scope="module")
def django_db_setup():
    """Create the test database schema"""
    from django.db import connection

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(User)

    yield

    # Cleanup
    with connection.schema_editor() as schema_editor:
        schema_editor.delete_model(User)


@pytest.fixture
def users(django_db_setup, db, test_user_data):
    """Create test users from shared fixture"""
    user_objects = [User(**user_data) for user_data in test_user_data]
    users = User.objects.bulk_create(user_objects)
    return users


@pytest.mark.django_db
class TestDjangoRealIntegration:
    """Real integration tests against Django ORM"""

    def test_simple_select_all(self, users):
        """Test simple select all with projection"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name"), FieldProjection("age")])
        )

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query)

        results = list(queryset)

        assert len(results) == 8
        assert results[0]["name"] == "Alice"
        assert "age" in results[0]

    def test_filter_equals(self, users):
        """Test filter with equals specification"""
        query = QueryProjection(
            filter=EqualsSpecification("status", "active"),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query)

        results = list(queryset)

        assert len(results) == 5  # 5 active users
        names = [r["name"] for r in results]
        assert "Alice" in names
        assert "Bob" in names
        assert "Charlie" not in names  # inactive

    def test_filter_greater_than(self, users):
        """Test filter with greater than"""
        query = QueryProjection(
            filter=GreaterThanSpecification("age", 30),
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("age"),
                ]
            ),
        )

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query)

        results = list(queryset)

        assert len(results) == 4  # 4 users older than 30
        for result in results:
            assert result["age"] > 30

    def test_filter_in_clause(self, users):
        """Test filter with IN clause"""
        query = QueryProjection(
            filter=InSpecification("department", ["Engineering", "Sales"]),
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("department"),
                ]
            ),
        )

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query)

        results = list(queryset)

        assert len(results) == 6  # 4 Engineering + 2 Sales
        for result in results:
            assert result["department"] in ["Engineering", "Sales"]

    def test_filter_and_condition(self, users):
        """Test filter with AND condition"""
        query = QueryProjection(
            filter=AndSpecification(
                [
                    EqualsSpecification("status", "active"),
                    GreaterThanEqualSpecification("age", 30),
                ]
            ),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query)

        results = list(queryset)

        # Alice (30), Eve (32) - Grace (29) is excluded
        assert len(results) == 2
        names = [r["name"] for r in results]
        assert "Alice" in names
        assert "Eve" in names

    def test_filter_or_condition(self, users):
        """Test filter with OR condition"""
        query = QueryProjection(
            filter=OrSpecification(
                [
                    EqualsSpecification("department", "Sales"),
                    LessThanSpecification("age", 27),
                ]
            ),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query)

        results = list(queryset)

        # Sales: Charlie, Frank; Age < 27: Bob (25)
        assert len(results) == 3
        names = [r["name"] for r in results]
        assert "Bob" in names
        assert "Charlie" in names
        assert "Frank" in names

    def test_order_by_ascending(self, users):
        """Test ORDER BY ascending"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("age"),
                ]
            ),
            ordering=OrderingList([OrderingProjection("age", ascending=True)]),
        )

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query)

        results = list(queryset)

        # Should be ordered by age ascending
        ages = [r["age"] for r in results]
        assert ages == sorted(ages)
        assert results[0]["name"] == "Bob"  # Youngest (25)
        assert results[-1]["name"] == "Frank"  # Oldest (40)

    def test_order_by_descending(self, users):
        """Test ORDER BY descending"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("salary"),
                ]
            ),
            ordering=OrderingList([OrderingProjection("salary", ascending=False)]),
        )

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query)

        results = list(queryset)

        # Should be ordered by salary descending
        salaries = [float(r["salary"]) for r in results]
        assert salaries == sorted(salaries, reverse=True)
        assert results[0]["name"] == "Eve"  # Highest salary (80000)

    def test_limit(self, users):
        """Test LIMIT clause"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            limiting=LimitProjection(3),
        )

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query)

        results = list(queryset)

        assert len(results) == 3

    def test_limit_with_offset(self, users):
        """Test LIMIT with OFFSET"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            ordering=OrderingList([OrderingProjection("id", ascending=True)]),
            limiting=LimitProjection(3, offset=2),
        )

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query)

        results = list(queryset)

        assert len(results) == 3
        # With offset 2, should start from 3rd user (Charlie)
        assert results[0]["name"] == "Charlie"

    def test_group_by_with_count(self, users):
        """Test GROUP BY with COUNT aggregate"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("department"),
                    AggregateProjection(AggregateFunction.COUNT, alias="count"),
                ]
            ),
            grouping=GroupingProjection(["department"]),
        )

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query)

        results = list(queryset)

        # Should have 3 departments
        assert len(results) == 3

        # Convert to dict for easier testing
        dept_counts = {r["department"]: r["count"] for r in results}
        assert dept_counts["Engineering"] == 4
        assert dept_counts["Sales"] == 2
        assert dept_counts["Marketing"] == 2

    def test_group_by_with_avg(self, users):
        """Test GROUP BY with AVG aggregate"""
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

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query)

        results = list(queryset)

        assert len(results) == 3

        # Engineering: (75000 + 65000 + 80000 + 76000) / 4 = 74000
        dept_avgs = {r["department"]: float(r["avg_salary"]) for r in results}
        assert abs(dept_avgs["Engineering"] - 74000.0) < 0.01

    def test_group_by_with_multiple_aggregates(self, users):
        """Test GROUP BY with multiple aggregates"""
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

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query)

        results = list(queryset)

        # Should have 3 statuses
        assert len(results) == 3

        # Find active status row
        active_row = [r for r in results if r["status"] == "active"][0]
        assert active_row["count"] == 5  # 5 active users
        # avg_age for active: (30+25+28+32+29)/5 = 28.8
        assert abs(float(active_row["avg_age"]) - 28.8) < 0.1

    def test_count_query(self, users):
        """Test count query"""
        query = QueryProjection(filter=EqualsSpecification("status", "active"))

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build_count(query)

        count = queryset.count()

        assert count == 5  # 5 active users

    def test_global_aggregation_no_grouping(self, users):
        """Test aggregation without grouping"""
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

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query)

        results = list(queryset)

        assert len(results) == 1
        assert results[0]["total"] == 8
        # Average salary of all users
        expected_avg = (
            75000 + 65000 + 70000 + 68000 + 80000 + 72000 + 69000 + 76000
        ) / 8
        assert abs(float(results[0]["avg_salary"]) - expected_avg) < 0.01

    def test_complex_query(self, users):
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

        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query)

        results = list(queryset)

        # Should have results
        assert len(results) > 0
        assert len(results) <= 5

        # All should be active or pending, and age > 25
        for result in results:
            assert result["age"] > 25
