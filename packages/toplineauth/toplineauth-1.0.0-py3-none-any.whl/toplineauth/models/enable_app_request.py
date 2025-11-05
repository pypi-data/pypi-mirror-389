from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.enable_app_request_settings_type_0 import EnableAppRequestSettingsType0


T = TypeVar("T", bound="EnableAppRequest")


@_attrs_define
class EnableAppRequest:
    """启用应用请求

    Attributes:
        app_id (UUID):
        settings (EnableAppRequestSettingsType0 | None | Unset):
    """

    app_id: UUID
    settings: EnableAppRequestSettingsType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.enable_app_request_settings_type_0 import EnableAppRequestSettingsType0

        app_id = str(self.app_id)

        settings: dict[str, Any] | None | Unset
        if isinstance(self.settings, Unset):
            settings = UNSET
        elif isinstance(self.settings, EnableAppRequestSettingsType0):
            settings = self.settings.to_dict()
        else:
            settings = self.settings

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "app_id": app_id,
            }
        )
        if settings is not UNSET:
            field_dict["settings"] = settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.enable_app_request_settings_type_0 import EnableAppRequestSettingsType0

        d = dict(src_dict)
        app_id = UUID(d.pop("app_id"))

        def _parse_settings(data: object) -> EnableAppRequestSettingsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                settings_type_0 = EnableAppRequestSettingsType0.from_dict(data)

                return settings_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EnableAppRequestSettingsType0 | None | Unset, data)

        settings = _parse_settings(d.pop("settings", UNSET))

        enable_app_request = cls(
            app_id=app_id,
            settings=settings,
        )

        enable_app_request.additional_properties = d
        return enable_app_request

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
