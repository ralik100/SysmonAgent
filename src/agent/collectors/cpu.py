import psutil


def get_cpu_usage():


    x=psutil.cpu_percent(1)

    return x