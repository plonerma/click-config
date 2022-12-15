from os import PathLike
from pathlib import Path
from typing import Any, Callable, Dict


def get_loader(extension):
    """Load relevant module for reading a file with the given extension."""
    if extension not in ("toml", "yaml", "yml", "json"):
        raise RuntimeError(
            f"Unrecognized file format: '.{extension}' "
            "(supported are .toml, .yaml, and .json)."
        )

    loader: Callable

    if extension == "toml":
        try:
            from toml import load as toml_loader

            loader = toml_loader
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                f"Package toml is required to read .{extension} files."
            ) from exc

    elif extension in ("yaml", "yl"):
        try:
            from yaml import safe_load as yaml_loader

            loader = yaml_loader
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                f"Package pyyaml is required to read .{extension} files."
            ) from exc
    else:
        try:
            from json import load as json_loader

            loader = json_loader
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                f"Package json is required to read .{extension} files."
            ) from exc

    return loader


def read_config_file(path: PathLike) -> Dict[str, Any]:
    """Read config file.

    Can be of type toml, yaml, or json.
    """
    extension = Path(path).suffix[1:]

    loader = get_loader(extension)

    with open(path, "r", encoding="utf-8") as conf_file:
        return loader(conf_file)
