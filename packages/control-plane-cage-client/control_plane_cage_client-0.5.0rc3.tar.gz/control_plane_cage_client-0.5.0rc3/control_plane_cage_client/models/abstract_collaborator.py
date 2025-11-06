from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.abstract_collaborator_configuration import AbstractCollaboratorConfiguration


T = TypeVar("T", bound="AbstractCollaborator")


@_attrs_define
class AbstractCollaborator:
    """Abstract Collaborator

    Attributes:
        name (str | Unset): A name given the collaborator. This value is intended to be read by humans. Example: My
            Collaborator.
        label (str | Unset): A label given the collaborator. This value is intended to refered to in code. Example: my-
            collaborator.
        role (str | Unset):
        configuration (AbstractCollaboratorConfiguration | Unset): A configuration of the collaborator. This is an
            object representing key-value pairs that will be available in the cage as environment variables.
    """

    name: str | Unset = UNSET
    label: str | Unset = UNSET
    role: str | Unset = UNSET
    configuration: AbstractCollaboratorConfiguration | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        label = self.label

        role = self.role

        configuration: dict[str, Any] | Unset = UNSET
        if not isinstance(self.configuration, Unset):
            configuration = self.configuration.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if label is not UNSET:
            field_dict["label"] = label
        if role is not UNSET:
            field_dict["role"] = role
        if configuration is not UNSET:
            field_dict["configuration"] = configuration

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.abstract_collaborator_configuration import AbstractCollaboratorConfiguration

        d = dict(src_dict)
        name = d.pop("name", UNSET)

        label = d.pop("label", UNSET)

        role = d.pop("role", UNSET)

        _configuration = d.pop("configuration", UNSET)
        configuration: AbstractCollaboratorConfiguration | Unset
        if isinstance(_configuration, Unset):
            configuration = UNSET
        else:
            configuration = AbstractCollaboratorConfiguration.from_dict(_configuration)

        abstract_collaborator = cls(
            name=name,
            label=label,
            role=role,
            configuration=configuration,
        )

        abstract_collaborator.additional_properties = d
        return abstract_collaborator

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
