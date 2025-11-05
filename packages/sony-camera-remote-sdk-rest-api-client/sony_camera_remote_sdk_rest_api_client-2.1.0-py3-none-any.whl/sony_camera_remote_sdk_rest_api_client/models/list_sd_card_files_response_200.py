from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sd_card_file import SDCardFile


T = TypeVar("T", bound="ListSDCardFilesResponse200")


@_attrs_define
class ListSDCardFilesResponse200:
    """
    Attributes:
        success (bool | Unset):
        slot (int | Unset):
        file_count (int | Unset):
        files (list[SDCardFile] | Unset):
    """

    success: bool | Unset = UNSET
    slot: int | Unset = UNSET
    file_count: int | Unset = UNSET
    files: list[SDCardFile] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        success = self.success

        slot = self.slot

        file_count = self.file_count

        files: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.files, Unset):
            files = []
            for files_item_data in self.files:
                files_item = files_item_data.to_dict()
                files.append(files_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if success is not UNSET:
            field_dict["success"] = success
        if slot is not UNSET:
            field_dict["slot"] = slot
        if file_count is not UNSET:
            field_dict["file_count"] = file_count
        if files is not UNSET:
            field_dict["files"] = files

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sd_card_file import SDCardFile

        d = dict(src_dict)
        success = d.pop("success", UNSET)

        slot = d.pop("slot", UNSET)

        file_count = d.pop("file_count", UNSET)

        _files = d.pop("files", UNSET)
        files: list[SDCardFile] | Unset = UNSET
        if _files is not UNSET:
            files = []
            for files_item_data in _files:
                files_item = SDCardFile.from_dict(files_item_data)

                files.append(files_item)

        list_sd_card_files_response_200 = cls(
            success=success,
            slot=slot,
            file_count=file_count,
            files=files,
        )

        list_sd_card_files_response_200.additional_properties = d
        return list_sd_card_files_response_200

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
