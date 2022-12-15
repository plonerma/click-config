import json
from dataclasses import dataclass
from typing import List

import pytest
from click.testing import CliRunner

from click_config import (
    ConfigClass,
    click_config_options,
    command,
    config_class,
    field,
)


@pytest.fixture
def sample_config_class_decorator():
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
    def func(config):
        print(json.dumps(config.to_dict()))

    return func


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

    @command()
    @click_config_options(Config)
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

    @command()
    @click_config_options(Config)
    def func(config):
        print(json.dumps(ConfigClass.to_dict(config)))

    return func


config_class_types = [
    "sample_config_class_decorator",
    "sample_config_child_class",
    "sample_dataclass_config",
]


@pytest.mark.parametrize("config_type", config_class_types)
def test_help(config_type, request):
    func = request.getfixturevalue(config_type)

    runner = CliRunner()
    result = runner.invoke(func, ["--help"])

    print(result.output)

    lines = str(result.output).split("\n")

    assert any(
        [line.split() == "-c TEXT c_help_str".split() for line in lines]
    )

    assert any(
        [line.split()[:2] == "--a INTEGER".split() for line in lines]
    ), "Type of field 'a' was not inferred from the annotations."

    assert any(
        [line.split() == "--a INTEGER a_help_str".split() for line in lines]
    ), "Help string of a was not inferred from the doc string."

    assert result.exit_code == 0


@pytest.mark.parametrize("config_type", config_class_types)
def test_basic_example(config_type, request):
    func = request.getfixturevalue(config_type)

    runner = CliRunner()
    result = runner.invoke(func, ["--a", "1", "-c", "x", "-c", "y"])

    assert result.exit_code == 0

    output = json.loads(result.output)

    print("Output:", output)

    assert output["a"] == 1
    assert output["b"] == "test"
    assert output["c"] == ["x", "y"]


@pytest.mark.parametrize("config_type", config_class_types)
def test_required_fields(config_type, request):
    func = request.getfixturevalue(config_type)

    runner = CliRunner()
    result = runner.invoke(func, ["--b", "value"])

    print(result.output)
    assert result.exit_code != 0


_test_conf_files = {
    # config using yaml format
    "yaml": """
a: 2
c: [x, y]
""",
    # config using toml format
    "toml": """
a = 2
c = [ "x", "y" ]
""",
    # config using json format
    "json": """
{
    "a": 2,
    "c": ["x", "y"]
}
""",
}


@pytest.mark.parametrize("extension", _test_conf_files.keys())
@pytest.mark.parametrize("config_type", config_class_types)
def test_config_file(config_type, request, tmp_path, extension):
    func = request.getfixturevalue(config_type)

    file_content = _test_conf_files[extension]

    conf_file = tmp_path / f"config.{extension}"

    with open(conf_file, "w", encoding="utf-8") as f:
        f.write(file_content)

    runner = CliRunner()
    result = runner.invoke(func, ["--a", "1", "--config", str(conf_file)])

    assert result.exit_code == 0

    output = json.loads(result.output)

    print("Output:", output)

    assert output["a"] == 1
    assert output["b"] == "test"
    assert output["c"] == ["x", "y"]
