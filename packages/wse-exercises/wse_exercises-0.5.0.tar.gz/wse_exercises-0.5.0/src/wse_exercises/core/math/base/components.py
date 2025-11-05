"""Defines mathematical task component models."""

from pydantic import Field, ValidationInfo, field_validator

from wse_exercises.base.components import (
    Conditions,
    Config,
    NumberAnswer,
    TextQuestion,
)

MIN_VALUE = 1
MAX_VALUE = 9


class CalcConfig(Config):
    """Simple calculation math task config model."""

    min_value: int = MIN_VALUE
    max_value: int = MAX_VALUE

    @classmethod
    @field_validator('max_value')
    def check_min_less_than_max(
        cls,
        value: int,
        info: ValidationInfo,
    ) -> int:
        """Check that the minimum value is greater than the maximum."""
        min_value = info.data.get('min_value') if info.data else None
        if min_value is not None and value <= min_value:
            raise ValueError('max_value must be greater than min_value')
        return value


class CalcConditions(Conditions):
    """Simple calculation math task conditions model."""

    operand_1: int
    operand_2: int
    time: int = Field(default=60, description='Time for task solution')


class CalcQuestion(TextQuestion):
    """Simple calculation math task question model."""


class CalcAnswer(NumberAnswer):
    """Simple calculation math task answer model."""
