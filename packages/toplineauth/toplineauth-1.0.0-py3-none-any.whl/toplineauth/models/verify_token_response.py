from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="VerifyTokenResponse")


@_attrs_define
class VerifyTokenResponse:
    """验证令牌响应

    Attributes:
        valid (bool): 令牌是否有效
        user_id (None | str | Unset): 用户ID
        tenant_id (None | str | Unset): 租户ID
        app_id (None | str | Unset): 应用ID
        roles (list[Any] | None | Unset): 角色列表
        permissions (list[Any] | None | Unset): 权限列表
        exp (int | None | Unset): 过期时间戳
        message (None | str | Unset): 错误信息
    """

    valid: bool
    user_id: None | str | Unset = UNSET
    tenant_id: None | str | Unset = UNSET
    app_id: None | str | Unset = UNSET
    roles: list[Any] | None | Unset = UNSET
    permissions: list[Any] | None | Unset = UNSET
    exp: int | None | Unset = UNSET
    message: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        valid = self.valid

        user_id: None | str | Unset
        if isinstance(self.user_id, Unset):
            user_id = UNSET
        else:
            user_id = self.user_id

        tenant_id: None | str | Unset
        if isinstance(self.tenant_id, Unset):
            tenant_id = UNSET
        else:
            tenant_id = self.tenant_id

        app_id: None | str | Unset
        if isinstance(self.app_id, Unset):
            app_id = UNSET
        else:
            app_id = self.app_id

        roles: list[Any] | None | Unset
        if isinstance(self.roles, Unset):
            roles = UNSET
        elif isinstance(self.roles, list):
            roles = self.roles

        else:
            roles = self.roles

        permissions: list[Any] | None | Unset
        if isinstance(self.permissions, Unset):
            permissions = UNSET
        elif isinstance(self.permissions, list):
            permissions = self.permissions

        else:
            permissions = self.permissions

        exp: int | None | Unset
        if isinstance(self.exp, Unset):
            exp = UNSET
        else:
            exp = self.exp

        message: None | str | Unset
        if isinstance(self.message, Unset):
            message = UNSET
        else:
            message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "valid": valid,
            }
        )
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if tenant_id is not UNSET:
            field_dict["tenant_id"] = tenant_id
        if app_id is not UNSET:
            field_dict["app_id"] = app_id
        if roles is not UNSET:
            field_dict["roles"] = roles
        if permissions is not UNSET:
            field_dict["permissions"] = permissions
        if exp is not UNSET:
            field_dict["exp"] = exp
        if message is not UNSET:
            field_dict["message"] = message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        valid = d.pop("valid")

        def _parse_user_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_id = _parse_user_id(d.pop("user_id", UNSET))

        def _parse_tenant_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tenant_id = _parse_tenant_id(d.pop("tenant_id", UNSET))

        def _parse_app_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        app_id = _parse_app_id(d.pop("app_id", UNSET))

        def _parse_roles(data: object) -> list[Any] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                roles_type_0 = cast(list[Any], data)

                return roles_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[Any] | None | Unset, data)

        roles = _parse_roles(d.pop("roles", UNSET))

        def _parse_permissions(data: object) -> list[Any] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                permissions_type_0 = cast(list[Any], data)

                return permissions_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[Any] | None | Unset, data)

        permissions = _parse_permissions(d.pop("permissions", UNSET))

        def _parse_exp(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        exp = _parse_exp(d.pop("exp", UNSET))

        def _parse_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        message = _parse_message(d.pop("message", UNSET))

        verify_token_response = cls(
            valid=valid,
            user_id=user_id,
            tenant_id=tenant_id,
            app_id=app_id,
            roles=roles,
            permissions=permissions,
            exp=exp,
            message=message,
        )

        verify_token_response.additional_properties = d
        return verify_token_response

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
