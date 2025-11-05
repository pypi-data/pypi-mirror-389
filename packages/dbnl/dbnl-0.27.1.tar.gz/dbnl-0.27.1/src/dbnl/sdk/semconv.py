from enum import Enum
from typing import Union

from dbnl.sdk.spans import span_dtype
from dbnl.sdk.types import Category, DataType, Field, Float, Int, List, Map, Schema, String, TimestampTZ


class Columns(Enum):
    INPUT = "input"
    OUTPUT = "output"
    TIMESTAMP = "timestamp"
    SPANS = "spans"
    STATUS = "status"
    DURATION_MS = "duration_ms"
    SESSION_ID = "session_id"
    TRACE_ID = "trace_id"
    TOTAL_TOKEN_COUNT = "total_token_count"
    PROMPT_TOKEN_COUNT = "prompt_token_count"
    COMPLETION_TOKEN_COUNT = "completion_token_count"
    TOTAL_COST = "total_cost"
    PROMPT_COST = "prompt_cost"
    COMPLETION_COST = "completion_cost"
    TOOL_CALL_COUNT = "tool_call_count"
    TOOL_CALL_ERROR_COUNT = "tool_call_error_count"
    TOOL_CALL_NAME_COUNTS = "tool_call_name_counts"
    LLM_CALL_COUNT = "llm_call_count"
    LLM_CALL_ERROR_COUNT = "llm_call_error_count"
    LLM_CALL_MODEL_COUNTS = "llm_call_model_counts"
    FEEDBACK_SCORE = "feedback_score"
    FEEDBACK_TEXT = "feedback_text"


_SCHEMA = Schema(
    fields=[
        Field(
            name=Columns.INPUT.value,
            type=String(),
            description="The input to the AI app invocation.",
        ),
        Field(
            name=Columns.OUTPUT.value,
            type=String(),
            description="The output from the AI app invocation.",
        ),
        Field(
            name=Columns.TIMESTAMP.value,
            type=TimestampTZ(),
            nullable=False,
            description="The timestamp of the AI app invocation.",
        ),
        Field(
            name=Columns.SPANS.value,
            type=List(span_dtype()),
            description="The spans representing operations within the AI app invocation.",
        ),
        Field(
            name=Columns.STATUS.value,
            type=Category(),
            description="The status of the AI app invocation (e.g., Ok, Error).",
        ),
        Field(
            name=Columns.DURATION_MS.value,
            type=Int(),
            description="The duration of the AI app invocation in milliseconds.",
        ),
        Field(
            name=Columns.SESSION_ID.value,
            type=String(),
            description="The session ID associated with the AI app invocation.",
        ),
        Field(
            name=Columns.TRACE_ID.value,
            type=String(),
            description="The trace ID associated with the AI app invocation.",
        ),
        Field(
            name=Columns.TOTAL_TOKEN_COUNT.value,
            type=Int(),
            description="The total number of tokens used in the AI app invocation.",
        ),
        Field(
            name=Columns.PROMPT_TOKEN_COUNT.value,
            type=Int(),
            description="The number of prompt tokens used in the AI app invocation.",
        ),
        Field(
            name=Columns.COMPLETION_TOKEN_COUNT.value,
            type=Int(),
            description="The number of completion tokens used in the AI app invocation.",
        ),
        Field(
            name=Columns.TOTAL_COST.value,
            type=Float(),
            description="The total cost of the AI app invocation.",
        ),
        Field(
            name=Columns.PROMPT_COST.value,
            type=Float(),
            description="The cost of the prompt tokens in the AI app invocation.",
        ),
        Field(
            name=Columns.COMPLETION_COST.value,
            type=Float(),
            description="The cost of the completion tokens in the AI app invocation.",
        ),
        Field(
            name=Columns.TOOL_CALL_COUNT.value,
            type=Int(),
            description="The number of tool calls made during the AI app invocation.",
        ),
        Field(
            name=Columns.TOOL_CALL_ERROR_COUNT.value,
            type=Int(),
            description="The number of tool call errors during the AI app invocation.",
        ),
        Field(
            name=Columns.TOOL_CALL_NAME_COUNTS.value,
            type=Map(String(), Int()),
            description="A map of tool call names to their respective counts during the AI app invocation.",
        ),
        Field(
            name=Columns.LLM_CALL_COUNT.value,
            type=Int(),
            description="The number of LLM calls made during the AI app invocation.",
        ),
        Field(
            name=Columns.LLM_CALL_ERROR_COUNT.value,
            type=Int(),
            description="The number of LLM call errors during the AI app invocation.",
        ),
        Field(
            name=Columns.LLM_CALL_MODEL_COUNTS.value,
            type=Map(String(), Int()),
            description="A map of LLM models to their respective call counts during the AI app invocation.",
        ),
        Field(
            name=Columns.FEEDBACK_SCORE.value,
            type=Float(),
            description="The feedback score for the AI app invocation.",
        ),
        Field(
            name=Columns.FEEDBACK_TEXT.value,
            type=String(),
            description="The feedback text for the AI app invocation.",
        ),
    ]
)


def schema() -> Schema:
    """Returns the base schema for AI app invocations."""
    return _SCHEMA


def dtypes() -> dict[str, DataType]:
    """Returns a mapping of column names to their data types."""
    return {f.name: f.type for f in _SCHEMA.fields}


def field(column: str) -> Union[Field, None]:
    """Returns the field for the given column if any."""
    return _SCHEMA.field(column)


def field_or_die(column: str) -> Field:
    """Returns the field for the given column or raises an error if not found."""
    f = field(column)
    if f is None:
        raise ValueError(f"Unknown column: {column}")
    return f


def field_type(column: str) -> Union[DataType, None]:
    """Returns the type for the given column if any."""
    f = field(column)
    if f is None:
        return None
    return f.type
