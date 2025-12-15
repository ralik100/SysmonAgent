import psutil


def get_ram_usage():

    usage=psutil.virtual_memory().percent

    return usage