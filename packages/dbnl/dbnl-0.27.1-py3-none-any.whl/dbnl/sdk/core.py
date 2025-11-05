from __future__ import annotations

import re
import time
import warnings
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Literal, Optional, TypeVar

import pandas as pd
import pyarrow as pa
from typing_extensions import ParamSpec

from dbnl import api, config
from dbnl.errors import (
    DBNLConflictingProjectError,
    DBNLDuplicateError,
    DBNLInputValidationError,
    DBNLInvalidDataError,
    DBNLNotLoggedInError,
    DBNLProjectNotFoundError,
    DBNLResourceNotFoundError,
    DBNLRunError,
    DBNLRunNotFoundError,
    DBNLUnsupportedDataTypeError,
    WaitTimeoutError,
)
from dbnl.logging import logger
from dbnl.sdk import semconv
from dbnl.sdk.models import LLMModel, Metric, Project, Run
from dbnl.sdk.spans import convert_otlp_traces_data
from dbnl.sdk.types import Field, Schema, from_arrow
from dbnl.sdk.util import generate_app_url


def login(
    *,
    api_token: Optional[str] = None,
    namespace_id: Optional[str] = None,
    api_url: Optional[str] = None,
    app_url: Optional[str] = None,
    verify: bool = True,
) -> None:
    """
    Setup dbnl SDK to make authenticated requests. After login is run successfully, the dbnl client
    will be able to issue secure and authenticated requests against hosted endpoints of the dbnl service.


    :param api_token: dbnl API token for authentication; token can be found at /tokens page of the dbnl app.
        If None is provided, the environment variable `DBNL_API_TOKEN` will be used by default.
    :param namespace_id: The namespace ID to use for the session.
    :param api_url: The base url of the Distributional API. For SaaS users, set this variable to api.dbnl.com.
        For other users, please contact your sys admin. If None is provided, the environment variable `DBNL_API_URL` will be used by default.
    :param app_url: An optional base url of the Distributional app. If this variable is not set, the app url is inferred from the DBNL_API_URL
        variable. For on-prem users, please contact your sys admin if you cannot reach the Distributional UI.
    """
    config.load(
        api_token=api_token,
        api_url=api_url,
        app_url=app_url,
        namespace_id=namespace_id,
    )
    logger.setLevel(config.log_level())
    if verify:
        api.ensure_valid_token()
        api.maybe_warn_invalid_version()
        if namespace_id is not None:
            api.ensure_valid_namespace()


T = TypeVar("T")
P = ParamSpec("P")


def validate_login(func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator to validate that the user has logged in before making a request
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        if not config.loaded():
            raise DBNLNotLoggedInError()
        return func(*args, **kwargs)

    return wrapper


@validate_login
def log(
    *,
    project_id: str,
    data: pd.DataFrame,
    data_start_time: datetime,
    data_end_time: datetime,
    wait_timeout: Optional[float] = 600,
) -> None:
    """
    Log data for a date range to a project.

    :param project: The Project id to send the logs to.
    :param data: Pandas DataFrame with the data.
    :param data_start_time: Data start date.
    :param data_end_time: Data end time.
    :param wait_timeout: If set, the function will block for up to `wait_timeout` seconds until the
        data is done processing, defaults to 10 minutes.

    :raises DBNLNotLoggedInError: dbnl SDK is not logged in
    :raises DBNLInputValidationError: Input does not conform to expected format

    #### Examples:

    .. code-block:: python

        from datetime import datetime, UTC

        import dbnl
        import pandas as pd

        dbnl.login()

        proj = dbnl.get_or_create_project(name="test")
        test_data = pd.DataFrame(
            {"timestamp": [datetime(2025, 1, 1, 11, 39, 53, tzinfo=UTC)]}
            {"input": ["Hello"]}
            {"output": ["World"]}
        )

        run = dbnl.log(
            project=proj,
            column_data=test_data,
            data_start_time=datetime(2025, 1, 1, tzinfo=UTC),
            data_end_time=datetime(2025, 1, 2, tzinfo=UTC),
        )
    """
    required_columns = [semconv.Columns.TIMESTAMP, semconv.Columns.INPUT, semconv.Columns.OUTPUT]
    for c in required_columns:
        if c.value not in data.columns:
            raise DBNLInvalidDataError(f"DataFrame is missing required '{c.value}' column")

    data = _convert_traces_data(data)
    schema = _get_schema_from_dataframe(data)
    data = _cast_dataframe(data, schema)
    _check_timestamp(data, data_start_time, data_end_time)
    run = _create_run(project_id, schema, data_start_time, data_end_time)
    api.post_results(run.id, data)
    _close_run(run.id, wait_timeout)


def _get_schema_from_dataframe(data: pd.DataFrame) -> Schema:
    fields = []
    for f in pa.Schema.from_pandas(data):
        field = semconv.field(f.name)
        if field is not None:
            # If field is in semconv, force semconv type.
            fields.append(field)
        else:
            # Otherwise, infer type.
            try:
                fields.append(Field(f.name, from_arrow(f.type)))
            except ValueError as e:
                raise DBNLUnsupportedDataTypeError(f"Unsupported field '{f.name}' with type '{f.type}'") from e
    return Schema(fields=fields)


def _check_timestamp(data: pd.DataFrame, data_start_time: datetime, data_end_time: datetime) -> None:
    timestamp_column = semconv.Columns.TIMESTAMP.value
    if timestamp_column not in data.columns:
        raise DBNLInvalidDataError(f"DataFrame is missing required '{timestamp_column}' column")
    if data.empty:
        return
    if data[timestamp_column].isnull().any():
        raise DBNLInvalidDataError(f"DataFrame contains null values in '{timestamp_column}' column")
    if data[timestamp_column].min() < data_start_time:
        raise DBNLInvalidDataError(
            f"DataFrame contains timestamps before data_start_time: {data[timestamp_column].min()} < {data_start_time.isoformat()}"
        )
    if data[timestamp_column].max() >= data_end_time:
        raise DBNLInvalidDataError(
            f"DataFrame contains timestamps after or equal to data_end_time: {data[timestamp_column].max()} >= {data_end_time.isoformat()}"
        )


def _convert_traces_data(data: pd.DataFrame) -> pd.DataFrame:
    if not "traces_data" in data.columns:
        return data
    if "spans" in data.columns:
        warnings.warn("DataFrame contains both `traces_data` and `spans` columns. `spans` column will be used.")
        return data.drop("traces_data", axis=1)
    data["spans"] = convert_otlp_traces_data(data["traces_data"])
    return data.drop("traces_data", axis=1)


def _cast_dataframe(data: pd.DataFrame, schema: Schema) -> pd.DataFrame:
    try:
        return data.astype(schema.to_pandas())
    except ValueError as e:
        m = re.search("Error while type casting for column '(\w+)'", str(e))
        if m is not None and len(m.groups()) == 1:
            col = m.groups()[0]
            f = schema.field(col)
            if f is not None:
                raise DBNLInvalidDataError(f"Expected '{col}' with type '{f.type}': {str(e)}") from e
        raise DBNLInvalidDataError(str(e)) from e


def _create_run(
    project_id: str,
    schema: Schema,
    data_start_time: Optional[datetime],
    data_end_time: Optional[datetime],
) -> Run:
    resp_dict = api.create_run(
        project_id=project_id,
        run_schema={
            "columns": [
                {
                    "name": f.name,
                    "type": f.type.to_json_value(),
                }
                for f in schema.fields
            ]
        },
        data_start_time=data_start_time,
        data_end_time=data_end_time,
    )
    return Run.from_dict(resp_dict)


def _get_run(run_id: str) -> Run:
    try:
        resp_dict = api.get_run(run_id=run_id)
    except DBNLResourceNotFoundError:
        raise DBNLRunNotFoundError(run_id)
    return Run.from_dict(resp_dict)


def _close_run(
    run_id: str,
    wait_timeout: Optional[float] = 600,
) -> Run:
    resp_dict = api.close_run(run_id=run_id)
    run = Run.from_dict(resp_dict)
    logger.info(
        "Initiated run close. View results at: %s",
        generate_app_url(f"ns/{run.namespace_id}/projects/{run.project_id}/status"),
    )
    if wait_timeout is not None:
        return _wait_for_run_close(run_id=run_id, timeout=wait_timeout)
    return run


def _wait_for_run_close(run_id: str, timeout: float = 600, polling_interval: float = 5) -> Run:
    logger.info("Waiting for run to close...")
    start = time.time()
    run = _get_run(run_id=run_id)
    while run.completed_at is None and (time.time() - start) < timeout:
        time.sleep(polling_interval)
        run = _get_run(run_id=run_id)
    if run.completed_at is None:
        project_status_url = generate_app_url(f"ns/{run.namespace_id}/projects/{run.project_id}/status")
        raise WaitTimeoutError(
            f"Run [{run.data_start_time}-{run.data_end_time}] hasn't finished after waiting for {timeout} seconds."
            f" See {project_status_url} to check on run status and consider extending or removing `wait_timeout` to prevent this exception from being thrown."
        )
    if run.status != "closed":
        raise DBNLRunError(f"Run {run} ended in '{run.status}' state: {run.failure}")
    logger.info("Run closed successfully")
    return run


@validate_login
def get_project(
    *,
    name: str,
) -> Project:
    """
    Retrieve a Project by name.

    :param name: The name for the existing Project.

    :raises DBNLNotLoggedInError: dbnl SDK is not logged in
    :raises DBNLProjectNotFoundError: Project with the given name does not exist.

    :return: Project

    #### Examples:

    .. code-block:: python

        import dbnl

        dbnl.login()

        proj_1 = dbnl.create_project(name="test_p1")
        proj_2 = dbnl.get_project(name="test_p1")

        # Calling get_project will yield same Project object
        assert proj_1.id == proj_2.id

        # DBNLProjectNotFoundError: A dnnl Project with name not_exist does not exist
        proj_3 = dbnl.get_project(name="not_exist")
    """
    try:
        resp_dict = api.get_project_by_name(name=name)
    except DBNLResourceNotFoundError:
        raise DBNLProjectNotFoundError(name)

    return Project.from_dict(resp_dict)


@validate_login
def create_project(
    *,
    name: str,
    description: Optional[str] = None,
    schedule: Optional[Literal["daily", "hourly"]] = "daily",
    default_llm_model_id: Optional[str] = None,
    default_llm_model_name: Optional[str] = None,
    template: Optional[Literal["default"]] = "default",
) -> Project:
    """
    Create a new Project

    :param name: Name for the Project
    :param description: Description for the Project, defaults to None. Description is limited to 255 characters.

    :raises DBNLNotLoggedInError: dbnl SDK is not logged in
    :raises DBNLAPIValidationError: dbnl API failed to validate the request
    :raises DBNLConflictingProjectError: Project with the same name already exists

    :return: Project

    #### Examples:

    .. code-block:: python

        import dbnl

        dbnl.login()

        proj_1 = dbnl.create_project(name="test_p1")

        # DBNLConflictingProjectError: A Project with name test_p1 already exists.
        proj_2 = dbnl.create_project(name="test_p1")
    """
    if default_llm_model_id is not None and default_llm_model_name is not None:
        raise DBNLInputValidationError("Only one of llm_model_id and llm_model_name can be provided")

    if default_llm_model_name is not None:
        default_llm_model_id = get_llm_model_by_name(name=default_llm_model_name).id

    try:
        resp_dict = api.create_project(
            name=name,
            description=description,
            schedule=schedule,
            default_llm_model_id=default_llm_model_id,
            template=template,
        )
    except DBNLDuplicateError:
        raise DBNLConflictingProjectError(name)

    project = Project.from_dict(resp_dict)

    logger.info(
        "View Project %s at: %s",
        project.name,
        generate_app_url(f"ns/{project.namespace_id}/projects/{project.id}"),
    )

    return project


@validate_login
def get_or_create_project(
    *,
    name: str,
    description: Optional[str] = None,
    schedule: Optional[Literal["daily", "hourly"]] = "daily",
    default_llm_model_id: Optional[str] = None,
    default_llm_model_name: Optional[str] = None,
    template: Optional[Literal["default"]] = "default",
) -> Project:
    """
    Get the Project with the specified name or create a new one if it does not exist

    :param name: Name for the Project
    :param description: Description for the Project, defaults to None

    :raises DBNLNotLoggedInError: dbnl SDK is not logged in
    :raises DBNLAPIValidationError: dbnl API failed to validate the request

    :return: Newly created or matching existing Project

    #### Examples:

    .. code-block:: python

        import dbnl

        dbnl.login()

        proj_1 = dbnl.create_project(name="test_p1")
        proj_2 = dbnl.get_or_create_project(name="test_p1")

        # Calling get_or_create_project will yield same Project object
        assert proj_1.id == proj_2.id
    """

    try:
        return get_project(name=name)
    except DBNLProjectNotFoundError:
        try:
            return create_project(
                name=name,
                description=description,
                schedule=schedule,
                default_llm_model_id=default_llm_model_id,
                default_llm_model_name=default_llm_model_name,
                template=template,
            )
        except DBNLConflictingProjectError:
            return get_project(name=name)


@validate_login
def create_metric(
    *,
    project: Project,
    name: str,
    expression_template: str,
    description: Optional[str] = None,
    greater_is_better: Optional[bool] = None,
) -> Metric:
    """
    Create a new Metric

    :param project: The Project to create the Metric for
    :param name: Name for the Metric
    :param expression_template: Expression template string e.g. `token_count({RUN}.question)`
    :param description: Optional description of what computation the metric is performing
    :param greater_is_better: Flag indicating whether greater values are semantically 'better' than lesser values

    :raises DBNLNotLoggedInError: dbnl SDK is not logged in
    :raises DBNLInputValidationError: Input does not conform to expected format

    :return: Created Metric
    """
    resp_dict = api.create_metric(
        project_id=project.id,
        name=name,
        expression_template=expression_template,
        description=description,
        greater_is_better=greater_is_better,
    )
    return Metric.from_dict(resp_dict)


@validate_login
def delete_metric(
    *,
    metric_id: str,
) -> None:
    """
    Delete a Metric by ID

    :param metric_id: ID of the metric to delete

    :raises DBNLNotLoggedInError: dbnl SDK is not logged in
    :raises DBNLAPIValidationError: dbnl API failed to validate the request

    :return: None
    """
    api.delete_metric(metric_id=metric_id)


@validate_login
def get_metric(
    *,
    metric_id: str,
) -> Metric:
    """
    Get a Metric by ID

    :param metric_id: ID of the metric to get

    :raises DBNLNotLoggedInError: dbnl SDK is not logged in
    :raises DBNLAPIValidationError: dbnl API failed to validate the request

    :return: The requested metric
    """
    resp_dict = api.get_metric(metric_id=metric_id)
    return Metric.from_dict(resp_dict)


@validate_login
def get_or_create_llm_model(
    *,
    name: str,
    description: Optional[str] = None,
    type: Optional[Literal["completion", "embedding"]] = "completion",
    provider: str,
    model: str,
    params: dict[str, Any] = {},
) -> LLMModel:
    """
    Get an LLM Model by name, or create it if it does not exist.

    :param name: Model name
    :param description: Model description, defaults to None
    :param type: Model type (e.g. completion or embedding), defaults to "completion"
    :param provider: Model provider (e.g. openai, bedrock, etc.)
    :param model: Model (e.g. gpt-4, gpt-3.5-turbo, etc.)
    :param params: Model provider parameters (e.g. api key), defaults to {}
    :return: Model
    """
    try:
        return get_llm_model_by_name(name=name)
    except DBNLResourceNotFoundError:
        return create_llm_model(
            name=name,
            description=description,
            type=type,
            provider=provider,
            model=model,
            params=params,
        )


@validate_login
def create_llm_model(
    *,
    name: str,
    description: Optional[str] = None,
    type: Optional[Literal["completion", "embedding"]] = "completion",
    provider: str,
    model: str,
    params: dict[str, Any] = {},
) -> LLMModel:
    """
    Create an LLM Model.

    :param name: Model name
    :param description: Model description, defaults to None
    :param type: Model type (e.g. completion or embedding), defaults to "completion"
    :param provider: Model provider (e.g. openai, bedrock, etc.)
    :param model: Model (e.g. gpt-4, gpt-3.5-turbo, etc.)
    :param params: Model provider parameters (e.g. api key), defaults to {}
    :return: Model
    """
    resp = api.create_llm_model(
        name=name,
        description=description,
        type=type,
        provider=provider,
        model=model,
        params=params,
    )
    return LLMModel.from_dict(resp)


@validate_login
def get_llm_model_by_name(
    *,
    name: str,
) -> LLMModel:
    """
    Get an LLM Model by name

    :param name: Model name
    :return: Model if found
    """
    resp = api.list_llm_models(name=name)
    if not resp:
        raise DBNLResourceNotFoundError(f"LLM Model with name '{name}' not found")
    return LLMModel.from_dict(resp[0])


@validate_login
def get_llm_model(
    *,
    llm_model_id: str,
) -> LLMModel:
    """
    Get an LLM Model by id.

    :param llm_model_id: Model id
    :return: Model if found
    """
    resp = api.get_llm_model(llm_model_id=llm_model_id)
    return LLMModel.from_dict(resp)


@validate_login
def update_llm_model(
    *,
    llm_model_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    model: Optional[str] = None,
    params: Optional[dict[str, Any]] = None,
) -> LLMModel:
    """
    Update an LLM Model by id.

    :param llm_model_id: Model id
    :param name: Model name
    :param description: Model description, defaults to None
    :param model: Model (e.g. gpt-4, gpt-3.5-turbo, etc.)
    :param params: Model provider parameters (e.g. api key), defaults to {}
    :return: Updated Model
    """
    resp = api.update_llm_model(
        llm_model_id=llm_model_id,
        name=name,
        description=description,
        model=model,
        params=params,
    )
    return LLMModel.from_dict(resp)


@validate_login
def delete_llm_model(
    *,
    llm_model_id: str,
) -> None:
    """
    Delete an LLM Model by id.

    :param llm_model_id: Model id
    :return: Model if found
    """
    api.delete_llm_model(llm_model_id=llm_model_id)
