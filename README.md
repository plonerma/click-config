# Click-Config

Click-config offers a small wrapper around `dataclass` to enable the population
of a config class with values from a config file (yaml, toml, or json; the type
is derived from the file extension) and command line options.


## Example Usage

```python
from typing import List

from click_config import click_config_options, command, config_class, field


@config_class
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

The resulting config object has all the features of a `dataclass` and additionally
methods for loading values from a file (`from_file`) and a returning the values
as a `dict` (`to_dict`).

The name of the argument (in the decorated CLI function; here `config`) can be
changed using the `name` argument of `click_config_options`.
This also affects the name of the option used to load configuration files.


## Installation

In your environment, run:

```pip install git+https://github.com/plonerma/click-config.git```
