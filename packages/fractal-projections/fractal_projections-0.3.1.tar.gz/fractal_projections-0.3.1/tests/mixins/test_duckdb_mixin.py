from unittest.mock import MagicMock

from fractal_projections.mixins.duckdb import DuckDBProjectionsMixin
from fractal_projections.projections.fields import FieldProjection, ProjectionList
from fractal_projections.projections.query import QueryProjection


class MockDuckDBRepository(DuckDBProjectionsMixin):
    """Mock repository for testing DuckDBProjectionsMixin"""

    def __init__(self, table_name, connection):
        self.table_name = table_name
        self.connection = connection

    def _row_to_domain(self, row):
        return row


class TestDuckDBProjectionsMixin:
    """Tests for DuckDBProjectionsMixin"""

    def test_find_with_projection(self):
        """Test find_with_projection returns projected results"""
        # Create mock connection and result
        mock_conn = MagicMock()
        mock_result = MagicMock()

        # Mock execute to return result
        mock_conn.execute.return_value = mock_result

        # Mock description (column names)
        mock_result.description = [("id",), ("name",)]

        # Mock rows
        mock_result.fetchall.return_value = [(1, "Alice"), (2, "Bob")]

        # Create repository and query
        repo = MockDuckDBRepository("users", mock_conn)
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

        # Verify execute was called
        mock_conn.execute.assert_called_once()

    def test_count_with_projection(self):
        """Test count_with_projection returns count"""
        # Create mock connection and result
        mock_conn = MagicMock()
        mock_result = MagicMock()

        # Mock execute to return result
        mock_conn.execute.return_value = mock_result

        # Mock fetchone result
        mock_result.fetchone.return_value = (42,)

        # Create repository and query
        repo = MockDuckDBRepository("users", mock_conn)
        query = QueryProjection()

        # Execute count
        count = repo.count_with_projection(query)

        # Verify count
        assert count == 42
        mock_conn.execute.assert_called_once()
        mock_result.fetchone.assert_called_once()

    def test_count_with_projection_none_result(self):
        """Test count_with_projection when fetchone returns None"""
        # Create mock connection and result
        mock_conn = MagicMock()
        mock_result = MagicMock()

        # Mock execute to return result
        mock_conn.execute.return_value = mock_result

        # Mock fetchone returning None
        mock_result.fetchone.return_value = None

        # Create repository and query
        repo = MockDuckDBRepository("users", mock_conn)
        query = QueryProjection()

        # Execute count
        count = repo.count_with_projection(query)

        # Verify count is 0 when result is None
        assert count == 0

    def test_count_with_projection_and_filter(self):
        """Test count_with_projection with filter"""
        # Create mock connection and result
        mock_conn = MagicMock()
        mock_result = MagicMock()

        # Mock execute to return result
        mock_conn.execute.return_value = mock_result

        # Mock fetchone result
        mock_result.fetchone.return_value = (10,)

        # Create repository and query with filter
        from fractal_specifications.generic.operators import EqualsSpecification

        repo = MockDuckDBRepository("users", mock_conn)
        query = QueryProjection(filter=EqualsSpecification("status", "active"))

        # Execute count
        count = repo.count_with_projection(query)

        # Verify count
        assert count == 10
        mock_conn.execute.assert_called_once()

    def test_explain_query(self):
        """Test explain_query returns explanation"""
        # Create mock connection and result
        mock_conn = MagicMock()
        mock_result = MagicMock()

        # Mock execute to return result
        mock_conn.execute.return_value = mock_result

        # Mock fetchall result
        mock_result.fetchall.return_value = [
            ("QUERY PLAN",),
            ("Seq Scan on users",),
        ]

        # Create repository and query
        repo = MockDuckDBRepository("users", mock_conn)
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
        assert len(explanation) == 2
        assert explanation[0] == "QUERY PLAN"
        mock_conn.execute.assert_called_once()
        mock_result.fetchall.assert_called_once()

    def test_find_with_projection_empty_results(self):
        """Test find_with_projection with no results"""
        # Create mock connection and result
        mock_conn = MagicMock()
        mock_result = MagicMock()

        # Mock execute to return result
        mock_conn.execute.return_value = mock_result

        # Mock description
        mock_result.description = [("id",)]

        # Mock empty fetchall
        mock_result.fetchall.return_value = []

        # Create repository and query
        repo = MockDuckDBRepository("users", mock_conn)
        query = QueryProjection(projection=ProjectionList([FieldProjection("id")]))

        # Execute query
        results = list(repo.find_with_projection(query))

        # Verify empty results
        assert len(results) == 0
