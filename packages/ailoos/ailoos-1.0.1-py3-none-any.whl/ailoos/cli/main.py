#!/usr/bin/env python3
"""
Ailoos CLI - Command Line Interface for Decentralized AI Training
================================================================

Usage:
    ailoos node start [--id=NODE_ID] [--coordinator=URL]
    ailoos node stop
    ailoos node status
    ailoos train start [--model=MODEL] [--rounds=ROUNDS]
    ailoos train status
    ailoos train stop
    ailoos models list
    ailoos models download MODEL_NAME
    ailoos hardware info
    ailoos setup [--auto]
    ailoos --help
    ailoos --version

Examples:
    # Quick start a training node
    ailoos node start

    # Start federated training
    ailoos train start --model=empoorio-lm --rounds=10

    # Check hardware capabilities
    ailoos hardware info

    # Auto-setup for new developers
    ailoos setup --auto
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
import argparse

from ..core.node import Node
from ..core.model_manager import ModelManager
from ..federated.trainer import FederatedTrainer
from ..utils.logging import setup_logging
from ..utils.hardware import get_hardware_info, print_hardware_summary


class AiloosCLI:
    """Main CLI class for Ailoos commands."""

    def __init__(self):
        self.logger = setup_logging()
        self.node: Optional[Node] = None
        self.trainer: Optional[FederatedTrainer] = None
        self.model_manager = ModelManager()

    async def run_command(self, args):
        """Run the appropriate command based on arguments."""
        command = args.command

        if command == "node":
            await self._handle_node_command(args)
        elif command == "train":
            await self._handle_train_command(args)
        elif command == "models":
            await self._handle_models_command(args)
        elif command == "hardware":
            self._handle_hardware_command(args)
        elif command == "setup":
            await self._handle_setup_command(args)
        else:
            self._print_help()

    async def _handle_node_command(self, args):
        """Handle node-related commands."""
        subcommand = args.subcommand

        if subcommand == "start":
            node_id = args.id or f"cli_node_{hash(str(args)) % 10000}"
            coordinator = args.coordinator or "http://localhost:5000"

            print(f"🚀 Starting Ailoos node '{node_id}'...")
            print(f"📡 Coordinator: {coordinator}")

            self.node = Node(node_id=node_id, coordinator_url=coordinator)

            try:
                success = await self.node.start()
                if success:
                    print("✅ Node started successfully!")
                    print(f"🆔 Node ID: {node_id}")
                    print(f"🌐 Status: Active")
                    print("\n💡 Use 'ailoos node status' to check status")
                    print("💡 Use 'ailoos train start' to begin training")
                else:
                    print("❌ Failed to start node")
                    sys.exit(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping node...")
                if self.node:
                    await self.node.stop()
                sys.exit(0)

        elif subcommand == "stop":
            if self.node:
                print("🛑 Stopping node...")
                await self.node.stop()
                print("✅ Node stopped")
            else:
                print("❌ No active node to stop")

        elif subcommand == "status":
            if self.node:
                status = self.node.status
                print("📊 Node Status:")
                print(f"  🆔 ID: {status['node_id']}")
                print(f"  🟢 Running: {status['is_running']}")
                print(f"  🖥️  Hardware: {status['hardware']['cpu_cores']} CPU cores, {status['hardware']['memory_gb']}GB RAM")
                if status['hardware']['gpu'] != 'CPU Only':
                    print(f"  🎮 GPU: {status['hardware']['gpu']}")
                print(f"  📡 Coordinator: {status['coordinator']}")
                print(f"  🕒 Last Update: {status['last_update']}")
            else:
                print("❌ No active node. Use 'ailoos node start' first.")

    async def _handle_train_command(self, args):
        """Handle training-related commands."""
        subcommand = args.subcommand

        if subcommand == "start":
            if not self.node:
                print("❌ No active node. Start a node first with 'ailoos node start'")
                sys.exit(1)

            model = args.model or "empoorio-lm"
            rounds = args.rounds or 5

            print(f"🎯 Starting federated training...")
            print(f"🤖 Model: {model}")
            print(f"🔄 Rounds: {rounds}")

            self.trainer = FederatedTrainer(
                model_name=model,
                rounds=rounds,
                node_id=self.node.node_id
            )

            try:
                results = await self.trainer.train()
                print("\n🎉 Training completed!")
                print(f"📊 Average Accuracy: {results['average_accuracy']:.2f}%")
                print(f"📉 Average Loss: {results['average_loss']:.4f}")
                print(f"📈 Total Samples: {results['total_samples']}")
                print(f"⏱️  Total Time: {results['total_training_time']:.2f}s")

            except KeyboardInterrupt:
                print("\n🛑 Training interrupted")
                if self.trainer:
                    await self.trainer.stop()
                sys.exit(0)
            except Exception as e:
                print(f"❌ Training failed: {e}")
                sys.exit(1)

        elif subcommand == "status":
            if self.trainer:
                status = await self.trainer.get_training_status()
                print("📊 Training Status:")
                print(f"  🎯 Current Round: {status['current_round']}/{status['total_rounds']}")
                print(f"  🚀 Is Training: {status['is_training']}")
                print(f"  🤖 Model: {status['model_name']}")
                print(f"  🆔 Node: {status['node_id']}")
            else:
                print("❌ No active training session")

        elif subcommand == "stop":
            if self.trainer:
                print("🛑 Stopping training...")
                await self.trainer.stop()
                print("✅ Training stopped")
            else:
                print("❌ No active training to stop")

    async def _handle_models_command(self, args):
        """Handle model-related commands."""
        subcommand = args.subcommand

        if subcommand == "list":
            print("📚 Available Models:")
            models = await self.model_manager.list_available_models()
            if models:
                for model in models:
                    print(f"  • {model.get('name', 'Unknown')} (v{model.get('version', 'latest')})")
            else:
                print("  No models available or coordinator not reachable")
                print("  💡 Make sure the coordinator API is running")

        elif subcommand == "download":
            model_name = args.model_name
            print(f"📥 Downloading model: {model_name}")
            success = await self.model_manager.load_model(model_name)
            if success:
                print("✅ Model downloaded successfully")
            else:
                print("❌ Failed to download model")
    def _handle_hardware_command(self, args):
        """Handle hardware-related commands."""
        subcommand = args.subcommand

        if subcommand == "info":
            print_hardware_summary()

    async def _handle_setup_command(self, args):
        """Handle setup-related commands."""
        if args.auto:
            print("🔧 Starting auto-setup for Ailoos...")
            print("📦 This will install dependencies and configure your environment")

            # Check hardware
            print("\n1️⃣ Checking hardware capabilities...")
            hardware = get_hardware_info()
            if hardware['detection_status'] == 'success':
                print("✅ Hardware detection successful")
                print(f"   CPU: {hardware['cpu']['logical_cores']} cores")
                print(f"   RAM: {hardware['memory']['total_gb']} GB")
            else:
                print("⚠️  Hardware detection limited")

            # Check Python environment
            print("\n2️⃣ Checking Python environment...")
            import torch
            print(f"✅ PyTorch available: {torch.__version__}")
            print(f"   CUDA available: {torch.cuda.is_available()}")

            # Create necessary directories
            print("\n3️⃣ Creating project directories...")
            dirs = ["models", "logs", "checkpoints"]
            for dir_name in dirs:
                Path(dir_name).mkdir(exist_ok=True)
                print(f"   📁 Created {dir_name}/")

            print("\n🎉 Auto-setup completed!")
            print("\n🚀 Next steps:")
            print("   1. Start a node: ailoos node start")
            print("   2. Begin training: ailoos train start")
            print("   3. Check status: ailoos node status")

        else:
            print("🔧 Ailoos Setup Options:")
            print("  --auto    : Automatic setup with hardware detection")
            print("  --manual  : Interactive setup (not implemented yet)")

    def _print_help(self):
        """Print help information."""
        print(__doc__)


def create_parser():
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="ailoos",
        description="Ailoos CLI - Decentralized AI Training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ailoos node start                    # Start a training node
  ailoos train start --rounds=10       # Start federated training
  ailoos hardware info                 # Check hardware capabilities
  ailoos setup --auto                  # Auto-setup environment
        """
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version="Ailoos CLI v1.0.0"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Node commands
    node_parser = subparsers.add_parser("node", help="Node management")
    node_subparsers = node_parser.add_subparsers(dest="subcommand")

    node_start = node_subparsers.add_parser("start", help="Start a training node")
    node_start.add_argument("--id", help="Node ID (auto-generated if not provided)")
    node_start.add_argument("--coordinator", default="http://localhost:5000",
                           help="Coordinator API URL")

    node_subparsers.add_parser("stop", help="Stop the active node")
    node_subparsers.add_parser("status", help="Show node status")

    # Training commands
    train_parser = subparsers.add_parser("train", help="Training management")
    train_subparsers = train_parser.add_subparsers(dest="subcommand")

    train_start = train_subparsers.add_parser("start", help="Start federated training")
    train_start.add_argument("--model", default="empoorio-lm", help="Model to train")
    train_start.add_argument("--rounds", type=int, default=5, help="Number of rounds")

    train_subparsers.add_parser("status", help="Show training status")
    train_subparsers.add_parser("stop", help="Stop training")

    # Model commands
    models_parser = subparsers.add_parser("models", help="Model management")
    models_subparsers = models_parser.add_subparsers(dest="subcommand")

    models_subparsers.add_parser("list", help="List available models")
    models_download = models_subparsers.add_parser("download", help="Download a model")
    models_download.add_argument("model_name", help="Name of model to download")

    # Hardware commands
    hardware_parser = subparsers.add_parser("hardware", help="Hardware information")
    hardware_subparsers = hardware_parser.add_subparsers(dest="subcommand")
    hardware_subparsers.add_parser("info", help="Show hardware information")

    # Setup commands
    setup_parser = subparsers.add_parser("setup", help="Environment setup")
    setup_parser.add_argument("--auto", action="store_true",
                             help="Automatic setup with hardware detection")

    return parser


async def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = AiloosCLI()
    try:
        await cli.run_command(args)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())