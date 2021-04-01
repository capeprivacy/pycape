import contextlib

import pytest

from ...exceptions import StorageSchemeException
from ..dataview.dataview import DataView
from .task import Task
from .vertical_linear_regression_task import VerticallyPartitionedLinearRegression


@contextlib.contextmanager
def notraising():
    yield


class TestTask:
    def test_task__repr__(self):
        id = "abc123"
        model_location = "s3://my-bucket"
        t = Task(id=id, model_location=model_location)
        rep = f"Task(id={id})"

        assert repr(t) == rep

    def test_vplr__repr__(self):
        dataview_x = DataView(
            id="dv_x",
            name="my-data-x",
            location="s3://my-data.csv",
            schema=[{"name": "a", "schema_type": "string"}],
        )
        dataview_y = DataView(
            id="dv_y",
            name="my-data-y",
            location="s3://my-data.csv",
            schema=[{"name": "b", "schema_type": "string"}],
        )
        t = VerticallyPartitionedLinearRegression(
            x_train_dataview=dataview_x,
            y_train_dataview=dataview_y["b"],
            model_location="s3://my-location",
        )
        rep = (
            "VerticallyPartitionedLinearRegression(x_train_dataview=my-data-x, y_train_dataview=my-data-y['b'], "
            "model_location=s3://my-location)"
        )

        assert repr(t) == rep

    @pytest.mark.parametrize(
        "model_location,exception",
        [
            ("s3://my-location", notraising()),
            (
                "not a uri",
                pytest.raises(
                    StorageSchemeException, match="only s3 locations supported, got"
                ),
            ),
            (None, pytest.raises(Exception, match="no model location provided")),
        ],
    )
    def test_model_location(self, model_location, exception):
        with exception:
            dataview_x = DataView(
                id="dv_x",
                name="my-data-x",
                location="s3://my-data.csv",
                schema=[{"name": "a", "schema_type": "string"}],
            )
            dataview_y = DataView(
                id="dv_y",
                name="my-data-y",
                location="s3://my-data.csv",
                schema=[{"name": "b", "schema_type": "string"}],
            )
            t = VerticallyPartitionedLinearRegression(
                x_train_dataview=dataview_x,
                y_train_dataview=dataview_y["b"],
                model_location=model_location,
            )

        if isinstance(exception, contextlib._GeneratorContextManager):
            assert t.model_location == model_location
