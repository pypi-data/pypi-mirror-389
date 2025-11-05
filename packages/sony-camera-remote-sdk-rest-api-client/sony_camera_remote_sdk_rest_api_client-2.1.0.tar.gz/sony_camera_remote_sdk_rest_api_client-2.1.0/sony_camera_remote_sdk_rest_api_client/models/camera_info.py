from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.camera_info_connection_type import CameraInfoConnectionType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CameraInfo")


@_attrs_define
class CameraInfo:
    """
    Attributes:
        model (str | Unset): Camera model name Example: ILCE-7M4.
        id (str | Unset): Unique camera identifier (32-character hex string) Example: 00000000000000000000000000000000.
        connection_type (CameraInfoConnectionType | Unset): Connection type Example: USB.
        connected (bool | Unset): Connection status
    """

    model: str | Unset = UNSET
    id: str | Unset = UNSET
    connection_type: CameraInfoConnectionType | Unset = UNSET
    connected: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        model = self.model

        id = self.id

        connection_type: str | Unset = UNSET
        if not isinstance(self.connection_type, Unset):
            connection_type = self.connection_type.value

        connected = self.connected

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if model is not UNSET:
            field_dict["model"] = model
        if id is not UNSET:
            field_dict["id"] = id
        if connection_type is not UNSET:
            field_dict["connectionType"] = connection_type
        if connected is not UNSET:
            field_dict["connected"] = connected

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        model = d.pop("model", UNSET)

        id = d.pop("id", UNSET)

        _connection_type = d.pop("connectionType", UNSET)
        connection_type: CameraInfoConnectionType | Unset
        if isinstance(_connection_type, Unset):
            connection_type = UNSET
        else:
            connection_type = CameraInfoConnectionType(_connection_type)

        connected = d.pop("connected", UNSET)

        camera_info = cls(
            model=model,
            id=id,
            connection_type=connection_type,
            connected=connected,
        )

        camera_info.additional_properties = d
        return camera_info

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
