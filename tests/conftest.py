import json
from dataclasses import dataclass
from typing import List

import pytest

from click_config import ConfigClass, click_config_options, command, field


@pytest.fixture
def sample_config_child_class():
    @dataclass
    class Config(ConfigClass):
        """Some description.

        :param a: a_help_str
        """

        a: int
        b: str = "test"
        c: List[str] = field(
            "-c", help="c_help_str", default_factory=lambda: ["z"]
        )

    return Config


@pytest.fixture
def sample_config_child_class_routine(sample_config_child_class):
    @command()
    @click_config_options(sample_config_child_class)
    def func(config):
        print(json.dumps(config.to_dict()))

    return func


@pytest.fixture
def sample_dataclass_config():
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

    return Config


@pytest.fixture
def sample_dataclass_config_routine(sample_dataclass_config):
    @command()
    @click_config_options(sample_dataclass_config)
    def func(config):
        print(json.dumps(ConfigClass.to_dict(config)))

    return func
