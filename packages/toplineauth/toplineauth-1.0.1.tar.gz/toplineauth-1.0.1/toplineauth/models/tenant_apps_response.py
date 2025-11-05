from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.tenant_apps_response_apps_item import TenantAppsResponseAppsItem


T = TypeVar("T", bound="TenantAppsResponse")


@_attrs_define
class TenantAppsResponse:
    """租户应用列表响应

    Attributes:
        apps (List['TenantAppsResponseAppsItem']):
    """

    apps: List["TenantAppsResponseAppsItem"]
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        apps = []
        for apps_item_data in self.apps:
            apps_item = apps_item_data.to_dict()
            apps.append(apps_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "apps": apps,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.tenant_apps_response_apps_item import TenantAppsResponseAppsItem

        d = src_dict.copy()
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
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
