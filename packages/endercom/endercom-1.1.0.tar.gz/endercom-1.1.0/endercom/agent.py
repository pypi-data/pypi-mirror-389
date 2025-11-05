"""
Endercom Agent for Python

This module provides a simple interface for connecting Python agents
to the Endercom communication platform.
"""

import asyncio
import logging
import signal
import sys
from typing import Callable, Optional
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    raise ImportError(
        "httpx is required. Install it with: pip install httpx"
    )

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Message object received from the Endercom platform."""
    id: str
    content: str
    request_id: str
    created_at: str
    agent_id: Optional[str] = None


@dataclass
class AgentOptions:
    """Configuration options for an Agent."""
    api_key: str
    frequency_id: str
    base_url: str = "https://endercom.io"


@dataclass
class RunOptions:
    """Options for running the agent."""
    poll_interval: float = 2.0  # seconds


MessageHandler = Callable[[Message], Optional[str]]


class Agent:
    """
    Endercom Agent for Python

    This class provides a simple interface for connecting Python agents
    to the Endercom communication platform.
    """

    def __init__(self, options: AgentOptions):
        """
        Initialize a new Agent instance.

        Args:
            options: Agent configuration options
        """
        self.api_key = options.api_key
        self.frequency_id = options.frequency_id
        self.base_url = options.base_url.rstrip('/')
        self.freq_base = f"{self.base_url}/api/{self.frequency_id}"
        self.message_handler: Optional[MessageHandler] = None
        self.running = False
        self._poll_task: Optional[asyncio.Task] = None
        self._client: Optional[httpx.AsyncClient] = None

    def set_message_handler(self, handler: MessageHandler) -> None:
        """
        Set a custom message handler function.

        Args:
            handler: Function that takes a message object and returns a response string
        """
        self.message_handler = handler

    def _default_message_handler(self, message: Message) -> str:
        """
        Default message handler that echoes the received message.

        Args:
            message: The received message

        Returns:
            Response string
        """
        logger.info(f"received: {message.content}")
        return f"Echo: {message.content}"

    async def _poll_messages(self) -> None:
        """Internal method to poll for messages."""
        if not self._client:
            return

        try:
            response = await self._client.get(
                f"{self.freq_base}/messages/poll",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )

            if response.is_success:
                data = response.json()
                if data.get("success") and data.get("data", {}).get("messages"):
                    messages = data["data"]["messages"]
                    for msg_data in messages:
                        message = Message(
                            id=msg_data["id"],
                            content=msg_data["content"],
                            request_id=msg_data["request_id"],
                            created_at=msg_data["created_at"],
                            agent_id=msg_data.get("agent_id")
                        )
                        await self._handle_message(message)
            else:
                logger.error(f"Polling error: {response.status_code}")
        except Exception as error:
            logger.error(f"Network error: {error}", exc_info=True)

    async def _handle_message(self, message: Message) -> None:
        """
        Handle a received message.

        Args:
            message: The message to handle
        """
        try:
            # Use custom handler if set, otherwise use default
            handler = self.message_handler or self._default_message_handler
            response_content = handler(message)

            # If handler returns None, skip sending response
            if response_content is None:
                return

            # Send response
            await self._respond_to_message(message.request_id, response_content)
        except Exception as error:
            logger.error(f"Error handling message: {error}", exc_info=True)

    async def _respond_to_message(self, request_id: str, content: str) -> None:
        """
        Send a response to a message.

        Args:
            request_id: The request ID to respond to
            content: The response content
        """
        if not self._client:
            return

        try:
            payload = {
                "request_id": request_id,
                "content": content
            }

            response = await self._client.post(
                f"{self.freq_base}/messages/respond",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )

            if not response.is_success:
                logger.error(f"Response error: {response.status_code}")
        except Exception as error:
            logger.error(f"Network error sending response: {error}", exc_info=True)

    async def send_message(self, content: str, target_agent: Optional[str] = None) -> bool:
        """
        Send a message to other agents.

        Args:
            content: Message content
            target_agent: Target agent ID (optional)

        Returns:
            True if successful, False otherwise
        """
        # Use existing client if available, otherwise create a temporary one
        if self._client:
            client = self._client
            should_close = False
        else:
            client = httpx.AsyncClient(timeout=30.0)
            should_close = True

        try:
            payload = {"content": content}

            if target_agent:
                payload["target_agent"] = target_agent

            response = await client.post(
                f"{self.freq_base}/messages/send",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )

            return response.is_success
        except Exception as error:
            logger.error(f"Error sending message: {error}", exc_info=True)
            return False
        finally:
            if should_close:
                await client.aclose()

    async def _poll_loop(self, poll_interval: float) -> None:
        """Internal polling loop."""
        while self.running:
            await self._poll_messages()
            await asyncio.sleep(poll_interval)

    def run(self, options: Optional[RunOptions] = None) -> None:
        """
        Start the agent polling loop.

        Args:
            options: Configuration options
        """
        if self.running:
            logger.warning("Agent is already running")
            return

        run_options = options or RunOptions()
        poll_interval = run_options.poll_interval
        self.running = True

        logger.info(f"Agent started, polling every {poll_interval}s")
        logger.info("Press Ctrl+C to stop")

        # Setup signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Create async client and run
        async def main():
            async with httpx.AsyncClient(timeout=30.0) as client:
                self._client = client
                self._poll_task = asyncio.create_task(
                    self._poll_loop(poll_interval)
                )
                try:
                    await self._poll_task
                except asyncio.CancelledError:
                    pass

        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            self.stop()

    async def run_async(self, options: Optional[RunOptions] = None) -> None:
        """
        Start the agent polling loop asynchronously (for use in existing async contexts).

        Args:
            options: Configuration options
        """
        if self.running:
            logger.warning("Agent is already running")
            return

        run_options = options or RunOptions()
        poll_interval = run_options.poll_interval
        self.running = True

        logger.info(f"Agent started, polling every {poll_interval}s")

        async with httpx.AsyncClient(timeout=30.0) as client:
            self._client = client
            self._poll_task = asyncio.create_task(
                self._poll_loop(poll_interval)
            )
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

    def stop(self) -> None:
        """Stop the agent polling loop."""
        if not self.running:
            return

        self.running = False
        if self._poll_task:
            self._poll_task.cancel()

        logger.info("Agent stopped")


def create_agent(options: AgentOptions) -> Agent:
    """
    Create a new Endercom agent.

    Args:
        options: Agent configuration options

    Returns:
        Agent instance
    """
    return Agent(options)

