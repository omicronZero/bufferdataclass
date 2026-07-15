import pytest

from bufferstruct.util import validate_shape


def test_valid() -> None:
    shape = (0, 1, 2, 3)

    validate_shape(shape)


def test_invalid() -> None:
    shape = (-1,)

    with pytest.raises(ValueError):
        validate_shape(shape)


def test_empty() -> None:
    validate_shape(())
