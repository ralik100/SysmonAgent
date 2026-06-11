# SysmonAgent

# Overview

SysmonAgent is a tool designed for safe Docker container monitoring. The system uses a client-server architecture to separate monitoring logic from host-level resource access.

The monitoring agent runs inside a Docker container and communicates with a server running on the host through a UNIX socket. The host-side server is responsible for collecting container metrics using the Docker SDK, filtering the collected data, and returning only the required information to the monitoring agent.

This architecture provides several advantages:

* The monitoring container has no direct access to the Docker daemon.
* The monitoring container does not require access to `/var/run/docker.sock`.
* Container statistics are collected through a dedicated host-side service.
* Communication between components is isolated through a UNIX socket.
* Monitoring logic, data collection, and logging are separated into independent modules.
* New collectors can be added through configuration without modifying the core application logic.

The system currently collects metrics such as CPU usage, memory usage, and network statistics from monitored containers and stores them in a unified JSON event format for further processing and analysis.


# Requirements

* Windows 11
* WSL2
* Ubuntu (WSL distribution)
* Python 3
* Python virtual environment (venv)
* Docker Desktop

# Installation

## 1. Clone repository

```bash
git clone https://github.com/ralik100/SysmonAgent.git
cd SysmonAgent
```

## 2. Install WSL and Ubuntu

Run PowerShell as Administrator:

```powershell
wsl --install
```

Install Ubuntu distribution:

```powershell
wsl --install -d Ubuntu
```

Verify installation:

```powershell
wsl -l -v
```

## 3. Enter Ubuntu

```powershell
wsl -d Ubuntu -u root
```

## 4. Install Python, pip and venv

```bash
apt update
apt install -y python3 python3-pip python3-venv
```

Verify installation:

```bash
python3 --version
pip3 --version
```

## 5. Create Python virtual environment

From the project directory:

```bash
python3 -m venv .venv
```

Activate virtual environment:

```bash
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## 6. Install Docker Desktop

Install Docker Desktop for Windows and enable WSL integration.

Verify Docker access from WSL:

```bash
docker --version
docker compose version
```

# Running SysmonAgent

Start the application:

```cmd
start.bat
```

Or manually:

```bash
source .venv/bin/activate
python3 src/server/main.py
```

and in another terminal:

```bash
docker compose up --build
```

IMPORTANT:
In order to start.bat work you must not change it's place in filesystem and always run it from file explorer