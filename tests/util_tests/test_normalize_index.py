import pytest

from bufferstruct.util import normalize_index


def test_few_indices_fill() -> None:
    shape = (2, 3, 5, 7)
    indices = (1, 2)

    normalized = normalize_index(shape, indices, fill=True)

    assert normalized.indices == (1, 2, slice(None), slice(None))
    assert normalized.original_axes == (0, 1, 2, 3)


def test_few_indices_no_fill() -> None:
    shape = (2, 3, 5, 7)
    indices = (1, 2)

    normalized = normalize_index(shape, indices, fill=False)

    assert normalized.indices == (1, 2)
    assert normalized.original_axes == (0, 1)


@pytest.mark.parametrize('fill', [True, False])
def test_matching_index_count(fill: bool) -> None:
    shape = (2, 3, 5, 7)
    indices = (1, 2, 3, 4)

    normalized = normalize_index(shape, indices, fill=fill)

    assert normalized.indices == (1, 2, 3, 4)
    assert normalized.original_axes == (0, 1, 2, 3)


@pytest.mark.parametrize('fill', [True, False])
def test_too_many_indices(fill: bool) -> None:
    shape = (2, 3, 5, 7)
    indices = (1, 2, 3, 4, 5)

    with pytest.raises(ValueError):
        normalize_index(shape, indices, fill=fill)


@pytest.mark.parametrize('fill', [True, False])
def test_ellipsis(fill: bool) -> None:
    shape = (2, 3, 5, 7)
    indices = (1, ..., 4)

    normalized = normalize_index(shape, indices, fill=fill)

    assert normalized.indices == (1, slice(None), slice(None), 4)
    assert normalized.original_axes == (0, 1, 2, 3)


@pytest.mark.parametrize('fill', [True, False])
def test_ellipsis_multiple(fill: bool) -> None:
    shape = (2, 3, 5, 7)
    indices = (1, ..., ...)

    with pytest.raises(ValueError):
        normalize_index(shape, indices, fill=fill)


@pytest.mark.parametrize('fill', [True, False])
def test_ellipsis_front(fill: bool) -> None:
    shape = (2, 3, 5, 7)
    indices = (..., 4)

    normalized = normalize_index(shape, indices, fill=fill)

    assert normalized.indices == (slice(None), slice(None), slice(None), 4)
    assert normalized.original_axes == (0, 1, 2, 3)


@pytest.mark.parametrize('fill', [True, False])
def test_ellipsis_back(fill: bool) -> None:
    shape = (2, 3, 5, 7)
    indices = (1, ...)

    normalized = normalize_index(shape, indices, fill=fill)

    if fill:
        assert normalized.indices == (1, slice(None), slice(None), slice(None))
        assert normalized.original_axes == (0, 1, 2, 3)
    else:
        assert normalized.indices == (1,)
        assert normalized.original_axes == (0,)


@pytest.mark.parametrize('fill', [True, False])
def test_ellipsis_matching_index_count(fill: bool) -> None:
    shape = (2, 3, 5, 7)
    indices = (1, 2, 3, ..., 4)

    normalized = normalize_index(shape, indices, fill=fill)

    assert normalized.indices == (1, 2, 3, 4)
    assert normalized.original_axes == (0, 1, 2, 3)


@pytest.mark.parametrize('fill', [True, False])
def test_ellipsis_too_many_indices(fill: bool) -> None:
    shape = (2, 3, 5, 7)
    indices = (1, 2, 3, ..., 4, 5)

    with pytest.raises(ValueError):
        normalize_index(shape, indices, fill=fill)


def test_none() -> None:
    shape = (2, 3, 5, 7)
    indices = (1, 2, None, 3, 4)

    normalized = normalize_index(shape, indices)

    assert normalized.indices == (1, 2, None, 3, 4)
    assert normalized.original_axes == (0, 1, None, 2, 3)


def test_none_few_indices_fill() -> None:
    shape = (2, 3, 5, 7)
    indices = (1, 2, None)

    normalized = normalize_index(shape, indices, fill=True)

    assert normalized.indices == (1, 2, None, slice(None), slice(None))
    assert normalized.original_axes == (0, 1, None, 2, 3)


def test_none_few_indices_no_fill() -> None:
    shape = (2, 3, 5, 7)
    indices = (1, 2, None, 3)

    normalized = normalize_index(shape, indices, fill=False)

    assert normalized.indices == (1, 2, None, 3)
    assert normalized.original_axes == (0, 1, None, 2)


@pytest.mark.parametrize('fill', [True, False])
def test_none_matching_index_count(fill: bool) -> None:
    shape = (2, 3, 5, 7)
    indices = (1, 2, 3, None, 4)

    normalized = normalize_index(shape, indices, fill=fill)

    assert normalized.indices == (1, 2, 3, None, 4)
    assert normalized.original_axes == (0, 1, 2, None, 3)


@pytest.mark.parametrize('fill', [True, False])
def test_none_too_many_indices(fill: bool) -> None:
    shape = (2, 3, 5, 7)
    indices = (1, 2, 3, None, 4, 5)

    with pytest.raises(ValueError):
        normalize_index(shape, indices, fill=fill)


@pytest.mark.parametrize('fill', [True, False])
def test_ellipsis_none(fill: bool) -> None:
    shape = (2, 3, 5, 7)
    indices = (1, ..., None, 4)

    normalized = normalize_index(shape, indices, fill=fill)

    assert normalized.indices == (1, slice(None), slice(None), None, 4)
    assert normalized.original_axes == (0, 1, 2, None, 3)


@pytest.mark.parametrize('fill', [True, False])
def test_ellipsis_none_matching_index_count(fill: bool) -> None:
    shape = (2, 3, 5, 7)
    indices = (1, 2, 3, ..., None, 4)

    normalized = normalize_index(shape, indices, fill=fill)

    assert normalized.indices == (1, 2, 3, None, 4)
    assert normalized.original_axes == (0, 1, 2, None, 3)


@pytest.mark.parametrize('fill', [True, False])
def test_ellipsis_none_too_many_indices(fill: bool) -> None:
    shape = (2, 3, 5, 7)
    indices = (1, 2, 3, ..., None, 4, 5)

    with pytest.raises(ValueError):
        normalize_index(shape, indices, fill=fill)


@pytest.mark.parametrize('fill', [True, False])
def test_ellipsis_none_front(fill: bool) -> None:
    shape = (2, 3, 5, 7)
    indices = (..., 1, 2, 3, None, 4)

    normalized = normalize_index(shape, indices, fill=fill)

    assert normalized.indices == (1, 2, 3, None, 4)
    assert normalized.original_axes == (0, 1, 2, None, 3)


@pytest.mark.parametrize('fill', [True, False])
def test_ellipsis_none_back(fill: bool) -> None:
    shape = (2, 3, 5, 7)
    indices = (1, 2, 3, None, 4, ...)

    normalized = normalize_index(shape, indices, fill=fill)

    assert normalized.indices == (1, 2, 3, None, 4)
    assert normalized.original_axes == (0, 1, 2, None, 3)
