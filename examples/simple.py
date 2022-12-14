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
# Alternativ (but mypy does not like it): @Config.click_options
def run(config):
    print("Config", config)


if __name__ == "__main__":
    run()
