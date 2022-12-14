from typing import Any, Dict


def get_loader(extension):
    """Load relevant module for reading a file with the given extension."""
    if extension not in ("toml", "yaml", "yml", "json"):
        raise RuntimeError(
            f"Unrecognized file format: '.{extension}' "
            "(supported are .toml, .yaml, and .json).")

    if extension == "toml":
        try:
            from toml import load as loader
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                f"Package toml is required to read .{extension} files."
            ) from exc

    elif extension in ("yaml", "yl"):
        try:
            from yaml import safe_load as loader
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                f"Package pyyaml is required to read .{extension} files."
            ) from exc
    else:
        try:
            from json import load as loader
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                f"Package json is required to read .{extension} files."
            ) from exc

    return loader


def read_config_file(path: str) -> Dict[str, Any]:
    """Read config file.

    Can be of type toml, yaml, or json.
    """
    extension = path.split(".")[-1]

    loader = get_loader(extension)

    with open(path, "r", encoding="utf-8") as conf_file:
        return loader(conf_file)
