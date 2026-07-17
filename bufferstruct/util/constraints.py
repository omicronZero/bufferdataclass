import abc as _abc
import dataclasses as _dc
import enum as _enum
import os as _os
import types as _types
import typing as _typing

from .. import util as _util

_linesep = _os.linesep
"""Used as a line separator in error messages."""

_nested_indent: int = 2
"""The number of space characters to insert before a nested error message."""

error_max_displayed_origin_members: int | None = None
"""The maximum number of origin members to display in an error header."""


_HandledErrors: _typing.TypeAlias = ValueError | TypeError
_HandledErrorTuple: tuple[type[BaseException], ...] = _HandledErrors.__args__


@_typing.final
class ConstraintError(ValueError):
    def __init__(self, constraint: Constraint[_typing.Any], inner_error: _HandledErrors) -> None:
        super().__init__(constraint, inner_error)

    @property
    def constraint(self) -> Constraint[_typing.Any]:
        return self.args[0]

    @property
    def inner_error(self) -> _HandledErrors:
        return self.args[1]

    def __repr__(self) -> str:
        return str(self.inner_error)

    def __str__(self) -> str:
        return str(self.inner_error)


class _State(_enum.Enum):
    open = 'open'
    merging = 'merging'
    closed = 'closed'


class ValidationErrorEntry:
    def __init__(self, exception: _HandledErrors, origin: Constraint | type[ConstraintValue]) -> None:
        self._exception = exception
        self._origin = origin

    @property
    def exception(self) -> _HandledErrors:
        return self._exception

    @property
    def origin(self) -> Constraint | type[ConstraintValue]:
        return self._origin


def _format_error(source: str, values: tuple[ValidationErrorEntry, ...]) -> str:
    frags = []

    if source == '':
        source = '<root>'

    frags.append(source)

    if len(values) > 1:
        frags.append(':')
    else:
        frags.append(': ')

    if len(values) == 1:
        frags.append((_linesep + ' ' * _nested_indent).join(str(values[0].exception).splitlines()))
    else:
        frags.append(_util.bullet(str(v.exception) for v in values))

    return ''.join(frags)


class ValidationError(ValueError):
    def __init__(self, errors_by_path: dict[str, _typing.Iterable[ValidationErrorEntry]]) -> None:
        if len(errors_by_path) == 0:
            raise ValueError('`errors_by_path` must contain at least one item.')

        errors_by_path = {k: tuple(v) for k, v in errors_by_path.items()}

        if any(len(v) == 0 for v in errors_by_path.values()):
            raise ValueError('All key-value pairs in `errors_by_path` must contain at least one item in their value.')

        self._message: str | None = None

        super().__init__(_types.MappingProxyType(errors_by_path))

    @property
    def errors(self) -> _types.MappingProxyType[str, tuple[ValidationErrorEntry, ...]]:
        return self.args[0]

    def __repr__(self) -> str:
        if self._message is None:
            sorted_errors = sorted(self.errors.items(), key=lambda v: v[0])

            frags = []

            for path, errors in sorted_errors:
                if path == '':
                    path = '<root>'
                frags.append(path)

                if len(errors) == 1:
                    frags.append(': ')
                    frags.append(str(errors[0].exception))
                else:
                    frags.append(':\n')

                    _util.bullet((str(err.exception) for err in errors), target=frags, linesep='\n')

            self._message = ''.join(frags)

        return self._message

    def __str__(self) -> str:
        return repr(self)


@_typing.final
@_dc.dataclass(frozen=True)
class _ConstraintValueEntry:
    value: ConstraintValue
    origin: Constraint
    path: str


class ValidationContext:
    def __init__(self, parent: ValidationContext | None = None, name: str | None = None) -> None:
        if name is not None:
            if parent is None:
                raise ValueError('If `name` is set to a value a parent must be indicated.')

            if not name.isidentifier():
                raise ValueError('`name` must be a Python identifier.')

        self._parent = parent
        self._name = name

        self._children: list[ValidationContext] = []

        self._errors: dict[str, list[ValidationErrorEntry]] = {}
        self._constraint_values: dict[type[ConstraintValue], list[_ConstraintValueEntry]] | None = {}
        self._merged_constraint_values: ConstraintMergedValues | None = None

        self._state = _State.open
        self._errors_propagated = False

        self.__entered = False

        if parent is not None:
            parent._children.append(self)

    def __enter__(self) -> _typing.Self:
        if self.__entered:
            raise RuntimeError('The current context is already active and thus cannot be entered.')

        self.__entered = True

        return self

    def __exit__(
        self, exc_type: BaseException | None, exc_val: BaseException | None, exc_tb: _types.TracebackType | None
    ) -> bool | None:
        if not self.__entered:
            raise RuntimeError('The current context is not active and thus cannot be exited.')

        self.__entered = False

        if self._state == _State.open:
            # we do not want to generate a new error if `__exit__` happened due to an uncaught exception. If we have a
            # parent, we propagate to it, otherwise we ignore the errors for now
            self.close('ignore' if exc_val is not None and self.parent is None else 'auto')

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def parent(self) -> str | None:
        return self._parent

    def sub(self, name: str | None) -> ValidationContext:
        return ValidationContext(self, name)

    def has_errors(self, include_children: bool = True) -> bool:
        if len(self._errors) > 0:
            return True

        return (
            include_children
            and self._state != _State.closed
            and any(c.has_errors(include_children=True) for c in self._children)
        )

    @property
    def constraint_values(self) -> ConstraintMergedValues:
        if self._state != _State.closed:
            raise RuntimeError(
                '`constraint_values` are only available after closing the instance with '
                '`merge_constraint_values` set to `True`.'
            )

        return self._merged_constraint_values

    @_typing.overload
    def add_error(self, error: ValidationErrorEntry) -> None: ...

    @_typing.overload
    def add_error(self, error: _HandledErrors, origin: Constraint | type[ConstraintValue]) -> None: ...

    def add_error(
        self, error: ValidationErrorEntry | _HandledErrors, origin: Constraint | type[ConstraintValue] | None = None
    ) -> None:
        if not isinstance(error, ValidationErrorEntry):
            if origin is None:
                raise TypeError(
                    f'`origin` must be set to a value if `error` is not of type `{_util.nameof(ValidationErrorEntry)}.'
                )

            error = ValidationErrorEntry(error, origin)
        elif origin is not None:
            raise TypeError(
                f'`origin` must not be set to a value if `error` is of type `{_util.nameof(ValidationErrorEntry)}.'
            )

        self._add_error_core('', error)

    def add_constraint_value(
        self,
        constraint_value_type: type[ConstraintValue],
        constraint_value: ConstraintValue[_typing.Any],
        origin: Constraint[_typing.Any],
    ) -> None:
        if constraint_value_type is not type(constraint_value):
            raise TypeError(
                '`constraint_value` must be an instance of the exact type specified in `constraint_value_type`.'
            )

        self._add_constraint_values_core(constraint_value_type, constraint_value, '', origin)

    def _merge_constraint_values(self) -> None:
        merged = {}

        for tp, values in self._constraint_values.items():
            merged[tp] = tp.merge(values, self)

        self._merged_constraint_values = ConstraintMergedValues(merged)

    @property
    def closed(self) -> bool:
        return self._state != _State.open

    def close(
        self,
        error_handling: _typing.Literal['raise', 'propagate_to_parent', 'ignore', 'auto'] = 'auto',
        merge_constraint_values: bool | _typing.Literal['if_successful'] = 'if_successful',
    ) -> None:
        if error_handling not in ('raise', 'propagate_to_parent', 'ignore', 'auto'):
            raise TypeError(f'Invalid value indicated for `error_handling`: {error_handling!r}.')

        if self._state != _State.open:
            raise RuntimeError('The current instance has already been closed.')

        if any(c._state != _State.closed for c in self._children):
            raise RuntimeError('All child contexts must be closed before the current instance can be closed.')

        if error_handling == 'auto':
            error_handling = 'raise' if self.parent is None else 'propagate_to_parent'

        if merge_constraint_values:
            if merge_constraint_values != 'if_successful' or not self.has_errors():
                self._state = _State.merging

                self._merge_constraint_values()

        self._state = _State.closed

        if error_handling == 'propagate_to_parent':
            self.propagate()
        elif error_handling == 'raise':
            self.raise_errors()

    def _add_errors_core(self, path: str, errors: _typing.Iterable[ValidationErrorEntry]) -> None:
        tgt = self._errors.get(path)

        if tgt is None:
            self._errors[path] = tgt = []

        tgt.extend(errors)

    def _add_error_core(self, path: str, error: ValidationErrorEntry) -> None:
        if self._state == _State.closed:
            raise RuntimeError('The context has already been closed.')

        tgt = self._errors.get(path)

        if tgt is None:
            self._errors[path] = tgt = []

        tgt.append(error)

    def _add_constraint_values_core(
        self,
        constraint_value_type: type[ConstraintValue],
        constraint_value: ConstraintValue[_typing.Any],
        path: str,
        origin: Constraint[_typing.Any],
    ) -> None:
        if self._state != _State.open:
            raise RuntimeError('The context has already been closed.')

        tgt = self._constraint_values.get(constraint_value_type)

        if tgt is None:
            self._constraint_values[constraint_value_type] = tgt = []

        tgt.append(_ConstraintValueEntry(constraint_value, origin, path))

    def propagate(self) -> None:
        if self.parent is None:
            raise RuntimeError('The current instance does not have a parent that could be propagated to.')

        if self._state != _State.closed:
            raise RuntimeError('Propagation can only be performed from closed instances.')

        if self._errors_propagated:
            return

        self._errors_propagated = True

        parent = self._parent
        name = self.name

        def merge_path(path: str) -> str:
            if path == '':
                if name is not None:
                    path = name
            elif name is not None:
                path = f'{name}.{path}'

            return path

        for path, errors in self._errors.items():
            path = merge_path(path)

            parent._add_errors_core(path, errors)

        for constraint_value_type, entries in self._constraint_values.items():
            for entry in entries:
                path = merge_path(entry.path)

                parent._add_constraint_values_core(constraint_value_type, entry.value, path, entry.origin)

    def raise_errors(self) -> None:
        if self._state != _State.closed:
            raise RuntimeError('Errors can only be raised from closed instances.')

        if len(self._errors) > 0:
            raise ValidationError(self._errors)


class ConstraintMergedValues:
    def __init__(self, values: dict[type[ConstraintValue], _typing.Any]) -> None:
        self._values = values

    def __iter__(self) -> _typing.Iterator[type[ConstraintValue]]:
        return iter(self._values)

    def __contains__(self, value_type: ConstraintValue) -> bool:
        return value_type in self._values

    def __getitem__[T](self, value_type: type[ConstraintValue[T]]) -> T:
        return self._values[value_type]

    def __len__(self) -> int:
        return len(self._values)

    def __repr__(self) -> str:
        return repr({_util.nameof(tp, repr): v for tp, v in self._values.items()})


class ConstraintValue[T](_abc.ABC):
    @classmethod
    @_abc.abstractmethod
    def _merge_core[TCls](cls: type[TCls], instances: list[TCls]) -> T: ...

    @classmethod
    def merge[TCls](cls: type[TCls], instances: list[TCls], context: ValidationContext) -> T:
        try:
            cls._merge_core(instances)
        except _HandledErrorTuple as ex:
            context.add_error(ex, cls)


class Constraint[T](_abc.ABC):
    @_abc.abstractmethod
    def _evaluate_core(self, obj: T, context: ValidationContext) -> None: ...

    def evaluate(self, obj: T, context: ValidationContext) -> None:
        try:
            self._evaluate_core(obj, context)
        except _HandledErrorTuple as ex:
            context.add_error(ex, self)

        if context.closed:
            raise RuntimeError(f'`{_util.nameof(type(self)._evaluate_core)}` must not close the `context` it receives.')

    def check(self, obj: T) -> ConstraintMergedValues:
        context = ValidationContext()

        self._evaluate_core(obj, context)

        context.close(error_handling='raise')

        return context.constraint_values


class Constraints[T](Constraint[T]):
    def __init__(self, constraints: _typing.Iterable[Constraint[T]]) -> None:
        self._constraints = tuple(constraints)

    def _evaluate_core(self, obj: T, context: ValidationContext) -> None:
        for inner in self._constraints:
            inner._evaluate_core(obj, context)

    @property
    def constraints(self) -> tuple[Constraint[T], ...]:
        return self._constraints


class AnyOf[T](Constraint[T]):
    @_typing.overload
    def __init__(self, *constraints: Constraint[T]) -> None: ...

    @_typing.overload
    def __init__(self, constraints: _typing.Iterable[Constraint[T]], /) -> None: ...

    def __init__(self, *constraints: Constraint[T] | _typing.Iterable[Constraint[T]]) -> None:
        if len(constraints) == 1 and not isinstance(constraints[0], Constraint):
            constraints = constraints[0]

        self._constraints: tuple[Constraint[T], ...] = tuple(constraints)

    @property
    def constraints(self) -> tuple[Constraint[T], ...]:
        return self._constraints

    def _evaluate_core(self, obj: T, context: ValidationContext) -> None:
        subcontexts: list[ValidationContext] = []

        for constraint in self._constraints:
            subcontext = context.sub(name=None)

            try:
                constraint.evaluate(obj, subcontext)
            except:
                raise

            subcontext.close('ignore', merge_constraint_values=False)

            if not subcontext.has_errors():
                # if one of the subcontexts was successful, we have succeeded

                for ctx in subcontexts:
                    ctx.close(error_handling='ignore', merge_constraint_values=False)

                return

        # if none of the subcontexts were successful, we collect their errors to their parent

        for subcontext in subcontexts:
            subcontext.close('propagate_to_parent')


@_typing.overload
def join[T](constraints: _typing.Iterable[Constraint[T]], flatten: bool = False) -> Constraint[T]: ...


@_typing.overload
def join[T](*constraints: Constraint[T], flatten: bool = False) -> Constraint[T]: ...


def join[T](*constraints: Constraint[T] | _typing.Iterable[Constraint[T]], flatten: bool = False) -> Constraint[T]:
    if len(constraints) == 1 and not isinstance(constraints[0], Constraint):
        constraints = constraints[0]

    inner = []

    for c in constraints:
        if not isinstance(c, Constraint):
            raise TypeError(
                f'Expected subtypes of type `{_util.nameof(Constraint)}`, but got type `{_util.classnameof(c)}`.'
            )
        if flatten and type(c) is Constraints:
            inner.extend(_typing.cast(Constraints, c).constraints)
        else:
            inner.append(c)

    if len(inner) == 1:
        return inner[0]
    else:
        return Constraints(inner)


def parse_annotation(
    annotation: _typing.Any,
    name: str | None = None,
    validate_annotation_type: _typing.Callable[[_typing.Any, type], None] | None = None,
) -> tuple[type | _types.UnionType | _typing.Annotated[type | _types.UnionType, ...], list[Constraint]]:
    orig_annotation = annotation

    origin = _typing.get_origin(annotation)

    constraints: list[Constraint] = []
    annotations = []

    if origin is _typing.Annotated:
        annotation, *args = _typing.get_args(annotation)

        for arg in args:
            if isinstance(arg, Constraint):
                constraints.append(arg)
            else:
                annotations.append(arg)

    if annotation is None or annotation is _types.NoneType:
        annotation = _types.NoneType
    elif isinstance(annotation, type):
        if validate_annotation_type is not None:
            validate_annotation_type(orig_annotation, annotation)
    else:
        origin = _typing.get_origin(annotation)

        if origin is _typing.Union:
            if validate_annotation_type is not None:
                for tp in _typing.get_args(annotation):
                    validate_annotation_type(annotation, tp)

        else:
            if name is None:
                raise TypeError(
                    f'Unsupported annotation: `{_util.nameof(annotation, repr)}`. Expected type or union of types.'
                )
            else:
                raise TypeError(
                    f'Unsupported annotation: `{_util.nameof(annotation, repr)}` of member {name!r}. Expected type or '
                    'union of types.'
                )

    if len(annotations) > 0:
        annotation = _typing.Annotated[annotation, *annotations]

    return annotation, constraints


class MemberConstraints[T](Constraint[T]):
    def __init__(self, object_type: type[T], member_constraints: dict[str, Constraint]) -> None:
        self._object_type = object_type
        self._member_constraints = member_constraints

    def _evaluate_core(self, obj: T, context: ValidationContext) -> None:
        if not isinstance(obj, self._object_type):
            raise TypeError(
                f'Expected `obj` to be an instance of type `{_util.nameof(self._object_type)}`, but got '
                f'an instance of type `{_util.classnameof(obj)}` instead.'
            )

        attrs = {k: getattr(obj, k) for k in self._member_constraints}

        for k, constraint in self._member_constraints.items():
            att = attrs[k]

            with context.sub(k) as subcontext:
                constraint.evaluate(att, subcontext)

    @staticmethod
    def from_type(
        object_type: type[T], validate_annotation_type: _typing.Callable[[_typing.Any, type], None] | None = None
    ) -> MemberConstraints[T]:
        constraints: dict[str, list[Constraint]] = {}

        # take the object annotations as a source (they may be parsed from `typing.Annotated`)
        annotations: _typing.Mapping[str, _typing.Any] = getattr(object_type, '__annotations__', None)

        if annotations is not None:
            for k, annotation in annotations.items():
                _, constraints[k] = parse_annotation(
                    annotation, name=k, validate_annotation_type=validate_annotation_type
                )

        # the objects themselves may have default values being constraints
        for k, v in _util.attrsof(object_type).items():
            if isinstance(v, Constraint):
                key_constraints = constraints.get(k)

                if key_constraints is None:
                    constraints[k] = key_constraints = []

                key_constraints.append(v)

        return MemberConstraints(object_type, {k: join(v) for k, v in constraints.items()})
