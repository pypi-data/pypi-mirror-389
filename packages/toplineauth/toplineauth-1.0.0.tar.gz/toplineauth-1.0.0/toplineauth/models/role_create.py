from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RoleCreate")


@_attrs_define
class RoleCreate:
    """
    Attributes:
        app_id (UUID): 所属应用ID
        tenant_id (UUID): 所属租户ID
        name (str): 角色名称，如：admin, editor, viewer
        display_name (str): 显示名称，如：管理员、编辑者、查看者
        description (None | str | Unset): 角色描述
        is_active (bool | Unset): 是否激活 Default: True.
    """

    app_id: UUID
    tenant_id: UUID
    name: str
    display_name: str
    description: None | str | Unset = UNSET
    is_active: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        app_id = str(self.app_id)

        tenant_id = str(self.tenant_id)

        name = self.name

        display_name = self.display_name

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        is_active = self.is_active

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "app_id": app_id,
                "tenant_id": tenant_id,
                "name": name,
                "display_name": display_name,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if is_active is not UNSET:
            field_dict["is_active"] = is_active

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        app_id = UUID(d.pop("app_id"))

        tenant_id = UUID(d.pop("tenant_id"))

        name = d.pop("name")

        display_name = d.pop("display_name")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        is_active = d.pop("is_active", UNSET)

        role_create = cls(
            app_id=app_id,
            tenant_id=tenant_id,
            name=name,
            display_name=display_name,
            description=description,
            is_active=is_active,
        )

        role_create.additional_properties = d
        return role_create

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
