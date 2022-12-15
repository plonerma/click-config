# Click-Config

Click-config enables the use of dataclasses as config objects which can be read
from configurations files (yaml, toml, or json; the type is derived from the
file extension).
Values in the config file can be overwritten using command line options
(click-config integrates dataclasses with [click](https://click.palletsprojects.com/en/8.1.x/)).


## Example Usage

```python
from typing import List

from click_config import click_config_options, command, field


@dataclass
class Config:
    """Some description.

    :param a: a_help_str
    """

    a: int
    b: str = "test"
    c: List[str] = field(
        "-c", help="c_help_str", default_factory=lambda: ["z"]
    )


@command()
@click_config_options(Config)
def run(config):
    print("Config", config)


if __name__ == "__main__":
    run()
```

This script can be called from the command line. A configuration file can be
loaded via `--config <path>` and individual fields can be overwritten using
command line options such as `--a 5`.

```bash
$ python examples/simple.py --help
Usage: simple.py [OPTIONS]

Options:
  --config FILE
  -c TEXT        c_help_str
  --b TEXT
  --a INTEGER    a_help_str
  --help         Show this message and exit.
```

If there is no help argument in a field description (using
`field(help=<help string>)`), *click-config* tries to find a param description
based on the docstring of the dataclass.
Currently ReST, Google, Numpydoc-style and Epydoc docstrings are supported
(using the [docstring-parser package](https://github.com/rr-/docstring_parser)).


The resulting config object has all the features of a `dataclass` and, if
the `@config_class` decorator or `ConfigClass` base class have been used,
additionally methods for loading values from a file (`from_file`) and a
returning the values as a `dict` (`to_dict`).

The name of the argument (in the decorated CLI function; here `config`) can be
changed using the `name` argument of `click_config_options`.
This also affects the name of the option used to load configuration files.


## Installation

In your environment, run:

```pip install git+https://github.com/plonerma/click-config.git```
