import types as _types
import typing as _typing


@_typing.runtime_checkable
class Shaped(_typing.Protocol):
    """A protocol that defines shape and length."""

    @property
    def shape(self) -> tuple[int, ...]:
        """
        The shape of the current instance.

        :return: The shape as a tuple. The values are required to be non-negative integers.
        """
        ...

    def __len__(self) -> int:
        """
        The length of the current instance.

        :return: The length of the current instance. This must be equal to the first value of `shape`.
        :raises RuntimeError: Raised if the current instance is a singleton (i.e., it has a shape of length 0).
        """
        ...


class ReadableBuffer[T](Shaped, _typing.Protocol):
    """
    A buffer that supports reading.

    The buffer's size must be immutable.
    """

    @_typing.overload
    def __getitem__(self, s: slice, /) -> ReadableBuffer[T]:
        """
        Slices the current instance and returns a view of the current buffer (i.e., the content of the buffer does not
        get copied).

        :param s: The slice indicating the start, stop, and step the view uses.
        :return: The sliced buffer view.
        """
        ...

    @_typing.overload
    def __getitem__(self, index: int, /) -> ReadableBuffer[T] | T:
        """
        Indexes into the current instance and returns either a view of the sub-buffer or the element at the index.
        Returns a view of the item or sub-buffer (i.e., the content of the buffer does not get copied).

        :param index: The index of the item or sub-buffer to extract.
        :return:
        """
        ...

    @_typing.overload
    def __getitem__(
        self,
        args: tuple[_types.EllipsisType | None | int | slice | _typing.Sequence[int] | _typing.Sequence[bool], ...],
    ) -> _typing.Self:
        """
        Combines the different types of access operations to the buffer's axes.
        Returns either a view into the current buffer or a new buffer: If any operation by itself would not return a
        view, a new buffer is created, otherwise a view is returned. The indexing is per-axis.

        The following operations are supported:

        * `int`: The item at the position in the respective axis gets selected. Returns a view.
        * `slice`: The range in the respective axis gets selected. Returns a view.
        * buffer: Either masking or indexing is performed across the respective axis. Returns a new buffer.
        * `None`: A new axis is created. Returns a view.
        * `...`: The indices following the ellipsis are relative to the last axis. Note that only one ellipsis is
            allowed per indexing operation.

        :param args: A tuple of indexing modes.
        :return: The view or new buffer.
        """
        ...

    @_typing.overload
    def __getitem__(self, mask: _typing.Sequence[bool], /) -> _typing.Self | T:
        """
        Returns a new buffer containing the items for which the indicated mask is `True`.

        :param mask: The mask which is `True` for all items to pick and `False` for all other items. It must have the
            same length as the current instance.
        :return: A buffer containing the selected items.
        """
        ...

    @_typing.overload
    def __getitem__(self, indices: _typing.Sequence[int], /) -> _typing.Self | T:
        """
        Returns a new buffer containing the indexed items.

        :param indices: The indices of the items to take.
        :return: A buffer containing the selected items.
        """
        ...
