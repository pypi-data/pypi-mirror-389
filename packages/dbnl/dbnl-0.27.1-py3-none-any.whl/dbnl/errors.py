import json
from typing import Any, Optional

import yaml
from requests import Response


class DBNLError(Exception):
    pass


class DBNLInputValidationError(DBNLError):
    """An error that occurs when the DBNL SDK input does not conform to the expected format."""


class DBNLAPIError(DBNLError):
    """An error that occurs when the DBNL API was contacted successfully, but it responded with an error."""

    def __init__(self, response: Response) -> None:
        self.response = response
        self.status_code = response.status_code
        self.code = None
        self.message = None
        try:
            data = json.loads(response.text)
            if isinstance(data, dict):
                self.code = data.get("code", None)
                self.message = data.get("message", None)
        except json.JSONDecodeError:
            pass
        msg = f"An error returned by DBNL API ({self.status_code}):"
        if self.code:
            msg += f" {self.code}:"
        msg += f" {self.message or 'unknown'}"
        super().__init__(msg)


def _sanitize_key(key: str) -> str:
    if key.isnumeric():
        return f"index_{key}"
    return key


def _recursively_sanitize(err_data: Any) -> Any:
    if isinstance(err_data, dict):
        if len(err_data) == 1 and "_schema" in err_data:
            # NOTE: Technically a user might have a key named "_schema" but it's unlikely.
            # In the even that they do, the error message will be slightly incorrect.
            return err_data["_schema"]
        return {_sanitize_key(k): _recursively_sanitize(v) for k, v in err_data.items()}
    if isinstance(err_data, list):
        return [_recursively_sanitize(v) for v in err_data]
    return err_data


def _prettify_error_info(error_content: dict[str, Any]) -> str:
    error_content = _recursively_sanitize(error_content)
    return yaml.safe_dump(error_content)


class DBNLAPIValidationError(DBNLError):
    """An error that occurs when the DBNL API was contacted successfully, but it responded with a validation error."""

    def __init__(self, error_content: dict[str, list[str]]) -> None:
        message = "The DBNL API failed to validate the request.\n"
        message += _prettify_error_info(error_content)
        super().__init__(message)
        self.error_content = error_content


class DBNLDuplicateError(DBNLError):
    """An error that occurs when trying to create a duplicate DBNL object."""


class DBNLConnectionError(DBNLError):
    """An error that occurs when unable to contact DBNL API endpoints."""

    def __init__(self, url: str, error_message: str) -> None:
        self.message = " ".join([
            f"An error occurred connecting to {url}.",
            "Contact support@distributional.com for assistance.",
            error_message,
        ])
        super().__init__(self.message)


class DBNLAuthenticationError(DBNLError):
    def __init__(self, msg: Optional[str] = None, *args: Any) -> None:
        if not msg:
            msg = " ".join([
                "Error, could not login. Please make sure your DBNL_API_TOKEN environment variable is set and is correct."
            ])
        super().__init__(msg, *args)


class DBNLNotLoggedInError(DBNLError):
    def __init__(self, msg: Optional[str] = None, *args: Any) -> None:
        if not msg:
            msg = "You are currently not logged in to DBNL. Please run dbnl.login() before running other parts of your workflow"
        super().__init__(msg, *args)


class DBNLResourceNotFoundError(DBNLError):
    """An error that occurs when the DBNL object cannot be returned from the API."""


class DBNLConflictingProjectError(DBNLError):
    def __init__(self, project_name: str) -> None:
        self.message = f"A DBNL Project with name {project_name} already exists. Try dbnl.get_project(name='{project_name}') to fetch the project."
        super().__init__(self.message)


class DBNLProjectNotFoundError(DBNLResourceNotFoundError):
    def __init__(self, project_name: str) -> None:
        self.message = f"A DBNL Project with name {project_name} does not exist."
        super().__init__(self.message)


class DBNLRunNotFoundError(DBNLResourceNotFoundError):
    def __init__(self, run_id: str) -> None:
        self.message = f"A DBNL Run with id {run_id} does not exist."
        if run_id == "latest":
            self.message = "No DBNL Runs exist for this Project."
        super().__init__(self.message)


class DBNLRunNotUploadableError(DBNLError):
    def __init__(self, run_id: str) -> None:
        super().__init__(f"Run {run_id} is not uploadable. Run must in the `PENDING` state to upload results.")
        self.run_id = run_id


class DBNLUploadResultsError(DBNLError):
    def __init__(self, run_id: str, error_detail: str, url: str) -> None:
        super().__init__(
            f"An error occurred uploading Results for Run `{run_id}` to DBNL.\n"
            f"{error_detail}\n"
            f"The url being used to upload the results is {url}",
        )
        self.run_id = run_id
        self.error_detail = error_detail
        self.url = url


class DBNLRunError(DBNLError):
    """An error that occurs when a run ends in an ERRORED state."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class DBNLConfigurationError(DBNLError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class DBNLUnsupportedDataTypeError(DBNLError):
    """An error that occurs when an unsupported data type is used in DBNL."""


class DBNLInvalidDataError(DBNLError):
    """An error that occurs when invalid data is used in DBNL."""


class DBNLResponseParsingError(DBNLError):
    """An error that occurs when the response from the DBNL API cannot be parsed."""


class WaitTimeoutError(DBNLError):
    """When timeout waiting for a run to complete but the run is still in progress."""
