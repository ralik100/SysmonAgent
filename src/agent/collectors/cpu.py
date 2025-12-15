import psutil


def get_cpu_usage(interval):


    x=psutil.cpu_percent(interval)

    return x