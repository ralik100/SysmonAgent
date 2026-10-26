import os
import src.server.server as server
import subprocess
import argparse
import filehandler


def setup_environment_variables(environment_variables):

    for key, value in environment_variables.items():
        os.environ(key) = value

def end_logging(client_result, server_result):
    pass

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        required=True,
        help="Path to JSON configuration file"
    )

    args = parser.parse_args()
    config_file_path = args.config

    client_configuration = (
        mode,
        interval_configuration,
        collectors_configuration,
        warning_threshold,
        logging_configuration,
        heartbeat_configuration,
        container_names,
        environment_variables
    ) = filehandler.load_config(config_file_path)

    environment_variables["CONFIG_FILE_PATH"]=config_file_path

    setup_environment_variables(environment_variables)

    client = subprocess.Popen(
        ["docker","compose","up","--build"],
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