import dataclasses as dc
from typing import Annotated

import pytest

import bufferstruct.util.constraints as constraints
from bufferstruct.util.constraints import ValidationContext


class Nonnegative(constraints.Constraint[int | float]):
    def _evaluate_core(self, obj: int | float, context: ValidationContext) -> None:
        if obj < 0:
            raise ValueError('Negative value found.')


@dc.dataclass
class X:
    x: Annotated[int, Nonnegative()]


def test_member_constraint_pass() -> None:
    constraint = constraints.MemberConstraints.from_type(X)

    constraint.check(X(1))


def test_member_constraint_fail() -> None:
    constraint = constraints.MemberConstraints.from_type(X)

    with pytest.raises(constraints.ValidationError):
        constraint.check(X(-1))
