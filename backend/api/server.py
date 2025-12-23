"""Run the PDF upload API server."""

import sys
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).parent.parent
env_path = backend_dir / ".env"
load_dotenv(env_path)

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import uvicorn
from api.upload import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

