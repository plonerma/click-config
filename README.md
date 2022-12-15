# Click-Config

Click-config enables the use of dataclasses as config objects which can be read
from configurations files (yaml, toml, or json; the type is derived from the
file extension).
Values in the config file can be overwritten using command line options
(click-config integrates dataclasses with [click](https://click.palletsprojects.com/en/8.1.x/)).


## Example Usage

For a more detailed description of each field, see `examples/simple.py`.

```python
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal

from click import command

from click_config import click_config_options, field


@dataclass
class Config:
    """Some description.

    :param epochs: Number of epochs to train
    :param output_dir: This help text is ignored in cli (see --help)
    """

    epochs: int
    learning_rate: float = field("--lr")
    output_dir: Path = field(
        "-o", "--outdir", help="Where to store the results."
    )
    comment: str = ""
    optimizer: Literal["sgd", "adam"] = "sgd"
    hidden_sizes: List[int] = field(
        "-h", "--hidden", default_factory=lambda: [100, 10]
    )

@command()
@click_config_options(Config)
def run(config):
    print(config)


if __name__ == "__main__":
    run()
```

This script can be called from the command line. A configuration file can be
loaded via `--config <path>` and individual fields can be overwritten using
command line options such as `--comment "test comment"`.

A help text describing each parameter and its type is automatically generated.

```bash
$ python examples/simple.py --help
Usage: simple.py [OPTIONS]

Options:
  --config FILE
  -h, --hidden INTEGER
  --optimizer [sgd|adam]
  --comment TEXT
  -o, --outdir PATH       Where to store the results.
  --lr FLOAT
  --epochs INTEGER        Number of epochs to train
  --help                  Show this message and exit.
```

If there is no help argument in a field description (using
`field(help=<help string>)`), *click-config* tries to find a param description
based on the docstring of the class.
Currently ReST, Google, Numpydoc-style and Epydoc docstrings are supported
(using the [docstring-parser package](https://github.com/rr-/docstring_parser)).

The resulting config object has all the features of a `dataclass` and, if
the `@config_class` decorator or `ConfigClass` base class have been used,
additionally methods for loading values from a file (`from_file`) and a
returning the values as a `dict` (`to_dict`) are added.

The name of the argument (in the decorated CLI function; here `config`) can be
changed using the `name` argument of `click_config_options`.
This also affects the name of the option used to load configuration files.


## Installation

In your environment, run:

```pip install git+https://github.com/plonerma/click-config.git```
