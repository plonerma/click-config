"""This module shows a examplatory usage of the click-config package.

$ python examples/simple.py --epochs 10 --lr 1.0 -o path --optimizer sgd -h 1 -h 2
Config(epochs=10, learning_rate=1.0, output_dir=PosixPath('path'), comment='', optimizer='sgd', hidden_sizes=(1, 2))
"""


from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal

from click import command

from click_config import click_config_options, field


# use ConfigClass (imported from click_config) as a base class to get
# additional helper functions
@dataclass
class Config:
    """Some description.

    :param epochs: Number of epochs to train
    :param output_dir: This help text is ignored in cli (see --help)
    """

    # no default: field is required
    # annotated with int: only integers are accepted in the cli
    # help text is retrieved from doc string (see python simple.py --help)
    epochs: int

    # annotated with float: only floats are accepted in cli
    # specified option is used instead of field name
    learning_rate: float = field("--lr")

    # help text is passed via kw (this takes precedence)
    # field can be set with short (-o) and long option (--outdir)
    output_dir: Path = field(
        "-o", "--outdir", help="Where to store the results."
    )

    # field does not need to be set as a default value does exist
    comment: str = ""

    # Literal: only the specified options are accepted on the cli
    optimizer: Literal["sgd", "adam"] = "sgd"

    # to use default values for lists, use a default_factory (see dataclasses
    # documentation)
    # on the command line, the default value can be overwritten using mulitple
    # -h options
    hidden_sizes: List[int] = field(
        "-h", "--hidden", default_factory=lambda: [100, 10]
    )


@command()
@click_config_options(Config)
def run(config):
    print(config)


if __name__ == "__main__":
    run()
