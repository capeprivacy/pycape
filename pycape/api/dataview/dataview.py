import json
from abc import ABC
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
from urllib.error import HTTPError

import pandas as pd
from marshmallow import Schema
from marshmallow import fields

from ...utils import filter_date
from ...vars import PANDAS_TO_JSON_DATATYPES


class DataView(ABC):
    """
    Dataviews store metadata around datasets, including namely a pointer to the dataset's location.

    Arguments:
        id (str): ID of `DataView`
        name (str): name of `DataView`.
        schema (list): schema of the data that `DataView` points to.
        location (str): URI of `DataView`.
        owner (dict): Dictionary of fields related to the `DataView` owner.
        user_id (str): User ID of requester.
        development (bool): Whether this dataview is in development mode or not.
    """

    def __init__(
        self,
        id: str = None,
        name: str = None,
        location: str = None,
        schema: Union[pd.Series, List, None] = None,
        owner: dict = None,
        user_id: str = None,
        development: Optional[bool] = None,
    ):
        self.id: Optional[str] = id
        self.name: Optional[str] = name
        self.location: Optional[str] = location
        self._schema: Union[pd.Series, List, None] = schema
        self._user_id: Optional[str] = user_id
        self._owner: Optional[Dict] = owner
        self._cols = None
        self.development = development

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, name={self.name}, location={self.location})"

    def __getitem__(self, cols):
        if isinstance(cols, str):
            self._cols = [cols]
        elif isinstance(cols, tuple):
            self._cols = [c for c in cols]
        return self

    @property
    def schema(self) -> Optional[Dict[str, str]]:
        """
        Return schema as a dict of column names as keys, and values as key data types
        """
        if hasattr(self, "_schema") and self._schema:
            return {s.get("name"): s.get("schema_type") for s in self._schema}

    @staticmethod
    def _validate_schema(schema: Union[pd.Series, List, None]):
        """
        Validate that updates to the schema property are pd.Series.
        """

        def _convert_pd_objects_json(pd_obj: pd.Series) -> list:
            """
            Accepts a pandas dataframe.dtype, converts this pandas schema to a dictionary of JSON-like
            data types defined by the PANDAS_TO_JSON_DATATYPES. Returns converted schema list.
            """
            json_obj = pd_obj.apply(lambda x: x.name).to_dict()
            schema = [{"name": k, "schema_type": v} for k, v in json_obj.items()]

            for i, s in enumerate(schema):
                schema[i]["schema_type"] = PANDAS_TO_JSON_DATATYPES[
                    s.get("schema_type")
                ]

            return schema

        # Check for truthiness seperately because panda throws
        # exception if you check it's truth value within an comparison operator:
        # https://pandas.pydata.org/pandas-docs/version/0.15/gotchas.html
        try:
            if not schema:
                return None
            elif isinstance(schema, list):
                try:
                    DataViewSchema(many=True).load(schema)
                    return schema
                except Exception as e:
                    raise Exception(f"Invalid schema list: {e}")

        except ValueError:
            if isinstance(schema, pd.Series):
                try:
                    return _convert_pd_objects_json(schema)
                except Exception as e:
                    raise Exception(f"Invalid schema pd.Series: {e}")

        raise Exception("Schema is not of type pd.Series")

    @staticmethod
    def _get_schema_from_uri(uri) -> list:
        """
        Read first line from csv file read from uri as dataframe,
        grab schema from dataframe object, return as list of json:
        {
          type: "string",
          name: "my_col_name"
        }
        """

        def _get_date_cols(dataframe: pd.DataFrame) -> list:
            """
            Get list of column names that are of datetime data types
            """
            columns = df.columns
            row_1 = df.iloc[0].values
            date_cols = []

            for i, d in enumerate(row_1):
                if isinstance(d, str) and filter_date(d):
                    date_cols.append(columns[i])

            return date_cols

        try:
            df = pd.read_csv(uri, nrows=1)
        except (HTTPError, FileNotFoundError):
            raise Exception("Cannot access data resource")

        date_cols = _get_date_cols(df)
        for date_col in date_cols:
            df[date_col] = pd.to_datetime(df[date_col])

        # Pandas to_json function converts dataframe object to json
        # in doing so it transforms df datatypes into json-like datatypes
        # ---
        # dtypes object -> string
        # dtypes int64 -> integer
        # dtypes float64 -> number
        # dtypes datetime64[ns] -> datetime
        # dtypes category -> any

        return [
            {"name": s["name"], "schema_type": s["type"]}
            for s in json.loads(df.to_json(orient="table"))
            .get("schema", {})
            .get("fields")
            if s["name"] != "index"
        ]


class DataViewSchema(Schema):
    """
    Schema to validate the schema field on DataViews
    """

    name = fields.Str(required=True)
    schema_type = fields.Str(required=True)
