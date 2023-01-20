import json
from dataclasses import dataclass
from typing import List

from click import command
from click.testing import CliRunner

from click_config import ConfigClass, click_config_options, field


def test_experiment_series(request, tmp_path):
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
        print("\n---\n")

    file_content = """
    {
        "__series__": {
            "a": [0, 1, 2],
            "c": [["x", "y"], ["z"]]
        }
    }

    """

    conf_file = tmp_path / "config.json"

    with open(conf_file, "w", encoding="utf-8") as f:
        f.write(file_content)

    runner = CliRunner()
    result = runner.invoke(func, ["--b", "hello world", "--config", conf_file])

    print(result.output)

    assert result.exit_code == 0

    experiments = []

    for data in result.output.split("\n---\n"):
        data = data.strip()

        if len(data) == 0:
            continue

        experiments.append(json.loads(data.strip()))

    print(experiments)

    assert len(experiments) == 6

    for exp in experiments:
        assert exp["b"] == "hello world"

    expected_combinations = [
        (0, "x", "y"),
        (1, "x", "y"),
        (2, "x", "y"),
        (0, "z"),
        (1, "z"),
        (2, "z"),
    ]

    for exp in experiments:
        assert (exp["a"],) + tuple(exp["c"]) in expected_combinations
