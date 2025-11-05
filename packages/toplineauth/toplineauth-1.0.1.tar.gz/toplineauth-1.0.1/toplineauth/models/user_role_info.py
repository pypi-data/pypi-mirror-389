import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.role_public import RolePublic


T = TypeVar("T", bound="UserRoleInfo")


@_attrs_define
class UserRoleInfo:
    """用户角色信息

    Attributes:
        id (str):
        user_id (str):
        role (RolePublic):
        app_id (str):
        tenant_id (str):
        created_at (datetime.datetime):
        expires_at (Union[None, datetime.datetime]):
    """

    id: str
    user_id: str
    role: "RolePublic"
    app_id: str
    tenant_id: str
    created_at: datetime.datetime
    expires_at: Union[None, datetime.datetime]
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id

        user_id = self.user_id

        role = self.role.to_dict()

        app_id = self.app_id

        tenant_id = self.tenant_id

        created_at = self.created_at.isoformat()

        expires_at: Union[None, str]
        if isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "user_id": user_id,
                "role": role,
                "app_id": app_id,
                "tenant_id": tenant_id,
                "created_at": created_at,
                "expires_at": expires_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.role_public import RolePublic

        d = src_dict.copy()
        id = d.pop("id")

        user_id = d.pop("user_id")

        role = RolePublic.from_dict(d.pop("role"))

        app_id = d.pop("app_id")

        tenant_id = d.pop("tenant_id")

        created_at = isoparse(d.pop("created_at"))

        def _parse_expires_at(data: object) -> Union[None, datetime.datetime]:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_at_type_0 = isoparse(data)

                return expires_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, datetime.datetime], data)

        expires_at = _parse_expires_at(d.pop("expires_at"))

        user_role_info = cls(
            id=id,
            user_id=user_id,
            role=role,
            app_id=app_id,
            tenant_id=tenant_id,
            created_at=created_at,
            expires_at=expires_at,
        )

        user_role_info.additional_properties = d
        return user_role_info

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
