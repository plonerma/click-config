import json

import pytest
from click.testing import CliRunner

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
def test_read_write(sample_config_child_class, request, tmp_path, extension):
    file_content = _test_conf_files[extension]

    conf_file = tmp_path / f"config.{extension}"

    # write tile content to file
    with open(conf_file, "w", encoding="utf-8") as f:
        f.write(file_content)

    # read config file from content
    config = sample_config_child_class.from_file(conf_file)

    # write config to second file (this time from the config object)
    second_config_path = tmp_path / f"config_second.{extension}"
    config.to_file(second_config_path)

    # create second config object from file
    second_config = sample_config_child_class.from_file(second_config_path)

    assert config == second_config


config_class_types = [
    "sample_config_child_class_routine",
    "sample_dataclass_config_routine",
]


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
