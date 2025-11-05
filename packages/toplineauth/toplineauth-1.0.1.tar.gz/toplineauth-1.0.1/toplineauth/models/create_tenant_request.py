from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_tenant_request_settings_type_0 import CreateTenantRequestSettingsType0


T = TypeVar("T", bound="CreateTenantRequest")


@_attrs_define
class CreateTenantRequest:
    """创建租户请求

    Attributes:
        name (str): 租户名称 Example: 示例公司.
        code (str): 租户代码（唯一标识） Example: demo-company.
        description (Union[None, Unset, str]): 租户描述 Example: 这是一个示例租户.
        settings (Union['CreateTenantRequestSettingsType0', None, Unset]): 租户配置（JSON对象） Example: {'language': 'zh-CN',
            'theme': 'light'}.
    """

    name: str
    code: str
    description: Union[None, Unset, str] = UNSET
    settings: Union["CreateTenantRequestSettingsType0", None, Unset] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.create_tenant_request_settings_type_0 import CreateTenantRequestSettingsType0

        name = self.name

        code = self.code

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        settings: Union[Dict[str, Any], None, Unset]
        if isinstance(self.settings, Unset):
            settings = UNSET
        elif isinstance(self.settings, CreateTenantRequestSettingsType0):
            settings = self.settings.to_dict()
        else:
            settings = self.settings

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "code": code,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if settings is not UNSET:
            field_dict["settings"] = settings

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.create_tenant_request_settings_type_0 import CreateTenantRequestSettingsType0

        d = src_dict.copy()
        name = d.pop("name")

        code = d.pop("code")

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_settings(data: object) -> Union["CreateTenantRequestSettingsType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                settings_type_0 = CreateTenantRequestSettingsType0.from_dict(data)

                return settings_type_0
            except:  # noqa: E722
                pass
            return cast(Union["CreateTenantRequestSettingsType0", None, Unset], data)

        settings = _parse_settings(d.pop("settings", UNSET))

        create_tenant_request = cls(
            name=name,
            code=code,
            description=description,
            settings=settings,
        )

        create_tenant_request.additional_properties = d
        return create_tenant_request

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
