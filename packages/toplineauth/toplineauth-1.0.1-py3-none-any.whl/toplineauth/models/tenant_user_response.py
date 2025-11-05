import datetime
from typing import Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="TenantUserResponse")


@_attrs_define
class TenantUserResponse:
    """租户用户响应

    Attributes:
        user_id (str):
        email (str):
        full_name (Union[None, str]):
        is_admin (bool):
        joined_at (datetime.datetime):
    """

    user_id: str
    email: str
    full_name: Union[None, str]
    is_admin: bool
    joined_at: datetime.datetime
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        user_id = self.user_id

        email = self.email

        full_name: Union[None, str]
        full_name = self.full_name

        is_admin = self.is_admin

        joined_at = self.joined_at.isoformat()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "email": email,
                "full_name": full_name,
                "is_admin": is_admin,
                "joined_at": joined_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        user_id = d.pop("user_id")

        email = d.pop("email")

        def _parse_full_name(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        full_name = _parse_full_name(d.pop("full_name"))

        is_admin = d.pop("is_admin")

        joined_at = isoparse(d.pop("joined_at"))

        tenant_user_response = cls(
            user_id=user_id,
            email=email,
            full_name=full_name,
            is_admin=is_admin,
            joined_at=joined_at,
        )

        tenant_user_response.additional_properties = d
        return tenant_user_response

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
