"""
Real integration tests for DuckDB builder against actual DuckDB database

These tests create an in-memory DuckDB database, populate it with test data,
and execute the generated queries to verify they work correctly.
"""

import pytest

pytest.importorskip("duckdb")

import duckdb
from fractal_specifications.generic.collections import AndSpecification, OrSpecification
from fractal_specifications.generic.operators import (
    EqualsSpecification,
    GreaterThanEqualSpecification,
    GreaterThanSpecification,
    InSpecification,
    LessThanSpecification,
)

from fractal_projections.builders.duckdb import DuckDBProjectionBuilder
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
def duckdb_connection(test_user_data):
    """Create an in-memory DuckDB connection with test data"""
    conn = duckdb.connect(":memory:")

    # Create users table
    conn.execute(
        """
        CREATE TABLE users (
            id INTEGER,
            name VARCHAR,
            email VARCHAR,
            age INTEGER,
            status VARCHAR,
            department VARCHAR,
            salary DECIMAL(10, 2),
            created_at TIMESTAMP
        )
    """
    )

    # Insert test data from shared fixture
    # Add synthetic created_at timestamps based on user ID
    base_timestamps = [
        "2023-01-15 10:00:00",
        "2023-02-20 11:00:00",
        "2023-03-10 12:00:00",
        "2023-04-05 13:00:00",
        "2023-05-12 14:00:00",
        "2023-06-18 15:00:00",
        "2023-07-22 16:00:00",
        "2023-08-30 17:00:00",
    ]

    for i, user in enumerate(test_user_data):
        conn.execute(
            """
            INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                user["id"],
                user["name"],
                user["email"],
                user["age"],
                user["status"],
                user["department"],
                user["salary"],
                base_timestamps[i],
            ],
        )

    yield conn
    conn.close()


class TestDuckDBRealIntegration:
    """Real integration tests against DuckDB"""

    def test_simple_select_all(self, duckdb_connection):
        """Test simple SELECT * query"""
        query = QueryProjection()

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        assert len(result) == 8
        assert result[0][1] == "Alice"  # name column

    def test_select_specific_fields(self, duckdb_connection):
        """Test SELECT with specific fields"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("age"),
                ]
            )
        )

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        assert len(result) == 8
        assert len(result[0]) == 2  # Only 2 columns
        assert result[0][0] == "Alice"
        assert result[0][1] == 30

    def test_filter_equals(self, duckdb_connection):
        """Test WHERE with equals filter"""
        query = QueryProjection(
            filter=EqualsSpecification("status", "active"),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        assert len(result) == 5  # 5 active users
        names = [row[0] for row in result]
        assert "Alice" in names
        assert "Bob" in names
        assert "Charlie" not in names  # inactive

    def test_filter_greater_than(self, duckdb_connection):
        """Test WHERE with greater than filter"""
        query = QueryProjection(
            filter=GreaterThanSpecification("age", 30),
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("age"),
                ]
            ),
        )

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        assert len(result) == 4  # 4 users older than 30
        for row in result:
            assert row[1] > 30

    def test_filter_in_clause(self, duckdb_connection):
        """Test WHERE with IN clause"""
        query = QueryProjection(
            filter=InSpecification("department", ["Engineering", "Sales"]),
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("department"),
                ]
            ),
        )

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        assert len(result) == 6  # 4 Engineering + 2 Sales
        for row in result:
            assert row[1] in ["Engineering", "Sales"]

    def test_filter_and_condition(self, duckdb_connection):
        """Test WHERE with AND condition"""
        query = QueryProjection(
            filter=AndSpecification(
                [
                    EqualsSpecification("status", "active"),
                    GreaterThanEqualSpecification("age", 30),
                ]
            ),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        # Alice (30), Eve (32) - Grace (29) is excluded because age >= 30
        assert len(result) == 2
        names = [row[0] for row in result]
        assert "Alice" in names
        assert "Eve" in names

    def test_filter_or_condition(self, duckdb_connection):
        """Test WHERE with OR condition"""
        query = QueryProjection(
            filter=OrSpecification(
                [
                    EqualsSpecification("department", "Sales"),
                    LessThanSpecification("age", 27),
                ]
            ),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        # Sales: Charlie, Frank
        # Age < 27: Bob (25)
        assert len(result) == 3
        names = [row[0] for row in result]
        assert "Bob" in names
        assert "Charlie" in names
        assert "Frank" in names

    def test_order_by_ascending(self, duckdb_connection):
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

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        # Should be ordered by age ascending
        ages = [row[1] for row in result]
        assert ages == sorted(ages)
        assert result[0][0] == "Bob"  # Youngest (25)
        assert result[-1][0] == "Frank"  # Oldest (40)

    def test_order_by_descending(self, duckdb_connection):
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

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        # Should be ordered by salary descending
        salaries = [float(row[1]) for row in result]
        assert salaries == sorted(salaries, reverse=True)
        assert result[0][0] == "Eve"  # Highest salary (80000)

    def test_limit(self, duckdb_connection):
        """Test LIMIT clause"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            limiting=LimitProjection(3),
        )

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        assert len(result) == 3

    def test_limit_with_offset(self, duckdb_connection):
        """Test LIMIT with OFFSET"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            ordering=OrderingList([OrderingProjection("id", ascending=True)]),
            limiting=LimitProjection(3, offset=2),
        )

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        assert len(result) == 3
        # With offset 2, should start from 3rd user (Charlie)
        assert result[0][0] == "Charlie"

    def test_group_by_with_count(self, duckdb_connection):
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

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        # Should have 3 departments
        assert len(result) == 3

        # Convert to dict for easier testing
        dept_counts = {row[0]: row[1] for row in result}
        assert dept_counts["Engineering"] == 4
        assert dept_counts["Sales"] == 2
        assert dept_counts["Marketing"] == 2

    def test_group_by_with_avg(self, duckdb_connection):
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

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        assert len(result) == 3

        # Engineering: (75000 + 65000 + 80000 + 76000) / 4 = 74000
        dept_avgs = {row[0]: float(row[1]) for row in result}
        assert abs(dept_avgs["Engineering"] - 74000.0) < 0.01

    def test_group_by_with_multiple_aggregates(self, duckdb_connection):
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
            ordering=OrderingList([OrderingProjection("status", ascending=True)]),
        )

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        # Should have 3 statuses
        assert len(result) == 3

        # Find active status row
        active_row = [row for row in result if row[0] == "active"][0]
        assert active_row[1] == 5  # 5 active users
        # avg_age for active: (30+25+28+32+29)/5 = 28.8
        assert abs(float(active_row[2]) - 28.8) < 0.1

    def test_count_query(self, duckdb_connection):
        """Test optimized COUNT query"""
        query = QueryProjection(filter=EqualsSpecification("status", "active"))

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build_count(query)

        result = duckdb_connection.execute(sql, params).fetchone()

        assert result[0] == 5  # 5 active users

    def test_distinct_select(self, duckdb_connection):
        """Test SELECT DISTINCT"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("department")], distinct=True)
        )

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        assert len(result) == 3  # 3 unique departments
        departments = [row[0] for row in result]
        assert "Engineering" in departments
        assert "Sales" in departments
        assert "Marketing" in departments

    def test_complex_query(self, duckdb_connection):
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

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        result = duckdb_connection.execute(sql, params).fetchall()

        # Should have results
        assert len(result) > 0
        assert len(result) <= 5

        # All should be active or pending, and age > 25
        for row in result:
            age = row[1]
            assert age > 25

    def test_explain_query(self, duckdb_connection):
        """Test that EXPLAIN query executes without error"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            limiting=LimitProjection(10),
        )

        builder = DuckDBProjectionBuilder("users")
        explain_sql, params = builder.explain(query)

        # EXPLAIN queries return different format, just verify it executes
        result = duckdb_connection.execute(explain_sql, params).fetchall()

        # Should return some explanation output
        assert len(result) > 0
