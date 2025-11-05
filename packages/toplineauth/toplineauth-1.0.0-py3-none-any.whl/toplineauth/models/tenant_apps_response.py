from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.tenant_apps_response_apps_item import TenantAppsResponseAppsItem


T = TypeVar("T", bound="TenantAppsResponse")


@_attrs_define
class TenantAppsResponse:
    """租户应用列表响应

    Attributes:
        apps (list[TenantAppsResponseAppsItem]):
    """

    apps: list[TenantAppsResponseAppsItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        apps = []
        for apps_item_data in self.apps:
            apps_item = apps_item_data.to_dict()
            apps.append(apps_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "apps": apps,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tenant_apps_response_apps_item import TenantAppsResponseAppsItem

        d = dict(src_dict)
        apps = []
        _apps = d.pop("apps")
        for apps_item_data in _apps:
            apps_item = TenantAppsResponseAppsItem.from_dict(apps_item_data)

            apps.append(apps_item)

        tenant_apps_response = cls(
            apps=apps,
        )

        tenant_apps_response.additional_properties = d
        return tenant_apps_response

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
