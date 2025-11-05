# src/konvigius/configlib.py
"""
Module for defining and managing dynamic configuration objects with metadata-driven
options.

This module provides classes to define configuration options with metadata, create
configuration objects dynamically, and validate the consistency of metadata during
configuration object creation.
It enables easy-to-use configuration management by transforming options into attributes
of a configuration object.

Classes:
    Option: Represents a configuration option with associated metadata. Instances of
            this class are dynamically converted into attributes of a configuration
            object.

    Config: The base class for creating dynamic configuration objects. Configuration
            objects are instantiated with attributes derived from Option objects. The
            configuration object automatically validates that the metadata of an Option
            is consistent upon creation.

    ConfigField:
            A Helper-Class.
            A building block of the Config class. It is responsible for converting an
            Option object into an attribute within the Config class.

Usage Example:
    Here is an example of how to create a configuration object using the Option and
    Config classes:

```python
from konvigius import Schema, Config

cfg = Config.config_factory([
          Schema("url", default="example.com"),
          Schema("port", default=80, domain=(80, 443))
])

print(cfg.url)      # Output: example.com
print(cfg.port)     # Output: 80
cfg.port = 443      # OK
print(cfg.port)     # Output: 443
cfg.port = 1000     # Raises a ConfigDomainError:
                    #     DomainValidator: value (1000) is not in the domain of
                    #                      acceptable values
```

In this example:
- `url` and `port` are dynamic attributes of the configuration object `cfg`.
- `url` has a default value of `"example.com"`.
- `port` has a default value of `80` and is constrained to the domain `(80, 443)`,
   meaning it can only have values `80` or `443`. Any attempt to assign a value
   outside this domain raises a `ConfigDomainError`.
"""
from __future__ import annotations  # prefends 'config' lint errors
import json
from types import SimpleNamespace
from typing import Any, Callable, Type, Tuple, Union

from .exceptions import ConfigError, ConfigMetadataError, ConfigInvalidFieldError

from .validators import (
    RequiredValidator,
    TypeValidator,
    RangeValidator,
    DomainValidator,
    CustomValidator,
    ComputedValidator,
)

from .core.types import ComputedFn, Schema

# -----------------------------------------------------------------------------
# 1. Define the Option metadata class
# -----------------------------------------------------------------------------


class Option:
    """Describes the properties and validation rules of a configuration option.

    Each configuration option is defined using keyword arguments from a
    corresponding `Schema` object. During instantiation of the surrounding
    `Config` object, these keyword arguments are validated using instances of
    subclasses of the `Validator` class.

    The following attributes of an `Option` instance are derived from the
    `Schema` object and subsequently validated:

    Attributes:
        name (str):
            The name of the configuration option, e.g., `'debug'` or `'userrole'`.
            A name can optionally end with a `'|<char>'` sequence, where `<char>`
            specifies the short CLI flag.
            Example:
                `"userrole|r"` → option name: `<cfg>.userrole`, CLI flag: `--userrole -r`

            If the `short_flag` is explicitly set in the `Schema` object, it takes
            precedence over the `'|<char>'` notation.

            Any hyphens (`-`) in the option name are replaced with underscores (`_`).

        default_value (Any | None):
            The default value for the option.

        required (bool):
            Whether the option must have a value (non-empty default).

        field_type (type | tuple[type, ...] | None):
            The expected data type(s) for the option.
            Multiple types can be specified as a tuple, e.g., `(int, str)`.

        domain (tuple[Any, ...] | None):
            A tuple defining the valid set of values for the option.
            Example: `('admin', 'guest', 'tester')`.

        r_min (int | None):
            The minimum value or length allowed for numeric, string, or other
            sizeable collections.
            A validation ensures that `r_min` cannot exceed `r_max`.

        r_max (int | None):
            The maximum value or length allowed for numeric, string, or other
            sizeable collections.

        fn_validator (Callable | tuple[Callable, ...] | None):
            A validation function (or tuple of functions) that performs
            additional checks and may raise exceptions.

        fn_computed (ComputedFn | tuple[ComputedFn, ...] | None):
            A function (or tuple of functions) that dynamically creates new
            configuration properties.
            Used for computed or derived configuration values.

        help_text (str | None):
            A one-line help text displayed in the CLI help output.

        help_add_default (bool):
            Whether the default value should be appended to the help text.

        do_validate (bool):
            When `False`, disables most validation checks.
            This should only be used temporarily to work around validation
            issues until a proper fix is found.

    Validation Process:
        The following validations are performed when `do_validate` is `True`:

        - The data type of the option value (initially the default value).
        - Whether the value belongs to the specified domain.
        - Whether a value is provided if the option is required.
        - Whether the value lies within the valid range (`r_min` / `r_max`).
        - Whether the value passes any custom validator functions.

        Additionally, the *compute validator* executes any functions specified
        in `fn_computed`, which generate derived fields as properties on the
        `Config` object.

        If `do_validate` is `False`, all these validation steps are skipped.
    """

    def __init__(self, entry: Schema, help_map: dict[str, str] | None = None):
        """Instantiate an Option object from a Schema definition.

        Creates a new Option instance using the attributes provided by a `Schema`
        object. If a help map is supplied, the help line defined in the `Schema`
        object will be overridden by the corresponding entry in the help map.

        Args:
            entry (Schema):
                The Schema instance that defines the metadata and validation rules
                for this option.
            help_map (dict[str, str] | None, optional):
                An optional mapping of help texts. If provided, the help text from
                this map will replace the one from the Schema definition.

        """
        self.default_value: Any | None = entry.default
        self.name, self.short_flag = Option.parse_entryname(
            entry.name, entry.short_flag
        )
        # self.field_type: Type[Any] | Tuple[Type[Any], ...] | None = entry.field_type
        self.field_type: Union[Type[Any], Tuple[Type[Any], ...], None] = (
            entry.field_type
        )
        self.required: bool = entry.required
        self.r_min: int | None = entry.r_min
        self.r_max: int | None = entry.r_max
        self.domain: tuple[Any, ...] | None = entry.domain
        self.fn_validator: Callable | tuple[Callable, ...] | None = entry.fn_validator
        self.fn_computed: ComputedFn | tuple[ComputedFn, ...] | None = entry.fn_computed
        self.do_validate: bool = not entry.no_validate
        self.help_add_default: bool = entry.help_add_default
        self.help_text: str | None = self._setup_helpline(
            self.name,
            entry.help_text,
            help_map,
            self.help_add_default,
            self.default_value,
        )

    # TODO: test on valid python identifier with builtin
    @staticmethod
    def parse_entryname(ename: str, short_flag: str | None):
        """Return the option name and its short CLI flag.

        Parses a configuration option name and optional short flag.
        If the `short_flag` is explicitly provided, it takes precedence over
        the shorthand character defined in the option name (e.g., `"userrole|r"`).

        Args:
            ename (str):
                The full option name, optionally containing a shorthand suffix in
                the form `"name|<char>"`.
            short_flag (str | None):
                An explicit one-character CLI flag. If provided, this overrides
                any shorthand specified in `ename`.

        Returns:
            tuple[str, str | None]:
                A tuple containing the normalized option name and the short flag
                (or `None` if no short flag was defined).

        Raises:
            ConfigMetadataError:
                If `short_flag` contains more than one character.
            ConfigMetadataError:
                If the option name is empty.
        """
        name, sep, _short_flag = ename.partition("|")
        name = name.strip("-").replace("-", "_") if name else name
        _short_flag = short_flag or _short_flag
        if not name:
            raise ConfigMetadataError(f"Schema name not valid ({ename})")
        if _short_flag and len(_short_flag) != 1:
            raise ConfigMetadataError(
                f"short CLI flags must be a single character: '{_short_flag}'"
            )
        return name, _short_flag or None

    @staticmethod
    def _setup_helpline(name, help_text, help_map, add_dflt, dflt):
        """Build the help line used for the CLI `-h` (help) output.

        Generates a descriptive help line for a configuration option. The function
        selects the most appropriate help text based on the following precedence:

        1. If a `help_map` is provided and contains an entry for `name`, that value
           is used.
        2. Otherwise, the help text from the Schema (`help_text`) is used.
        3. If no help text is available, a generic placeholder of the form
           `"Option: <name>"` is created.

        When `add_dflt` is `True`, the default value is appended to the help line
        in the form `" (default '<value>')"`. Non-primitive default values are
        converted to strings.

        Args:
            name (str):
                The name of the configuration option.
            help_text (str | None):
                The base help text from the Schema definition.
            help_map (dict[str, str] | None):
                Optional mapping that can override help texts by name.
            add_dflt (bool):
                Whether to append the default value to the help text.
            dflt (Any):
                The default value to include if `add_dflt` is enabled.

        Returns:
            str:
                The formatted help line suitable for CLI help display.

        Example:
            `>>> Option._setup_helpline("debug", "Enable debug mode", None, True, False)`
                "Enable debug mode (default 'False')"
        """
        # setup the helpline
        helpline = help_text
        if help_map:
            helpline = help_map.get(name, help_text)
        if not helpline:
            helpline = f"Option: {name}"
        if add_dflt:
            _default = ""
            if isinstance(dflt, (str, int, float, bool)):
                _default = f" (default '{dflt}')"
            else:
                _default = f" (default '{str(dflt)}')"
            helpline = f"{helpline}{_default}"
        return helpline

    # At Option level the validation can be switched on/off (a Schema option)

    def init_validators(self):
        """Initialize the validator subclasses.

        Creates a set of validator objects based on the properties defined in the
        current `Option` instance. During initialization, each validator checks
        whether the corresponding option attributes are correctly specified.

        The following validators are instantiated:

          * `TypeValidator` – Ensures the option value matches the expected data type.
          * `RequiredValidator` – Checks that required options are not empty.
          * `DomainValidator` – Validates that the option value belongs to a valid domain.
          * `RangeValidator` – Verifies that numeric or sequence values fall within
            the defined range.

        Additionally, two special validators are created:

          * `CustomValidator` – Executes user-defined validation functions.
          * `ComputedValidator` – Evaluates computed field functions (`fn_computed`).

        These validators are only created if validation is enabled at the
        `Option` level (`do_validate=True`).
        """
        self._validators = []
        if self.do_validate:  # at Option level validation can be switched on/off
            self._validators.append(TypeValidator(self))
            self._validators.append(RequiredValidator(self))
            self._validators.append(DomainValidator(self))
            self._validators.append(RangeValidator(self))
            # custom and computes validators:
            self._custom_validator = CustomValidator(self)
            self._comp_validator = ComputedValidator(self)

    def validate_default(self, value: Any, cfg: Config):
        """Validate the option value using the standard validators.

        Executes all core validators defined in `_validators` for this option,
        ensuring that the value meets the type, domain, range, and required-field
        constraints.

        Validation runs only if `do_validate` is enabled.

        Args:
            value (Any):
                The value to validate.
            cfg (Config):
                The configuration object providing context for validation.
        """
        if self.do_validate:
            for validator in self._validators:
                validator(value, cfg=cfg.copy_config(dirty=True))

    def validate_custom(self, value: Any, cfg: Config):
        """Validate the option value using custom validation functions.

        Invokes user-defined validator functions associated with this option.
        Custom validation runs only if `do_validate` is enabled.

        Args:
            value (Any):
                The value to validate.
            cfg (Config):
                The configuration object providing context for validation.
        """
        if self.do_validate:  # at Option level validation can be switched on/off
            self._custom_validator(value, cfg=cfg.copy_config(dirty=True))

    def validate_computed(self, value: Any, cfg: Config):
        """Validate and compute auto-generated (derived) configuration fields.

        Executes all functions defined in `fn_computed`, allowing computed fields
        to be dynamically generated based on other configuration values. The
        computed results are stored in `cfg._computed_values`.

        Computation runs only if `do_validate` is enabled.

        Args:
            value (Any):
                The current option value used as input for computation.
            cfg (Config):
                The configuration object providing context and storage for results.
        """
        if self.do_validate:  # at Option level validation can be switched on/off
            values_computed = self._comp_validator(
                value, cfg=cfg.copy_config(dirty=True)
            )
            for fname, value in values_computed.items():
                cfg._computed_values[fname] = value

    def __repr__(self):
        """Return a string representation that can recreate the object.

        Returns:
            str: A string that represents the constructor call needed
            to recreate this Option instance.
        """
        args = [
            f"{name}={value!r}"
            for name, value in vars(self).items()
            if not name.startswith("_") and name not in ("fn_validators", "fn_computes")
        ]
        args = ", ".join(args)
        return f"Option({args})"

    def __str__(self):
        """Return a multiline, human-readable string representation.

        Provides a formatted overview of all public attributes and their values,
        suitable for debugging or CLI output.

        Returns:
            str: A multiline string containing all option names and their values.
        """
        header = "<Option values>"
        # body = [f"  {name}: {getattr(self, name)!r}" for name, alue in vars(self)]
        body = [
            f"  - {name}: {value!r}"
            for name, value in vars(self).items()
            if not name.startswith("_")
        ]
        lines = [header] + body
        return "\n".join(lines)


# -----------------------------------------------------------------------------
# 2. Define the descriptor to handle access + validation
# -----------------------------------------------------------------------------


class ConfigField:
    """Descriptor that manages access and validation for a single config field.

    Each ConfigField wraps an `Option`, which defines the metadata
    (e.g., default value, type constraints, min/max range) for that field.

    This descriptor is installed on dynamically generated `Config` subclasses
    via the `config_factory()` method. It intercepts attribute access to:

    - Return either the set value or the default.
    - Validate assigned values before storing.
    """

    def __init__(self, option: Option):
        """Initializes the descriptor with the associated Option.

        Args:
            option (Option): Metadata describing the field
                             (default, type, constraints, etc.)
        """
        self.option = option

    def __get__(self, cfg, owner):
        """Retrieves the value of the config field for the given instance (cfg).

        - If accessed via the class (e.g., `ConfigClass.field`), returns the descriptor itself.
        - If accessed via an instance, returns the stored value or the default.

        Args:
            instance (Config): The config instance this field belongs to.
            owner (type): The owner class.

        Returns:
            Any: The current value of the field, or its default if unset.
        """
        if cfg is None:  # pragma: no coverage
            return self  # Accessed from class
        return cfg._pending_values.get(self.option.name, cfg._values[self.option.name])

        # return cfg._values.get(self.name, self.option.default_value)

    def __set__(self, cfg, value):
        """Validates and sets the value of the config field on the given instance (cfg).

        This method ensures the assigned value meets all constraints defined in
        the associated `Option`, such as type, min, and max.

        Args:
            instance (Config): The config instance this field belongs to.
            value (Any): The value to be assigned.

        Raises:
            A ConfigError: If the value fails validation.
        """
        # print("* Config_Field:", self.option.name, " old", cfg._values[self.option.name], " new:", value, " _trx_", cfg._trx_)
        if cfg._trx_:
            # transaction mode, put all in temporary pending datastore
            cfg._pending_values[self.option.name] = value
        else:
            cfg.start_transaction()
            cfg._pending_values[self.option.name] = value
            cfg.commit_transaction(suppress_error_prefix=True)


# -----------------------------------------------------------------------------
# 3. Config class that manages instance state and metadata
# -----------------------------------------------------------------------------


class Config:
    """Base class for dynamically generated configuration objects.

    This class is not used directly, but acts as a base for subclasses
    created by `Config.config_factory()` or `Config.from_dict()`.

    Each instance manages:
    - `_values`: The actual runtime values for each config field.
    - `_metadata`: A dictionary of Option objects keyed by field name,
                   used for validation, default handling, and introspection.
    """

    def __init__(self):
        """Initializes internal state for a Config instance.

        - `_values` holds actual values set by the user or defaults.
        - `_metadata` holds the schema (Option) for each config field.

        Normally this constructor is called indirectly via `config_factory()`.
        """
        self._values = {}  # current values per instance
        self._pending_values = {}  # mutated values per instance
        self._computed_values = {}  # derived values per instance
        self._metadata = {}  # Option objects per field
        self._trx_: bool = False  # transaction mode

    def _create_inverted_bool_properties(self):
        """Auto generate inverted version of boolean fields.

        Lazy operation.
        """

        # inner-helper function returning a closure:
        def fn_return_inverted(
            source_field: str, field_name: str
        ) -> Callable[[str, SimpleNamespace], bool]:
            """TODO:"""

            def fn_return_bool(value: str, cfg: SimpleNamespace) -> bool:
                # print("return inverted-bool", value, "--" , source_field)
                # value = cfg._values[source_field]
                return not value

            fn_return_bool.field_name = field_name  # type: ignore[attr-defined]
            return fn_return_bool

        # end-closure

        for option in self._metadata.values():
            if not option.do_validate:
                continue

            existing = list(option._comp_validator.fn_callbacks)
            if option.field_type is bool:
                if option.name.startswith("no_"):
                    field_name = option.name.partition("_")[2]
                else:
                    field_name = "no_" + option.name

                if field_name and field_name not in self._metadata:
                    existing.append(fn_return_inverted(option.name, field_name))
            option._comp_validator.fn_callbacks = tuple(existing)

    def _create_computed_properties(self):
        """Auto generate custom config fields based on Option property 'fn_computed'.

        This will create the read-only properties for the config-instance based on the
        metadata object Option.computed.
        These properties return their values from cfg._computed_values.
        """
        cfg = self
        for option in self._metadata.values():
            if not option.do_validate:
                continue

            for fn in option._comp_validator.fn_callbacks:
                if fn.field_name in self._metadata:
                    # the computed fieldname may not be already in use
                    raise ConfigInvalidFieldError(
                        "cannot create computed field "
                        f"'{fn.field_name}', field already exists; "
                        "choose a different name.",
                        fn.field_name,
                    )

                # create a property (wihtout setter) for this computed field
                prop = property(make_getter(fn.field_name))
                setattr(cfg.__class__, fn.field_name, prop)

    def start_transaction(self):
        if self._trx_:
            return

        self._trx_ = True
        self._pending_values.clear()

    def commit_transaction(self, suppress_error_prefix=False):
        if not self._trx_:
            return

        merged = {**self._values, **self._pending_values}

        try:
            # Run the validators
            for option in self._metadata.values():
                option.validate_default(merged[option.name], self)

            # Run the custom validators
            for option in self._metadata.values():
                option.validate_custom(merged[option.name], self)

            # Run the computes validators
            for option in self._metadata.values():
                option.validate_computed(merged[option.name], self)

            # at this point no exception was raised, copy merged to the actual datastore (this is the commit phase)
            self._values = merged

        except Exception as e:
            raise
            # if suppress_error_prefix:
            #     msg = f"{e}")
            #     raise ConfigError(e)
            # else:
            #     msg = f"Commit raised an error (changes are undone): {e}")

        finally:
            self._trx_ = False
            self._pending_values.clear()

    def rollback_transaction(self):
        self._trx_ = False
        self._pending_values.clear()

    @classmethod
    def config_factory(
        cls,
        schema: list[Schema],
        *,
        help_map: dict[str, str] | None = None,
        auto_bools: bool = True,
    ) -> Config:
        """
        Dynamically creates a Config subclass with fields based on the provided
        schema.

        This method constructs a subclass of Config by injecting `ConfigField`
        descriptors for each field defined in the schema.

        This is the core entry point for schema-based config creation.

        Args:
            schema (list[Schema]):
                A list of Schema options.

            help_map (dict[str, str], optional):
                Mapping from long field names to help text. This will inject
                the helptext into the corresponding Option object.

            auto_bools (bool, optional):
                Whether inverted boolean fields must be generated.

        Returns:
            Config: An instance of a dynamically generated Config subclass.

        Raises:
            ConfigMetadataError: If any Option metadata is invalid.

        Example:
            schema = [
                 Schema("username|u", default="guest", field_type=str),
                 Schema("timeout|t", default=30, r_min=1, r_max=60, field_type=int),
            ]
            cfg = Config.config_factory(schema)
            print(cfg.username)  # → 'guest'
            print(cfg.timeout)   # → 30
        """
        # Create the ConfigField objects, each referencing an Option object.

        namespace = {}
        for entry in schema:
            option = Option(entry, help_map)
            namespace[option.name] = ConfigField(option)

        # Create a Config instance dynamically

        Config_cls = type("DynamicConfig", (cls,), namespace)
        cfg = Config_cls()

        # Instantiate the default validators and fill the backend datastore

        for config_field in namespace.values():
            option = config_field.option  # aliasing
            option.init_validators()
            cfg._metadata[option.name] = option
            cfg._values[option.name] = option.default_value

        # Run the validators

        for option in cfg._metadata.values():
            option.validate_default(cfg._values[option.name], cfg)

        # Run the custom validators

        for option in cfg._metadata.values():
            option.validate_custom(cfg._values[option.name], cfg)

        # Add properties for bool typed Options: inverted bools.

        if auto_bools:
            cfg._create_inverted_bool_properties()

        # Create properties for the conputed-functions from the Schema-field fn_computed

        cfg._create_computed_properties()

        # Run the field-computation validators

        for option in cfg._metadata.values():
            option.validate_computed(cfg._values[option.name], cfg)

        return cfg

    @classmethod
    def from_dict(cls, schema: list[Schema], values: dict):
        """
        Create a Config instance from a schema and a dictionary of override
        values.

        Use this to load user-configured values in a dictionary while falling
        back on defaults defined in the schema.

        This method:
        - Calls `config_factory()` to construct the config instance based on
          schema
        - Applies override values from the provided dictionary
        - Performs validation on all overridden values

        Args:
            schema (list): A list of Schema objects defining the schema defaults.
            values (dict): A dictionary of values to override defaults.

        Returns:
            Config: A fully validated config instance with applied overrides.

        Raises:
            ConfigInvalidFieldError: If a key in `values` is not part of the schema.
            ValueError / TypeError: If any override value fails validation.
        """
        cfg = cls.config_factory(schema)

        cfg.start_transaction()
        for name, value in values.items():
            if name not in cfg._metadata:
                raise ConfigInvalidFieldError(f"Invalid config field: '{name}'.", name)

            setattr(cfg, name, value)  # triggers validation via descriptor
        cfg.commit_transaction()

        return cfg

    def get_computed_prop(self, name):
        """Return the value produced by the fn_computed attribute (callable) from
        the metadata object (Option) for the given field name.

        Note:
        The value of 'name' can also be retrieved on the cfg instance as
        a regular fieldname: cfg.some_computed_field (a property).

        Args:
            name (str): The name of the field with the derived value.

        Returns:
            Some value (Any): The values that was produced.
        """
        return self._computed_values.get(name, f"Field '{name}' is invalid")

    def get_meta(self, name):
        """Return the Option metadata object for the given field name.

        This can be used for introspection, e.g., to inspect default values,
        type expectations, or constraints.

        Args:
            name (str): The name of the config field.

        Returns:
            Option or None: The metadata object for the field, or None
            if the field is not defined in this config instance.
        """
        return self._metadata.get(name)

    def to_dict(self) -> dict:
        """Return a dictionary representation of the current config values.

        This includes both default values and any values overridden at runtime.

        Returns:
            dict: A mapping of field names to their current values.
        """
        return {name: getattr(self, name) for name in self._metadata.keys()}

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize the current config values to a JSON-formatted string.

        Args:
            indent (int): Number of spaces for indentation in the JSON output.

        Returns:
            str: JSON string of the current config values.
        """
        # TODO:this is not finished, actual / pending values are not incooperated
        return json.dumps(self.to_dict(), indent=indent)

    # TODO: add parameter exclude_fields (e.g. big lists)
    def inspect_vars(self, chop_at: int = 45) -> str:
        """
        Utility to display field names, values and their help text from the
        config object.

        The table is formatted as markdown.

        Args:
            chop_at (int): Maximum length of the fields (default 45)

        Returns:
            str: a string with the markdown table.
        """
        chop_at = chop_at if chop_at > 15 else 15
        # create table header
        lengths = [str(ln) if ln < chop_at else chop_at for ln in (15, 22, 6, 40)]
        headers = zip(["Field", "Value", "Source", "Description"], lengths)
        lines = ["| " + " | ".join([f"{h[0]:<{h[1]}}" for h in headers]) + " |"]
        headers = zip(list("----"), lengths)
        lines.append("| " + " | ".join([f"{h[0] * int(h[1])}" for h in headers]) + " |")

        sorted_rows = sorted(self)

        for row in sorted_rows:
            if (name := row[0]) in self._metadata:
                desc = self._metadata[name].help_text or ""
            else:
                desc = "Autogenerated: " + name
            zrow = zip(row + (desc,), lengths)
            lines.append(
                "| " + " | ".join(f"{cell[0]!r:<{cell[1]}}" for cell in zrow) + " |"
            )

        return "\n".join(lines)

    def copy_config(self, dirty=False) -> SimpleNamespace:
        """Create a simple copy of the config attribute values.

        Args:
            dirty (bool): If True, includes mutated values in the copy, even if they
                          are not final.

        Returns:
            SimpleNameSpace: A copy of the config values.
        """
        data = {fname: value for fname, value, _ in self}
        data["_values"] = {**self._values}
        data["_computed_values"] = {**self._computed_values}
        if dirty:
            data = {**data, **self._pending_values}

        return SimpleNamespace(**data)

    def __len__(self):
        """Return number of fields.

        These fields consists of:
         - config_fields
         - generated properties like computed fields
         - auto generated inverted booleans.
        """
        return len(self._values) + len(self._computed_values)

    def __iter__(self):
        yield from ((key, value, "S") for key, value in self._values.items())
        yield from ((key, value, "C") for key, value in self._computed_values.items())

    def __str__(self):
        header = "<Config values>"
        body = [f"  {name}: {getattr(self, name)!r}" for name in self._metadata]
        lines = [header] + body
        return "\n".join(lines)

    def __repr__(self):
        items = [f"{k}={getattr(self, k)!r}" for k in self._metadata]
        joined = ", ".join(items)
        return f"<Config: {joined}>"


# === Module functions ===


def make_getter(attr):
    def getter(self):
        return self._computed_values[attr]

    return getter


# def make_setter(attr):  # pragma: no coverage
#     def setter(self, value):
#         self._computed_values[attr] = value
#
#     return setter


# === END ===
