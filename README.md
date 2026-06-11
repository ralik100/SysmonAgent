# SysmonAgent

## Overview

SysmonAgent is a tool designed for safe Docker container monitoring. The system uses a client-server architecture to separate monitoring logic from host-level resource access.

The monitoring agent runs inside a Docker container and communicates with a server running on the host through a UNIX socket. The host-side server is responsible for collecting container metrics using the Docker SDK, filtering the collected data, and returning only the required information to the monitoring agent.

### Architecture

```text
+----------------------+
| Monitoring Container |
+----------+-----------+
           |
           | UNIX Socket
           |
+----------v-----------+
| Host Server          |
| Docker SDK           |
+----------+-----------+
           |
           | Docker API
           |
+----------v-----------+
| Monitored Containers |
+----------------------+
```

### Advantages

* The monitoring container has no direct access to the Docker daemon.
* The monitoring container does not require access to `/var/run/docker.sock`.
* Container statistics are collected through a dedicated host-side service.
* Communication between components is isolated through a UNIX socket.
* Monitoring logic, data collection, and logging are separated into independent modules.
* New collectors can be added through configuration without modifying the core application logic.

The system currently collects metrics such as CPU usage, memory usage, and network statistics from monitored containers and stores them in a unified JSON event format for further processing and analysis.

---

## Features

* Docker container monitoring
* Client-server architecture
* UNIX socket communication
* Docker SDK integration
* JSON event logging
* Configurable collectors
* Configurable monitoring intervals
* Configurable logging
* Host isolation from monitoring container
* Lightweight deployment using Docker Compose

---

## Requirements

* Windows 11
* WSL2
* Ubuntu (WSL distribution)
* Python 3
* Python virtual environment (venv)
* Docker Desktop

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/ralik100/SysmonAgent.git
cd SysmonAgent
```

### 2. Install WSL and Ubuntu

Run PowerShell as Administrator:

```powershell
wsl --install
```

Install Ubuntu:

```powershell
wsl --install -d Ubuntu
```

Verify installation:

```powershell
wsl -l -v
```

### 3. Enter Ubuntu

```bash
wsl -d Ubuntu -u root
```

### 4. Install Python, pip and venv

```bash
apt update
apt install -y python3 python3-pip python3-venv
```

Verify installation:

```bash
python3 --version
pip3 --version
```

### 5. Create Python Virtual Environment

From the project directory:

```bash
python3 -m venv .venv
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

### 6. Install Docker Desktop

Install Docker Desktop for Windows and enable WSL integration.

Verify Docker access from WSL:

```bash
docker --version
docker compose version
```

---

## Configuration

Application configuration is stored in `config.json`.

Example:

```json
{
  "mode": "loop",
  "intervals": {
    "container_stats": 1
  },
  "collectors": [
    "container_stats"
  ],
  "heartbeat": {
    "enabled": true,
    "interval": 15
  },
  "logger": {
    "batchsize": 10,
    "flush_interval": 2,
    "log_filename": "log.json"
  },
  "warning_threshold": 70,
  "monitored_container_names": [
    "postgres"
  ]
}
```

---

## Running SysmonAgent

### Automatic Startup

The easiest way to start the application is:

```cmd
start.bat
```

### Manual Startup

Start the host-side server:

```bash
source .venv/bin/activate
python3 src/server/main.py
```

In a separate terminal start the monitoring container:

```bash
docker compose up --build
```

---

## Example Event

```json
{
  "container_id": "3d18a539c7d614717c350c39b835ea05efccc851a84004b464593e85b3718634",
  "container_name": "sysmonagent-postgres-1",
  "level": "INFO",
  "event": "get_stats",
  "cpu_percent": 0.54,
  "memory_percent": 0.48,
  "memory_usage_bytes": 40108032,
  "network_rx_bytes": 1424,
  "network_tx_bytes": 126,
  "created_at": 1781124450.7401938,
  "timestamp": "2026-06-10T20:47:30.740497Z"
}
```

---

## Notes

> `start.bat` assumes the default project directory structure.
>
> If the file is moved to another location, paths inside the script may need to be updated accordingly.

> Docker Desktop must be running before starting SysmonAgent.

> WSL integration must be enabled in Docker Desktop settings.

> For further information look into documentation stored in /docs.