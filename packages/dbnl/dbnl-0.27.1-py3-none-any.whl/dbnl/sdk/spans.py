import json
from binascii import hexlify
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, Union

import pandas as pd
from opentelemetry.proto.common.v1.common_pb2 import AnyValue as AnyValueProto
from opentelemetry.proto.common.v1.common_pb2 import KeyValue as KeyValueProto
from opentelemetry.proto.trace.v1.trace_pb2 import Span as SpanProto
from opentelemetry.proto.trace.v1.trace_pb2 import Status as StatusProto
from opentelemetry.proto.trace.v1.trace_pb2 import TracesData as TracesDataProto
from opentelemetry.trace import SpanKind, StatusCode

from dbnl.sdk.types import DataType, Field, List, Map, String, Struct, TimestampTZ

_TraceId = str
_SpanId = str

_AnyValue = Union[str, int, float, bool, bytes, list["_AnyValue"], dict[str, "_AnyValue"], None]

_Attributes = dict[str, _AnyValue]


def _decode_span_id(b: bytes) -> Union[_SpanId, None]:
    """
    Decodes a span ID from bytes to a lowercase hex string.

    https://github.com/open-telemetry/opentelemetry-specification/blob/2bc7276d35d3d1785eb6aef9db85e047adcd271a/specification/trace/api.md?plain=1#L255-L265
    """
    if not b:
        return None
    return hexlify(b).decode()


def _decode_span_id_or_die(b: bytes) -> _SpanId:
    """
    Decodes a span ID from bytes to a lowercase hex string or throws if invalid.

    https://github.com/open-telemetry/opentelemetry-specification/blob/2bc7276d35d3d1785eb6aef9db85e047adcd271a/specification/trace/api.md?plain=1#L255-L265
    """
    span_id = _decode_span_id(b)
    if not span_id:
        raise ValueError("Invalid span ID: cannot be empty")
    return span_id


def _decode_trace_id(b: bytes) -> Union[_TraceId, None]:
    """
    Decodes a trace ID from bytes to a lowercase hex string.

    https://github.com/open-telemetry/opentelemetry-specification/blob/2bc7276d35d3d1785eb6aef9db85e047adcd271a/specification/trace/api.md?plain=1#L255-L265
    """
    if not b:
        return None
    return hexlify(b).decode()


def _decode_trace_id_or_die(b: bytes) -> _TraceId:
    """
    Decodes a trace ID from bytes to a lowercase hex string or throws if invalid.

    https://github.com/open-telemetry/opentelemetry-specification/blob/2bc7276d35d3d1785eb6aef9db85e047adcd271a/specification/trace/api.md?plain=1#L255-L265
    """
    trace_id = _decode_trace_id(b)
    if not trace_id:
        raise ValueError("Invalid trace ID: cannot be empty")
    return trace_id


def _decode_time_unix_nano(time_unix_nano: int) -> datetime:
    """Decodes a timestamp in nanoseconds."""
    return datetime.fromtimestamp(time_unix_nano / 1_000_000_000, timezone.utc)


def _decode_any_value_proto(value: AnyValueProto) -> Union[_AnyValue, None]:
    """
    Decodes an any value.

    https://github.com/open-telemetry/opentelemetry-specification/blob/2bc7276d35d3d1785eb6aef9db85e047adcd271a/specification/logs/data-model.md?plain=1#L115-L127
    """
    which = value.WhichOneof("value")
    if which == "string_value":
        return value.string_value
    elif which == "bool_value":
        return value.bool_value
    elif which == "int_value":
        return value.int_value
    elif which == "double_value":
        return value.double_value
    elif which == "array_value":
        return [_decode_any_value_proto(v) for v in value.array_value.values]
    elif which == "kvlist_value":
        return _decode_key_values_proto(value.kvlist_value.values)
    elif which == "bytes_value":
        return value.bytes_value
    elif which is None:
        return None
    else:
        raise ValueError(f"Unexpected value: {which}")


def _decode_any_value_json_value(value: Union[dict[str, Any], None]) -> Union[_AnyValue, None]:
    """
    Decodes an any value from JSON value.

    https://github.com/open-telemetry/opentelemetry-specification/blob/2bc7276d35d3d1785eb6aef9db85e047adcd271a/specification/logs/data-model.md?plain=1#L115-L127
    """
    if value is None:
        return None
    elif "stringValue" in value:
        return str(value["stringValue"])
    elif "boolValue" in value:
        return bool(value["boolValue"])
    elif "intValue" in value:
        return int(value["intValue"])
    elif "doubleValue" in value:
        return float(value["doubleValue"])
    elif "arrayValue" in value and "values" in value["arrayValue"]:
        return [_decode_any_value_json_value(v) for v in value["arrayValue"]["values"]]
    elif "kvlistValue" in value and "values" in value["kvlistValue"]:
        return _decode_key_values_json_value(value["kvlistValue"]["values"])
    elif "bytesValue" in value:
        return bytes(value["bytesValue"])
    else:
        raise ValueError(f"Unexpected value: {value}")


def _decode_key_values_proto(kvs: Sequence[KeyValueProto]) -> Union[dict[str, _AnyValue], None]:
    """
    Decodes a set of key-value pairs.

    https://github.com/open-telemetry/opentelemetry-specification/blob/2bc7276d35d3d1785eb6aef9db85e047adcd271a/specification/logs/data-model.md?plain=1#L129-L145
    """
    if not kvs:
        return None
    return {kv.key: _decode_any_value_proto(kv.value) for kv in kvs if kv.value is not None}


def _decode_key_values_json_value(kvs: list[dict[str, Any]]) -> Union[dict[str, _AnyValue], None]:
    """
    Decodes a set of key-value pairs from JSON value.


    https://github.com/open-telemetry/opentelemetry-specification/blob/2bc7276d35d3d1785eb6aef9db85e047adcd271a/specification/logs/data-model.md?plain=1#L129-L145
    """
    if not kvs:
        return None
    return {kv["key"]: _decode_any_value_json_value(kv["value"]) for kv in kvs if kv.get("value") is not None}


def _decode_attributes_proto(kvs: Sequence[KeyValueProto]) -> dict[str, _AnyValue]:
    """
    Decodes a set of attributes.

    https://github.com/open-telemetry/opentelemetry-specification/blob/2bc7276d35d3d1785eb6aef9db85e047adcd271a/specification/common/README.md?plain=1#L29-L69
    """
    return _decode_key_values_proto(kvs) or {}


def _decode_attributes_json_value(kvs: list[dict[str, Any]]) -> dict[str, _AnyValue]:
    """
    Decodes a set of attributes from JSON value.

    https://github.com/open-telemetry/opentelemetry-specification/blob/2bc7276d35d3d1785eb6aef9db85e047adcd271a/specification/common/README.md?plain=1#L29-L69
    """
    return _decode_key_values_json_value(kvs) or {}


def _decode_trace_state(state: str) -> Union[str, None]:
    """Decodes the trace state, returning None if empty."""
    if not state:
        return None
    return state


def _encode_attributes(attributes: dict[str, _AnyValue]) -> dict[str, str]:
    """Encodes attributes to a flat map of strings."""
    return {k: json.dumps(v) for k, v in attributes.items()}


@dataclass
class _Event:
    """
    Span event.

    https://github.com/open-telemetry/opentelemetry-specification/blob/2bc7276d35d3d1785eb6aef9db85e047adcd271a/specification/trace/api.md#add-events
    """

    timestamp: datetime
    name: str
    attributes: _Attributes

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "name": self.name,
            "attributes": _encode_attributes(self.attributes),
        }

    @classmethod
    def from_proto(cls, event: SpanProto.Event) -> "_Event":
        return _Event(
            timestamp=_decode_time_unix_nano(int(event.time_unix_nano)),
            name=event.name,
            attributes=_decode_attributes_proto(event.attributes),
        )

    @classmethod
    def from_json_value(cls, event: dict[str, Any]) -> "_Event":
        return _Event(
            timestamp=_decode_time_unix_nano(event["time_unix_nano"]),
            name=event["name"],
            attributes=_decode_attributes_json_value(event.get("attributes", {})),
        )


@dataclass
class _Link:
    """
    Span link.

    https://github.com/open-telemetry/opentelemetry-specification/blob/2bc7276d35d3d1785eb6aef9db85e047adcd271a/specification/trace/api.md#add-link
    """

    trace_id: _TraceId
    span_id: _SpanId
    trace_state: Union[str, None]
    attributes: _Attributes

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "trace_state": self.trace_state,
            "attributes": _encode_attributes(self.attributes),
        }

    @classmethod
    def from_proto(cls, link: SpanProto.Link) -> "_Link":
        return _Link(
            trace_id=_decode_trace_id_or_die(link.trace_id),
            span_id=_decode_span_id_or_die(link.span_id),
            trace_state=link.trace_state,
            attributes=_decode_attributes_proto(link.attributes),
        )

    @classmethod
    def from_json_value(cls, link: dict[str, Any]) -> "_Link":
        return _Link(
            trace_id=link["traceId"].lower(),
            span_id=link["spanId"].lower(),
            trace_state=link.get("traceState", None) or None,
            attributes=_decode_attributes_json_value(link.get("attributes", {})),
        )


@dataclass
class _Status:
    """
    Span status.

    https://github.com/open-telemetry/opentelemetry-specification/blob/2bc7276d35d3d1785eb6aef9db85e047adcd271a/specification/trace/api.md#set-status
    """

    code: StatusCode = StatusCode.UNSET
    message: Union[str, None] = None

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code.name, "message": self.message}

    @classmethod
    def from_proto(cls, status: StatusProto) -> "_Status":
        return _Status(StatusCode(status.code), status.message if status.message else None)

    @classmethod
    def from_json_value(cls, status: dict[str, Any]) -> "_Status":
        return _Status(StatusCode(status.get("code", 0)), status.get("message", None))


@dataclass
class _Span:
    """
    Span.

    https://github.com/open-telemetry/opentelemetry-specification/blob/2bc7276d35d3d1785eb6aef9db85e047adcd271a/specification/trace/api.md#span
    """

    trace_id: _TraceId
    span_id: _SpanId
    trace_state: Union[str, None]
    parent_span_id: Union[_SpanId, None]
    name: str
    kind: SpanKind
    start_time: datetime
    end_time: datetime
    attributes: _Attributes
    events: list[_Event]
    links: list[_Link]
    status: _Status

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "trace_state": self.trace_state,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "kind": self.kind.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "attributes": _encode_attributes(self.attributes),
            "events": [e.to_dict() for e in self.events],
            "links": [l.to_dict() for l in self.links],
            "status": self.status.to_dict(),
        }

    @classmethod
    def from_proto(cls, span: SpanProto) -> "_Span":
        return _Span(
            trace_id=_decode_trace_id_or_die(span.trace_id),
            span_id=_decode_span_id_or_die(span.span_id),
            trace_state=_decode_trace_state(span.trace_state),
            parent_span_id=_decode_trace_id(span.parent_span_id),
            name=span.name,
            kind=SpanKind(span.kind),
            start_time=_decode_time_unix_nano(span.start_time_unix_nano),
            end_time=_decode_time_unix_nano(span.end_time_unix_nano),
            attributes=_decode_attributes_proto(span.attributes),
            events=[_Event.from_proto(e) for e in span.events or []],
            links=[_Link.from_proto(l) for l in span.links or []],
            status=_Status.from_proto(span.status) if span.status else _Status(),
        )

    @classmethod
    def from_traces_data_proto(cls, traces_data: TracesDataProto) -> list["_Span"]:
        return [
            cls.from_proto(span)
            for resource_span in traces_data.resource_spans
            for scope_span in resource_span.scope_spans
            for span in scope_span.spans
        ]

    @classmethod
    def from_json(cls, span: str) -> "_Span":
        return cls.from_json_value(json.loads(span))

    @classmethod
    def from_traces_data_json(cls, traces_data: str) -> list["_Span"]:
        return cls.from_traces_data_json_value(json.loads(traces_data))

    @classmethod
    def from_json_value(cls, span: dict[str, Any]) -> "_Span":
        return _Span(
            trace_id=span["traceId"].lower(),
            span_id=span["spanId"].lower(),
            trace_state=span.get("traceState", "") or None,
            parent_span_id=span.get("parentSpanId", "").lower() or None,
            name=span["name"],
            kind=SpanKind(span["kind"]),
            start_time=_decode_time_unix_nano(int(span["startTimeUnixNano"])),
            end_time=_decode_time_unix_nano(int(span["endTimeUnixNano"])),
            attributes=_decode_attributes_json_value(span.get("attributes", {})),
            events=[_Event.from_json_value(e) for e in span.get("events", [])],
            links=[_Link.from_json_value(l) for l in span.get("links", [])],
            status=_Status.from_json_value(status) if (status := span.get("status")) is not None else _Status(),
        )

    @classmethod
    def from_traces_data_json_value(cls, traces_data: dict[str, Any]) -> list["_Span"]:
        return [
            cls.from_json_value(span)
            for resource_span in traces_data.get("resourceSpans", [])
            for scope_span in resource_span.get("scopeSpans", [])
            for span in scope_span.get("spans", [])
        ]


def span_dtype() -> DataType:
    return Struct([
        Field("trace_id", String()),
        Field("span_id", String()),
        Field("trace_state", String()),
        Field("parent_span_id", String()),
        Field("name", String()),
        Field("kind", String()),
        Field("start_time", TimestampTZ()),
        Field("end_time", TimestampTZ()),
        Field("attributes", Map(String(), String())),
        Field(
            "events",
            List(
                Struct([
                    Field("timestamp", TimestampTZ()),
                    Field("name", String()),
                    Field("attributes", Map(String(), String())),
                ])
            ),
        ),
        Field(
            "links",
            List(
                Struct([
                    Field("trace_id", String()),
                    Field("span_id", String()),
                    Field("trace_state", String()),
                    Field("attributes", Map(String(), String())),
                ])
            ),
        ),
        Field(
            "status",
            Struct([
                Field("code", String()),
                Field("message", String()),
            ]),
        ),
    ])


def spans_dtype() -> DataType:
    return List(span_dtype())


def _convert_trace_data_json(data: str) -> list[dict[str, Any]]:
    return [s.to_dict() for s in _Span.from_traces_data_json(data)]


def _convert_trace_data_json_value(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [s.to_dict() for s in _Span.from_traces_data_json_value(data)]


def _convert_trace_data_proto(data: bytes) -> list[dict[str, Any]]:
    return [s.to_dict() for s in _Span.from_traces_data_proto(TracesDataProto.FromString(data))]


def _is_binary_dtype(data: "pd.Series[Any]") -> bool:
    if data.empty:
        return False
    return isinstance(data.iloc[0], bytes)


def _infer_otlp_format(data: "pd.Series[Any]") -> Literal["otlp_json", "otlp_proto"]:
    if _is_binary_dtype(data):
        return "otlp_proto"
    elif pd.api.types.is_string_dtype(data):
        return "otlp_json"
    # Must check last because binary and string are dict like.
    elif pd.api.types.is_dict_like(data):
        return "otlp_json"
    else:
        raise ValueError(f"Could not infer OTLP format from data type: {data.dtype}")


def convert_otlp_traces_data(
    data: "pd.Series[Any]",
    format: Union[Literal["otlp_json", "otlp_proto"], None] = None,
) -> "pd.Series[Any]":
    """
    Converts a Series of OTLP TracesData to DBNL spans.

    :param data: Series of OTLP TracesData
    :param format: OTLP TracesData format (`otlp_json` or `otlp_proto`) or None to infer from data
    :return: Series of spans data
    """
    if format is None:
        format = _infer_otlp_format(data)
    if format == "otlp_json":
        if pd.api.types.is_string_dtype(data):
            return data.apply(_convert_trace_data_json).astype(spans_dtype().to_pandas())
        if pd.api.types.is_dict_like(data):
            return data.apply(_convert_trace_data_json_value).astype(spans_dtype().to_pandas())
        raise ValueError(f"Expected `string` or `dict` data for otlp_json format, got {data.dtype}")
    elif format == "otlp_proto":
        return data.apply(_convert_trace_data_proto).astype(spans_dtype().to_pandas())
    else:
        raise ValueError(f"Unexpected format: {format}")
