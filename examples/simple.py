from typing import List

import click

from click_config import click_config_options, config_class, field


@config_class
class Config:
    """Some description.

    :param a: a_help_str
    """

    a: int
    b: str = "test"
    c: List[str] = field("-c", help="c_help_str", default=["z"])


@click.command()
@click_config_options(Config)
# Alternativ (but mypy does not like it): @Config.click_options
def run(config):
    print("Config", config)


if __name__ == "__main__":
    run()
