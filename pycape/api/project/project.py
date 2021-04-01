import io
import sys
from abc import ABC
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
from urllib.parse import urlparse

import pandas as pd
from tabulate import tabulate

from ...network.requester import Requester
from ..dataview.dataview import DataView
from ..job.job import Job
from ..organization.organization import Organization
from ..task.task import Task


class Project(ABC):
    """
    Projects are the business contexts in which you collaborate with other organizations or Cape users to train models.

    Arguments:
        id (str): ID of `Project`.
        name (str): name of `Project`.
        label (str): label of `Project`.
        description (str): description of `Project`.
        owner (dict): Returned dictionary of fields related to the `Project` owner.
        organizations (list): Returned list of fields related to the organizations associated with the `Project`.
        dataviews (list): Returned list of `DataViews` added to the `Project`.
        jobs (list) Returned list of `Jobs` submitted on the `Project`.
    """

    def __init__(
        self,
        user_id: str,
        id: Optional[str] = None,
        name: Optional[str] = None,
        label: Optional[str] = None,
        description: Optional[str] = None,
        owner: Optional[dict] = None,
        organizations: Optional[List[Dict]] = None,
        data_views: Optional[List[Dict]] = None,
        jobs: Optional[List[Dict]] = None,
        requester: Optional[Requester] = None,
        out: Optional[io.StringIO] = None,
    ):
        self._requester: Requester = requester
        self._user_id: str = user_id
        self._out: io.StringIO = out
        if out is None:
            self._out = sys.stdout

        if id is None:
            raise Exception("Projects cannot be initialized without an id")

        self.id = id
        self.name: Optional[str] = name
        self.label: Optional[str] = label
        self.description: Optional[str] = description

        if organizations is not None:
            self.organizations: List[Organization] = [
                Organization(**o) for o in organizations
            ]

        if data_views is not None:
            self.dataviews: List[DataView] = [DataView(**d) for d in data_views]

        if jobs is not None:
            self.jobs: List[Job] = [
                Job(project_id=self.id, **j, requester=self._requester,) for j in jobs
            ]

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, name={self.name}, label={self.label})"

    def list_dataviews(self) -> List[DataView]:
        """
        Returns a list of dataviews for the scoped `Project`.

        Returns:
            A list of `DataView` instances.
        """

        data_views = self._requester.list_dataviews(project_id=self.id)
        get_data_view_values = [
            DataView(user_id=self._user_id, **d) for d in data_views
        ]
        dv_ids = []
        dv_names = []
        dv_locations = []
        dv_owners = []

        for dv in get_data_view_values:
            dv_ids.append(dv.id)
            dv_names.append(dv.name)
            dv_locations.append(dv.location)
            dv_owner_label = dv._owner.get("label")
            if self._user_id in [x.get("id") for x in dv._owner.get("members")]:
                dv_owners.append(f"{dv_owner_label} (You)")
            else:
                dv_owners.append(dv_owner_label)

        format_data_views = {
            "DATAVIEW ID": dv_ids,
            "NAME": dv_names,
            "LOCATION": dv_locations,
            "OWNER": dv_owners,
        }
        self._out.write(tabulate(format_data_views, headers="keys") + "\n")
        return [DataView(user_id=self._user_id, **d) for d in data_views]

    def get_dataview(
        self, id: Optional[str] = None, uri: Optional[str] = None
    ) -> DataView:
        """
        Query a `DataView` for the scoped `Project` by `DataView` \
        ID or URI.

        Arguments:
            id: ID of `DataView`.
            uri: Unique `DataView` URI.
        Returns:
            A `DataView` instance.
        """
        data_view = self._requester.get_dataview(
            project_id=self.id, dataview_id=id, uri=uri
        )

        return DataView(user_id=self._user_id, **data_view[0]) if data_view else None

    def create_dataview(
        self,
        name: str,
        uri: str,
        owner_id: Optional[str] = None,
        owner_label: Optional[str] = None,
        schema: Union[pd.Series, List, None] = None,
        development: bool = False,
    ) -> DataView:
        """
        Creates a `DataView` in Cape Cloud. Returns created `Dataview`

        Arguments:
            name: a name for the `DataView`.
            uri: URI location of the dataset.
            owner_id: The ID of the organization that owns this dataset.
            owner_label: The label of the organization that owns this dataset.
            schema: The schema of the data that `DataView` points to.
                A string value for each column's datatype. Possible datatypes:
                    string
                    integer
                    number
                    datetime
            development: Whether the created dataview is in development mode or not.
        Returns:
            A `DataView` instance.
        """
        parse_schema = DataView._validate_schema(schema)

        if not parse_schema and urlparse(uri).scheme in [
            "http",
            "https",
        ]:
            parse_schema = DataView._get_schema_from_uri(uri)
        elif not parse_schema:
            raise Exception("DataView schema must be specified.")

        data_view_dict = self._requester.create_dataview(
            project_id=self.id,
            name=name,
            uri=uri,
            owner_id=owner_id,
            owner_label=owner_label,
            schema=parse_schema,
            development=development,
        )
        data_view = DataView(user_id=self._user_id, **data_view_dict)

        if hasattr(self, "dataviews"):
            self.dataviews.append(data_view)
        else:
            self.dataviews = [data_view]
        return data_view

    def _create_task(self, task: Task, timeout: float = 600) -> Job:
        """
        Calls GQL `mutation createTask`

        Arguments:
            task: Instance of class that inherits from `Task`.
            timeout: How long (in ms) a Cape Worker should run before canceling the `Job`.
        Returns:
            A `Job` instance.
        """

        task_config = {k: v for k, v in task.__dict__.items()}
        model_location = task_config.get("_Task__model_location")
        task_config.update(model_location=model_location)

        created_task = task.__class__(**task_config)._create_task(
            project_id=self.id, timeout=timeout, requester=self._requester
        )
        return task.__class__(**created_task, model_location=model_location)

    def submit_job(self, task: Task, timeout: float = 600) -> Job:
        """
        Submits a `Job` to be run by your Cape worker in \
        collaboration with other organizations in your `Project`.

        Arguments:
            task: Instance of class that inherits from `Task`.
            timeout: How long (in ms) a Cape Worker should run before canceling the `Job`.
        Returns:
            A `Job` instance.
        """
        created_job = self._create_task(task=task, timeout=timeout)

        submitted_job = created_job._submit_job(requester=self._requester)

        return Job(project_id=self.id, **submitted_job, requester=self._requester)

    def get_job(self, id: str) -> List[Job]:
        """
        Returns a `Job` given an ID.

        Arguments:
            id: ID of `Job`.
        Returns:
            A `Job` instance.
        """
        job = self._requester.get_job(project_id=self.id, job_id=id, return_params="")

        return Job(**job, project_id=self.id, requester=self._requester)

    def list_jobs(self) -> Job:
        """
        Returns a list of `Jobs` for the scoped `Project`.

        Returns:
            A list of `Job` instances.
        """
        jobs = self._requester.list_jobs(project_id=self.id)
        get_job_values = [
            Job(project_id=self.id, requester=self._requester, **j) for j in jobs
        ]
        j_ids = []
        j_type = []
        j_status = []

        for j in get_job_values:
            j_ids.append(j.id)
            j_type.append(j.job_type)
            j_status.append(j.status)

        format_jobs = {
            "JOB ID": j_ids,
            "TYPE": j_type,
            "STATUS": j_status,
        }
        self._out.write(tabulate(format_jobs, headers="keys") + "\n")
        return get_job_values

    def delete_dataview(self, id: str) -> None:
        """
        Remove a `DataView` by ID.

        Arguments:
            id: ID of `DataView`.
        """
        self._requester.delete_dataview(id=id)

        if hasattr(self, "dataviews"):
            self.dataviews = [x for x in self.dataviews if id != x.id]

        self._out.write(f"DataView ({id}) deleted" + "\n")
        return
