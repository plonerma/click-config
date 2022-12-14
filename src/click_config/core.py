"""Core functionality of click_config."""

import dataclasses
from dataclasses import Field as DataclassesField
from dataclasses import dataclass, fields
from functools import wraps
from os import PathLike
from typing import (
    Any,
    Callable,
    Literal,
    Mapping,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

import click
from docstring_parser import parse as parse_docstring

from .util import read_config_file

_dataclass_default_field_kws = {
    "default": dataclasses.MISSING,
    "default_factory": dataclasses.MISSING,
    "init": True,
    "repr": True,
    "hash": None,
    "compare": True,
}


class Field(DataclassesField):
    """Represents a field in a configuration class.

    This class is derived from `dataclasses.Field` and is essentially a
    (mostly) read-only description of a config field. It is used to create
    click options for creating a cli.
    """

    def __init__(self, *partial_param_decls, **kw):
        """Create a new field representation.

        Accepts the same kw arguments as `dataclasses.Field`, but additionally
        accepts param_decls and kw args used for the click option.
        """
        # get keyword args which belong to the dataclass field
        dataclass_field_kw = {
            key: kw.pop(key, default_value)
            for key, default_value in _dataclass_default_field_kws.items()
        }

        # since there are multiple ways of setting the value of a field,
        # the required option in the click option should not be set
        assert (
            "required" not in kw
        ), "Do not specify required (instead just do no set a default value)."

        dataclass_field_kw["metadata"] = {
            "attrs": kw,  # these will be passed to a click option
            "partial_param_decls": partial_param_decls,
        }

        super().__init__(**dataclass_field_kw)

    @property
    def param_decls(self) -> Tuple:
        """Return complete `param_decls` for click option."""
        partial_param_decls = self.metadata["partial_param_decls"]

        if len(partial_param_decls) == 0:
            # if no cli option was given, construct from identifier
            partial_param_decls = (f"--{self.name}",)

        return partial_param_decls + (self.name,)

    @property
    def attrs(self):
        """Attributes used for creating click options."""
        return {**self.metadata["attrs"], "default": None}

    def sync_type(self):
        """Assign converted (click compatible) annotation to this field."""
        multiple = False
        click_type: Any = None

        # annotation of the field, retrieved by dataclass
        annotation = self.type

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

        elif issubclass(annotation, list):
            multiple = True

        else:
            click_type = annotation

        if multiple:
            # test if multiple was explicitly set to false
            assert self.metadata["attrs"].get("multiple", True), (
                f"Annotation '{annotation}' is not compatible with the"
                "provided field (as multiple is set to False)."
            )

            self.metadata["attrs"]["multiple"] = True

        if "type" not in self.metadata["attrs"] and click_type is not None:
            # type has not been set explicitly
            self.metadata["attrs"]["type"] = click_type


def field(*param_decls: str, **kw: Any):
    """Return an object to identify config field.

    This field aids in creating a corresponding click option.
    """
    if "default" in kw and "default_factory" in kw:
        raise ValueError("cannot specify both default and default_factory")
    return Field(*param_decls, **kw)


class ConfigClass(Protocol):
    def to_dict(self) -> dict:
        ...

    def from_file(self, path: PathLike, overwrite: Optional[Mapping] = None):
        ...


T = TypeVar("T", bound=Type)


def config_class(
    cls: Optional[T] = None, /, **kw
) -> Union[Callable[..., T], T]:
    """Generate special methods for config class."""

    def make_config_class(cls: T) -> T:
        # make dataclass out of existing class

        # drop in our own field class (a bit hacky, but works)
        old_field = dataclasses.field
        dataclasses.field = field

        cls = cast(T, dataclass(order=False, **kw)(cls))

        # reset old field typoe of dataclasses
        dataclasses.field = old_field

        # if click type exists, check compatiblity with annotation
        # else set click type accordingly
        for _field in fields(cls):
            _field = cast(Field, _field)
            _field.sync_type()

        if cls.__doc__ is not None:
            # parse doc text, to generate help text for fields
            param_doc = {}

            for param in parse_docstring(cls.__doc__).params:
                param_doc[param.arg_name] = param.description

            for _field in fields(cls):
                if (
                    "help" not in _field.metadata["attrs"]
                    and _field.name in param_doc
                ):
                    _field.metadata["attrs"]["help"] = param_doc[_field.name]

        # add to_dict function
        def to_dict(self):
            """Represent the fields and values of configuration as a dict."""
            return {
                _field.name: getattr(self, _field.name)
                for _field in fields(self)
            }

        cls.to_dict = to_dict

        # add function to load configuration from file (and potentiall
        # overwrite some of the fields)
        def from_file(cls, path, overwrite=None):
            """Create config from json, toml, or yaml file.

            :param dict overrides: Overwrite specified fields.
            """
            data = read_config_file(path)

            if overwrite:
                data.update(overwrite)

            return cls(**data)

        cls.from_file = classmethod(from_file)

        # add decorator function for adding config to click command
        cls.click_options = classmethod(click_config_options)

        return cls

    if cls is None:
        return make_config_class

    return make_config_class(cls)


def add_click_options(func: Callable, config_cls: Type, name: str) -> Callable:
    """Add options to a click command based on this config."""
    # add a click option for each of the fields
    for _field in fields(config_cls):
        assert isinstance(_field, Field)

        attrs = _field.attrs

        func = click.option(*_field.param_decls, **attrs)(func)

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

        if conf_path is None:
            # create config directly from cli options
            config = config_cls(**cli_kw)
        else:
            # load config from file and overwrite values given via cli options
            config = config_cls.from_file(conf_path, overwrite=cli_kw)

        # add config object to the kw args passed to the decorated funcion
        kw[name] = config

        return func(**kw)

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
