"""
Core Projection Classes

These classes define data shaping operations (what data to return and
how to transform it) as opposed to specifications which define filtering
operations (what data to include/exclude).
"""

from fractal_projections.projections.fields import *
from fractal_projections.projections.grouping import *
from fractal_projections.projections.limiting import *
from fractal_projections.projections.ordering import *
from fractal_projections.projections.query import *

__all__ = [
    # Field projections
    "FieldProjection",
    "AggregateProjection",
    "AggregateFunction",
    "ProjectionList",
    # Grouping
    "GroupingProjection",
    # Ordering
    "OrderingProjection",
    "OrderingList",
    # Limiting
    "LimitProjection",
    # Complete query projection
    "QueryProjection",
    "QueryProjectionBuilder",
    # Convenience functions
    "select",
    "select_distinct",
    "count",
]
