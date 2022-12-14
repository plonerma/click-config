from typing import List

import json


import pytest

from click.testing import CliRunner

from click_config import config_class, command, field


@pytest.fixture
def basic_func():
    @config_class
    class Config:
        """Some description.

        :param a: a_help_str
        """
        a: int
        b: str = "test"
        c: List[str] = field(
            "-c", help="c_help_str", default_factory=lambda: ["z"])

    @command()
    @Config.click_options
    def func(config):
        print(json.dumps(config.to_dict()))

    return func


def test_help(basic_func):
    runner = CliRunner()
    result = runner.invoke(basic_func, ["--help"])

    print(result.output)

    lines = str(result.output).split("\n")

    assert any([
        line.split() == "-c TEXT c_help_str".split()
        for line in lines
    ])

    assert any([
        line.split()[:2] == "--a INTEGER".split()
        for line in lines
    ]), "Type of field 'a' was not inferred from the annotations."

    assert any([
        line.split() == "--a INTEGER a_help_str".split()
        for line in lines
    ]), "Help string of a was not inferred from the doc string."

    assert result.exit_code == 0


def test_basic_example(basic_func):
    runner = CliRunner()
    result = runner.invoke(basic_func, ["--a", "1", "-c", "x", "-c", "y"])

    assert result.exit_code == 0

    output = json.loads(result.output)

    print("Output:", output)

    assert output["a"] == 1
    assert output["b"] == "test"
    assert output["c"] == ["x", "y"]


def test_required_fields(basic_func):
    runner = CliRunner()
    result = runner.invoke(basic_func, ["--b", "value"])

    print(result.output)
    assert result.exit_code != 0


_test_conf_files = dict([
    ("yaml", """
a: 2
c: [x, y]
"""),

    ("toml", """
a = 2
c = [ "x", "y" ]
"""),

    ("json", """
{
    "a": 2,
    "c": ["x", "y"]
}
""")
])

@pytest.mark.parametrize("extension", _test_conf_files.keys())
def test_config_file(basic_func, tmp_path, extension):
    file_content = _test_conf_files[extension]

    conf_file = tmp_path / f"config.{extension}"

    with open(conf_file, "w", encoding="utf-8") as f:
        f.write(file_content)

    runner = CliRunner()
    result = runner.invoke(basic_func, ["--a", "1", "--config", str(conf_file)])

    assert result.exit_code == 0

    output = json.loads(result.output)

    print("Output:", output)

    assert output["a"] == 1
    assert output["b"] == "test"
    assert output["c"] == ["x", "y"]
