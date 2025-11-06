"""Repository projection mixins for fractal-repositories integration."""

from fractal_projections.mixins.base import ProjectionsMixin

__all__ = [
    "ProjectionsMixin",
]

# Optional imports - only available if dependencies are installed
try:
    from fractal_projections.mixins.postgres import (  # noqa: F401
        PostgresProjectionsMixin,
    )

    __all__.append("PostgresProjectionsMixin")
except ImportError:
    pass

try:
    from fractal_projections.mixins.django import DjangoProjectionsMixin  # noqa: F401

    __all__.append("DjangoProjectionsMixin")
except ImportError:
    pass

try:
    from fractal_projections.mixins.duckdb import DuckDBProjectionsMixin  # noqa: F401

    __all__.append("DuckDBProjectionsMixin")
except ImportError:
    pass

try:
    from fractal_projections.mixins.mongo import MongoProjectionsMixin  # noqa: F401

    __all__.append("MongoProjectionsMixin")
except ImportError:
    pass

try:
    from fractal_projections.mixins.firestore import (  # noqa: F401
        FirestoreProjectionsMixin,
    )

    __all__.append("FirestoreProjectionsMixin")
except ImportError:
    pass
