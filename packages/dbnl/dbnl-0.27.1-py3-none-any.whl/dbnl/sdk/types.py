import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, unique
from typing import Any, Union

import pandas as pd
import pyarrow as pa
from typing_extensions import override

from dbnl.logging import logger

JSON = Union[dict[str, "JSON"], list["JSON"], str, int, float, bool, None]


@unique
class Type(Enum):
    """Type enum. Those are raw unparametrized types (e.g. list instead of list<string>)."""

    NULL = "null"
    BOOLEAN = "boolean"
    INT = "int"
    LONG = "long"
    FLOAT = "float"
    DOUBLE = "double"
    STRING = "string"
    CATEGORY = "category"
    LIST = "list"
    MAP = "map"
    STRUCT = "struct"
    TIMESTAMP = "timestamp"
    TIMESTAMPTZ = "timestamptz"


class DataType(ABC):
    """
    DataType classes represent types supported by dbnl. Each datatype contains a unique mapping to
    a panda and an arrow datatype for easy reading, writing and processing of the data.
    """

    @property
    @abstractmethod
    def type(self) -> Type:
        """Returns the raw unparametrized type."""
        raise NotImplementedError()

    @abstractmethod
    def to_arrow(self) -> pa.DataType:
        """Returns the corresponding arrow type."""
        raise NotImplementedError()

    def to_pandas(self) -> pd.ArrowDtype:
        """Returns the corresponding pandas type."""
        return pd.ArrowDtype(self.to_arrow())

    def to_json_value(self) -> JSON:
        """Returns a json value representation of the type."""
        raise NotImplementedError()

    def to_json(self) -> str:
        """Returns a json representation of the type."""
        return json.dumps(self.to_json_value())


class PrimitiveDataType(DataType, ABC):
    @override
    def to_json_value(self) -> JSON:
        return self.type.value

    @override
    def __str__(self) -> str:
        return self.type.value

    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


@dataclass(frozen=True)
class Null(PrimitiveDataType):
    """Null datatype. Represents a null value."""

    @property
    @override
    def type(self) -> Type:
        return Type.NULL

    @override
    def to_arrow(self) -> pa.DataType:
        return pa.null()


@dataclass(frozen=True)
class Bool(PrimitiveDataType):
    @property
    @override
    def type(self) -> Type:
        return Type.BOOLEAN

    @override
    def to_arrow(self) -> pa.DataType:
        return pa.bool_()


@dataclass(frozen=True)
class Int(PrimitiveDataType):
    @property
    @override
    def type(self) -> Type:
        return Type.INT

    @override
    def to_arrow(self) -> pa.DataType:
        return pa.int32()


@dataclass(frozen=True)
class Long(PrimitiveDataType):
    @property
    @override
    def type(self) -> Type:
        return Type.LONG

    @override
    def to_arrow(self) -> pa.DataType:
        return pa.int64()


@dataclass(frozen=True)
class Float(PrimitiveDataType):
    @property
    @override
    def type(self) -> Type:
        return Type.FLOAT

    @override
    def to_arrow(self) -> pa.DataType:
        return pa.float32()


@dataclass(frozen=True)
class Double(PrimitiveDataType):
    @property
    @override
    def type(self) -> Type:
        return Type.DOUBLE

    @override
    def to_arrow(self) -> pa.DataType:
        return pa.float64()


@dataclass(frozen=True)
class String(PrimitiveDataType):
    @property
    @override
    def type(self) -> Type:
        return Type.STRING

    @override
    def to_arrow(self) -> pa.DataType:
        return pa.string()


@dataclass(frozen=True)
class Category(String):
    @property
    @override
    def type(self) -> Type:
        return Type.CATEGORY

    @override
    def to_arrow(self) -> pa.DataType:
        return pa.dictionary(pa.int64(), pa.string())


@dataclass(frozen=True)
class Timestamp(PrimitiveDataType):
    """Timestamp datatype. Represents a timestamp in microseconds without a timeazone."""

    @property
    @override
    def type(self) -> Type:
        return Type.TIMESTAMP

    @override
    def to_arrow(self) -> pa.DataType:
        return pa.timestamp("us", tz=None)


@dataclass(frozen=True)
class TimestampTZ(PrimitiveDataType):
    """Timestamp with Timezone datatype. Represents a timestamp in microseconds in UTC."""

    @property
    @override
    def type(self) -> Type:
        return Type.TIMESTAMPTZ

    @override
    def to_arrow(self) -> pa.DataType:
        return pa.timestamp("us", tz="UTC")


@dataclass(frozen=True)
class List(DataType):
    """List datatype.

    :param value_type: type of the list values.
    """

    value_type: DataType

    @property
    @override
    def type(self) -> Type:
        return Type.LIST

    @override
    def to_arrow(self) -> pa.DataType:
        return pa.list_(self.value_type.to_arrow())

    @override
    def to_json_value(self) -> JSON:
        return {"type": self.type.value, "value_type": self.value_type.to_json_value()}

    @override
    def __str__(self) -> str:
        return f"{self.type.value}<{str(self.value_type)}>"

    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.value_type)})"


@dataclass(frozen=True)
class Map(DataType):
    """Map datatype.

    :param key_type: type of the map keys.
    :param value_type: type of the map values.
    """

    key_type: DataType
    value_type: DataType

    @property
    @override
    def type(self) -> Type:
        return Type.MAP

    @override
    def to_arrow(self) -> pa.DataType:
        return pa.map_(self.key_type.to_arrow(), self.value_type.to_arrow())

    @override
    def to_json_value(self) -> JSON:
        return {
            "type": self.type.value,
            "key_type": self.key_type.to_json_value(),
            "value_type": self.value_type.to_json_value(),
        }

    @override
    def __str__(self) -> str:
        return f"{self.type.value}<{str(self.key_type)}, {str(self.value_type)}>"

    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.key_type)}, {repr(self.value_type)})"


@dataclass(frozen=True)
class Field:
    """Struct field. Includes a name and a type.

    :return: _description_
    """

    name: str
    type: DataType
    nullable: bool = True
    description: Union[str, None] = None

    def to_json_value(self) -> JSON:
        return {
            "name": self.name,
            "type": self.type.to_json_value(),
            **({"nullable": self.nullable} if not self.nullable else {}),
        }

    def to_arrow(self) -> pa.Field:  # type: ignore[type-arg]
        return pa.field(self.name, self.type.to_arrow(), nullable=self.nullable)

    @override
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.name}", {repr(self.type)}, {self.nullable})'


@dataclass(frozen=True)
class Struct(DataType):
    """Struct datatype.

    :param fields: list of fields.
    """

    fields: list[Field]

    @property
    @override
    def type(self) -> Type:
        return Type.STRUCT

    def field(self, name: str) -> Union[Field, None]:
        for f in self.fields:
            if f.name == name:
                return f
        return None

    @override
    def to_arrow(self) -> pa.DataType:
        return pa.struct([f.to_arrow() for f in self.fields])

    @override
    def to_json_value(self) -> JSON:
        return {
            "type": self.type.value,
            "fields": [f.to_json_value() for f in self.fields],
        }

    def to_arrow_schema(self) -> pa.Schema:
        return pa.schema([f.to_arrow() for f in self.fields])

    @override
    def __str__(self) -> str:
        fields = ", ".join(f"{f.name}: {str(f.type)}" for f in self.fields)
        return f"{self.type.value}<{fields}>"

    @override
    def __repr__(self) -> str:
        fields = ", ".join(repr(f) for f in self.fields)
        return f"{self.__class__.__name__}([{fields}])"


@dataclass(frozen=True)
class Schema:
    """Schema.

    :param fields: list of fields in the schema.
    """

    fields: list[Field]

    @classmethod
    def from_struct(cls, s: Struct) -> "Schema":
        """Creates a schema from a struct datatype.

        :param s: Struct datatype.
        :return: Schema with fields from the struct.
        """
        return cls(fields=s.fields)

    @classmethod
    def from_arrow(cls, schema: pa.Schema) -> "Schema":
        """Creates a schema from an arrow schema.

        :param schema: Arrow schema.
        :return: Schema with fields from the arrow schema.
        """
        return cls(fields=[Field(f.name, from_arrow(f.type), f.nullable) for f in schema])

    @classmethod
    def from_pandas(cls, dtypes: dict[str, pd.ArrowDtype]) -> "Schema":
        """Creates a schema from a pandas DataFrame dtypes.

        :param dtypes: Pandas DataFrame dtypes.
        :return: Schema with fields from the pandas dtypes.
        """
        return cls(fields=[Field(name, from_pandas(dtype)) for name, dtype in dtypes.items()])

    def to_arrow(self) -> pa.Schema:
        """Converts the schema to an arrow schema."""
        return pa.schema([f.to_arrow() for f in self.fields])

    def to_pandas(self) -> dict[str, pd.ArrowDtype]:
        """Converts the schema to a pandas DataFrame with the appropriate dtypes."""
        return {f.name: f.type.to_pandas() for f in self.fields}

    def field(self, name: str) -> Union[Field, None]:
        for f in self.fields:
            if f.name == name:
                return f
        return None


def from_arrow(dtype: pa.DataType) -> DataType:
    """Converts an arrow datatype to a dbnl datatype.

    :param dtype: arrow type
    :return: dbnl datatype
    """
    if pa.types.is_null(dtype):
        return Null()
    elif pa.types.is_boolean(dtype):
        return Bool()
    elif pa.types.is_integer(dtype):
        width = dtype.bit_width
        if width <= 32:
            return Int()
        elif width <= 64:
            return Long()
        else:
            raise ValueError(f"Unsupported integer bit width {width}")
    elif pa.types.is_floating(dtype):
        width = dtype.bit_width
        if width <= 32:
            return Float()
        elif width <= 64:
            return Double()
        else:
            raise ValueError(f"Unsupported float bit width {width}")
    elif pa.types.is_string(dtype) or pa.types.is_large_string(dtype):
        return String()
    elif pa.types.is_dictionary(dtype):
        assert isinstance(dtype, pa.DictionaryType)
        if pa.types.is_integer(dtype.index_type) and pa.types.is_string(dtype.value_type):
            return Category()
        # fallback to just treat as underlying type
        return from_arrow(dtype.value_type)
    elif pa.types.is_timestamp(dtype):
        assert isinstance(dtype, pa.TimestampType)
        if dtype.unit in ("s", "ms", "us"):
            pass
        elif dtype.unit == "ns":
            logger.warning("Unsupported timestamp unit 'ns'. Downcasting to 'us'.")
        else:
            raise ValueError(f"Unsupported timestamp unit {dtype.unit}. Only 's', 'ms', 'us' and 'ns' are supported.")
        if dtype.tz is None:
            return Timestamp()
        elif dtype.tz == "UTC":
            return TimestampTZ()
        else:
            raise ValueError(f"Unsupported arrow timestamp dtype with timezone {dtype.tz}. Only 'UTC' is supported.")
    elif pa.types.is_list(dtype):
        assert isinstance(dtype, pa.ListType)
        return List(from_arrow(dtype.value_type))
    elif pa.types.is_map(dtype):
        assert isinstance(dtype, pa.MapType)
        return Map(from_arrow(dtype.key_type), from_arrow(dtype.item_type))
    elif pa.types.is_struct(dtype):
        assert isinstance(dtype, pa.StructType)
        return Struct([Field(dtype.field(i).name, from_arrow(dtype.field(i).type)) for i in range(dtype.num_fields)])
    raise ValueError(f"Unsupported arrow dtype {dtype}")


def from_pandas(dtype: Any) -> DataType:
    """Converts a pandas datatype to a dbnl datatype.

    :param dtype: pandas datatype
    :return: dbnl datatype
    """
    if not isinstance(dtype, pd.ArrowDtype):
        raise ValueError(f"Unsupported pandas dtype {dtype}")
    return from_arrow(dtype.pyarrow_dtype)


def _list_from_json_value(d: JSON) -> DataType:
    if not isinstance(d, dict):
        raise ValueError(f"Invalid JSON value: {d}")
    if "value_type" not in d:
        raise KeyError(f"Missing value_type key in list JSON value: {d}")
    return List(value_type=from_json_value(d["value_type"]))


def _map_from_json_value(d: JSON) -> DataType:
    if not isinstance(d, dict):
        raise ValueError(f"Invalid JSON value: {d}")
    if "key_type" not in d:
        raise KeyError(f"Missing key_type key in map JSON value: {d}")
    if "value_type" not in d:
        raise KeyError(f"Missing value_type key in map JSON value: {d}")
    return Map(
        key_type=from_json_value(d["key_type"]),
        value_type=from_json_value(d["value_type"]),
    )


def _struct_from_json_value(d: JSON) -> DataType:
    if not isinstance(d, dict):
        raise ValueError(f"Invalid JSON value: {d}")
    if "fields" not in d:
        raise KeyError(f"Missing fields key in struct JSON value: {d}")
    fields = d["fields"]
    if not isinstance(fields, list):
        raise ValueError(f"Invalid fields value in struct JSON value, expected list: {d}")
    return Struct([_field_from_json_value(f) for f in fields])


def _field_from_json_value(d: JSON) -> Field:
    if not isinstance(d, dict):
        raise ValueError(f"Invalid field JSON value: {d}")
    if "name" not in d:
        raise KeyError(f"Missing name key in field JSON value: {d}")
    name = d["name"]
    if not isinstance(name, str):
        raise ValueError(f"Invalid name value in field JSON value: {name}")
    if "type" not in d:
        raise KeyError(f"Missing type key in field JSON value: {d}")
    tpe = from_json_value(d["type"])
    return Field(name, tpe)


def from_json_value(d: JSON) -> DataType:
    """Parses a datatype from JSON value.

    :param d: JSON value
    :param allow_legacy: Whether to allow legacy nested types. Should only be
                         needed for database reads where some legacy data still
                         exists.
    :return: datatype
    """
    # Parse primitive types.
    if isinstance(d, str):
        tpe = Type(d)
        if tpe == Type.NULL:
            return Null()
        elif tpe == Type.BOOLEAN:
            return Bool()
        elif tpe == Type.INT:
            return Int()
        elif tpe == Type.LONG:
            return Long()
        elif tpe == Type.FLOAT:
            return Float()
        elif tpe == Type.DOUBLE:
            return Double()
        elif tpe == Type.STRING:
            return String()
        elif tpe == Type.CATEGORY:
            return Category()
        elif tpe == Type.TIMESTAMP:
            return Timestamp()
        elif tpe == Type.TIMESTAMPTZ:
            return TimestampTZ()
        else:
            raise ValueError(f"Invalid primitive type: {d}")
    # Parse parametrized types.
    if not isinstance(d, dict):
        raise ValueError(f"Invalid JSON value: {d}")
    if "type" not in d or not isinstance(d["type"], str):
        raise KeyError(f"Missing type key in type JSON value: {d}")
    tpe = Type(d["type"])
    if tpe == Type.LIST:
        return _list_from_json_value(d)
    elif tpe == Type.MAP:
        return _map_from_json_value(d)
    elif tpe == Type.STRUCT:
        return _struct_from_json_value(d)
    raise ValueError(f"Invalid type: {d}")
