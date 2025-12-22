"""Main entry point for the Paradise voice agent."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import cli, WorkerOptions
from agent.basic_agent import entrypoint

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Check for required environment variables
required_vars = {
    "LIVEKIT_URL": "LiveKit WebSocket URL (e.g., wss://your-project.livekit.cloud)",
    "LIVEKIT_API_KEY": "LiveKit API key",
    "LIVEKIT_API_SECRET": "LiveKit API secret",
    "OPENAI_API_KEY": "OpenAI API key (starts with sk-)",
}

missing_vars = []
for var, description in required_vars.items():
    if not os.getenv(var):
        missing_vars.append(f"  - {var}: {description}")

if missing_vars:
    print("❌ Error: Missing required environment variables!", file=sys.stderr)
    print("\nPlease create a .env file in the backend directory with the following variables:\n", file=sys.stderr)
    print("\n".join(missing_vars), file=sys.stderr)
    print("\n💡 Tip: Copy env.example to .env and fill in your values:", file=sys.stderr)
    print("   Windows: copy env.example .env", file=sys.stderr)
    print("   Linux/Mac: cp env.example .env", file=sys.stderr)
    print("\n📖 See QUICK_START.md for detailed setup instructions.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    # Create WorkerOptions with entrypoint function
    # The entrypoint function will be called when agent joins a room
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

