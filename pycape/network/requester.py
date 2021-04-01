import os
from typing import Optional

import requests

from ..exceptions import GQLException
from .api_token import APIToken
from .base64 import from_string


class NotAUserException(Exception):
    pass


class Requester:
    dataview_fragment = """
        id
        name
        location
        development
        owner {
            ... on Organization {
                id
                label
                members {
                    id
                }
            }
        }
        schema {
            name
            schema_type
        }"""

    job_fragment = """
        id
        status { code }
        task { type }
    """

    def __init__(self, endpoint: str = None):
        self.endpoint = endpoint or os.environ.get(
            "CAPE_COORDINATOR", "https://demo.capeprivacy.com"
        ).rstrip("/")
        self.gql_endpoint = self.endpoint + "/v1/query"

        self.session = requests.Session()

    def login(self, token: Optional[str] = None) -> str:
        token = token or os.environ.get("CAPE_TOKEN")

        if not token:
            raise Exception("No token provided")

        self.token = token
        self.api_token = APIToken(self.token)

        resp = self.session.post(
            self.endpoint + "/v1/login",
            json={"token_id": self.api_token.token_id, "secret": self.api_token.secret},
        )

        resp.raise_for_status()
        json = resp.json()

        self.token = from_string(json["token"])

        self._check_user(token)

        return json["user_id"]

    def _check_user(self, token):
        me = self.me()

        if me["__typename"] == "MeResponse":
            return True
        else:
            raise NotAUserException(
                f"Token {token} is not a user token. Please navigate to User Settings on Cape to retrieve a user token"
            )

    def _gql_req(self, query: str, variables: Optional[dict]) -> dict:
        input_json = {"query": query, "variables": {}}
        if variables is not None:
            input_json["variables"] = variables

        r = self.session.post(self.gql_endpoint, json=input_json)

        j = {}
        try:
            j = r.json()
        except ValueError:
            r.raise_for_status()

        if "errors" in j:
            raise GQLException(f"An error occurred: {j['errors']}")
        return j["data"]

    def list_projects(self) -> Optional[list]:
        return self._gql_req(
            query=f"""
            query ListProjects {{
                projects {{
                    id
                    name
                    label
                    description
                    organizations {{
                        id
                        name
                        label
                    }}
                    data_views {{
                        {self.dataview_fragment}
                    }}
                    jobs {{
                        {self.job_fragment}
                    }}
                }}
            }}
            """,
            variables=None,
        ).get("projects")

    def get_project(self, id: str = None, label: str = None) -> Optional[dict]:
        return self._gql_req(
            query=f"""
            query GetProject($id: String, $label: Label) {{
                project(id: $id, label: $label) {{
                    id
                    name
                    label
                    description
                    organizations {{
                        id
                        name
                    }}
                    data_views {{
                        {self.dataview_fragment}
                    }}
                    jobs {{
                        {self.job_fragment}
                    }}
                }}
            }}
            """,
            variables={"id": id, "label": label},
        ).get("project")

    def create_project(self, name: str, owner: str, description: str) -> Optional[dict]:
        return self._gql_req(
            query=f"""
            mutation CreateProject (
              $name: ProjectDisplayName!,
              $description: ProjectDescription!,
              $owner: String
            ) {{
              createProject(
                    project: {{
                    name: $name,
                    Description: $description,
                    owner: $owner
                    }}
                ) {{
                id
                name
                owner {{
                  ... on Organization {{
                    id
                  }}
                }}
                data_views {{
                    {self.dataview_fragment}
                }}
                jobs {{
                    {self.job_fragment}
                }}
              }}
            }}
            """,
            variables={"name": name, "owner": owner, "description": description},
        ).get("createProject")

    def archive_project(self, id: str) -> Optional[dict]:
        return self._gql_req(
            query="""
            mutation ArchiveProject (
              $id: String!,
            ) {
              archiveProject(
                id: $id
            ) {
                ArchivedProjectID
              }
            }
            """,
            variables={"id": id},
        ).get("archiveProject")

    def create_dataview(
        self,
        project_id: str,
        name: str,
        uri: str,
        owner_id: Optional[str],
        owner_label: Optional[str],
        schema: list,
        development: bool = False,
    ) -> Optional[dict]:
        return self._gql_req(
            query=f"""
            mutation AddDataView (
              $project_id: String!,
              $data_view_input: DataViewInput!
            ) {{
              addDataView(project_id: $project_id, data_view_input: $data_view_input) {{
                {self.dataview_fragment}
              }}
            }}
            """,
            variables={
                "project_id": project_id,
                "data_view_input": {
                    "name": name,
                    "uri": uri,
                    "owner_id": owner_id,
                    "owner_label": owner_label,
                    "schema": schema,
                    "development": development,
                },
            },
        ).get("addDataView")

    def list_dataviews(self, project_id: str) -> Optional[list]:
        return (
            self._gql_req(
                query=f"""
            query ListDataViews($id: String!) {{
                project(id: $id) {{
                    data_views {{
                      {self.dataview_fragment}
                    }}
                    jobs {{
                        {self.job_fragment}
                    }}
                }}
            }}
            """,
                variables={"id": project_id},
            )
            .get("project", {})
            .get("data_views")
        )

    def get_dataview(
        self, project_id: str, dataview_id: str = None, uri: str = None
    ) -> Optional[dict]:
        if not dataview_id and not uri:
            raise Exception("Required identifier id or uri not specified.")
        return (
            self._gql_req(
                query=f"""
            query GetDataView($id: String, $project_id: String, $uri: String) {{
                project(id: $project_id) {{
                    data_views(id: $id, uri: $uri) {{
                      {self.dataview_fragment}
                    }}
                    jobs {{
                        {self.job_fragment}
                    }}
                }}
            }}
            """,
                variables={"project_id": project_id, "id": dataview_id, "uri": uri},
            )
            .get("project", {})
            .get("data_views")
        )

    def delete_dataview(self, id: str) -> dict:
        return self._gql_req(
            query="""
                mutation RemoveDataView($id: String!) {
                    removeDataView(id: $id) {
                        id
                    }
                }
                """,
            variables={"id": id},
        ).get("removeDataView", {})

    def create_job(self, project_id: str, job_type: str, task_config: str) -> dict:
        return self._gql_req(
            query="""
            mutation CreateTask($project_id: String!, $task_type: TaskType!, $task_config: TaskConfigInput) {
                createTask(project_id: $project_id, task_type: $task_type, task_config: $task_config) {
                  id
                }
            }
            """,
            variables={
                "project_id": project_id,
                "task_type": job_type,
                "task_config": task_config,
            },
        ).get("createTask", {})

    def approve_job(self, job_id: str, org_id: str) -> dict:
        return self._gql_req(
            query=f"""
            mutation ApproveJob($job_id: String!, $organization_id: String!) {{
                approveJob(job_id: $job_id, organization_id: $organization_id) {{
                    {self.job_fragment}
                }}
            }}
            """,
            variables={"job_id": job_id, "organization_id": org_id},
        ).get("approveJob", {})

    def submit_job(self, job_id: str) -> dict:
        return self._gql_req(
            query=f"""
                    mutation InitializeSession($task_id: String!) {{
                        initializeSession(task_id: $task_id) {{
                            {self.job_fragment}
                        }}
                    }}
                    """,
            variables={"task_id": job_id},
        ).get("initializeSession", {})

    def get_job(
        self, project_id: str, job_id: str, return_params: str
    ) -> Optional[dict]:
        return (
            self._gql_req(
                query=f"""
            query GetJob($project_id: String! $job_id: String!) {{
                project(id: $project_id) {{
                  job(id: $job_id) {{
                    {self.job_fragment}
                    {return_params}
                  }}
                }}
            }}
            """,
                variables={"project_id": project_id, "job_id": job_id},
            )
            .get("project", {})
            .get("job")
        )

    def list_jobs(self, project_id: str) -> Optional[dict]:
        return (
            self._gql_req(
                query=f"""
            query ListJobs($project_id: String!) {{
                project(id: $project_id) {{
                  jobs {{
                    {self.job_fragment}
                  }}
                }}
            }}
            """,
                variables={"project_id": project_id},
            )
            .get("project", {})
            .get("jobs")
        )

    def me(self):
        return self._gql_req(
            query="""
        query Me {
            me {
                __typename
                ... on MeResponse {
                    user {
                        id
                        email
                        name
                    }
                }

                ... on UnverifiedError {
                    message
                }
            }
        }
            """,
            variables=None,
        ).get("me", {})
