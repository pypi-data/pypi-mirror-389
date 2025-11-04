from __future__ import annotations

import abc
import sys
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    TypedDict,
)

import click
from pydantic import BaseModel, ValidationError
from typing_extensions import NotRequired, TypeVar

from swiftcli._pydantic_click_adapter import PydanticClickAdapter
from swiftcli.utils import strip_indent

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from pydantic.fields import FieldInfo

ParamsType = TypeVar("ParamsType", bound=BaseModel, default=BaseModel)


class CommandConfig(TypedDict):
    name: NotRequired[str | None]
    context_settings: NotRequired[MutableMapping[str, Any] | None]
    help: NotRequired[str | None]
    epilog: NotRequired[str | None]
    short_help: NotRequired[str | None]
    options_metavar: NotRequired[str | None]
    add_help_option: NotRequired[bool]
    no_args_is_help: NotRequired[bool]
    hidden: NotRequired[bool]
    deprecated: NotRequired[bool]


class BaseCommand(Generic[ParamsType]):
    NAME: str = ""
    COMMAND_CLS: type[click.Command] = click.Command
    CONFIG: CommandConfig = {}

    def __init__(self, **kwargs: Any):
        params_schema_cls = self.__get_parameters_type()
        try:
            self.params: ParamsType = params_schema_cls(**kwargs)
        except ValidationError as e:
            print(e)
            sys.exit(1)
        self._params: dict[str, Any] = kwargs

    @classmethod
    def to_command(cls) -> click.Command:
        def callback_fn(**kwargs: Any) -> None:
            cmd = cls(**kwargs)
            return cmd.run()

        params_schema_cls = cls.__get_parameters_type()
        model_fields: dict[str, FieldInfo] = params_schema_cls.model_fields

        parameters: list[click.Parameter] = []
        for name, field_info in model_fields.items():
            params = PydanticClickAdapter(name, field_info).to_click_params()
            parameters.extend(params)

        config = cls.CONFIG.copy()
        config["help"] = strip_indent(config.get("help"))
        config["name"] = config.get("name", cls.NAME)
        return cls.COMMAND_CLS(
            params=parameters,
            callback=callback_fn,
            **config,
        )

    @abc.abstractmethod
    def run(self) -> None:
        """
        Runs the command
        """
        raise NotImplementedError()

    @classmethod
    def __get_parameters_type(cls) -> type[ParamsType]:
        orig_bases = cls.__orig_bases__  # type: ignore[attr-defined]
        if not orig_bases:
            raise RuntimeError("Could not find parameters")

        args = cls.__orig_bases__[0].__args__  # type: ignore[attr-defined]
        if not args or args[0] == ParamsType:  # type: ignore[misc]
            raise RuntimeError("Could not find parameters")

        return args[0]  # type: ignore[no-any-return]
