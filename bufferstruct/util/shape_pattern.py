import abc as _abc
import dataclasses as _dc
import types as _types
import typing as _typing


@_typing.final
class ShapeVariable:
    """Used to represent dynamic axes in a shape pattern."""

    def __init__(self, name: str) -> None:
        """
        Initializes the current instance.

        :param name: The name of the variable. This must be a valid Python identifier.
        """
        if not name.isidentifier():
            if len(name) == 0:
                raise ValueError('The shape variable name must not be empty.')
            else:
                raise ValueError('Shape variables must be valid Python identifiers.')

        self._name = name
        self._hash = hash(name)

    @property
    def name(self) -> str:
        """
        Returns the name of the variable.

        :return: The name of the variable. This is a valid Python identifier.
        """
        return self._name

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.name!r})'

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: _typing.Any) -> bool:
        if not isinstance(other, ShapeVariable):
            return False

        return other._hash == self._hash and other.name == self.name


class VariableAssignment(_typing.Mapping[str | ShapeVariable, int]):
    """Represents a mapping of a shape variable or its name to its assignment."""

    def __init__(self, dct: dict[str, tuple[ShapeVariable, int]]) -> None:
        self._dct = dct

    def __getitem__(self, key: str | ShapeVariable, /) -> int:
        if isinstance(key, ShapeVariable):
            # if we're explicitly asked for a shape variable, we return the value of its name, but only if the shape
            # variable corresponding to it is exactly the one we were asked for (i.e., they may have the same name, but
            # they *are* not the same instance)
            var, value = self._dct[key.name]

            if var is not key:
                raise KeyError(key)

            return value
        else:
            _, value = self._dct[key]

            return value

    def __len__(self) -> int:
        return len(self._dct)

    def __iter__(self) -> _typing.Iterator[ShapeVariable]:
        return (var for var, _ in self._dct.values())


@_dc.dataclass
class ShapeMatch:
    """Represents the result of a match operation of a shape pattern."""

    batch_shape: tuple[int, ...] | None
    """If batching was allowed, this represents the shape of the batch. `None` if batching was not allowed."""

    variable_assignment: VariableAssignment | None
    """The assignment of variables. If `None`, a match was not possible."""

    def __getitem__(self, key: str | ShapeVariable) -> int:
        """
        Returns the assignment made to the indicated shape variable or shape variable name.

        :param key: The shape variable or the name of a shape variable.
        :return: The axis size assigned to the referred shape variable.
        :raises RuntimeError: The match was not successful.
        :raises KeyError: The shape variable or shape variable name was not assigned a value (i.e., it was not used in
            the pattern).
        """
        if self.variable_assignment is None:
            raise RuntimeError('The current operation was not successful.')

        return self.variable_assignment[key]

    @_typing.overload
    def get(self, key: str | ShapeVariable) -> int | None:
        """
        Returns the assignment made to the indicated shape variable or shape variable name or, if unassigned, the
        indicated default value.

        :param key: The shape variable or the name of a shape variable.
        :return: The axis size assigned to the referred shape variable.
        :raises RuntimeError: The match was not successful.
        """
        ...

    @_typing.overload
    def get[TOpt](self, key: str | ShapeVariable, default: TOpt) -> int | TOpt:
        """
        Returns the assignment made to the indicated shape variable or shape variable name or, if unassigned, the
        indicated default value.

        :param key: The shape variable or the name of a shape variable.
        :param default: The default value to return if the shape variable or shape variable name was not assigned a
            value (i.e., if it was not used in the pattern).
        :return: The axis size assigned to the referred shape variable or the default value, if unassigned.
        :raises RuntimeError: The match was not successful.
        """
        ...

    def get(self, key: str | ShapeVariable, default: _typing.Any = None) -> int | _typing.Any:
        if self.variable_assignment is None:
            raise RuntimeError('The current operation was not successful.')

        return self.variable_assignment.get(key, default)

    @property
    def success(self) -> bool:
        """
        Determines whether the match was successful or not.

        :return: `True` if and only if successful.
        """
        return self.variable_assignment is not None

    def __bool__(self) -> bool:
        """
        Returns whether the match was successful or not.

        :return: `True` if and only if successful.
        """
        return self.success

    @staticmethod
    def failed() -> ShapeMatch:
        """
        Returns a default value to use if a match was not successful.

        :return: A match result representing a failed match.
        """
        return ShapeMatch(None, None)


class Constraint(_abc.ABC):
    """Represents the constraint of the axes of a shape in a shape pattern."""

    @_abc.abstractmethod
    def __contains__(self, value: int, /) -> bool: ...

    def validate(
        self, axis_size: int, axis_index: int | None, variable: ShapeVariable | None, raise_errors: bool = True
    ) -> bool:
        """
        Validates the size of an axis and, if demanded, raises an exception giving further information about the
        constraint violation.

        :param axis_size: The size of the axis.
        :param axis_index: The index of the axis or `None` if the constraint is applied to a shape variable. Either
            `axis_index` or `variable` must be set to a value, but not both.
        :param variable: The variable being constrained or `None` if the constraint is applied to an axis. Either
            `axis_index` or `variable` must be set to a value, but not both.
        :param raise_errors: `True` if the function is to raise an exception upon a mismatch. If `False`, the function
            proceeds silently and returns a value indicating whether the axis size is valid.
        :return: `True` if the axis size is valid. If `raise_errors` is `False`, the function returns `False` if the
            axis size is invalid.
        :raises ValueError: Either `variable` and `axis_index` were set or neither, or the axis size is invalid.
        """
        if variable is None and axis_index is None:
            raise ValueError('Either `axis_index` or `variable` must be indicated.')
        elif variable is not None and axis_index is not None:
            raise ValueError('Either `axis_index` or `variable` must be indicated, but not both.')

        result = self._validate_core(axis_size, axis_index, variable, raise_errors)

        if not result and raise_errors:
            raise RuntimeError(
                f'{type(self).__module__}.{type(self).__qualname__}.{self._validate_core.__name__} returned `False`, '
                f'but `raise_errors` was set to `True`. An error must be raised upon failure.'
            )

        return result

    def _validate_core(
        self, axis_size: int, axis_index: int | None, variable: ShapeVariable | None, raise_errors: bool = True
    ) -> bool:
        """
        Validates the size of an axis and, if demanded, raises an exception giving further information about the
        constraint violation.

        :param axis_size: The size of the axis.
        :param axis_index: The index of the axis or `None` if the constraint is applied to a shape variable. Either
            `axis_index` or `variable` must be set to a value, but not both.
        :param variable: The variable being constrained or `None` if the constraint is applied to an axis. Either
            `axis_index` or `variable` must be set to a value, but not both.
        :param raise_errors: `True` if the function is to raise an exception upon a mismatch. If `False`, the function
            proceeds silently and returns a value indicating whether the axis size is valid.
        :return: `True` if the axis size is valid. If `raise_errors` is `False`, the function returns `False` if the
            axis size is invalid.
        :raises ValueError: The axis size is invalid.
        """
        if axis_size not in self:
            if raise_errors:
                if variable is None:
                    raise ValueError(f'The axis size for axis {axis_index} does not fall into the acceptable range.')
                else:
                    raise ValueError(
                        f'The axis size for variable {variable.name!r} does not fall into the acceptable range.'
                    )
            return False

        return True


class AcceptedSizes(Constraint):
    """Represents a constraint that allows only a specific set of sizes."""

    def __init__(self, accepted_sizes: _typing.Iterable[int] | int, display_numbers: bool = True) -> None:
        """
        Initializes the current instance.

        :param accepted_sizes: The set of sizes that are acceptable. This set must be finite.
        :param display_numbers: `True` to display the numbers in an error `False` if not. Set this to `False` if
            `accepted_sizes` contains a lot of items.
        """
        if not isinstance(accepted_sizes, _typing.Iterable):
            accepted_sizes = frozenset({accepted_sizes})
        else:
            accepted_sizes = frozenset(accepted_sizes)

        accepted_sizes_ordered: list[int] | None

        if display_numbers:
            accepted_sizes_ordered = list(accepted_sizes)
            accepted_sizes_ordered.sort()
        else:
            accepted_sizes_ordered = None

        self._accepted_size_ordered = accepted_sizes_ordered
        self._accepted_sizes = accepted_sizes
        self._display_numbers = display_numbers

    def __contains__(self, value: int, /) -> bool:
        return value in self._accepted_sizes

    def _validate_core(
        self, axis_size: int, axis_index: int | None, variable: ShapeVariable | None, raise_errors: bool = True
    ) -> bool:
        if not raise_errors or self._accepted_size_ordered is None:
            return super()._validate_core(axis_size, axis_index, variable, raise_errors)

        if axis_size not in self:
            if self._accepted_size_ordered is None:
                if variable is None:
                    raise ValueError(f'The axis size for axis {axis_index} does not fall into the acceptable range.')
                else:
                    raise ValueError(
                        f'The axis size for axis {axis_index} ({variable.name}) does not fall into the '
                        'acceptable range.'
                    )
            else:
                if variable is None:
                    raise ValueError(
                        f'The axis size for axis {axis_index} does not fall into the acceptable range: '
                        f'{", ".join(map(str, self._accepted_size_ordered))}.'
                    )
                else:
                    raise ValueError(
                        f'The axis size for axis {axis_index} ({variable.name}) does not fall into the '
                        'acceptable range: '
                        f'{", ".join(map(str, self._accepted_size_ordered))}.'
                    )

        return True


class MultipleConstraints(Constraint):
    """
    Combines multiple constraints into a single constraint: All inner constraints must be satisfied for the constraint
    itself to be satisfied.
    """

    def __init__(self, *constraints: Constraint) -> None:
        """
        Initializes the current instance.

        :param constraints: The inner constraints.
        """
        self._constraints = constraints

    def __contains__(self, value: int, /) -> bool:
        return all(value in constraints for constraints in self._constraints)

    def _validate_core(
        self, axis_size: int, axis_index: int | None, variable: ShapeVariable | None, raise_errors: bool = True
    ) -> bool:
        if not raise_errors:
            for constraint in self._constraints:
                if not constraint.validate(axis_size, axis_index, variable, raise_errors=False):
                    return False

            return True
        else:
            errors = []

            for constraint in self._constraints:
                try:
                    constraint.validate(axis_size, axis_index, variable, raise_errors=True)
                except ValueError as ex:
                    errors.append(ex)

            if len(errors) == 1:
                raise errors[0]
            else:
                raise ValueError('Multiple errors occurred: \n - ' + '\n - '.join(map(str, errors)))


def _format_shape_entry(value: None | ShapeVariable | Constraint) -> str:
    """
    Formats the shape pattern entry. This is used by the `__str__` and `__repr__` implementations of the shape pattern.

    :param value: The value to format.
    :return: A string representation hinting at the represented shape patternentry.
    """
    if value is None:
        return '*'
    elif isinstance(value, ShapeVariable):
        return value.name
    else:
        return '*'


class ShapePattern:
    """Used to represent a pattern that is to be satisfied by shapes."""

    def __init__(
        self,
        *args: None | Constraint | str | ShapeVariable,
        variable_constraints: _typing.Mapping[str | ShapeVariable, Constraint] | None = None,
        **variable_constraints_kwargs: Constraint,
    ) -> None:
        """
        Initializes the current instance.

        :param args: Any number of positional arguments representing the shape. `None` represents an arbitrary axis,
            supplying an instance of type `Constraint` constraints the axis to a specific set of valid values. Supplying
            a `ShapeVariable` object yields a named reference to the axis; strings get converted to shape variables.
            Shape variables and shape variable names can be indicated multiple times: When matching a shape, the shape
            variables must receive the same assignment across all their bound axes. Note that if two `ShapeVariable`
            references must refer to the same object if their names agree; strings that refer to supplied
            `ShapeVariable` objects get mapped to the supplied `ShapeVariable` rather than a newly created object.
        :param variable_constraints: Constraints that shape variables must satisfy.
        :param variable_constraints_kwargs: Constraints that shape variables must satisfy. The parameter names
            correspond to the shape variable names.
        """
        mapped: list[ShapeVariable | Constraint | None] = []
        shape_vars: dict[str, ShapeVariable] = {}

        # collect all shape variables and ensure that there aren't two separate shape variable instances having the
        # same name
        for source in (args, variable_constraints):
            if source is None:
                continue

            for arg in source:
                if isinstance(arg, ShapeVariable):
                    current = shape_vars.get(arg.name)

                    if current is not None and arg is not current:
                        raise ValueError(f'Multiple shape variable instances with the same name found: {arg.name!r}.')

                    shape_vars[arg.name] = arg

        # collect arguments and constraints
        for arg in args:
            if isinstance(arg, str):
                var = shape_vars.get(arg)

                if var is None:
                    var = ShapeVariable(arg)
                    shape_vars[arg] = var

                arg = var

            mapped.append(arg)

        # gather the constraints defined per variable rather than per position
        combined_var_constraints: dict[ShapeVariable, Constraint] = {}

        if variable_constraints is not None:
            for k, v in variable_constraints.items():
                if isinstance(k, ShapeVariable):
                    current = shape_vars.get(k.name)

                    if current is None:
                        raise ValueError(
                            f'Shape variable {k.name!r} is unused, but specified in `variable_constraints`.'
                        )
                    elif current is not k:
                        raise ValueError(
                            f'Multiple shape variable instances with the same name found: {k.name!r}. The variable was '
                            'found in `variable_constraints`.'
                        )
                else:
                    current = shape_vars.get(k)

                    if current is None:
                        raise ValueError(f'Shape variable {k!r} is unused, but specified in `variable_constraints`.')

                combined_var_constraints[current] = v

        for k, v in variable_constraints_kwargs.items():
            current = shape_vars.get(k)

            if current is None:
                raise ValueError(f'Shape variable {k!r} is unused, but specified in `variable_constraints_kwargs`.')
            elif current in combined_var_constraints:
                raise ValueError(
                    'If specified, `variable_constraints` and `variable_constraints_kwargs` must be distinct.'
                )

            combined_var_constraints[current] = v

        self._shape = tuple(mapped)
        self._variable_constraints = combined_var_constraints
        self._variables = shape_vars

    @property
    def ndim(self) -> int:
        """
        Returns the number of axes of the shape.

        :return: The number of axes of the shape.
        """
        return len(self.shape)

    @property
    def shape(self) -> tuple[ShapeVariable | Constraint | None, ...]:
        """
        Returns the underlying shape pattern, a tuple of shape variables, constraints, and arbitrary axes.

        :return: The underlying shape pattern.
        """
        return self._shape

    def __len__(self) -> int:
        return self.ndim

    def __getitem__(self, index: int, /) -> ShapeVariable | Constraint | None:
        return self.shape[index]

    @property
    def variable_constraints(self) -> _types.MappingProxyType[ShapeVariable, Constraint]:
        """
        Returns the constraints assignments to shape variables must satisfy.

        :return: A mapping of shape variables to their respective constraints.
        """
        return _types.MappingProxyType(self._variable_constraints)

    @property
    def variables(self) -> _types.MappingProxyType[str, ShapeVariable]:
        """
        A mapping from shape variable names to their corresponding shape variables.

        :return: The mapping from shape variable name to shape variable.
        """
        return _types.MappingProxyType(self._variables)

    def match(self, shape: tuple[int, ...], allow_batching: bool = True, raise_errors: bool = True) -> ShapeMatch:
        """
        Tries to match the indicated shape with the pattern. If successful, it returns the respective value.

        :param shape: The shape to test.
        :param allow_batching: `True` to allow `shape` to define a prefix of axes. These axes are treated as part of a
            batch. If `False`, `shape` is required to have exactly as many axes as the pattern.
        :param raise_errors: `True` to raise errors if the shape mismatches. `False` fails silently and shows its result
            on the returned object.
        :return: The result of the match operation.
        """
        if any(v < 0 for v in shape):
            raise ValueError('The entries of `shape` must be non-negative.')

        expected_shape = self.shape

        batch_shape: tuple[int, ...] | None = None

        # check whether we got fewer axes than required
        if len(shape) < len(expected_shape):
            if raise_errors:
                raise ValueError('The indicated shape defines fewer axes than the current shape pattern.')

            return ShapeMatch.failed()

        # check whether we received more axes than required and deduce the batch shape from it, if allowed
        if allow_batching:
            batch_shape = shape[: -len(expected_shape)]
            shape = shape[-len(expected_shape) :]
        elif len(shape) > len(expected_shape):
            if not allow_batching:
                if raise_errors:
                    raise ValueError('The indicated shape defines more axes than the current shape pattern.')

                return ShapeMatch.failed()

        assignment: dict[str, tuple[ShapeVariable, int]] = {}

        # check all positional constraints and whether the shape variable assignments match
        for i, (requirement, actual) in enumerate(zip(expected_shape, shape, strict=True)):
            if requirement is None:
                continue

            if isinstance(requirement, ShapeVariable):
                current = assignment.get(requirement.name)

                if current is None:
                    assignment[requirement.name] = requirement, actual
                else:
                    _, current_value = current
                    if current_value != actual:
                        if raise_errors:
                            raise ValueError(
                                f'Expected shape {self._format(allow_batching)}, but got shape '
                                f'({", ".join(map(str, shape))}).'
                            )

                        return ShapeMatch.failed()
            else:
                if not requirement.validate(actual, i, None, raise_errors=raise_errors):
                    return ShapeMatch.failed()

        # check whether all assignments are valid
        for variable, actual in assignment.values():
            constraint = self._variable_constraints.get(variable)

            if constraint is not None and not constraint.validate(actual, None, variable, raise_errors=raise_errors):
                return ShapeMatch.failed()

        return ShapeMatch(batch_shape, VariableAssignment(assignment))

    def __repr__(self) -> str:
        return self._format(include_batch_axis=False)

    def _format(self, include_batch_axis: bool) -> str:
        shape = self.shape
        if len(shape) == 0:
            return '(...)' if include_batch_axis else '()'
        elif len(shape) == 1 and not include_batch_axis:
            return f'({_format_shape_entry(shape[0])},)'
        elif include_batch_axis:
            return f'(..., {", ".join(map(_format_shape_entry, shape))})'
        else:
            return f'({", ".join(map(_format_shape_entry, shape))})'
