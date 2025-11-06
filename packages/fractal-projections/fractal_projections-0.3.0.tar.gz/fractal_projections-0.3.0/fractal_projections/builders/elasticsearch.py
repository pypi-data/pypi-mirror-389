"""
Elasticsearch Projection Builder

Converts generic projections to Elasticsearch query DSL with aggregations.
"""

from typing import Dict, List

from fractal_specifications.contrib.elasticsearch.specifications import (
    ElasticSpecificationBuilder,
)

from fractal_projections.builders.base import ProjectionBuilder
from fractal_projections.projections.fields import (
    AggregateFunction,
    AggregateProjection,
    FieldProjection,
    ProjectionList,
)
from fractal_projections.projections.grouping import GroupingProjection
from fractal_projections.projections.limiting import LimitProjection
from fractal_projections.projections.ordering import OrderingList
from fractal_projections.projections.query import QueryProjection


class ElasticsearchProjectionBuilder(ProjectionBuilder):
    """Builds Elasticsearch query DSL from projection objects and complete queries"""

    def __init__(self, index_name: str = None):
        """
        Initialize builder, optionally with an index name for complete queries

        Args:
            index_name: Name of the index to query (required for build(), build_count())
        """
        super().__init__(index_name)
        self.index_name = index_name  # Alias for backwards compatibility

    def build(self, query_projection: QueryProjection) -> Dict:
        """
        Build complete Elasticsearch query from QueryProjection

        Args:
            query_projection: The query projection to convert

        Returns:
            Elasticsearch query dictionary

        Example:
            builder = ElasticsearchProjectionBuilder("users")
            query = builder.build(query_projection)
        """
        self._require_collection_name("build")

        # Build the query using static method
        query = self.build_query(
            query_projection.projection,
            query_projection.grouping,
            query_projection.ordering,
            query_projection.limiting,
        )

        # Add filter/query clause
        if query_projection.filter:
            es_query = ElasticSpecificationBuilder.build(query_projection.filter)
            if es_query:
                query["query"] = es_query

        return query

    def build_count(self, query_projection: QueryProjection) -> Dict:
        """
        Build optimized COUNT query from QueryProjection

        Args:
            query_projection: The query projection to convert

        Returns:
            Elasticsearch count query dictionary
        """
        self._require_collection_name("build_count")

        query = {}

        # Add filter if present
        if query_projection.filter:
            es_query = ElasticSpecificationBuilder.build(query_projection.filter)
            if es_query:
                query["query"] = es_query

        # For count queries, we just need the query part, not aggregations
        return query

    @staticmethod
    def build_query(
        projection: ProjectionList,
        grouping: GroupingProjection = None,
        ordering: OrderingList = None,
        limiting: LimitProjection = None,
    ) -> Dict:
        """
        Convert projections to Elasticsearch query DSL

        Returns an Elasticsearch query dict with aggregations like:
        {
            "size": 0,  # Don't return documents, just aggregations
            "aggs": {
                "organization_stats": {
                    "terms": {"field": "organization_id"},
                    "aggs": {
                        "total_rows": {"sum": {"field": "rows"}},
                        "avg_rows": {"avg": {"field": "rows"}}
                    }
                }
            }
        }
        """
        query = {}

        if not projection or not projection.fields:
            # Simple query without aggregations
            if limiting:
                query["size"] = limiting.limit
                if limiting.offset > 0:
                    query["from"] = limiting.offset
            return query

        # Handle aggregations
        if projection.has_aggregates() or grouping:
            # Use aggregations - don't return documents
            query["size"] = 0
            query["aggs"] = ElasticsearchProjectionBuilder._build_aggregations(
                projection, grouping
            )
        else:
            # Simple field selection
            source_fields = [
                field.field
                for field in projection.fields
                if isinstance(field, FieldProjection)
            ]
            if source_fields:
                query["_source"] = source_fields

            # Add pagination
            if limiting:
                query["size"] = limiting.limit
                if limiting.offset > 0:
                    query["from"] = limiting.offset

        # Add sorting (only for non-aggregation queries)
        if ordering and not (projection.has_aggregates() or grouping):
            query["sort"] = ElasticsearchProjectionBuilder._build_sort(ordering)

        return query

    @staticmethod
    def _build_aggregations(
        projection: ProjectionList, grouping: GroupingProjection = None
    ) -> Dict:
        """Build Elasticsearch aggregations"""
        aggs = {}

        if grouping:
            # Terms aggregation for grouping
            group_field = grouping.fields[0]  # ES typically groups by one field
            agg_name = f"grouped_by_{group_field}"

            aggs[agg_name] = {
                "terms": {
                    "field": group_field,
                    "size": 10000,  # Large enough to get all groups
                }
            }

            # Sub-aggregations for metrics
            sub_aggs = {}
            for field_spec in projection.fields:
                if isinstance(field_spec, AggregateProjection):
                    sub_agg = ElasticsearchProjectionBuilder._build_metric_aggregation(
                        field_spec
                    )
                    if sub_agg:
                        agg_key = (
                            field_spec.alias
                            or f"{field_spec.function.value.lower()}_{field_spec.field}"
                        )
                        sub_aggs[agg_key] = sub_agg

            if sub_aggs:
                aggs[agg_name]["aggs"] = sub_aggs

        else:
            # Global aggregations (no grouping)
            for field_spec in projection.fields:
                if isinstance(field_spec, AggregateProjection):
                    agg = ElasticsearchProjectionBuilder._build_metric_aggregation(
                        field_spec
                    )
                    if agg:
                        func_name = field_spec.function.value.lower()
                        field_name = field_spec.field or "all"
                        agg_key = field_spec.alias or f"{func_name}_{field_name}"
                        aggs[agg_key] = agg

        return aggs

    @staticmethod
    def _build_metric_aggregation(agg_proj: AggregateProjection) -> Dict:
        """Build individual metric aggregation"""
        if agg_proj.function == AggregateFunction.COUNT:
            return (
                {"value_count": {"field": agg_proj.field}}
                if agg_proj.field
                else {"value_count": {"field": "_id"}}
            )

        elif agg_proj.function == AggregateFunction.COUNT_DISTINCT:
            return {"cardinality": {"field": agg_proj.field}}

        elif agg_proj.function == AggregateFunction.SUM:
            return {"sum": {"field": agg_proj.field}}

        elif agg_proj.function == AggregateFunction.AVG:
            return {"avg": {"field": agg_proj.field}}

        elif agg_proj.function == AggregateFunction.MIN:
            return {"min": {"field": agg_proj.field}}

        elif agg_proj.function == AggregateFunction.MAX:
            return {"max": {"field": agg_proj.field}}

        return {}

    @staticmethod
    def _build_sort(ordering: OrderingList) -> List[Dict]:
        """Build Elasticsearch sort configuration"""
        sort_configs = []

        for order_proj in ordering:
            sort_config = {
                order_proj.field: {"order": "asc" if order_proj.ascending else "desc"}
            }
            sort_configs.append(sort_config)

        return sort_configs

    @staticmethod
    def build_search_after_query(
        projection: ProjectionList,
        search_after_values: List,
        ordering: OrderingList = None,
        limiting: LimitProjection = None,
    ) -> Dict:
        """
        Build query with search_after for efficient pagination

        This is more efficient than offset-based pagination for large datasets.
        """
        query = ElasticsearchProjectionBuilder.build_query(
            projection, None, ordering, limiting
        )

        if search_after_values:
            query["search_after"] = search_after_values

        return query
