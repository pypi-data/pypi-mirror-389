"""
Node management for decentralized AI training.
Handles node registration, heartbeat, and communication with the network.
"""

import asyncio
import json
import logging
import platform
import psutil
import socket
import time
from datetime import datetime
from typing import Dict, Optional, Any
import aiohttp

logger = logging.getLogger(__name__)


class Node:
    """
    Represents a training node in the Ailoos decentralized network.

    This class handles:
    - Node registration with the network
    - Heartbeat monitoring
    - Hardware detection and reporting
    - Training session management
    - Communication with coordinator nodes

    Example:
        node = Node(node_id="my_training_node")
        await node.start()
        await node.join_training_session("session_123")
    """

    def __init__(
        self,
        node_id: str,
        coordinator_url: str = "http://localhost:5000",
        heartbeat_interval: int = 30,
        hardware_info: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a training node.

        Args:
            node_id: Unique identifier for this node
            coordinator_url: URL of the coordinator API server
            heartbeat_interval: Seconds between heartbeat messages
            hardware_info: Optional hardware information override
        """
        self.node_id = node_id
        self.coordinator_url = coordinator_url
        self.heartbeat_interval = heartbeat_interval
        self.hardware_info = hardware_info or self._detect_hardware()
        self.is_running = False
        self.session = None
        self._heartbeat_task: Optional[asyncio.Task] = None

    def _detect_hardware(self) -> Dict[str, Any]:
        """Automatically detect hardware capabilities."""
        try:
            # CPU info
            cpu_count = psutil.cpu_count(logical=True)
            cpu_physical = psutil.cpu_count(logical=False)

            # Memory info
            memory = psutil.virtual_memory()
            memory_gb = round(memory.total / (1024**3), 1)

            # GPU detection (simplified - would need torch/cuda detection in real impl)
            gpu_info = "Unknown"
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_info = torch.cuda.get_device_name(0)
                else:
                    gpu_info = "CPU Only"
            except ImportError:
                gpu_info = "PyTorch not available"

            return {
                "cpu_cores": cpu_count,
                "cpu_physical": cpu_physical,
                "memory_gb": memory_gb,
                "gpu": gpu_info,
                "platform": platform.system(),
                "architecture": platform.machine()
            }
        except Exception as e:
            logger.warning(f"Hardware detection failed: {e}")
            return {"error": "Hardware detection failed"}

    async def start(self) -> bool:
        """
        Start the node and register with the network.

        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Register with coordinator
            async with aiohttp.ClientSession() as session:
                payload = {
                    "node_id": self.node_id,
                    "ip_address": self._get_local_ip(),
                    "hardware_info": self.hardware_info,
                    "location": "Unknown"  # Could be detected via IP geolocation
                }

                async with session.post(
                    f"{self.coordinator_url}/api/node/register",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Node {self.node_id} registered successfully")
                        self.is_running = True

                        # Start heartbeat
                        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Registration failed: {error}")
                        return False

        except Exception as e:
            logger.error(f"Failed to start node: {e}")
            return False

    async def stop(self):
        """Stop the node and cleanup resources."""
        self.is_running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        logger.info(f"Node {self.node_id} stopped")

    async def _heartbeat_loop(self):
        """Send periodic heartbeat to coordinator."""
        while self.is_running:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.coordinator_url}/api/node/heartbeat",
                        json={"node_id": self.node_id}
                    ) as response:
                        if response.status != 200:
                            logger.warning(f"Heartbeat failed: {response.status}")
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

            await asyncio.sleep(self.heartbeat_interval)

    async def join_training_session(self, session_id: str) -> bool:
        """
        Join a federated training session.

        Args:
            session_id: ID of the training session to join

        Returns:
            True if joined successfully
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "node_id": self.node_id,
                    "session_id": session_id,
                    "model_version": "1.0.0"
                }

                async with session.post(
                    f"{self.coordinator_url}/api/training/start",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.session = session_id
                        logger.info(f"Joined training session {session_id}")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Failed to join session: {error}")
                        return False

        except Exception as e:
            logger.error(f"Error joining session: {e}")
            return False

    async def update_training_progress(
        self,
        parameters_trained: int,
        accuracy: float,
        loss: float,
        status: str = "running"
    ):
        """
        Update training progress for current session.

        Args:
            parameters_trained: Number of parameters trained
            accuracy: Current accuracy
            loss: Current loss
            status: Training status
        """
        if not self.session:
            logger.warning("No active training session")
            return

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "session_id": self.session,
                    "parameters_trained": parameters_trained,
                    "accuracy": accuracy,
                    "loss": loss,
                    "status": status
                }

                async with session.post(
                    f"{self.coordinator_url}/api/training/update",
                    json=payload
                ) as response:
                    if response.status == 200:
                        logger.debug(f"Progress updated for session {self.session}")
                    else:
                        logger.warning(f"Progress update failed: {response.status}")

        except Exception as e:
            logger.error(f"Error updating progress: {e}")

    def _get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            # Create a socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    async def get_network_stats(self) -> Optional[Dict[str, Any]]:
        """Get current network statistics."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.coordinator_url}/api/stats") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error(f"Error getting network stats: {e}")
        return None

    @property
    def status(self) -> Dict[str, Any]:
        """Get current node status."""
        return {
            "node_id": self.node_id,
            "is_running": self.is_running,
            "session": self.session,
            "hardware": self.hardware_info,
            "coordinator": self.coordinator_url,
            "last_update": datetime.now().isoformat()
        }