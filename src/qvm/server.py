"""
CLI entry to start the FastAPI server.

Usage:
    python -m qvm.server --host 127.0.0.1 --port 8000
"""

import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Start QVM API server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable autoreload (dev only)")
    args = parser.parse_args()

    uvicorn.run("api.app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
