from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="LoginRequest")


@_attrs_define
class LoginRequest:
    """登录请求（使用 ID）

    Attributes:
        email (str):
        password (str):
        tenant_id (UUID):
        app_id (UUID):
    """

    email: str
    password: str
    tenant_id: UUID
    app_id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        password = self.password

        tenant_id = str(self.tenant_id)

        app_id = str(self.app_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
                "password": password,
                "tenant_id": tenant_id,
                "app_id": app_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        password = d.pop("password")

        tenant_id = UUID(d.pop("tenant_id"))

        app_id = UUID(d.pop("app_id"))

        login_request = cls(
            email=email,
            password=password,
            tenant_id=tenant_id,
            app_id=app_id,
        )

        login_request.additional_properties = d
        return login_request

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
