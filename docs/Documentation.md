# SysmonAgent Documentation

## Table of Contents

1. Introduction
2. Project Objectives
3. Functional Requirements
4. Non-Functional Requirements
5. System Architecture
6. Component Description
7. Communication Flow
8. Configuration
9. Logging System
10. Monitoring Process
11. Testing
12. Future Improvements
13. Conclusion

---

# 1. Introduction

## 1.1 Project Description

SysmonAgent is a monitoring system designed to safely collect Docker container metrics without exposing the Docker daemon directly to monitoring containers.

The project implements a client-server architecture where the monitoring agent operates inside a Docker container while a host-side server is responsible for interacting with Docker Engine through the Docker SDK.

Communication between both components is performed through a UNIX socket.

## 1.2 Purpose of the Project

The purpose of this project is to provide a secure and extensible solution for collecting container metrics while maintaining isolation between monitoring components and host resources.

---

# 2. Project Objectives

The main objectives of the project are:

* Collect metrics from selected Docker containers.
* Avoid direct exposure of Docker Engine to monitoring containers.
* Provide configurable monitoring intervals.
* Implement a unified event logging mechanism.
* Allow easy addition of new collectors.
* Minimize host resource usage.

---

# 3. Functional Requirements

The system shall:

* Monitor selected Docker containers.
* Collect CPU usage metrics.
* Collect memory usage metrics.
* Collect network usage metrics.
* Store collected events in JSON format.
* Allow configuration through a JSON configuration file.
* Support multiple collectors.
* Support configurable collector execution intervals.

---

# 4. Non-Functional Requirements

The system shall provide:

## Security

* No direct access to Docker daemon from monitoring containers.
* Isolation between monitoring logic and host resources.

## Maintainability

* Modular code structure.
* Separation of responsibilities between components.

## Extensibility

* Ability to add new collectors with minimal code modifications.

## Performance

* Lightweight operation.
* Minimal CPU and memory overhead.

---

# 5. System Architecture

## 5.1 Architecture Overview

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

## 5.2 Architecture Rationale

The chosen architecture separates monitoring functionality from host-level resource access.

Instead of exposing the Docker daemon socket to the monitoring container, a dedicated host-side server is responsible for metric collection.

This approach improves security and follows the principle of least privilege.

---

# 6. Component Description

## 6.1 Monitoring Client

Responsibilities:

* Load application configuration.
* Schedule collectors.
* Send requests to the server.
* Receive collected metrics.
* Generate monitoring events.
* Forward events to the logging subsystem.

### Main Modules

* main.py
* loop.py
* collectors/
* logger.py

---

## 6.2 Host Server

Responsibilities:

* Listen for incoming client connections.
* Receive metric collection requests.
* Communicate with Docker Engine.
* Filter collected metrics.
* Return results to the client.

### Main Modules

* main.py
* server.py

---

## 6.3 Collectors

Collectors are responsible for gathering specific types of metrics.

Current collectors:

* container_stats

Future collectors may include:

* filesystem metrics
* process metrics
* application-specific metrics

---

## 6.4 Logger

Responsibilities:

* Queue events.
* Batch log writes.
* Persist events to storage.
* Provide unified event formatting.

---

# 7. Communication Flow

## 7.1 Request Flow

```text
Client
   |
   | Request
   v
Server
   |
   | Docker SDK
   v
Docker Engine
```

## 7.2 Response Flow

```text
Docker Engine
   |
   | Metrics
   v
Server
   |
   | Filtered Metrics
   v
Client
```

## 7.3 Example Request

```json
{
  "action": "container_stats",
  "container": "postgres"
}
```

## 7.4 Example Response

```json
{
  "container_id": "...",
  "container_name": "postgres",
  "cpu_percent": 0.54,
  "memory_percent": 0.48
}
```

---

# 8. Configuration

System configuration is stored in the `config.json` file.

## Example Configuration

```json
{
  "mode": "loop",
  "intervals": {
    "container_stats": 1
  },
  "collectors": [
    "container_stats"
  ]
}
```

## Configuration Parameters

| Parameter                 | Description                   |
| ------------------------- | ----------------------------- |
| mode                      | Application execution mode    |
| intervals                 | Collector execution intervals |
| collectors                | Enabled collectors            |
| heartbeat                 | Heartbeat settings            |
| logger                    | Logger configuration          |
| monitored_container_names | Containers to monitor         |

## Configuration Parameters

### mode

**Type:** `string`

Determines how the monitoring agent executes collectors.

Possible values:

* `loop` - collectors are executed continuously according to intervals defined in the `intervals` section.
* `once` - each collector is executed exactly one time and the application exits afterwards.

Example:

```json
{
  "mode": "loop"
}
```

---

### intervals

**Type:** `dictionary`

Defines execution intervals (in seconds) for individual collectors.

Each enabled collector should have a corresponding interval.

Example:

```json
{
  "intervals": {
    "container_stats": 1
  }
}
```

---

### collectors

**Type:** `array[string]`

List of enabled collectors.

Available collectors:

#### container_stats

Collects filtered Docker container statistics including:

* CPU utilization
* Memory utilization
* Memory usage in bytes
* Network RX bytes
* Network TX bytes

Example:

```json
{
  "collectors": [
    "container_stats"
  ]
}
```

---

### heartbeat

**Type:** `object`

Controls periodic heartbeat event generation.

Parameters:

| Parameter | Type    | Description                              |
| --------- | ------- | ---------------------------------------- |
| enabled   | boolean | Enables or disables heartbeat generation |
| interval  | integer | Heartbeat interval in seconds            |

Example:

```json
{
  "heartbeat": {
    "enabled": true,
    "interval": 15
  }
}
```

---

### logger

**Type:** `object`

Configures application logging.

Parameters:

| Parameter      | Type    | Description                                |
| -------------- | ------- | ------------------------------------------ |
| batchsize      | integer | Number of events written in a single batch |
| flush_interval | integer | Maximum time between batch writes          |
| log_filename   | string  | Output log file name                       |

Example:

```json
{
  "logger": {
    "batchsize": 10,
    "flush_interval": 2,
    "log_filename": "log.json"
  }
}
```

---

### warning_threshold

**Type:** `integer`

Defines warning threshold percentage for monitored metrics.

Example:

```json
{
  "warning_threshold": 70
}
```

---

### monitored_container_names

**Type:** `array[string]`

List of Docker container names that should be monitored.

Example:

```json
{
  "monitored_container_names": [
    "postgres"
  ]
}
```


---

# 9. Logging System

## Event Structure

```json
{
  "container_id": "...",
  "container_name": "...",
  "level": "INFO",
  "event": "get_stats",
  "cpu_percent": 0.54,
  "memory_percent": 0.48,
  "memory_usage_bytes": 40108032,
  "network_rx_bytes": 1424,
  "network_tx_bytes": 126,
  "timestamp": "2026-06-10T20:47:30.740497Z"
}
```

## Logging Workflow

```text
Collector
    |
    v
Event Queue
    |
    v
Batch Writer
    |
    v
Log File
```

---

# 10. Monitoring Process

The monitoring process follows these steps:

1. Application startup.
2. Configuration loading.
3. Collector scheduling.
4. Request transmission to the server.
5. Metric collection through Docker SDK.
6. Metric filtering.
7. Event creation.
8. Event logging.

---

# 11. Testing

## Tested Scenarios

### Startup Tests

* Server startup.
* Client startup.
* Docker Compose deployment.

### Communication Tests

* UNIX socket connection.
* Request handling.
* Response handling.

### Monitoring Tests

* CPU metric collection.
* Memory metric collection.
* Network metric collection.

### Logging Tests

* Event creation.
* Batch writing.
* Log persistence.

---

# 12. Future Improvements

Potential future improvements include:

* PostgreSQL storage backend.
* Alerting system.
* Multi-host monitoring.
* Historical metrics analysis.
* Web dashboard.
* Multi threading for multiple containers

---

# 13. Conclusion

SysmonAgent demonstrates a secure approach to Docker container monitoring through a client-server architecture and UNIX socket communication.

The project achieves its primary objectives by collecting container metrics while maintaining isolation from Docker Engine and supporting future extensibility.
