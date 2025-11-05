import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.tenant_response_settings_type_0 import TenantResponseSettingsType0


T = TypeVar("T", bound="TenantResponse")


@_attrs_define
class TenantResponse:
    """租户响应

    Attributes:
        id (str): 租户ID（UUID）
        name (str): 租户名称
        code (str): 租户代码
        is_active (bool): 是否激活
        created_at (datetime.datetime): 创建时间
        updated_at (datetime.datetime): 更新时间
        description (Union[None, Unset, str]): 租户描述
        settings (Union['TenantResponseSettingsType0', None, Unset]): 租户配置
        deleted_at (Union[None, Unset, datetime.datetime]): 删除时间（逻辑删除）
    """

    id: str
    name: str
    code: str
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    description: Union[None, Unset, str] = UNSET
    settings: Union["TenantResponseSettingsType0", None, Unset] = UNSET
    deleted_at: Union[None, Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.tenant_response_settings_type_0 import TenantResponseSettingsType0

        id = self.id

        name = self.name

        code = self.code

        is_active = self.is_active

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        settings: Union[Dict[str, Any], None, Unset]
        if isinstance(self.settings, Unset):
            settings = UNSET
        elif isinstance(self.settings, TenantResponseSettingsType0):
            settings = self.settings.to_dict()
        else:
            settings = self.settings

        deleted_at: Union[None, Unset, str]
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "code": code,
                "is_active": is_active,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if settings is not UNSET:
            field_dict["settings"] = settings
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.tenant_response_settings_type_0 import TenantResponseSettingsType0

        d = src_dict.copy()
        id = d.pop("id")

        name = d.pop("name")

        code = d.pop("code")

        is_active = d.pop("is_active")

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_settings(data: object) -> Union["TenantResponseSettingsType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                settings_type_0 = TenantResponseSettingsType0.from_dict(data)

                return settings_type_0
            except:  # noqa: E722
                pass
            return cast(Union["TenantResponseSettingsType0", None, Unset], data)

        settings = _parse_settings(d.pop("settings", UNSET))

        def _parse_deleted_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        tenant_response = cls(
            id=id,
            name=name,
            code=code,
            is_active=is_active,
            created_at=created_at,
            updated_at=updated_at,
            description=description,
            settings=settings,
            deleted_at=deleted_at,
        )

        tenant_response.additional_properties = d
        return tenant_response

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
