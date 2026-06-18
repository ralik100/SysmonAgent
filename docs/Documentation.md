# Dokumentacja SysmonAgent

## Spis Treści

1. Wprowadzenie
2. Cele Projektu
3. Wymagania Funkcjonalne
4. Wymagania Niefunkcjonalne
5. Architektura Systemu
6. Architektura Wdrożeniowa
7. Opis Komponentów
8. Przepływ Komunikacji
9. Konfiguracja
10. System Logowania
11. Obsługa Błędów
12. Proces Monitorowania
13. Testowanie
14. Znane Ograniczenia
15. Możliwe Usprawnienia
16. Podsumowanie

---

# 1. Wprowadzenie

## 1.1 Opis Projektu

SysmonAgent jest systemem monitorowania zaprojektowanym do bezpiecznego zbierania metryk kontenerów Docker bez bezpośredniego udostępniania demona Docker kontenerom monitorującym.

Projekt implementuje architekturę klient-serwer, w której agent monitorujący działa wewnątrz kontenera Docker, natomiast serwer uruchomiony na hoście odpowiada za komunikację z Docker Engine przy użyciu Docker SDK.

Komunikacja pomiędzy obydwoma komponentami odbywa się za pomocą gniazda UNIX.

## 1.2 Cel Projektu

Celem projektu jest dostarczenie bezpiecznego i rozszerzalnego rozwiązania do zbierania metryk kontenerów przy jednoczesnym zachowaniu izolacji pomiędzy komponentami monitorującymi a zasobami hosta.

---

# 2. Cele Projektu

Główne cele projektu:

* Zbieranie metryk z wybranych kontenerów Docker.
* Unikanie bezpośredniego udostępniania Docker Engine kontenerom monitorującym.
* Zapewnienie konfigurowalnych interwałów monitorowania.
* Implementacja ujednoliconego mechanizmu logowania zdarzeń.
* Umożliwienie łatwego dodawania nowych kolektorów.
* Minimalizacja wykorzystania zasobów hosta.

---

# 3. Wymagania Funkcjonalne

System powinien:

* Monitorować wybrane kontenery Docker.
* Zbierać metryki wykorzystania procesora.
* Zbierać metryki wykorzystania pamięci.
* Zbierać metryki wykorzystania sieci.
* Zapisywać zebrane zdarzenia w formacie JSON.
* Umożliwiać konfigurację za pomocą pliku JSON.
* Obsługiwać wiele kolektorów.
* Obsługiwać konfigurowalne interwały wykonywania kolektorów.

---

# 4. Wymagania Niefunkcjonalne

System powinien zapewniać:

## Bezpieczeństwo

* Brak bezpośredniego dostępu do demona Docker z poziomu kontenerów monitorujących.
* Izolację pomiędzy logiką monitorowania a zasobami hosta.

## Utrzymywalność

* Modułową strukturę kodu.
* Rozdzielenie odpowiedzialności pomiędzy komponentami.

## Rozszerzalność

* Możliwość dodawania nowych kolektorów przy minimalnych zmianach w kodzie.

## Wydajność

* Lekkie działanie aplikacji.
* Minimalne zużycie procesora i pamięci.

---

# 5. Architektura Systemu

## 5.1 Przegląd Architektury

```text
+----------------------+
| Kontener Monitorujący|
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

## 5.2 Uzasadnienie Architektury

Wybrana architektura oddziela funkcjonalność monitorowania od dostępu do zasobów hosta.

Zamiast udostępniać kontenerowi monitorującemu gniazdo demona Docker, za zbieranie metryk odpowiada dedykowany serwer działający po stronie hosta.

Takie podejście zwiększa bezpieczeństwo i realizuje zasadę najmniejszych uprawnień.

## 5.3 Przepływ Danych

Poniższy diagram przedstawia pełny cykl życia danych monitorujących w systemie.

```text
Monitorowany Kontener
         |
         | Statystyki Docker
         v
Docker Engine
         |
         | Docker SDK
         v
Serwer Hosta
         |
         | Przefiltrowane Metryki
         v
Gniazdo UNIX
         |
         v
Klient Monitorujący
         |
         | Zdarzenie Monitorujące
         v
Kolejka Loggera
         |
         v
Zapis Wsadowy
         |
         v
Plik Logów JSON
```

Klient monitorujący nigdy nie komunikuje się bezpośrednio z Docker Engine. Cała komunikacja odbywa się za pośrednictwem serwera hosta, który pełni rolę kontrolowanej warstwy dostępu pomiędzy komponentami monitorującymi a zasobami systemowymi.

---

# 6. Architektura Wdrożeniowa

## 6.1 Model Wdrożenia

SysmonAgent jest wdrażany przy użyciu architektury hybrydowej składającej się z:

* serwera monitorującego działającego na hoście,
* klienta monitorującego uruchomionego w kontenerze,
* monitorowanych kontenerów Docker.

Klient monitorujący działa wewnątrz kontenera Docker i komunikuje się z serwerem hosta za pośrednictwem gniazda UNIX.

Serwer odpowiada za komunikację z Docker Engine oraz zbieranie statystyk kontenerów przy użyciu Docker SDK.

Architektura ta eliminuje konieczność udostępniania gniazda demona Docker (`/var/run/docker.sock`) kontenerom monitorującym.

```text
+---------------------------+
| System Operacyjny Hosta   |
|                           |
|  +-------------------+    |
|  | Serwer Monitorujący|   |
|  +---------+---------+    |
|            |              |
|            | Gniazdo UNIX |
|            |              |
+------------+--------------+
             |
             v
+---------------------------+
| Kontener Monitorujący     |
| Klient SysmonAgent        |
+---------------------------+

+---------------------------+
| Monitorowane Kontenery    |
| PostgreSQL                |
| Przyszłe Usługi           |
+---------------------------+
```

---

## 6.2 Konstrukcja Obrazu Docker

Klient monitorujący jest pakowany jako obraz Docker.

Obraz budowany jest na podstawie oficjalnego obrazu Python 3.11 Slim.

Dockerfile:

```dockerfile
FROM python:3.11-slim
```

### Proces Budowania

Proces tworzenia obrazu wykonuje następujące kroki:

1. Tworzy katalog roboczy aplikacji.
2. Kopiuje definicje zależności.
3. Instaluje wymagane pakiety Python.
4. Kopiuje kod źródłowy aplikacji.
5. Definiuje punkt wejściowy aplikacji.

Sekwencja budowania:

```dockerfile
WORKDIR /client

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY /src/agent .

ENTRYPOINT ["python","main.py"]
```

### Uzasadnienie Projektowe

Obraz Python Slim został wybrany w celu:

* minimalizacji rozmiaru obrazu,
* zmniejszenia powierzchni ataku,
* skrócenia czasu wdrożenia,
* uproszczenia zarządzania zależnościami.

---

## 6.3 Konfiguracja Docker Compose

Docker Compose jest wykorzystywany do orkiestracji wszystkich kontenerów wymaganych przez środowisko monitorujące.

Obecna konfiguracja składa się z:

| Usługa   | Przeznaczenie                     |
| -------- | --------------------------------- |
| client   | Agent monitorujący                |
| postgres | Przykładowy monitorowany kontener |

---

## 6.4 Usługa Klienta Monitorującego

Agent monitorujący jest wdrażany jako usługa `client`.

### Konfiguracja Budowania

```yaml
build:
  context: ./
  dockerfile: Dockerfile
```

Obraz kontenera budowany jest lokalnie przy użyciu projektowego pliku Dockerfile.

### Obraz

```yaml
image: ralik100/sysag:client_v1
```

Obraz zawiera kompletną aplikację monitorującą.

### Współdzielone Wolumeny

```yaml
volumes:
  - /tmp/socket/metrics.sock:/tmp/socket/metrics.sock
  - ./src/agent/output:/output
```

#### Montowanie Gniazda UNIX

Pierwszy wolumen współdzieli gniazdo UNIX pomiędzy serwerem hosta a klientem monitorującym.

```text
Host
/tmp/socket/metrics.sock

        ⇅

Kontener
/tmp/socket/metrics.sock
```

To montowanie stanowi jedyny kanał komunikacji pomiędzy obydwoma komponentami.

#### Montowanie Logów

Drugi wolumen zapewnia trwałe przechowywanie logów monitorujących.

```text
Host
./src/agent/output

        ⇅

Kontener
/output
```

Dzięki temu logi wygenerowane wewnątrz kontenera pozostają dostępne w systemie plików hosta.

---

## 6.5 Monitorowana Usługa PostgreSQL

Projekt zawiera kontener PostgreSQL wykorzystywany jako przykładowe monitorowane obciążenie.

```yaml
image: postgres:16-alpine
```

### Konfiguracja Bazy Danych

```yaml
environment:
  POSTGRES_DB: sysmon
  POSTGRES_USER: sysmon
  POSTGRES_PASSWORD: super_secret_password
```

Kontener automatycznie tworzy instancję bazy danych podczas uruchamiania.

### Kontrola Stanu

Kontener PostgreSQL udostępnia mechanizm sprawdzania gotowości:

```yaml
healthcheck:
  test:
    ["CMD-SHELL",
     "pg_isready -U sysmon -d sysmon"]
```

Klient monitorujący został skonfigurowany tak, aby oczekiwał na poprawne uruchomienie PostgreSQL przed startem.

```yaml
depends_on:
  postgres:
    condition: service_healthy
```

Zapobiega to próbom monitorowania kontenerów, które nie są jeszcze gotowe do pracy.

---

## 6.6 Aspekty Bezpieczeństwa

Jednym z głównych założeń projektowych SysmonAgent jest bezpieczne zbieranie metryk.

W przeciwieństwie do wielu rozwiązań monitorujących Docker, kontener monitorujący nie otrzymuje bezpośredniego dostępu do:

* gniazda demona Docker,
* API Docker Engine,
* trybu uprzywilejowanego kontenera,
* informacji o procesach hosta.

Zamiast tego wszystkie operacje związane z Dockerem wykonywane są przez dedykowany serwer działający po stronie hosta.

Korzyści bezpieczeństwa:

* zmniejszona powierzchnia ataku,
* lepsza izolacja komponentów,
* zgodność z zasadą najmniejszych uprawnień,
* ochrona Docker Engine przed kompromitacją kontenera.

Klient monitorujący otrzymuje wyłącznie przefiltrowane dane monitorujące.

Surowe odpowiedzi API Dockera nigdy nie opuszczają serwera działającego na hoście.

---

# 7. Opis Komponentów

## 7.1 Klient Monitorujący

Odpowiedzialności:

* Wczytywanie konfiguracji aplikacji.
* Harmonogramowanie kolektorów.
* Wysyłanie żądań do serwera.
* Odbieranie zebranych metryk.
* Generowanie zdarzeń monitorujących.
* Przekazywanie zdarzeń do systemu logowania.

### Główne Moduły

* main.py
* loop.py
* collectors/
* logger.py

---

## 7.2 Serwer Hosta

Odpowiedzialności:

* Nasłuchiwanie połączeń klienta.
* Odbieranie żądań zbierania metryk.
* Komunikacja z Docker Engine.
* Filtrowanie zebranych metryk.
* Zwracanie wyników do klienta.

### Główne Moduły

* main.py
* server.py

---

## 7.3 Kolektory

Kolektory odpowiadają za zbieranie określonych typów metryk.

Obecnie dostępne kolektory:

* container_stats

Przyszłe kolektory mogą obejmować:

* metryki systemu plików,
* metryki procesów,
* metryki specyficzne dla aplikacji.

---

## 7.4 Logger

Odpowiedzialności:

* Kolejkowanie zdarzeń.
* Wsadowy zapis logów.
* Trwałe przechowywanie danych.
* Zapewnienie ujednoliconego formatu zdarzeń.

---
## 7.5 Struktura Kodu Źródłowego

Projekt wykorzystuje architekturę modułową, w której poszczególne komponenty zostały rozdzielone zgodnie z ich odpowiedzialnościami.

### Struktura Projektu

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

### Odpowiedzialności Modułów

| Moduł | Odpowiedzialność |
|--------|------------------|
| client/main.py | Uruchamianie i inicjalizacja aplikacji |
| client/loop.py | Harmonogramowanie i wykonywanie kolektorów |
| client/logger.py | Zarządzanie kolejką zdarzeń oraz ich trwały zapis |
| client/heartbeat.py | Generowanie zdarzeń heartbeat |
| client/collectors/* | Pobieranie danych monitoringowych |
| server/main.py | Uruchamianie serwera hosta |
| server/server.py | Komunikacja przez UNIX Socket oraz integracja z Docker SDK |
| config.json | Konfiguracja aplikacji |
| docker-compose.yml | Definicja wdrożenia kontenera monitorującego |
| Dockerfile | Definicja obrazu Docker klienta monitorującego |
| start.bat | Automatyczne uruchamianie aplikacji |

### Założenia Projektowe

Projekt został zaprojektowany zgodnie z następującymi zasadami:

* Rozdzielenie odpowiedzialności.
* Architektura modułowa.
* Zachowanie sterowane konfiguracją.
* Rozszerzalność poprzez kolektory.
* Minimalne zależności pomiędzy modułami.
* Zasada najmniejszych uprawnień (Principle of Least Privilege).

Powyższe założenia upraszczają utrzymanie projektu oraz umożliwiają dodawanie nowych funkcjonalności przy minimalnej modyfikacji istniejącego kodu.

---

# 8. Przepływ Komunikacji

## 8.1 Przepływ Żądania

```text
Klient
   |
   | Żądanie
   v
Serwer
   |
   | Docker SDK
   v
Docker Engine
```

## 8.2 Przepływ Odpowiedzi

```text
Docker Engine
   |
   | Metryki
   v
Serwer
   |
   | Przefiltrowane Metryki
   v
Klient
```

## 8.3 Przykładowe Żądanie

```json
{
  "action": "container_stats",
  "container": "postgres"
}
```

## 8.4 Przykładowa Odpowiedź

```json
{
  "container_id": "...",
  "container_name": "postgres",
  "cpu_percent": 0.54,
  "memory_percent": 0.48
}
```

---

# 9. Konfiguracja

Konfiguracja systemu przechowywana jest w pliku `config.json`.

## Przykładowa Konfiguracja

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

## Parametry Konfiguracyjne

| Parametr | Opis |
|-----------|------|
| mode | Tryb działania aplikacji |
| intervals | Interwały wykonywania kolektorów |
| collectors | Aktywne kolektory |
| heartbeat | Konfiguracja heartbeat |
| logger | Konfiguracja loggera |
| monitored_container_names | Lista monitorowanych kontenerów |

## Szczegółowy Opis Parametrów

### mode

**Typ:** `string`

Określa sposób wykonywania kolektorów przez agenta monitorującego.

Możliwe wartości:

* `loop` — kolektory wykonywane są cyklicznie zgodnie z interwałami zdefiniowanymi w sekcji `intervals`.
* `once` — każdy kolektor wykonywany jest dokładnie jeden raz, po czym aplikacja kończy działanie.

Przykład:

```json
{
  "mode": "loop"
}
```

---

### intervals

**Typ:** `dictionary`

Definiuje interwały wykonywania (w sekundach) dla poszczególnych kolektorów.

Każdy aktywny kolektor powinien posiadać przypisany interwał.

Przykład:

```json
{
  "intervals": {
    "container_stats": 1
  }
}
```

---

### collectors

**Typ:** `array[string]`

Lista aktywnych kolektorów.

Dostępne kolektory:

#### container_stats

Zbiera przefiltrowane statystyki kontenerów Docker obejmujące:

* wykorzystanie procesora (CPU),
* wykorzystanie pamięci operacyjnej (RAM),
* zużycie pamięci w bajtach,
* liczbę odebranych bajtów sieciowych (RX),
* liczbę wysłanych bajtów sieciowych (TX).

Przykład:

```json
{
  "collectors": [
    "container_stats"
  ]
}
```

---

### heartbeat

**Typ:** `object`

Steruje generowaniem cyklicznych zdarzeń heartbeat.

Parametry:

| Parametr | Typ | Opis |
|-----------|------|------|
| enabled | boolean | Włącza lub wyłącza generowanie heartbeat |
| interval | integer | Interwał heartbeat wyrażony w sekundach |

Przykład:

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

**Typ:** `object`

Konfiguruje sposób logowania zdarzeń przez aplikację.

Parametry:

| Parametr | Typ | Opis |
|-----------|------|------|
| batchsize | integer | Liczba zdarzeń zapisywanych w jednym pakiecie |
| flush_interval | integer | Maksymalny czas pomiędzy kolejnymi zapisami |
| log_filename | string | Nazwa pliku logów |

Przykład:

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

**Typ:** `integer`

Definiuje próg ostrzegawczy dla monitorowanych metryk wyrażony w procentach.

Przykład:

```json
{
  "warning_threshold": 70
}
```

---

### monitored_container_names

**Typ:** `array[string]`

Lista nazw kontenerów Docker, które mają być monitorowane.

Przykład:

```json
{
  "monitored_container_names": [
    "postgres"
  ]
}
```

---
# 10. System Logowania

Podsystem logowania odpowiada za przechowywanie wszystkich zdarzeń generowanych przez aplikację monitorującą w ujednoliconym formacie JSON.

Zamiast zapisywać każde zdarzenie bezpośrednio na dysk, zdarzenia są najpierw umieszczane w wewnętrznej kolejce. Logger okresowo zapisuje zgromadzone zdarzenia partiami, co zmniejsza liczbę operacji dyskowych i poprawia wydajność.

## Przepływ Logowania

```text
Kolektor / Heartbeat
         |
         v
  Utworzenie Zdarzenia
         |
         v
       Kolejka
         |
         v
   Zapis Wsadowy
         |
         v
    Plik Logów
```

## Typy Zdarzeń

System aktualnie generuje dwa typy zdarzeń:

* Zdarzenia monitorujące
* Zdarzenia heartbeat

---

## Struktura Zdarzenia Monitorującego

Zdarzenia monitorujące są generowane za każdym razem, gdy kolektor pomyślnie pobierze metryki kontenera.

Przykład:

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

### Pola Zdarzenia Monitorującego

| Pole | Opis |
|--------|--------|
| container_id | Unikalny identyfikator kontenera Docker |
| container_name | Czytelna dla użytkownika nazwa kontenera |
| level | Poziom ważności zdarzenia |
| event | Typ zdarzenia wygenerowanego przez kolektor |
| cpu_percent | Procentowe wykorzystanie procesora przez kontener |
| memory_percent | Procentowe wykorzystanie pamięci przez kontener |
| memory_usage_bytes | Aktualne zużycie pamięci przez kontener w bajtach |
| network_rx_bytes | Łączna liczba bajtów odebranych przez interfejsy sieciowe kontenera |
| network_tx_bytes | Łączna liczba bajtów wysłanych przez interfejsy sieciowe kontenera |
| created_at | Znacznik czasu UNIX wykorzystywany do obliczeń programistycznych |
| timestamp | Znacznik czasu ISO-8601 przeznaczony do odczytu przez użytkownika |

---

## Metodologia Zbierania Metryk

Statystyki kontenerów pobierane są przy użyciu Docker SDK for Python za pomocą interfejsu `container.stats(stream=False)`.

Serwer odbiera surowe statystyki Dockera i filtruje wyłącznie informacje wymagane przez klienta monitorującego.

### Wykorzystanie CPU

Wykorzystanie procesora obliczane jest na podstawie różnicy pomiędzy bieżącą i poprzednią próbką wykorzystania CPU dostarczoną przez Docker.

Wzór:

```text
CPU % = (cpu_delta / system_delta) * online_cpus * 100
```

Gdzie:

* `cpu_delta` oznacza różnicę wykorzystania CPU przez kontener.
* `system_delta` oznacza różnicę całkowitego wykorzystania CPU hosta.
* `online_cpus` oznacza liczbę dostępnych rdzeni procesora.

### Wykorzystanie Pamięci

Wykorzystanie pamięci obliczane jest według wzoru:

```text
memory_usage / memory_limit * 100
```

Gdzie:

* `memory_usage` oznacza aktualne zużycie pamięci przez kontener.
* `memory_limit` oznacza maksymalną ilość pamięci dostępną dla kontenera.

### Wykorzystanie Sieci

Statystyki sieciowe pobierane są z liczników sieciowych Dockera.

* `network_rx_bytes` oznacza całkowitą liczbę odebranych bajtów.
* `network_tx_bytes` oznacza całkowitą liczbę wysłanych bajtów.

Wartości te są licznikami narastającymi utrzymywanymi przez Docker od momentu uruchomienia kontenera.

---

## Mechanizm Heartbeat

Mechanizm heartbeat dostarcza informacji o wewnętrznym stanie oraz kondycji aplikacji monitorującej.

W przeciwieństwie do zdarzeń monitorujących, zdarzenia heartbeat nie dotyczą kontenerów Docker. Opisują one stan działania i wydajność samego SysmonAgent.

Generowanie heartbeat może zostać włączone lub wyłączone w pliku konfiguracyjnym.

Przykładowa konfiguracja:

```json
{
  "heartbeat": {
    "enabled": true,
    "interval": 15
  }
}
```

Po włączeniu aplikacja cyklicznie generuje zdarzenia heartbeat zgodnie ze skonfigurowanym interwałem.

### Przykładowe Zdarzenie Heartbeat

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

### Pola Zdarzenia Heartbeat

| Pole | Opis |
|--------|--------|
| level | Identyfikator typu zdarzenia. Dla heartbeat przyjmuje wartość `HEARTBEAT`. |
| uptime | Czas działania aplikacji od uruchomienia wyrażony w sekundach. |
| timestamp | Znacznik czasu ISO-8601 określający moment wygenerowania heartbeat. |

### Metryki Wydajności

Sekcja `performance` zawiera informacje dotyczące wydajności przetwarzania zdarzeń.

| Pole | Opis |
|--------|--------|
| events_processed | Łączna liczba przetworzonych zdarzeń od uruchomienia aplikacji |
| events_per_sec | Średnia liczba zdarzeń przetwarzanych na sekundę |
| avg_lag | Średnie opóźnienie pomiędzy utworzeniem a zapisaniem zdarzenia |
| max_lag | Maksymalne zaobserwowane opóźnienie przetwarzania |

### Metryki Kolejki

Sekcja `queue` dostarcza informacji o kolejce zdarzeń loggera.

| Pole | Opis |
|--------|--------|
| size | Aktualna liczba zdarzeń oczekujących w kolejce |
| capacity | Maksymalna pojemność kolejki |
| utilization | Stopień wykorzystania kolejki |

Wykorzystanie kolejki obliczane jest według wzoru:

```text
(size / capacity) * 100
```

### Metryki Błędów

Sekcja `errors` zawiera zagregowane informacje o błędach występujących podczas działania aplikacji.

| Pole | Opis |
|--------|--------|
| total | Łączna liczba błędów wykrytych od uruchomienia aplikacji |

### Cel Zdarzeń Heartbeat

Zdarzenia heartbeat umożliwiają administratorowi:

* Weryfikację poprawnego działania usługi monitorującej.
* Monitorowanie stopnia zapełnienia kolejki loggera.
* Wykrywanie wąskich gardeł podczas przetwarzania zdarzeń.
* Obserwację przepustowości systemu monitorowania.
* Wykrywanie nadmiernej liczby błędów.
* Pomiar czasu działania aplikacji.

Informacje te pozwalają ocenić stan i wydajność SysmonAgent niezależnie od monitorowanych kontenerów.

---

## Konfiguracja Loggera

Zachowanie loggera może być konfigurowane za pomocą sekcji `logger` w pliku konfiguracyjnym.

Przykład:

```json
{
  "logger": {
    "batchsize": 10,
    "flush_interval": 2,
    "log_filename": "log.json"
  }
}
```

### Parametry Loggera

| Parametr | Opis |
|-----------|--------|
| batchsize | Maksymalna liczba zdarzeń zapisywanych podczas pojedynczego zapisu wsadowego |
| flush_interval | Maksymalna liczba sekund pomiędzy automatycznymi zapisami |
| log_filename | Nazwa pliku przeznaczonego do przechowywania zdarzeń JSON |

Logger zapisuje dane, gdy zostanie osiągnięty rozmiar partii lub gdy upłynie skonfigurowany interwał zapisu.

---

# 11. Obsługa Błędów

System zawiera dedykowane mechanizmy wykrywania oraz raportowania błędów występujących podczas działania aplikacji.

## Struktura Zdarzenia Błędu

Błędy są konwertowane do ustrukturyzowanych zdarzeń JSON.

Przykład:

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

## Pola Zdarzenia Błędu

| Pole | Opis |
|--------|--------|
| level | Poziom ważności zdarzenia |
| event | Identyfikator zdarzenia błędu |
| action | Kolektor lub podsystem odpowiedzialny za błąd |
| error_type | Typ wyjątku języka Python |
| error_message | Treść wyjątku |
| timestamp | Znacznik czasu utworzenia błędu |

## Błędy Kolektorów

Awaria pojedynczego kolektora jest izolowana od pozostałych elementów aplikacji.

Jeżeli kolektor zakończy działanie błędem:

* wyjątek zostaje przechwycony,
* generowane jest zdarzenie błędu,
* pozostałe kolektory kontynuują działanie.

Dzięki temu awaria pojedynczego kolektora nie zatrzymuje procesu monitorowania.

## Błędy Komunikacji

Możliwe błędy komunikacyjne obejmują:

* niedostępny UNIX Socket,
* niedostępny proces serwera,
* niepoprawne żądania,
* niepoprawne odpowiedzi.

Błędy komunikacyjne są raportowane poprzez zdarzenia błędów, gdy jest to możliwe.

## Błędy Loggera

Logger obsługuje błędy związane z:

* nieprawidłowymi ścieżkami plików,
* brakiem uprawnień,
* błędami serializacji JSON,
* błędami systemu plików.

Błędy te są odizolowane od działania kolektorów, aby nie przerywać procesu monitorowania.

---

# 12. Proces Monitorowania

Proces monitorowania przebiega według następujących kroków:

1. Uruchomienie aplikacji.
2. Wczytanie konfiguracji.
3. Zaplanowanie kolektorów.
4. Wysłanie żądania do serwera.
5. Pobranie metryk przy użyciu Docker SDK.
6. Filtrowanie metryk.
7. Utworzenie zdarzenia.
8. Zapisanie zdarzenia do logów.

---

# 13. Testowanie

## Przetestowane Scenariusze

### Testy Uruchomienia

* Uruchomienie serwera.
* Uruchomienie klienta.
* Wdrożenie przy użyciu Docker Compose.

### Testy Komunikacji

* Połączenie przez UNIX Socket.
* Obsługa żądań.
* Obsługa odpowiedzi.

### Testy Monitorowania

* Pobieranie metryk CPU.
* Pobieranie metryk pamięci.
* Pobieranie metryk sieciowych.

### Testy Logowania

* Tworzenie zdarzeń.
* Zapis wsadowy.
* Trwały zapis logów.

---

# 14. Znane Ograniczenia

Pomimo spełnienia założeń projektowych SysmonAgent posiada kilka ograniczeń.

## Monitorowanie Pojedynczego Hosta

Obecna implementacja obsługuje monitorowanie wyłącznie jednego hosta Docker.

Monitorowanie rozproszone nie zostało zaimplementowane.

## Lokalne Przechowywanie Logów

Zdarzenia monitorujące przechowywane są w plikach JSON.

System obecnie nie obsługuje:

* PostgreSQL
* MySQL
* Elasticsearch
* Baz danych typu Time-Series

## Brak Systemu Alertów

Aplikacja zbiera i zapisuje metryki, lecz nie powiadamia administratorów o przekroczeniu progów alarmowych.

Możliwe przyszłe integracje obejmują:

* Powiadomienia e-mail
* Powiadomienia Slack
* Webhooki
* Microsoft Teams

## Ograniczony Zestaw Kolektorów

Aktualna implementacja udostępnia jeden kolektor:

* container_stats

Dodatkowe kolektory mogą zostać zaimplementowane w kolejnych wersjach projektu.

## Brak Analizy Historycznej

System skupia się na zbieraniu i przechowywaniu metryk.

Analiza trendów, agregacja danych oraz wizualizacja wyników nie należą do zakresu obecnej implementacji.

## Zakres Platform

Projekt był rozwijany i testowany głównie na:

* Windows 11
* WSL2
* Ubuntu
* Docker Desktop

W przypadku innych środowisk może być wymagana dodatkowa walidacja.

# 15. Możliwe Kierunki Rozwoju

Potencjalne usprawnienia projektu obejmują:

* Integrację z PostgreSQL.
* System alertów.
* Monitorowanie wielu hostów.
* Analizę historycznych metryk.
* Panel webowy.
* Wielowątkowe monitorowanie wielu kontenerów.

---

# 16. Podsumowanie

SysmonAgent prezentuje bezpieczne podejście do monitorowania kontenerów Docker poprzez zastosowanie architektury klient-serwer oraz komunikacji opartej o UNIX Socket.

Projekt realizuje swoje główne cele poprzez zbieranie metryk kontenerów przy jednoczesnym zachowaniu izolacji od Docker Engine oraz zapewnieniu możliwości dalszej rozbudowy.