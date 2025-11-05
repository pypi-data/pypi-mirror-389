from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_all_properties_response_200_data import GetAllPropertiesResponse200Data


T = TypeVar("T", bound="GetAllPropertiesResponse200")


@_attrs_define
class GetAllPropertiesResponse200:
    """
    Attributes:
        success (bool | Unset):
        message (str | Unset):
        data (GetAllPropertiesResponse200Data | Unset): Key-value pairs of all camera properties
    """

    success: bool | Unset = UNSET
    message: str | Unset = UNSET
    data: GetAllPropertiesResponse200Data | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        success = self.success

        message = self.message

        data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.data, Unset):
            data = self.data.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if success is not UNSET:
            field_dict["success"] = success
        if message is not UNSET:
            field_dict["message"] = message
        if data is not UNSET:
            field_dict["data"] = data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_all_properties_response_200_data import GetAllPropertiesResponse200Data

        d = dict(src_dict)
        success = d.pop("success", UNSET)

        message = d.pop("message", UNSET)

        _data = d.pop("data", UNSET)
        data: GetAllPropertiesResponse200Data | Unset
        if isinstance(_data, Unset):
            data = UNSET
        else:
            data = GetAllPropertiesResponse200Data.from_dict(_data)

        get_all_properties_response_200 = cls(
            success=success,
            message=message,
            data=data,
        )

        get_all_properties_response_200.additional_properties = d
        return get_all_properties_response_200

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
