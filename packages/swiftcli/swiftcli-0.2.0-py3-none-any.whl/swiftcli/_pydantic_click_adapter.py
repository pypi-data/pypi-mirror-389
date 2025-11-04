from __future__ import annotations

from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Any, cast

import click
from pydantic_core import PydanticUndefined

from .types import ArgumentSettings, OptionSettings

try:
    from click.core import UNSET  # type: ignore[attr-defined]
except ImportError:
    UNSET = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo

StrDict = dict[str, Any]


class PydanticClickAdapter:
    def __init__(self, field_name: str, field_info: FieldInfo):
        self.field_name = field_name
        self.field_info = field_info

    @cached_property
    def metadata(self) -> OptionSettings | ArgumentSettings:
        assert len(self.field_info.metadata), (
            f"No metadata found for field {self.field_name}"
        )
        metadata = self.field_info.metadata[0]

        if not isinstance(metadata, OptionSettings | ArgumentSettings):
            raise RuntimeError(f"Unsupported metadata type: {type(metadata)}")
        return metadata

    @cached_property
    def field_type(self) -> type:
        assert self.field_info.annotation is not None, "Annotation is required"
        return self.field_info.annotation

    def to_click_params(self) -> list[click.Parameter]:
        param_decls = self._get_default_param_decls()
        param_cls = self.metadata.cls_type

        param_kwargs = cast("StrDict", self.metadata.kwargs.copy())
        param_kwargs.pop("param_decls", None)
        param_kwargs["required"] = self.field_info.default == PydanticUndefined
        param_kwargs["default"] = self._get_field_default_value()
        param_kwargs["type"] = self._to_click_type(self.field_type)

        if isinstance(self.metadata, OptionSettings):
            param_kwargs["show_default"] = param_kwargs.get("show_default", True)
            if self._is_feature_switch():
                return self._create_switch_params(param_kwargs)

        param = param_cls(param_decls, **param_kwargs)
        return [param]

    def _get_default_param_decls(self) -> list[str]:
        param_decls = list(self.metadata.kwargs.get("param_decls") or [])
        if param_decls:
            return param_decls

        long_name = str(self.field_info.alias or self.field_name)
        param_decls = [long_name]
        if isinstance(self.metadata, OptionSettings):
            dashed_named = self.field_name.replace("_", "-")
            param_decls.append(f"--{dashed_named}")
            param_decls.extend(self.metadata.aliases)
        return param_decls

    def _get_field_default_value(self) -> Any:
        default = self.field_info.default
        if default == PydanticUndefined:
            return UNSET
        if isinstance(default, Enum):
            return default.value
        return default

    @classmethod
    def _to_click_type(cls, annotation: type | None) -> click.ParamType:
        assert annotation is not None, "Annotation is required"
        if cls._is_multiple_types(annotation):
            return click.STRING
        if issubclass(annotation, bool):
            return click.BOOL
        elif issubclass(annotation, int):
            return click.INT
        elif issubclass(annotation, float):
            return click.FLOAT
        elif issubclass(annotation, Enum):
            return click.Choice([e.value for e in annotation])
        return click.STRING

    def _is_feature_switch(self) -> bool:
        if self._is_multiple_types(self.field_type):
            return False
        is_flag = bool(self.metadata.kwargs.get("is_flag"))
        is_enum = issubclass(self.field_type, Enum)
        return is_flag and is_enum

    def _create_switch_params(self, param_kwargs: StrDict) -> list[click.Parameter]:
        param_cls = self.metadata.cls_type
        enum_values = list(cast("type[Enum]", self.field_type))

        param_kwargs = {
            k: v
            for k, v in param_kwargs.items()
            if k not in {"default", "is_flag", "flag_value", "help"}
        }

        switch_params: list[click.Parameter] = []
        for e in enum_values:
            help_msg = param_kwargs.get("help", f'Set "{self.field_name}" to {e.value}')
            param = param_cls(
                [f"--{e.name.lower().replace('_', '-')}", self.field_name],
                default=True if e.value == self._get_field_default_value() else None,
                is_flag=True,
                flag_value=e.value,
                help=help_msg,
                **param_kwargs,
            )
            switch_params.append(param)

        return switch_params

    @classmethod
    def _is_multiple_types(cls, annotation: type) -> bool:
        return bool(getattr(annotation, "__args__", None))
