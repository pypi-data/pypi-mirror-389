import pytest
from fractal_specifications.generic.operators import EqualsSpecification

from fractal_projections import (
    AggregateFunction,
    AggregateProjection,
    ElasticsearchProjectionBuilder,
    FieldProjection,
    GroupingProjection,
    LimitProjection,
    OrderingList,
    OrderingProjection,
    ProjectionList,
    QueryProjection,
)


class TestElasticsearchBuilder:
    """Integration tests for ElasticsearchProjectionBuilder"""

    def test_build_without_index_name_raises_error(self):
        """Test that build() raises error if no index name provided"""
        builder = ElasticsearchProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="collection_name is required"):
            builder.build(query)

    def test_build_count_without_index_name_raises_error(self):
        """Test that build_count() raises error if no index name provided"""
        builder = ElasticsearchProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="collection_name is required"):
            builder.build_count(query)

    def test_build_simple_query(self):
        """Test building simple ES query"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("email"),
                ]
            )
        )

        builder = ElasticsearchProjectionBuilder("users")
        es_query = builder.build(query)

        assert isinstance(es_query, dict)
        assert "_source" in es_query
        assert "name" in es_query["_source"]

    def test_build_query_with_filter(self):
        """Test building ES query with filter"""
        query = QueryProjection(
            filter=EqualsSpecification("status", "active"),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = ElasticsearchProjectionBuilder("users")
        es_query = builder.build(query)

        assert "query" in es_query

    def test_build_count_query(self):
        """Test building ES count query"""
        query = QueryProjection()

        builder = ElasticsearchProjectionBuilder("users")
        es_query = builder.build_count(query)

        assert isinstance(es_query, dict)

    def test_build_count_with_filter(self):
        """Test building ES count query with filter"""
        query = QueryProjection(filter=EqualsSpecification("status", "active"))

        builder = ElasticsearchProjectionBuilder("users")
        es_query = builder.build_count(query)

        assert "query" in es_query

    def test_build_query_with_limit_no_projection(self):
        """Test building query with limit but no projection (lines 122-126)"""
        query = QueryProjection(limiting=LimitProjection(10, offset=5))

        builder = ElasticsearchProjectionBuilder("users")
        es_query = builder.build(query)

        assert es_query["size"] == 10
        assert es_query["from"] == 5

    def test_build_query_with_limit_and_projection(self):
        """Test building query with limit and field projection (lines 147-149)"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            limiting=LimitProjection(20, offset=10),
        )

        builder = ElasticsearchProjectionBuilder("users")
        es_query = builder.build(query)

        assert es_query["size"] == 20
        assert es_query["from"] == 10
        assert "_source" in es_query

    def test_build_query_with_ordering(self):
        """Test building query with ordering (line 153)"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            ordering=OrderingList(
                [
                    OrderingProjection("created_at", ascending=False),
                    OrderingProjection("name", ascending=True),
                ]
            ),
        )

        builder = ElasticsearchProjectionBuilder("users")
        es_query = builder.build(query)

        assert "sort" in es_query
        assert len(es_query["sort"]) == 2
        assert es_query["sort"][0] == {"created_at": {"order": "desc"}}
        assert es_query["sort"][1] == {"name": {"order": "asc"}}

    def test_build_query_with_aggregation_no_grouping(self):
        """Test building query with aggregations but no grouping (lines 131-132, 193-205)"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    AggregateProjection(
                        AggregateFunction.COUNT, field="id", alias="total"
                    ),
                    AggregateProjection(
                        AggregateFunction.SUM, field="amount", alias="total_amount"
                    ),
                ]
            )
        )

        builder = ElasticsearchProjectionBuilder("users")
        es_query = builder.build(query)

        assert es_query["size"] == 0  # No documents, just aggregations
        assert "aggs" in es_query
        assert "total" in es_query["aggs"]
        assert "total_amount" in es_query["aggs"]

    def test_build_query_with_aggregation_and_grouping(self):
        """Test building query with aggregations and grouping (lines 164-191)"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    AggregateProjection(
                        AggregateFunction.COUNT, field="id", alias="count"
                    ),
                    AggregateProjection(
                        AggregateFunction.AVG, field="amount", alias="avg_amount"
                    ),
                ]
            ),
            grouping=GroupingProjection(["department"]),
        )

        builder = ElasticsearchProjectionBuilder("users")
        es_query = builder.build(query)

        assert es_query["size"] == 0
        assert "aggs" in es_query
        assert "grouped_by_department" in es_query["aggs"]

        # Check terms aggregation
        group_agg = es_query["aggs"]["grouped_by_department"]
        assert "terms" in group_agg
        assert group_agg["terms"]["field"] == "department"

        # Check sub-aggregations
        assert "aggs" in group_agg
        assert "count" in group_agg["aggs"]
        assert "avg_amount" in group_agg["aggs"]

    def test_build_metric_aggregation_count(self):
        """Test COUNT aggregation (lines 211-216)"""
        agg_proj = AggregateProjection(AggregateFunction.COUNT, field="id")
        result = ElasticsearchProjectionBuilder._build_metric_aggregation(agg_proj)

        assert "value_count" in result
        assert result["value_count"]["field"] == "id"

    def test_build_metric_aggregation_count_no_field(self):
        """Test COUNT(*) aggregation (lines 211-216)"""
        agg_proj = AggregateProjection(AggregateFunction.COUNT)
        result = ElasticsearchProjectionBuilder._build_metric_aggregation(agg_proj)

        assert "value_count" in result
        assert result["value_count"]["field"] == "_id"

    def test_build_metric_aggregation_count_distinct(self):
        """Test COUNT DISTINCT aggregation (lines 218-219)"""
        agg_proj = AggregateProjection(
            AggregateFunction.COUNT_DISTINCT, field="user_id"
        )
        result = ElasticsearchProjectionBuilder._build_metric_aggregation(agg_proj)

        assert "cardinality" in result
        assert result["cardinality"]["field"] == "user_id"

    def test_build_metric_aggregation_sum(self):
        """Test SUM aggregation (lines 221-222)"""
        agg_proj = AggregateProjection(AggregateFunction.SUM, field="amount")
        result = ElasticsearchProjectionBuilder._build_metric_aggregation(agg_proj)

        assert "sum" in result
        assert result["sum"]["field"] == "amount"

    def test_build_metric_aggregation_avg(self):
        """Test AVG aggregation (lines 224-225)"""
        agg_proj = AggregateProjection(AggregateFunction.AVG, field="price")
        result = ElasticsearchProjectionBuilder._build_metric_aggregation(agg_proj)

        assert "avg" in result
        assert result["avg"]["field"] == "price"

    def test_build_metric_aggregation_min(self):
        """Test MIN aggregation (lines 227-228)"""
        agg_proj = AggregateProjection(AggregateFunction.MIN, field="created_at")
        result = ElasticsearchProjectionBuilder._build_metric_aggregation(agg_proj)

        assert "min" in result
        assert result["min"]["field"] == "created_at"

    def test_build_metric_aggregation_max(self):
        """Test MAX aggregation (lines 230-231)"""
        agg_proj = AggregateProjection(AggregateFunction.MAX, field="updated_at")
        result = ElasticsearchProjectionBuilder._build_metric_aggregation(agg_proj)

        assert "max" in result
        assert result["max"]["field"] == "updated_at"

    def test_build_sort(self):
        """Test _build_sort method (lines 238-246)"""
        ordering = OrderingList(
            [
                OrderingProjection("timestamp", ascending=False),
                OrderingProjection("id", ascending=True),
            ]
        )

        result = ElasticsearchProjectionBuilder._build_sort(ordering)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == {"timestamp": {"order": "desc"}}
        assert result[1] == {"id": {"order": "asc"}}

    def test_build_search_after_query(self):
        """Test build_search_after_query method (lines 260-267)"""
        projection = ProjectionList([FieldProjection("name")])
        search_after_values = [1234567890, "user_123"]
        ordering = OrderingList([OrderingProjection("timestamp", ascending=False)])
        limiting = LimitProjection(10)

        result = ElasticsearchProjectionBuilder.build_search_after_query(
            projection, search_after_values, ordering, limiting
        )

        assert "search_after" in result
        assert result["search_after"] == search_after_values
        assert "sort" in result
        assert result["size"] == 10

    def test_build_search_after_query_without_values(self):
        """Test build_search_after_query without search_after values"""
        projection = ProjectionList([FieldProjection("name")])

        result = ElasticsearchProjectionBuilder.build_search_after_query(
            projection, None, None, None
        )

        assert "search_after" not in result

    def test_aggregation_without_sub_aggs(self):
        """Test aggregation grouping without any sub-aggregations"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("department")]),
            grouping=GroupingProjection(["department"]),
        )

        builder = ElasticsearchProjectionBuilder("users")
        es_query = builder.build(query)

        # Should still create the terms aggregation but no sub-aggs
        assert "aggs" in es_query
        group_agg = es_query["aggs"]["grouped_by_department"]
        # Sub-aggs should not be added if there are no aggregate projections
        assert "aggs" not in group_agg or len(group_agg.get("aggs", {})) == 0

    def test_build_metric_aggregation_unknown_function(self):
        """Test _build_metric_aggregation with unknown function (line 233)"""
        # Create a mock aggregate projection with a non-standard function
        # This covers the default case that returns empty dict
        from unittest.mock import Mock

        agg_proj = Mock()
        agg_proj.function = Mock()
        agg_proj.function.value = "UNKNOWN_FUNCTION"
        agg_proj.field = "test_field"

        result = ElasticsearchProjectionBuilder._build_metric_aggregation(agg_proj)

        # Should return empty dict for unknown functions
        assert result == {}
