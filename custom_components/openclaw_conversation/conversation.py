"""Conversation support for OpenClaw."""
from __future__ import annotations

import logging
from typing import Literal

import aiohttp
import voluptuous as vol

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, intent
from homeassistant.util import ulid as ulid_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_GENERATE_RESPONSE = "generate_response"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenClaw conversation from config entry."""
    try:
        agent = OpenClawConversationAgent(hass, entry)
        conversation.async_set_agent(hass, entry, agent)
        
        _LOGGER.info(
            "OpenClaw Conversation Agent registered successfully. "
            "Entry ID: %s, Agent ID: %s",
            entry.entry_id,
            conversation.async_get_agent_info(hass, entry)
        )
        return True
    except Exception as err:
        _LOGGER.error("Failed to set up OpenClaw Conversation Agent: %s", err, exc_info=True)
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload OpenClaw conversation."""
    conversation.async_unset_agent(hass, entry)
    return True


class OpenClawConversationAgent(conversation.AbstractConversationAgent):
    """OpenClaw Conversation Agent (Kaspar as AI Assistant)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self._manager_url = entry.data["manager_url"].rstrip("/")
        self._device_token = entry.data["device_token"]
        self._session_id: str | None = None
        
        _LOGGER.debug(
            "OpenClawConversationAgent initialized with manager_url=%s",
            self._manager_url
        )

    @property
    def attribution(self) -> dict | None:
        """Return attribution information."""
        return {
            "name": "OpenClaw (Kaspar)",
            "url": "https://github.com/eulennest/ha-openclaw-conversation",
        }

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return list of supported languages."""
        return "*"  # Support all languages (Kaspar can handle any)

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process user input and return Kaspar's response."""
        
        _LOGGER.debug(f"OpenClaw Conversation: Processing '{user_input.text}'")
        
        try:
            # Create session if needed (creates on Manager side)
            if not self._session_id:
                self._session_id = await self._create_session()
            
            # Send message to Kaspar via OpenClaw Manager
            # Manager handles Gateway WebSocket communication
            response_text = await self._send_message(user_input.text)
            
            # Create conversation result
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_speech(response_text)
            
            return conversation.ConversationResult(
                response=intent_response,
                conversation_id=self._session_id
            )
            
        except Exception as err:
            _LOGGER.error(f"Error processing conversation: {err}", exc_info=True)
            
            # Return error response
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_speech(
                "Entschuldigung, ich konnte die Anfrage nicht verarbeiten."
            )
            
            return conversation.ConversationResult(
                response=intent_response,
                conversation_id=self._session_id or ulid_util.ulid()
            )

    async def _create_session(self) -> str:
        """Create a new voice session with OpenClaw Manager (Device authenticates with token)."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self._manager_url}/api/v1/voice/sessions",
                headers={"Authorization": f"Bearer {self._device_token}"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to create session: HTTP {response.status} - {error_text}")
                
                data = await response.json()
                session_id = data["sessionId"]
                
                _LOGGER.info(f"Created OpenClaw voice session: {session_id}")
                return session_id

    async def _send_message(self, text: str) -> str:
        """Send message to Kaspar via Manager and wait for response."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self._manager_url}/api/v1/voice/sessions/{self._session_id}/message",
                headers={"Authorization": f"Bearer {self._device_token}"},
                json={"text": text},
                timeout=aiohttp.ClientTimeout(total=35)  # Manager waits up to 30s for Kaspar
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to send message: HTTP {response.status} - {error_text}")
                
                data = await response.json()
                response_text = data.get("assistantText")
                
                if not response_text:
                    raise Exception("Manager returned empty response")
                
                _LOGGER.debug(f"Kaspar response: {response_text[:100]}...")
                return response_text
