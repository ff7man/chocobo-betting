#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -f webapp/data/winners.zip ]; then
  python3 build_db.py
fi
exec python3 -m http.server 8766 --bind 127.0.0.1 --directory webapp
