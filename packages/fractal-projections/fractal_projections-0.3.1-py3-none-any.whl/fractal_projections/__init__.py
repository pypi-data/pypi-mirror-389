"""
Fractal Projections Library

A comprehensive projection system for defining how data should be shaped,
aggregated, grouped, ordered, and limited in database queries.

This library complements fractal_specifications (which handles filtering)
by providing data shaping capabilities.

Includes repository mixins for fractal-repositories integration.
"""

from fractal_projections.builders import *
from fractal_projections.mixins import *
from fractal_projections.projections import *

__version__ = "0.3.1"

__all__ = [
    # Core projections
    "FieldProjection",
    "AggregateProjection",
    "AggregateFunction",
    "ProjectionList",
    "GroupingProjection",
    "OrderingProjection",
    "OrderingList",
    "LimitProjection",
    "QueryProjection",
    # Builder pattern
    "QueryProjectionBuilder",
    # Convenience functions
    "select",
    "select_distinct",
    "count",
    # Builders (for when you need database-specific functionality)
    "PostgresProjectionBuilder",
    "DjangoProjectionBuilder",
    "MongoProjectionBuilder",
    "FirestoreProjectionBuilder",
    "ElasticsearchProjectionBuilder",
    "DuckDBProjectionBuilder",
    # Repository mixins (for fractal-repositories integration)
    "ProjectionsMixin",
    "PostgresProjectionsMixin",
    "DjangoProjectionsMixin",
    "DuckDBProjectionsMixin",
    "MongoProjectionsMixin",
    "FirestoreProjectionsMixin",
]
