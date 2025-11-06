# Copyright (c) 2022-2025 Mario S. Könz; License: MIT
import dataclasses as dc
import typing as tp

__all__ = ["InspectDataclass", "MetaInfo"]


class MetaInfo(tp.NamedTuple):
    pk_key: str | None
    unique_together: list[str] | None
    extra_kwgs: dict[str, dict[str, tp.Any]] | None
    ordering: list[str] | None
    app_label: str | None
    db_table: str | None
    validate_on_save: bool


@dc.dataclass(frozen=True)
class InspectDataclass:
    dataclass: type

    def extract_meta(self) -> MetaInfo:
        pk_key, unique_together, extra_kwgs, ordering, app_label, db_table = (
            None,
            None,
            None,
            None,
            None,
            None,
        )
        validate_on_save = False
        if hasattr(self.dataclass, "Meta"):
            meta = self.dataclass.Meta
            if hasattr(meta, "primary_key"):
                pk_key = meta.primary_key
                if not isinstance(pk_key, str):
                    raise RuntimeError("primary_key must be a string, please fix!")
            if hasattr(meta, "unique_together"):
                unique_together = meta.unique_together
                assert isinstance(unique_together, list)
            if hasattr(meta, "extra"):
                extra_kwgs = meta.extra
                assert isinstance(extra_kwgs, dict)
            if hasattr(meta, "ordering"):
                ordering = meta.ordering
                assert isinstance(ordering, list)
            if hasattr(meta, "app_label"):
                app_label = meta.app_label
                assert isinstance(app_label, str)
            if hasattr(meta, "db_table"):
                db_table = meta.db_table
                assert isinstance(db_table, str)
            if hasattr(meta, "validate_on_save"):
                validate_on_save = meta.validate_on_save
                if not isinstance(validate_on_save, bool):
                    raise RuntimeError("validate_on_save must be a boolean")

        return MetaInfo(
            pk_key,
            unique_together,
            extra_kwgs,
            ordering,
            app_label,
            db_table,
            validate_on_save,
        )

    def get_identifying_parameter(self) -> set[str]:
        meta = self.extract_meta()
        pk_key = meta.pk_key
        unique_together = meta.unique_together
        res = set()
        if pk_key is not None:
            res.add(pk_key)
        if unique_together is not None:
            res.update(unique_together)
        return res
