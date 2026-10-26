import json

def load_config(config_file):
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

    with open(config_file, "r") as f:
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