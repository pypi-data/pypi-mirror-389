from __future__ import annotations

import json
from enum import Enum
from http import HTTPStatus
from typing import Any, Optional
from xml.etree import ElementTree

import requests

from dbnl import __version__ as version
from dbnl import config
from dbnl.errors import (
    DBNLAPIError,
    DBNLAPIValidationError,
    DBNLAuthenticationError,
    DBNLConnectionError,
    DBNLDuplicateError,
    DBNLResourceNotFoundError,
    DBNLResponseParsingError,
)


class ResourceName(Enum):
    LLM_MODELS = "llm_models"
    NAMESPACES = "namespaces"
    METRICS = "metrics"
    NOTIFICATION_INTEGRATIONS = "notification_integrations"
    NOTIFICATION_RULES = "notification_rules"
    ORG = "org"
    PROJECTS = "projects"
    RUNS = "runs"
    USERS = "users"


ORG_RESOURCES = {
    ResourceName.NAMESPACES.value,
    ResourceName.ORG.value,
    ResourceName.USERS.value,
}


def is_namespaced(resource_name: str) -> bool:
    resource_base = resource_name.split("/", 1)[0]
    return resource_base not in ORG_RESOURCES


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token: str) -> None:
        self.token = token

    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:
        r.headers["authorization"] = "Bearer " + self.token
        return r


def _request(
    method: str,
    path: str,
    query_params: Optional[dict[str, Any]],
    json_payload: Optional[dict[str, Any]],
) -> requests.Response:
    """Extracted out for testing purposes."""
    api_url = config.api_url().rstrip("/")
    url = f"{api_url}/v0/{path}"
    if is_namespaced(path) and config.namespace_id():
        if query_params is None:
            query_params = {}
        query_params["namespace_id"] = config.namespace_id()
    try:
        response = requests.request(
            method,
            url=url,
            params=query_params,
            auth=BearerAuth(config.api_token()),
            json=json_payload,
            headers={"User-Agent": f"dbnl/{version}"},
            timeout=10,
        )
    except requests.exceptions.RequestException as re:
        raise DBNLConnectionError(url, str(re)) from re
    return response


def request(
    method: str,
    path: str,
    query_params: Optional[dict[str, Any]] = None,
    json_payload: Optional[dict[str, Any]] = None,
) -> requests.Response:
    """Make an API request."""
    return _request(method, path, query_params, json_payload)


def get(resource: ResourceName, id: str) -> dict[str, Any]:
    """Get a single resource."""
    response = _request("GET", f"{resource.value}/{id}", None, None)
    return parse_response(response)


def get_by_name(resource: ResourceName, name: str) -> dict[str, Any]:
    """Get a single resource by name."""
    response = _request("GET", resource.value, {"name": name}, None)
    return parse_query_response(response)


def list_(resource: ResourceName, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    """List a resource."""
    response = _request("GET", resource.value, params, None)
    return parse_query_response_list(response)


def create(resource: ResourceName, json: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Create a resource."""
    response = _request("POST", resource.value, None, json)
    return parse_response(response)


def update(resource: ResourceName, id: str, json: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Update a resource."""
    response = _request("PATCH", f"{resource.value}/{id}", None, json)
    return parse_response(response)


def delete(resource: ResourceName, id: str) -> None:
    """Delete a resource."""
    response = _request("DELETE", f"{resource.value}/{id}", None, None)
    parse_response(response)


def parse_response(response: requests.Response) -> dict[str, Any]:
    if response.status_code == HTTPStatus.OK:
        try:
            return dict(json.loads(response.text))
        except json.JSONDecodeError as e:
            raise DBNLResponseParsingError(f"Failed to parse response content: {response.text}") from e
    elif response.status_code == HTTPStatus.NO_CONTENT:
        return {}
    elif response.status_code == HTTPStatus.BAD_REQUEST:
        try:
            resp_data = json.loads(response.text)
        except json.JSONDecodeError as e:
            raise DBNLResponseParsingError(f"Failed to parse response content: {response.text}") from e
        if isinstance(resp_data, dict):
            code = resp_data.get("code")
            message = resp_data.get("message")
            if code is not None:
                if code.startswith("duplicate"):
                    raise DBNLDuplicateError(response.text)
                if (
                    code == "invalid_data"
                    and isinstance(message, dict)
                    and isinstance(error_info := message.get("json"), dict)
                ):
                    raise DBNLAPIValidationError(error_info)
        raise DBNLAPIError(response)
    elif response.status_code == HTTPStatus.NOT_FOUND:
        raise DBNLResourceNotFoundError(response.text)
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise DBNLAuthenticationError()
    else:
        raise DBNLAPIError(response)


def parse_query_response(response: requests.Response) -> dict[str, Any]:
    parsed_response = parse_response(response)
    if len(parsed_response["data"]) == 0:
        raise DBNLResourceNotFoundError()
    return dict(parsed_response["data"][0])


def parse_query_response_list(response: requests.Response) -> list[dict[str, Any]]:
    parsed_response = parse_response(response)
    # response with 0 items is not an error
    return list(parsed_response["data"])


def parse_error_from_xml(response: requests.Response) -> str | None:
    try:
        response_xml = ElementTree.fromstring(response.text)
    except ElementTree.ParseError:
        return None
    ecode_elem = response_xml.find(".//Code")
    emessage_elem = response_xml.find(".//Message")
    if ecode_elem is None or emessage_elem is None:
        response.raise_for_status()
    assert ecode_elem is not None  # for type checker
    assert emessage_elem is not None  # for type checker
    error_code = ecode_elem.text
    error_message = emessage_elem.text
    return f"{error_code}: {error_message}"
