#!/usr/bin/env bash
HOST=${1:-127.0.0.1}
PORT=${2:-8000}
RELOAD=${3:-}

echo "Starting QVM API at http://$HOST:$PORT ..."
python -m src.qvm.server --host "$HOST" --port "$PORT" $RELOAD
