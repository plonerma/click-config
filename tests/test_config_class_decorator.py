from dataclasses import fields

import pytest

from click_config import config_class, field


def test_no_annotation_field():
    with pytest.raises(TypeError):

        @config_class
        class Test:
            a: int
            b: str = "test"
            c = field(help="some value")


def test_no_annotation_no_field():
    @config_class
    class Test:
        a: int
        b = "test"

    test_fields = tuple(_field.name for _field in fields(Test))

    assert test_fields == ("a",)
