from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Annotated

import click
from typing_extensions import TypeVar, Unpack

if TYPE_CHECKING:
    from swiftcli._click_types import ClickArgumentFields, ClickOptionFields

__all__ = [
    "Argument",
    "ArgumentSettings",
    "Flag",
    "Option",
    "OptionSettings",
    "Switch",
]


class OptionSettings:
    def __init__(
        self,
        cls_type: type[click.Option] = click.Option,
        aliases: list[str] | None = None,
        **kwargs: Unpack[ClickOptionFields],
    ):
        self.cls_type = cls_type
        self.aliases = aliases if aliases else []
        self.kwargs: ClickOptionFields = kwargs


class ArgumentSettings:
    def __init__(
        self,
        cls_type: type[click.Argument] = click.Argument,
        **kwargs: Unpack[ClickArgumentFields],
    ):
        self.cls_type = cls_type
        self.kwargs: ClickArgumentFields = kwargs


T = TypeVar("T")
E = TypeVar("E", bound=Enum)

Argument = Annotated[T, ArgumentSettings()]
Option = Annotated[T, OptionSettings()]
Flag = Annotated[bool, OptionSettings(is_flag=True, default=False)]
Switch = Annotated[E, OptionSettings(is_flag=True)]
