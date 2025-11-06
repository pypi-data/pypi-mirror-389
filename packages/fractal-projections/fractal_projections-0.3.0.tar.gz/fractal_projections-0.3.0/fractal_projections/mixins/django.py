"""Django ORM projection builder and mixin for fractal-repositories integration."""

from typing import Any, Iterator, List, Protocol, Type

from django.db.models import Model  # type: ignore

from fractal_projections.builders.django import DjangoProjectionBuilder
from fractal_projections.mixins.base import ProjectionsMixin
from fractal_projections.projections.query import QueryProjection


class _DjangoRepositoryProtocol(Protocol):
    """Protocol defining the interface required by DjangoProjectionsMixin."""

    django_model: Type[Model]


class DjangoProjectionsMixin(ProjectionsMixin):
    """
    Django ORM implementation of projection query capabilities.

    Provides advanced querying with projections, aggregations, grouping, and
    computed fields using Django's QuerySet API.

    Must be used with DjangoModelRepositoryMixin from fractal-repositories.

    Example:
        from fractal_repositories.contrib.django import DjangoModelRepositoryMixin
        from fractal_projections import DjangoProjectionsMixin

        class MyRepository(DjangoModelRepositoryMixin[MyEntity],
                          DjangoProjectionsMixin):
            entity = MyEntity
            django_model = MyDjangoModel
    """

    def find_with_projection(
        self: _DjangoRepositoryProtocol, query_projection: QueryProjection
    ) -> Iterator[Any]:
        """
        Execute a complete query projection with projections, aggregates, etc.

        Returns raw results (not domain entities) since projections may not map to entities.
        """
        builder = DjangoProjectionBuilder(self.django_model)
        queryset = builder.build(query_projection)

        for result in queryset:
            yield result

    def count_with_projection(
        self: _DjangoRepositoryProtocol, query_projection: QueryProjection
    ) -> int:
        """Count rows matching the query projection (ignores projections)"""
        builder = DjangoProjectionBuilder(self.django_model)
        queryset = builder.build_count(query_projection)
        return queryset.count()

    def explain_query(
        self: _DjangoRepositoryProtocol, query_projection: QueryProjection
    ) -> List[str]:
        """Get query execution plan for performance analysis"""
        builder = DjangoProjectionBuilder(self.django_model)
        explanation = builder.explain(query_projection)
        return [explanation]
