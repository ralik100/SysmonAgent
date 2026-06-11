@echo off

start wsl -d Ubuntu -u root bash -c "cd /tmp && mkdir -p socket"

start wsl -d Ubuntu -u root bash -c "sleep 3 && source .venv/bin/activate && python3 src/server/main.py"

start wsl -d Ubuntu -u root bash -c "sleep 3 && docker compose up --build"