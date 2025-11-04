# SwiftCLI
Build testable CLI apps with `click` and `pydantic`

`swiftcli` makes it easy to define CLI parameters with `pydantic` BaseModels, combining the power of `click` with `pydantic`'s data validation.

## Features
- Define CLI parameters using pydantic models
- Type validation and conversion out of the box
- Support for arguments, options, flags and switches
- Easy to test CLI applications

## Installation
```bash
pip install swiftcli
```

## Simple Example
```python
from pydantic import BaseModel

from swiftcli import BaseCommand, Group
from swiftcli.types import Argument, Option


class GreetParams(BaseModel):
    name: Argument[str]  # required argument
    color: Option[str] = ""  # Optional --color option with default value


class GreetCommand(BaseCommand[GreetParams]):
    NAME = "greet"

    def run(self) -> None:
        if self.params.color:
            print(f"Hello, {self.params.name}. You like the color {self.params.color}.")
        else:
            print(f"Hello, {self.params.name}.")


cli = Group()
cli.add_command_cls(GreetCommand)

if __name__ == "__main__":
    cli()
```

## Parameter Types
SwiftCLI provides several parameter types through the `swiftcli.types` module:

### Argument
Required positional arguments:
```python
class MyParams(BaseModel):
    filename: Argument[str]  # Required positional argument
```

### Option
Optional named parameters with default values:
```python
class MyParams(BaseModel):
    output: Option[str] = "output.txt"  # --output option with default
    count: Option[int] = 1  # --count option with default
```

### Flag
Boolean flags that can be enabled:
```python
class MyParams(BaseModel):
    verbose: Flag  # --verbose flag, defaults to False
```

### Switch
Enum-based switches that create multiple mutually exclusive flags:
```python
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info" 
    ERROR = "error"

class MyParams(BaseModel):
    log_level: Switch[LogLevel] = LogLevel.INFO  # Creates --debug, --info, --error flags
```

## Advanced Usage

### Command Configuration
Commands can be configured using the CONFIG class variable:

```python
class MyCommand(BaseCommand[MyParams]):
    NAME = "mycommand"
    CONFIG = {
        "help": "My command help text",
        "short_help": "Short help",
        "epilog": "Additional help text at the bottom",
        "hidden": False,
        "deprecated": False,
    }
```

### Option Customization
Options can be customized using OptionSettings:

```python
from typing import Annotated
from swiftcli.types import OptionSettings

class MyParams(BaseModel):
    verbose: Annotated[
        int,
        OptionSettings(
            count=True,  # Allow multiple flags (-vvv)
            aliases=["-v"],  # Add short alias
            help="Sets the verbosity level"
        )
    ] = 0
```

### Command Groups
Group multiple commands together:

```python
from swiftcli import Group

cli = Group()
cli.add_command_cls(CommandOne)
cli.add_command_cls(CommandTwo)

if __name__ == "__main__":
    cli()
```

## Testing
SwiftCLI makes it easy to test your CLI applications:

```python
# Import the command we want to test
from my_cli.commands import MyCommand

# Test the command
def test_my_command():
    # You can mock, stub, or read the stdout/err
    # Run the command:
    MyCommand(param1="a", param2="b").run()
```

## License
MIT
