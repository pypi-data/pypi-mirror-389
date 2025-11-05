from typing import Any, Dict, List, Type, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="AssignRolesRequest")


@_attrs_define
class AssignRolesRequest:
    """分配角色请求

    Attributes:
        user_id (UUID):
        roles (List[str]):
    """

    user_id: UUID
    roles: List[str]
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        user_id = str(self.user_id)

        roles = self.roles

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "roles": roles,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        user_id = UUID(d.pop("user_id"))

        roles = cast(List[str], d.pop("roles"))

        assign_roles_request = cls(
            user_id=user_id,
            roles=roles,
        )

        assign_roles_request.additional_properties = d
        return assign_roles_request

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
