"""Smart home service: Home Assistant integration."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class SmartHomeService:
    """Control smart home devices via Home Assistant REST API."""

    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = (base_url or settings.HOME_ASSISTANT_URL or "").rstrip("/")
        self.token = token or settings.HOME_ASSISTANT_TOKEN

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def get_states(self) -> Dict[str, Any]:
        """Get the state of all entities."""
        if not self.base_url or not self.token:
            return {"success": False, "error": "Home Assistant not configured."}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/api/states", headers=self._headers())
                resp.raise_for_status()
                return {"success": True, "states": resp.json()}
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("HA get_states failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def get_entity_state(self, entity_id: str) -> Dict[str, Any]:
        """Get the state of a specific entity."""
        if not self.base_url or not self.token:
            return {"success": False, "error": "Home Assistant not configured."}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/api/states/{entity_id}", headers=self._headers())
                resp.raise_for_status()
                return {"success": True, "entity": resp.json()}
        except Exception as exc:  # pylint: disable=broad-except
            return {"success": False, "error": str(exc)}

    async def call_service(self, domain: str, service: str, entity_id: str, extra: Optional[Dict] = None) -> Dict[str, Any]:
        """Call a Home Assistant service."""
        if not self.base_url or not self.token:
            return {"success": False, "error": "Home Assistant not configured."}
        try:
            payload: Dict[str, Any] = {"entity_id": entity_id}
            if extra:
                payload.update(extra)
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/services/{domain}/{service}",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                return {"success": True, "domain": domain, "service": service, "entity_id": entity_id}
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("HA call_service failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def turn_on(self, entity_id: str) -> Dict[str, Any]:
        """Turn on a device."""
        domain = entity_id.split(".")[0]
        return await self.call_service(domain, "turn_on", entity_id)

    async def turn_off(self, entity_id: str) -> Dict[str, Any]:
        """Turn off a device."""
        domain = entity_id.split(".")[0]
        return await self.call_service(domain, "turn_off", entity_id)

    async def toggle(self, entity_id: str) -> Dict[str, Any]:
        """Toggle a device."""
        domain = entity_id.split(".")[0]
        return await self.call_service(domain, "toggle", entity_id)
