import datetime
from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="TenantInApp")


@_attrs_define
class TenantInApp:
    """应用中的租户

    Attributes:
        id (str):
        name (str):
        code (str):
        is_active (bool):
        joined_at (datetime.datetime):
    """

    id: str
    name: str
    code: str
    is_active: bool
    joined_at: datetime.datetime
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id

        name = self.name

        code = self.code

        is_active = self.is_active

        joined_at = self.joined_at.isoformat()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "code": code,
                "is_active": is_active,
                "joined_at": joined_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        name = d.pop("name")

        code = d.pop("code")

        is_active = d.pop("is_active")

        joined_at = isoparse(d.pop("joined_at"))

        tenant_in_app = cls(
            id=id,
            name=name,
            code=code,
            is_active=is_active,
            joined_at=joined_at,
        )

        tenant_in_app.additional_properties = d
        return tenant_in_app

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
