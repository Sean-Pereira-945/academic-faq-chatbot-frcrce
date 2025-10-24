#!/usr/bin/env bash
# Render start script to launch the Flask app via gunicorn

set -o errexit
set -o pipefail
set -o nounset

exec gunicorn \
  --workers 1 \
  --bind "0.0.0.0:${PORT:-5000}" \
  --timeout 120 \
  --log-level info \
  --access-logfile - \
  --error-logfile - \
  wsgi:app
