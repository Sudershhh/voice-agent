"""Main entry point for the Paradise voice agent."""

import sys
from livekit.agents import cli, WorkerOptions
from agent.basic_agent import entrypoint
from config import config

required_descriptions = {
    "LIVEKIT_URL": "LiveKit WebSocket URL (e.g., wss://your-project.livekit.cloud)",
    "LIVEKIT_API_KEY": "LiveKit API key",
    "LIVEKIT_API_SECRET": "LiveKit API secret",
    "OPENAI_API_KEY": "OpenAI API key (starts with sk-)",
}

missing_vars = config.validate_required()
if missing_vars:
    missing_vars_with_desc = [
        f"  - {var}: {required_descriptions.get(var, 'Required environment variable')}"
        for var in missing_vars
    ]

if missing_vars:
    sys.exit(1)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

