from unittest.mock import MagicMock, Mock

from fractal_projections.mixins.postgres import PostgresProjectionsMixin
from fractal_projections.projections.fields import FieldProjection, ProjectionList
from fractal_projections.projections.query import QueryProjection


class MockPostgresRepository(PostgresProjectionsMixin):
    """Mock repository for testing PostgresProjectionsMixin"""

    def __init__(self, table_name, connection):
        self.table_name = table_name
        self._connection = connection

    def _get_connection(self):
        return self._connection


class TestPostgresProjectionsMixin:
    """Tests for PostgresProjectionsMixin"""

    def test_find_with_projection(self):
        """Test find_with_projection returns projected results"""
        # Create mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)

        # Mock cursor results
        mock_results = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        mock_cursor.__iter__ = Mock(return_value=iter(mock_results))

        # Create repository and query
        repo = MockPostgresRepository("users", mock_conn)
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

        # Verify cursor.execute was called
        mock_cursor.execute.assert_called_once()

    def test_count_with_projection(self):
        """Test count_with_projection returns count"""
        # Create mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)

        # Mock count result
        mock_cursor.fetchone.return_value = (42,)

        # Create repository and query
        repo = MockPostgresRepository("users", mock_conn)
        query = QueryProjection()

        # Execute count
        count = repo.count_with_projection(query)

        # Verify count
        assert count == 42
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchone.assert_called_once()

    def test_count_with_projection_and_filter(self):
        """Test count_with_projection with filter"""
        # Create mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)

        # Mock count result
        mock_cursor.fetchone.return_value = (10,)

        # Create repository and query with filter
        from fractal_specifications.generic.operators import EqualsSpecification

        repo = MockPostgresRepository("users", mock_conn)
        query = QueryProjection(filter=EqualsSpecification("status", "active"))

        # Execute count
        count = repo.count_with_projection(query)

        # Verify count
        assert count == 10
        mock_cursor.execute.assert_called_once()

    def test_explain_query(self):
        """Test explain_query returns explanation"""
        # Create mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)

        # Mock explain result
        mock_cursor.fetchall.return_value = [
            ("Seq Scan on users",),
            ("  Filter: (status = 'active')",),
        ]

        # Create repository and query
        repo = MockPostgresRepository("users", mock_conn)
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
        assert explanation[0] == "Seq Scan on users"
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()

    def test_find_with_projection_empty_results(self):
        """Test find_with_projection with no results"""
        # Create mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)

        # Mock empty iteration
        mock_cursor.__iter__ = Mock(return_value=iter([]))

        # Create repository and query
        repo = MockPostgresRepository("users", mock_conn)
        query = QueryProjection(projection=ProjectionList([FieldProjection("id")]))

        # Execute query
        results = list(repo.find_with_projection(query))

        # Verify empty results
        assert len(results) == 0
