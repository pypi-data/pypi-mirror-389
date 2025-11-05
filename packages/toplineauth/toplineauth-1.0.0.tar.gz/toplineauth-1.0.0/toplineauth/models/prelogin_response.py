from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.candidate_tenant import CandidateTenant


T = TypeVar("T", bound="PreloginResponse")


@_attrs_define
class PreloginResponse:
    """预登录响应：返回候选租户列表，供用户选择

    Attributes:
        needs_selection (bool):
        candidates (list[CandidateTenant]):
    """

    needs_selection: bool
    candidates: list[CandidateTenant]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        needs_selection = self.needs_selection

        candidates = []
        for candidates_item_data in self.candidates:
            candidates_item = candidates_item_data.to_dict()
            candidates.append(candidates_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "needs_selection": needs_selection,
                "candidates": candidates,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.candidate_tenant import CandidateTenant

        d = dict(src_dict)
        needs_selection = d.pop("needs_selection")

        candidates = []
        _candidates = d.pop("candidates")
        for candidates_item_data in _candidates:
            candidates_item = CandidateTenant.from_dict(candidates_item_data)

            candidates.append(candidates_item)

        prelogin_response = cls(
            needs_selection=needs_selection,
            candidates=candidates,
        )

        prelogin_response.additional_properties = d
        return prelogin_response

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
