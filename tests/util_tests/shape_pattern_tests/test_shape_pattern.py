import pytest

import bufferstruct.util.shape_pattern as ds


def test_init_pattern() -> None:
    instance = ds.ShapePattern('V', None, ds.AcceptedSizes([1, 2, 3]))

    assert len(instance.shape) == 3
    assert isinstance(instance.shape[0], ds.ShapeVariable) and instance.shape[0].name == 'V'
    assert instance.shape[1] is None
    assert isinstance(instance.shape[2], ds.AcceptedSizes)


@pytest.mark.parametrize('batched', [False, True])
def test_shape_match(batched: bool) -> None:
    instance = ds.ShapePattern('V', None, ds.AcceptedSizes([1, 2, 3]))

    match = instance.match((5, 7, 2), allow_batching=batched)

    assert match.success
    assert match.variable_assignment['V'] == 5


def test_batched() -> None:
    instance = ds.ShapePattern('V', None, ds.AcceptedSizes([1, 2, 3]))

    match = instance.match((5, 7, 2), allow_batching=True)

    assert match.batch_shape == ()


def test_non_batched() -> None:
    instance = ds.ShapePattern('V', None, ds.AcceptedSizes([1, 2, 3]))

    match = instance.match((5, 7, 2), allow_batching=False)

    assert match.batch_shape is None


def test_too_few_values_error() -> None:
    instance = ds.ShapePattern('V', None, ds.AcceptedSizes([1, 2, 3]))

    with pytest.raises(ValueError):
        instance.match((7, 2), raise_errors=True)


def test_too_few_values_silent() -> None:
    instance = ds.ShapePattern('V', None, ds.AcceptedSizes([1, 2, 3]))

    match = instance.match((7, 2), raise_errors=False)

    assert not match


def test_too_many_values_batched() -> None:
    instance = ds.ShapePattern('V', None, ds.AcceptedSizes([1, 2, 3]))

    match = instance.match((9, 5, 7, 2), allow_batching=True)

    assert match.success
    assert match.batch_shape == (9,)
    assert match.variable_assignment['V'] == 5


def test_too_many_values_nonbatched_error() -> None:
    instance = ds.ShapePattern('V', None, ds.AcceptedSizes([1, 2, 3]))

    with pytest.raises(ValueError):
        instance.match((9, 5, 7, 2), allow_batching=False, raise_errors=True)


def test_too_many_values_nonbatched_silent() -> None:
    instance = ds.ShapePattern('V', None, ds.AcceptedSizes([1, 2, 3]))

    match = instance.match((9, 5, 7, 2), allow_batching=False, raise_errors=False)

    assert not match


@pytest.mark.parametrize('batched', [False, True])
def test_empty_shape(batched: bool) -> None:
    instance = ds.ShapePattern()
    assert instance.match((), allow_batching=batched)


@pytest.mark.parametrize('batched', [False, True])
def test_singleton(batched: bool) -> None:
    instance = ds.ShapePattern(None)
    assert instance.match((1,), allow_batching=batched)


@pytest.mark.parametrize('batched', [False, True])
def test_bound_shapevars(batched: bool) -> None:
    instance = ds.ShapePattern('Q', 'Q')

    match = instance.match((3, 3), allow_batching=batched)

    assert match
    assert match['Q'] == 3


def test_bound_shapevars_batched() -> None:
    instance = ds.ShapePattern('Q', 'Q')

    match = instance.match((5, 3, 3), allow_batching=True)

    assert match['Q'] == 3


@pytest.mark.parametrize('batched', [False, True])
def test_bound_shapevars_mismatch(batched: bool) -> None:
    instance = ds.ShapePattern('Q', 'Q')

    with pytest.raises(ValueError):
        instance.match((3, 4), allow_batching=batched)


@pytest.mark.parametrize('batched', [False, True])
def test_shape_pos_constraint_mismatch_error(batched: bool) -> None:
    instance = ds.ShapePattern('V', None, ds.AcceptedSizes([1, 2, 3]))

    with pytest.raises(ValueError):
        instance.match((5, 7, 4), allow_batching=batched)


@pytest.mark.parametrize('batched', [False, True])
def test_shape_pos_constraint_mismatch_silent(batched: bool) -> None:
    instance = ds.ShapePattern('V', None, ds.AcceptedSizes([1, 2, 3]))

    assert not instance.match((5, 7, 4), allow_batching=batched, raise_errors=False)


@pytest.mark.parametrize('batched', [False, True])
def test_shape_kw_constraint(batched: bool) -> None:
    instance = ds.ShapePattern('U', 'V', variable_constraints={'V': ds.AcceptedSizes(5)})

    assert instance.match((1, 5), allow_batching=batched, raise_errors=False)


@pytest.mark.parametrize('batched', [False, True])
def test_shape_kw_constraint_mismatch_error(batched: bool) -> None:
    instance = ds.ShapePattern('U', 'V', variable_constraints={'V': ds.AcceptedSizes(5)})

    with pytest.raises(ValueError):
        instance.match((1, 2), allow_batching=batched)


@pytest.mark.parametrize('batched', [False, True])
def test_shape_kw_constraint_mismatch_silent(batched: bool) -> None:
    instance = ds.ShapePattern('U', 'V', variable_constraints={'V': ds.AcceptedSizes(5)})

    assert not instance.match((1, 2), allow_batching=batched, raise_errors=False)


@pytest.mark.parametrize('batched', [False, True])
def test_shape_kw_constraint_mixed_disjoint(batched: bool) -> None:
    instance = ds.ShapePattern('U', 'V', variable_constraints={'U': ds.AcceptedSizes(5)}, V=ds.AcceptedSizes(6))

    match = instance.match((5, 6), allow_batching=batched)

    assert match['U'] == 5
    assert match['V'] == 6


def test_shape_kw_constraint_mixed_overlapping() -> None:
    with pytest.raises(ValueError):
        ds.ShapePattern('U', 'V', variable_constraints={'U': ds.AcceptedSizes(5)}, U=ds.AcceptedSizes(6))


def test_shape_kw_constraint_without_member() -> None:
    with pytest.raises(ValueError):
        ds.ShapePattern(None, variable_constraints={'U': ds.AcceptedSizes(5)})


def test_shape_kw_constraint_without_member_kwargs() -> None:
    with pytest.raises(ValueError):
        ds.ShapePattern(None, U=ds.AcceptedSizes(5))


def test_repr_singleton() -> None:
    assert repr(ds.ShapePattern('U')) == '(U,)'


def test_repr_vars() -> None:
    assert repr(ds.ShapePattern('U', 'V')) == '(U, V)'


def test_repr_mixed() -> None:
    assert repr(ds.ShapePattern('U', None)) == '(U, *)'


def test_format_batched_singleton() -> None:
    assert ds.ShapePattern('U')._format(include_batch_axis=True) == '(..., U)'


def test_format_batched_vars() -> None:
    assert ds.ShapePattern('U', 'V')._format(include_batch_axis=True) == '(..., U, V)'


def test_format_batched_mixed() -> None:
    assert ds.ShapePattern('U', None)._format(include_batch_axis=True) == '(..., U, *)'


def test_predeclared_var() -> None:
    U = ds.ShapeVariable('U')

    instance = ds.ShapePattern(U, variable_constraints={U: ds.AcceptedSizes(5)})

    assert instance.match((5,))


def test_predeclared_var_mixed() -> None:
    U = ds.ShapeVariable('U')

    instance = ds.ShapePattern('U', variable_constraints={U: ds.AcceptedSizes(5)})

    assert instance.match((5,))
