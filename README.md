# SysmonAgent

## Przegląd

SysmonAgent jest narzędziem przeznaczonym do bezpiecznego monitorowania kontenerów Docker. System wykorzystuje architekturę klient-serwer w celu oddzielenia logiki monitorowania od dostępu do zasobów hosta.

Agent monitorujący działa wewnątrz kontenera Docker i komunikuje się z serwerem uruchomionym na hoście za pomocą gniazda UNIX. Serwer działający po stronie hosta odpowiada za zbieranie metryk kontenerów przy użyciu Docker SDK, filtrowanie zebranych danych oraz zwracanie wyłącznie wymaganych informacji do agenta monitorującego.

### Architektura

```text
+----------------------+
| Kontener Monitorujący |
+----------+-----------+
           |
           | Gniazdo UNIX
           |
+----------v-----------+
| Serwer Hosta         |
| Docker SDK           |
+----------+-----------+
           |
           | Docker API
           |
+----------v-----------+
| Monitorowane         |
| Kontenery            |
+----------------------+
```

### Zalety

* Kontener monitorujący nie posiada bezpośredniego dostępu do demona Docker.
* Kontener monitorujący nie wymaga dostępu do `/var/run/docker.sock`.
* Statystyki kontenerów są zbierane przez dedykowaną usługę działającą po stronie hosta.
* Komunikacja pomiędzy komponentami jest izolowana przy użyciu gniazda UNIX.
* Logika monitorowania, zbieranie danych oraz logowanie są rozdzielone na niezależne moduły.
* Nowe kolektory mogą być dodawane poprzez konfigurację bez modyfikowania głównej logiki aplikacji.

System obecnie zbiera metryki takie jak wykorzystanie procesora, wykorzystanie pamięci oraz statystyki sieciowe z monitorowanych kontenerów i zapisuje je w ujednoliconym formacie zdarzeń JSON do dalszego przetwarzania i analizy.

---

## Funkcjonalności

* Monitorowanie kontenerów Docker
* Architektura klient-serwer
* Komunikacja przez gniazdo UNIX
* Integracja z Docker SDK
* Logowanie zdarzeń w formacie JSON
* Konfigurowalne kolektory
* Konfigurowalne interwały monitorowania
* Konfigurowalne logowanie
* Izolacja hosta od kontenera monitorującego
* Lekkie wdrożenie przy użyciu Docker Compose

---

## Wymagania

* Windows 11
* WSL2
* Ubuntu (dystrybucja WSL)
* Python 3
* Python virtual environment (venv)
* Docker Desktop

---

## Instalacja

### 1. Sklonowanie repozytorium

```bash
git clone https://github.com/ralik100/SysmonAgent.git
cd SysmonAgent
```

### 2. Instalacja WSL i Ubuntu

Uruchom PowerShell jako Administrator:

```powershell
wsl --install
```

Zainstaluj Ubuntu:

```powershell
wsl --install -d Ubuntu
```

Zweryfikuj instalację:

```powershell
wsl -l -v
```

### 3. Uruchom Ubuntu

```bash
wsl -d Ubuntu -u root
```

### 4. Instalacja Python, pip oraz venv

```bash
apt update
apt install -y python3 python3-pip python3-venv
```

Zweryfikuj instalację:

```bash
python3 --version
pip3 --version
```

### 5. Utworzenie środowiska wirtualnego Python

W katalogu projektu:

```bash
python3 -m venv .venv
```

Aktywuj środowisko wirtualne:

```bash
source .venv/bin/activate
```

Zainstaluj zależności:

```bash
pip install -r requirements.txt
```

### 6. Instalacja Docker Desktop

Zainstaluj Docker Desktop dla systemu Windows i włącz integrację z WSL.

Zweryfikuj dostęp do Dockera z poziomu WSL:

```bash
docker --version
docker compose version
```

---

## Konfiguracja

Konfiguracja aplikacji znajduje się w pliku `config.json`.

Przykład:

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

## Uruchamianie SysmonAgent

### Automatyczne uruchamianie

Najprostszym sposobem uruchomienia aplikacji jest:

```cmd
start.bat
```

### Ręczne uruchamianie

Uruchom serwer po stronie hosta:

```bash
source .venv/bin/activate
python3 src/server/main.py
```

W osobnym terminalu uruchom kontener monitorujący:

```bash
docker compose up --build
```

---

## Przykładowe zdarzenie

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

## Uwagi

> `start.bat` zakłada domyślną strukturę katalogów projektu.
>
> Jeśli plik zostanie przeniesiony w inne miejsce, ścieżki wewnątrz skryptu mogą wymagać aktualizacji.

> Docker Desktop musi być uruchomiony przed startem SysmonAgent.

> Integracja WSL musi być włączona w ustawieniach Docker Desktop.

> Więcej informacji znajduje się w dokumentacji przechowywanej w katalogu `/docs`.
