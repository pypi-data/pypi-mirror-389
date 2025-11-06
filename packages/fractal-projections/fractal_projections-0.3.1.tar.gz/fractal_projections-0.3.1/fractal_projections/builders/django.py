from typing import Any, Optional, Type

from django.db.models import Avg, Count, Max, Min, Model, QuerySet, Sum, Value  # type: ignore
from fractal_specifications.contrib.django.specifications import (
    DjangoOrmSpecificationBuilder,
)

from fractal_projections.builders.base import ProjectionBuilder
from fractal_projections.projections.fields import (
    AggregateProjection,
    FieldProjection,
)
from fractal_projections.projections.query import QueryProjection


class DjangoProjectionBuilder(ProjectionBuilder):
    """
    Translates QueryProjection to Django ORM QuerySet operations.

    Handles filters, projections, aggregates, grouping, ordering, and limits
    using Django's QuerySet API.

    Example:
        builder = DjangoProjectionBuilder(User)
        queryset = builder.build(query_projection)
        for result in queryset:
            print(result)  # Dictionary with projected fields
    """

    # Map aggregate functions to Django aggregate classes
    AGGREGATE_MAP = {
        "COUNT": Count,
        "AVG": Avg,
        "SUM": Sum,
        "MAX": Max,
        "MIN": Min,
    }

    def __init__(self, model_class: Type[Model] = None):
        """
        Initialize builder with a Django model class

        Args:
            model_class: Django model class to query (required for build(), build_count(), explain())
        """
        super().__init__(collection_name=model_class.__name__ if model_class else None)
        self.model_class = model_class

    def build(self, query_projection: QueryProjection) -> QuerySet:
        """
        Build a complete QuerySet with filters, projections, aggregates, and ordering.

        Args:
            query_projection: The projection configuration

        Returns:
            QuerySet configured with filters and projections

        Raises:
            ValueError: If model_class is not set

        Example:
            builder = DjangoProjectionBuilder(User)
            queryset = builder.build(query_projection)
        """
        if not self.model_class:
            raise ValueError(
                "model_class is required for build(). Initialize with DjangoProjectionBuilder(model_class)"
            )

        queryset = self.model_class.objects.all()

        # Apply filters using Specification
        if query_projection.filter:
            q_filter = DjangoOrmSpecificationBuilder.build(query_projection.filter)
            if q_filter:
                queryset = queryset.filter(q_filter)

        # Handle projections and aggregates
        if query_projection.projection:
            queryset = self._apply_projections(
                queryset,
                query_projection.projection,
                query_projection.grouping,
            )

        # Apply ordering
        if query_projection.ordering:
            queryset = self._apply_ordering(queryset, query_projection.ordering)

        # Apply limit and offset
        if query_projection.limiting:
            queryset = self._apply_limiting(queryset, query_projection.limiting)

        return queryset

    def build_count(self, query_projection: QueryProjection) -> QuerySet:
        """
        Build a QuerySet configured for counting (applies filters only).

        Args:
            query_projection: The projection configuration

        Returns:
            QuerySet filtered and ready for .count()

        Raises:
            ValueError: If model_class is not set
        """
        if not self.model_class:
            raise ValueError(
                "model_class is required for build_count(). Initialize with DjangoProjectionBuilder(model_class)"
            )

        queryset = self.model_class.objects.all()

        # Apply filters only
        if query_projection.filter:
            q_filter = DjangoOrmSpecificationBuilder.build(query_projection.filter)
            if q_filter:
                queryset = queryset.filter(q_filter)

        return queryset

    def explain(self, query_projection: QueryProjection) -> str:
        """
        Get query execution plan using Django's .explain().

        Args:
            query_projection: The projection configuration

        Returns:
            Explanation string from Django's QuerySet.explain()

        Raises:
            ValueError: If model_class is not set
        """
        if not self.model_class:
            raise ValueError(
                "model_class is required for explain(). Initialize with DjangoProjectionBuilder(model_class)"
            )

        queryset = self.build(query_projection)
        explanation = queryset.explain()
        return explanation

    def _apply_projections(
        self,
        queryset: QuerySet,
        projection_list: Any,
        grouping: Any = None,
    ) -> QuerySet:
        """
        Apply projections and aggregates to QuerySet.

        Args:
            queryset: Base QuerySet
            projection_list: ProjectionList object
            grouping: Optional GroupingProjection object

        Returns:
            QuerySet with .values() and .annotate() applied
        """
        # Extract field names and aggregates from projection list
        simple_fields = []
        annotate_fields = {}

        # Get projections from the projection_list
        if hasattr(projection_list, "fields") and projection_list.fields:
            for proj in projection_list.fields:
                if isinstance(proj, FieldProjection):
                    simple_fields.append(proj.field)
                elif isinstance(proj, AggregateProjection):
                    # Handle aggregate projection
                    aggregate = self._build_aggregate(proj)
                    if aggregate:
                        annotate_fields[proj.alias or proj.field] = aggregate

        # Apply grouping and aggregation
        if grouping and hasattr(grouping, "fields"):
            # Group by specified fields
            queryset = queryset.values(*grouping.fields)
            if annotate_fields:
                queryset = queryset.annotate(**annotate_fields)
        elif annotate_fields:
            # Aggregation without grouping (single result)
            if simple_fields:
                queryset = queryset.values(*simple_fields).annotate(**annotate_fields)
            else:
                # For global aggregation, use a dummy grouping field to group all rows together
                queryset = (
                    queryset.annotate(_group=Value(1))
                    .values("_group")
                    .annotate(**annotate_fields)
                    .values(*annotate_fields.keys())
                )
        elif simple_fields:
            # Simple projection without aggregates
            queryset = queryset.values(*simple_fields)

        return queryset

    def _build_aggregate(self, aggregate_proj: AggregateProjection) -> Optional[Any]:
        """
        Build Django aggregate from AggregateProjection.

        Args:
            aggregate_proj: AggregateProjection object

        Returns:
            Django aggregate object or None
        """
        func_name = aggregate_proj.function.value
        field_name = aggregate_proj.field

        aggregate_class = self.AGGREGATE_MAP.get(func_name)
        if not aggregate_class:
            return None

        if field_name == "*" or not field_name:
            # COUNT(*) - count all rows
            return aggregate_class("id")  # Use primary key for counting
        else:
            # COUNT(field), AVG(field), etc.
            return aggregate_class(field_name)

    def _apply_ordering(self, queryset: QuerySet, ordering_list: Any) -> QuerySet:
        """
        Apply ordering to QuerySet.

        Args:
            queryset: Base QuerySet
            ordering_list: OrderingList object

        Returns:
            QuerySet with .order_by() applied
        """
        if not ordering_list or not hasattr(ordering_list, "orderings"):
            return queryset

        order_fields = []
        for ordering in ordering_list.orderings:
            field = ordering.field
            ascending = ordering.ascending  # Boolean value

            if not ascending:
                order_fields.append(f"-{field}")
            else:
                order_fields.append(field)

        if order_fields:
            queryset = queryset.order_by(*order_fields)

        return queryset

    def _apply_limiting(self, queryset: QuerySet, limiting: Any) -> QuerySet:
        """
        Apply limit and offset to QuerySet.

        Args:
            queryset: Base QuerySet
            limiting: LimitProjection object

        Returns:
            QuerySet with slicing applied
        """
        if not limiting:
            return queryset

        limit = getattr(limiting, "limit", None)
        offset = getattr(limiting, "offset", 0)

        if limit:
            return queryset[offset : offset + limit]
        elif offset:
            return queryset[offset:]

        return queryset
