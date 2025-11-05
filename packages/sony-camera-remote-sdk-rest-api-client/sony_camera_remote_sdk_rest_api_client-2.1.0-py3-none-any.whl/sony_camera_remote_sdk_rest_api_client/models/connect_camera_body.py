from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.connect_camera_body_mode import ConnectCameraBodyMode
from ..models.connect_camera_body_reconnecting import ConnectCameraBodyReconnecting
from ..types import UNSET, Unset

T = TypeVar("T", bound="ConnectCameraBody")


@_attrs_define
class ConnectCameraBody:
    """
    Attributes:
        mode (ConnectCameraBodyMode | Unset): Connection mode Default: ConnectCameraBodyMode.REMOTE.
        username (str | Unset): Optional username for network cameras
        password (str | Unset): Optional password for network cameras
        reconnecting (ConnectCameraBodyReconnecting | Unset): Enable automatic reconnection during connection loss
            Default: ConnectCameraBodyReconnecting.OFF.
    """

    mode: ConnectCameraBodyMode | Unset = ConnectCameraBodyMode.REMOTE
    username: str | Unset = UNSET
    password: str | Unset = UNSET
    reconnecting: ConnectCameraBodyReconnecting | Unset = ConnectCameraBodyReconnecting.OFF
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mode: str | Unset = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        username = self.username

        password = self.password

        reconnecting: str | Unset = UNSET
        if not isinstance(self.reconnecting, Unset):
            reconnecting = self.reconnecting.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if mode is not UNSET:
            field_dict["mode"] = mode
        if username is not UNSET:
            field_dict["username"] = username
        if password is not UNSET:
            field_dict["password"] = password
        if reconnecting is not UNSET:
            field_dict["reconnecting"] = reconnecting

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _mode = d.pop("mode", UNSET)
        mode: ConnectCameraBodyMode | Unset
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = ConnectCameraBodyMode(_mode)

        username = d.pop("username", UNSET)

        password = d.pop("password", UNSET)

        _reconnecting = d.pop("reconnecting", UNSET)
        reconnecting: ConnectCameraBodyReconnecting | Unset
        if isinstance(_reconnecting, Unset):
            reconnecting = UNSET
        else:
            reconnecting = ConnectCameraBodyReconnecting(_reconnecting)

        connect_camera_body = cls(
            mode=mode,
            username=username,
            password=password,
            reconnecting=reconnecting,
        )

        connect_camera_body.additional_properties = d
        return connect_camera_body

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
