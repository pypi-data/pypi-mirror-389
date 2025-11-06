from unittest.mock import MagicMock

from fractal_projections.mixins.mongo import MongoProjectionsMixin
from fractal_projections.projections.fields import FieldProjection, ProjectionList
from fractal_projections.projections.query import QueryProjection


class MockMongoRepository(MongoProjectionsMixin):
    """Mock repository for testing MongoProjectionsMixin"""

    def __init__(self, collection):
        self.collection = collection


class TestMongoProjectionsMixin:
    """Tests for MongoProjectionsMixin"""

    def test_find_with_projection(self):
        """Test find_with_projection returns projected results"""
        # Create mock collection
        mock_collection = MagicMock()

        # Mock aggregate results
        mock_results = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        mock_collection.aggregate.return_value = iter(mock_results)

        # Create repository and query
        repo = MockMongoRepository(mock_collection)
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

        # Verify aggregate was called
        mock_collection.aggregate.assert_called_once()

    def test_count_with_projection(self):
        """Test count_with_projection returns count"""
        # Create mock collection
        mock_collection = MagicMock()

        # Mock aggregate count result
        mock_collection.aggregate.return_value = [{"count": 42}]

        # Create repository and query
        repo = MockMongoRepository(mock_collection)
        query = QueryProjection()

        # Execute count
        count = repo.count_with_projection(query)

        # Verify count
        assert count == 42
        mock_collection.aggregate.assert_called_once()

    def test_count_with_projection_empty_result(self):
        """Test count_with_projection when result is empty"""
        # Create mock collection
        mock_collection = MagicMock()

        # Mock empty aggregate result
        mock_collection.aggregate.return_value = []

        # Create repository and query
        repo = MockMongoRepository(mock_collection)
        query = QueryProjection()

        # Execute count
        count = repo.count_with_projection(query)

        # Verify count is 0
        assert count == 0

    def test_count_with_projection_no_count_field(self):
        """Test count_with_projection when result has no count field"""
        # Create mock collection
        mock_collection = MagicMock()

        # Mock aggregate result without count field
        mock_collection.aggregate.return_value = [{"other_field": "value"}]

        # Create repository and query
        repo = MockMongoRepository(mock_collection)
        query = QueryProjection()

        # Execute count
        count = repo.count_with_projection(query)

        # Verify count is 0
        assert count == 0

    def test_count_with_projection_and_filter(self):
        """Test count_with_projection with filter"""
        # Create mock collection
        mock_collection = MagicMock()

        # Mock aggregate count result
        mock_collection.aggregate.return_value = [{"count": 10}]

        # Create repository and query with filter
        from fractal_specifications.generic.operators import EqualsSpecification

        repo = MockMongoRepository(mock_collection)
        query = QueryProjection(filter=EqualsSpecification("status", "active"))

        # Execute count
        count = repo.count_with_projection(query)

        # Verify count
        assert count == 10
        mock_collection.aggregate.assert_called_once()

    def test_explain_query(self):
        """Test explain_query returns explanation"""
        # Create mock collection
        mock_collection = MagicMock()

        # Mock aggregate explain result
        explain_result = {"stages": [{"$match": {"status": "active"}}]}
        mock_collection.aggregate.return_value = explain_result

        # Create repository and query
        repo = MockMongoRepository(mock_collection)
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
        assert "stages" in explanation[0]
        mock_collection.aggregate.assert_called_once()

    def test_find_with_projection_empty_results(self):
        """Test find_with_projection with no results"""
        # Create mock collection
        mock_collection = MagicMock()

        # Mock empty aggregate results
        mock_collection.aggregate.return_value = iter([])

        # Create repository and query
        repo = MockMongoRepository(mock_collection)
        query = QueryProjection(projection=ProjectionList([FieldProjection("id")]))

        # Execute query
        results = list(repo.find_with_projection(query))

        # Verify empty results
        assert len(results) == 0
