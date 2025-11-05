from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="PermissionPublic")


@_attrs_define
class PermissionPublic:
    """
    Attributes:
        resource (str): 资源名称，如：user, order, report
        action (str): 操作名称，如：create, read, update, delete
        name (str): 完整权限名，格式：resource:action
        id (UUID):
        created_at (datetime.datetime):
        description (None | str | Unset): 权限描述
    """

    resource: str
    action: str
    name: str
    id: UUID
    created_at: datetime.datetime
    description: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        resource = self.resource

        action = self.action

        name = self.name

        id = str(self.id)

        created_at = self.created_at.isoformat()

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "resource": resource,
                "action": action,
                "name": name,
                "id": id,
                "created_at": created_at,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        resource = d.pop("resource")

        action = d.pop("action")

        name = d.pop("name")

        id = UUID(d.pop("id"))

        created_at = isoparse(d.pop("created_at"))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        permission_public = cls(
            resource=resource,
            action=action,
            name=name,
            id=id,
            created_at=created_at,
            description=description,
        )

        permission_public.additional_properties = d
        return permission_public

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
