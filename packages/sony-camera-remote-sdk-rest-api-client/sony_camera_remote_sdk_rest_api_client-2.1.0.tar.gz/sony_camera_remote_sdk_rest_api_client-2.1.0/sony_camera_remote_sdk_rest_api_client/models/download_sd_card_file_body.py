from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DownloadSDCardFileBody")


@_attrs_define
class DownloadSDCardFileBody:
    """
    Attributes:
        save_path (str | Unset): Directory path to save the file Default: '.'.
    """

    save_path: str | Unset = "."
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        save_path = self.save_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if save_path is not UNSET:
            field_dict["save_path"] = save_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        save_path = d.pop("save_path", UNSET)

        download_sd_card_file_body = cls(
            save_path=save_path,
        )

        download_sd_card_file_body.additional_properties = d
        return download_sd_card_file_body

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
