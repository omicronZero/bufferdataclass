import types as _types
import typing as _typing


@_typing.runtime_checkable
class Named(_typing.Protocol):
    __name__: str


@_typing.runtime_checkable
class QualNamed(_typing.Protocol):
    __qualname__: str


@_typing.runtime_checkable
class ModuleMember(_typing.Protocol):
    __module__: str
    __qualname__: str


def nameof(
    obj: _typing.Any,
    fallback: _typing.Callable[[_typing.Any], str] | None = None,
    prune_modules: _typing.Container[str] = (),
    prune_builtins: bool = True,
    prune_main: bool = True,
) -> str:
    if isinstance(obj, property):
        return nameof(obj.fget or obj.fset or obj.fdel, fallback, prune_modules, prune_builtins, prune_main)

    module = None

    if isinstance(obj, ModuleMember):
        module = obj.__module__
        name = obj.__qualname__
    elif isinstance(obj, QualNamed):
        name = obj.__qualname__
    elif isinstance(obj, Named):
        name = obj.__name__
    elif fallback is not None:
        return fallback(obj)
    else:
        raise TypeError('The indicated object could not be represented as a name.')

    if module is not None:
        if module in prune_modules:
            module = None
        elif prune_builtins and module == 'builtins':
            module = None
        elif prune_main and module == '__main__':
            module = None

    if module is None:
        return name
    else:
        return f'{module}.{name}'


def classnameof(
    obj: _typing.Any,
    fallback: _typing.Callable[[_typing.Any], str] | None = None,
    prune_modules: _typing.Container[str] = (),
    prune_builtins: bool = True,
    prune_main: bool = True,
) -> str:
    if isinstance(obj, property):
        return classnameof(obj.fget or obj.fset or obj.fdel, fallback, prune_modules, prune_builtins, prune_main)

    return nameof(type(obj), fallback, prune_modules, prune_builtins, prune_main)


@_typing.overload
def bullet(
    items: _typing.Iterable[str],
    bullet: str = ' - ',
    header: str | None = None,
    skip_empty_items: bool | _typing.Literal['keep_whitespace'] = True,
    linesep: str | _types.EllipsisType = ...,
    target: _typing.Literal[None] = None,
) -> str: ...


@_typing.overload
def bullet(
    items: _typing.Iterable[str],
    bullet: str = ' - ',
    header: str | None = None,
    skip_empty_items: bool | _typing.Literal['keep_whitespace'] = True,
    linesep: str | _types.EllipsisType = ...,
    target: list[str] = ...,
) -> None: ...


@_typing.overload
def bullet(
    items: _typing.Iterable[str],
    bullet: str = ' - ',
    header: str | None = None,
    skip_empty_items: bool | _typing.Literal['keep_whitespace'] = True,
    linesep: str | _types.EllipsisType = ...,
    target: list[str] | None = None,
) -> str | None: ...


def bullet(
    items: _typing.Iterable[str],
    bullet: str = ' - ',
    header: str | None = None,
    skip_empty_items: bool | _typing.Literal['keep_whitespace'] = True,
    linesep: str | _types.EllipsisType = ...,
    target: list[str] | None = None,
) -> str | None:
    if linesep is ...:
        import os

        linesep = os.linesep

    require_linesep = False

    frags = []

    if header is not None:
        frags.append(header)
        require_linesep = True

    line_prefix = ' ' * len(bullet)

    for value in items:
        if skip_empty_items:
            if skip_empty_items == 'keep_whitespace':
                if len(value) == 0:
                    continue
            elif value.isspace():
                continue

        lines = value.splitlines()

        for i, line in enumerate(lines):
            if require_linesep:
                frags.append(linesep)

            frags.append(bullet if i == 0 else line_prefix)
            frags.append(line)

            require_linesep = True

    return ''.join(frags) if target is None else None


def attrsof(obj: _typing.Any) -> _typing.Mapping[str, _typing.Any]:
    dct = getattr(obj, '__dict__', None)

    if dct is None:
        slots: tuple[str, ...] | None = getattr(type(obj), '__slots__', None)

        if slots is not None:
            dct = {k: getattr(obj, k) for k in slots}

        if dct is None:
            dct = {}

    return dct
