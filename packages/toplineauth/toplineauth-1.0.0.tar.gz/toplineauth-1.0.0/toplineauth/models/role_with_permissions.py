from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.permission_public import PermissionPublic


T = TypeVar("T", bound="RoleWithPermissions")


@_attrs_define
class RoleWithPermissions:
    """带权限的角色信息

    Attributes:
        id (str):
        app_id (str):
        tenant_id (str):
        name (str):
        display_name (str):
        description (None | str):
        is_active (bool):
        permissions (list[PermissionPublic]):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
    """

    id: str
    app_id: str
    tenant_id: str
    name: str
    display_name: str
    description: None | str
    is_active: bool
    permissions: list[PermissionPublic]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        app_id = self.app_id

        tenant_id = self.tenant_id

        name = self.name

        display_name = self.display_name

        description: None | str
        description = self.description

        is_active = self.is_active

        permissions = []
        for permissions_item_data in self.permissions:
            permissions_item = permissions_item_data.to_dict()
            permissions.append(permissions_item)

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "app_id": app_id,
                "tenant_id": tenant_id,
                "name": name,
                "display_name": display_name,
                "description": description,
                "is_active": is_active,
                "permissions": permissions,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.permission_public import PermissionPublic

        d = dict(src_dict)
        id = d.pop("id")

        app_id = d.pop("app_id")

        tenant_id = d.pop("tenant_id")

        name = d.pop("name")

        display_name = d.pop("display_name")

        def _parse_description(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        description = _parse_description(d.pop("description"))

        is_active = d.pop("is_active")

        permissions = []
        _permissions = d.pop("permissions")
        for permissions_item_data in _permissions:
            permissions_item = PermissionPublic.from_dict(permissions_item_data)

            permissions.append(permissions_item)

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        role_with_permissions = cls(
            id=id,
            app_id=app_id,
            tenant_id=tenant_id,
            name=name,
            display_name=display_name,
            description=description,
            is_active=is_active,
            permissions=permissions,
            created_at=created_at,
            updated_at=updated_at,
        )

        role_with_permissions.additional_properties = d
        return role_with_permissions

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
