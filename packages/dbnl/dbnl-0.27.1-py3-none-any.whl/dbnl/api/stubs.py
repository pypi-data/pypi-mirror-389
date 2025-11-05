from __future__ import annotations

import json
import warnings
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Literal, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests

from dbnl import config
from dbnl.api.util import (
    ResourceName,
    create,
    delete,
    get,
    get_by_name,
    list_,
    parse_error_from_xml,
    parse_query_response,
    parse_response,
    request,
    update,
)
from dbnl.api.version import check_version_compatibility
from dbnl.errors import (
    DBNLConfigurationError,
    DBNLRunNotUploadableError,
    DBNLUploadResultsError,
)
from dbnl.warnings import DBNLAPIIncompatibilityWarning


def get_spec() -> dict[str, Any]:
    response = request("GET", "spec.json")
    return parse_response(response)


def maybe_warn_invalid_version() -> None:
    response = request("GET", "spec.json")
    if response.status_code != 200:
        warnings.warn(
            f"Failed to fetch OpenAPI spec: {response.status_code}. Cannot validate API version compatability with SDK.",
            DBNLAPIIncompatibilityWarning,
        )
        return
    try:
        spec = json.loads(response.text)
        api_version = spec.get("info", {}).get("version")
        check_version_compatibility(api_version)
    except json.JSONDecodeError:
        warnings.warn(
            "Failed to parse OpenAPI spec. Cannot validate API version compatability with SDK.",
            DBNLAPIIncompatibilityWarning,
        )


def ensure_valid_token() -> None:
    data = parse_response(request("GET", "users/me"))
    # A bad DBNL_API_URL may still return a 200. Sanity check the response.
    if not "id" in data:
        raise DBNLConfigurationError(
            "Failed to validate user token against the dbnl API. Likely your DBNL_API_URL is incorrect. "
            f"Current value is {config.api_url()}"
        )


def ensure_valid_namespace() -> None:
    parse_response(request("GET", "projects"))


def get_me() -> dict[str, Any]:
    response = request("GET", "users/me")
    return parse_response(response)


def get_default_namespace() -> dict[str, Any]:
    response = request("GET", "namespaces", query_params={"is_default": True})
    return parse_query_response(response)


#
# Projects endpoints.
#


def create_project(
    name: str,
    description: Optional[str] = None,
    schedule: Optional[Literal["daily", "hourly"]] = "daily",
    default_llm_model_id: Optional[str] = None,
    template: Optional[Literal["default"]] = "default",
) -> dict[str, Any]:
    json_payload = {"name": name}
    if description is not None:
        json_payload.update({"description": description})
    if schedule is not None:
        json_payload.update({"schedule": schedule})
    if default_llm_model_id is not None:
        json_payload.update({"default_llm_model_id": default_llm_model_id})
    if template is not None:
        json_payload.update({"template": template})
    return create(ResourceName.PROJECTS, json=json_payload)


def get_project_by_name(name: str) -> dict[Any, Any]:
    return get_by_name(ResourceName.PROJECTS, name)


#
# Runs endpoints.
#


def create_run(
    project_id: str,
    run_schema: dict[str, Any],
    data_start_time: Optional[datetime] = None,
    data_end_time: Optional[datetime] = None,
) -> dict[str, Any]:
    json_payload: dict[str, Any] = {
        "project_id": project_id,
        "schema": run_schema,
    }
    if data_start_time is not None:
        json_payload.update({"data_start_time": data_start_time.isoformat()})
    if data_end_time is not None:
        json_payload.update({"data_end_time": data_end_time.isoformat()})
    return create(ResourceName.RUNS, json=json_payload)


def get_run(run_id: str) -> dict[Any, Any]:
    return get(ResourceName.RUNS, run_id)


def generate_run_upload_url(*, run_id: str) -> dict[str, Any]:
    response = request("POST", f"runs/{run_id}/generate_upload_url")
    if response.status_code == 400 and json.loads(response.text).get("code") == "run_not_uploadable":
        raise DBNLRunNotUploadableError(run_id)
    return parse_response(response)


def close_run(run_id: str) -> dict[Any, Any]:
    response = request("POST", f"runs/{run_id}/close")
    return parse_response(response)


def post_results(run_id: str, data: pd.DataFrame) -> None:
    upload_details = generate_run_upload_url(run_id=run_id)
    # Write DataFrame to memory buffer as parquet
    table = pa.Table.from_pandas(data, preserve_index=False)
    data_buffer = pa.BufferOutputStream()
    pq.write_table(table, data_buffer)

    # GCS requires PUT method and uploads raw data rather than POST + files
    files: Mapping[str, pa.lib.Buffer] | None
    if upload_details["method"] == "PUT" and not upload_details["data"]:
        upload_details["data"] = data_buffer.getvalue()
        files = None
    else:
        files = {"file": data_buffer.getvalue()}

    response = requests.request(
        method=upload_details["method"],
        url=upload_details["url"],
        data=upload_details["data"],
        files=files,  # type: ignore[arg-type]
        headers=upload_details["headers"],
    )

    if response.status_code >= 400:
        error_detail = parse_error_from_xml(response) or response.text

        raise DBNLUploadResultsError(
            run_id,
            error_detail,
            upload_details["url"],
        )


#
# Metrics endpoints.
#


def create_metric(
    project_id: str,
    name: str,
    expression_template: str,
    description: Optional[str] = None,
    greater_is_better: Optional[bool] = None,
) -> dict[str, Any]:
    json_payload: dict[str, Any] = {
        "project_id": project_id,
        "name": name,
        "expression_template": expression_template,
    }
    if description is not None:
        json_payload.update({"description": description})
    if greater_is_better is not None:
        json_payload.update({"greater_is_better": greater_is_better})
    return create(ResourceName.METRICS, json=json_payload)


def get_metric(metric_id: str) -> dict[str, Any]:
    return get(ResourceName.METRICS, metric_id)


def delete_metric(metric_id: str) -> None:
    delete(ResourceName.METRICS, metric_id)


#
# LLM models endpoints.
#


def create_llm_model(
    name: str,
    provider: str,
    model: str,
    description: Optional[str] = None,
    type: Optional[Literal["completion", "embedding"]] = "completion",
    params: dict[str, Any] = {},
) -> dict[str, Any]:
    json_payload: dict[str, Any] = {
        "name": name,
        "model": model,
        "provider": provider,
        "params": params,
        "type": type,
    }
    if description is not None:
        json_payload.update({"description": description})
    return create(ResourceName.LLM_MODELS, json=json_payload)


def get_llm_model(llm_model_id: str) -> dict[str, Any]:
    return get(ResourceName.LLM_MODELS, llm_model_id)


def update_llm_model(
    llm_model_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    model: Optional[str] = None,
    params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    json_payload: dict[str, Any] = {}
    if name is not None:
        json_payload["name"] = name
    if model is not None:
        json_payload["model"] = model
    if params is not None:
        json_payload["params"] = params
    if description is not None:
        json_payload["description"] = description
    return update(ResourceName.LLM_MODELS, llm_model_id, json=json_payload)


def delete_llm_model(llm_model_id: str) -> None:
    return delete(ResourceName.LLM_MODELS, llm_model_id)


def list_llm_models(
    name: Optional[str] = None,
    type: Optional[Literal["completion", "embedding"]] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    if name is not None:
        params["name"] = name
    if model is not None:
        params["model"] = model
    if provider is not None:
        params["provider"] = provider
    if type is not None:
        params["type"] = type
    return list_(ResourceName.LLM_MODELS, params=params)


#
# Notification integrations endpoints.
#


def create_notification_integration(
    name: str,
    integration_type: str,
    integration_params: dict[str, Any],
    description: Optional[str] = None,
) -> dict[str, Any]:
    json_payload = {
        "name": name,
        "integration_type": integration_type,
        "integration_params": integration_params,
    }
    if description is not None:
        json_payload.update({"description": description})
    return create(ResourceName.NOTIFICATION_INTEGRATIONS, json=json_payload)


def get_notification_integration(notification_integration_id: str) -> dict[str, Any]:
    return get(ResourceName.NOTIFICATION_INTEGRATIONS, notification_integration_id)


def update_notification_integration(
    notification_integration_id: str,
    name: Optional[str] = None,
    integration_type: Optional[str] = None,
    integration_params: Optional[dict[str, Any]] = None,
    description: Optional[str] = None,
) -> dict[str, Any]:
    json_payload: dict[str, Any] = {}
    if name is not None:
        json_payload["name"] = name
    if integration_type is not None:
        json_payload["integration_type"] = integration_type
    if integration_params is not None:
        json_payload["integration_params"] = integration_params
    if description is not None:
        json_payload["description"] = description
    return update(ResourceName.NOTIFICATION_INTEGRATIONS, notification_integration_id, json=json_payload)


def delete_notification_integration(notification_integration_id: str) -> None:
    delete(ResourceName.NOTIFICATION_INTEGRATIONS, notification_integration_id)


def list_notification_integrations() -> list[dict[str, Any]]:
    return list_(ResourceName.NOTIFICATION_INTEGRATIONS)


#
# Notification rules endpoints.
#


def create_notification_rule(
    project_id: str,
    name: str,
    status: str,
    trigger: str,
    notification_integration_ids: list[str],
    conditions: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    json_payload: dict[str, Any] = {
        "project_id": project_id,
        "name": name,
        "status": status,
        "trigger": trigger,
        "notification_integration_ids": notification_integration_ids,
    }
    if conditions is not None:
        json_payload.update({"conditions": conditions})
    return create(ResourceName.NOTIFICATION_RULES, json=json_payload)


def get_notification_rule(notification_rule_id: str) -> dict[str, Any]:
    return get(ResourceName.NOTIFICATION_RULES, notification_rule_id)


def update_notification_rule(
    notification_rule_id: str,
    name: Optional[str] = None,
    status: Optional[str] = None,
    notification_integration_ids: Optional[list[str]] = None,
    conditions: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    json_payload: dict[str, Any] = {}
    if name is not None:
        json_payload["name"] = name
    if status is not None:
        json_payload["status"] = status
    if notification_integration_ids is not None:
        json_payload["notification_integration_ids"] = notification_integration_ids
    if conditions is not None:
        json_payload["conditions"] = conditions
    return update(ResourceName.NOTIFICATION_RULES, notification_rule_id, json=json_payload)


def delete_notification_rule(notification_rule_id: str) -> None:
    delete(ResourceName.NOTIFICATION_RULES, notification_rule_id)


def list_notification_rules(
    project_id: Optional[str] = None,
    notification_integration_id: Optional[str] = None,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    if project_id is not None:
        params["project_id"] = project_id
    if notification_integration_id is not None:
        params["notification_integration_id"] = notification_integration_id
    return list_(ResourceName.NOTIFICATION_RULES, params=params)
