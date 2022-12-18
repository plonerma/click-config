import json

import pytest
from click.testing import CliRunner

config_class_types = [
    "sample_config_child_class_routine",
    "sample_dataclass_config_routine",
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
