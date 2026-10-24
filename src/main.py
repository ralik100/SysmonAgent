import loop
import logger
import heartbeat
import json
import collectors.collector
import threading
import stats
import socket
import os
import src.agent.client as client
import src.server.server as server
import subprocess

def load_config():
    """
    Wczytuje konfigurację aplikacji z pliku config.json.

    Funkcja odczytuje wszystkie parametry konfiguracyjne oraz
    tworzy słownik zawierający wyłącznie kolektory aktywowane
    przez użytkownika.

    Zwraca:
        tuple:
            mode (str)
            intervals (dict)
            active_collectors (dict)
            warning_threshold (int)
            logger_config (dict)
            heartbeat_conf (dict)
            container_names (list[str])

    Wyjątki:
        FileNotFoundError:
            Jeśli plik config.json nie istnieje.

        json.JSONDecodeError:
            Jeśli plik konfiguracji zawiera niepoprawny JSON.
    """

    with open("config.json", "r") as f:
        config = json.load(f)

    mode = config["mode"]
    interval_configuration = config["interval_configuration"]    
    collectors_configuration = config["collectors_configuration"]
    warning_threshold = config["warning_threshold"]
    logging_configuration = config["logging_configuration"]
    heartbeat_configuration = config["heartbeat_configuration"]
    container_names = config["monitored_container_names"]
    environment_variables = config["environment_variables"]


    return (
        mode,
        interval_configuration,
        collectors_configuration,
        warning_threshold,
        logging_configuration,
        heartbeat_configuration,
        container_names,
        environment_variables
    )


def setup_environment_variables(environment_variables):

    for key, value in environment_variables.items():
        os.environ(key) = value

def end_logging(client_result, server_result):
    pass

def main():

    client_configuration = (
        mode,
        interval_configuration,
        collectors_configuration,
        warning_threshold,
        logging_configuration,
        heartbeat_configuration,
        container_names,
        environment_variables
    ) = load_config()


    setup_environment_variables(environment_variables)

    client = subprocess.Popen(
        ["python", "/agent/client.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    server = subprocess.Popen(
        ["python", "/server/server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    client_stdout, client_stderr = client.communicate()
    server_stdout, server_stderr = server.communicate()

    client_result = (client_stdout, client_stderr)
    server_result = (server_stdout, server_stderr)

    end_logging(client_result, server_result)

if __name__ == "__main__":
    main()