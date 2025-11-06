# Copyright (c) 2022-2025 Mario S. Könz; License: MIT
import dataclasses as dc
import datetime
import enum
import types
import typing as tp  # pylint: disable=reimported
import uuid
from decimal import Decimal
from pathlib import Path

import django.db  # pylint: disable=unused-import
from django.core import validators as dj_validators
from django.db import models

from ._decorator import BACKEND_LINKER
from ._decorator import django_model
from ._inspect_dataclass import InspectDataclass
from ._model_fields import is_pydantic_model
from ._model_fields import iter_model_fields
from ._model_fields import ModelFieldInfo
from ._model_fields import require_pydantic
from ._util import public_name

# 2023-Q1: sphinx has a bug regarding adjusting the signature for attributes,
# hence I need fully qualified imports for typing and django.db

__all__ = ["CreateDjangoModel", "create_django_model"]


@dc.dataclass(frozen=True)
class CreateDjangoModel(InspectDataclass):
    alt_field_type: "dict[str, type[models.Field[tp.Any,tp.Any]]]" = dc.field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        # evaluate the Meta class
        meta = self.extract_meta()

        if not (meta.unique_together or meta.pk_key):
            raise RuntimeError("specify either unique_together or pk_key")
        # translate fields
        fields: dict[str, tp.Any] = self.translate_fields(meta.pk_key, meta.extra_kwgs)
        if not meta.validate_on_save:
            fields.pop("save")

        fields["Meta"] = self.generate_meta(
            meta.unique_together, meta.ordering, meta.app_label, meta.db_table
        )
        # pylint: disable=comparison-with-callable
        if self.dataclass.__str__ != object.__str__:  # type: ignore
            fields["__str__"] = self.dataclass.__str__
        fields["__module__"] = fields["Meta"].app_label
        if "." in fields["Meta"].app_label:
            fields["Meta"].app_label = fields["Meta"].app_label.rsplit(".", 1)[1]
        dj_model = type(self.dataclass.__name__, (models.Model,), fields)
        BACKEND_LINKER.link(self.dataclass, dj_model)

    def translate_fields(
        self,
        pk_key: str | None,  # pylint: disable=unused-argument
        extra_kwgs: dict[str, dict[str, tp.Any]] | None,
    ) -> "dict[str, models.Field[tp.Any, tp.Any]]":
        fields: dict[str, models.Field[tp.Any, tp.Any]] = {}
        for field in iter_model_fields(self.dataclass):
            name = field.name
            raw_type = field.annotation
            metadata = field.metadata
            default = field.default
            constraints = field.constraints
            try:
                django_field = self.alt_field_type.pop(name)
                opts: dict[str, tp.Any] = {}
            except KeyError:
                type_ = self._extract_pydantic_type(raw_type)
                django_field, opts = self.django_field_precursor(type_)  # type: ignore[unused-ignore,arg-type]
            if name == pk_key:
                opts["primary_key"] = True
                if django_field is models.ForeignKey:
                    django_field = models.OneToOneField
            if default is not dc.MISSING:
                opts["default"] = default
            extra = dict(metadata)
            if extra_kwgs:
                extra.update(extra_kwgs.pop(name, {}))
            for key in self._metadata_keys_to_skip(raw_type):
                extra.pop(key, None)
            self._apply_constraints(django_field, opts, extra, constraints)
            fields[name] = django_field(**{**opts, **extra})
        if extra_kwgs:
            raise RuntimeError(
                f"unconsumed extra kwgs ({extra_kwgs}) found for {self.dataclass}, please adjust!"
            )
        if self.alt_field_type:
            raise RuntimeError(
                f"unused alt_field_type ({self.alt_field_type}) found for {self.dataclass}, please adjust!"
            )
        self._add_validation_on_save(fields)
        return fields

    @classmethod
    def _extract_pydantic_type(cls, type_: type[tp.Any]) -> type[tp.Any]:
        is_annotated = tp.get_origin(type_) is tp.Annotated
        if is_annotated:
            return tp.get_args(type_)[0]  # type: ignore
        return type_

    @staticmethod
    def _metadata_keys_to_skip(annotation: tp.Any) -> tp.Iterable[str]:
        base = annotation
        if tp.get_origin(base) is tp.Annotated:
            base = tp.get_args(base)[0]
        if base is Path:
            return ("resave", "allow_dir")
        origin = tp.get_origin(base)
        if origin in {tp.Union, types.UnionType}:
            args = tp.get_args(base)
            if Path in args and type(None) in args:
                return ("resave",)
        return ()

    def _apply_constraints(  # pylint: disable=too-many-branches
        self,
        django_field: "type[models.Field[tp.Any,tp.Any]]",
        opts: dict[str, tp.Any],
        extra: dict[str, tp.Any],
        constraints: dict[str, tp.Any],
    ) -> None:
        if not constraints:
            return

        validators: list[tp.Callable[[tp.Any], None]] = list(opts.get("validators", []))

        if issubclass(django_field, models.CharField) or issubclass(
            django_field, models.TextField
        ):
            max_length = constraints.get("max_length")
            if max_length is not None:
                existing = opts.get("max_length", extra.get("max_length"))
                if existing is None or max_length < existing:
                    opts["max_length"] = max_length
            min_length = constraints.get("min_length")
            if min_length is not None:
                validators.append(dj_validators.MinLengthValidator(min_length))
            pattern = constraints.get("pattern")
            if pattern is not None:
                validators.append(dj_validators.RegexValidator(pattern))

        if issubclass(
            django_field,
            (models.IntegerField, models.FloatField, models.DecimalField),
        ):
            if "ge" in constraints:
                validators.append(dj_validators.MinValueValidator(constraints["ge"]))
            if "gt" in constraints:
                validators.append(GreaterThanValidator(constraints["gt"]))
            if "le" in constraints:
                validators.append(dj_validators.MaxValueValidator(constraints["le"]))
            if "lt" in constraints:
                validators.append(LessThanValidator(constraints["lt"]))
            if "multiple_of" in constraints:
                validators.append(MultipleOfValidator(constraints["multiple_of"]))

        if validators:
            opts["validators"] = validators

    def _resolve_pydantic_validator(
        self,
    ) -> tp.Optional[tuple[tp.Callable[[dict[str, tp.Any]], tp.Any], type[Exception]]]:
        if is_pydantic_model(self.dataclass):
            pyd = require_pydantic("to validate BaseModel subclasses")
            return self.dataclass.model_validate, pyd.ValidationError  # type: ignore
        validator = getattr(self.dataclass, "__pydantic_validator__", None)
        if validator is not None:
            pyd = require_pydantic("to validate dataclasses")
            return validator.validate_python, pyd.ValidationError
        return None

    @staticmethod
    def _collect_validation_payload(
        model_instance: models.Model,
        fields: tp.Iterable[ModelFieldInfo],
    ) -> dict[str, tp.Any]:
        payload: dict[str, tp.Any] = {}
        for field in fields:
            value = getattr(model_instance, field.name)
            if isinstance(value, models.Manager):
                value = list(value.all())
            payload[field.name] = value
        return payload

    def _add_validation_on_save(self, fields: tp.Dict[str, tp.Any]) -> None:
        validator_info = self._resolve_pydantic_validator()
        validator_fields: tuple[ModelFieldInfo, ...] = (
            tuple(iter_model_fields(self.dataclass)) if validator_info else tuple()
        )

        def save(mod_self: models.Model, *args: tp.Any, **kwgs: tp.Any) -> None:
            mod_self.full_clean(validate_unique=False, validate_constraints=False)
            super(type(mod_self), mod_self).save(*args, **kwgs)  # type: ignore  # pylint: disable=bad-super-call

        def clean(mod_self: models.Model) -> None:
            super(type(mod_self), mod_self).clean()  # type: ignore  # pylint: disable=bad-super-call
            if not validator_info:
                return
            validator, error_type = validator_info
            payload = self._collect_validation_payload(mod_self, validator_fields)
            try:
                validator(payload)
            except error_type as exc:
                raise exc

        fields["clean"] = clean
        fields["save"] = save  # will get removed depending on validate_on_save

    def generate_meta(
        self,
        unique_together: list[str] | None,
        ordering: list[str] | None,
        app_label: str | None,
        db_table: str | None,
    ) -> type:
        if app_label is None:
            app_label = public_name(self.dataclass, without_cls=True)
        if db_table is None:
            db_table = public_name(self.dataclass)

        class Meta:
            pass

        Meta.app_label = app_label  # type: ignore
        Meta.db_table = db_table  # type: ignore

        if unique_together:
            Meta.unique_together = unique_together  # type: ignore

        if ordering:
            Meta.ordering = ordering  # type: ignore
        return Meta

    @classmethod
    def django_field_precursor(
        cls, type_: type
    ) -> "tuple[type[models.Field[tp.Any,tp.Any]], dict[str, tp.Any]]":
        # pylint: disable=too-many-return-statements,too-many-branches
        special = cls._pydantic_special_field(type_)
        if special is not None:
            return special
        if type_ == str:
            return models.CharField, dict(max_length=1024)
        if type_ == int:
            return models.IntegerField, {}
        if type_ == float:
            return models.FloatField, {}
        if type_ == datetime.datetime:
            return models.DateTimeField, {}
        if type_ == datetime.date:
            return models.DateField, {}
        if type_ == datetime.time:
            return models.TimeField, {}
        if type_ == bytes:
            return models.BinaryField, dict(editable=True)
        if type_ == bool:
            return models.BooleanField, {}
        if type_ == uuid.UUID:
            return models.UUIDField, {}

        if isinstance(type_, types.GenericAlias):
            origin = tp.get_origin(type_)
            subtypes = tp.get_args(type_)
            if origin is set:
                assert len(subtypes) == 1
                subtype = subtypes[0]
                try:
                    fk_class = BACKEND_LINKER.backend_class(subtype)
                    assert issubclass(fk_class, models.Model)
                    return models.ManyToManyField, dict(to=fk_class, related_name="+")
                except KeyError:
                    pass

        if isinstance(type_, types.UnionType):
            target_type, none_type = tp.get_args(type_)
            if none_type is type(None):  # pylint: disable=unidiomatic-typecheck
                field, kwgs = cls.django_field_precursor(target_type)
                kwgs["blank"] = True
                kwgs["null"] = True
                return field, kwgs

        if issubclass(type_, enum.Enum):
            max_length = 256
            choices = []
            for val in type_.__members__.values():
                choices.append((val.value, val.value))
                assert len(val.value) < max_length

            return models.CharField, dict(max_length=max_length, choices=choices)

        if issubclass(type_, Path):
            return models.FileField, dict(max_length=1024)

        try:  # try Foreign Key relation (many-to-one)
            fk_class = BACKEND_LINKER.backend_class(type_)
            assert issubclass(fk_class, models.Model)
            return models.ForeignKey, dict(
                to=fk_class, on_delete=models.CASCADE, related_name="+"
            )

        except KeyError:
            pass

        raise NotImplementedError(type_)

    @classmethod
    def _pydantic_special_field(
        cls, type_: type
    ) -> "tp.Optional[tuple[type[models.Field[tp.Any,tp.Any]], dict[str, tp.Any]]]":
        try:
            pyd = require_pydantic("to map Pydantic constrained types")
        except RuntimeError:
            return None

        mapping: (
            "list[tuple[type, type[models.Field[tp.Any,tp.Any]], dict[str, tp.Any]]]"
        )
        mapping = [
            (pyd.EmailStr, models.EmailField, {}),
            (pyd.AnyUrl, models.URLField, {}),
            (pyd.AnyHttpUrl, models.URLField, {}),
            (pyd.HttpUrl, models.URLField, {}),
            (
                pyd.networks.IPv4Address,
                models.GenericIPAddressField,
                dict(protocol="IPv4"),
            ),
            (
                pyd.networks.IPv6Address,
                models.GenericIPAddressField,
                dict(protocol="IPv6"),
            ),
            (pyd.networks.IPvAnyAddress, models.GenericIPAddressField, {}),
            (pyd.Json, models.JSONField, {}),
        ]

        for pyd_type, dj_field, options in mapping:
            if type_ is pyd_type:
                return dj_field, dict(options)
        return None


def create_django_model(
    dataclass: type,
    alt_field_type: "dict[str, type[models.Field[tp.Any, tp.Any]]] | None" = None,
) -> "type[models.Model]":
    alt_field_type = alt_field_type or {}
    CreateDjangoModel(dataclass, alt_field_type)
    return django_model(dataclass)


class GreaterThanValidator(dj_validators.BaseValidator):
    message = "Ensure this value is greater than %(limit_value)s."
    code = "greater_than"

    def compare(self, a: tp.Any, b: tp.Any) -> bool:
        return a <= b  # type: ignore


class LessThanValidator(dj_validators.BaseValidator):
    message = "Ensure this value is less than %(limit_value)s."
    code = "less_than"

    def compare(self, a: tp.Any, b: tp.Any) -> bool:
        return a >= b  # type: ignore


class MultipleOfValidator(dj_validators.BaseValidator):
    message = "Ensure this value is a multiple of %(limit_value)s."
    code = "multiple_of"

    def __init__(self, limit_value: tp.Any) -> None:
        super().__init__(Decimal(str(limit_value)) if limit_value != 0 else Decimal(0))

    def clean(self, x: tp.Any) -> Decimal:
        return Decimal(str(x))

    def compare(self, a: Decimal, b: Decimal) -> bool:
        if b == 0:
            return False
        return a % b != 0
