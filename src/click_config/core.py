"""Core functionality of click_config."""

import logging
from dataclasses import MISSING, Field
from dataclasses import field as dataclasses_field
from dataclasses import fields
from functools import wraps
from itertools import product
from os import PathLike
from typing import (
    Any,
    Callable,
    Dict,
    Literal,
    Mapping,
    Optional,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
)

import click
from docstring_parser import parse as parse_docstring

from .util import read_config_file, write_config_file

_dataclass_field_kw_names = {
    "default",
    "default_factory",
    "init",
    "repr",
    "hash",
    "compare",
    "metadata",
    "kw_only",
}


class RequiredFieldMissing(RuntimeError):
    def __init__(self, field_name):
        text = f"Required field '{field_name}' was not set."
        super().__init__(text)
        self.field_name = field_name
        self.message = text


def get_param_decls(_field: Field) -> Tuple:
    """Return complete `param_decls` for click option."""
    partial_param_decls = _field.metadata.get("partial_param_decls", ())

    if len(partial_param_decls) == 0:
        # if no cli option was given, construct from identifier
        partial_param_decls = (f"--{_field.name}",)

    return partial_param_decls + (_field.name,)


def get_attrs(_field: Field) -> Dict[str, Any]:
    """Generate attributes used for creating click options."""

    multiple = False
    click_type: Any = None

    # annotation of the field, retrieved by dataclass
    annotation = _field.type

    # generic base type (such as list, Literal)
    origin = get_origin(annotation)

    if origin is not None:
        if origin is Literal:
            click_type = click.Choice(get_args(annotation))
        elif origin is list:
            multiple = True
            args = get_args(annotation)

            if len(args) == 1:
                click_type = args[0]
        elif origin is Union:
            # potentially an optional field
            args = get_args(annotation)
            if str in args:
                click_type = str
            elif len(args) == 2:
                click_type = args[0]

    elif issubclass(annotation, list):
        multiple = True

    else:
        click_type = annotation

    attrs = dict(_field.metadata.get("attrs", {}))

    if multiple:
        # test if multiple was explicitly set to false
        assert attrs.get("multiple", True), (
            f"Annotation '{annotation}' is not compatible with the"
            "provided field (as multiple is set to False)."
        )

        attrs["multiple"] = True

    if "type" not in attrs and click_type is not None:
        # type has not been set explicitly
        attrs["type"] = click_type

    attrs["default"] = None  # defaults are handled by dataclass

    return attrs


def field(*param_decls: str, **kw: Any):
    """Return an object to identify config field.

    This field aids in creating a corresponding click option.
    """
    if "default" in kw and "default_factory" in kw:
        raise ValueError("cannot specify both default and default_factory")

    # since there are multiple ways of setting the value of a field,
    # the required option in the click option should not be set
    assert (
        "required" not in kw
    ), "Do not specify required (instead just do no set a default value)."

    # get keyword args which belong to the dataclass field
    dataclass_field_kw = {
        key: kw.pop(key) for key in _dataclass_field_kw_names if key in kw
    }

    dataclass_field_kw["metadata"] = {
        "attrs": kw,  # these will be passed to a click option
        "partial_param_decls": param_decls,
    }

    return dataclasses_field(**dataclass_field_kw)


def check_required_fields(cls: Type, data: Mapping):
    # if cls is dataclass, check if all required fields are set
    try:
        for _field in fields(cls):
            if (
                _field.default is MISSING
                and _field.default_factory is MISSING
                and _field.name not in data
            ):
                raise RequiredFieldMissing(_field.name)
    except TypeError:
        # not a dataclass, skip field checking
        pass


def from_dict(cls, data: Mapping, overwrite: Optional[Mapping] = None):
    """Create config from mapping.

    :param dict overrides: Overwrite specified fields.
    """

    fields = {**data}

    if overwrite:
        fields.update(overwrite)

    check_required_fields(cls, fields)

    return cls(**fields)


def from_file(cls, path: PathLike, overwrite: Optional[Mapping] = None):
    """Create config from json, toml, or yaml file.

    :param dict overrides: Overwrite specified fields.
    """
    data = read_config_file(path)

    return from_dict(cls, data, overwrite=overwrite)


def add_click_options(func: Callable, config_cls: Type, name: str) -> Callable:
    """Add options to a click command based on a dataclass.

    :param Callable func: Function (cli command) to decorate.
    :param Type config_cls: Configuration class. Must be a dataclass.
    :param str name: Name of the argument the resulting config object is passed
        as (as well as the resulting cli option).
    :returns: Callable -- the decorated function.
    :raises: TypeError
    """
    if config_cls.__doc__ is not None:
        # parse doc text, to generate help text for fields
        param_doc = {}

        for param in parse_docstring(config_cls.__doc__).params:
            param_doc[param.arg_name] = param.description

    for _field in fields(config_cls):
        assert isinstance(_field, Field)

        attrs = get_attrs(_field)
        param_decls = get_param_decls(_field)

        if "help" not in attrs and _field.name in param_doc:
            attrs["help"] = param_doc[_field.name]

        func = click.option(*param_decls, **attrs)(func)

    # add option for reading values from a file
    func = click.option(
        f"--{name}",
        default=None,
        type=click.Path(
            exists=True, file_okay=True, dir_okay=False, readable=True
        ),
    )(func)

    @wraps(func)
    def wrapped_func(**kw):
        cli_kw = {}

        for _field in fields(config_cls):
            value = kw.pop(_field.name, None)

            if value is None:
                # cli option was not used
                continue

            try:
                if len(value) == 0:
                    # option with multiple=True was not used
                    continue
            except TypeError:
                pass

            cli_kw[_field.name] = value

        # get path to config file
        conf_path = kw.pop(name, None)

        configurations = []

        try:
            if conf_path is None:
                # check if all required fields were set
                check_required_fields(config_cls, cli_kw)

                # create config directly from cli options
                configurations.append(config_cls(**cli_kw))
            else:
                # load config from file and overwrite values given via cli options
                data = read_config_file(conf_path)

                if "__series__" in data:
                    series = data.pop("__series__")
                    keys = series.keys()

                    for experiment in product(*series.values()):
                        exp_data = dict(zip(keys, experiment))

                        configurations.append(
                            from_dict(
                                config_cls,
                                {**data, **exp_data},
                                overwrite=cli_kw,
                            )
                        )

                else:
                    configurations.append(
                        from_dict(config_cls, data, overwrite=cli_kw)
                    )
        except RequiredFieldMissing as exc:
            raise click.UsageError(exc.message)

        for i, config in enumerate(configurations):
            if len(configurations) > 1:
                logging.info("__series__ run #%s/%s", i, len(configurations))

            # add config object to the kw args passed to the decorated funcion
            func_kw = dict(kw)
            func_kw[name] = config
            func(**func_kw)

    return wrapped_func


def click_config_options(
    cls: Type, func: Optional[Callable] = None, *, name: str = "config"
) -> Callable:
    """Decorator for attaching options of a class to a click command.

    Example: `@click_config_options(Config)`
    Note: Mypy likes using this more than using `@Config.click_options`.
    """

    def _process_func(func):
        return add_click_options(func, cls, name)

    if func is None:
        return _process_func
    return _process_func(func)


class ConfigClass:
    """Configuration base class which provides helper functions."""

    def to_dict(self) -> dict:
        """Represent the fields and values of configuration as a dict."""
        return {
            _field.name: getattr(self, _field.name) for _field in fields(self)
        }

    def to_file(self, path: PathLike):
        """Write config to json, toml, or yaml file."""
        data = self.to_dict()
        write_config_file(path, data)

    from_dict = classmethod(from_dict)
    from_file = classmethod(from_file)
    click_options = classmethod(click_config_options)
