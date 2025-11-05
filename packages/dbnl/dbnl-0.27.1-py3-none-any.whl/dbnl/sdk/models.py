from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Literal, Optional

from dataclasses_json import DataClassJsonMixin, config

from dbnl.sdk.types import DataType, from_json_value

REPR_INDENT = 4

"""
When adding a new class that should be exposed in the documentation, make sure to update
/docs/classes.rst
"""


@dataclass(repr=False)
class DBNLObject(DataClassJsonMixin):
    def __repr__(self) -> str:
        return self._pretty_print()

    def _pretty_print(self, nested_indent: int = 0) -> str:
        field_reprs = []
        for f in fields(self):
            value = getattr(self, f.name)
            if isinstance(value, list):
                value_repr = " " * (
                    2 * REPR_INDENT + nested_indent
                ) + f",\n{' ' * (2 * REPR_INDENT + nested_indent)}".join([f"{d}" for d in value])
                field_reprs.append(f"{f.name}=[\n{value_repr}\n{' ' * (REPR_INDENT + nested_indent)}]")
            elif isinstance(value, dict):
                value_repr = " " * (
                    2 * REPR_INDENT + nested_indent
                ) + f",\n{' ' * (2 * REPR_INDENT + nested_indent)}".join([
                    f"'{k}': {repr(v)}" for k, v in value.items()
                ])
                field_reprs.append(f"{f.name}=" + "{" + f"\n{value_repr}\n{' ' * (REPR_INDENT + nested_indent)}" + "}")
            elif isinstance(value, DBNLObject):
                field_reprs.append(f"{f.name}={value._pretty_print(nested_indent=REPR_INDENT)}")
            else:
                field_reprs.append(f"{f.name}={repr(value)}")
        return (
            f"{self.__class__.__name__}(\n{' ' * (REPR_INDENT + nested_indent)}"
            + f",\n{' ' * (REPR_INDENT + nested_indent)}".join(field_reprs)
            + f"\n{' ' * nested_indent})"
        )


@dataclass(repr=False)
class Project(DBNLObject):
    id: str
    org_id: str
    namespace_id: str
    created_at: str
    updated_at: str
    name: str
    description: Optional[str] = None
    schedule: Optional[Literal["daily", "hourly"]] = None
    default_llm_model_id: Optional[str] = None


@dataclass(repr=False)
class Metric(DBNLObject):
    id: str
    org_id: str
    namespace_id: str
    created_at: str
    updated_at: str
    project_id: str
    name: str
    expression_template: str
    description: Optional[str] = None
    greater_is_better: Optional[bool] = None


@dataclass(repr=False)
class RunSchemaMetric(DBNLObject):
    inputs: list[str]
    expression: Optional[str] = None


@dataclass(repr=False)
class RunSchemaColumnSchema(DBNLObject):
    name: str
    type: DataType = field(metadata=config(decoder=from_json_value, encoder=lambda x: x.to_json_value()))
    description: Optional[str] = None
    greater_is_better: Optional[bool] = None
    metric: Optional[RunSchemaMetric] = None


@dataclass(repr=False)
class RunSchema(DBNLObject):
    columns: list[RunSchemaColumnSchema]


@dataclass(repr=False)
class Run(DBNLObject):
    id: str
    org_id: str
    namespace_id: str
    created_at: str
    updated_at: str
    project_id: str
    schema_: RunSchema = field(metadata=config(field_name="schema"))
    data_start_time: Optional[str] = None
    data_end_time: Optional[str] = None
    status: Optional[Literal["pending", "closing", "closed", "canceled", "errored"]] = None
    completed_at: Optional[str] = None
    failure: Optional[str] = None


@dataclass(repr=False)
class LLMModel(DBNLObject):
    id: str
    org_id: str
    namespace_id: str
    created_at: str
    updated_at: str
    name: str
    model: str
    type: str
    provider: str
    author_id: str
    params: dict[str, str]
    description: Optional[str] = None
