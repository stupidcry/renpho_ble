"""Config flow for Xiaomi Bluetooth integration."""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import onboarding
from homeassistant.components.bluetooth import (
    BluetoothServiceInfo,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import DOMAIN
from .RenphoBluetoothDeviceData import RenphoBluetoothDeviceData as DeviceData

_LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass
class Discovery:
    """A discovered bluetooth device."""

    title: str
    discovery_info: BluetoothServiceInfo
    device: DeviceData


def _title(discovery_info: BluetoothServiceInfo, device: DeviceData) -> str:
    return device.title or device.get_device_name() or discovery_info.name


class RenphoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Renpho Bluetooth."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfo | None = None
        self._discovered_device: DeviceData | None = None
        self._discovered_devices: dict[str, Discovery] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfo
    ) -> ConfigFlowResult:
        """Handle the bluetooth discovery step."""
        _LOGGER.warning("*** async_step_bluetooth")
        # 设置的是entry的uniq id,会被setup entry使用
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        device = DeviceData()
        # if not device.supported(discovery_info):
        if "-001" not in discovery_info.name:
            return self.async_abort(reason="not_supported")

        title = _title(discovery_info, device)
        self.context["title_placeholders"] = {"name": title}

        self._discovered_device = device

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        _LOGGER.warning("*** async_step_bluetooth_confirm")
        if user_input is not None or not onboarding.async_is_onboarded(self.hass):
            return self._async_get_or_create_entry()

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=self.context["title_placeholders"],
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step to pick discovered device."""
        _LOGGER.warning("*** async_step_user")
        if user_input is not None:
            _LOGGER.warning("*** User input:%s", user_input)
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            discovery = self._discovered_devices[address]
            _LOGGER.warning("*** discovery:%s", discovery)

            self.context["title_placeholders"] = {"name": discovery.title}

            self._discovered_device = discovery.device

            _LOGGER.warning("*** goto _async_get_or_create_entry")
            return self._async_get_or_create_entry()

        current_addresses = self._async_current_ids()
        for discovery_info in async_discovered_service_info(self.hass, False):
            address = discovery_info.address
            if address in current_addresses or address in self._discovered_devices:
                continue
            device = DeviceData()
            # if device.supported(discovery_info):
            if "-001" in discovery_info.name:
                self._discovered_devices[address] = Discovery(
                    title=_title(discovery_info, device),
                    discovery_info=discovery_info,
                    device=device,
                )
                _LOGGER.warning("Found My Device")
                _LOGGER.warning("=== Discovery address: %s", address)
                _LOGGER.warning("=== Man Data: %s", discovery_info.manufacturer_data)
                _LOGGER.warning("=== advertisement: %s", discovery_info.advertisement)
                _LOGGER.warning("=== device: %s", discovery_info.device)
                _LOGGER.warning("=== service data: %s", discovery_info.service_data)
                _LOGGER.warning("=== service uuids: %s", discovery_info.service_uuids)
                _LOGGER.warning("=== rssi: %s", discovery_info.rssi)
                _LOGGER.warning(
                    "=== advertisement: %s", discovery_info.advertisement.local_name
                )

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        titles = {
            address: discovery.title
            for (address, discovery) in self._discovered_devices.items()
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(titles)}),
        )

    def _async_get_or_create_entry(
        self, bindkey: str | None = None
    ) -> ConfigFlowResult:
        data: dict[str, Any] = {}

        data["hello"] = "world"

        if entry_id := self.context.get("entry_id"):
            _LOGGER.warning("*** _async_get_or_create_entry: %s", entry_id)
            entry = self.hass.config_entries.async_get_entry(entry_id)
            assert entry is not None
            _LOGGER.warning("*** goto async_update_reload_and_abort: %s", entry)
            return self.async_update_reload_and_abort(entry, data=data)

        _LOGGER.warning("*** goto async_create_entry: %s", data)
        return self.async_create_entry(
            title=self.context["title_placeholders"]["name"],
            data=data,
        )
