# src/konvigius/validators.py
"""
validators.py

This module provides a set of configurable and reusable validator classes
designed to validate configuration or user-provided data by means of Schema object(s).

All validators inherit from a common abstract base class, `Validator`, which enforces
implementation of a `_init_validate()` method and a `_validate_value` method.

Each validator-class is designed to check a specific constraint (e.g., type,
range, presence, or membership in a domain), and raise a validation exception if the
constraint is not met.

These validators are created automatically when instantiating a Config class.

Classes:
    Validator (ABC): Abstract base class for all validators. Implements a callable
        interface that delegates to the subclass's methods.

    TypeValidator: Validates that a value is of a specified type or set of types.

    RequiredValidator: Validates that a value is present (i.e., not None or empty string)
        if it is marked as required.

    RangeValidator: Validates that a numeric value falls within a specified inclusive
        range defined by `min_val` and `max_val`.

    DomainValidator: Validates that a value exists within a predefined set of allowed values.

    CustomValidator: Validates a value using a user-provided function(s). This allows
        for flexible or domain-specific validation logic. Unexpected errors are
        wrapped in a `ConfigValidationError`, while known config exceptions are re-raised.

    ComputedValidator: Validates user-provided function(s) and creates new properties
    that are added to the config-instance.

Note:
    All validators are dataclasses for convenient instantiation and introspection.
"""
from __future__ import annotations
from collections.abc import Sized
from dataclasses import dataclass, field
from typing import Any, Callable

from .exceptions import (
    ConfigRangeError,
    ConfigDomainError,
    ConfigTypeError,
    ConfigRequiredError,
)

from .core.base import Validator
from .core.types import ComputedFn


@dataclass
class TypeValidator(Validator):
    """
    Validates whether a given value is of the specified data type(s).
    """

    def _init_validate(self):
        """
        Validates that `field_type` is a type or tuple of types.

        Raises:
            ConfigTypeError: If `field_type` contains non-type elements.
        """
        self._type = self.option.field_type  # make short alias
        if self._type is not None:
            if not isinstance(self._type, tuple):
                self._type = tuple([self._type])

            for ft in self._type:
                if not isinstance(ft, type):
                    raise ConfigTypeError(
                        f"'field_type' must be a class type like str, int, bool etc; "
                        f"got type {type(ft).__name__}"
                    )
            # eventually set the new value
            if self._type[0] is bool and self.option.default_value not in (True, False):
                self.option.default_value = False

    def _validate_value(self, value: Any):
        """
        Validates whether the given `value` is of the allowed type(s).

        Args:
            value (Any): The value to validate.

        Raises:
            ConfigTypeError: If the value is not of the expected type.
        """
        if self._type is not None:
            if value and not isinstance(value, self._type):
                raise ConfigTypeError(
                    f"value is of the wrong type; got type {type(value).__name__}"
                )


@dataclass
class RequiredValidator(Validator):
    """
    Validates that a required value is not None or an empty string.

    This validator checks whether a value is present (i.e., not None and not an empty string)
    if the `required` flag is set to True.
    """

    required: bool = False

    def _init_validate(self):
        """
        Post-initialization hook to ensure `required` is a valid boolean.

        If `required` is None or an empty string, it is treated as False.

        Raises:
            ConfigTypeError: If `required` is not of type bool.
        """
        if self.option.required in (None, ""):
            self.required = False
        elif isinstance(self.option.required, bool):
            self.required = self.option.required
        else:
            raise ConfigRequiredError(
                "'required' must be of type boolean; "
                f"got value '{self.option.required}'"
            )
        self.option.required = self.required  # eventually set the new value

    def _validate_value(self, value: Any):
        """
        Validates that the value is not None or an empty string when required.

        Args:
            value (Any): The value to validate.

        Raises:
            ConfigRequiredError: If the value is None or empty and `required` is True.
        """
        if self.required and (value is None or value == ""):
            raise ConfigRequiredError("value can not be None or empty")


@dataclass
class RangeValidator(Validator):
    """
    Validates that a numeric value or the length of an object falls within a specified range.

    This validator checks whether a value (int or float) or a length (string, list etc)
    lies between `min_val` and `max_val`, inclusive. If either bound is not set (None),
    that side of the range is considered open.
    """

    def _init_validate(self):
        """
        Validates and normalizes the min_val and max_val bounds after initialization.
        """
        if self.option.r_min is not None and not isinstance(
            self.option.r_min, (float, int)
        ):
            raise ConfigTypeError(
                f"value min_val must be int or float; "
                f"got type {type(self.option.r_min).__name__}",
            )
        if self.option.r_max is not None and not isinstance(
            self.option.r_max, (float, int)
        ):
            raise ConfigTypeError(
                f"value max_val must be int or float; "
                f"got type {type(self.option.r_max).__name__}",
            )
        if (
            self.option.r_min is not None
            and self.option.r_max is not None
            and self.option.r_min > self.option.r_max
        ):
            raise ConfigRangeError(
                f"min ({self.option.r_min}) cannot be greater "
                f"than max ({self.option.r_max})",
            )

    def _validate_value(self, value: int | float | Sized | None):
        """
        Validates that the value is within the defined numeric range.

        Empty strings and None are considered valid and skipped.

        Args:
            value (int | float | str | None): The value to validate.
                If a string, it is converted to None if empty.

        Raises:
            ConfigValidationError: If the value is not numeric,
                or if it falls outside the defined range.
        """
        if self.option.r_min is None and self.option.r_max is None:
            # testing makes no sense
            return

        value = None if value == "" else value
        if value is None:
            return

        if isinstance(value, Sized):
            value = len(value)

        if self.option.r_min is not None and value < self.option.r_min:
            raise ConfigRangeError(
                f"value ({value}) must be >= min-value ({self.option.r_min})",
            )
        if self.option.r_max is not None and value > self.option.r_max:
            raise ConfigRangeError(
                f"value ({value}) must be <= max-value ({self.option.r_max})",
            )


@dataclass
class DomainValidator(Validator):
    """
    Validates that a value exists within a predefined domain (set of acceptable values).

    This validator ensures the value is present in the `domain` set.
    The domain must be a non-empty set, provided at initialization.
    """

    domain: set[Any] = field(default_factory=set)

    def _init_validate(self):
        """
        Validates that `domain` is a set (empty or not) after initialization.

        Raises:
            ConfigDomainError: If `domain` is not a set.
        """
        _domain = ()
        if self.option.domain is None:
            _domain = ()

        elif isinstance(self.option.domain, tuple):
            _domain = self.option.domain
        else:
            raise ConfigDomainError(
                f"domain must be a tuple collection; "
                f"got type {type(self.option.domain).__name__}",
            )
        # must be a tuple by now
        try:
            self.domain = set(_domain)
        except Exception as e:
            raise ConfigDomainError(
                "cannot convert domain tuple to a set; "
                "probably due to unhashable types"
            ) from e

    def _validate_value(self, value: Any):
        """
        Validates that the given value is part of the domain set.

        Args:
            value (Any): The value to validate.

        Raises:
            ConfigDomainError: If the value is not in the domain set.
        """
        if value and self.domain and value not in self.domain:
            raise ConfigDomainError(
                f"value ({value}) is not in the domain of acceptable values",
            )


@dataclass
class CustomValidator(Validator):
    """
    A validator that delegates validation logic to a user-defined function.

    This class allows dynamic or reusable validation logic by accepting
    a custom function (`fn_validator`) at initialization. The function should
    raise a `ConfigError` or another appropriate exception if validation fails.

    Attributes:
        fn_validator (Callable[[Any], Any]): A user-provided function that performs
            validation. It should accept a single argument (the value to validate)
            and either return a result or raise an exception.
    """

    fn_validators: tuple[Callable[..., Any], ...] = ()

    def _init_validate(self):

        if self.option.fn_validator is None:
            self.fn_validators = ()
        elif isinstance(self.option.fn_validator, tuple):
            self.fn_validators = self.option.fn_validator
        else:
            self.fn_validators = (self.option.fn_validator,)

        for fn in self.fn_validators:
            if not isinstance(fn, Callable):
                raise ConfigTypeError(
                    f"custom validators must be a callable or a tuple of callables; "
                    f"got type {type(fn).__name__}"
                )

    def _validate_value(self, value: Any):
        """
        Executes the user-defined validation function with the provided value.

        Args:
            value (Any): The value to validate.

        Raises:
            ConfigError: If the user-defined function raises this known validation exception.
            ConfigValidationError: If an unexpected exception occurs during validation.
        """
        # for fn in self.option.fn_validator or ():  # or ... to please pyright
        for fn in self.fn_validators:
            fn(value, self.cfg)


@dataclass
class ComputedValidator(Validator):
    """
    A validator that runs one or more computed callback functions and returns
    derived values for additional fields.
    """

    fn_callbacks: tuple[ComputedFn, ...] = ()

    def _init_validate(self):
        """
        Normalizes and validates the fn_computed callbacks.
        Ensures all are callable and conform to ComputedFn.
        """
        fn_raw = self.option.fn_computed

        # Normalize to tuple
        if fn_raw is None:
            self.fn_callbacks = ()
        elif isinstance(fn_raw, tuple):
            self.fn_callbacks = fn_raw
        else:
            self.fn_callbacks = (fn_raw,)

        # Validate all entries
        for fn in self.fn_callbacks:
            if not isinstance(fn, Callable):
                raise ConfigTypeError(
                    f"computed (decorators) must be a callable or a tuple of "
                    f"callables; got type {type(fn).__name__}"
                )
            if not isinstance(fn, ComputedFn):
                raise ConfigTypeError(
                    f"computed callback does not conform to ComputedFn protocol: {fn}"
                )

    def _validate_value(self, value: Any) -> dict[str, Any]:
        """
        Executes the user-defined function(s) with the provided value.

        Returns a dictionary of {field_name: computed_value}.
        """
        fields: dict[str, Any] = {}
        for fn in self.fn_callbacks:
            fields[fn.field_name] = fn(value, self.cfg)
        return fields


# === END ===
