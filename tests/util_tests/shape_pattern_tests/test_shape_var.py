import pytest

import bufferstruct.util.shape_pattern as ds


def test_illegal_shapevar_format() -> None:
    with pytest.raises(ValueError):
        ds.ShapeVariable('.')


def test_illegal_shapevar_empty() -> None:
    with pytest.raises(ValueError):
        ds.ShapeVariable('')


def test_shape_var_repr() -> None:
    assert repr(ds.ShapeVariable('U')) == "ShapeVariable('U')"


def test_shape_var_str() -> None:
    assert str(ds.ShapeVariable('U')) == 'U'


def test_shape_var_equality() -> None:
    assert ds.ShapeVariable('U') == ds.ShapeVariable('U')
    assert hash(ds.ShapeVariable('U')) == hash(ds.ShapeVariable('U'))
    assert ds.ShapeVariable('V') != ds.ShapeVariable('U')
