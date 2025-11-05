from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.user_tenants_response_tenants_item import UserTenantsResponseTenantsItem


T = TypeVar("T", bound="UserTenantsResponse")


@_attrs_define
class UserTenantsResponse:
    """用户租户列表响应

    Attributes:
        tenants (List['UserTenantsResponseTenantsItem']):
    """

    tenants: List["UserTenantsResponseTenantsItem"]
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        tenants = []
        for tenants_item_data in self.tenants:
            tenants_item = tenants_item_data.to_dict()
            tenants.append(tenants_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tenants": tenants,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.user_tenants_response_tenants_item import UserTenantsResponseTenantsItem

        d = src_dict.copy()
        tenants = []
        _tenants = d.pop("tenants")
        for tenants_item_data in _tenants:
            tenants_item = UserTenantsResponseTenantsItem.from_dict(tenants_item_data)

            tenants.append(tenants_item)

        user_tenants_response = cls(
            tenants=tenants,
        )

        user_tenants_response.additional_properties = d
        return user_tenants_response

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
