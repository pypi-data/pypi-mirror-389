from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.camera_info import CameraInfo


T = TypeVar("T", bound="ConnectionResponse")


@_attrs_define
class ConnectionResponse:
    """
    Example:
        {'success': True, 'message': 'Connected to camera in remote-transfer mode', 'camera': {'model': 'ILCE-7M4',
            'id': '00000000000000000000000000000000', 'connectionType': 'USB', 'connected': True}}

    Attributes:
        success (bool | Unset): Operation success status
        message (str | Unset): Human-readable message
        camera (CameraInfo | Unset):
    """

    success: bool | Unset = UNSET
    message: str | Unset = UNSET
    camera: CameraInfo | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        success = self.success

        message = self.message

        camera: dict[str, Any] | Unset = UNSET
        if not isinstance(self.camera, Unset):
            camera = self.camera.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if success is not UNSET:
            field_dict["success"] = success
        if message is not UNSET:
            field_dict["message"] = message
        if camera is not UNSET:
            field_dict["camera"] = camera

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.camera_info import CameraInfo

        d = dict(src_dict)
        success = d.pop("success", UNSET)

        message = d.pop("message", UNSET)

        _camera = d.pop("camera", UNSET)
        camera: CameraInfo | Unset
        if isinstance(_camera, Unset):
            camera = UNSET
        else:
            camera = CameraInfo.from_dict(_camera)

        connection_response = cls(
            success=success,
            message=message,
            camera=camera,
        )

        connection_response.additional_properties = d
        return connection_response

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
