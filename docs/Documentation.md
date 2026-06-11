# SysmonAgent Documentation

## Table of Contents

1. Introduction
2. Project Objectives
3. Functional Requirements
4. Non-Functional Requirements
5. System Architecture
6. Deployment Architecture
7. Component Description
8. Communication Flow
9. Configuration
10. Logging System
11. Error Handling
12. Monitoring Process
13. Testing
14. Known Limitations
15. Future Improvements
16. Conclusion

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

## 5.3 Data Flow

The following diagram presents the complete lifecycle of monitoring data inside the system.

Monitored Container
         |
         | Docker Statistics
         v
Docker Engine
         |
         | Docker SDK
         v
Host Server
         |
         | Filtered Metrics
         v
UNIX Socket
         |
         v
Monitoring Client
         |
         | Monitoring Event
         v
Logger Queue
         |
         v
Batch Writer
         |
         v
JSON Log File

The monitoring client never communicates directly with Docker Engine. All communication is performed through the host-side server, which acts as a controlled access layer between monitoring components and host resources.

---

# 6. Deployment Architecture

## 6.1 Deployment Model

SysmonAgent is deployed using a hybrid architecture consisting of:

* a host-side monitoring server,
* a containerized monitoring client,
* monitored Docker containers.

The monitoring client runs inside a Docker container and communicates with the host-side server through a UNIX socket.

The server is responsible for interacting with Docker Engine and collecting container statistics using Docker SDK.

This architecture eliminates the need to expose the Docker daemon socket (`/var/run/docker.sock`) to monitoring containers.

```text
+---------------------------+
| Host Operating System     |
|                           |
|  +-------------------+    |
|  | Monitoring Server |    |
|  +---------+---------+    |
|            |              |
|            | UNIX Socket  |
|            |              |
+------------+--------------+
             |
             v
+---------------------------+
| Monitoring Container      |
| SysmonAgent Client        |
+---------------------------+

+---------------------------+
| Monitored Containers      |
| PostgreSQL                |
| Future Services           |
+---------------------------+
```

---

## 6.2 Docker Image Design

The monitoring client is packaged as a Docker image.

The image is built from the official Python 3.11 Slim image.

Dockerfile:

```dockerfile
FROM python:3.11-slim
```

### Build Process

The image creation process performs the following steps:

1. Creates the application working directory.
2. Copies dependency definitions.
3. Installs required Python packages.
4. Copies application source code.
5. Defines the application entry point.

Build sequence:

```dockerfile
WORKDIR /client

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY /src/agent .

ENTRYPOINT ["python","main.py"]
```

### Design Rationale

The slim Python image was selected to:

* minimize image size,
* reduce attack surface,
* decrease deployment time,
* simplify dependency management.

---

## 6.3 Docker Compose Configuration

Docker Compose is used to orchestrate all containers required by the monitoring environment.

Current deployment consists of:

| Service  | Purpose                     |
| -------- | --------------------------- |
| client   | Monitoring agent            |
| postgres | Example monitored container |

---

## 6.4 Monitoring Client Service

The monitoring agent is deployed as the `client` service.

### Build Configuration

```yaml
build:
  context: ./
  dockerfile: Dockerfile
```

The container image is built locally using the project Dockerfile.

### Image

```yaml
image: ralik100/sysag:client_v1
```

This image contains the complete monitoring application.

### Shared Volumes

```yaml
volumes:
  - /tmp/socket/metrics.sock:/tmp/socket/metrics.sock
  - ./src/agent/output:/output
```

#### UNIX Socket Mount

The first volume shares the UNIX socket between the host server and monitoring client.

```text
Host
/tmp/socket/metrics.sock

        ⇅

Container
/tmp/socket/metrics.sock
```

This mount provides the only communication channel between both components.

#### Log Storage Mount

The second volume provides persistent storage for monitoring logs.

```text
Host
./src/agent/output

        ⇅

Container
/output
```

This allows logs generated inside the container to remain available on the host filesystem.

---

## 6.5 Monitored PostgreSQL Service

The project includes a PostgreSQL container used as an example monitored workload.

```yaml
image: postgres:16-alpine
```

### Database Configuration

```yaml
environment:
  POSTGRES_DB: sysmon
  POSTGRES_USER: sysmon
  POSTGRES_PASSWORD: super_secret_password
```

The container automatically creates a database instance during startup.

### Health Check

The PostgreSQL container exposes a health check:

```yaml
healthcheck:
  test:
    ["CMD-SHELL",
     "pg_isready -U sysmon -d sysmon"]
```

The monitoring client is configured to wait until PostgreSQL becomes healthy before startup.

```yaml
depends_on:
  postgres:
    condition: service_healthy
```

This prevents monitoring attempts against containers that are not yet ready.

---

## 6.6 Security Considerations

One of the primary design goals of SysmonAgent is secure metric collection.

Unlike many Docker monitoring solutions, the monitoring container does not receive direct access to:

* Docker daemon socket,
* Docker Engine API,
* privileged container mode,
* host process information.

Instead, all Docker interactions are performed by a dedicated host-side server.

Security benefits include:

* reduced attack surface,
* improved component isolation,
* adherence to the Principle of Least Privilege,
* protection of Docker Engine from container compromise.

Only filtered monitoring data is exposed to the monitoring client.

Raw Docker API responses never leave the host-side server.

```
```


# 7. Component Description

## 7.1 Monitoring Client

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

## 7.2 Host Server

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

## 7.3 Collectors

Collectors are responsible for gathering specific types of metrics.

Current collectors:

* container_stats

Future collectors may include:

* filesystem metrics
* process metrics
* application-specific metrics

---

## 7.4 Logger

Responsibilities:

* Queue events.
* Batch log writes.
* Persist events to storage.
* Provide unified event formatting.

---

## 7.5 Source Code Structure

The project follows a modular architecture where individual components are separated according to their responsibilities.

### Project Structure

```text
SysmonAgent/
│
├── src/
│   │
│   ├── client/
│   │   ├── main.py
│   │   ├── loop.py
│   │   ├── logger.py
│   │   ├── heartbeat.py
│   │   └── collectors/
│   │
│   └── server/
│       ├── main.py
│       └── server.py
│
├── config.json
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── start.bat
└── README.md
```

### Module Responsibilities

| Module              | Responsibility                                       |
| ------------------- | ---------------------------------------------------- |
| client/main.py      | Application startup and initialization               |
| client/loop.py      | Collector scheduling and execution                   |
| client/logger.py    | Event queue management and persistence               |
| client/heartbeat.py | Heartbeat event generation                           |
| client/collectors/* | Monitoring data collection                           |
| server/main.py      | Host server startup                                  |
| server/server.py    | UNIX socket communication and Docker SDK integration |
| config.json         | Runtime configuration                                |
| docker-compose.yml  | Monitoring container deployment                      |
| Dockerfile          | Prepared Docker image for monitoring container       |
| start.bat           | Automated application startup                        |

### Design Principles

The project design follows several principles:

* Separation of responsibilities.
* Modular architecture.
* Configuration-driven behavior.
* Extensibility through collectors.
* Minimal coupling between modules.
* Principle of least privilege.

These principles simplify maintenance and allow new functionality to be added with minimal modifications to existing code.

---

# 8. Communication Flow

## 8.1 Request Flow

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

## 8.2 Response Flow

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

## 8.3 Example Request

```json
{
  "action": "container_stats",
  "container": "postgres"
}
```

## 8.4 Example Response

```json
{
  "container_id": "...",
  "container_name": "postgres",
  "cpu_percent": 0.54,
  "memory_percent": 0.48
}
```

---

# 9. Configuration

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

# 10. Logging System

The logging subsystem is responsible for storing all events generated by the monitoring application in a unified JSON format.

Instead of writing every event directly to disk, events are first placed in an internal queue. The logger periodically writes queued events in batches, reducing the number of disk operations and improving performance.

## Logging Workflow

```text
Collector / Heartbeat
         |
         v
    Event Creation
         |
         v
      Queue
         |
         v
   Batch Writer
         |
         v
     Log File
```

## Event Types

The system currently generates two types of events:

* Monitoring events
* Heartbeat events

---

## Monitoring Event Structure

Monitoring events are generated whenever a collector successfully gathers container metrics.

Example:

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

### Monitoring Event Fields

| Field              | Description                                                           |
| ------------------ | --------------------------------------------------------------------- |
| container_id       | Unique Docker container identifier                                    |
| container_name     | Human-readable Docker container name                                  |
| level              | Event severity level                                                  |
| event              | Event type generated by the collector                                 |
| cpu_percent        | Container CPU utilization percentage                                  |
| memory_percent     | Container memory utilization percentage                               |
| memory_usage_bytes | Memory currently consumed by the container in bytes                   |
| network_rx_bytes   | Total number of bytes received by the container network interfaces    |
| network_tx_bytes   | Total number of bytes transmitted by the container network interfaces |
| created_at         | UNIX timestamp used for programmatic processing                       |
| timestamp          | ISO-8601 timestamp used for human-readable logs                       |

---

## Metric Collection Methodology

Container statistics are collected using Docker SDK for Python through the `container.stats(stream=False)` API.

The server receives raw Docker statistics and filters only the information required by the monitoring client.

### CPU Percentage

CPU utilization is calculated using the difference between current and previous CPU usage samples provided by Docker.

Formula:

```text
CPU % = (cpu_delta / system_delta) * online_cpus * 100
```

Where:

* `cpu_delta` is the difference in container CPU usage.
* `system_delta` is the difference in host CPU usage.
* `online_cpus` is the number of available CPU cores.

### Memory Percentage

Memory utilization is calculated using:

```text
memory_usage / memory_limit * 100
```

Where:

* `memory_usage` is the current memory consumption of the container.
* `memory_limit` is the maximum memory available to the container.

### Network Usage

Network statistics are obtained from Docker network counters.

* `network_rx_bytes` represents total received bytes.
* `network_tx_bytes` represents total transmitted bytes.

These values are cumulative counters maintained by Docker since container startup.

---

## Heartbeat Mechanism

The heartbeat mechanism provides information about the internal state and health of the monitoring application.

Unlike monitoring events, heartbeat events are not related to Docker containers. Instead, they describe the operational status and performance of SysmonAgent itself.

Heartbeat generation can be enabled or disabled through the configuration file.

Example configuration:

```json
{
  "heartbeat": {
    "enabled": true,
    "interval": 15
  }
}
```

When enabled, the application periodically generates heartbeat events according to the configured interval.

### Heartbeat Event Example

```json
{
  "level": "HEARTBEAT",
  "uptime": 0.002252817153930664,
  "performance": {
    "events_processed": 0,
    "events_per_sec": 0.0,
    "avg_lag": 0.0,
    "max_lag": 0.0
  },
  "queue": {
    "size": 0,
    "capacity": 1000,
    "utilization": 0.0
  },
  "errors": {
    "total": 0
  },
  "timestamp": "2026-06-10T20:26:04.678565Z"
}
```

### Heartbeat Event Fields

| Field     | Description                                                        |
| --------- | ------------------------------------------------------------------ |
| level     | Event type identifier. Heartbeat events use the value `HEARTBEAT`. |
| uptime    | Time elapsed since application startup, expressed in seconds.      |
| timestamp | ISO-8601 timestamp indicating when the heartbeat was generated.    |

### Performance Metrics

The `performance` section contains information about event processing efficiency.

| Field            | Description                                                            |
| ---------------- | ---------------------------------------------------------------------- |
| events_processed | Total number of events processed since startup.                        |
| events_per_sec   | Average event throughput per second.                                   |
| avg_lag          | Average processing delay between event creation and event persistence. |
| max_lag          | Maximum observed processing delay.                                     |

### Queue Metrics

The `queue` section provides information about the logger event queue.

| Field       | Description                                    |
| ----------- | ---------------------------------------------- |
| size        | Current number of events waiting in the queue. |
| capacity    | Maximum queue capacity.                        |
| utilization | Queue utilization percentage.                  |

Queue utilization is calculated as:

```text
(size / capacity) * 100
```

### Error Metrics

The `errors` section contains aggregated information about runtime failures.

| Field | Description                                                |
| ----- | ---------------------------------------------------------- |
| total | Total number of errors detected since application startup. |

### Purpose of Heartbeat Events

Heartbeat events allow administrators to:

* Verify that the monitoring service is running.
* Monitor logger queue saturation.
* Detect event processing bottlenecks.
* Observe monitoring throughput.
* Detect abnormal error accumulation.
* Measure application uptime.

This information can be used to assess the health and performance of SysmonAgent independently of the monitored containers.

---

## Logger Configuration

The logger behavior can be configured using the `logger` section of the configuration file.

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

### Logger Parameters

| Parameter      | Description                                                   |
| -------------- | ------------------------------------------------------------- |
| batchsize      | Maximum number of queued events written during a single flush |
| flush_interval | Maximum number of seconds between automatic writes            |
| log_filename   | Destination file used for JSON event storage                  |

The logger flushes events either when the batch size is reached or when the configured flush interval expires.

---

# 11. Error Handling

The system includes dedicated mechanisms for detecting and reporting runtime failures.

## Error Event Structure

Errors are converted into structured JSON events.

Example:

```json
{
  "level": "ERROR",
  "event": "collector_error",
  "action": "container_stats",
  "error_type": "KeyError",
  "error_message": "...",
  "timestamp": "2026-06-10T20:00:02.582166Z"
}
```

## Error Event Fields

| Field         | Description                                      |
| ------------- | ------------------------------------------------ |
| level         | Event severity level                             |
| event         | Error event identifier                           |
| action        | Collector or subsystem responsible for the error |
| error_type    | Python exception type                            |
| error_message | Exception message                                |
| timestamp     | Error creation timestamp                         |

## Collector Errors

Collector failures are isolated from the rest of the application.

If a collector fails:

* The exception is captured.
* An error event is generated.
* Other collectors continue execution.

This prevents a single collector failure from stopping the monitoring process.

## Communication Errors

Possible communication failures include:

* UNIX socket unavailable.
* Server process unavailable.
* Invalid requests.
* Invalid responses.

Communication failures are reported through error events whenever possible.

## Logging Errors

The logger handles failures related to:

* Invalid file paths.
* Missing permissions.
* JSON serialization failures.
* File system errors.

These failures are isolated from collector execution to prevent monitoring interruptions.

---

# 12. Monitoring Process

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

# 13. Testing

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


# 14. Known Limitations

Although SysmonAgent fulfills its design objectives, several limitations remain.

## Single Host Monitoring

The current implementation supports monitoring only a single Docker host.

Distributed monitoring is not implemented.

## Local JSON Storage

Monitoring events are stored in JSON files.

The system currently does not support:

* PostgreSQL
* MySQL
* Elasticsearch
* Time-series databases

## No Alerting System

The application collects and stores metrics but does not actively notify administrators when thresholds are exceeded.

Potential future integrations include:

* Email notifications
* Slack notifications
* Webhooks
* Microsoft Teams

## Limited Collector Set

The current implementation provides a single collector:

* container_stats

Additional collectors may be implemented in future versions.

## No Historical Analytics

The system focuses on metric collection and storage.

Trend analysis, aggregation and visualization are outside the scope of the current implementation.

## Platform Scope

The project was developed and tested primarily on:

* Windows 11
* WSL2
* Ubuntu
* Docker Desktop

Additional validation may be required for other environments.


# 15. Future Improvements

Potential future improvements include:

* PostgreSQL storage backend.
* Alerting system.
* Multi-host monitoring.
* Historical metrics analysis.
* Web dashboard.
* Multi threading for multiple containers

---

# 16. Conclusion

SysmonAgent demonstrates a secure approach to Docker container monitoring through a client-server architecture and UNIX socket communication.

The project achieves its primary objectives by collecting container metrics while maintaining isolation from Docker Engine and supporting future extensibility.
