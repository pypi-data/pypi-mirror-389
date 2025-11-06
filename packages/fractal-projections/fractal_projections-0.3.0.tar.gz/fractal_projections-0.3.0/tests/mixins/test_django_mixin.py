from unittest.mock import MagicMock, Mock

from fractal_projections import (
    DjangoProjectionsMixin,
    FieldProjection,
    ProjectionList,
    QueryProjection,
)


class MockDjangoRepository(DjangoProjectionsMixin):
    """Mock repository for testing DjangoProjectionsMixin"""

    def __init__(self, django_model):
        self.django_model = django_model


class TestDjangoProjectionsMixin:
    """Tests for DjangoProjectionsMixin"""

    def test_find_with_projection(self):
        """Test find_with_projection returns projected results"""
        # Create mock model
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset

        # Mock iteration over queryset
        mock_results = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        mock_queryset.__iter__ = Mock(return_value=iter(mock_results))

        # Create repository and query
        repo = MockDjangoRepository(mock_model)
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("id"),
                    FieldProjection("name"),
                ]
            )
        )

        # Execute query
        results = list(repo.find_with_projection(query))

        # Verify results
        assert len(results) == 2
        assert results[0] == {"id": 1, "name": "Alice"}
        assert results[1] == {"id": 2, "name": "Bob"}

        # Verify queryset methods were called
        mock_model.objects.all.assert_called_once()
        mock_queryset.values.assert_called_once_with("id", "name")

    def test_count_with_projection(self):
        """Test count_with_projection returns count"""
        # Create mock model
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.count.return_value = 42

        # Create repository and query
        repo = MockDjangoRepository(mock_model)
        query = QueryProjection()

        # Execute count
        count = repo.count_with_projection(query)

        # Verify count
        assert count == 42
        mock_queryset.count.assert_called_once()

    def test_count_with_projection_and_filter(self):
        """Test count_with_projection with filter"""
        # Create mock model
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.count.return_value = 10

        # Create repository and query with filter
        from fractal_specifications.generic.operators import EqualsSpecification

        repo = MockDjangoRepository(mock_model)
        query = QueryProjection(filter=EqualsSpecification("status", "active"))

        # Execute count
        count = repo.count_with_projection(query)

        # Verify count
        assert count == 10
        mock_queryset.filter.assert_called_once()
        mock_queryset.count.assert_called_once()

    def test_explain_query(self):
        """Test explain_query returns explanation"""
        # Create mock model
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.explain.return_value = "QUERY PLAN: SELECT id, name FROM users"

        # Create repository and query
        repo = MockDjangoRepository(mock_model)
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("id"),
                    FieldProjection("name"),
                ]
            )
        )

        # Execute explain
        explanation = repo.explain_query(query)

        # Verify explanation
        assert isinstance(explanation, list)
        assert len(explanation) == 1
        assert explanation[0] == "QUERY PLAN: SELECT id, name FROM users"
        mock_queryset.explain.assert_called_once()

    def test_find_with_projection_empty_results(self):
        """Test find_with_projection with no results"""
        # Create mock model
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset

        # Mock empty iteration
        mock_queryset.__iter__ = Mock(return_value=iter([]))

        # Create repository and query
        repo = MockDjangoRepository(mock_model)
        query = QueryProjection(projection=ProjectionList([FieldProjection("id")]))

        # Execute query
        results = list(repo.find_with_projection(query))

        # Verify empty results
        assert len(results) == 0

    def test_mixin_uses_builder_correctly(self):
        """Test that mixin properly initializes and uses DjangoProjectionBuilder"""
        # Create mock model
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_queryset = MagicMock()
        mock_model.objects.all.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.__iter__ = Mock(return_value=iter([]))

        # Create repository
        repo = MockDjangoRepository(mock_model)
        query = QueryProjection(projection=ProjectionList([FieldProjection("name")]))

        # Execute query
        list(repo.find_with_projection(query))

        # Verify the model was accessed
        mock_model.objects.all.assert_called()
