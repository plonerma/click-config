# Click-Config

Click-config offers a small wrapper around `dataclass` to enable the population
of a config class with values from a config file (yaml, toml, or json) and
command line options.


## Example Usage

```
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
cli options such as `--a 5`.
