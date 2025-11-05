from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SDCardFile")


@_attrs_define
class SDCardFile:
    """
    Example:
        {'content_id': 65536, 'file_id': 1, 'file_path': '/DCIM/100MSDCF/DSC04535.JPG', 'file_size': 15728640,
            'creation_year': 2025, 'creation_month': 9, 'creation_day': 13, 'creation_hour': 14, 'creation_minute': 23,
            'creation_second': 15}

    Attributes:
        content_id (int | Unset): Content ID for download
        file_id (int | Unset): File ID for download
        file_path (str | Unset): Full path on SD card
        file_size (int | Unset): File size in bytes
        creation_year (int | Unset):
        creation_month (int | Unset):
        creation_day (int | Unset):
        creation_hour (int | Unset):
        creation_minute (int | Unset):
        creation_second (int | Unset):
    """

    content_id: int | Unset = UNSET
    file_id: int | Unset = UNSET
    file_path: str | Unset = UNSET
    file_size: int | Unset = UNSET
    creation_year: int | Unset = UNSET
    creation_month: int | Unset = UNSET
    creation_day: int | Unset = UNSET
    creation_hour: int | Unset = UNSET
    creation_minute: int | Unset = UNSET
    creation_second: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        content_id = self.content_id

        file_id = self.file_id

        file_path = self.file_path

        file_size = self.file_size

        creation_year = self.creation_year

        creation_month = self.creation_month

        creation_day = self.creation_day

        creation_hour = self.creation_hour

        creation_minute = self.creation_minute

        creation_second = self.creation_second

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if content_id is not UNSET:
            field_dict["content_id"] = content_id
        if file_id is not UNSET:
            field_dict["file_id"] = file_id
        if file_path is not UNSET:
            field_dict["file_path"] = file_path
        if file_size is not UNSET:
            field_dict["file_size"] = file_size
        if creation_year is not UNSET:
            field_dict["creation_year"] = creation_year
        if creation_month is not UNSET:
            field_dict["creation_month"] = creation_month
        if creation_day is not UNSET:
            field_dict["creation_day"] = creation_day
        if creation_hour is not UNSET:
            field_dict["creation_hour"] = creation_hour
        if creation_minute is not UNSET:
            field_dict["creation_minute"] = creation_minute
        if creation_second is not UNSET:
            field_dict["creation_second"] = creation_second

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        content_id = d.pop("content_id", UNSET)

        file_id = d.pop("file_id", UNSET)

        file_path = d.pop("file_path", UNSET)

        file_size = d.pop("file_size", UNSET)

        creation_year = d.pop("creation_year", UNSET)

        creation_month = d.pop("creation_month", UNSET)

        creation_day = d.pop("creation_day", UNSET)

        creation_hour = d.pop("creation_hour", UNSET)

        creation_minute = d.pop("creation_minute", UNSET)

        creation_second = d.pop("creation_second", UNSET)

        sd_card_file = cls(
            content_id=content_id,
            file_id=file_id,
            file_path=file_path,
            file_size=file_size,
            creation_year=creation_year,
            creation_month=creation_month,
            creation_day=creation_day,
            creation_hour=creation_hour,
            creation_minute=creation_minute,
            creation_second=creation_second,
        )

        sd_card_file.additional_properties = d
        return sd_card_file

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
