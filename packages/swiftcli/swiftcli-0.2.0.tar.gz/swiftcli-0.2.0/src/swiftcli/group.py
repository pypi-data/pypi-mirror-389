from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

if TYPE_CHECKING:
    from swiftcli.command import BaseCommand


class Group(click.Group):
    def add_command_cls(
        self, cmd_cls: type[BaseCommand[Any]], name: str | None = None
    ) -> None:
        cmd = cmd_cls.to_command()
        self.add_command(cmd, name=name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return super().__call__(*args, **kwargs)
