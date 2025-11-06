"""
Projection Builders

Database-specific builders that convert generic projections into
optimized database queries (SQL, MongoDB aggregation pipelines, etc.).
"""

from fractal_projections.builders.base import ProjectionBuilder

__all__ = [
    "ProjectionBuilder",
]

# Optional imports - only available if dependencies are installed
try:
    from fractal_projections.builders.postgres import (  # noqa: F401
        PostgresProjectionBuilder,
    )

    __all__.append("PostgresProjectionBuilder")
except ImportError:
    pass

try:
    from fractal_projections.builders.django import DjangoProjectionBuilder  # noqa: F401

    __all__.append("DjangoProjectionBuilder")
except ImportError:
    pass

try:
    from fractal_projections.builders.duckdb import DuckDBProjectionBuilder  # noqa: F401

    __all__.append("DuckDBProjectionBuilder")
except ImportError:
    pass

try:
    from fractal_projections.builders.mongo import MongoProjectionBuilder  # noqa: F401

    __all__.append("MongoProjectionBuilder")
except ImportError:
    pass

try:
    from fractal_projections.builders.firestore import (  # noqa: F401
        FirestoreProjectionBuilder,
    )

    __all__.append("FirestoreProjectionBuilder")
except ImportError:
    pass

try:
    from fractal_projections.builders.elasticsearch import (  # noqa: F401
        ElasticsearchProjectionBuilder,
    )

    __all__.append("ElasticsearchProjectionBuilder")
except ImportError:
    pass
