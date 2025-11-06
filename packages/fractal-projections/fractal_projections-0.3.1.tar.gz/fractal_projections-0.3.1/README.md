# Fractal Projections

> A comprehensive projection system for defining how data should be shaped, aggregated, grouped, ordered, and limited in database queries.

[![PyPI Version][pypi-image]][pypi-url]
[![Build Status][build-image]][build-url]

<!-- Badges -->

[pypi-image]: https://img.shields.io/pypi/v/fractal-projections
[pypi-url]: https://pypi.org/project/fractal-projections/
[build-image]: https://github.com/Fractal-Forge/fractal-projections/actions/workflows/build.yml/badge.svg
[build-url]: https://github.com/Fractal-Forge/fractal-projections/actions/workflows/build.yml

This library complements [fractal-specifications](https://pypi.org/project/fractal-specifications/) (which handles filtering) by providing database-agnostic data shaping capabilities.

## Features

- **Database-Agnostic**: Write projections once, use them across different databases
- **Type-Safe**: Fully typed Python API for better IDE support and fewer errors
- **Flexible**: Support for field selection, aggregations, grouping, ordering, and limiting
- **Multi-Database Support**: Built-in builders for:
  - PostgreSQL
  - Django ORM
  - DuckDB
  - MongoDB
  - Firestore
  - Elasticsearch
- **Repository Integration**: Ready-to-use mixins for [fractal-repositories](https://pypi.org/project/fractal-repositories/)

## Installation

```bash
pip install fractal-projections
```

For specific database support:

```bash
# PostgreSQL
pip install fractal-projections[postgres]

# Django ORM
pip install fractal-projections[django]

# DuckDB
pip install fractal-projections[duckdb]

# MongoDB
pip install fractal-projections[mongo]

# Firestore
pip install fractal-projections[firestore]

# Elasticsearch
pip install fractal-projections[elasticsearch]

# All databases
pip install fractal-projections[all]
```

## Quick Start

```python
from fractal_projections import (
    QueryProjection,
    FieldProjection,
    ProjectionList,
    OrderingProjection,
    OrderingList,
    LimitProjection,
)
from fractal_projections.builders import PostgresProjectionBuilder
from fractal_specifications.generic.operators import EqualsSpecification

# Define a database-agnostic projection
query = QueryProjection(
    filter=EqualsSpecification("status", "active"),
    projection=ProjectionList([
        FieldProjection("id"),
        FieldProjection("name"),
        FieldProjection("created_at"),
    ]),
    ordering=OrderingList([OrderingProjection("created_at", ascending=False)]),
    limiting=LimitProjection(10),
)

# Convert to database-specific query
builder = PostgresProjectionBuilder("users")
sql, params = builder.build(query)
print(sql)
# SELECT id, name, created_at FROM users WHERE status = %s ORDER BY created_at DESC LIMIT 10
# params = ['active']
```

## Core Concepts

### Field Projection

Select specific fields from your data:

```python
from fractal_projections import FieldProjection, ProjectionList

projection = ProjectionList([
    FieldProjection("user_id"),
    FieldProjection("email"),
])
```

### Distinct Selection

Select unique values using the `distinct` parameter:

```python
from fractal_projections import FieldProjection, ProjectionList

# SELECT DISTINCT department FROM users
projection = ProjectionList(
    [FieldProjection("department")],
    distinct=True
)
```

### Aggregation

Perform aggregations using available aggregate functions: COUNT, SUM, AVG, MIN, MAX, COUNT_DISTINCT:

```python
from fractal_projections import AggregateProjection, AggregateFunction, ProjectionList

# Single aggregate
projection = ProjectionList([
    AggregateProjection(AggregateFunction.SUM, "revenue", "total_revenue")
])

# Multiple aggregates
projection = ProjectionList([
    AggregateProjection(AggregateFunction.COUNT, alias="total_count"),
    AggregateProjection(AggregateFunction.AVG, "salary", "avg_salary"),
    AggregateProjection(AggregateFunction.MIN, "created_at", "earliest"),
    AggregateProjection(AggregateFunction.MAX, "updated_at", "latest"),
    AggregateProjection(AggregateFunction.COUNT_DISTINCT, "user_id", "unique_users"),
])
```

### Grouping

Group results by one or more fields:

```python
from fractal_projections import GroupingProjection

grouping = GroupingProjection(["organization_id", "status"])
```

### Ordering

Sort results by fields:

```python
from fractal_projections import OrderingProjection, OrderingList

ordering = OrderingList([
    OrderingProjection("created_at", ascending=False),  # descending
    OrderingProjection("name", ascending=True),  # ascending
])
```

### Limiting

Limit and offset results:

```python
from fractal_projections import LimitProjection

limit = LimitProjection(limit=20, offset=10)
```

## Architecture

The library follows a builder pattern:

1. **Projections**: Database-agnostic definitions of how data should be shaped
2. **Builders**: Database-specific converters that translate projections into native queries
3. **Mixins**: Repository mixins for seamless integration with fractal-repositories

```
QueryProjection (agnostic)
    ↓
PostgresProjectionBuilder → SQL
DjangoProjectionBuilder → Django QuerySet
DuckDBProjectionBuilder → SQL
MongoProjectionBuilder → MongoDB Pipeline
FirestoreProjectionBuilder → Firestore Query
ElasticsearchProjectionBuilder → ES Query DSL
```

This separation allows you to:
- Write business logic once
- Switch databases without changing application code
- Get optimized native queries for each backend

## Repository Integration

Fractal Projections provides ready-to-use mixins for seamless integration with [fractal-repositories](https://pypi.org/project/fractal-repositories/). These mixins add projection capabilities to your repositories.

### Available Mixins

- `PostgresProjectionsMixin` - For PostgreSQL databases
- `DjangoProjectionsMixin` - For Django ORM
- `DuckDBProjectionsMixin` - For DuckDB databases
- `MongoProjectionsMixin` - For MongoDB
- `FirestoreProjectionsMixin` - For Firestore

### Django Example

```python
from fractal_repositories.contrib.django import DjangoModelRepositoryMixin
from fractal_projections import DjangoProjectionsMixin, QueryProjection, FieldProjection, ProjectionList
from fractal_specifications.generic.operators import EqualsSpecification

class UserRepository(DjangoModelRepositoryMixin, DjangoProjectionsMixin):
    entity = User
    django_model = DjangoUserModel

# Use the repository with projections
repo = UserRepository()

# Define a projection query
query = QueryProjection(
    filter=EqualsSpecification("is_active", True),
    projection=ProjectionList([
        FieldProjection("id"),
        FieldProjection("email"),
        FieldProjection("username"),
    ]),
)

# Execute the query using the mixin
results = list(repo.find_with_projection(query))
# Returns: [{'id': 1, 'email': 'user@example.com', 'username': 'user1'}, ...]

# Count results
count = repo.count_with_projection(query)

# Get query explanation
explanation = repo.explain_query(query)
```

### PostgreSQL Example

```python
from fractal_repositories.contrib.postgres import PostgresRepositoryMixin
from fractal_projections import PostgresProjectionsMixin, QueryProjection

class ProductRepository(PostgresRepositoryMixin, PostgresProjectionsMixin):
    entity = Product
    table_name = "products"

repo = ProductRepository(connection)
results = list(repo.find_with_projection(query))
```

### Mixin Methods

All projection mixins provide these methods:

- `find_with_projection(query_projection)` - Execute query and return results
- `count_with_projection(query_projection)` - Count matching records
- `explain_query(query_projection)` - Get query execution plan (for debugging/optimization)

## Advanced Usage

See the [examples.py](https://github.com/Fractal-Forge/fractal-projections/blob/main/fractal_projections/examples.py) file for comprehensive examples including:
- Complex aggregations with grouping
- Multi-field ordering
- Combining filters with projections
- Database-specific optimizations

## Development

```bash
# Clone the repository
git clone https://github.com/Fractal-Forge/fractal-projections.git
cd fractal-projections

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
isort .
ruff check --fix .

# Lint code
ruff check .
mypy fractal_projections
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Related Projects

- [fractal-specifications](https://github.com/douwevandermeij/fractal-specifications) - Database-agnostic filtering system
- [fractal-repositories](https://github.com/douwevandermeij/fractal-repositories) - Repository pattern implementation with projection support
