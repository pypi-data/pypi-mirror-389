from unittest.mock import MagicMock

from fractal_projections.mixins.firestore import FirestoreProjectionsMixin
from fractal_projections.projections.fields import FieldProjection, ProjectionList
from fractal_projections.projections.limiting import LimitProjection
from fractal_projections.projections.ordering import OrderingList, OrderingProjection
from fractal_projections.projections.query import QueryProjection


class MockFirestoreRepository(FirestoreProjectionsMixin):
    """Mock repository for testing FirestoreProjectionsMixin"""

    def __init__(self, collection):
        self.collection = collection

    @staticmethod
    def _get_collection_stream(collection):
        return collection.stream()


class TestFirestoreProjectionsMixin:
    """Tests for FirestoreProjectionsMixin"""

    def test_find_with_projection(self):
        """Test find_with_projection returns projected results"""
        # Create mock collection and documents
        mock_collection = MagicMock()

        # Mock documents
        mock_doc1 = MagicMock()
        mock_doc1.to_dict.return_value = {"id": 1, "name": "Alice"}
        mock_doc2 = MagicMock()
        mock_doc2.to_dict.return_value = {"id": 2, "name": "Bob"}

        # Mock stream
        mock_collection.stream.return_value = iter([mock_doc1, mock_doc2])

        # Create repository and query
        repo = MockFirestoreRepository(mock_collection)
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

    def test_find_with_projection_with_filter(self):
        """Test find_with_projection with filter"""
        from fractal_specifications.generic.operators import EqualsSpecification
        from google.cloud.firestore_v1 import FieldFilter

        # Create mock collection
        mock_collection = MagicMock()
        mock_filtered_collection = MagicMock()

        # Mock where to return filtered collection
        mock_collection.where.return_value = mock_filtered_collection

        # Mock document
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {"id": 1, "name": "Alice", "status": "active"}

        # Mock stream
        mock_filtered_collection.stream.return_value = iter([mock_doc])

        # Create repository and query with filter
        repo = MockFirestoreRepository(mock_collection)
        query = QueryProjection(
            filter=EqualsSpecification("status", "active"),
            projection=ProjectionList([FieldProjection("id"), FieldProjection("name")]),
        )

        # Execute query
        results = list(repo.find_with_projection(query))

        # Verify results
        assert len(results) == 1
        assert results[0]["status"] == "active"

        # Verify where was called with FieldFilter
        mock_collection.where.assert_called_once()
        call_args = mock_collection.where.call_args
        assert "filter" in call_args.kwargs
        # The filter should be a FieldFilter with the spec converted to (field, operator, value)
        assert isinstance(call_args.kwargs["filter"], FieldFilter)

    def test_find_with_projection_with_ordering(self):
        """Test find_with_projection with ordering"""
        # Create mock collection
        mock_collection = MagicMock()
        mock_ordered_collection = MagicMock()

        # Mock order_by to return ordered collection
        mock_collection.order_by.return_value = mock_ordered_collection

        # Mock document
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {"id": 1, "name": "Alice"}

        # Mock stream
        mock_ordered_collection.stream.return_value = iter([mock_doc])

        # Create repository and query with ordering
        repo = MockFirestoreRepository(mock_collection)
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("id")]),
            ordering=OrderingList([OrderingProjection("created_at", ascending=False)]),
        )

        # Execute query
        results = list(repo.find_with_projection(query))

        # Verify results
        assert len(results) == 1

        # Verify order_by was called
        mock_collection.order_by.assert_called_once()

    def test_find_with_projection_with_limit(self):
        """Test find_with_projection with limit"""
        # Create mock collection
        mock_collection = MagicMock()
        mock_limited_collection = MagicMock()

        # Mock limit to return limited collection
        mock_collection.limit.return_value = mock_limited_collection

        # Mock document
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {"id": 1, "name": "Alice"}

        # Mock stream
        mock_limited_collection.stream.return_value = iter([mock_doc])

        # Create repository and query with limit
        repo = MockFirestoreRepository(mock_collection)
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("id")]),
            limiting=LimitProjection(10),
        )

        # Execute query
        results = list(repo.find_with_projection(query))

        # Verify results
        assert len(results) == 1

        # Verify limit was called
        mock_collection.limit.assert_called_once_with(10)

    def test_count_with_projection(self):
        """Test count_with_projection returns count"""
        # Create mock collection and count query
        mock_collection = MagicMock()
        mock_count_query = MagicMock()

        # Mock count
        mock_collection.count.return_value = mock_count_query

        # Mock count result
        mock_count_result = MagicMock()
        mock_count_result.value = 42
        mock_count_query.get.return_value = [[mock_count_result]]

        # Create repository and query
        repo = MockFirestoreRepository(mock_collection)
        query = QueryProjection()

        # Execute count
        count = repo.count_with_projection(query)

        # Verify count
        assert count == 42
        mock_collection.count.assert_called_once()

    def test_count_with_projection_empty_result(self):
        """Test count_with_projection when result is empty"""
        # Create mock collection and count query
        mock_collection = MagicMock()
        mock_count_query = MagicMock()

        # Mock count
        mock_collection.count.return_value = mock_count_query

        # Mock empty result
        mock_count_query.get.return_value = None

        # Create repository and query
        repo = MockFirestoreRepository(mock_collection)
        query = QueryProjection()

        # Execute count
        count = repo.count_with_projection(query)

        # Verify count is 0
        assert count == 0

    def test_count_with_projection_with_filter(self):
        """Test count_with_projection with filter"""
        from fractal_specifications.generic.operators import EqualsSpecification
        from google.cloud.firestore_v1 import FieldFilter

        # Create mock collection and filtered collection
        mock_collection = MagicMock()
        mock_filtered_collection = MagicMock()
        mock_count_query = MagicMock()

        # Mock where to return filtered collection
        mock_collection.where.return_value = mock_filtered_collection

        # Mock count on the filtered collection
        mock_filtered_collection.count.return_value = mock_count_query

        # Mock count result
        mock_count_result = MagicMock()
        mock_count_result.value = 15
        mock_count_query.get.return_value = [[mock_count_result]]

        # Create repository and query with filter
        repo = MockFirestoreRepository(mock_collection)
        query = QueryProjection(filter=EqualsSpecification("status", "active"))

        # Execute count
        count = repo.count_with_projection(query)

        # Verify count
        assert count == 15

        # Verify where was called with FieldFilter
        mock_collection.where.assert_called_once()
        call_args = mock_collection.where.call_args
        assert "filter" in call_args.kwargs
        assert isinstance(call_args.kwargs["filter"], FieldFilter)

        # Verify count was called on the filtered collection
        mock_filtered_collection.count.assert_called_once()

    def test_explain_query(self):
        """Test explain_query returns query configuration"""
        # Create mock collection
        mock_collection = MagicMock()

        # Create repository and query
        repo = MockFirestoreRepository(mock_collection)
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

        # Verify explanation (should be a list with stringified query config)
        assert isinstance(explanation, list)
        assert len(explanation) == 1
        assert isinstance(explanation[0], str)

    def test_find_with_projection_empty_results(self):
        """Test find_with_projection with no results"""
        # Create mock collection
        mock_collection = MagicMock()

        # Mock empty stream
        mock_collection.stream.return_value = iter([])

        # Create repository and query
        repo = MockFirestoreRepository(mock_collection)
        query = QueryProjection(projection=ProjectionList([FieldProjection("id")]))

        # Execute query
        results = list(repo.find_with_projection(query))

        # Verify empty results
        assert len(results) == 0
