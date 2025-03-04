"""Support for Rituals Perfume Genie numbers."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from pyrituals import Diffuser

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import AREA_SQUARE_METERS, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RitualsDataUpdateCoordinator
from .entity import DiffuserEntity


@dataclass
class RitualsEntityDescriptionMixin:
    """Mixin for required keys."""

    current_fn: Callable[[Diffuser], str]
    select_fn: Callable[[Diffuser, str], Awaitable[None]]


@dataclass
class RitualsSelectEntityDescription(
    SelectEntityDescription, RitualsEntityDescriptionMixin
):
    """Class describing Rituals select entities."""


ENTITY_DESCRIPTIONS = (
    RitualsSelectEntityDescription(
        key="room_size_square_meter",
        name="Room Size",
        icon="mdi:ruler-square",
        unit_of_measurement=AREA_SQUARE_METERS,
        entity_category=EntityCategory.CONFIG,
        options=["15", "30", "60", "100"],
        current_fn=lambda diffuser: str(diffuser.room_size_square_meter),
        select_fn=lambda diffuser, value: (
            diffuser.set_room_size_square_meter(int(value))
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the diffuser select entities."""
    coordinators: dict[str, RitualsDataUpdateCoordinator] = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    async_add_entities(
        RitualsSelectEntity(coordinator, description)
        for coordinator in coordinators.values()
        for description in ENTITY_DESCRIPTIONS
    )


class RitualsSelectEntity(DiffuserEntity, SelectEntity):
    """Representation of a diffuser select entity."""

    entity_description: RitualsSelectEntityDescription

    def __init__(
        self,
        coordinator: RitualsDataUpdateCoordinator,
        description: RitualsSelectEntityDescription,
    ) -> None:
        """Initialize the diffuser room size select entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_entity_registry_enabled_default = (
            self.coordinator.diffuser.has_battery
        )
        self._attr_unique_id = f"{coordinator.diffuser.hublot}-{description.key}"
        self._attr_name = f"{coordinator.diffuser.name} {description.name}"

    @property
    def current_option(self) -> str:
        """Return the selected entity option to represent the entity state."""
        return self.entity_description.current_fn(self.coordinator.diffuser)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.entity_description.select_fn(self.coordinator.diffuser, option)
