from unittest.mock import MagicMock, Mock

import pytest
from fractal_specifications.generic.operators import EqualsSpecification

from fractal_projections import (
    AggregateFunction,
    AggregateProjection,
    DjangoProjectionBuilder,
    FieldProjection,
    GroupingProjection,
    LimitProjection,
    OrderingList,
    OrderingProjection,
    ProjectionList,
    QueryProjection,
)


class TestDjangoBuilder:
    """Integration tests for DjangoProjectionBuilder"""

    def test_build_without_model_class_raises_error(self):
        """Test that build() raises error if no model class provided"""
        builder = DjangoProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="model_class is required"):
            builder.build(query)

    def test_build_count_without_model_class_raises_error(self):
        """Test that build_count() raises error if no model class provided"""
        builder = DjangoProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="model_class is required"):
            builder.build_count(query)

    def test_explain_without_model_class_raises_error(self):
        """Test that explain() raises error if no model class provided"""
        builder = DjangoProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="model_class is required"):
            builder.explain(query)

    def test_build_simple_query_no_filter(self):
        """Test building a simple query without filter"""
        # Create mock model
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset

        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("id"),
                    FieldProjection("name"),
                ]
            )
        )

        builder = DjangoProjectionBuilder(mock_model)
        _queryset = builder.build(query)

        # Verify build returns tuple
        assert _queryset is not None

        # Verify queryset.values was called with correct fields
        mock_queryset.values.assert_called_once_with("id", "name")

    def test_build_query_with_filter(self):
        """Test building query with WHERE clause"""
        # Create mock model
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset

        query = QueryProjection(
            filter=EqualsSpecification("status", "active"),
            projection=ProjectionList(
                [
                    FieldProjection("id"),
                    FieldProjection("name"),
                ]
            ),
        )

        builder = DjangoProjectionBuilder(mock_model)
        _queryset = builder.build(query)

        # Verify filter was called
        mock_queryset.filter.assert_called_once()
        # Verify values was called with correct fields
        mock_queryset.values.assert_called_once_with("id", "name")

    def test_build_query_with_ordering(self):
        """Test building query with ORDER BY"""
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset

        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            ordering=OrderingList([OrderingProjection("created_at", ascending=False)]),
        )

        builder = DjangoProjectionBuilder(mock_model)
        _queryset = builder.build(query)

        # Verify order_by was called with descending field
        mock_queryset.order_by.assert_called_once_with("-created_at")

    def test_build_query_with_ascending_ordering(self):
        """Test building query with ascending ORDER BY"""
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset

        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            ordering=OrderingList([OrderingProjection("name", ascending=True)]),
        )

        builder = DjangoProjectionBuilder(mock_model)
        _queryset = builder.build(query)

        # Verify order_by was called with ascending field (no minus)
        mock_queryset.order_by.assert_called_once_with("name")

    def test_build_query_with_limit(self):
        """Test building query with LIMIT"""
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset
        # Mock slicing behavior
        mock_queryset.__getitem__ = Mock(return_value=mock_queryset)

        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            limiting=LimitProjection(10),
        )

        builder = DjangoProjectionBuilder(mock_model)
        _queryset = builder.build(query)

        # Verify slicing was attempted
        mock_queryset.__getitem__.assert_called_once()

    def test_build_query_with_limit_and_offset(self):
        """Test building query with LIMIT and OFFSET"""
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.__getitem__ = Mock(return_value=mock_queryset)

        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            limiting=LimitProjection(10, offset=5),
        )

        builder = DjangoProjectionBuilder(mock_model)
        _queryset = builder.build(query)

        # Verify slicing was used
        mock_queryset.__getitem__.assert_called_once()

    def test_build_query_with_grouping(self):
        """Test building query with GROUP BY"""
        mock_model = Mock()
        mock_model.__name__ = "Employee"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.annotate.return_value = mock_queryset

        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("department"),
                    AggregateProjection(AggregateFunction.COUNT, alias="count"),
                ]
            ),
            grouping=GroupingProjection(["department"]),
        )

        builder = DjangoProjectionBuilder(mock_model)
        _queryset = builder.build(query)

        # Verify values was called with grouping fields
        mock_queryset.values.assert_called_once_with("department")
        # Verify annotate was called
        mock_queryset.annotate.assert_called_once()

    def test_build_count_simple(self):
        """Test building COUNT query"""
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset

        query = QueryProjection()

        builder = DjangoProjectionBuilder(mock_model)
        _queryset = builder.build_count(query)

        assert _queryset is not None
        # Verify we got the base queryset
        mock_model.objects.all.assert_called_once()

    def test_build_count_with_filter(self):
        """Test building COUNT query with WHERE clause"""
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset

        query = QueryProjection(filter=EqualsSpecification("status", "active"))

        builder = DjangoProjectionBuilder(mock_model)
        _queryset = builder.build_count(query)

        # Verify filter was called
        mock_queryset.filter.assert_called_once()

    def test_explain_query(self):
        """Test building EXPLAIN query"""
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.explain.return_value = "QUERY PLAN: SELECT * FROM users"

        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = DjangoProjectionBuilder(mock_model)
        explanation = builder.explain(query)

        assert explanation == "QUERY PLAN: SELECT * FROM users"
        # Verify explain was called
        mock_queryset.explain.assert_called_once()

    def test_init_with_model_class(self):
        """Test initialization with model class"""
        mock_model = Mock()
        mock_model.__name__ = "User"

        builder = DjangoProjectionBuilder(mock_model)

        assert builder.model_class == mock_model
        assert builder.collection_name == "User"

    def test_build_aggregate_count_star(self):
        """Test building COUNT(*) aggregate"""
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset

        query = QueryProjection(
            projection=ProjectionList(
                [AggregateProjection(AggregateFunction.COUNT, field="*", alias="total")]
            ),
        )

        builder = DjangoProjectionBuilder(mock_model)
        _queryset = builder.build(query)

        # Verify annotate was called twice (once for _group, once for aggregation)
        assert mock_queryset.annotate.call_count == 2

    def test_build_aggregate_sum(self):
        """Test building SUM aggregate"""
        mock_model = Mock()
        mock_model.__name__ = "Order"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset

        query = QueryProjection(
            projection=ProjectionList(
                [
                    AggregateProjection(
                        AggregateFunction.SUM, field="amount", alias="total_amount"
                    )
                ]
            ),
        )

        builder = DjangoProjectionBuilder(mock_model)
        _queryset = builder.build(query)

        # Verify annotate was called twice (once for _group, once for aggregation)
        assert mock_queryset.annotate.call_count == 2

    def test_build_with_multiple_orderings(self):
        """Test building query with multiple ORDER BY fields"""
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset

        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            ordering=OrderingList(
                [
                    OrderingProjection("created_at", ascending=False),
                    OrderingProjection("name", ascending=True),
                ]
            ),
        )

        builder = DjangoProjectionBuilder(mock_model)
        _queryset = builder.build(query)

        # Verify order_by was called with both fields
        mock_queryset.order_by.assert_called_once_with("-created_at", "name")

    def test_build_with_mixed_fields_and_aggregates(self):
        """Test building query with both simple fields and aggregates (line 188)"""
        mock_model = Mock()
        mock_model.__name__ = "Order"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.annotate.return_value = mock_queryset

        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("product"),
                    AggregateProjection(
                        AggregateFunction.SUM, field="amount", alias="total"
                    ),
                ]
            ),
        )

        builder = DjangoProjectionBuilder(mock_model)
        _queryset = builder.build(query)

        # Verify values was called with the field
        mock_queryset.values.assert_called()
        mock_queryset.annotate.assert_called()

    def test_build_without_limiting(self):
        """Test building query without limiting (line 268)"""
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset

        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            limiting=None,
        )

        builder = DjangoProjectionBuilder(mock_model)
        queryset = builder.build(query)

        # Just verify it doesn't error
        assert queryset is not None

    def test_build_without_ordering(self):
        """Test building query without ordering (line 239)"""
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset

        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            ordering=None,
        )

        builder = DjangoProjectionBuilder(mock_model)
        queryset = builder.build(query)

        # Verify order_by was not called
        mock_queryset.order_by.assert_not_called()
