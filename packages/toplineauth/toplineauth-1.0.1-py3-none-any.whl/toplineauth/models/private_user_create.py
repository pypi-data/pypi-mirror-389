from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PrivateUserCreate")


@_attrs_define
class PrivateUserCreate:
    """
    Attributes:
        email (str):
        password (str):
        full_name (str):
        is_verified (Union[Unset, bool]):  Default: False.
    """

    email: str
    password: str
    full_name: str
    is_verified: Union[Unset, bool] = False
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        email = self.email

        password = self.password

        full_name = self.full_name

        is_verified = self.is_verified

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
                "password": password,
                "full_name": full_name,
            }
        )
        if is_verified is not UNSET:
            field_dict["is_verified"] = is_verified

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        email = d.pop("email")

        password = d.pop("password")

        full_name = d.pop("full_name")

        is_verified = d.pop("is_verified", UNSET)

        private_user_create = cls(
            email=email,
            password=password,
            full_name=full_name,
            is_verified=is_verified,
        )

        private_user_create.additional_properties = d
        return private_user_create

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
