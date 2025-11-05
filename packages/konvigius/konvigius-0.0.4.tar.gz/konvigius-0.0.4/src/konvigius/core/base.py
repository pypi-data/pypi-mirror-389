# src/konvigius/core/base.py

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Callable, TYPE_CHECKING

from ..exceptions import ConfigError, ConfigValidationError

if TYPE_CHECKING:
    from ..configlib import Option

# -----------------------------------------------------------------------------
#  abstract base-class: Validator(ABC)
# -----------------------------------------------------------------------------


@dataclass
class Validator(ABC):
    """
    The Validator class is the base class for subclasses that perform checks on a value.

    When instantiating all subclasses, the `__init__` option, an Option instance, is
    validated. If these checks fail, a ConfigError is raised.

    Each subclass must implement the `_init_validate` and `_validate_value` methods.
    """

    option: Option

    def __post_init__(self):
        self._validator(self._init_validate)

    def __call__(self, value: Any, cfg: SimpleNamespace):
        self.cfg = cfg
        result = self._validator(self._validate_value, value=value)

        return result

    def _validator(self, fn: Callable, **kwargs):
        try:
            result = fn(**kwargs)
        except Exception as e:
            if isinstance(e, ConfigError):
                # Re-raise with amended message, preserving subclass
                new_exc = type(e)(f"{self.__class__.__name__}: {e}")
                raise new_exc from e
            else:
                # Wrap all other exceptions in ConfigValidationError
                raise ConfigValidationError(
                    f"{self.__class__.__name__} [{type(e).__name__}]: {e}"
                ) from e

        return result

    @abstractmethod
    # def _init_validate(self, **kwargs):
    def _init_validate(self):  # pragma: no cover
        pass

    @abstractmethod
    def _validate_value(self, value: Any) -> None | dict[str, Any]:  # pragma: no cover
        """
        Validate the given value.

        Args:
            value (Any): The value to validate.

        Returns:
            None | dict[str, Any]: Depending on the subclass.

        Raises:
            Any validation-specific exception (e.g., ConfigValidationError).
        """
        pass


# === END ===
