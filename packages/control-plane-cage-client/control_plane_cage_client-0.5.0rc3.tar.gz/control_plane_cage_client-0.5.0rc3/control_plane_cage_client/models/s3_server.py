from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.s3_server_format import S3ServerFormat
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.s3_server_dv_properties import S3ServerDvProperties


T = TypeVar("T", bound="S3Server")


@_attrs_define
class S3Server:
    """Data can be fetched via S3 protocol

    Attributes:
        type_ (str): Type of the server. Example: s3.
        location (str): S3 URL, starting with s3://
        endpoint_url (str | Unset): The server endpoint for S3-compatible servers, such as MioIO or Google Cloud Storage
        format_ (S3ServerFormat | Unset): Format of files
        delimeter (str | Unset): (Only for format = json), how multiple json documents are delimited within one file
        dv_properties (S3ServerDvProperties | Unset): Properties for Datavillage DCP
    """

    type_: str
    location: str
    endpoint_url: str | Unset = UNSET
    format_: S3ServerFormat | Unset = UNSET
    delimeter: str | Unset = UNSET
    dv_properties: S3ServerDvProperties | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        location = self.location

        endpoint_url = self.endpoint_url

        format_: str | Unset = UNSET
        if not isinstance(self.format_, Unset):
            format_ = self.format_.value

        delimeter = self.delimeter

        dv_properties: dict[str, Any] | Unset = UNSET
        if not isinstance(self.dv_properties, Unset):
            dv_properties = self.dv_properties.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "location": location,
            }
        )
        if endpoint_url is not UNSET:
            field_dict["endpointUrl"] = endpoint_url
        if format_ is not UNSET:
            field_dict["format"] = format_
        if delimeter is not UNSET:
            field_dict["delimeter"] = delimeter
        if dv_properties is not UNSET:
            field_dict["dvProperties"] = dv_properties

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.s3_server_dv_properties import S3ServerDvProperties

        d = dict(src_dict)
        type_ = d.pop("type")

        location = d.pop("location")

        endpoint_url = d.pop("endpointUrl", UNSET)

        _format_ = d.pop("format", UNSET)
        format_: S3ServerFormat | Unset
        if isinstance(_format_, Unset):
            format_ = UNSET
        else:
            format_ = S3ServerFormat(_format_)

        delimeter = d.pop("delimeter", UNSET)

        _dv_properties = d.pop("dvProperties", UNSET)
        dv_properties: S3ServerDvProperties | Unset
        if isinstance(_dv_properties, Unset):
            dv_properties = UNSET
        else:
            dv_properties = S3ServerDvProperties.from_dict(_dv_properties)

        s3_server = cls(
            type_=type_,
            location=location,
            endpoint_url=endpoint_url,
            format_=format_,
            delimeter=delimeter,
            dv_properties=dv_properties,
        )

        s3_server.additional_properties = d
        return s3_server

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
