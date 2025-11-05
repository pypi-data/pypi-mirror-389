from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="RegisterRequest")


@_attrs_define
class RegisterRequest:
    """多租户注册请求

    Attributes:
        email (str):
        password (str):
        full_name (str):
        app_key (str):
        tenant_key (str):
    """

    email: str
    password: str
    full_name: str
    app_key: str
    tenant_key: str
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        email = self.email

        password = self.password

        full_name = self.full_name

        app_key = self.app_key

        tenant_key = self.tenant_key

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
                "password": password,
                "full_name": full_name,
                "app_key": app_key,
                "tenant_key": tenant_key,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        email = d.pop("email")

        password = d.pop("password")

        full_name = d.pop("full_name")

        app_key = d.pop("app_key")

        tenant_key = d.pop("tenant_key")

        register_request = cls(
            email=email,
            password=password,
            full_name=full_name,
            app_key=app_key,
            tenant_key=tenant_key,
        )

        register_request.additional_properties = d
        return register_request

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
