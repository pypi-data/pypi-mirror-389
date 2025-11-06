"""
Tests for PostgreSQL projection builder
"""

import pytest
from fractal_specifications.generic.collections import AndSpecification
from fractal_specifications.generic.operators import (
    EqualsSpecification,
    GreaterThanSpecification,
    InSpecification,
)

from fractal_projections import (
    AggregateFunction,
    AggregateProjection,
    FieldProjection,
    GroupingProjection,
    LimitProjection,
    OrderingList,
    OrderingProjection,
    PostgresProjectionBuilder,
    ProjectionList,
    QueryProjection,
)


class TestPostgresProjectionBuilder:
    """Tests for PostgreSQL projection builder"""

    def test_build_select_empty_fields(self):
        """Test building SELECT with no fields returns *"""
        projection = ProjectionList([])
        result = PostgresProjectionBuilder.build_select(projection)
        assert result == "*"

    def test_build_select_single_field(self):
        """Test building SELECT with single field"""
        projection = ProjectionList([FieldProjection("name")])
        result = PostgresProjectionBuilder.build_select(projection)
        assert result == "name"

    def test_build_select_multiple_fields(self):
        """Test building SELECT with multiple fields"""
        projection = ProjectionList(
            [FieldProjection("name"), FieldProjection("email"), FieldProjection("age")]
        )
        result = PostgresProjectionBuilder.build_select(projection)
        assert result == "name, email, age"

    def test_build_select_field_with_alias(self):
        """Test building SELECT with field alias"""
        projection = ProjectionList([FieldProjection("name", alias="full_name")])
        result = PostgresProjectionBuilder.build_select(projection)
        assert result == "name AS full_name"

    def test_build_select_distinct(self):
        """Test building SELECT DISTINCT"""
        projection = ProjectionList([FieldProjection("category")], distinct=True)
        result = PostgresProjectionBuilder.build_select(projection)
        assert result == "DISTINCT category"

    def test_build_select_distinct_multiple_fields(self):
        """Test building SELECT DISTINCT with multiple fields"""
        projection = ProjectionList(
            [FieldProjection("category"), FieldProjection("status")], distinct=True
        )
        result = PostgresProjectionBuilder.build_select(projection)
        assert result == "DISTINCT category, status"

    def test_build_aggregate_count_all(self):
        """Test building COUNT(*) aggregate"""
        projection = ProjectionList([AggregateProjection(AggregateFunction.COUNT)])
        result = PostgresProjectionBuilder.build_select(projection)
        assert result == "COUNT(*)"

    def test_build_aggregate_count_with_field(self):
        """Test building COUNT with field"""
        projection = ProjectionList(
            [AggregateProjection(AggregateFunction.COUNT, "user_id")]
        )
        result = PostgresProjectionBuilder.build_select(projection)
        assert result == "COUNT(user_id)"

    def test_build_aggregate_count_with_alias(self):
        """Test building COUNT with alias"""
        projection = ProjectionList(
            [AggregateProjection(AggregateFunction.COUNT, alias="total")]
        )
        result = PostgresProjectionBuilder.build_select(projection)
        assert result == "COUNT(*) AS total"

    @pytest.mark.parametrize(
        "function,field,alias,expected_sql",
        [
            (
                AggregateFunction.SUM,
                "amount",
                "total_amount",
                "SUM(amount) AS total_amount",
            ),
            (
                AggregateFunction.AVG,
                "salary",
                "avg_salary",
                "AVG(salary) AS avg_salary",
            ),
            (AggregateFunction.MIN, "price", None, "MIN(price)"),
            (AggregateFunction.MAX, "price", None, "MAX(price)"),
            (
                AggregateFunction.COUNT_DISTINCT,
                "user_id",
                "unique_users",
                "COUNT(DISTINCT user_id) AS unique_users",
            ),
        ],
    )
    def test_build_aggregate_functions(self, function, field, alias, expected_sql):
        """Test building aggregate functions (SUM, AVG, MIN, MAX, COUNT_DISTINCT)"""
        projection = ProjectionList([AggregateProjection(function, field, alias)])
        result = PostgresProjectionBuilder.build_select(projection)
        assert result == expected_sql

    def test_build_select_mixed_fields_and_aggregates(self):
        """Test building SELECT with mixed field and aggregate projections"""
        projection = ProjectionList(
            [
                FieldProjection("department"),
                AggregateProjection(AggregateFunction.COUNT, alias="employee_count"),
                AggregateProjection(AggregateFunction.AVG, "salary", "avg_salary"),
            ]
        )
        result = PostgresProjectionBuilder.build_select(projection)
        expected = "department, COUNT(*) AS employee_count, AVG(salary) AS avg_salary"
        assert result == expected

    def test_build_group_by_single_field(self):
        """Test building GROUP BY with single field"""
        grouping = GroupingProjection(["department"])
        result = PostgresProjectionBuilder.build_group_by(grouping)
        assert result == "department"

    def test_build_group_by_multiple_fields(self):
        """Test building GROUP BY with multiple fields"""
        grouping = GroupingProjection(["department", "role", "location"])
        result = PostgresProjectionBuilder.build_group_by(grouping)
        assert result == "department, role, location"

    def test_build_order_by_empty(self):
        """Test building ORDER BY with empty list"""
        ordering = OrderingList([])
        result = PostgresProjectionBuilder.build_order_by(ordering)
        assert result == ""

    def test_build_order_by_single_ascending(self):
        """Test building ORDER BY with single ascending field"""
        ordering = OrderingList([OrderingProjection("name", ascending=True)])
        result = PostgresProjectionBuilder.build_order_by(ordering)
        assert result == "name ASC"

    def test_build_order_by_single_descending(self):
        """Test building ORDER BY with single descending field"""
        ordering = OrderingList([OrderingProjection("created_at", ascending=False)])
        result = PostgresProjectionBuilder.build_order_by(ordering)
        assert result == "created_at DESC"

    def test_build_order_by_multiple_fields(self):
        """Test building ORDER BY with multiple fields"""
        ordering = OrderingList(
            [
                OrderingProjection("department", ascending=True),
                OrderingProjection("salary", ascending=False),
                OrderingProjection("name", ascending=True),
            ]
        )
        result = PostgresProjectionBuilder.build_order_by(ordering)
        assert result == "department ASC, salary DESC, name ASC"

    def test_build_limit_only(self):
        """Test building LIMIT without offset"""
        limit = LimitProjection(10)
        result = PostgresProjectionBuilder.build_limit(limit)
        assert result == "LIMIT 10"

    def test_build_limit_with_offset(self):
        """Test building LIMIT with offset"""
        limit = LimitProjection(20, offset=40)
        result = PostgresProjectionBuilder.build_limit(limit)
        assert result == "LIMIT 20 OFFSET 40"

    def test_build_limit_large_values(self):
        """Test building LIMIT with large values"""
        limit = LimitProjection(1000, offset=5000)
        result = PostgresProjectionBuilder.build_limit(limit)
        assert result == "LIMIT 1000 OFFSET 5000"

    def test_build_field_projection_without_alias(self):
        """Test _build_field_projection without alias"""
        field = FieldProjection("email")
        result = PostgresProjectionBuilder._build_field_projection(field)
        assert result == "email"

    def test_build_field_projection_with_alias(self):
        """Test _build_field_projection with alias"""
        field = FieldProjection("email", alias="user_email")
        result = PostgresProjectionBuilder._build_field_projection(field)
        assert result == "email AS user_email"

    def test_build_aggregate_projection_count_all(self):
        """Test _build_aggregate_projection for COUNT(*)"""
        agg = AggregateProjection(AggregateFunction.COUNT)
        result = PostgresProjectionBuilder._build_aggregate_projection(agg)
        assert result == "COUNT(*)"

    def test_build_aggregate_projection_count_distinct(self):
        """Test _build_aggregate_projection for COUNT DISTINCT"""
        agg = AggregateProjection(AggregateFunction.COUNT_DISTINCT, "user_id")
        result = PostgresProjectionBuilder._build_aggregate_projection(agg)
        assert result == "COUNT(DISTINCT user_id)"

    def test_build_aggregate_projection_sum(self):
        """Test _build_aggregate_projection for SUM"""
        agg = AggregateProjection(AggregateFunction.SUM, "amount")
        result = PostgresProjectionBuilder._build_aggregate_projection(agg)
        assert result == "SUM(amount)"

    def test_build_aggregate_projection_with_alias(self):
        """Test _build_aggregate_projection with alias"""
        agg = AggregateProjection(AggregateFunction.AVG, "salary", "avg_salary")
        result = PostgresProjectionBuilder._build_aggregate_projection(agg)
        assert result == "AVG(salary) AS avg_salary"

    def test_build_select_invalid_projection_type_raises_error(self):
        """Test that invalid projection type raises ValueError"""

        class InvalidProjection:
            pass

        projection = ProjectionList([InvalidProjection()])

        with pytest.raises(ValueError, match="Unknown projection type"):
            PostgresProjectionBuilder.build_select(projection)

    def test_integration_complex_query_parts(self):
        """Test building all parts of a complex query"""
        # SELECT department, COUNT(*) as employee_count, AVG(salary) as avg_salary
        select_projection = ProjectionList(
            [
                FieldProjection("department"),
                AggregateProjection(AggregateFunction.COUNT, alias="employee_count"),
                AggregateProjection(AggregateFunction.AVG, "salary", "avg_salary"),
            ]
        )

        # GROUP BY department
        grouping = GroupingProjection(["department"])

        # ORDER BY employee_count DESC, avg_salary DESC
        ordering = OrderingList(
            [
                OrderingProjection("employee_count", ascending=False),
                OrderingProjection("avg_salary", ascending=False),
            ]
        )

        # LIMIT 10
        limiting = LimitProjection(10)

        select_clause = PostgresProjectionBuilder.build_select(select_projection)
        group_by_clause = PostgresProjectionBuilder.build_group_by(grouping)
        order_by_clause = PostgresProjectionBuilder.build_order_by(ordering)
        limit_clause = PostgresProjectionBuilder.build_limit(limiting)

        # Verify each part
        assert "department" in select_clause
        assert "COUNT(*) AS employee_count" in select_clause
        assert "AVG(salary) AS avg_salary" in select_clause

        assert group_by_clause == "department"

        assert "employee_count DESC" in order_by_clause
        assert "avg_salary DESC" in order_by_clause

        assert limit_clause == "LIMIT 10"

    def test_build_without_table_name_raises_error(self):
        """Test that build() raises error if no table name provided"""
        builder = PostgresProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="table_name is required"):
            builder.build(query)

    def test_build_count_without_table_name_raises_error(self):
        """Test that build_count() raises error if no table name provided"""
        builder = PostgresProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="table_name is required"):
            builder.build_count(query)

    def test_explain_without_table_name_raises_error(self):
        """Test that explain() raises error if no table name provided"""
        builder = PostgresProjectionBuilder()
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

        builder = PostgresProjectionBuilder("users")
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

        builder = PostgresProjectionBuilder("users")
        sql, params = builder.build(query)

        assert "SELECT id, name FROM users WHERE status = %s" == sql
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

        builder = PostgresProjectionBuilder("users")
        sql, params = builder.build(query)

        assert "WHERE" in sql
        assert "status = %s" in sql
        assert "age > %s" in sql
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

        builder = PostgresProjectionBuilder("users")
        sql, params = builder.build(query)

        assert (
            sql
            == "SELECT id, name, created_at FROM users WHERE status = %s ORDER BY created_at DESC LIMIT 10 OFFSET 5"
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

        builder = PostgresProjectionBuilder("employees")
        sql, params = builder.build(query)

        assert (
            "SELECT department, COUNT(*) AS count FROM employees GROUP BY department"
            == sql
        )
        assert params == []

    def test_build_count_simple(self):
        """Test building COUNT query"""
        query = QueryProjection()

        builder = PostgresProjectionBuilder("users")
        sql, params = builder.build_count(query)

        assert sql == "SELECT COUNT(*) FROM users"
        assert params == []

    def test_build_count_with_filter(self):
        """Test building COUNT query with WHERE clause"""
        query = QueryProjection(filter=InSpecification("status", ["active", "pending"]))

        builder = PostgresProjectionBuilder("users")
        sql, params = builder.build_count(query)

        assert "SELECT COUNT(*) FROM users WHERE status IN (%s,%s)" == sql
        assert params == ["active", "pending"]

    def test_explain_query(self):
        """Test building EXPLAIN query"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            limiting=LimitProjection(10),
        )

        builder = PostgresProjectionBuilder("users")
        explain_sql, params = builder.explain(query)

        assert explain_sql.startswith("EXPLAIN (ANALYZE, BUFFERS)")
        assert "SELECT name FROM users LIMIT 10" in explain_sql
        assert params == []

    def test_build_query_without_projection_uses_select_star(self):
        """Test building query without projection uses SELECT * (line 138)"""
        query = QueryProjection(
            projection=None,
        )

        builder = PostgresProjectionBuilder("users")
        sql, params = builder.build(query)

        assert "SELECT *" in sql
        assert "FROM users" in sql
        assert params == []
