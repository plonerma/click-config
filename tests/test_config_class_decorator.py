import pytest

from dataclasses import fields

from click_config import config_class, field


def test_no_annotation_field():
    with pytest.raises(TypeError):
        @config_class
        class Test:
            a: int
            b: str = 1
            c = field(help="some value")

def test_no_annotation_no_field():
    @config_class
    class Test:
        a: int
        b = 1

    test_fields = tuple(_field.name for _field in fields(Test))

    assert test_fields == ("a", )
