import types as _types
import typing as _typing


def validate_shape(shape: tuple[int, ...], parameter_name: str | None = None) -> None:
    """
    Validates the indicated shape. All entries of the shape must be non-negative integers.

    :param shape: The shape to check.
    :param parameter_name: Optional. If specified, this is the parameter name the shape was supplied to.
    """

    if any(not isinstance(s, int) or s < 0 for s in shape):
        if parameter_name is None:
            raise ValueError('All entries of the shape must be non-negative integers.')
        else:
            raise ValueError(f'All entries of `{parameter_name}` must be non-negative integers.')


IndexDecl: _typing.TypeAlias = int | slice | _types.EllipsisType | None | _typing.Sequence[int] | _typing.Sequence[bool]
IndicesDecl = IndexDecl | tuple[IndexDecl, ...]
Index: _typing.TypeAlias = None | int | slice | _typing.Sequence[int] | _typing.Sequence[bool]
Indices: _typing.TypeAlias = tuple[Index, ...]


class NormalizeIndexResult(_typing.NamedTuple):
    indices: Indices
    original_axes: tuple[int | None, ...]

    @property
    def has_new_axes(self) -> bool:
        return any(ax is None for ax in self.original_axes)


def normalize_index(
        shape: tuple[int, ...], indices: IndicesDecl, fill: bool = True, parameter_name: str | None = None
) -> NormalizeIndexResult:
    if not isinstance(indices, _typing.Iterable):
        indices = (indices,)
    else:
        indices = tuple(indices)

    head_indices: list[Index] = []
    head_orig_axes: list[int | None] = []

    tail_indices: list[Index] | None = None
    tail_orig_axes: list[int | None] | None = None

    tgt_indices = head_indices
    tgt_orig_axes = head_orig_axes

    remaining_axes = len(shape)
    last_head_orig_index = 0

    orig_index = 0

    for i, v in enumerate(indices):
        if tail_indices is not None:
            # we fill if we encountered a tail index
            fill = True

        if v is ...:
            if tail_indices is not None:
                if parameter_name is None:
                    raise ValueError('At most one ellipsis may be specified in a multi-index.')
                else:
                    raise ValueError(f'At most one ellipsis may be specified in `{parameter_name}`.')

            # as soon as we encounter an ellipsis, we write to the tail, not to the head
            tgt_indices = tail_indices = []
            tgt_orig_axes = tail_orig_axes = []
            orig_index = len(shape) - sum(v is not None for v in indices[i + 1:])
        elif v is None:
            tgt_indices.append(None)
            tgt_orig_axes.append(None)
        else:
            if remaining_axes == 0:
                if parameter_name is None:
                    raise ValueError('Too many indices specified.')
                else:
                    raise ValueError(f'Too many indices specified for `{parameter_name}`.')

            tgt_indices.append(v)
            tgt_orig_axes.append(orig_index)
            orig_index += 1
            remaining_axes -= 1

            if tail_indices is None:
                last_head_orig_index = orig_index

    if fill and remaining_axes > 0:
        fill_base_index = last_head_orig_index

        head_indices.extend([slice(None)] * remaining_axes)
        head_orig_axes.extend(range(fill_base_index, fill_base_index + remaining_axes))

    if tail_indices is not None:
        head_indices.extend(tail_indices)
        head_orig_axes.extend(tail_orig_axes)  # type: ignore[arg-type]

    return NormalizeIndexResult(tuple(head_indices), tuple(head_orig_axes))


@_typing.overload
def unsqueeze(shape: tuple[int, ...], indices: tuple[int, ...], /) -> tuple[int, ...]:
    ...


@_typing.overload
def unsqueeze(shape: tuple[int, ...], /, *indices: int) -> tuple[int, ...]:
    ...


def unsqueeze(shape: tuple[int, ...], *indices: int | tuple[int, ...]) -> tuple[int, ...]:
    if len(indices) == 1 and isinstance(indices[0], _typing.Iterable):
        indices = indices[0]

    shape = list(shape)

    for i, idx in enumerate(indices):
        if idx < 0:
            idx += len(shape) + 1

        if idx < 0 or idx > len(shape):
            raise ValueError(f'Index {i} did not fall into the shape.')

        shape.insert(idx, 1)

    return tuple(shape)
