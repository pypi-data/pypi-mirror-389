# src/konvigius/core/types.py
"""Provides simple classes and helper objects for configuration schemas.

This module defines the core components used for describing configuration
metadata and computed fields:

    * `Schema` — Describes a single configuration option, including metadata
      such as name, type, default value, and validation properties.
    * `with_field_name()` — A decorator that attaches a `field_name` attribute
      to a function, typically used with `Schema.fn_computed`.
    * `ComputedFn` — A runtime-checkable protocol that defines the expected
      interface for computed-field functions.
    * @runtime_checkable
      class ComputedFn(Protocol):

The next two symbols are automatically imported at the package level for convenience,
so they can be used directly as follows:

    `>>> from konvigius import Schema, with_field_name`

"""

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Callable, Protocol, Type, runtime_checkable

# -----------------------------------------------------------------------------
# Define Protocol: ComputedFn
# -----------------------------------------------------------------------------


@runtime_checkable
class ComputedFn(Protocol):
    """Runtime-checkable protocol for functions that compute derived configuration fields.

    A `ComputedFn` describes the callable interface expected for functions
    used in the `Schema.fn_computed` attribute. These functions dynamically
    compute additional configuration values based on existing ones.

    The protocol defines two required members:
      * a `field_name` attribute, which indicates the target field name to create;
      * a `__call__` method that performs the computation.

    This allows static type checkers (like mypy) and runtime checks
    (`isinstance(fn, ComputedFn)`) to verify that a given object behaves
    like a valid computed-field function.

    Attributes:
        field_name (str):
            The name of the configuration property that the function computes.

    Methods:
        __call__(value: str, cfg: SimpleNamespace) -> Any:
            Performs the computation. The function receives:
              * `value`: The current or base value for the computation.
              * `cfg`: A namespace (the configuration context) where other
                options and computed fields are accessible.
            Returns the computed result, which will be assigned to the field
            identified by `field_name`.

    Example:
        >>> @with_field_name("port")
        ... def compute_port(value: str, cfg: SimpleNamespace) -> int:
        ...     return int(value) + 1000
        ...
        >>> isinstance(compute_port, ComputedFn)
        True
    """

    field_name: str

    def __call__(self, value: str, cfg: SimpleNamespace) -> Any: ...


# -----------------------------------------------------------------------------
# Define the Schema metadata class, part of the API
# -----------------------------------------------------------------------------


@dataclass(kw_only=True)
class Schema:
    """Defines the metadata for a single configuration option.

    The `Schema` class provides a lightweight interface for defining a single
    configuration option within a `Config` object. By placing multiple
    `Schema` instances inside a list, a `Config` object can define multiple
    options at once.

    Each `Schema` instance describes the characteristics of a configuration
    option. Except for the option name (the first positional argument), all
    attributes are optional and have sensible default values.

    The `Schema` class itself performs no validation logic; it is a simple
    data container that holds metadata about configuration options.

    Attributes:
        name (str):
            The name of the configuration option (required).
            For example, "debug" or "userrole".
            Optionally, the name may end with a `|<char>` suffix, where
            `<char>` defines the short flag used by the CLI.
            Example:
                `"userrole|r"` → option name: `cfg.userrole` → CLI: `--userrole -r`.
            If the `short_flag` attribute is explicitly provided, it takes
            precedence over the `|<char>` naming convention.

        short_flag (str | None):
            Optional single-character short name for CLI usage.

        default (Any | None):
            The default value of the option.

        required (bool):
            Whether the option must be provided (i.e., cannot be empty).

        field_type (Type[Any] | Tuple[Type[Any], ...] | None):
            The expected data type or tuple with data types for the option.
            For example: `str`, `int`, or a tuple of allowed types like `(int, str)`.

        r_min (int | None):
            The minimum value or size allowed. Applies to numeric types,
            string lengths, or collection sizes.
            (Validation ensures that `r_min` ≤ `r_max`.)

        r_max (int | None):
            The maximum value or size allowed. Applies to numeric types,
            string lengths, or collection sizes.

        domain (tuple[Any, ...] | None):
            A tuple of allowed values for the option.
            For example: `('admin', 'guest', 'tester')`.

        fn_validator (Callable | tuple[Callable, ...] | None):
            A function or tuple of functions used to perform custom validation.
            Each validator may raise an exception if validation fails.

        fn_computed (ComputedFn | tuple[ComputedFn, ...] | None):
            A function or tuple of functions that compute additional
            configuration properties dynamically.

        help_text (str | None):
            A short one-line help text shown in the CLI help output.

        help_add_default (bool):
            Whether to include the default value in the help text output.

        no_validate (bool):
            If True, disables most validation checks.
            Intended only for debugging or temporary use to bypass
            validation issues.
    """

    name: str = field(kw_only=False)
    short_flag: str | None = None
    default: Any | None = None
    required: bool = False
    field_type: Type[Any] | tuple[Type[Any], ...] | None = None
    r_min: int | None = None
    r_max: int | None = None
    domain: tuple[Any, ...] | None = None
    fn_validator: Callable | tuple[Callable, ...] | None = None
    fn_computed: ComputedFn | tuple[ComputedFn, ...] | None = None
    help_text: str | None = None
    help_add_default: bool = True
    no_validate: bool = False


# -----------------------------------------------------------------------------
# Define decorator function: with_field_name
# -----------------------------------------------------------------------------


def with_field_name(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that attaches a `field_name` attribute to a function.

    This decorator is designed for use with the `fn_computed` attribute
    of a `Schema` object. The assigned `field_name` value indicates the
    name of the configuration property that the decorated function will
    create within a `Config` object.

    Args:
        name (str):
            The name to assign to the `field_name` attribute.

    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]:
            A decorator that sets the `field_name` attribute on the decorated function.

    Example:
        >>> @with_field_name("hostname")
        ... def compute_hostname(config):
        ...     return config.base_url.split("//")[1]
        ...
        >>> compute_hostname.field_name
        'hostname'
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        fn.field_name = name  # type: ignore[attr-defined]
        return fn

    return decorator


# === END ===
