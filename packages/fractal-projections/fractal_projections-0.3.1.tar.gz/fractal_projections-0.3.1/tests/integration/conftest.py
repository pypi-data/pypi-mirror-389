"""Shared fixtures for integration tests."""

import pytest


@pytest.fixture
def test_user_data():
    """Common test user data used across integration tests.

    Returns a list of user dictionaries with consistent test data.
    All integration tests (Django, MongoDB, DuckDB) use the same dataset
    to ensure consistent behavior across different backends.
    """
    return [
        {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "age": 30,
            "status": "active",
            "department": "Engineering",
            "salary": 75000.00,
        },
        {
            "id": 2,
            "name": "Bob",
            "email": "bob@example.com",
            "age": 25,
            "status": "active",
            "department": "Engineering",
            "salary": 65000.00,
        },
        {
            "id": 3,
            "name": "Charlie",
            "email": "charlie@example.com",
            "age": 35,
            "status": "inactive",
            "department": "Sales",
            "salary": 70000.00,
        },
        {
            "id": 4,
            "name": "Diana",
            "email": "diana@example.com",
            "age": 28,
            "status": "active",
            "department": "Marketing",
            "salary": 68000.00,
        },
        {
            "id": 5,
            "name": "Eve",
            "email": "eve@example.com",
            "age": 32,
            "status": "active",
            "department": "Engineering",
            "salary": 80000.00,
        },
        {
            "id": 6,
            "name": "Frank",
            "email": "frank@example.com",
            "age": 40,
            "status": "pending",
            "department": "Sales",
            "salary": 72000.00,
        },
        {
            "id": 7,
            "name": "Grace",
            "email": "grace@example.com",
            "age": 29,
            "status": "active",
            "department": "Marketing",
            "salary": 69000.00,
        },
        {
            "id": 8,
            "name": "Henry",
            "email": "henry@example.com",
            "age": 33,
            "status": "inactive",
            "department": "Engineering",
            "salary": 76000.00,
        },
    ]
