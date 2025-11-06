"""
Tests for DuckDB projection builder
"""

import pytest
from fractal_specifications.generic.collections import AndSpecification
from fractal_specifications.generic.operators import (
    EqualsSpecification,
    GreaterThanSpecification,
    InSpecification,
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


class TestDuckDBProjectionBuilder:
    """Tests for DuckDB projection builder"""

    def test_build_select_empty_fields(self):
        """Test building SELECT with no fields returns *"""
        projection = ProjectionList([])
        result = DuckDBProjectionBuilder.build_select(projection)
        assert result == "*"

    def test_build_select_single_field(self):
        """Test building SELECT with single field"""
        projection = ProjectionList([FieldProjection("name")])
        result = DuckDBProjectionBuilder.build_select(projection)
        assert result == "name"

    def test_build_select_multiple_fields(self):
        """Test building SELECT with multiple fields"""
        projection = ProjectionList(
            [
                FieldProjection("id"),
                FieldProjection("name"),
                FieldProjection("email"),
            ]
        )
        result = DuckDBProjectionBuilder.build_select(projection)
        assert result == "id, name, email"

    def test_build_select_field_with_alias(self):
        """Test building SELECT with aliased field"""
        projection = ProjectionList([FieldProjection("user_name", alias="name")])
        result = DuckDBProjectionBuilder.build_select(projection)
        assert result == "user_name AS name"

    def test_build_select_distinct(self):
        """Test building SELECT DISTINCT"""
        projection = ProjectionList([FieldProjection("status")], distinct=True)
        result = DuckDBProjectionBuilder.build_select(projection)
        assert result == "DISTINCT status"

    def test_build_aggregate_count_all(self):
        """Test building COUNT(*) aggregate"""
        projection = ProjectionList([AggregateProjection(AggregateFunction.COUNT)])
        result = DuckDBProjectionBuilder.build_select(projection)
        assert result == "COUNT(*)"

    @pytest.mark.parametrize(
        "function,field,alias,expected_sql",
        [
            (AggregateFunction.COUNT, "id", None, "COUNT(id)"),
            (
                AggregateFunction.COUNT_DISTINCT,
                "user_id",
                None,
                "COUNT(DISTINCT user_id)",
            ),
            (AggregateFunction.SUM, "amount", None, "SUM(amount)"),
            (AggregateFunction.AVG, "score", "avg_score", "AVG(score) AS avg_score"),
        ],
    )
    def test_build_aggregate_functions(self, function, field, alias, expected_sql):
        """Test building aggregate functions (COUNT, COUNT_DISTINCT, SUM, AVG)"""
        projection = ProjectionList(
            [AggregateProjection(function, field=field, alias=alias)]
        )
        result = DuckDBProjectionBuilder.build_select(projection)
        assert result == expected_sql

    def test_build_group_by_single_field(self):
        """Test building GROUP BY with single field"""
        grouping = GroupingProjection(["department"])
        result = DuckDBProjectionBuilder.build_group_by(grouping)
        assert result == "department"

    def test_build_group_by_multiple_fields(self):
        """Test building GROUP BY with multiple fields"""
        grouping = GroupingProjection(["department", "status"])
        result = DuckDBProjectionBuilder.build_group_by(grouping)
        assert result == "department, status"

    def test_build_order_by_single_ascending(self):
        """Test building ORDER BY with single ascending field"""
        ordering = OrderingList([OrderingProjection("name", ascending=True)])
        result = DuckDBProjectionBuilder.build_order_by(ordering)
        assert result == "name ASC"

    def test_build_order_by_single_descending(self):
        """Test building ORDER BY with single descending field"""
        ordering = OrderingList([OrderingProjection("created_at", ascending=False)])
        result = DuckDBProjectionBuilder.build_order_by(ordering)
        assert result == "created_at DESC"

    def test_build_order_by_multiple_fields(self):
        """Test building ORDER BY with multiple fields"""
        ordering = OrderingList(
            [
                OrderingProjection("priority", ascending=False),
                OrderingProjection("name", ascending=True),
            ]
        )
        result = DuckDBProjectionBuilder.build_order_by(ordering)
        assert result == "priority DESC, name ASC"

    def test_build_limit_only(self):
        """Test building LIMIT clause"""
        limiting = LimitProjection(10)
        result = DuckDBProjectionBuilder.build_limit(limiting)
        assert result == "LIMIT 10"

    def test_build_limit_with_offset(self):
        """Test building LIMIT with OFFSET"""
        limiting = LimitProjection(10, offset=20)
        result = DuckDBProjectionBuilder.build_limit(limiting)
        assert result == "LIMIT 10 OFFSET 20"


class TestDuckDBQueryBuilder:
    """Integration tests for DuckDB query building"""

    def test_build_without_table_name_raises_error(self):
        """Test that build() raises error if no table name provided"""
        builder = DuckDBProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="table_name is required"):
            builder.build(query)

    def test_build_count_without_table_name_raises_error(self):
        """Test that build_count() raises error if no table name provided"""
        builder = DuckDBProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="table_name is required"):
            builder.build_count(query)

    def test_explain_without_table_name_raises_error(self):
        """Test that explain() raises error if no table name provided"""
        builder = DuckDBProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="table_name is required"):
            builder.explain(query)

    def test_build_simple_query_no_filter(self):
        """Test building a simple SELECT query without filter"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("id"),
                    FieldProjection("name"),
                ]
            )
        )

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        assert sql == "SELECT id, name FROM users"
        assert params == []

    def test_build_query_with_filter(self):
        """Test building query with WHERE clause"""
        query = QueryProjection(
            filter=EqualsSpecification("status", "active"),
            projection=ProjectionList(
                [
                    FieldProjection("id"),
                    FieldProjection("name"),
                ]
            ),
        )

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        assert sql == "SELECT id, name FROM users WHERE status = ?"
        assert params == ["active"]

    def test_build_query_with_complex_filter(self):
        """Test building query with complex AND filter"""
        query = QueryProjection(
            filter=AndSpecification(
                [
                    EqualsSpecification("status", "active"),
                    GreaterThanSpecification("age", 18),
                ]
            ),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        assert "WHERE" in sql
        assert "status = ?" in sql
        assert "age > ?" in sql
        assert "AND" in sql
        assert params == ["active", 18]

    def test_build_complete_query(self):
        """Test building complete query with all components"""
        query = QueryProjection(
            filter=EqualsSpecification("status", "active"),
            projection=ProjectionList(
                [
                    FieldProjection("id"),
                    FieldProjection("name"),
                    FieldProjection("created_at"),
                ]
            ),
            ordering=OrderingList([OrderingProjection("created_at", ascending=False)]),
            limiting=LimitProjection(10, offset=5),
        )

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build(query)

        assert (
            sql
            == "SELECT id, name, created_at FROM users WHERE status = ? ORDER BY created_at DESC LIMIT 10 OFFSET 5"
        )
        assert params == ["active"]

    def test_build_query_with_grouping(self):
        """Test building query with GROUP BY"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("department"),
                    AggregateProjection(AggregateFunction.COUNT, alias="count"),
                ]
            ),
            grouping=GroupingProjection(["department"]),
        )

        builder = DuckDBProjectionBuilder("employees")
        sql, params = builder.build(query)

        assert (
            sql
            == "SELECT department, COUNT(*) AS count FROM employees GROUP BY department"
        )
        assert params == []

    def test_build_count_simple(self):
        """Test building COUNT query"""
        query = QueryProjection()

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build_count(query)

        assert sql == "SELECT COUNT(*) FROM users"
        assert params == []

    def test_build_count_with_filter(self):
        """Test building COUNT query with WHERE clause"""
        query = QueryProjection(filter=InSpecification("status", ["active", "pending"]))

        builder = DuckDBProjectionBuilder("users")
        sql, params = builder.build_count(query)

        assert sql == "SELECT COUNT(*) FROM users WHERE status IN (?,?)"
        assert params == ["active", "pending"]

    def test_explain_query(self):
        """Test building EXPLAIN query"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            limiting=LimitProjection(10),
        )

        builder = DuckDBProjectionBuilder("users")
        explain_sql, params = builder.explain(query)

        assert explain_sql.startswith("EXPLAIN")
        assert "SELECT name FROM users LIMIT 10" in explain_sql
        assert params == []

    def test_build_query_with_in_filter(self):
        """Test building query with IN clause"""
        query = QueryProjection(
            filter=InSpecification("category", ["electronics", "books", "toys"]),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = DuckDBProjectionBuilder("products")
        sql, params = builder.build(query)

        assert sql == "SELECT name FROM products WHERE category IN (?,?,?)"
        assert params == ["electronics", "books", "toys"]

    def test_build_aggregation_query(self):
        """Test building complex aggregation query"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("department"),
                    AggregateProjection(
                        AggregateFunction.COUNT, alias="employee_count"
                    ),
                    AggregateProjection(
                        AggregateFunction.AVG, field="salary", alias="avg_salary"
                    ),
                    AggregateProjection(
                        AggregateFunction.SUM, field="salary", alias="total_salary"
                    ),
                ]
            ),
            grouping=GroupingProjection(["department"]),
            ordering=OrderingList(
                [OrderingProjection("employee_count", ascending=False)]
            ),
        )

        builder = DuckDBProjectionBuilder("employees")
        sql, params = builder.build(query)

        assert (
            "SELECT department, COUNT(*) AS employee_count, AVG(salary) AS avg_salary, SUM(salary) AS total_salary"
            in sql
        )
        assert "FROM employees" in sql
        assert "GROUP BY department" in sql
        assert "ORDER BY employee_count DESC" in sql
        assert params == []

    def test_build_select_with_invalid_projection_type(self):
        """Test that build_select raises error for unknown projection type (line 53)"""
        # Create an invalid projection type
        class InvalidProjection:
            pass

        projection = ProjectionList([InvalidProjection()])

        builder = DuckDBProjectionBuilder("test_table")

        # Should raise ValueError for unknown projection type
        with pytest.raises(ValueError, match="Unknown projection type"):
            builder.build_select(projection)

    def test_build_order_by_with_none(self):
        """Test build_order_by returns empty string for None (line 95)"""
        result = DuckDBProjectionBuilder.build_order_by(None)
        assert result == ""
