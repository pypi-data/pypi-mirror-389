from fractal_specifications.generic.operators import EqualsSpecification

from fractal_projections import (
    AggregateFunction,
    AggregateProjection,
    FieldProjection,
    FirestoreProjectionBuilder,
    GroupingProjection,
    LimitProjection,
    OrderingList,
    OrderingProjection,
    ProjectionList,
    QueryProjection,
)


class TestFirestoreBuilder:
    """Integration tests for FirestoreProjectionBuilder"""

    def test_build_without_collection_name_works(self):
        """Test that build() works without collection name (configs are collection-agnostic)"""
        builder = FirestoreProjectionBuilder()
        query = QueryProjection()

        # Should not raise error - configs don't require collection name
        config = builder.build(query)
        assert isinstance(config, dict)

    def test_build_count_without_collection_name_works(self):
        """Test that build_count() works without collection name (configs are collection-agnostic)"""
        builder = FirestoreProjectionBuilder()
        query = QueryProjection()

        # Should not raise error - configs don't require collection name
        config = builder.build_count(query)
        assert isinstance(config, dict)
        assert config.get("use_count_aggregation") is True

    def test_build_simple_config(self):
        """Test building simple query config"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("email"),
                ]
            )
        )

        builder = FirestoreProjectionBuilder("users")
        config = builder.build(query)

        assert isinstance(config, dict)
        assert "select_fields" in config
        assert "name" in config["select_fields"]

    def test_build_config_with_filter(self):
        """Test building config with filter"""
        query = QueryProjection(
            filter=EqualsSpecification("status", "active"),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = FirestoreProjectionBuilder("users")
        config = builder.build(query)

        assert "where_clauses" in config

    def test_build_count_config(self):
        """Test building count config"""
        query = QueryProjection()

        builder = FirestoreProjectionBuilder("users")
        config = builder.build_count(query)

        assert config["use_count_aggregation"] is True
        assert config["server_side_only"] is True

    def test_build_count_with_filter(self):
        """Test building count query with filter (lines 99-101)"""
        query = QueryProjection(filter=EqualsSpecification("status", "active"))

        builder = FirestoreProjectionBuilder("users")
        config = builder.build_count(query)

        assert "where_clauses" in config
        assert config.get("use_count_aggregation") is True

    def test_build_with_grouping(self):
        """Test building query with grouping (lines 79-80)"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("department")]),
            grouping=GroupingProjection(["department"]),
        )

        builder = FirestoreProjectionBuilder("users")
        config = builder.build(query)

        assert config.get("client_side_processing") is True
        assert "grouping" in config
        assert config["grouping"] == ["department"]

    def test_build_query_config_with_aggregates(self):
        """Test build_query_config with aggregates (lines 125-137)"""
        projection = ProjectionList(
            [
                AggregateProjection(AggregateFunction.COUNT, alias="total"),
            ]
        )

        config = FirestoreProjectionBuilder.build_query_config(projection)

        assert config.get("count_only") is True

    def test_build_query_config_with_count_field(self):
        """Test COUNT(field) requiring field filtering"""
        projection = ProjectionList(
            [
                AggregateProjection(
                    AggregateFunction.COUNT, field="user_id", alias="user_count"
                ),
            ]
        )

        config = FirestoreProjectionBuilder.build_query_config(projection)

        assert config.get("count_only") is True
        assert config.get("count_field") == "user_id"

    def test_build_query_config_with_non_count_aggregate(self):
        """Test non-COUNT aggregates requiring client-side processing (lines 134-137)"""
        projection = ProjectionList(
            [
                AggregateProjection(
                    AggregateFunction.SUM, field="amount", alias="total_amount"
                ),
            ]
        )

        config = FirestoreProjectionBuilder.build_query_config(projection)

        assert config.get("client_side_aggregation") is True

    def test_build_query_config_with_distinct(self):
        """Test DISTINCT handling (lines 146-147)"""
        projection = ProjectionList([FieldProjection("email")], distinct=True)

        config = FirestoreProjectionBuilder.build_query_config(projection)

        assert config.get("distinct") is True
        assert config.get("client_side_processing") is True

    def test_build_query_config_empty_projection(self):
        """Test empty projection (line 117)"""
        projection = ProjectionList([])

        config = FirestoreProjectionBuilder.build_query_config(projection)

        assert config == {}

    def test_build_query_config_none_projection(self):
        """Test None projection (line 117)"""
        config = FirestoreProjectionBuilder.build_query_config(None)

        assert config == {}

    def test_build_order_constraints(self):
        """Test building order constraints (line 155)"""
        ordering = OrderingList(
            [
                OrderingProjection("created_at", ascending=False),
                OrderingProjection("name", ascending=True),
            ]
        )

        result = FirestoreProjectionBuilder.build_order_constraints(ordering)

        assert len(result) == 2
        assert result[0] == {"field": "created_at", "direction": "DESCENDING"}
        assert result[1] == {"field": "name", "direction": "ASCENDING"}

    def test_build_limit_constraint_with_offset(self):
        """Test limit constraint with offset (line 173)"""
        limit = LimitProjection(10, offset=5)

        result = FirestoreProjectionBuilder.build_limit_constraint(limit)

        assert result["limit"] == 10
        assert result["offset"] == 5

    def test_build_limit_constraint_without_offset(self):
        """Test limit constraint without offset"""
        limit = LimitProjection(20)

        result = FirestoreProjectionBuilder.build_limit_constraint(limit)

        assert result["limit"] == 20
        assert "offset" not in result

    def test_requires_client_processing_with_distinct(self):
        """Test requires_client_processing with DISTINCT (lines 185-190)"""
        projection = ProjectionList([FieldProjection("email")], distinct=True)

        result = FirestoreProjectionBuilder.requires_client_processing(projection)

        assert result is True

    def test_requires_client_processing_with_non_count_aggregate(self):
        """Test requires_client_processing with non-COUNT aggregate (lines 193-200)"""
        projection = ProjectionList(
            [
                AggregateProjection(AggregateFunction.SUM, field="amount"),
            ]
        )

        result = FirestoreProjectionBuilder.requires_client_processing(projection)

        assert result is True

    def test_requires_client_processing_with_count(self):
        """Test COUNT doesn't require client processing"""
        projection = ProjectionList(
            [
                AggregateProjection(AggregateFunction.COUNT, field="id"),
            ]
        )

        result = FirestoreProjectionBuilder.requires_client_processing(projection)

        assert result is False

    def test_requires_client_processing_with_count_distinct(self):
        """Test COUNT DISTINCT requires client processing (lines 198-200)"""
        projection = ProjectionList(
            [
                AggregateProjection(AggregateFunction.COUNT_DISTINCT, field="user_id"),
            ]
        )

        result = FirestoreProjectionBuilder.requires_client_processing(projection)

        assert result is True

    def test_requires_client_processing_none_projection(self):
        """Test requires_client_processing with None projection"""
        result = FirestoreProjectionBuilder.requires_client_processing(None)

        assert result is False

    def test_requires_client_processing_simple_fields(self):
        """Test simple field selection doesn't require client processing"""
        projection = ProjectionList(
            [
                FieldProjection("name"),
                FieldProjection("email"),
            ]
        )

        result = FirestoreProjectionBuilder.requires_client_processing(projection)

        assert result is False

    def test_can_use_native_operations_with_grouping(self):
        """Test can_use_native_operations with grouping (lines 223-225)"""
        projection = ProjectionList([FieldProjection("name")])
        grouping = GroupingProjection(["department"])

        result = FirestoreProjectionBuilder.can_use_native_operations(
            projection, grouping
        )

        assert result is False

    def test_can_use_native_operations_with_complex_projection(self):
        """Test can_use_native_operations with complex projection (lines 227-229)"""
        projection = ProjectionList(
            [
                AggregateProjection(AggregateFunction.SUM, field="amount"),
            ]
        )

        result = FirestoreProjectionBuilder.can_use_native_operations(projection)

        assert result is False

    def test_can_use_native_operations_with_simple_projection(self):
        """Test can_use_native_operations with simple projection (line 231)"""
        projection = ProjectionList(
            [
                FieldProjection("name"),
                FieldProjection("email"),
            ]
        )

        result = FirestoreProjectionBuilder.can_use_native_operations(projection)

        assert result is True

    def test_can_use_native_operations_with_count(self):
        """Test COUNT can use native operations"""
        projection = ProjectionList(
            [
                AggregateProjection(AggregateFunction.COUNT, field="id"),
            ]
        )

        result = FirestoreProjectionBuilder.can_use_native_operations(projection)

        assert result is True

    def test_build_with_ordering(self):
        """Test build() with ordering (line 71)"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            ordering=OrderingList([OrderingProjection("created_at", ascending=False)]),
        )

        builder = FirestoreProjectionBuilder("users")
        config = builder.build(query)

        assert "order_by" in config
        assert len(config["order_by"]) == 1

    def test_build_with_limiting(self):
        """Test build() with limiting (line 75)"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            limiting=LimitProjection(10, offset=5),
        )

        builder = FirestoreProjectionBuilder("users")
        config = builder.build(query)

        assert "limit" in config
        assert config["limit"] == 10
        assert config["offset"] == 5

    def test_build_order_constraints_with_empty_list(self):
        """Test build_order_constraints with empty ordering (line 155)"""
        result = FirestoreProjectionBuilder.build_order_constraints(None)

        assert result == []

    def test_requires_client_processing_avg_aggregate(self):
        """Test AVG aggregate requires client processing (line 199)"""
        projection = ProjectionList(
            [
                AggregateProjection(AggregateFunction.AVG, field="price"),
            ]
        )

        result = FirestoreProjectionBuilder.requires_client_processing(projection)

        assert result is True

    def test_requires_client_processing_count_distinct(self):
        """Test COUNT_DISTINCT aggregate requires client processing (line 207)"""
        projection = ProjectionList(
            [
                AggregateProjection(
                    AggregateFunction.COUNT_DISTINCT,
                    field="user_id",
                    alias="unique_users",
                ),
            ]
        )

        result = FirestoreProjectionBuilder.requires_client_processing(projection)

        assert result is True

    def test_build_with_list_filter(self):
        """Test building config when filter returns a list instead of tuple (line 66)"""
        from fractal_specifications.generic.collections import AndSpecification
        from fractal_specifications.generic.operators import (
            EqualsSpecification,
            GreaterThanSpecification,
        )

        query = QueryProjection(
            filter=AndSpecification(
                [
                    EqualsSpecification("status", "active"),
                    GreaterThanSpecification("age", 18),
                ]
            )
        )

        builder = FirestoreProjectionBuilder("users")
        config = builder.build(query)

        # Should have where_clauses as a list
        assert "where_clauses" in config
        assert isinstance(config["where_clauses"], list)

    def test_build_count_with_list_filter(self):
        """Test building count config when filter returns a list (line 109)"""
        from fractal_specifications.generic.collections import AndSpecification
        from fractal_specifications.generic.operators import (
            EqualsSpecification,
            GreaterThanSpecification,
        )

        query = QueryProjection(
            filter=AndSpecification(
                [
                    EqualsSpecification("status", "active"),
                    GreaterThanSpecification("age", 18),
                ]
            )
        )

        builder = FirestoreProjectionBuilder("users")
        config = builder.build_count(query)

        # Should have where_clauses as a list
        assert "where_clauses" in config
        assert isinstance(config["where_clauses"], list)
