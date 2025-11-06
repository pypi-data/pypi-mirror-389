import pytest
from fractal_specifications.generic.operators import EqualsSpecification

from fractal_projections import (
    AggregateFunction,
    AggregateProjection,
    FieldProjection,
    GroupingProjection,
    LimitProjection,
    MongoProjectionBuilder,
    OrderingList,
    OrderingProjection,
    ProjectionList,
    QueryProjection,
)


class TestMongoBuilder:
    """Integration tests for MongoProjectionBuilder"""

    def test_build_without_collection_name_works(self):
        """Test that build() works without collection name (pipelines are collection-agnostic)"""
        builder = MongoProjectionBuilder()
        query = QueryProjection()

        # Should not raise error - pipelines don't require collection name
        pipeline = builder.build(query)
        assert isinstance(pipeline, list)

    def test_build_count_without_collection_name_works(self):
        """Test that build_count() works without collection name (pipelines are collection-agnostic)"""
        builder = MongoProjectionBuilder()
        query = QueryProjection()

        # Should not raise error - pipelines don't require collection name
        pipeline = builder.build_count(query)
        assert isinstance(pipeline, list)
        assert len(pipeline) == 1
        assert "$count" in pipeline[0]

    def test_build_simple_pipeline(self):
        """Test building simple aggregation pipeline"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("email"),
                ]
            )
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        assert isinstance(pipeline, list)
        assert len(pipeline) == 1
        assert "$project" in pipeline[0]

    def test_build_pipeline_with_filter(self):
        """Test building pipeline with $match stage"""
        query = QueryProjection(
            filter=EqualsSpecification("status", "active"),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        assert len(pipeline) >= 1
        assert "$match" in pipeline[0]
        assert "status" in pipeline[0]["$match"]

    def test_build_count_pipeline(self):
        """Test building COUNT pipeline"""
        query = QueryProjection()

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build_count(query)

        assert isinstance(pipeline, list)
        assert {"$count": "count"} in pipeline

    def test_build_count_with_filter(self):
        """Test building COUNT pipeline with filter"""
        query = QueryProjection(filter=EqualsSpecification("status", "active"))

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build_count(query)

        assert "$match" in pipeline[0]
        assert "status" in pipeline[0]["$match"]
        assert {"$count": "count"} in pipeline

    def test_build_with_grouping(self):
        """Test building pipeline with $group stage (lines 121-125)"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("department"),
                    AggregateProjection(
                        AggregateFunction.COUNT, field="id", alias="count"
                    ),
                ]
            ),
            grouping=GroupingProjection(["department"]),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        # Should have a $group stage
        assert any("$group" in stage for stage in pipeline)

    def test_build_with_ordering(self):
        """Test building pipeline with $sort stage (lines 134-136)"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            ordering=OrderingList(
                [
                    OrderingProjection("created_at", ascending=False),
                    OrderingProjection("name", ascending=True),
                ]
            ),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        # Should have a $sort stage
        assert any("$sort" in stage for stage in pipeline)
        sort_stage = next(stage for stage in pipeline if "$sort" in stage)
        assert sort_stage["$sort"]["created_at"] == -1
        assert sort_stage["$sort"]["name"] == 1

    def test_build_with_limiting(self):
        """Test building pipeline with $limit and $skip (lines 140-142)"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            limiting=LimitProjection(10, offset=5),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        # Should have $skip and $limit stages
        assert any("$skip" in stage for stage in pipeline)
        assert any("$limit" in stage for stage in pipeline)

    def test_build_with_aggregates_no_grouping(self):
        """Test building pipeline with aggregates but no grouping (lines 166-207)"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    AggregateProjection(AggregateFunction.COUNT, alias="total"),
                    AggregateProjection(
                        AggregateFunction.SUM, field="amount", alias="total_amount"
                    ),
                ]
            ),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        # Should have a $group stage with null _id (global aggregation)
        group_stage = next((stage for stage in pipeline if "$group" in stage), None)
        assert group_stage is not None
        assert group_stage["$group"]["_id"] is None

    def test_build_project_stage(self):
        """Test _build_project_stage with simple field projection (line 157)"""
        projection_list = ProjectionList(
            [FieldProjection("name"), FieldProjection("email")]
        )

        project_dict = MongoProjectionBuilder._build_project_stage(projection_list)

        # Should have field selections in $project stage
        assert "$project" in project_dict
        assert "name" in project_dict["$project"]
        assert project_dict["$project"]["name"] == "$name"
        assert "email" in project_dict["$project"]
        assert project_dict["$project"]["email"] == "$email"

    def test_build_group_stage(self):
        """Test _build_group_stage with grouping and aggregates (lines 166-207)"""
        projection_list = ProjectionList(
            [
                FieldProjection("department"),
                AggregateProjection(AggregateFunction.COUNT, field="id", alias="count"),
                AggregateProjection(
                    AggregateFunction.AVG, field="salary", alias="avg_salary"
                ),
            ]
        )
        grouping = GroupingProjection(["department"])

        group_dict = MongoProjectionBuilder._build_group_stage(
            projection_list, grouping
        )

        # Check $group stage structure
        assert "$group" in group_dict
        assert "_id" in group_dict["$group"]

        # Check aggregates
        assert "count" in group_dict["$group"]
        assert "avg_salary" in group_dict["$group"]

    def test_build_sort_stage(self):
        """Test _build_sort_stage method (lines 212-217)"""
        ordering = OrderingList(
            [
                OrderingProjection("created_at", ascending=False),
                OrderingProjection("name", ascending=True),
            ]
        )

        sort_dict = MongoProjectionBuilder._build_sort_stage(ordering)

        assert "$sort" in sort_dict
        assert sort_dict["$sort"]["created_at"] == -1
        assert sort_dict["$sort"]["name"] == 1

    def test_build_aggregate_count_star(self):
        """Test building COUNT(*) aggregate"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    AggregateProjection(AggregateFunction.COUNT, alias="total"),
                ]
            ),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        group_stage = next(stage for stage in pipeline if "$group" in stage)
        assert "total" in group_stage["$group"]
        assert "$sum" in group_stage["$group"]["total"]

    def test_build_aggregate_count_field(self):
        """Test building COUNT(field) aggregate"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    AggregateProjection(
                        AggregateFunction.COUNT, field="user_id", alias="user_count"
                    ),
                ]
            ),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        group_stage = next(stage for stage in pipeline if "$group" in stage)
        assert "user_count" in group_stage["$group"]

    @pytest.mark.parametrize(
        "function,field,alias,expected_operator",
        [
            (AggregateFunction.SUM, "amount", "total", "$sum"),
            (AggregateFunction.AVG, "price", "avg_price", "$avg"),
            (AggregateFunction.MIN, "created_at", "earliest", "$min"),
            (AggregateFunction.MAX, "updated_at", "latest", "$max"),
            (AggregateFunction.COUNT_DISTINCT, "email", "unique_emails", "$addToSet"),
        ],
    )
    def test_build_aggregate_functions(self, function, field, alias, expected_operator):
        """Test building aggregate functions (SUM, AVG, MIN, MAX, COUNT_DISTINCT)"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    AggregateProjection(function, field=field, alias=alias),
                ]
            ),
        )

        builder = MongoProjectionBuilder("users")
        pipeline = builder.build(query)

        group_stage = next(stage for stage in pipeline if "$group" in stage)
        assert alias in group_stage["$group"]
        assert expected_operator in group_stage["$group"][alias]

    def test_build_project_stage_empty(self):
        """Test _build_project_stage with empty projection (line 157)"""
        projection_list = ProjectionList([])

        project_dict = MongoProjectionBuilder._build_project_stage(projection_list)

        # Should return empty dict
        assert project_dict == {}

    def test_build_group_stage_multiple_fields(self):
        """Test _build_group_stage with multiple grouping fields (line 173)"""
        projection_list = ProjectionList(
            [
                FieldProjection("department"),
                FieldProjection("location"),
                AggregateProjection(AggregateFunction.COUNT, alias="count"),
            ]
        )
        grouping = GroupingProjection(["department", "location"])

        group_dict = MongoProjectionBuilder._build_group_stage(
            projection_list, grouping
        )

        # Check _id is a dict with multiple fields
        assert "$group" in group_dict
        assert isinstance(group_dict["$group"]["_id"], dict)
        assert "department" in group_dict["$group"]["_id"]
        assert "location" in group_dict["$group"]["_id"]

    def test_build_count_distinct_pipeline(self):
        """Test build_count_distinct_pipeline static method (line 227)"""
        pipeline = MongoProjectionBuilder.build_count_distinct_pipeline("user_id")

        # Should have two stages: group with addToSet, then project with size
        assert len(pipeline) == 2
        assert "$group" in pipeline[0]
        assert "$addToSet" in pipeline[0]["$group"]["distinct_values"]
        assert "$project" in pipeline[1]
        assert "$size" in pipeline[1]["$project"]["count"]
