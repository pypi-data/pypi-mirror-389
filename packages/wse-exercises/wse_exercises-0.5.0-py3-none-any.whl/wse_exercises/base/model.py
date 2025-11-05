"""Defines base model for DTO."""

from pydantic import BaseModel

from .mixins import ConvertMixin


class BaseSchema(ConvertMixin, BaseModel):
    """Base model with custom conversion between dict/json."""
